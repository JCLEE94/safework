# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SafeWork Pro** (건설업 보건관리 시스템) - A comprehensive web application for construction site health management complying with Korean occupational safety and health laws. Manages worker health, medical examinations, workplace monitoring, health education, chemical substances (MSDS), and accident reporting.

### Repository Information
- **GitHub**: JCLEE94/safework (previously qws941/health)
- **Registry**: registry.jclee.me/safework:latest (public registry, no auth required)
- **Production**: https://safework.jclee.me
- **NodePort Access**: Port 32301 (configured for Kubernetes NodePort service)
- **Architecture**: All-in-one container (PostgreSQL + Redis + FastAPI + React)
- **CI/CD**: GitHub Actions + ArgoCD Image Updater (automated image deployment)

## Essential Commands

### Quick Start Development
```bash
# Start backend with all services (PostgreSQL + Redis + FastAPI)
docker run -d --name safework -p 3001:3001 registry.jclee.me/safework:latest

# Frontend development (React 19 + TypeScript + Vite)
cd frontend && npm install && npm run dev    # Port 5173

# Backend testing with coverage
pytest tests/ -v --cov=src --cov-report=html --timeout=60 -x

# Code quality
black src/ tests/ && isort src/ tests/ && flake8 src/ tests/

# Frontend linting
cd frontend && npm run lint
```

### Build & Deploy
```bash
# Automated deployment (recommended)
git add . && git commit -m "feat: description" && git push

# Frontend build for production
cd frontend && npm run build

# Manual Docker build
docker build -t registry.jclee.me/frontend-v2:latest .

# Check deployment status
curl https://safework.jclee.me/health
kubectl get pods -n safework
```

### Database Operations
```bash
# Database shell access
docker exec safework psql -U admin -d health_management

# Run migrations
docker exec safework alembic upgrade head

# Check database status
docker exec safework psql -U admin -d health_management -c "\dt"
```

## Architecture

### High-Level System Design
```
┌─────────────────────────────────────────────────┐
│                SafeWork Pro                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  React UI   │──│  FastAPI    │──│ PG 15   │ │
│  │  (Nginx)    │  │  Backend    │  │ Database│ │
│  │  :3001      │  └──────┬──────┘  └─────────┘ │
│  └─────────────┘         │                     │
│                  ┌───────┴───────┐             │
│                  │   Redis 7     │             │
│                  │   Cache       │             │
│                  └───────────────┘             │
└─────────────────────────────────────────────────┘
        External Port: 3001 / NodePort: 32301
```

### Code Organization

#### Backend Architecture (`src/`)
- **Application Factory**: `src/app.py` - FastAPI app with modular middleware stack
- **Domain Models**: `src/models/` - SQLAlchemy ORM with Korean industry enums
- **API Layer**: `src/handlers/` - Route handlers with dependency injection
- **Business Logic**: `src/services/` - Service classes for complex operations
- **Data Access**: `src/repositories/` - Repository pattern for database operations
- **Middleware Stack**: Security, caching, logging, performance (order matters)

#### Frontend Architecture (`frontend/`)
- **Modern React**: React 19 + TypeScript + Vite + Ant Design 5.26.6
- **State Management**: Redux Toolkit 2.8+ (UI state) + TanStack Query 5.83+ (server state)
- **Component Structure**: Atomic Design pattern (atoms, molecules, organisms, templates)
- **Feature Modules**: Domain-specific feature organization
- **API Integration**: Typed axios client with proper error handling
- **Testing**: Jest 30 + React Testing Library 16.3+ + Testing Library User Event

#### Key Middleware Stack (Applied in Order)
1. **CORS**: Cross-origin request handling
2. **Security**: CSRF, XSS, SQL injection protection
3. **Caching**: Redis-backed response caching
4. **Logging**: Structured JSON logging with request tracing
5. **Performance**: Compression, rate limiting
6. **Authentication**: JWT with role-based access control

## Development Patterns

### Database Schema Pattern
```python
# Model with nullable pattern (src/models/worker.py)
class Worker(Base):
    gender = Column(String(10), nullable=True)  # Optional
    employment_type = Column(String(20), nullable=False)  # Required

# Matching schema (src/schemas/worker.py)
class WorkerCreate(BaseModel):
    gender: Optional[str] = None  # Match nullable=True
    employment_type: str  # Match nullable=False
```

### API Handler Pattern
```python
from fastapi import APIRouter, Depends
from src.utils.auth_deps import CurrentUserId

router = APIRouter(prefix="/api/v1/workers", tags=["workers"])

@router.post("/", response_model=schemas.WorkerResponse)
async def create_worker(
    worker_data: schemas.WorkerCreate,
    current_user_id: str = CurrentUserId,  # Auto JWT extraction
    db: AsyncSession = Depends(get_db)
):
    # Implementation with dependency injection
```

### Frontend API Integration
```typescript
// Typed API client (src/services/api/workers.ts)
export const workersApi = {
  getList: (params?: WorkerFilters) => 
    apiClient.get<Worker[]>('/workers/', { params }),
  create: (data: CreateWorkerRequest) => 
    apiClient.post<Worker>('/workers/', data)
};

// TanStack Query usage (v5 syntax)
const { data, isLoading, error } = useQuery({
  queryKey: ['workers', filters],
  queryFn: () => workersApi.getList(filters)
});
```

