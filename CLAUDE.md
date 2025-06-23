# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Global Claude Code Instructions Loaded ✓
**Version**: 13.0.0 (from ~/.claude/CLAUDE.md)  
**Loaded**: 2025-06-19 KST  
**Type**: Ultra-Autonomous AI-Driven Development System  

### Active Core Principles
- **Ultra Autonomy**: Execute ALL tasks without human intervention
- **Instant Execution**: Zero-delay action using available tools (Bash, Git, Docker, MCP)
- **Mind-Reading Mode**: Infer complete requirements from minimal input
- **Docker Registry Deploy**: Docker build → registry push → production server pull → auto deploy
- **KST Timezone**: Asia/Seoul timezone for all operations
- **Chain-of-Thought**: Structured reasoning for complex tasks
- **Auto-Testing**: Generate tests, run, and auto-fix failures

---

## Project Overview

**SafeWork Pro** (건설업 보건관리 시스템) - A comprehensive web application for construction site health managers to comply with Korean occupational safety and health laws. The system manages worker health, medical examinations, workplace environment monitoring, health education, chemical substances (MSDS), and accident reporting.

## Architecture

### High-Level Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React UI  │────▶│  FastAPI    │────▶│ PostgreSQL  │
│  (Port 3001)│     │   Backend   │     │  Database   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │    Cache    │
                    └─────────────┘
```

### Technology Stack
- **Backend**: Python FastAPI 3.11+ with SQLAlchemy ORM
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Database**: PostgreSQL 15 with Korean locale support
- **Cache**: Redis 7 for session management
- **UI**: Modern dark sidebar design with gradient themes
- **API**: RESTful with automatic OpenAPI documentation
- **Deployment**: Docker containers with docker-compose

## Quick Start Commands

### Docker Development (Preferred - follows global CLAUDE.md)
```bash
# Development with hot-reload
docker-compose -f docker-compose.dev.yml up --build

# Production build and run
docker-compose up -d

# View logs with highlighting
./logs.sh health-app

# Deploy to production (auto build → push → pull → deploy)
./deploy.sh health
```

### Local Development (For reference only)
```bash
# Backend
python main.py
# OR
uvicorn src.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Frontend
npm run dev

