"""
User routes: /me, /me/update, /me/password, /{username}
"""
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.api.deps import get_current_user, get_current_verified_user
from backend.api.models.user import User
from backend.api.schemas.auth import UserBase, UserPublic, UserUpdateRequest, PasswordChangeRequest
from backend.core.security import verify_password, hash_password

log = structlog.get_logger()
router = APIRouter()


@router.get("/me", response_model=UserBase)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.patch("/me", response_model=UserBase)
async def update_me(
    body: UserUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if body.full_name is not None:
        current_user.full_name = body.full_name
    if body.department is not None:
        current_user.department = body.department
    if body.opt_in_data_sharing is not None:
        current_user.opt_in_data_sharing = body.opt_in_data_sharing
    if body.opt_in_federated is not None:
        current_user.opt_in_federated = body.opt_in_federated

    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(body.new_password)
    await db.flush()


@router.get("/{username}", response_model=UserPublic)
async def get_user_profile(
    username: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.username == username, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
