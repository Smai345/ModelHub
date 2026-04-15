"""
Admin routes: user management, system stats, moderation.
"""
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.db.database import get_db
from backend.api.deps import get_current_admin
from backend.api.models.user import User
from backend.api.models.experiment import Experiment
from backend.api.models.leaderboard import ModelSubmission

log = structlog.get_logger()
router = APIRouter()


@router.get("/stats")
async def get_system_stats(
    current_user: Annotated[User, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get system-wide statistics (admin only)."""
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    total_experiments = await db.scalar(select(func.count(Experiment.id)))
    total_submissions = await db.scalar(select(func.count(ModelSubmission.id)))
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_experiments": total_experiments,
        "total_submissions": total_submissions,
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: UUID,
    role: str = None,
    is_active: bool = None,
    trust_score: float = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_admin)] = None,
):
    """Update user (admin only)."""
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if role:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    if trust_score is not None:
        user.trust_score = trust_score
    
    await db.flush()
    log.info("User updated by admin", user_id=user_id, admin_id=current_user.id)
    
    return {"status": "updated", "user_id": user_id}
