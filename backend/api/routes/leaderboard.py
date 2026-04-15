"""
Leaderboard routes: list, get, statistics, rankings.
"""
from typing import Annotated, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from backend.db.database import get_db
from backend.api.deps import get_current_user
from backend.api.models.user import User
from backend.api.models.leaderboard import LeaderboardEntry, ModelSubmission

log = structlog.get_logger()
router = APIRouter()


@router.get("/global")
async def get_global_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get global leaderboard ranked by accuracy and trust."""
    query = select(LeaderboardEntry).order_by(
        desc(LeaderboardEntry.average_accuracy),
        desc(LeaderboardEntry.trust_score),
    )
    
    entries = await db.scalars(query.offset(offset).limit(limit))
    return list(entries)


@router.get("/user/{user_id}")
async def get_user_leaderboard_stats(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get leaderboard entry for a specific user."""
    entry = await db.scalar(
        select(LeaderboardEntry).where(LeaderboardEntry.user_id == user_id)
    )
    if not entry:
        raise ValueError(f"No leaderboard entry for user {user_id}")
    return entry