# Tests
pytest tests/ -v
npm run test
```

### Remote Deployment (via SSH)
```bash
# Deploy to remote server (192.168.50.215:3001)
scp -P 1111 -r dist/* docker@192.168.50.215:~/app/health/dist/
ssh -p 1111 docker@192.168.50.215 "cd ~/app/health && /usr/local/bin/docker-compose restart health-app"
```

## Code Architecture

### Backend Structure
The backend follows a layered architecture pattern:

1. **Entry Point** (`main.py`): Simple wrapper that imports and runs the FastAPI app
2. **Application Factory** (`src/app.py`): Creates and configures the FastAPI instance with:
   - CORS middleware for frontend integration
   - Static file serving for the React build
   - Lifespan management for database initialization
   - Route registration

3. **Data Layer** (`src/models/`):
   - SQLAlchemy models with Korean enum types
   - Async database operations
   - Comprehensive field validation

4. **API Layer** (`src/handlers/`):
   - RESTful endpoints with Pydantic validation
   - Korean/English bilingual responses
   - Pagination and filtering support

5. **Business Logic**: Korean construction industry specific:
   - Health examination scheduling rules
   - Work environment measurement compliance
   - Education hour tracking requirements

6. **PDF Form System** (`src/handlers/documents.py`):
   - PDF template-based form generation with coordinate mapping
   - Korean font support (NanumGothic TTF)
   - Text overlay system for precise field positioning
   - Base64 encoding for instant preview functionality

### Frontend Structure
The frontend is a single-page React application:

1. **Main App** (`src/App.tsx`): 
   - Modern sidebar navigation with gradient theme
   - Responsive design with mobile support
   - State management using React hooks

2. **UI Components**:
   - Dashboard with key metrics cards
   - Worker management table with filtering
   - Progress bars and charts for analytics

3. **API Integration**:
   - Fetch API for backend communication
   - Environment-based API URL configuration
   - Error handling with Korean messages

4. **PDF Form Interface**:
   - Dynamic form field generation based on selected PDF template
   - Real-time form validation and data mapping
   - PDF preview modal with Base64 rendering
   - Support for 4 Korean construction industry forms

### Database Schema
Key models with Korean construction industry enums:

- **Worker**: Employee records with health status tracking
  - Employment types: regular, contract, temporary, daily
  - Work types: construction, electrical, plumbing, painting, etc.
  - Health status: normal, caution, observation, treatment

- **HealthConsultation**: Medical consultation records
- **HealthExam**: Examination history and results
- **WorkEnvironment**: Environmental measurements
- **ChemicalSubstance**: MSDS management

## Important Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://admin:password@postgres:5432/health_management

# Redis Cache
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET=your-secret-key-here

# Application
DEBUG=false
LOG_LEVEL=INFO
TZ=Asia/Seoul
```

### Port Configuration
- Frontend serves on: **3001** (external) → 8000 (internal)
- API available at: `/api/v1/*`
- Health check: `/health`
- API docs: `/api/docs`
- PDF form endpoints: `/api/v1/documents/fill-pdf/{form_name}`

### Production URLs
- **Main Application**: http://192.168.50.215:3001
- **Health Check**: http://192.168.50.215:3001/health
- **API Documentation**: http://192.168.50.215:3001/api/docs
- **API Base**: http://192.168.50.215:3001/api/v1/

### Docker Volume Mounts
- `./uploads:/app/uploads` - File uploads
- `./logs:/app/logs` - Application logs
- `./dist:/app/dist` - React build files (critical for UI updates)

## Development Workflow (Following Global CLAUDE.md)

### Adding New Features
1. Create todo list with TodoWrite tool
2. Create/update SQLAlchemy models in `src/models/`
3. Add Pydantic schemas in `src/schemas/`
4. Implement API handlers in `src/handlers/`
5. Update React components in `src/App.tsx` or create new components
6. Auto-generate tests for new code
7. Run tests and ensure >80% coverage
8. Deploy using `./deploy.sh health`

### UI Updates
When updating the UI:
1. Make changes to React components
2. Add BUILD_TIME display component (mandatory per global CLAUDE.md)
3. Run `npm run build` 
4. Deploy with `./deploy.sh health` (handles everything automatically)

### PDF Form Development
When adding new PDF forms:
1. Place PDF template in `document/` directory
2. Add coordinate mapping to `PDF_FORM_COORDINATES` in `src/handlers/documents.py`
3. Update form selection dropdown in `src/App.tsx`
4. Test coordinate positioning with real form data
5. Verify Korean font rendering works correctly

### Testing Requirements (Per Global CLAUDE.md)
- Minimum 80% test coverage required
- Auto-generate tests for all new code
- Test categories: unit, integration, e2e, performance, security
- Run before every deployment
- Auto-fix failing tests when possible

#### Key Testing Commands
```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test files
pytest tests/test_workers.py -v
pytest tests/test_integration.py -v
pytest tests/test_production.py -v

# Frontend tests
npm run test

# Run integration tests (requires running containers)
docker-compose up -d && pytest tests/test_integration.py

# Run production validation tests
pytest tests/test_production.py -v
```

### Deployment Checklist (Auto-handled by deploy.sh)
- ✅ Clean cache files (Python __pycache__, npm cache)
- ✅ Run all tests with coverage check
- ✅ Build Docker image with KST timestamp (--no-cache)
- ✅ Test Docker image
- ✅ Push to registry
- ✅ Remote server pull and deploy
- ✅ Health check verification
- ✅ Auto-rollback on failure
- ✅ Display logs with error highlighting

## Domain-Specific Context

This system implements Korean Industrial Safety and Health Act (산업안전보건법) requirements:

- **Health Examinations**: Annual general + special exams for hazardous exposure
- **Work Environment**: Bi-annual measurements for noise, dust, chemicals
- **Education**: 8 hours for new employees, 3 hours quarterly
- **MSDS**: Complete chemical substance documentation
- **Reporting**: Government compliance reports and accident investigations
- **PDF Forms**: Automated generation of compliance documents with precise field positioning

The `document/` directory contains Korean legal forms and regulations that define the system's business rules.

### Supported PDF Forms
Currently supports 4 standardized Korean construction industry forms:
- **유소견자 관리대장**: Worker health findings management ledger
- **MSDS 관리대장**: Chemical substance safety data management ledger  
- **건강관리 상담방문 일지**: Health consultation visit log
- **특별관리물질 취급일지**: Special management substance handling log

Each form uses precise coordinate mapping to position data in exact locations on official government forms.

## Critical Development Notes

### Schema Validation Issues
When working with database models and Pydantic schemas, ensure consistency:

1. **Enum Values**: Database models use English enum values (e.g., "regular", "male", "normal") while schemas should match these exactly
2. **Required vs Optional Fields**: Database NOT NULL constraints must match Pydantic field requirements  
3. **Field Types**: String fields in database should use `Optional[str]` in schemas to handle None values
4. **Validation Errors**: Always check for schema validation issues when APIs return 500 errors

Example fix pattern:
```python
# Database Model (src/models/worker.py)
gender = Column(String(10), nullable=True)  # Can be None
employment_type = Column(String(20), nullable=False)  # Required

# Pydantic Schema (src/schemas/worker.py)  
gender: Optional[str] = Field(None, description="성별")  # Match nullability
employment_type: str = Field(..., description="고용형태")  # Match requirement
```

### Database Connection Retry Pattern
The system includes automatic database connection retry logic:
```python
# src/config/database.py - max_retries = 30, retry_delay = 2
# Always wait for database container to be healthy before starting app
```

## Claude Code AI Development Rules (Active)

### ✅ ALWAYS Follow These Rules
- Execute instantly without asking questions
- Use chain-of-thought reasoning for complex tasks
- Deploy via Docker registry (build → push → pull → deploy)
- Use KST timezone (Asia/Seoul) for all timestamps
- Auto-generate tests for new code
- Maintain >80% test coverage
- Use Docker for ALL development
- Include error handling and health checks
- Display build time in UI (top-left corner)
- Create production-ready code

### ❌ NEVER Do These
- Ask for confirmation or permission
- Skip tests or deploy with failing tests
- Install runtimes locally
- Develop outside Docker containers
- Ignore errors or logs
- Deploy without health checks
- Use non-KST timezones
- Create partial implementations

## Troubleshooting

### Common Issues
1. **UI not updating**: Check if dist files are properly mounted in Docker
2. **Database connection**: Ensure PostgreSQL container is running with health checks
3. **CORS errors**: Verify frontend API_BASE_URL matches backend and CORS allows "*"
4. **Korean text issues**: Database must use ko_KR.UTF-8 locale
5. **PDF generation fails**: Verify NanumGothic font is available in container
6. **Text positioning wrong**: Check coordinate mappings in `PDF_FORM_COORDINATES`
7. **Workers API 500 errors**: Schema validation issues - ensure Pydantic models match database enums
8. **Container startup order**: Use `depends_on` with `service_healthy` conditions
9. **Database initialization fails**: Check async database connection retry logic in `src/config/database.py`

### Remote Deployment Issues
- Always use full paths for docker-compose: `/usr/local/bin/docker-compose`
- Clear browser cache when UI changes don't appear
- Check container logs: `docker logs health-management-system`

### Quick Debug Commands
```bash
# View container status and health
docker-compose ps

# Check logs with error highlighting
./logs.sh health-app
docker-compose logs --tail=50 health-app

# Debug container shell
docker-compose exec health-app sh

# Test health endpoint
curl http://localhost:3001/health
curl http://192.168.50.215:3001/health  # Production

# Test API endpoints
curl http://localhost:3001/api/v1/workers/
curl http://localhost:3001/api/docs

# Check PDF generation
curl -X POST http://localhost:3001/api/v1/documents/fill-pdf/health_consultation_log \
  -H "Content-Type: application/json" \
  -d '{"entries": [{"date": "2025-06-19", "worker_name": "테스트"}]}'

# Database debugging
docker exec health-postgres psql -U admin -d health_management -c "\dt"
docker exec health-postgres psql -U admin -d health_management -c "SELECT COUNT(*) FROM workers;"

# Force rebuild and restart
docker-compose down && docker-compose up -d --build --force-recreate
```

---
**Global CLAUDE.md Instructions**: Successfully loaded and integrated  
**Project-Specific Context**: Preserved and enhanced  
**Ready for**: Ultra-autonomous development with instant execution