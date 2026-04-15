# IITG ML Platform - Federated Learning & Collaborative ML

A next-generation collaborative machine learning platform designed for the IITG network, featuring smart model fusion, federated learning with opt-in data sharing, a trust-based leaderboard, and real-time dashboards.

## 🎯 Key Features

### Smart Model Fusion
- **Accuracy-Weighted Aggregation**: Combines models based on their accuracy and trust scores
- **Federated Learning (FedAvg)**: Industry-standard secure aggregation protocol
- **Trust-Weighted Averaging**: Incorporates data quality and user trust metrics

### Federated Learning
- **Privacy-First Design**: Opt-in data sharing model
- **Differential Privacy**: Optional epsilon-configured privacy guarantees
- **Multi-Round Training**: Iterative model improvement across distributed participants

### Leaderboard & Rankings
- **Trust Scoring System**: Rates participants based on contributions and data quality
- **Accuracy Rankings**: Global and experiment-specific leaderboards
- **Contribution Tracking**: Automatic metrics for participation and model performance

### Real-Time Dashboard
- **Experiment Monitoring**: Live stats on active experiments and participants
- **Data Quality Scoring**: Automated assessment of submitted datasets
- **Performance Analytics**: Aggregated metrics across all experiments

### Admin & Governance
- **User Management**: Role-based access control (Admin, Researcher, Participant)
- **Experiment Moderation**: Control over experiment creation and participant acceptance
- **System Statistics**: Comprehensive platform analytics

## 🔄 How It Works

The platform enables collaborative machine learning through intelligent model aggregation and quality assessment:

### **Training Flow**
1. **Researcher** creates a federated learning experiment with model architecture and training parameters
2. **Participants** (from different departments/institutions) join the experiment
3. **Local Training**: Each participant trains the model on their own dataset locally
4. **Model Submission**: Participants upload trained model weights + accuracy metrics

### **Quality Evaluation** ⭐ Key Differentiator
The platform automatically evaluates each submission:
- **Data Quality Score (0-1)**: Checks for data diversity, duplicates, corruption, and statistical distribution
- **Trust Score (0-1)**: Historical reliability based on past contributions
- **Contribution Weight**: Calculated as `Accuracy × Data_Quality × Trust_Score`

### **Smart Aggregation** (Model Fusion)
Instead of simple averaging, the platform uses **weighted aggregation**:
```
Final_Model = Σ(Weight_i × Model_i) / Σ(Weight_i)
```
- Good quality datasets have MORE influence
- Poor quality datasets have LESS influence
- Ensures aggregate model is optimal and robust

### **Iterative Improvement**
- Platform releases improved aggregate model
- Participants download and retrain for next round
- Accuracy improves progressively across multiple rounds

### **Leaderboard & Recognition**
- Global rankings based on accuracy, data quality, and contributions
- Trust scores increase for reliable contributors
- Top contributors get recognized as "Data Quality Experts"

**Result**: A collaborative ecosystem where good data is incentivized and model quality continuously improves.

See [PLATFORM_LOGIC.md](PLATFORM_LOGIC.md) for detailed technical explanation.

## 🏗️ Architecture

```
IITG ML Platform
├── Frontend (Streamlit)
│   └── Interactive dashboards & experiment UI
├── Backend (FastAPI)
│   ├── API v1 (REST)
│   ├── Authentication (JWT)
│   └── WebSocket (Real-time updates)
├── Task Queue (Celery + Redis)
│   ├── Model aggregation
│   ├── Data quality assessment
│   └── Experiment orchestration
├── Database (PostgreSQL)
│   ├── Users & roles
│   ├── Experiments & rounds
│   ├── Model submissions
│   └── Leaderboard entries
├── Object Storage (MinIO)
│   ├── Model weights
│   └── Datasets
└── Tracking (MLflow)
    └── Experiment metrics & artifacts
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI + Uvicorn |
| **Database** | PostgreSQL (async) |
| **Task Queue** | Celery |
| **Message Broker** | Redis |
| **Object Storage** | MinIO |
| **Monitoring** | MLflow + Flower |
| **Auth** | JWT (HS256) |
| **Deployment** | Docker, Docker Compose |

## 📦 Project Structure

```
backend/
├── core/                 # Configuration & utilities
│   ├── config.py        # Pydantic settings
│   ├── security.py      # JWT, password hashing
│   ├── deps.py          # FastAPI dependencies
│   ├── storage.py       # MinIO client
│   ├── aggregation.py   # Model fusion logic
│   └── federated.py     # FL protocols
├── db/                   # Database
│   └── database.py      # SQLAlchemy engine
├── api/
│   ├── models/          # ORM models
│   │   ├── user.py
│   │   ├── experiment.py
│   │   └── leaderboard.py
│   ├── schemas/         # Pydantic request/response models
│   │   ├── auth.py
│   │   ├── experiment.py
│   │   └── admin.py
│   ├── routes/          # FastAPI routers
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── experiments.py
│   │   ├── leaderboard.py
│   │   └── admin.py
│   └── deps.py          # Dependency injection
├── services/            # Business logic
│   ├── aggregation.py   # Model aggregation service
│   └── data_quality.py  # Quality assessment
├── tasks/               # Celery task definitions
│   └── celery_app.py
└── init_db.py          # Database initialization

