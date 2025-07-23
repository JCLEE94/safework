# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SafeWork Pro** (건설업 보건관리 시스템) - A comprehensive web application for construction site health management complying with Korean occupational safety and health laws. Manages worker health, medical examinations, workplace monitoring, health education, chemical substances (MSDS), and accident reporting.

### Key Information
- **Repository**: JCLEE94/safework (previously qws941/health)
- **Registry**: registry.jclee.me/safework:latest (public registry, no auth required)
- **Production URL**: https://safework.jclee.me
- **Local Access**: http://192.168.50.100:3001 (Docker)
- **K8s NodePort**: http://192.168.50.110:32301 (when pod is running)
- **Architecture**: All-in-one container (PostgreSQL + Redis + FastAPI + React)

## Quick Commands

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term --timeout=60 -x --maxfail=5

# Run specific test file
pytest tests/test_workers.py -v

# Run tests by marker
pytest -m "not slow" -v          # Skip slow tests
pytest -m integration -v          # Integration tests only
pytest -m unit -v                 # Unit tests only

# Linting and formatting
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Frontend development
cd frontend && npm run dev        # Vite dev server (port 5173)
cd frontend && npm run build      # Production build
cd frontend && npm run preview    # Preview production build
```

### Local Deployment
```bash
# Production deployment (single container)
docker-compose up -d

# Check health
curl http://localhost:3001/health

# View logs
docker logs safework -f

# Database operations
docker exec safework alembic upgrade head                    # Run migrations
docker exec safework alembic revision --autogenerate -m "description"  # Create migration
docker exec safework psql -U admin -d health_management     # DB shell
```

### CI/CD & Deployment
```bash
# Deploy via CI/CD (currently has billing issues)
git add . && git commit -m "feat: description" && git push

# Manual build and deploy
./scripts/manual-build.sh         # Build Docker image locally
./scripts/deploy-to-k8s.sh        # Deploy to Kubernetes

# Check CI/CD status
gh run list --limit 5
gh run view <run-id> --log-failed

# K8s operations
kubectl get pods -n safework
kubectl logs deployment/safework -n safework
kubectl rollout restart deployment/safework -n safework
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

### Code Architecture

