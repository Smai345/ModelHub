"""
Celery tasks for federated learning pipeline.
"""
import asyncio
import structlog
from uuid import UUID
from datetime import datetime, timezone, timedelta

from backend.tasks.celery_app import celery_app

log = structlog.get_logger()


def _run_async(coro):
    """Run async coroutine from sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="backend.tasks.federated.validate_and_aggregate", bind=True, max_retries=3)
def validate_and_aggregate(self, experiment_id: str, submission_id: str):
    """
    1. Validate submitted model metrics.
    2. Accept or reject submission.
    3. Trigger aggregation if enough submissions in the round.
    """
    async def _inner():
        from backend.db.database import AsyncSessionLocal
        from backend.api.models.leaderboard import ModelSubmission, SubmissionStatus
        from backend.api.models.experiment import Experiment, FederatedRound, RoundStatus
        from backend.services.aggregation import run_federated_aggregation
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            sub = await db.get(ModelSubmission, UUID(submission_id))
            if not sub:
                log.error("Submission not found", sub_id=submission_id)
                return

            # Simple validation rules
            if sub.local_accuracy < 0.01 or sub.local_accuracy > 1.0:
                sub.status = SubmissionStatus.REJECTED
                sub.rejection_reason = "local_accuracy out of valid range"
                await db.commit()
                return

            if sub.training_samples < 1:
                sub.status = SubmissionStatus.REJECTED
                sub.rejection_reason = "training_samples must be >= 1"
                await db.commit()
                return

            sub.status = SubmissionStatus.ACCEPTED
            await db.flush()

            # Check if round has enough submissions to aggregate
            if not sub.round_id:
                await db.commit()
                return

            accepted_count = await db.scalar(
                select(__import__('sqlalchemy').func.count(ModelSubmission.id)).where(
                    ModelSubmission.round_id == sub.round_id,
                    ModelSubmission.status == SubmissionStatus.ACCEPTED,
                )
            )
            exp = await db.get(Experiment, UUID(experiment_id))
            if exp and accepted_count >= exp.min_participants:
                await run_federated_aggregation(db, UUID(experiment_id), sub.round_id)

            await db.commit()
            log.info("Submission validated", sub_id=submission_id, status="accepted")

    try:
        _run_async(_inner())
    except Exception as exc:
        log.error("validate_and_aggregate failed", error=str(exc))
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(name="backend.tasks.federated.cleanup_stale_rounds")
def cleanup_stale_rounds():
    """Mark rounds stuck in ACTIVE for > 24h as FAILED."""
    async def _inner():
        from backend.db.database import AsyncSessionLocal
        from backend.api.models.experiment import FederatedRound, RoundStatus
        from sqlalchemy import select, update

        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(FederatedRound).where(
                    FederatedRound.status == RoundStatus.ACTIVE,
                    FederatedRound.created_at < cutoff,
                )
            )
            stale = result.scalars().all()
            for r in stale:
                r.status = RoundStatus.FAILED
                log.warning("Marked stale round as failed", round_id=str(r.id))
            await db.commit()
            log.info("Stale round cleanup done", count=len(stale))

    _run_async(_inner())
