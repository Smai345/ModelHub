"""
Automated Data Quality Scoring.

Scores each submission on:
  - Completeness (training_samples vs expected minimum)
  - Accuracy plausibility (local_acc vs val_acc gap)
  - Loss sanity (not nan/inf, reasonable range)
  - Metadata richness

Final score ∈ [0, 1].
"""
from __future__ import annotations
import math
from backend.api.schemas.experiment import SubmissionCreateRequest


def compute_data_quality(submission: SubmissionCreateRequest) -> float:
    """Return a data quality score in [0.0, 1.0]."""
    scores: list[float] = []

    # 1. Completeness: reward more training samples (log scale, 1000+ = full score)
    completeness = min(math.log1p(submission.training_samples) / math.log1p(1000), 1.0)
    scores.append(completeness)

    # 2. Accuracy/validation gap: large gap = potential overfitting / bad data
    acc_gap = abs(submission.local_accuracy - submission.local_val_accuracy)
    gap_score = max(0.0, 1.0 - acc_gap * 2)  # penalize gap > 0.5
    scores.append(gap_score)

    # 3. Loss sanity
    loss = submission.local_loss
    if math.isnan(loss) or math.isinf(loss) or loss <= 0:
        loss_score = 0.0
    elif loss < 0.1:
        loss_score = 1.0
    elif loss < 1.0:
        loss_score = 1.0 - (loss - 0.1) / 0.9 * 0.3  # 0.7–1.0
    elif loss < 5.0:
        loss_score = 0.7 - (loss - 1.0) / 4.0 * 0.4  # 0.3–0.7
    else:
        loss_score = 0.1
    scores.append(loss_score)

    # 4. Metadata richness (optional bonus)
    meta = submission.model_metadata or {}
    meta_score = min(len(meta) / 5, 1.0)  # up to 5 keys = full bonus
    scores.append(meta_score * 0.5 + 0.5)  # floor at 0.5

    # Weighted average
    weights = [0.35, 0.30, 0.25, 0.10]
    final = sum(s * w for s, w in zip(scores, weights))
    return round(min(max(final, 0.0), 1.0), 4)


def compute_label_noise_estimate(class_distribution: dict[str, int]) -> float:
    """
    Estimate label noise from class distribution entropy.
    Perfectly uniform = 0 noise estimate. Heavily skewed = higher noise estimate.
    """
    if not class_distribution:
        return 0.5  # unknown

    counts = list(class_distribution.values())
    total = sum(counts) or 1
    probs = [c / total for c in counts]
    n = len(probs)
    if n <= 1:
        return 0.0

    max_entropy = math.log(n)
    entropy = -sum(p * math.log(p + 1e-9) for p in probs)
    normalized = entropy / max_entropy  # 1 = uniform, 0 = all one class

    # Skew = 1 - normalized; treat extreme skew as potential noise
    skew = 1.0 - normalized
    return round(min(skew * 0.6, 1.0), 4)
