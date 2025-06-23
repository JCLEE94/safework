# Testing & Deployment Patterns

## 🧪 Comprehensive Testing Architecture

### **Testing Structure**:
```
tests/
├── conftest.py           # Pytest configuration and fixtures
├── unit/                 # Unit tests for individual components
├── integration/          # Integration tests for API endpoints
├── test_production.py    # Production environment validation
├── test_integration.py   # Full system integration tests
└── test_*_forms.py      # PDF form generation tests
```

### **Testing Technologies**:
- **Backend**: Pytest with async support, SQLAlchemy test sessions
- **Frontend**: Vitest with React Testing Library
- **API Testing**: HTTP client testing with FastAPI TestClient
- **PDF Testing**: Complete form generation validation

### **Key Testing Patterns**:

#### **Async Test Configuration**:
```python
@pytest.fixture
async def async_session():
    # Test database session with rollback
    async with test_engine.begin() as conn:
        async with AsyncSession(conn) as session:
            yield session
            await session.rollback()
```

#### **API Integration Tests**:
```python
async def test_worker_crud_operations(client: AsyncClient):
    # Create, read, update, delete workflow
    # Test Korean/English data handling
    # Validate response schemas
```

#### **PDF Generation Tests**:
```python
async def test_all_pdf_forms():
    # Test 4 Korean construction forms
    # Validate coordinate positioning
    # Check Korean font rendering
    # Verify Base64 encoding
```

## 🚀 Advanced Deployment System

### **Docker-Based Deployment**

#### **Multi-Stage Build** (`Dockerfile`):
```dockerfile
# Frontend build stage
FROM node:18-alpine AS frontend-builder
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Python backend stage  
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY --from=frontend-builder /app/dist ./dist
```

#### **Production Configuration** (`docker-compose.yml`):
- **Health Checks**: Application and database monitoring
- **Service Dependencies**: Proper startup ordering
- **Volume Mounts**: Persistent data and logs
- **Network Isolation**: Secure container communication

### **Deployment Automation** (`deploy.sh`)

#### **Deployment Pipeline**:
1. **Build Validation**: Type checking and linting
2. **Test Execution**: Full test suite with coverage
3. **Docker Build**: Multi-stage containerization
4. **Health Validation**: Service startup verification
5. **Rolling Deployment**: Zero-downtime updates

#### **Production Deployment Process**:
```bash
# Local build and test
npm run build && pytest tests/ -v

# Docker containerization
docker build --no-cache -t health-app .

# Production deployment
scp -r dist/ docker@192.168.50.215:~/app/health/
ssh docker@192.168.50.215 "docker-compose restart health-app"

# Health verification
curl http://192.168.50.215:3001/health
```

## 🔍 Testing Coverage & Quality

### **Coverage Requirements**:
- **Backend**: >80% code coverage with pytest-cov
- **Frontend**: Component and integration testing
- **API**: All endpoints tested with success/error scenarios
- **PDF Generation**: Complete form validation

### **Quality Gates**:
- **Type Safety**: Full TypeScript and Python type checking
- **Linting**: ESLint, Prettier, Black, isort
- **Security**: Dependency vulnerability scanning
- **Performance**: Load testing and optimization

### **Continuous Integration**:
```yaml
# .gitlab-ci.yml pattern
stages:
  - lint
  - test  
  - build
  - deploy
  
test:
  script:
    - pytest tests/ --cov=src --cov-report=html
    - npm run test
    - npm run build
```

## 🌐 Production Environment

### **Infrastructure Setup**:
- **Server**: 192.168.50.215:3001
- **Reverse Proxy**: Nginx with SSL termination
- **Container Registry**: Docker Hub or private registry
- **Monitoring**: Application logs and health checks

### **Environment Configuration**:
```env
# Production environment variables
DATABASE_URL=postgresql://admin:password@postgres:5432/health_management
REDIS_URL=redis://redis:6379/0
DEBUG=false
LOG_LEVEL=INFO
TZ=Asia/Seoul
```

### **Security Considerations**:
- **Container Security**: Non-root user execution
- **Secret Management**: Environment variable injection
- **Network Security**: Internal container communication
- **Data Protection**: Volume encryption and backup

### **Monitoring & Observability**:
- **Health Checks**: `/health` endpoint monitoring
- **Log Aggregation**: Structured JSON logging
- **Performance Metrics**: Request duration and error rates
- **Resource Monitoring**: Container CPU/memory usage

## 🔄 Development Workflow

### **Local Development**:
```bash
# Development environment
docker-compose -f docker-compose.dev.yml up --build

# Hot reload enabled
# Debug logging active
# Development database
```

### **Testing Workflow**:
```bash
# Backend tests
pytest tests/ -v --cov=src

# Frontend tests  
npm run test

# Integration tests
pytest tests/test_integration.py -v

# Production validation
pytest tests/test_production.py -v
```

### **Deployment Workflow**:
```bash
# Automated deployment
./deploy.sh health

# Manual deployment steps
npm run build
docker build -t health-app .
docker push registry/health-app:latest
ssh production-server "docker pull && docker-compose restart"
```