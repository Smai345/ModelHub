"""
Experiment routes: create, list, get, update, delete, rounds, submissions.
"""
from typing import Annotated, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.db.database import get_db
from backend.api.deps import get_current_user, require_researcher_or_admin
from backend.api.models.user import User
from backend.api.models.experiment import Experiment, ExperimentStatus, FederatedRound, RoundStatus
from backend.api.models.leaderboard import ModelSubmission, SubmissionStatus
from backend.api.schemas.experiment import (
    ExperimentCreateRequest,
    ExperimentResponse,
    ExperimentListResponse,
    FederatedRoundResponse,
    SubmissionCreateRequest,
    SubmissionResponse,
    DashboardStats,
)
from backend.services.aggregation import run_federated_aggregation
from backend.services.data_quality import compute_data_quality
from backend.tasks.celery_app import celery_app

log = structlog.get_logger()
router = APIRouter()


# ─── Dashboard ────────────────────────────────────────────────────────────────
@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from datetime import datetime, timezone, timedelta

    total_exp = await db.scalar(select(func.count(Experiment.id)))
    active_exp = await db.scalar(
        select(func.count(Experiment.id)).where(
            Experiment.status.in_([ExperimentStatus.RECRUITING, ExperimentStatus.TRAINING])
        )
    )
    total_participants = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    total_subs = await db.scalar(select(func.count(ModelSubmission.id)))
    best_acc = await db.scalar(select(func.max(Experiment.best_accuracy))) or 0.0
    avg_trust = await db.scalar(select(func.avg(User.trust_score))) or 0.0

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    exps_week = await db.scalar(
        select(func.count(Experiment.id)).where(Experiment.created_at >= week_ago)
    )
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    subs_today = await db.scalar(
        select(func.count(ModelSubmission.id)).where(ModelSubmission.created_at >= today)
    )

    return DashboardStats(
        total_experiments=total_exp or 0,
        active_experiments=active_exp or 0,
        total_participants=total_participants or 0,
        total_submissions=total_subs or 0,
        global_best_accuracy=round(best_acc, 4),
        avg_trust_score=round(avg_trust, 4),
        experiments_this_week=exps_week or 0,
        submissions_today=subs_today or 0,
    )


# ─── Experiments CRUD ────────────────────────────────────────────────────────
@router.post("/", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment(
    body: ExperimentCreateRequest,
    current_user: Annotated[User, Depends(require_researcher_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    exp = Experiment(
        **body.model_dump(),
        creator_id=current_user.id,
    )
    db.add(exp)
    await db.flush()
    await db.refresh(exp)
    log.info("Experiment created", exp_id=str(exp.id), creator=current_user.username)
    return exp


@router.get("/", response_model=ExperimentListResponse)
async def list_experiments(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[ExperimentStatus] = Query(None, alias="status"),
    my_only: bool = Query(False),
):
    q = select(Experiment)
    if status_filter:
        q = q.where(Experiment.status == status_filter)
    if my_only:
        q = q.where(Experiment.creator_id == current_user.id)
    else:
        q = q.where(Experiment.is_public == True)

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.offset((page - 1) * page_size).limit(page_size).order_by(Experiment.created_at.desc())
    result = await db.execute(q)
    experiments = result.scalars().all()

    return ExperimentListResponse(
        experiments=experiments,
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.get("/{exp_id}", response_model=ExperimentResponse)
async def get_experiment(
    exp_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    exp = await db.get(Experiment, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if not exp.is_public and exp.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this experiment")
    return exp


@router.delete("/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(
    exp_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    exp = await db.get(Experiment, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp.creator_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(exp)


# ─── Rounds ──────────────────────────────────────────────────────────────────
@router.post("/{exp_id}/rounds/next", response_model=FederatedRoundResponse)
async def start_next_round(
    exp_id: UUID,
    current_user: Annotated[User, Depends(require_researcher_or_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    exp = await db.get(Experiment, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the experiment creator can start rounds")
    if exp.current_round >= exp.max_rounds:
        raise HTTPException(status_code=400, detail="Max rounds reached")

    exp.current_round += 1
    exp.status = ExperimentStatus.TRAINING

    federated_round = FederatedRound(
        experiment_id=exp_id,
        round_number=exp.current_round,
        status=RoundStatus.ACTIVE,
    )
    db.add(federated_round)
    await db.flush()
    await db.refresh(federated_round)
    return federated_round


@router.get("/{exp_id}/rounds", response_model=list[FederatedRoundResponse])
async def list_rounds(
    exp_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(FederatedRound)
        .where(FederatedRound.experiment_id == exp_id)
        .order_by(FederatedRound.round_number)
    )
    return result.scalars().all()


# ─── Submissions ─────────────────────────────────────────────────────────────
@router.post("/{exp_id}/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_model(
    exp_id: UUID,
    body: SubmissionCreateRequest,
    current_user: Annotated[User, Depends(get_current_verified_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    exp = await db.get(Experiment, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp.status not in (ExperimentStatus.TRAINING, ExperimentStatus.RECRUITING):
        raise HTTPException(status_code=400, detail="Experiment is not accepting submissions")

    # Get active round
    result = await db.execute(
        select(FederatedRound)
        .where(FederatedRound.experiment_id == exp_id, FederatedRound.status == RoundStatus.ACTIVE)
        .order_by(FederatedRound.round_number.desc())
        .limit(1)
    )
    active_round = result.scalar_one_or_none()

    # Compute data quality score
    dq_score = compute_data_quality(body)

    submission = ModelSubmission(
        experiment_id=exp_id,
        round_id=active_round.id if active_round else None,
        submitter_id=current_user.id,
        local_accuracy=body.local_accuracy,
        local_loss=body.local_loss,
        local_val_accuracy=body.local_val_accuracy,
        training_samples=body.training_samples,
        model_metadata=body.model_metadata,
        data_quality_score=dq_score,
        status=SubmissionStatus.PENDING,
    )
    db.add(submission)
    await db.flush()
    await db.refresh(submission)

    # Queue async aggregation
    celery_app.send_task(
        "backend.tasks.federated.validate_and_aggregate",
        args=[str(exp_id), str(submission.id)],
    )

    log.info("Model submitted", sub_id=str(submission.id), user=current_user.username)
    return submission


@router.get("/{exp_id}/submissions", response_model=list[SubmissionResponse])
async def list_submissions(
    exp_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ModelSubmission)
        .where(ModelSubmission.experiment_id == exp_id)
        .order_by(ModelSubmission.created_at.desc())
    )
    return result.scalars().all()


# Fix missing import
from backend.api.deps import get_current_verified_user
