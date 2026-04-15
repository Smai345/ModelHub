# Makefile for common development tasks

.PHONY: help install dev prod test lint format clean docker

help:
	@echo "IITG ML Platform - Available Commands"
	@echo "======================================"
	@echo "make install       - Install dependencies"
	@echo "make dev           - Run development server"
	@echo "make prod          - Run production server (docker-compose)"
	@echo "make test          - Run tests"
	@echo "make lint          - Run code quality checks"
	@echo "make format        - Auto-format code"
	@echo "make clean         - Clean up temporary files"
	@echo "make docker        - Build and start Docker containers"
	@echo "make docker-stop   - Stop Docker containers"
	@echo "make db-init       - Initialize database"
	@echo "make db-migrate    - Run database migrations"
	@echo "make celery        - Start Celery worker"
	@echo "make verify        - Verify startup configuration"

install:
	python -m venv venv
	. venv/Scripts/activate && pip install -r requirements.txt
	@echo "✓ Dependencies installed"

dev:
	. venv/Scripts/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

prod:
	docker-compose up --build

docker:
	docker-compose -f docker-compose.dev.yml up --build

docker-stop:
	docker-compose -f docker-compose.dev.yml down

db-init:
	. venv/Scripts/activate && python backend/init_db.py
	@echo "✓ Database initialized"

db-migrate:
	. venv/Scripts/activate && alembic upgrade head

celery:
	. venv/Scripts/activate && celery -A backend.tasks.celery_app worker --loglevel=info

test:
	. venv/Scripts/activate && pytest -v --cov=backend tests/

lint:
	. venv/Scripts/activate && ruff check backend/ tests/
	. venv/Scripts/activate && mypy backend/

format:
	. venv/Scripts/activate && black backend/ tests/
	. venv/Scripts/activate && isort backend/ tests/

verify:
	. venv/Scripts/activate && python verify_startup.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov
	@echo "✓ Cleanup complete"
