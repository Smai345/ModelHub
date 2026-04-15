"""
Authentication routes: register, login, refresh, logout.
"""
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db
from backend.core.security import hash_password, create_jwt_tokens
from backend.api.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from backend.api.models.user import User

log = structlog.get_logger()
router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """Register a new user."""
    existing = await db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    user = User(
        email=body.email,
        username=body.username,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        department=body.department,
        institution=body.institution,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    tokens = create_jwt_tokens(user_id=user.id)
    log.info("User registered", user_id=user.id, email=user.email)
    
    return tokens


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """Login with email and password."""
    user = await db.scalar(select(User).where(User.email == body.email))
    if not user or not user.verify_password(body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    tokens = create_jwt_tokens(user_id=user.id)
    log.info("User logged in", user_id=user.id)
    
    return tokens
