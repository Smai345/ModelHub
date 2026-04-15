"""
Pydantic schemas for User endpoints.
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str
    full_name: str
    department: Optional[str] = None
    institution: str = "IIT Guwahati"
    
    class Config:
        from_attributes = True


class UserPublic(UserBase):
    """Public user information."""
    id: UUID
    role: str
    trust_score: float
    total_contributions: int
    avg_model_accuracy: float
    data_quality_score: float
    created_at: datetime


class UserUpdateRequest(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    department: Optional[str] = None
    opt_in_data_sharing: Optional[bool] = None
    opt_in_federated: Optional[bool] = None


class PasswordChangeRequest(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class LoginRequest(BaseModel):
    """Schema for login."""
    email: EmailStr
    password: str
