"""Pydantic schemas for Admin endpoints."""
from typing import Optional
from pydantic import BaseModel
from backend.api.models.user import UserRole


class AdminUserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    trust_score: Optional[float] = None


class SystemStatsResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    total_experiments: int
    total_submissions: int