#### Backend Structure (`src/`)
- **app.py**: FastAPI app factory with middleware stack registration
- **models/**: SQLAlchemy models with Korean enums
  - Nullable fields in models must match Optional fields in schemas
  - All models inherit from `declarative_base()`
- **schemas/**: Pydantic validation schemas
  - Separate Create/Update/Response schemas
  - Korean field validation included
- **handlers/**: API endpoints by domain
  - Consistent pattern: router + dependency injection
  - Import models, schemas, services
- **middleware/**: Applied in specific order:
  1. CORS → 2. Security → 3. Caching → 4. Logging → 5. Performance → 6. Auth
- **services/**: Business logic
  - `cache.py`: Redis caching service
  - `auth_service.py`: JWT authentication
  - `notifications.py`: Alert services
- **config/**: Settings with environment defaults

#### Frontend Structure (`frontend/`)
- **src/App.tsx**: Main React app with sidebar
- **src/components/**: Reusable UI components
- **src/pages/**: Feature-specific pages
- **src/api/**: Backend API integration
- Tech: React 18, TypeScript, Vite, Tailwind CSS

## Development Patterns

### Adding New Features
1. Create model in `src/models/` (follow nullable pattern)
2. Create schemas in `src/schemas/` (match model nullable fields)
3. Implement handler in `src/handlers/`
4. Register router in `src/app.py`
5. Update frontend components
6. Write tests with `pytest_asyncio.fixture`
7. Ensure >70% coverage

### Database Schema Pattern
```python
# Model (src/models/worker.py)
class Worker(Base):
    gender = Column(String(10), nullable=True)        # Optional
    employment_type = Column(String(20), nullable=False)  # Required

# Schema (src/schemas/worker.py)
class WorkerCreate(BaseModel):
    gender: Optional[str] = None  # Match nullable=True
    employment_type: str          # Match nullable=False
```

### API Handler Pattern
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

### Async Test Pattern
```python
import pytest_asyncio

@pytest_asyncio.fixture(scope="function")
async def test_worker(async_session):
    worker = Worker(name="Test", employee_id="TEST001", employment_type="정규직")
    async_session.add(worker)
    await async_session.commit()
    await async_session.refresh(worker)
    return worker

# Usage - no await needed on fixture
async def test_worker_creation(test_worker):
    assert test_worker.name == "Test"
```

### Authentication Pattern
```python
# Development mode bypasses auth
# src/middleware/auth.py checks ENVIRONMENT=development

# Usage in handlers:
from src.utils.auth_deps import CurrentUserId

@router.post("/")
async def create_worker(
    worker_data: schemas.WorkerCreate,
    current_user_id: str = CurrentUserId,  # Auto-extracted from JWT
    db: AsyncSession = Depends(get_db)
):
    pass
```

## Testing Configuration

- **Framework**: pytest with pytest-asyncio
- **Config**: `pytest.ini` with `asyncio_mode = auto`
- **Timeout**: 60 seconds per test
- **Fail-fast**: `-x --maxfail=5`
- **Coverage**: 70% minimum target
- **Markers**:
  - `slow`: Long-running tests
  - `integration`: Integration tests
  - `unit`: Unit tests
  - `smoke`: Quick validation
  - `critical`: Critical path

## CI/CD Pipeline

### Current Status
⚠️ **GitHub Actions has billing issues** - "account payments have failed"
- Alternative: Use `deploy-minimal.yml` workflow
- Manual deployment: `./scripts/manual-build.sh`

### Normal Flow (when billing is resolved)
1. Push to main → GitHub Actions
2. Run tests → Build Docker image → Push to registry.jclee.me
3. ArgoCD Image Updater detects new image
4. Auto-deploy to Kubernetes cluster
5. Health check at https://safework.jclee.me/health

### Image Tagging
- Production: `prod-YYYYMMDD-SHA7`
- Semantic: `1.YYYYMMDD.BUILD_NUMBER`
- Latest: Always points to newest build

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| GitHub Actions billing error | Use manual build script or fix billing |
| Pod ErrImageNeverPull | Push image to registry or use IfNotPresent |
| pydantic_settings missing | Install with `pip install pydantic-settings` |
| NodePort not accessible | Ensure pod is running and endpoints exist |
| Async fixture errors | Use `@pytest_asyncio.fixture` decorator |
| Korean text garbled | Set ko_KR.UTF-8 locale in PostgreSQL |
| Auth errors in dev | Set `ENVIRONMENT=development` |
| 502 Bad Gateway | Check if container is running on correct port |

## API Endpoints

### Core APIs
- `/api/v1/workers/` - Worker management
- `/api/v1/health-exams/` - Health examinations
- `/api/v1/work-environments/` - Environmental monitoring
- `/api/v1/educations/` - Health education
- `/api/v1/chemical-substances/` - MSDS management
- `/api/v1/accidents/` - Accident reporting
- `/api/v1/documents/fill-pdf/{form_name}` - PDF generation
- `/api/v1/monitoring/ws` - WebSocket monitoring
- `/health` - Health check endpoint

### API Documentation
- Swagger UI: http://localhost:3001/api/docs
- ReDoc: http://localhost:3001/api/redoc

## Environment Configuration

### Key Environment Variables
```bash
ENVIRONMENT=development|production  # Auth bypass in development
DATABASE_URL=postgresql://admin:password@localhost:5432/health_management
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key
DEBUG=true|false
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
```

### Settings Pattern
The application uses pydantic-settings with smart defaults:
- Development-friendly defaults that work out of the box
- Environment variable overrides for production
- Dynamic URL generation methods

## Korean Industry Enums

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

## Recent Updates (2025-01-23)

### CI/CD Issues
- GitHub Actions billing problem prevents automated deployment
- Created `deploy-minimal.yml` for free tier limits
- Manual deployment scripts available in `scripts/`

### K8s Deployment
- NodePort 32301 configured but requires working pod
- Current workaround: Local Docker on port 3001
- External endpoints configured for host network access

### Project Structure
- Major cleanup completed (38+ duplicate files removed)
- Scripts organized into logical directories
- Consolidated Docker Compose configurations
- Comprehensive documentation structure

---
**Version**: 3.5.0  
**Updated**: 2025-01-23  
**Maintainer**: SafeWork Pro Development Team  
**Production**: ✅ Running (Docker), ⚠️ K8s pending billing fix