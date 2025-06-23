# Task Completion Workflow

## ✅ Required Steps When Task is Completed

### **1. Code Quality Checks**
```bash
# Backend formatting and linting
black src/ tests/                    # Format Python code
isort src/ tests/                    # Sort imports
flake8 src/ tests/                   # Check code style
mypy src/                           # Type checking

# Frontend linting
npm run lint                        # ESLint checking
npm run lint:fix                    # Auto-fix linting issues
npx tsc --noEmit                    # TypeScript type checking
```

### **2. Testing Requirements**
```bash
# Backend tests (REQUIRED: >80% coverage)
pytest tests/ -v --cov=src --cov-report=html
pytest tests/ --cov=src --cov-fail-under=80

# Frontend tests
npm run test                        # Vitest tests
npm run test -- --coverage         # With coverage report

# Integration tests (if API changes made)
docker-compose up -d
pytest tests/test_integration.py -v

# Production validation (before deployment)
pytest tests/test_production.py -v
```

### **3. Build Validation**
```bash
# Frontend build (REQUIRED before deployment)
npm run build                       # Create production build
npm run preview                     # Test built application

# Docker build test
docker build --no-cache -t health-app-test .
docker run --rm health-app-test python -c "import src.app; print('Import successful')"
```

### **4. Database Changes** (if applicable)
```bash
# Test database migrations
python init_db.py                  # Initialize fresh database
pytest tests/test_workers.py -v    # Test data operations

# Verify optimization if models changed
docker-compose exec health-app python -c "
from src.models.migration_optimized import optimize_database
optimize_database()
"
```

### **5. Documentation Updates** (if required)
```bash
# Update API documentation (auto-generated)
# Visit: http://localhost:3001/api/docs

# Update CLAUDE.md if architecture changes
# Update README.md if major features added

# Update type definitions if schemas changed
# Verify TypeScript interfaces match Python schemas
```

### **6. Security Validation**
```bash
# Check for security vulnerabilities
npm audit                          # Frontend dependencies
pip-audit                          # Backend dependencies (if available)

# Validate environment variables
grep -r "password\|secret\|key" src/ --exclude-dir=__pycache__
# Ensure no hardcoded secrets in code
```

### **7. Performance Validation**
```bash
# Test API performance
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:3001/api/v1/workers/

# Check database query performance
docker exec health-postgres psql -U admin -d health_management -c "
EXPLAIN ANALYZE SELECT * FROM workers WHERE name ILIKE '%test%';
"

# Monitor memory usage
docker stats health-management-system
```

### **8. Deployment Process**
```bash
# PREFERRED: Automated deployment
./deploy.sh health

# MANUAL: Step-by-step deployment
npm run build
docker build --no-cache -t health-app .
docker tag health-app registry/health-app:$(date +%Y%m%d-%H%M%S)
docker push registry/health-app:latest

# Production deployment
scp -P 1111 -r dist/* docker@192.168.50.215:~/app/health/dist/
ssh -p 1111 docker@192.168.50.215 "cd ~/app/health && /usr/local/bin/docker-compose restart health-app"
```

### **9. Post-Deployment Validation**
```bash
# Health check validation
curl -s http://192.168.50.215:3001/health | jq .

# API functionality test
curl -s http://192.168.50.215:3001/api/v1/workers/ | jq .

# PDF generation test (if documents changed)
curl -X POST http://192.168.50.215:3001/api/v1/documents/fill-pdf/health_consultation_log \
  -H "Content-Type: application/json" \
  -d '{"entries": [{"date": "2025-06-19", "worker_name": "테스트"}]}'

# Log monitoring
ssh -p 1111 docker@192.168.50.215 "docker logs --tail=50 health-management-system"
```

### **10. Documentation & Communication**
```bash
# Update OPTIMIZATION_SUMMARY.md if major improvements made
# Document any breaking changes
# Update version numbers if applicable
# Notify stakeholders of deployment completion
```

## 🚨 Critical Validation Points

### **MUST PASS Before Deployment**:
- [ ] All tests pass with >80% coverage
- [ ] TypeScript compilation successful
- [ ] Frontend build creates valid dist/ directory
- [ ] Docker container builds and starts successfully
- [ ] Health endpoint returns 200 status
- [ ] No hardcoded secrets in code
- [ ] Environment variables properly configured

### **MUST VERIFY After Deployment**:
- [ ] Production health check responds correctly
- [ ] All API endpoints accessible
- [ ] Frontend loads and functions properly
- [ ] Database connections established
- [ ] Logs show no critical errors
- [ ] PDF generation works (if applicable)

## 🔧 Automation Scripts

### **Pre-commit Hook** (recommended)
```bash
#!/bin/bash
# .git/hooks/pre-commit
set -e

echo "Running pre-commit checks..."

# Format and lint
black src/ tests/
isort src/ tests/
npm run lint:fix

# Test
pytest tests/ --cov=src --cov-fail-under=80
npm run test

# Build
npm run build

echo "All pre-commit checks passed!"
```

### **Deployment Script Enhancement**
```bash
#!/bin/bash
# Enhanced deploy.sh

set -e

echo "🚀 Starting deployment process..."

# 1. Quality checks
npm run lint
pytest tests/ -v --cov=src --cov-fail-under=80

# 2. Build
npm run build
docker build --no-cache -t health-app .

# 3. Local validation
docker run --rm health-app curl -f http://localhost:8000/health

# 4. Deploy
scp -P 1111 -r dist/* docker@192.168.50.215:~/app/health/dist/
ssh -p 1111 docker@192.168.50.215 "cd ~/app/health && /usr/local/bin/docker-compose restart health-app"

# 5. Validate
sleep 10
curl -f http://192.168.50.215:3001/health

echo "✅ Deployment completed successfully!"
```

## 📊 Success Metrics

### **Code Quality Metrics**:
- Test coverage: >80%
- Type coverage: >95%
- Linting errors: 0
- Security vulnerabilities: 0

### **Performance Metrics**:
- API response time: <500ms average
- Frontend load time: <3 seconds
- Database query time: <100ms average
- PDF generation: <2 seconds

### **Deployment Metrics**:
- Deployment time: <5 minutes
- Zero downtime: 100%
- Rollback capability: Available
- Health check: 100% success rate