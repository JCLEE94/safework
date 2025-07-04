# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SafeWork Pro** (건설업 보건관리 시스템) - A comprehensive web application for construction site health management complying with Korean occupational safety and health laws. Manages worker health, medical examinations, workplace monitoring, health education, chemical substances (MSDS), and accident reporting.

### Repository Information
- **GitHub**: JCLEE94/safework (previously qws941/health)
- **Registry**: registry.jclee.me/safework:latest
- **Production**: http://192.168.50.215:3001
- **Architecture**: All-in-one container (PostgreSQL + Redis + FastAPI + React)
- **Self-hosted runner**: Used for CI/CD with special configurations

## Quick Commands

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term --timeout=300 -x

# Run single test file
pytest tests/test_workers.py -v

# Lint and format
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Frontend development
npm run dev          # Start Vite dev server (port 5173)
npm run build        # Build for production
npm run preview      # Preview production build
```

### Testing Configuration
- **pytest.ini**: Configured with `asyncio_mode = auto` for async fixtures
- **Timeout**: 300 seconds per test, 10 minutes for entire test suite
- **Dependencies**: pytest, pytest-asyncio, pytest-cov, pytest-timeout
- **Coverage target**: 70% minimum (configured in CI/CD)

### Deployment
```bash
# Deploy to production (automated CI/CD via GitHub Actions + ArgoCD)
git add . && git commit -m "feat: description" && git push

# Manual deployment (backup)
./deploy-single.sh

# Check deployment status
curl http://192.168.50.215:3001/health
docker logs safework --tail=50

# Monitor pipeline status
gh run list --limit 5
gh run view <run-id> --log-failed
```

### Database Operations
```bash
# Run migrations
docker exec safework alembic upgrade head

# Create new migration
docker exec safework alembic revision --autogenerate -m "description"

# Database shell
docker exec safework psql -U admin -d health_management

# Check tables
docker exec safework psql -U admin -d health_management -c "\dt"
```

## Architecture

### System Architecture
```
┌──────────────────────────────────────┐
│         All-in-One Container         │
│  ┌─────────┐  ┌─────────┐  ┌──────┐ │
│  │ React   │──│ FastAPI │──│ PG   │ │
│  │ (Nginx) │  │ Backend │  │ DB   │ │
│  └─────────┘  └────┬────┘  └──────┘ │
│     :3001          │         :5432   │
│                ┌───┴───┐             │
│                │ Redis │             │
│                └───────┘             │
│                  :6379               │
└──────────────────────────────────────┘
         Port 3001 (External)
```

### Code Structure

#### Backend (`src/`)
- `app.py` - FastAPI application factory with middleware stack and router registration
- `models/` - SQLAlchemy models with Korean industry enums
  - Base models inherit from `declarative_base()`
  - Nullable fields in models match Optional fields in schemas
- `schemas/` - Pydantic validation schemas
  - Create/Update schemas separate from response schemas
  - Korean field validation included
- `handlers/` - API endpoints organized by domain
  - Each handler imports models, schemas, and services
  - Dependency injection via FastAPI's `Depends`
- `middleware/` - Security, caching, logging, performance layers
  - Applied in specific order in `app.py`
- `services/` - Business logic and external integrations
  - `cache.py` - Redis caching with CacheService class
  - `notifications.py` - Alert and notification services
- `utils/` - Helper functions and utilities
- `config/` - Database configuration and settings

#### Frontend (`src/`)
- `App.tsx` - Main React application with sidebar navigation
- `components/` - Reusable UI components
- `pages/` - Feature-specific page components
- `api/` - Backend API integration layer
- Uses Vite for bundling, Tailwind for styling

#### Key Middleware Stack (Order matters!)
1. **CORS**: Allow frontend communication
2. **Security**: CSRF, XSS, SQL injection protection
3. **Caching**: Redis-backed response caching
4. **Logging**: Structured logging with metrics
5. **Performance**: Compression, rate limiting
6. **Auth**: JWT with role-based access control

## Development Guidelines

### Adding New Features
1. Define database model in `src/models/` (follow nullable pattern)
2. Create Pydantic schema in `src/schemas/` (match model nullable fields)
3. Implement API handler in `src/handlers/`
4. Import handler router in `src/app.py`
5. Update frontend in React components
6. Write tests with pytest (use pytest_asyncio.fixture for async)
7. Ensure tests pass with coverage >70%

### Database Schema Patterns
```python
# Model (src/models/worker.py)
class Worker(Base):
    gender = Column(String(10), nullable=True)  # Optional field
    employment_type = Column(String(20), nullable=False)  # Required field

