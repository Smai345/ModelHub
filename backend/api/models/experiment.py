"""
Experiment and Federated Learning Round ORM models.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, JSON, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from backend.db.database import Base


class ExperimentStatus(str, enum.Enum):
    CREATED = "created"
    RECRUITING = "recruiting"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RoundStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[ExperimentStatus] = mapped_column(
        SAEnum(ExperimentStatus), default=ExperimentStatus.CREATED
    )

    # FL configuration
    model_architecture: Mapped[dict] = mapped_column(JSON, default=dict)
    aggregation_strategy: Mapped[str] = mapped_column(String(50), default="fedavg_weighted")
    min_participants: Mapped[int] = mapped_column(Integer, default=2)
    max_rounds: Mapped[int] = mapped_column(Integer, default=10)
    current_round: Mapped[int] = mapped_column(Integer, default=0)
    target_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Global model metrics
    global_model_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    global_model_loss: Mapped[float] = mapped_column(Float, default=999.0)
    best_accuracy: Mapped[float] = mapped_column(Float, default=0.0)

    # Privacy settings
    differential_privacy: Mapped[bool] = mapped_column(Boolean, default=False)
    noise_multiplier: Mapped[float] = mapped_column(Float, default=0.1)

    # MLflow
    mlflow_experiment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mlflow_run_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Global model artifact path in MinIO
    global_model_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", back_populates="experiments")
    rounds = relationship("FederatedRound", back_populates="experiment", cascade="all, delete-orphan")
    model_submissions = relationship("ModelSubmission", back_populates="experiment", cascade="all, delete-orphan")


class FederatedRound(Base):
    __tablename__ = "federated_rounds"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)

    status: Mapped[RoundStatus] = mapped_column(SAEnum(RoundStatus), default=RoundStatus.PENDING)

    # Aggregation results
    aggregated_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    aggregated_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    participants_count: Mapped[int] = mapped_column(Integer, default=0)
    aggregation_weights: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    experiment = relationship("Experiment", back_populates="rounds")
    submissions = relationship("ModelSubmission", back_populates="round")
