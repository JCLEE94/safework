# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SafeWork Pro** (건설업 보건관리 시스템) - A comprehensive web application for construction site health management complying with Korean occupational safety and health laws. Manages worker health, medical examinations, workplace monitoring, health education, chemical substances (MSDS), and accident reporting.

### Repository Information
- **GitHub**: JCLEE94/safework (previously qws941/health)
- **Registry**: registry.jclee.me/safework:latest (public registry, no auth required)
- **Production**: https://safework.jclee.me
- **Architecture**: All-in-one container (PostgreSQL + Redis + FastAPI + React)
- **CI/CD**: GitHub Actions + ArgoCD Image Updater (automated image deployment)

### Frontend V2 Information
- **Framework**: React 18 + TypeScript + Vite
- **UI Library**: Ant Design 5.x
- **State Management**: Redux Toolkit (client state) + React Query/TanStack Query (server state)
- **Styling**: Styled Components + CSS-in-JS
- **Build Tool**: Vite 7.x
- **Package Manager**: npm

## Quick Commands

### Development
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=html --cov-report=term --timeout=300 -x

# Run single test file
pytest tests/test_workers.py -v

# Run tests by marker (skip slow tests)
pytest -m "not slow" -v

# Run integration tests only
pytest -m integration -v

# Run with specific timeout
pytest tests/test_api.py -v --timeout=120

# Lint and format
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# Frontend V2 development (run from safework-frontend-v2/ directory)
cd safework-frontend-v2 && npm install    # Install dependencies
cd safework-frontend-v2 && npm run dev    # Start Vite dev server (port 5173)
cd safework-frontend-v2 && npm run build  # Build for production
cd safework-frontend-v2 && npm run lint   # Run ESLint
cd safework-frontend-v2 && npm run preview # Preview production build

# Frontend V1 development (legacy - run from frontend/ directory)
cd frontend && npm run dev          # Start Vite dev server (port 5173)
cd frontend && npm run build        # Build for production
cd frontend && npm run preview      # Preview production build
```

### Testing Configuration
- **pytest.ini**: Configured with `asyncio_mode = auto` for async fixtures
- **Timeout**: 60 seconds per test (optimized from 300), fail-fast with `-x --maxfail=5`
- **Dependencies**: pytest, pytest-asyncio, pytest-cov, pytest-timeout
- **Test markers**: `slow`, `integration`, `unit` - use `-m "not slow"` to skip slow tests
- **Coverage target**: 70% minimum (configured in CI/CD)

### Deployment
```bash
# Deploy to production (automated CI/CD via GitHub Actions + ArgoCD Image Updater)
git add . && git commit -m "feat: description" && git push

# Manual deployment (backup)
./scripts/deploy/deploy-main.sh

# Check deployment status
curl https://safework.jclee.me/health
docker logs safework --tail=50

# Monitor pipeline status
gh run list --limit 5
gh run view <run-id> --log-failed

# Check ArgoCD Image Updater logs
kubectl logs -n argocd deployment/argocd-image-updater -f
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

#### Frontend V2 (`safework-frontend-v2/`) - Modern Architecture
- `src/App.tsx` - Main app with providers (Redux, React Query, Ant Design)
- `src/components/` - Atomic Design structure
  - `atoms/` - Basic UI elements (Button, Input, etc.)
  - `molecules/` - Composite components
  - `organisms/` - Complex components (DataTable, etc.)
  - `templates/` - Page layouts (DashboardLayout)
- `src/features/` - Feature-based module structure
  - Each feature has: components/, hooks/, pages/, services/, types/
  - Examples: health-monitoring/, incident-management/, compliance/
- `src/pages/` - Route-level page components
- `src/services/api/` - API client layer with typed endpoints
- `src/store/` - Redux store with feature slices
- `src/utils/` - Shared utilities (formatters, validators)
- `src/routes/` - React Router configuration
- `src/styles/` - Global styles and Ant Design theme

