# CONTRIBUTING.md - Contribution Guidelines

## Development Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 14+
- Redis 7+

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ModelHub
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-cov black ruff mypy isort
   ```

4. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. **Initialize database**
   ```bash
   python backend/init_db.py
   ```

## Code Style Guidelines

### Format Code
```bash
black backend/ tests/
isort backend/ tests/
```

### Lint Code
```bash
ruff check backend/ tests/
mypy backend/
```

### Run Tests
```bash
pytest -v
pytest --cov=backend tests/  # with coverage
```

## Project Structure

- `backend/` - FastAPI application code
  - `core/` - Configuration, security, utilities
  - `db/` - Database models and session management
  - `api/` - Routes, schemas, and dependency injection
  - `services/` - Business logic
  - `tasks/` - Celery tasks

- `frontend/` - Streamlit application
- `tests/` - Unit and integration tests

## Commit Message Format

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Testing
- `chore` - Build system, dependencies

**Examples:**
```
feat(auth): add JWT token refresh endpoint
fix(experiments): resolve FedAvg aggregation bug
docs(api): add authentication examples
```

## Pull Request Process

1. Create a branch: `git checkout -b feature/your-feature`
2. Make changes and commit
3. Push to branch: `git push origin feature/your-feature`
4. Create Pull Request with description:
   - What does it do?
   - Why is it needed?
   - How to test?
5. Ensure CI/CD passes
6. Request review from maintainers
7. Address feedback and merge

## Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### With Coverage
```bash
pytest --cov=backend --cov-report=html tests/
```

## Database Migrations

Using Alembic:

```bash
# Create migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Revert migration
alembic downgrade -1
```

## Documentation

- Add docstrings to all functions
- Use Google-style docstrings
- Update README for major changes
- Add inline comments for complex logic

## Security

- Never commit sensitive credentials
- Use environment variables
- Review security checklist before PR
- Report security issues privately

## Performance

- Profile code before optimization
- Use database indexes for frequent queries
- Cache expensive computations
- Monitor API response times

## Questions?

- Open an issue for questions
- Check existing issues first
- Join our community discussions

---

Thank you for contributing!
