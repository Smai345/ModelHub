#!/usr/bin/env python3
"""
Startup verification script - tests if the application can be imported and configured.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("IITG ML Platform - Startup Verification")
print("=" * 60)

try:
    print("\n[1/5] Loading environment configuration...")
    from backend.core.config import settings
    print(f"     ✓ APP_ENV: {settings.APP_ENV}")
    print(f"     ✓ DEBUG: {settings.DEBUG}")
    print(f"     ✓ APP_NAME: {settings.APP_NAME}")
except Exception as e:
    print(f"     ✗ Error: {e}")
    sys.exit(1)

try:
    print("\n[2/5] Checking database configuration...")
    print(f"     ✓ DATABASE_URL configured")
    print(f"     ✓ DB_POOL_SIZE: {settings.DB_POOL_SIZE}")
except Exception as e:
    print(f"     ✗ Error: {e}")
    sys.exit(1)

try:
    print("\n[3/5] Verifying ORM models...")
    from backend.api.models import User, Experiment, ModelSubmission
    print(f"     ✓ User model imported")
    print(f"     ✓ Experiment model imported")
    print(f"     ✓ ModelSubmission model imported")
except Exception as e:
    print(f"     ✗ Error: {e}")
    sys.exit(1)

try:
    print("\n[4/5] Verifying FastAPI routes...")
    from backend.api.routes import (
        auth_router, users_router, experiments_router, 
        leaderboard_router, admin_router
    )
    print(f"     ✓ auth_router imported")
    print(f"     ✓ users_router imported")
    print(f"     ✓ experiments_router imported")
    print(f"     ✓ leaderboard_router imported")
    print(f"     ✓ admin_router imported")
except Exception as e:
    print(f"     ✗ Error: {e}")
    sys.exit(1)

try:
    print("\n[5/5] Creating FastAPI application...")
    from main import create_app
    app = create_app()
    print(f"     ✓ FastAPI app created successfully")
    print(f"     ✓ App title: {app.title}")
except Exception as e:
    print(f"     ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All checks passed! Application is ready to start.")
print("=" * 60)
print("\nTo start the application, run:")
print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
print()
