# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SafeWork Pro** (건설업 보건관리 시스템) - A comprehensive web application for construction site health management complying with Korean occupational safety and health laws. Manages worker health, medical examinations, workplace monitoring, health education, chemical substances (MSDS), and accident reporting.

### Repository Information
- **GitHub**: JCLEE94/safework (previously qws941/health)
- **Registry**: registry.jclee.me/safework:latest (public registry, no auth required)
- **Production**: https://safework.jclee.me
- **Architecture**: All-in-one container (PostgreSQL + Redis + FastAPI + React)
- **CI/CD**: GitHub Actions (self-hosted runner) + ArgoCD + charts.jclee.me

## Quick Commands

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term --timeout=60 -x --maxfail=5

# Run single test file
pytest tests/test_workers.py -v

# Run tests by marker (skip slow tests)
pytest -m "not slow" -v

# Run integration tests only
pytest -m integration -v

# Run Rust-style inline integration tests (NEW)
python3 -m src.handlers.workers              # Worker management integration tests
python3 -m src.handlers.health_exams         # Health exam integration tests  
python3 -m src.handlers.chemical_substances  # Chemical substance integration tests

# Lint and format
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Frontend development (run from frontend/ directory)
cd frontend && npm run dev          # Start Vite dev server (port 5173)
cd frontend && npm run build        # Build for production
cd frontend && npm run preview      # Preview production build
```

### Testing Configuration
- **pytest.ini**: Configured with `asyncio_mode = auto` for async fixtures
- **Timeout**: 60 seconds per test, fail-fast with `-x --maxfail=5`
- **Dependencies**: pytest, pytest-asyncio, pytest-cov, pytest-timeout
- **Test markers**: `slow`, `integration`, `unit`, `smoke`, `critical`
- **Coverage target**: 70% minimum
- **Rust-style Inline Tests**: Integration tests embedded directly in handler files using `if __name__ == "__main__":` blocks
  - Tests complete API → Database → Response flows with real data validation
  - Each component has isolated SQLite test database
  - Clear Given-When-Then structure with Korean business logic comments

### Deployment
```bash
# Deploy to production (automated via GitHub Actions)
git add . && git commit -m "feat: description" && git push

# Manual deployment (if CI/CD fails)
docker build -t registry.jclee.me/safework:latest .
echo "bingogo1" | docker login registry.jclee.me -u admin --password-stdin
docker push registry.jclee.me/safework:latest

# Check deployment status
kubectl get pods -n safework
curl https://safework.jclee.me/health

# Monitor CI/CD pipeline
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
  - `auth_service.py` - JWT authentication service
  - `notifications.py` - Alert and notification services
- `utils/` - Helper functions and utilities
- `config/` - Database configuration and settings

#### Frontend (`frontend/`)
- `src/App.tsx` - Main React application with sidebar navigation
- `src/components/` - Reusable UI components
- `src/pages/` - Feature-specific page components
- `src/api/` - Backend API integration layer
- Uses Vite for bundling, TypeScript, Tailwind for styling

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

### Current Setup
- **Runner**: Self-hosted GitHub Actions runner on k8s.jclee.me
- **Registry**: registry.jclee.me (public, credentials: admin/bingogo1)
- **Helm Repository**: charts.jclee.me (ArgoCD uses this)
- **Workflow**: `.github/workflows/deploy.yml`
- **ArgoCD**: Monitors charts.jclee.me for updates (targetRevision: "*")

### Deployment Flow
```
1. Git Push (main) → GitHub Actions (self-hosted runner)
2. Build Docker Image → Push to registry.jclee.me
3. Update Helm Chart → Push to charts.jclee.me
4. ArgoCD detects new chart version → Auto-deploy to K8s
5. Production health check at https://safework.jclee.me/health
```

### Image Tagging Strategy
- Commit SHA: Used for Docker images (e.g., `abc1234...`)
- Latest: Always points to most recent build
- ArgoCD tracks chart versions from charts.jclee.me

## Common Issues & Solutions

### Development Issues
| Issue | Solution |
|-------|----------|
| Docker 413 error | Use registry.jclee.me instead of ghcr.io |
| Self-hosted runner offline | Check k8s.jclee.me runner status |
| Port conflicts | SafeWork uses 3001, PostgreSQL 5432, Redis 6379 |
| Async fixture errors | Use `@pytest_asyncio.fixture` decorator |
| Import errors | Check paths (e.g., `services.cache` not `services.cache_service`) |
| Tests hanging | Add timeout with pytest-timeout |
| Korean text garbled | Ensure ko_KR.UTF-8 locale in PostgreSQL |
| Environment variable missing | Check settings.py defaults |
| Authentication errors | Set `ENVIRONMENT=development` for dev mode |
| ArgoCD not syncing | Check charts.jclee.me repository |