frontend/               # Streamlit application
tests/                  # Unit & integration tests
docker-compose.yml      # Service orchestration
Dockerfile             # Backend container
requirements.txt       # Python dependencies
.env                   # Environment configuration
main.py                # FastAPI entry point
verify_startup.py      # Startup verification script
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone and Setup**
   ```bash
   cd ModelHub
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Copy .env template and update with your values
   cp .env.example .env
   # Edit .env with your database and service credentials
   ```

3. **Initialize Database**
   ```bash
   python backend/init_db.py
   ```

4. **Verify Startup**
   ```bash
   python verify_startup.py
   ```

5. **Start Backend Server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **In another terminal, start Celery worker**
   ```bash
   celery -A backend.tasks.celery_app worker --loglevel=info
   ```

7. **Start Frontend (Streamlit)**
   ```bash
   streamlit run frontend/app.py
   ```

### Accessing the Application
- **API Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:8501

## 🐳 Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Create database tables
docker-compose exec backend python backend/init_db.py

# Access services
# API: http://localhost:8000
# Frontend: http://localhost:8501
# MLflow: http://localhost:5000
# Flower (Celery): http://localhost:5555
# MinIO: http://localhost:9001
```

## 📚 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT tokens

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update profile
- `POST /api/v1/users/me/password` - Change password

### Experiments
- `GET /api/v1/experiments/dashboard` - Platform stats
- `POST /api/v1/experiments/` - Create experiment
- `GET /api/v1/experiments/` - List experiments
- `GET /api/v1/experiments/{exp_id}` - Get experiment details
- `POST /api/v1/experiments/{exp_id}/submit` - Submit model

### Leaderboard
- `GET /api/v1/leaderboard/global` - Global rankings
- `GET /api/v1/leaderboard/user/{user_id}` - User stats

### Admin
- `GET /api/v1/admin/stats` - System statistics
- `PATCH /api/v1/admin/users/{user_id}` - Update user

## 🔐 Security Features

- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: Bcrypt with random salts
- **CORS Configuration**: Restricted origins
- **Rate Limiting**: Per-minute request limits
- **Trusted Hosts**: Configured host whitelist
- **Differential Privacy**: Optional privacy-preserving aggregation

## 📊 Environment Variables

Key configuration variables (see `.env`):

```
# Application
APP_ENV=development|production
DEBUG=true|false
SECRET_KEY=your_secret_key

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# JWT
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8501
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest tests/test_auth.py

# Run in verbose mode
pytest -v
```

## 📖 API Documentation

Full OpenAPI documentation available at `/api/docs` when running with `DEBUG=true`.

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes and commit: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/your-feature`
4. Submit a pull request

## 📝 Detailed Setup Guide

### PostgreSQL Setup

```bash
# Create database and user
createdb ml_platform
createuser mlplatform_user
# In psql:
ALTER USER mlplatform_user PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ml_platform TO mlplatform_user;
```

### Redis Setup

```bash
# Install Redis (Ubuntu)
sudo apt-get install redis-server

# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### MinIO Setup

```bash
# Start MinIO
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"

# Create buckets
mc alias set minio http://localhost:9000 minioadmin minioadmin
mc mb minio/ml-models
mc mb minio/ml-datasets
```

## 🐛 Troubleshooting

### Database Connection Error
- Verify PostgreSQL is running
- Check DATABASE_URL in .env
- Run: `python backend/init_db.py`

### Celery Tasks Not Running
- Verify Redis is running
- Check Celery worker logs
- Ensure CELERY_BROKER_URL is correct

### CORS Issues
- Update CORS_ORIGINS in .env
- Frontend and backend must use matching origins

### Import Errors
- Verify all files in backend/ folder
- Run: `python verify_startup.py`
- Check PYTHONPATH includes project root


## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- IIT Guwahati Computer Science Department
- Federated Learning research community
- Open source contributors

---

**Last Updated**: April 2026
**Version**: 1.0.0
**Status**: Production Ready ✅
