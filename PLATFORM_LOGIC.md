# Platform Logic & How It Works

## Table of Contents
1. [Overview](#overview)
2. [Training Flow](#training-flow)
3. [Data Quality Evaluation](#data-quality-evaluation)
4. [Smart Aggregation Algorithm](#smart-aggregation-algorithm)
5. [Leaderboard System](#leaderboard-system)
6. [Example Walkthrough](#example-walkthrough)
7. [Why This Matters](#why-this-matters)

---

## Overview

The IITG ML Platform is a collaborative federated learning system enabling multiple participants to contribute to model training while maintaining data privacy, ensuring high-quality contributions, incentivizing data sharing, and creating fair rankings.

Key Innovation: Instead of treating all contributions equally, the platform intelligently weights each participant's model based on data quality and accuracy.

---

## Training Flow

### Phase 1: Experiment Setup
When a researcher creates a new experiment, they define the model architecture, training configuration (learning rate, batch size, epochs), minimum requirements (participant count, max rounds), aggregation strategy (fedavg_weighted by default), and quality thresholds.

### Phase 2: Participant Recruitment
Participants join by downloading the experiment model, reviewing training guidelines, accepting terms with opt-in data sharing, and accessing training resources.

### Phase 3: Local Training
Each participant independently trains on their own data, producing trained model weights, accuracy metrics, sample counts, training time, and hardware specifications.

### Phase 4: Model Submission
Participants upload their submission including model ID, accuracy achieved, training samples count, model size, and status tracking (PENDING → VALIDATING).

---

## Data Quality Evaluation

When a participant submits their model, the platform runs five quality checks:

### 1. Statistical Distribution Check
Analyzes data distribution through mean, standard deviation, skewness, outlier detection (beyond 3 standard deviations), class balance, and sample diversity. Quality scores range from 1.0 (perfect distribution) to 0.0 (severely skewed).

### 2. Duplicate Detection
Identifies redundant samples using hash-based detection, cosine similarity for near-duplicates, and feature variance analysis. Each duplicate reduces the score by 0.05, near-duplicates by 0.02.

### 3. Corruption Detection
Checks for corrupted data including missing values, invalid data types, out-of-range values, and NaN/Inf detection. Quality penalty: (corrupted_ratio × 0.10).

### 4. Sample Diversity Check
Measures feature variance to ensure diversity. Low variance features (< 0.01) are flagged. High diversity adds 0.15 bonus, low diversity incurs 0.20 penalty.

### 5. Temporal Pattern Check
For time-series data, checks trend consistency, seasonal patterns, and anomaly frequency to generate quality confidence intervals.

### Quality Score Calculation

The final quality score weights each component:

```python
base_score = 1.0
base_score -= (1.0 - distribution_score) × 0.25
base_score -= (duplicate_ratio × 0.15)
base_score -= (corruption_ratio × 0.25)

if diversity_score < 0.5:
    base_score -= 0.20
elif diversity_score > 0.8:
    base_score += 0.10

final_score = max(0.0, min(1.0, base_score))
```

Example: Base Score 1.00 → Distribution Penalty -0.05 (0.95) → Duplication -0.08 (0.87) → Corruption -0.02 (0.85) → Diversity Bonus +0.10 = Final Quality Score 0.95

---

## Smart Aggregation Algorithm

### Traditional Approach: Naive Averaging
Simple averaging: `Final_Model = (Model_A + Model_B + Model_C) / 3`

Problem: Poor quality data significantly drags down aggregate performance.

### Smart Approach: Quality-Weighted FedAvg

Weight calculation: `Weight_i = Accuracy_i × Data_Quality_i × Trust_Score_i`

Example with three participants:

**Participant A:** Accuracy 92%, Data Quality 0.95, Trust Score 0.90
- Weight_A = 0.92 × 0.95 × 0.90 = 0.786

**Participant B:** Accuracy 89%, Data Quality 0.60, Trust Score 0.85
- Weight_B = 0.89 × 0.60 × 0.85 = 0.453

**Participant C:** Accuracy 94%, Data Quality 0.98, Trust Score 0.95
- Weight_C = 0.94 × 0.98 × 0.95 = 0.876

Normalizing weights (Total = 2.115):
- Weight_A = 0.372 (37.2%)
- Weight_B = 0.214 (21.4%)
- Weight_C = 0.414 (41.4%)

Weighted aggregation: `Final_Model_Layer_i = (0.372 × Model_A_Layer_i) + (0.214 × Model_B_Layer_i) + (0.414 × Model_C_Layer_i)`

Result: Participant C's model has most influence, B has least, creating optimal aggregate.

### Result Comparison

Traditional Average: 91.7% accuracy (influenced by poor quality data)
Quality-Weighted Average: 93.2% accuracy (influenced by high quality data)

---

## Leaderboard System

### Ranking Criteria

Leaderboard Score = Contribution_Score × Reliability_Multiplier

Where:
- Contribution_Score = Sum of model weights across rounds
- Reliability_Multiplier = Consistency_Score × Trust_Score × Participation_Rate
- Consistency_Score = 1 - (standard_deviation / mean accuracy)

### Leaderboard Example

| Rank | Participant | Avg Accuracy | Data Quality | Trust | Contribution |
|------|-------------|--------------|--------------|-------|--------------|
| 1    | Participant C | 94.0% | 0.98 | 0.95 | 12.5 |
| 2    | Participant A | 92.0% | 0.95 | 0.90 | 10.2 |
| 3    | Participant B | 89.0% | 0.60 | 0.85 | 5.8 |

Badges: C = Data Quality Expert, A = Consistent Performer, B = Improving

### Trust Score Dynamics

- Data Quality Improves: trust_score += 0.05 (max 1.0)
- Data Quality Degrades: trust_score -= 0.10 (min 0.0)
- Consistent Performance: trust_score += 0.02 per round
- Missing Submission: trust_score -= 0.05

---

## Example Walkthrough

### Round 1: Initial Setup

Three participants with 5000, 3000, and 8000 samples respectively.

Submissions: A = 92% accuracy, B = 89%, C = 94%
Quality: A = 0.95, B = 0.60, C = 0.98
Trust (all new): 0.50

Weights: A = 0.437, B = 0.267, C = 0.461
Final accuracy: 92.1%
Ranking: C (best quality), A (good quality), B (needs improvement)

### Round 2: Improvement Phase

Using Round 1 aggregate as base model.

Submissions: A = 93%, B = 91%, C = 95% (all improved)
Quality: A = 0.96, B = 0.75, C = 0.99 (improved)
Trust: A = 0.60, B = 0.55, C = 0.65 (increased)

Weights: A = 0.537, B = 0.376, C = 0.612
Final accuracy: 93.8% (improvement from 92.1%)
Recognition: C = Data Quality Expert, B = Improving Contributor, A = Reliable Partner

---

## Why This Matters

### The Problem

In a 100-participant scenario with 80% high-quality data and 20% poor-quality data:

Without quality scoring: Simple averaging pulls down quality by ~20%, result = 88% accuracy
With quality scoring: Intelligent weighting preserves quality, result = 92% accuracy

### Key Benefits

1. Fair Contribution: Better data receives more influence
2. Motivation: Incentivizes quality data sharing
3. Model Quality: Aggregate improves faster
4. Transparency: Clear ranking explains participant positions
5. Continuous Improvement: Feedback loop encourages better practices

---

## Technical Implementation

### Core Algorithms Location

```
backend/
├── services/
│   ├── aggregation.py        # Weighted aggregation logic
│   └── data_quality.py       # Quality scoring algorithm
├── api/
│   ├── models/
│   │   ├── leaderboard.py    # Leaderboard data models
│   │   └── experiment.py     # Experiment tracking
│   └── routes/
│       ├── experiments.py    # Submission handling
│       └── leaderboard.py    # Rankings API
└── core/
    └── config.py             # Quality thresholds
```

### Data Flow

Participant Submission → Validation → Data Quality Scoring → Weight Calculation → Aggregation → Leaderboard Update → Participant Notification

---

## Conclusion

The IITG ML Platform implements intelligent collaborative learning where data quality is automatically evaluated, weights are determined by contribution quality, best contributors are recognized, and models improve iteratively. This creates a sustainable federated learning ecosystem where participants benefit from higher quality aggregates and the community benefits from reliable contributors.
# Platform Logic & How It Works

## Table of Contents
1. [Overview](#overview)
2. [Training Flow](#training-flow)
3. [Data Quality Evaluation](#data-quality-evaluation)
4. [Smart Aggregation Algorithm](#smart-aggregation-algorithm)
5. [Leaderboard System](#leaderboard-system)
6. [Example Walkthrough](#example-walkthrough)
7. [Why This Matters](#why-this-matters)

---

## Overview

The IITG ML Platform is a collaborative federated learning system that enables multiple participants to contribute to model training while maintaining data privacy, ensuring high-quality contributions, incentivizing good data sharing, and creating fair rankings.

Key Innovation: Instead of treating all contributions equally, the platform intelligently weights each participant's model based on data quality and accuracy.

---

## Training Flow

### Phase 1: Experiment Setup
When a researcher creates a new experiment, they define the model architecture, training configuration (learning rate, batch size, epochs), requirements (minimum participants, max rounds), aggregation strategy (fedavg_weighted by default), and quality thresholds.

### Phase 2: Participant Recruitment
Once the experiment is posted, participants can join by downloading the experiment model, reviewing training guidelines, accepting terms and opting into data sharing, and accessing training resources.

### Phase 3: Local Training
Each participant independently trains on their own data and returns the trained model weights, training accuracy, number of training samples, training time, and hardware specifications.

### Phase 4: Model Submission
The participant uploads their submission which includes a model ID, accuracy achieved, number of training samples, model size, and status tracking.

---

## Data Quality Evaluation

### How Quality Scoring Works

When a participant submits their model and data, the platform runs five quality checks:

### 1. Statistical Distribution Check
The system analyzes data distribution by examining mean, standard deviation, skewness, outlier detection (values beyond 3 standard deviations), class balance, and overall sample diversity. The quality score ranges from 0.0 to 1.0: 1.0 for perfect distribution, 0.7 for minor imbalances, 0.3 for heavy class imbalance, and 0.0 for severely skewed data.

### 2. Duplicate Detection
The system identifies redundant samples using hash-based duplicate detection, cosine similarity for near-duplicates, and feature variance analysis. Each duplicate reduces the quality score by 0.05, and near-duplicates reduce it by 0.02.

### 3. Corruption Detection
The system checks for corrupted or invalid data including missing values ratio, invalid data types, out-of-range values, and NaN/Inf detection. The quality penalty is (corrupted_ratio × 0.10).

### 4. Sample Diversity Check
The system measures feature variance to ensure diversity, flagging low variance features (< 0.01), detecting excessive repeat patterns, and identifying data augmentation indicators. High diversity adds a 0.15 bonus, while low diversity incurs a 0.20 penalty.

### 5. Temporal Pattern Check
For time-series data, the system checks trend consistency, seasonal patterns, and anomaly frequency to generate confidence intervals for quality estimates.

### Quality Score Calculation

The final quality score is calculated as::

```python
base_score = 1.0
base_score -= (1.0 - distribution_score) × 0.25
base_score -= (duplicate_ratio × 0.15)
base_score -= (corruption_ratio × 0.25)

if diversity_score < 0.5:
    base_score -= 0.20
elif diversity_score > 0.8:
    base_score += 0.10

final_score = max(0.0, min(1.0, base_score))
```

Example output:
- Base Score: 1.00
- Distribution Penalty: -0.05 → 0.95
- Duplication Penalty: -0.08 → 0.87
- Corruption Penalty: -0.02 → 0.85
- Diversity Bonus: +0.10 → 0.95
- Final Quality Score: 0.95

---

## Smart Aggregation Algorithm

### Traditional Approach: Naive Averaging

The simple method is: `Final_Model = (Model_A + Model_B + Model_C) / 3`

The problem with this approach is that poor quality data significantly drags down the aggregate model's performance.

### Smart Approach: Quality-Weighted FedAvg

The platform uses intelligent weighting based on three factors: `Weight_i = Accuracy_i × Data_Quality_i × Trust_Score_i`

**Example with three participants:**

Participant A: Accuracy 92%, Data Quality 0.95, Trust Score 0.90
- Weight_A = 0.92 × 0.95 × 0.90 = 0.786

Participant B: Accuracy 89%, Data Quality 0.60, Trust Score 0.85
- Weight_B = 0.89 × 0.60 × 0.85 = 0.453

Participant C: Accuracy 94%, Data Quality 0.98, Trust Score 0.95
- Weight_C = 0.94 × 0.98 × 0.95 = 0.876

**Normalizing weights:**

Total_Weight = 0.786 + 0.453 + 0.876 = 2.115

Normalized:
- Weight_A = 0.786 / 2.115 = 0.372 (37.2%)
- Weight_B = 0.453 / 2.115 = 0.214 (21.4%)
- Weight_C = 0.876 / 2.115 = 0.414 (41.4%)

**Weighted aggregation:**

For each layer: `Final_Model_Layer_i = (0.372 × Model_A_Layer_i) + (0.214 × Model_B_Layer_i) + (0.414 × Model_C_Layer_i)`

Participant C's model has the most influence (best quality), Participant B has the least influence (poor quality), and the final aggregate balances accuracy and quality.

**Result comparison:**

Traditional Average: 91.7% accuracy (influenced by poor quality data)
Quality-Weighted Average: 93.2% accuracy (influenced by high quality data)

---

## Leaderboard System

### Ranking Criteria

The leaderboard score is calculated as: `Leaderboard Score = Contribution_Score × Reliability_Multiplier`

Where:
- Contribution_Score = Sum of all model weights across rounds
- Reliability_Multiplier = Consistency_Score × Trust_Score × Participation_Rate
- Consistency_Score = 1 - (standard_deviation / mean accuracy)

### Leaderboard Example

| Rank | Participant | Avg Accuracy | Data Quality | Trust | Contribution |
|------|-------------|--------------|--------------|-------|----------|
| 1 | Participant C | 94.0% | 0.98 | 0.95 | 12.5 |
| 2 | Participant A | 92.0% | 0.95 | 0.90 | 10.2 |
| 3 | Participant B | 89.0% | 0.60 | 0.85 | 5.8 |

Badges earned:
- Participant C: Data Quality Expert
- Participant A: Consistent Performer
- Participant B: Improving

### Trust Score Dynamics

The trust score evolves based on participant behavior:

- If Data Quality Improves: trust_score += 0.05 (max 1.0)
- If Data Quality Degrades: trust_score -= 0.10 (min 0.0)
- For Consistent Performance: trust_score += 0.02 per round
- For Missing Submissions: trust_score -= 0.05

---

## Example Walkthrough

### Round 1: Initial Setup

Three participants launch training with 5000, 3000, and 8000 samples respectively.

Submissions: A: 92% accuracy, B: 89% accuracy, C: 94% accuracy

Quality Assessment: A: Quality = 0.95, Trust = 0.50 (new user); B: Quality = 0.60, Trust = 0.50; C: Quality = 0.98, Trust = 0.50

Weight Calculation: A: 0.437, B: 0.267, C: 0.461

Aggregate Model: 0.437A + 0.267B + 0.461C with Final Model Accuracy: 92.1%

Leaderboard ranking: C (best quality), A (good quality), B (needs improvement)

### Round 2: Improvement Phase

The aggregate model from Round 1 is released. Participants fine-tune using this better base model.

New Submissions: A: 93% accuracy, B: 91% accuracy, C: 95% accuracy (all improved)

Quality Assessment: A: Quality = 0.96, Trust = 0.60; B: Quality = 0.75, Trust = 0.55; C: Quality = 0.99, Trust = 0.65

Weight Calculation: A: 0.537, B: 0.376, C: 0.612

Aggregate Model Accuracy: 93.8% (improved from 92.1%)

Recognition: C: Data Quality Expert, B: Improving Contributor, A: Reliable Partner

---

## Why This Matters

### Problem Solved ✅

**Without Quality Scoring:**
```
Scenario: 100 participants join
├── 80% have GOOD data (high quality) ✅
├── 20% have BAD data (duplicates, corruption) ❌
└── Result: Simple average pulls down quality by ~20%
   Final model accuracy: 88% (degraded)
```

**With Quality Scoring:**
```
Scenario: Same 100 participants
├── 80% GOOD data get HIGH weight ✅
├── 20% BAD data get LOW weight ❌
└── Result: Intelligent weighting preserves quality
   Final model accuracy: 92% (optimized!)
```

### Key Benefits

1. **Fair Contribution**: Better data = More influence
2. **Motivation**: Incentivizes quality data sharing
3. **Model Quality**: Aggregate improves faster
4. **Transparency**: Clear ranking explains why participants rank where they do
5. **Continuous Improvement**: Feedback loop drives better participation

---

## Technical Implementation

### Core Algorithms Location

```
backend/
├── services/
│   ├── aggregation.py        # Smart aggregation logic
│   └── data_quality.py       # Quality scoring algorithm
├── api/
│   ├── models/
│   │   ├── leaderboard.py    # Leaderboard data models
│   │   └── experiment.py     # Experiment tracking
│   └── routes/
│       ├── experiments.py    # Submission handling
│       └── leaderboard.py    # Rankings API
└── core/
    └── config.py             # Quality thresholds
```

### Data Flow

```
Participant Submission
        ↓
    Validation
        ↓
    Data Quality Scoring ← [Services/data_quality.py]
        ↓
    Weight Calculation
        ↓
    Aggregation ← [Services/aggregation.py]
        ↓
    Leaderboard Update ← [Models/leaderboard.py]
        ↓
    Participant Notification
```

---

## Conclusion

The IITG ML Platform implements intelligent collaborative learning where data quality is automatically evaluated, weights are determined by contribution quality, best contributors are recognized, models improve with each round, and the incentive structure rewards good behavior. This creates a sustainable ecosystem for federated learning within the IITG network.
