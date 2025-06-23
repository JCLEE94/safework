# Essential Development Commands

## 🚀 Quick Start Commands

### **Docker Development (Recommended)**
```bash
# Start development environment with hot-reload
docker-compose -f docker-compose.dev.yml up --build

# Production deployment
docker-compose up -d

# View application logs
docker-compose logs -f health-app

# View logs with error highlighting  
./logs.sh health-app

# Deploy to production server
./deploy.sh health
```

### **Local Development (Alternative)**
```bash
# Backend (Python FastAPI)
python main.py
# OR
uvicorn src.app:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Frontend (React + Vite)
npm run dev

# Build frontend
npm run build
```

## 🧪 Testing Commands

### **Backend Testing**
```bash
# Run all tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_workers.py -v
pytest tests/test_integration.py -v  
pytest tests/test_production.py -v

# Run tests for specific functionality
pytest tests/test_*_forms.py -v  # PDF form tests
pytest tests/unit/ -v            # Unit tests only
pytest tests/integration/ -v     # Integration tests only
```

### **Frontend Testing**
```bash
# Run frontend tests
npm run test

# Run tests with coverage
npm run test -- --coverage

# Build and test
npm run build && npm run preview
```

### **Integration Testing**
```bash
# Start containers first, then run integration tests
docker-compose up -d && pytest tests/test_integration.py -v

# Test production environment
pytest tests/test_production.py -v
```

## 🔧 Development Tools

### **Code Quality**
```bash
# Python formatting and linting
black src/ tests/
isort src/ tests/
flake8 src/ tests/

# TypeScript linting  
npm run lint
npm run lint:fix

# Type checking
mypy src/
npx tsc --noEmit
```

### **Database Operations**
```bash
# Initialize database
python init_db.py

# Database shell access
docker exec -it health-postgres psql -U admin -d health_management

# View database contents
docker exec health-postgres psql -U admin -d health_management -c "\\dt"
docker exec health-postgres psql -U admin -d health_management -c "SELECT COUNT(*) FROM workers;"
```

## 🐛 Debugging Commands

### **Container Debugging**
```bash
# View container status
docker-compose ps

# Check container health
docker-compose exec health-app curl http://localhost:8000/health

# Access container shell
docker-compose exec health-app sh

# View detailed logs
docker-compose logs --tail=100 health-app
docker logs health-management-system
```

### **API Testing**
```bash
# Test health endpoint
curl http://localhost:3001/health
curl http://192.168.50.215:3001/health  # Production

# Test API endpoints
curl http://localhost:3001/api/v1/workers/
curl http://localhost:3001/api/docs  # API documentation

# Test PDF generation
curl -X POST http://localhost:3001/api/v1/documents/fill-pdf/health_consultation_log \\
  -H "Content-Type: application/json" \\
  -d '{"entries": [{"date": "2025-06-19", "worker_name": "테스트"}]}'
```

### **Performance Monitoring**
```bash
# Monitor container resources
docker stats health-management-system

# Check disk usage
docker system df
docker system prune -f

# Monitor log files
tail -f logs/health_system.log
tail -f logs/errors.log
```

## 🔄 Maintenance Commands

### **System Cleanup**
```bash
# Clean Docker system
docker-compose down
docker system prune -f
docker volume prune -f

# Clean node modules and rebuild
rm -rf node_modules package-lock.json
npm install

# Clean Python cache
find . -type d -name __pycache__ -delete
find . -name "*.pyc" -delete
```

### **Backup & Recovery**
```bash
# Database backup
docker exec health-postgres pg_dump -U admin health_management > backup.sql

# Restore database
docker exec -i health-postgres psql -U admin health_management < backup.sql

# Backup uploaded files
tar -czf uploads_backup.tar.gz uploads/

# Backup logs
tar -czf logs_backup.tar.gz logs/
```

## 🚀 Deployment Commands

### **Production Deployment**
```bash
# Full deployment pipeline
./deploy.sh health

# Manual deployment steps
npm run build
docker build --no-cache -t health-app .
docker tag health-app registry/health-app:latest
docker push registry/health-app:latest

# Remote deployment
scp -P 1111 -r dist/* docker@192.168.50.215:~/app/health/dist/
ssh -p 1111 docker@192.168.50.215 "cd ~/app/health && /usr/local/bin/docker-compose restart health-app"
```

### **Environment Management**
```bash
# Switch to development environment
cp .env.development .env

# Switch to production environment  
cp .env.production .env

# View current configuration
docker-compose config
```

## 📊 Monitoring Commands

### **System Health**
```bash
# Check application health
curl -s http://localhost:3001/health | jq .

# Monitor API response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:3001/api/v1/workers/

# Check database connection
docker exec health-postgres pg_isready -U admin -d health_management
```

### **Log Analysis**
```bash
# Search for errors in logs
grep "ERROR" logs/health_system.log
grep "CRITICAL" logs/errors.log

# Monitor real-time logs
tail -f logs/health_system.log | grep "duration"

# Search for specific patterns
grep -r "SQL" logs/ --include="*.log"
```