# Schema (src/schemas/worker.py)
class WorkerCreate(BaseModel):
    gender: Optional[str] = None  # Match nullable=True
    employment_type: str  # Match nullable=False
```

### Async Test Fixtures
```python
# Use pytest_asyncio for async fixtures
import pytest_asyncio

@pytest_asyncio.fixture(scope="function")
async def test_worker(async_session):
    # Create test data
    worker = Worker(...)
    async_session.add(worker)
    await async_session.commit()
    return worker  # No await needed in test usage
```

### PDF Form Development
1. Add PDF template to `document/`
2. Define coordinates in `PDF_FORM_COORDINATES` (src/handlers/documents.py)
3. Update form selector in frontend
4. Test with Korean font rendering (NanumGothic)

## CI/CD Pipeline

### GitHub Actions Configuration
- **Self-hosted runner**: `[self-hosted, linux]`
- **Service containers**: PostgreSQL (port 15432), Redis (port 16379)
- **npm cache workaround**: `npm_config_cache: ${{ runner.temp }}/.npm`
- **Test timeout**: 10 minutes max
- **ArgoCD auto-sync**: Automatically detects and deploys new images

### Workflow Files
- `main-deploy.yml` - Primary CI/CD pipeline for production (ArgoCD)
- `build-deploy.yml` - Development branch deployment (Watchtower)
- `test.yml` - Test suite with service containers
- `security.yml` - Trivy security scanning
- ~~`argocd-simple.yml`~~ - Disabled (replaced by main-deploy.yml)
- ~~`k8s-deploy.yml`~~ - Disabled (replaced by main-deploy.yml)

### Environment Variables (CI/CD)
```yaml
DATABASE_URL: postgresql://admin:password@localhost:15432/health_management
REDIS_URL: redis://localhost:16379/0
JWT_SECRET: test-secret-key
PYTHONPATH: ${{ github.workspace }}
npm_config_cache: ${{ runner.temp }}/.npm  # For self-hosted runner
```

## Deployment Pipeline

### Automated Flow
```
1. Git Push (main) → GitHub Actions (self-hosted runner)
2. Run Tests + Security Scan → Build Docker Image → Push to registry.jclee.me
3. Update K8s manifests → Git commit with new image tags
4. ArgoCD auto-sync → Deploy to Kubernetes cluster
5. Production health check at https://safework.jclee.me/health
```

### ArgoCD Configuration
- Monitors Git repository k8s/ directory for changes
- Auto-sync enabled with self-healing
- Private registry credentials configured
- Dashboard: https://argo.jclee.me/applications/safework

### Image Tagging Strategy
- Production: `prod-YYYYMMDD-SHA7` (e.g., prod-20250104-abc1234)
- Development: `dev-YYYYMMDD-SHA7`
- Latest: Always points to most recent production build

## Common Issues & Solutions

### Development Issues
| Issue | Solution |
|-------|----------|
| npm cache read-only error | Set `npm_config_cache: ${{ runner.temp }}/.npm` |
| Port conflicts in CI | Use ports 15432 (PG) and 16379 (Redis) |
| Async fixture errors | Use `@pytest_asyncio.fixture` decorator |
| Import errors | Check import paths (e.g., `services.cache` not `services.cache_service`) |
| Tests hanging | Add timeout configuration (pytest-timeout) |
| Korean text garbled | Ensure ko_KR.UTF-8 locale in PostgreSQL |

### Production Debugging
```bash
# Container health
docker ps | grep safework
curl http://192.168.50.215:3001/health

# View logs
docker logs safework --tail=100 | grep ERROR
curl http://192.168.50.200:5555/log/safework  # Production log viewer

# Pipeline monitoring
gh run list --limit 5
gh run view <run-id> --log-failed

