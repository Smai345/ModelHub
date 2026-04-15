# How to Run & Deploy the IITG ML Platform

## 🚀 Quickest Start (5 minutes)

### Option 1: Docker Compose (Recommended - No Setup Required)

```bash
cd ModelHub

# Start everything
docker-compose up --build

# Wait for services to be ready (2-3 minutes)
# Then open in browser:
```

**Access Points:**
- **API & Documentation**: http://localhost:8000/api/docs
- **Frontend (Streamlit)**: http://localhost:8501
- **MinIO Console**: http://localhost:9001 (user: minioadmin, pass: minioadmin)
- **Flower (Task Monitoring)**: http://localhost:5555
- **MLflow (Experiment Tracking)**: http://localhost:5000

---

## 💻 Local Development Setup

### Option 2: Run Locally (For Development)

**Step 1: Install Dependencies**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

**Step 2: Start Database & Cache Services** (use Docker for these)
```bash
# Terminal 1: Start PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ml_platform \
  postgres:15-alpine

# Terminal 2: Start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 3: Start MinIO (optional, for file storage)
docker run -d -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio server /data --console-address ":9001"
```

**Step 3: Initialize Database**
```bash
python backend/init_db.py
```

**Step 4: Start Backend** (Terminal in your project folder)
```bash
# Activate venv first if not already activated
venv\Scripts\activate  # Windows

# Start FastAPI server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Step 5: Start Celery Worker** (Another terminal)
```bash
# Activate venv
venv\Scripts\activate

# Start Celery worker
celery -A backend.tasks.celery_app worker --loglevel=info
```

**Step 6: Start Frontend** (Another terminal)
```bash
# Activate venv
venv\Scripts\activate

# Install streamlit if not already installed
pip install streamlit requests

# Start Streamlit
streamlit run frontend/app.py
```

**Access at:**
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Frontend: http://localhost:8501

---

## 🐳 Docker Compose Options

### Development Mode (With Hot Reload)
```bash
# Uses docker-compose.dev.yml with live code reloading
docker-compose -f docker-compose.dev.yml up --build
```

### Production Mode
```bash
# Uses docker-compose.yml with optimized settings
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### Stop Services
```bash
# Stop containers
docker-compose down

# Stop and remove volumes (clears data)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery_worker
docker-compose logs -f postgres
```

---

## 🔧 Useful Make Commands

If you have `make` installed (or on Windows with GNU Make):

```bash
# Install dependencies
make install

# Run development server locally
make dev

# Run with Docker
make docker

# Stop Docker services
make docker-stop

# Initialize database
make db-init

# Run Celery worker
make celery

# Run tests
make test

# Check startup
make verify

# Clean temporary files
make clean
```

---

## 📋 Verification Checklist

After starting services, verify everything works:

**1. Check if backend is running**
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","app":"IITG ML Platform","env":"development"}
```

**2. Test API authentication**
```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@iitg.edu",
    "username": "testuser",
    "full_name": "Test User",
    "password": "TestPassword123",
    "institution": "IIT Guwahati"
  }'
```

**3. Login**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@iitg.edu",
    "password": "TestPassword123"
  }'
```

**4. Check Celery tasks**
- Open http://localhost:5555 (Flower)
- Should show active worker

**5. Check database**
```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/ml_platform

# List tables
\dt

# Check users
SELECT * FROM users;
```

---

## 📊 First API Calls

### 1. Register & Login
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@iitg.edu",
    "password": "TestPassword123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 2. Get Your Profile
```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Get Platform Stats
```bash
curl http://localhost:8000/api/v1/experiments/dashboard \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Create an Experiment
```bash
curl -X POST http://localhost:8000/api/v1/experiments/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First FL Experiment",
    "description": "Testing federated learning",
    "min_participants": 2,
    "max_rounds": 5
  }'
```

---

## 🚨 Troubleshooting

### "Port already in use"
```bash
# Find and kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -i :8000
kill -9 <PID>
```

### Database connection error
```bash
# Make sure PostgreSQL is running
docker ps | grep postgres

# Restart services
docker-compose down
docker-compose up --build
```

### Module not found errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify installation
python verify_startup.py
```

### Redis connection error
```bash
# Check if Redis is running
docker ps | grep redis

# Or check local Redis
redis-cli ping
```

### Celery worker not connecting
```bash
# Check Redis connection
redis-cli

# Restart Celery worker
celery -A backend.tasks.celery_app worker --loglevel=debug
```

---

## 📦 Production Deployment

### On Linux Server / VPS

1. **Clone repository**
```bash
git clone <repo-url>
cd ModelHub
```

2. **Install Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with production values:
nano .env
```

4. **Start services**
```bash
sudo docker-compose up -d --build
```

5. **Check status**
```bash
sudo docker-compose ps
sudo docker-compose logs -f backend
```

### With Nginx Reverse Proxy

Create `nginx.conf`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### With SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d yourdomain.com
# Then configure .env: ALLOWED_HOSTS=yourdomain.com
```

---

## ✅ Quick Comparison

| Method | Setup Time | Best For | Pros | Cons |
|--------|-----------|----------|------|------|
| Docker Compose | 5 min | Quick demo | Works everywhere | Needs Docker |
| Local Dev | 15 min | Development | Full control | Manual setup |
| Production VPS | 30 min | Real deployment | Scalable | Complex config |

---

## 🎯 Recommended Start

```bash
# For first-time users (RECOMMENDED)
docker-compose up --build

# Open browser
# API: http://localhost:8000/api/docs
# Frontend: http://localhost:8501
```

---

## 📞 Need Help?

- **API Documentation**: http://localhost:8000/api/docs (when running)
- **Logs**: `docker-compose logs -f`
- **Verification**: `python verify_startup.py`
- **Issues**: Check README.md troubleshooting section

**Your platform is ready to run! 🚀**
