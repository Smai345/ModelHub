"""
Model Submission and Leaderboard ORM models.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from backend.db.database import Base


class SubmissionStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    AGGREGATED = "aggregated"


class ModelSubmission(Base):
    __tablename__ = "model_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    round_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("federated_rounds.id"), nullable=True)
    submitter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus), default=SubmissionStatus.PENDING
    )

    # Model metrics
    local_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    local_loss: Mapped[float] = mapped_column(Float, default=999.0)
    local_val_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    training_samples: Mapped[int] = mapped_column(Integer, default=0)

    # Data quality
    data_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    data_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    data_consistency: Mapped[float] = mapped_column(Float, default=0.0)
    label_noise_estimate: Mapped[float] = mapped_column(Float, default=0.0)

    # Aggregation weight (computed by fusion engine)
    fusion_weight: Mapped[float] = mapped_column(Float, default=0.0)

    # MinIO paths
    model_artifact_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    weights_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Model metadata
    model_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    rejection_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    experiment = relationship("Experiment", back_populates="model_submissions")
    round = relationship("FederatedRound", back_populates="submissions")
    submitter = relationship("User", back_populates="model_submissions")


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    # Composite trust score (0-1)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[int] = mapped_column(Integer, default=0)

    # Score components
    accuracy_score: Mapped[float] = mapped_column(Float, default=0.0)      # 40%
    data_quality_score: Mapped[float] = mapped_column(Float, default=0.0)  # 30%
    contribution_score: Mapped[float] = mapped_column(Float, default=0.0)  # 20%
    peer_validation_score: Mapped[float] = mapped_column(Float, default=0.0)  # 10%

    # Raw stats
    total_submissions: Mapped[int] = mapped_column(Integer, default=0)
    accepted_submissions: Mapped[int] = mapped_column(Integer, default=0)
    experiments_contributed: Mapped[int] = mapped_column(Integer, default=0)
    best_local_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    avg_data_quality: Mapped[float] = mapped_column(Float, default=0.0)

    # 30-day rolling window stats
    monthly_submissions: Mapped[int] = mapped_column(Integer, default=0)
    monthly_avg_accuracy: Mapped[float] = mapped_column(Float, default=0.0)

    score_history: Mapped[list] = mapped_column(JSON, default=list)  # [{date, score}]

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    user = relationship("User")