# Force restart
docker restart safework
```

## API Endpoints

### Core APIs
- `/api/v1/workers/` - Worker management
- `/api/v1/health-exams/` - Health examination records
- `/api/v1/work-environments/` - Environmental measurements
- `/api/v1/educations/` - Health education tracking
- `/api/v1/chemical-substances/` - MSDS and chemical management
- `/api/v1/accidents/` - Accident reporting
- `/api/v1/documents/fill-pdf/{form_name}` - PDF generation
- `/api/v1/monitoring/ws` - WebSocket real-time monitoring
- `/api/v1/pipeline/status/{commit}` - CI/CD pipeline status

### API Documentation
- Swagger UI: http://localhost:3001/api/docs
- ReDoc: http://localhost:3001/api/redoc

## Security Configuration

### Implemented Measures
- JWT authentication with refresh tokens
- CSRF protection in middleware
- XSS prevention headers
- SQL injection protection via SQLAlchemy
- Rate limiting (100 requests/minute)
- Secure headers automatically applied

### Required Secrets (GitHub)
```bash
DOCKER_USERNAME
DOCKER_PASSWORD
DEPLOY_KEY
DEPLOY_USER
DEPLOY_HOST
```

## Important Patterns & Conventions

### API Handler Pattern
All handlers follow a consistent pattern with dependency injection:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.database import get_db
from src.schemas import worker as schemas
from src.models import worker as models

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])

@router.get("/", response_model=List[schemas.WorkerResponse])
async def get_workers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    # Implementation
```

### Frontend API Integration Pattern
Frontend uses consistent API client pattern:
```typescript
const API_BASE = '/api/v1';

export const workersApi = {
  getAll: () => fetch(`${API_BASE}/workers/`).then(res => res.json()),
  create: (data) => fetch(`${API_BASE}/workers/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
};
```

### Docker Development Commands
```bash
# Quick container commands
docker exec -it safework bash              # Shell access
docker exec safework python -c "..."        # Run Python commands
docker logs safework -f                     # Follow logs
docker-compose ps                           # Check service status
docker-compose exec db psql -U admin -d health_management  # DB access
```

### Async Testing Pattern
All async tests must use pytest_asyncio:
```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

@pytest_asyncio.fixture
async def test_worker(async_session: AsyncSession):
    worker = Worker(name="Test", ...)
    async_session.add(worker)
    await async_session.commit()
    await async_session.refresh(worker)
    return worker

# Usage in tests - no await needed
async def test_worker_creation(test_worker):
    assert test_worker.name == "Test"
```

### Korean Industry Enums
The system uses Korean occupational safety classifications:
```python
# src/models/enums.py
class IndustryType(str, Enum):
    CONSTRUCTION = "건설업"
    MANUFACTURING = "제조업"
    SERVICE = "서비스업"
    
class HealthExamType(str, Enum):
    GENERAL = "일반건강진단"
    SPECIAL = "특수건강진단"
    PLACEMENT = "배치전건강진단"
```

### Redis Caching Pattern
Cache service is injected via dependency:
```python
from src.services.cache import CacheService

@router.get("/{worker_id}")
async def get_worker(
    worker_id: int,
    cache: CacheService = Depends(get_cache_service)
):
    cache_key = f"worker:{worker_id}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    # Fetch from DB and cache
```

### PDF Generation Pattern
PDF forms use predefined coordinates:
```python
# src/handlers/documents.py
PDF_FORM_COORDINATES = {
    "health_checkup_report": {
        "fields": {
            "name": (100, 700),
            "date": (300, 700),
            # ...
        }
    }
}
```

### Environment-Specific Configuration
```bash
# Development
ENVIRONMENT=development docker-compose up

# Production
docker-compose up -d  # Uses default production config

# Testing (CI/CD)
DATABASE_URL=postgresql://admin:password@localhost:15432/health_management
REDIS_URL=redis://localhost:16379/0
```

---
**Version**: 3.1.0  
**Updated**: 2025-07-01  
**Maintainer**: SafeWork Pro Development Team  
**CI/CD Status**: ✅ Active (Self-hosted runner + Watchtower)