### Production Debugging
```bash
# Container health
docker ps | grep safework
curl https://safework.jclee.me/health

# View logs
docker logs safework --tail=100 | grep ERROR
kubectl logs deployment/safework -n safework

# Pipeline monitoring
gh run list --limit 5
gh run view <run-id> --log-failed

# Force restart
kubectl rollout restart deployment/safework -n safework
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
- `/health` - Health check endpoint

### API Documentation
- Swagger UI: http://localhost:3001/api/docs
- ReDoc: http://localhost:3001/api/redoc

## Security Configuration

### Authentication System
The system uses a custom JWT-based authentication service:
```python
# src/services/auth_service.py - Core authentication service
# src/utils/auth_deps.py - FastAPI dependency injection
# src/middleware/auth.py - Authentication middleware

# Usage in handlers:
from src.utils.auth_deps import CurrentUserId

@router.post("/")
async def create_worker(
    worker_data: schemas.WorkerCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    # current_user_id is automatically extracted from JWT token
```

### Environment-Based Authentication
- **Development**: `ENVIRONMENT=development` allows bypassed auth with default user
- **Production**: Full JWT validation required
- **Settings**: All auth configuration via environment variables (no hardcoded secrets)

### Implemented Measures
- JWT authentication with role-based access control
- CSRF protection in middleware
- XSS prevention headers
- SQL injection protection via SQLAlchemy
- Rate limiting (100 requests/minute)
- Secure headers automatically applied

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

### Rust-style Inline Integration Testing Pattern
Core handlers have embedded integration tests following Rust's approach:
```python
# At the end of handler files (e.g., src/handlers/workers.py)
if __name__ == "__main__":
    import asyncio
    import pytest_asyncio
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import create_async_engine

    # Test database setup
    SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test_component.db"
    test_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
    
    async def test_integration_workflow(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 전체 비즈니스 플로우 검증
        - API 요청 → 검증 → DB 저장 → 응답
        """
        # Given: 테스트 데이터
        test_data = {...}
        
        # When: API 호출
        response = await async_client.post("/api/v1/endpoint", json=test_data)
        
        # Then: 응답 및 DB 상태 검증
        assert response.status_code == 200
        # DB validation...
    
    # Execute: python3 -m src.handlers.component_name
    asyncio.run(run_integration_tests())
```

This pattern enables testing complete business workflows with real data validation.

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
Settings system provides defaults for all environments:
```python
# src/config/settings.py pattern:
class Settings(BaseSettings):
    # Development-friendly defaults with env var overrides
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    jwt_secret: str = Field(default="dev-jwt-secret-change-in-production", env="JWT_SECRET")
    
    # Dynamic URL generation methods
    def generate_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
```

## Recent Updates & Current Status

### Integration Testing Implementation (2025-01-23)
- ✅ **Rust-style inline integration tests** implemented for core components
- ✅ **Worker Management** - Registration, validation, filtering, search, caching tests
- ✅ **Health Examinations** - Creation, filtering, due-soon detection, statistics tests  
- ✅ **Chemical Substances** - Registration, CAS validation, usage tracking, inventory tests
- ✅ **Real data validation** - Tests use actual business data and verify database states
- ✅ **Isolated test environments** - Each component has dedicated SQLite test database

### CI/CD Configuration (2025-01-23)
- Self-hosted GitHub Actions runner on k8s.jclee.me
- ArgoCD configured to use charts.jclee.me Helm repository
- Automatic version tracking with `targetRevision: "*"`
- Single workflow file: `.github/workflows/deploy.yml`

### Production Status
- ✅ Application running at https://safework.jclee.me
- ✅ Health check endpoint responding normally
- ✅ All components connected (PostgreSQL, Redis, FastAPI, React)
- ✅ HTTPS with valid certificate
- ✅ Kubernetes deployment via ArgoCD
- ✅ Comprehensive integration test coverage for critical workflows

### Testing Infrastructure
- **Traditional Tests**: pytest-based unit and integration tests in `tests/` directory
- **Inline Integration Tests**: Rust-style tests embedded in handler files for comprehensive workflow validation
- **Test Execution**: Both approaches available - `pytest tests/` for traditional, `python3 -m src.handlers.component` for inline
- **Coverage**: Combined approach provides comprehensive test coverage with focus on real business scenarios

### Known Issues
- ArgoCD needs charts.jclee.me to have proper Helm charts
- Manual deployment required if charts repository is unavailable
- GitHub Actions billing may affect automated deployments

---
**Version**: 4.1.0  
**Updated**: 2025-01-23  
**Maintainer**: SafeWork Pro Development Team  
**CI/CD Status**: ✅ Active (Self-hosted runner + ArgoCD + charts.jclee.me)  
**Testing Status**: ✅ Comprehensive (Traditional + Rust-style Inline Integration Tests)