#### Frontend V1 (`frontend/`) - Legacy
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

### GitHub Actions Configuration
- **Runners**: GitHub-hosted (ubuntu-latest) for stability
- **Service containers**: PostgreSQL (port 5432), Redis (port 6379)
- **Test timeout**: 5 minutes per test type
- **ArgoCD Image Updater**: Automatically detects and deploys new images
- **Concurrency**: Cancels previous runs on new push to same branch
- **Registry**: registry.jclee.me (public, no authentication)

### Workflow Files
- `gitops-deploy.yml` - GitOps CI/CD pipeline with ArgoCD Image Updater
- Service containers and optimized build process
- Helm chart deployment to ChartMuseum

### Environment Variables (CI/CD)
```yaml
DATABASE_URL: postgresql://admin:password@localhost:5432/health_management
REDIS_URL: redis://localhost:6379/0
JWT_SECRET: test-secret-key
PYTHONPATH: ${{ github.workspace }}
ENVIRONMENT: development  # For test runs
```

## Deployment Pipeline

### Automated Flow (ArgoCD Image Updater)
```
1. Git Push (main) → GitHub Actions (GitHub-hosted runner)
2. Run Tests (parallel) → Build Docker Image → Push to registry.jclee.me
3. ArgoCD Image Updater detects new image (no manual commits needed)
4. Image Updater updates K8s manifests automatically
5. ArgoCD auto-sync → Deploy to Kubernetes cluster
6. Production health check at https://safework.jclee.me/health
```

### ArgoCD Configuration
- Monitors Git repository k8s/ directory for changes
- Auto-sync enabled with self-healing
- ArgoCD Image Updater monitors registry.jclee.me for new images
- Image pattern: `^prod-[0-9]{8}-[a-f0-9]{7}$`
- Dashboard: https://argo.jclee.me/applications/safework

### Image Tagging Strategy
- Production: `prod-YYYYMMDD-SHA7` (e.g., prod-20250104-abc1234)
- Semantic Version: `1.YYYYMMDD.BUILD_NUMBER` (e.g., 1.20250110.123)
- Latest: Always points to most recent production build
- ArgoCD Image Updater tracks these patterns automatically

## Common Issues & Solutions

### Development Issues
| Issue | Solution |
|-------|----------|
| Docker 413 error | Use optimized Dockerfile and registry.jclee.me |
| Self-hosted runner issues | Switch to GitHub-hosted runners |
| Port conflicts in CI | Use standard ports (5432, 6379) with GitHub-hosted runners |
| Async fixture errors | Use `@pytest_asyncio.fixture` decorator |
| Import errors | Check import paths (e.g., `services.cache` not `services.cache_service`) |
| Tests hanging | Add timeout configuration (pytest-timeout) |
| Korean text garbled | Ensure ko_KR.UTF-8 locale in PostgreSQL |
| Environment variable missing | Check settings.py defaults and use `generate_*_url()` methods |
| Authentication errors | Set `ENVIRONMENT=development` for bypassed auth in dev |
| API endpoint 404s | Check router prefix in handlers and app.py registration |
| ArgoCD not updating | Check Image Updater logs and annotations |
| PyMuPDF import errors | Ensure PyMuPDF is installed: `pip install PyMuPDF` |
| Document editing fails | Check file permissions in `document/` directory |
| Mobile registration issues | Test `/register` route accessibility without auth |

### Production Debugging
```bash
# Container health
docker ps | grep safework
curl https://safework.jclee.me/health

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
- `/api/v1/documents/` - Legacy document management (PDF generation)
- `/api/v1/integrated-documents/` - New integrated document system (PDF/Excel/Word editing)
- `/api/v1/simple-registration/` - Simple worker registration (mobile-friendly)
- `/api/v1/monitoring/ws` - WebSocket real-time monitoring
- `/api/v1/pipeline/status/{commit}` - CI/CD pipeline status

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

### Required Secrets (GitHub)
```bash
REGISTRY_USERNAME
REGISTRY_PASSWORD
CHARTMUSEUM_USERNAME
CHARTMUSEUM_PASSWORD
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

