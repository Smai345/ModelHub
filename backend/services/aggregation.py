"""
Smart Model Fusion / Federated Aggregation Service.

Implements:
  - FedAvg (standard weighted by training_samples)
  - Trust-weighted FedAvg (accuracy × data_quality × trust_score)
  - Contribution score update for leaderboard
"""
from __future__ import annotations

import structlog
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.api.models.leaderboard import ModelSubmission, SubmissionStatus, LeaderboardEntry
from backend.api.models.experiment import Experiment, FederatedRound, RoundStatus, ExperimentStatus
from backend.api.models.user import User

log = structlog.get_logger()


def _compute_fusion_weights(submissions: Sequence[ModelSubmission]) -> dict[UUID, float]:
    """
    Trust-weighted aggregation:
      raw_weight = training_samples × local_accuracy × data_quality_score
    Then normalize to sum=1.
    """
    raw: dict[UUID, float] = {}
    for sub in submissions:
        raw[sub.id] = (
            sub.training_samples
            * max(sub.local_accuracy, 0.01)
            * max(sub.data_quality_score, 0.01)
        )

    total = sum(raw.values()) or 1.0
    return {sid: w / total for sid, w in raw.items()}


async def run_federated_aggregation(
    db: AsyncSession,
    experiment_id: UUID,
    round_id: UUID,
) -> dict:
    """
    Aggregate accepted submissions for a given round.
    Returns aggregation metadata dict.
    """
    # Fetch submissions
    result = await db.execute(
        select(ModelSubmission).where(
            ModelSubmission.experiment_id == experiment_id,
            ModelSubmission.round_id == round_id,
            ModelSubmission.status == SubmissionStatus.ACCEPTED,
        )
    )
    submissions = result.scalars().all()

    if not submissions:
        log.warning("No accepted submissions to aggregate", exp_id=str(experiment_id))
        return {"status": "skipped", "reason": "no_accepted_submissions"}

    weights = _compute_fusion_weights(submissions)

    # Weighted accuracy & loss
    agg_accuracy = sum(weights[s.id] * s.local_accuracy for s in submissions)
    agg_loss = sum(weights[s.id] * s.local_loss for s in submissions)

    # Update fusion weights on submissions
    for sub in submissions:
        sub.fusion_weight = weights[sub.id]
        sub.status = SubmissionStatus.AGGREGATED

    # Update round
    federated_round = await db.get(FederatedRound, round_id)
    if federated_round:
        federated_round.status = RoundStatus.COMPLETED
        federated_round.aggregated_accuracy = round(agg_accuracy, 6)
        federated_round.aggregated_loss = round(agg_loss, 6)
        federated_round.participants_count = len(submissions)
        federated_round.aggregation_weights = {str(k): round(v, 6) for k, v in weights.items()}
        federated_round.completed_at = datetime.now(timezone.utc)

    # Update experiment global metrics
    exp = await db.get(Experiment, experiment_id)
    if exp:
        exp.global_model_accuracy = round(agg_accuracy, 6)
        exp.global_model_loss = round(agg_loss, 6)
        if agg_accuracy > exp.best_accuracy:
            exp.best_accuracy = round(agg_accuracy, 6)
        # Check convergence / completion
        if exp.current_round >= exp.max_rounds:
            exp.status = ExperimentStatus.COMPLETED
            exp.completed_at = datetime.now(timezone.utc)

    # Update contributor leaderboard entries
    for sub in submissions:
        await _update_leaderboard(db, sub, weights[sub.id])

    await db.flush()

    log.info(
        "Aggregation complete",
        exp_id=str(experiment_id),
        round_id=str(round_id),
        participants=len(submissions),
        agg_accuracy=agg_accuracy,
    )
    return {
        "status": "ok",
        "participants": len(submissions),
        "aggregated_accuracy": agg_accuracy,
        "aggregated_loss": agg_loss,
    }


async def _update_leaderboard(db: AsyncSession, sub: ModelSubmission, fusion_weight: float):
    """Upsert leaderboard entry for the submitter."""
    result = await db.execute(
        select(LeaderboardEntry).where(LeaderboardEntry.user_id == sub.submitter_id)
    )
    entry = result.scalar_one_or_none()

    if not entry:
        entry = LeaderboardEntry(user_id=sub.submitter_id)
        db.add(entry)

    entry.total_submissions += 1
    entry.accepted_submissions += 1

    # Update accuracy score (running average)
    n = entry.accepted_submissions
    entry.accuracy_score = ((entry.accuracy_score * (n - 1)) + sub.local_accuracy) / n
    entry.avg_data_quality = ((entry.avg_data_quality * (n - 1)) + sub.data_quality_score) / n

    if sub.local_accuracy > entry.best_local_accuracy:
        entry.best_local_accuracy = sub.local_accuracy

    # Contribution score = log(total_submissions + 1) normalized to 0-1
    import math
    entry.contribution_score = min(math.log1p(entry.total_submissions) / math.log1p(100), 1.0)

    # Composite trust score: accuracy(40%) + data_quality(30%) + contribution(20%) + peer(10%)
    entry.trust_score = round(
        0.40 * entry.accuracy_score
        + 0.30 * entry.avg_data_quality
        + 0.20 * entry.contribution_score
        + 0.10 * entry.peer_validation_score,
        6,
    )

    # Append to score history
    history = entry.score_history or []
    history.append({"date": datetime.now(timezone.utc).isoformat(), "score": entry.trust_score})
    entry.score_history = history[-90:]  # keep last 90 data points
    entry.last_updated = datetime.now(timezone.utc)

    # Update user trust score
    user = await db.get(User, sub.submitter_id)
    if user:
        user.trust_score = entry.trust_score
        user.total_contributions += 1
        user.avg_model_accuracy = entry.accuracy_score
        user.data_quality_score = entry.avg_data_quality


async def rerank_leaderboard(db: AsyncSession):
    """Recompute ranks for all leaderboard entries by trust_score desc."""
    result = await db.execute(
        select(LeaderboardEntry).order_by(LeaderboardEntry.trust_score.desc())
    )
    entries = result.scalars().all()
    for rank, entry in enumerate(entries, start=1):
        entry.rank = rank
    await db.flush()
    log.info("Leaderboard reranked", total=len(entries))
