"""
User ORM model.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Float, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

from backend.db.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher"
    PARTICIPANT = "participant"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), default=UserRole.PARTICIPANT, nullable=False
    )
    department: Mapped[str] = mapped_column(String(200), nullable=True)
    institution: Mapped[str] = mapped_column(String(200), default="IIT Guwahati")

    # Trust & contribution metrics
    trust_score: Mapped[float] = mapped_column(Float, default=0.5)
    total_contributions: Mapped[int] = mapped_column(Integer, default=0)
    total_rounds_participated: Mapped[int] = mapped_column(Integer, default=0)
    avg_model_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    data_quality_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Federated learning opt-ins
    opt_in_data_sharing: Mapped[bool] = mapped_column(Boolean, default=False)
    opt_in_federated: Mapped[bool] = mapped_column(Boolean, default=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    experiments = relationship("Experiment", back_populates="creator", lazy="selectin")
    model_submissions = relationship("ModelSubmission", back_populates="submitter", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