### Frontend V2 API Integration Pattern
Frontend V2 uses axios-based API client with TypeScript interfaces:
```typescript
// src/services/api/baseApi.ts
import axios from 'axios';

const API_BASE = '/api/v1';
export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' }
});

// src/services/api/workers.ts
export interface Worker {
  id: number;
  name: string;
  employee_id: string;
  department: string;
  // ...
}

export const workersApi = {
  getList: (params?: any) => 
    apiClient.get<Worker[]>('/workers/', { params }),
  create: (data: Omit<Worker, 'id'>) => 
    apiClient.post<Worker>('/workers/', data),
  update: (id: number, data: Partial<Worker>) =>
    apiClient.put<Worker>(`/workers/${id}`, data)
};
```

### Frontend V2 State Management Pattern
Uses Redux Toolkit for client state and React Query for server state:
```typescript
// React Query for server state
const { data, isLoading, error } = useQuery({
  queryKey: ['workers', filters],
  queryFn: () => workersApi.getList(filters),
});

// Redux Toolkit for UI state
const dispatch = useAppDispatch();
const { sidebarCollapsed } = useAppSelector((state) => state.ui);
dispatch(uiActions.toggleSidebar());
```

### Frontend V1 API Integration Pattern (Legacy)
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
The settings system provides defaults for all environments while enforcing security in production:

```python
# src/config/settings.py pattern:
class Settings(BaseSettings):
    # Development-friendly defaults with environment variable overrides
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    jwt_secret: str = Field(default="dev-jwt-secret-change-in-production", env="JWT_SECRET")
    
    # Dynamic URL generation methods
    def generate_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
```

Environment usage:
```bash
# Development
ENVIRONMENT=development docker-compose up

# Production
docker-compose up -d  # Uses default production config

# Testing (CI/CD) - Uses defaults with service container ports
DATABASE_URL=postgresql://admin:password@localhost:5432/health_management
REDIS_URL=redis://localhost:6379/0
```

### Document Management Systems
The project has two document management approaches:

1. **Legacy Documents** (`/api/v1/documents/`) - PDF form filling and template-based generation
2. **Integrated Documents** (`/api/v1/integrated-documents/`) - Advanced PDF/Excel/Word editing with PyMuPDF

```python
# Integrated document editing pattern
from src.handlers.integrated_documents import router

# PDF editing with text insertion
pdf_data = {
    "text_inserts": [{
        "text": "Sample text",
        "x": 100, "y": 100,
        "font_size": 12,
        "color": "black"
    }]
}

# Excel editing with cell data
excel_data = {
    "cell_data": {
        "A1": "Value",
        "B1": "Another value"
    }
}
```

### Simple Worker Registration
Mobile-friendly worker registration system without QR codes:
- **URL**: `/register` (public access, no authentication)
- **API**: `/api/v1/simple-registration/worker`
- **Features**: Employee ID duplicate checking, mobile-optimized UI
- **Usage**: Direct phone registration instead of complex QR token system

## Recent Best Practices & Lessons Learned

### CI/CD Optimization (2025-01-10)
1. **Registry Migration**: Moved from ghcr.io to registry.jclee.me (public registry)
   - Resolved 413 Request Entity Too Large errors
   - No authentication required for public registry
   - Optimized Docker images (50% size reduction)

2. **ArgoCD Image Updater**: Automated image deployment
   - No manual K8s manifest updates needed
   - Automatic detection of new images
   - Git write-back for audit trail
   - Semantic versioning support

3. **GitHub-hosted Runners**: Better stability
   - Resolved self-hosted runner Docker permission issues
   - Standard port usage (5432, 6379)
   - Faster parallel test execution

