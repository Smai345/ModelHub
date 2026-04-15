"""
IITG ML Platform — FastAPI Application Entry Point
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.db.database import engine, Base
from backend.api.routes import auth_router, users_router, experiments_router, leaderboard_router, admin_router

log = structlog.get_logger()

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting IITG ML Platform", env=settings.APP_ENV)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables ready")
    yield
    log.info("Shutting down IITG ML Platform")
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        description="Federated Learning & Collaborative ML Platform for IIT Guwahati",
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware ────────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS + ["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(auth_router,        prefix="/api/v1/auth",         tags=["Auth"])
    app.include_router(users_router,       prefix="/api/v1/users",        tags=["Users"])
    app.include_router(experiments_router, prefix="/api/v1/experiments",  tags=["Experiments"])
    app.include_router(leaderboard_router, prefix="/api/v1/leaderboard",  tags=["Leaderboard"])
    app.include_router(admin_router,       prefix="/api/v1/admin",        tags=["Admin"])

    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}

    return app


app = create_app()
