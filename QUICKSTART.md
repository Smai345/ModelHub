# Quick Start Guide - IITG ML Platform

## 🚀 Get Running in 5 Minutes

### Option 1: Docker (Recommended - Easiest)

```bash
# 1. Start all services
docker-compose up --build

# 2. Open in browser
# API Documentation: http://localhost:8000/api/docs
# Frontend: http://localhost:8501
# MinIO Console: http://localhost:9001
# Flower (Tasks): http://localhost:5555
# MLflow: http://localhost:5000
```

**That's it!** The database will be initialized automatically.

### Option 2: Local Setup (For Development)

```bash
# 1. Install dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Start PostgreSQL & Redis
# Option A: Using Docker containers (no venv needed for these)
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ml_platform \
  postgres:15-alpine

docker run -d -p 6379:6379 redis:7-alpine

# Option B: Or install locally (macOS: brew install postgresql redis)

# 3. Initialize database
python backend/init_db.py

# 4. Start backend (Terminal 1)
uvicorn main:app --reload

# 5. Start Celery worker (Terminal 2)
celery -A backend.tasks.celery_app worker --loglevel=info

# 6. Start frontend (Terminal 3)
streamlit run frontend/app.py

# Access at: http://localhost:8000 (API), http://localhost:8501 (UI)
```

## 📝 First Steps

### 1. Register a User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@iitg.edu",
    "username": "researcher_01",
    "full_name": "Dr. Researcher",
    "password": "SecurePassword123!",
    "department": "Computer Science",
    "institution": "IIT Guwahati"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@iitg.edu",
    "password": "SecurePassword123!"
  }'
```

### 3. Get Your Profile
```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Create an Experiment
```bash
curl -X POST http://localhost:8000/api/v1/experiments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Federated MNIST Classification",
    "description": "Distributed training on handwritten digits",
    "model_architecture": {
      "layers": [784, 128, 64, 10],
      "activation": "relu"
    },
    "aggregation_strategy": "fedavg_weighted",
    "min_participants": 3,
    "max_rounds": 10
  }'
```

## 🔑 API Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/register` | POST | Create new account |
| `/api/v1/auth/login` | POST | Login and get tokens |
| `/api/v1/users/me` | GET | Get current user profile |
| `/api/v1/experiments/` | GET | List all experiments |
| `/api/v1/experiments/` | POST | Create new experiment |
| `/api/v1/experiments/dashboard` | GET | Platform statistics |
| `/api/v1/leaderboard/global` | GET | Global rankings |
| `/api/v1/admin/stats` | GET | System analytics (Admin) |

Full docs at: http://localhost:8000/api/docs

## 🛠️ Common Tasks

### View API Documentation
http://localhost:8000/api/docs

### Monitor Task Queue  
http://localhost:5555 (Flower)

### Check ML Models
http://localhost:5000 (MLflow)

### Access File Storage
http://localhost:9001 (MinIO - user: minioadmin, pass: minioadmin)

### View Database
```bash
psql postgresql://postgres:postgres@localhost:5432/ml_platform
# List tables: \dt
# Query users: SELECT * FROM users;
```

### Check Logs
```bash
# Backend logs
docker logs ml_platform_backend

# Celery worker logs
docker logs ml_platform_celery

# All services
docker-compose logs -f
```

## 🐛 Troubleshooting

### "Connection refused" on database
```bash
# Make sure PostgreSQL is running
docker ps | grep postgres

# Or restart services
docker-compose down && docker-compose up
```

### "Module not found" errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify imports
python verify_startup.py
```

### Port already in use
```bash
# Find process using port (example: 8000)
lsof -i :8000

# Kill process (Linux/Mac)
kill -9 <PID>

# Or change port in .env and docker-compose.yml
```

### Celery tasks not running
```bash
# Check Redis
redis-cli ping  # Should return PONG

# Check Celery worker is running
docker logs ml_platform_celery

# or terminal: celery -A backend.tasks.celery_app worker --loglevel=debug
```

## 📚 Next Steps

1. **Read Full README**: See `README.md` for comprehensive documentation
2. **Join Experiments**: Participate in federated learning experiments
3. **Submit Models**: Upload your trained models  
4. **Check Leaderboard**: See global rankings
5. **Explore Admin Panel**: Platform statistics and user management

## 💡 Tips

- **Save your tokens**: Use the JWT token for authenticated requests
- **Check logs**: Always check `docker logs` when something fails
- **Read docs**: Full API documentation at `/api/docs`
- **Backend reload**: Changes in code auto-reload in development
- **Database persistence**: Data saved in Docker volumes

## 🆘 Need Help?

- **API Issues**: Check the OpenAPI docs (`/api/docs`)
- **Code Issues**: See `CONTRIBUTING.md` for development setup
- **Deployment**: Check `README.md` for production setup
- **Security**: Review JWT and CORS configuration

---

**Happy Machine Learning! 🚀**
