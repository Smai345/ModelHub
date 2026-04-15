"""
Pydantic schemas for Experiment endpoints.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ExperimentCreateRequest(BaseModel):
    """Schema for creating a new experiment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    model_architecture: Dict[str, Any] = Field(default_factory=dict)
    aggregation_strategy: str = Field(default="fedavg_weighted")
    min_participants: int = Field(default=2, ge=1)
    max_rounds: int = Field(default=10, ge=1)
    data_quality_threshold: float = Field(default=0.6, ge=0.0, le=1.0)


class ExperimentResponse(BaseModel):
    """Schema for experiment response."""
    id: UUID
    name: str
    description: Optional[str]
    creator_id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ExperimentListResponse(BaseModel):
    """Schema for experiment list response."""
    total: int
    experiments: List[ExperimentResponse]


class FederatedRoundResponse(BaseModel):
    """Schema for federated round."""
    id: UUID
    experiment_id: UUID
    round_number: int
    status: str
    aggregation_result: Optional[Dict[str, Any]]


class SubmissionCreateRequest(BaseModel):
    """Schema for model submission."""
    experiment_id: UUID
    round_id: Optional[UUID] = None
    accuracy: float = Field(..., ge=0.0, le=1.0)
    training_samples: int = Field(..., ge=1)
    model_weights_path: Optional[str] = None


class SubmissionResponse(BaseModel):
    """Schema for submission response."""
    id: UUID
    experiment_id: UUID
    submitter_id: UUID
    accuracy: float
    training_samples: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_experiments: int
    active_experiments: int
    total_participants: int
    total_submissions: int
    global_best_accuracy: float
    avg_trust_score: float
    experiments_this_week: int
    submissions_today: int