4. **Project Structure**: Major cleanup completed
   - Removed 38+ duplicate files
   - Organized scripts into logical directories
   - Consolidated Docker Compose configurations
   - Created comprehensive documentation structure

### Recent Features Added (2025-07-26)
1. **Frontend V2 Complete Refactoring**
   - Modern React architecture with TypeScript
   - Ant Design 5.x for professional UI components
   - Redux Toolkit + React Query for optimal state management
   - Atomic Design pattern for component organization
   - Feature-based module structure for better scalability
   - Vite for fast development and optimized builds

2. **Integrated Document Management System** (2025-07-24)
   - PyMuPDF integration for advanced PDF editing
   - Excel/Word document manipulation with openpyxl
   - Document categories: 10 predefined categories (업무매뉴얼, 법정서식, etc.)
   - API prefix: `/api/v1/integrated-documents/` (separated from legacy system)

3. **Simple Worker Registration System** (2025-07-24)
   - Mobile-first design for direct worker registration
   - Eliminated complex QR code token generation process
   - Real-time employee ID duplicate checking
   - Public access route: `/register` (no authentication required)
   - Backend: `src/handlers/simple_worker_registration.py`
   - Frontend: `frontend/src/components/SimpleWorkerRegistration.tsx`

### Project Organization (2025-07-26)
```
safework/
├── src/                    # Backend source code
├── frontend/               # Frontend V1 source code (legacy)
├── safework-frontend-v2/   # Frontend V2 source code (modern)
│   ├── src/                # Source files
│   │   ├── components/     # Atomic Design components
│   │   │   ├── atoms/      # Basic UI elements
│   │   │   ├── molecules/  # Composite components
│   │   │   ├── organisms/  # Complex components
│   │   │   └── templates/  # Page layouts
│   │   ├── features/       # Feature modules
│   │   ├── pages/          # Route pages
│   │   ├── services/       # API services
│   │   ├── store/          # Redux store
│   │   ├── routes/         # React Router config
│   │   ├── hooks/          # Custom React hooks
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utilities
│   ├── public/             # Static assets
│   ├── package.json        # Dependencies
│   ├── tsconfig.json       # TypeScript config
│   ├── vite.config.ts      # Vite build config
│   ├── Dockerfile          # Docker build config
│   └── nginx.conf          # Nginx server config
├── tests/                  # All test files (consolidated)
├── scripts/                # All scripts (organized)
│   ├── deploy/             # Deployment scripts
│   │   ├── deploy-frontend-v2.sh
│   │   ├── deploy-frontend-v2-local.sh
│   │   ├── canary-deploy-frontend.sh
│   │   ├── migrate-to-v2.sh
│   │   └── test-frontend-v2.sh
│   ├── setup/              # Setup scripts
│   └── utils/              # Utility scripts
├── k8s/                    # Kubernetes configurations
│   ├── base/               # Base resources
│   ├── argocd/             # ArgoCD configurations
│   ├── safework/           # Application manifests (legacy)
│   ├── safework-frontend-v2/ # Frontend V2 K8s manifests
│   │   ├── deployment.yaml
│   │   ├── deployment-local.yaml
│   │   ├── service.yaml
│   │   ├── ingress.yaml
│   │   └── kustomization.yaml
│   ├── cloudflare/         # Cloudflare tunnel configs
│   └── helm/               # Helm charts
├── docs/                   # Documentation
│   ├── deployment/         # Deployment guides
│   └── setup/              # Setup guides
├── deployment/             # Docker configurations
└── 재설계.pdf              # System redesign specification
```

### Frontend V2 Deployment
```bash
# Build and run Frontend V2 locally
cd safework-frontend-v2
npm install
npm run build

# Deploy to Kubernetes
cd scripts/deploy
./deploy-frontend-v2.sh        # Standard deployment
./canary-deploy-frontend.sh    # Canary deployment
./migrate-to-v2.sh            # Full migration from V1 to V2

# Test deployment
./test-frontend-v2.sh

# Rollback if needed
kubectl patch ingress safework -n safework --type='json' \
  -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value":"safework"}]'
```

