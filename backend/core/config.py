"""
Core configuration using Pydantic Settings.
All values loaded from environment / .env file.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "IITG ML Platform"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_MODELS: str = "ml-models"
    MINIO_BUCKET_DATASETS: str = "ml-datasets"
    MINIO_SECURE: bool = False

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"
    MLFLOW_EXPERIMENT_NAME: str = "iitg_federated_learning"

    # Federated Learning
    FL_MIN_PARTICIPANTS: int = 2
    FL_MAX_ROUNDS: int = 100
    FL_CONVERGENCE_THRESHOLD: float = 0.001
    FL_DIFFERENTIAL_PRIVACY_EPSILON: float = 1.0
    FL_NOISE_MULTIPLIER: float = 0.1

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://localhost:80"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