### Async Testing Pattern
```python
import pytest_asyncio

@pytest_asyncio.fixture
async def test_worker(async_session: AsyncSession):
    worker = Worker(name="Test", employee_id="TEST001")
    async_session.add(worker)
    await async_session.commit()
    return worker  # No await needed in test usage

async def test_worker_creation(test_worker):
    assert test_worker.name == "Test"
```

## CI/CD Pipeline

### Automated GitOps Flow
```
Git Push → GitHub Actions → Docker Build → Registry Push → 
ArgoCD Image Updater → Auto Deploy → Health Check
```

### Key Components
- **GitHub Actions**: Parallel testing, optimized Docker builds
- **Registry**: registry.jclee.me (public, no authentication)
- **ArgoCD Image Updater**: Automatic image detection and deployment
- **Image Tags**: `prod-YYYYMMDD-SHA7` for production releases
- **Monitoring**: Real-time deployment status via ArgoCD dashboard

### Environment Variables (CI/CD)
```yaml
DATABASE_URL: postgresql://admin:password@localhost:5432/health_management
REDIS_URL: redis://localhost:6379/0
JWT_SECRET: test-secret-key
ENVIRONMENT: development  # Bypasses auth in tests
NODE_OPTIONS: '--max-old-space-size=4096'  # For frontend builds
```

## Korean Industry Specifics

### Industry Classifications
```python
class IndustryType(str, Enum):
    CONSTRUCTION = "건설업"
    MANUFACTURING = "제조업"
    
class HealthExamType(str, Enum):
    GENERAL = "일반건강진단"
    SPECIAL = "특수건강진단"
    PLACEMENT = "배치전건강진단"
```

### PDF Form Generation
- Korean legal forms in `document/` directory
- Coordinate-based field positioning in `PDF_FORM_COORDINATES`
- NanumGothic font support for Korean text rendering
- Base64 encoding for web delivery

### Authentication & Localization
- Korean timezone: Asia/Seoul (KST)
- UTF-8 encoding throughout the stack
- Korean field validation in Pydantic schemas
- Development environment bypasses auth (`ENVIRONMENT=development`)

## API Endpoints

### Core Domain APIs
- `GET/POST /api/v1/workers/` - Worker management
- `GET/POST /api/v1/health-exams/` - Health examination records
- `GET/POST /api/v1/work-environments/` - Environmental measurements
- `GET/POST /api/v1/educations/` - Health education tracking
- `GET/POST /api/v1/chemical-substances/` - MSDS and chemical management
- `GET/POST /api/v1/accidents/` - Accident reporting

### System APIs
- `GET /health` - System health check
- `GET /api/docs` - Swagger API documentation
- `WS /api/v1/monitoring/ws` - Real-time monitoring WebSocket
- `GET /api/v1/pipeline/status/{commit}` - CI/CD pipeline status

### Document Management
- `/api/v1/documents/` - Legacy PDF form generation
- `/api/v1/integrated-documents/` - Advanced PDF/Excel/Word editing
- `/api/v1/simple-registration/` - Mobile worker registration

## Common Issues & Solutions

### Development Issues
| Issue | Solution |
|-------|----------|
| Async fixture errors | Use `@pytest_asyncio.fixture` decorator |
| Tests hanging | Add timeout: `pytest --timeout=60` |
| Korean text issues | Ensure UTF-8 locale in PostgreSQL |
| Import errors | Check paths: `services.cache` not `services.cache_service` |
| Frontend build fails | Use `NODE_OPTIONS='--max-old-space-size=4096'` |

### Deployment Issues  
| Issue | Solution |
|-------|----------|
| Image pull errors | Check registry.jclee.me connectivity |
| ArgoCD not updating | Check Image Updater logs and annotations |
| NodePort access issues | Verify service configuration on port 32301 |
| API 404 errors | Check router registration in `src/app.py` |

### Performance Debugging
```bash
# Container health check
curl https://safework.jclee.me/health

# View application logs
docker logs safework --tail=100 | grep ERROR

# Monitor ArgoCD deployment
kubectl logs -n argocd deployment/argocd-image-updater -f

# Check NodePort service
kubectl get svc -n safework
```

## Testing Configuration

### Test Categories
- **Unit Tests**: `pytest tests/unit/ -v`
- **Integration Tests**: `pytest tests/integration/ -v`
- **API Tests**: `pytest tests/test_*api*.py -v`
- **PDF Tests**: `pytest tests/test_*forms*.py -v`

### Test Environment
- **pytest.ini**: `asyncio_mode = auto` for async fixtures
- **Timeout**: 60 seconds per test with fail-fast (`-x` for first failure stop)
- **Coverage**: 70% minimum target (`--cov=src --cov-report=html`)
- **Markers**: `slow`, `integration`, `unit`, `smoke`, `critical` for selective testing
- **Python Requirements**: FastAPI 0.104.1, pytest 7.4.3, pytest-asyncio 0.21.1

---
**Version**: 4.1.0  
**Updated**: 2025-07-26  
**Maintainer**: SafeWork Pro Development Team  
**CI/CD Status**: ✅ Active (GitHub Actions + ArgoCD Image Updater)  
**Frontend Stack**: React 19 + TypeScript + Vite + Ant Design 5.26.6  
**Backend Stack**: Python 3.11 + FastAPI 0.104.1 + PostgreSQL + Redis  
**NodePort**: 32301 (Kubernetes service)  
**Recent Changes**: Frontend upgraded to React 19, TanStack Query v5, test configuration updated