## Frontend V2 Key Features

### Modern Architecture
1. **Component Architecture**: Atomic Design pattern
   - Atoms: Button, Input, Label, Icon components
   - Molecules: Form fields, Search bars, Card headers
   - Organisms: DataTable, Navigation, Complex forms
   - Templates: DashboardLayout, AuthLayout

2. **State Management**: Hybrid approach
   - Redux Toolkit: UI state, theme, user preferences
   - React Query: Server state, caching, background refetch
   - Local state: Component-specific interactions

3. **Type Safety**: Full TypeScript coverage
   - Strict mode enabled
   - Interface definitions for all API responses
   - Type-safe Redux actions and selectors
   - Generics for reusable components

4. **Performance Optimizations**
   - Code splitting with React.lazy
   - Virtual scrolling for large lists
   - Memoization with React.memo and useMemo
   - Optimistic UI updates
   - Image lazy loading

### UI/UX Improvements
- **Responsive Design**: Mobile-first approach with breakpoints
- **Dark Mode**: System preference detection and manual toggle
- **Accessibility**: WCAG 2.1 AA compliance
- **Internationalization**: Korean/English support ready
- **Loading States**: Skeleton screens and progress indicators
- **Error Handling**: Graceful error boundaries with recovery

### Development Experience
- **Hot Module Replacement**: Instant feedback during development
- **ESLint + Prettier**: Consistent code style
- **Husky + lint-staged**: Pre-commit hooks
- **Jest + React Testing Library**: Unit and integration tests
- **Storybook**: Component documentation and testing

## System Redesign Overview (재설계.pdf)

The system underwent a comprehensive redesign based on the specifications in 재설계.pdf, focusing on:

1. **Service-Oriented Architecture**
   - Modular service design
   - Clear separation of concerns
   - API-first approach
   - Microservices-ready architecture

2. **Enhanced Security**
   - OAuth 2.0 + JWT tokens
   - Role-based access control (RBAC)
   - API rate limiting
   - Input validation and sanitization

3. **Scalability Improvements**
   - Horizontal scaling support
   - Database connection pooling
   - Redis caching layer
   - CDN integration ready

4. **Monitoring & Observability**
   - Structured logging
   - Metrics collection
   - Distributed tracing ready
   - Health check endpoints

## Troubleshooting Guide

### Frontend V2 Issues
| Issue | Solution |
|-------|----------|
| Build fails with memory error | Increase Node memory: `NODE_OPTIONS='--max-old-space-size=4096' npm run build` |
| TypeScript errors after update | Delete node_modules and package-lock.json, then reinstall |
| Ant Design styles not loading | Check ConfigProvider theme configuration in App.tsx |
| API calls fail with CORS | Ensure backend CORS middleware includes frontend URL |
| Redux DevTools not showing | Install browser extension and check store configuration |
| React Query cache issues | Clear cache with queryClient.clear() or adjust staleTime |

### Deployment Issues
| Issue | Solution |
|-------|----------|
| Image pull errors in K8s | Check imagePullSecrets and registry credentials |
| Frontend V2 not accessible | Verify ingress configuration and service selector |
| Environment variables missing | Check ConfigMap and Secret configurations |
| Health check failures | Ensure /health endpoint returns 200 status |

---
**Version**: 3.7.0  
**Updated**: 2025-07-26  
**Maintainer**: SafeWork Pro Development Team  
**CI/CD Status**: ✅ Active (GitHub-hosted runners + ArgoCD Image Updater)  
**Recent Changes**: Frontend V2 complete refactoring with modern React architecture, Ant Design UI, Redux Toolkit + React Query state management, comprehensive system redesign implementation
