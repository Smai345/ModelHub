"""
Initialize database tables. Run once at startup.
Usage: python -m backend.db.init_db
"""
import asyncio
import structlog

from backend.db.database import engine, Base
from backend.api.models import user, experiment, model_submission, leaderboard  # noqa: F401

log = structlog.get_logger()


async def init_db() -> None:
    log.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
