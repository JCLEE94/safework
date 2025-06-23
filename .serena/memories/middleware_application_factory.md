# Middleware & Application Factory Patterns

## 🏭 Application Factory Pattern

### **FastAPI Application Factory** (`src/app.py`)

#### **Factory Function Benefits**:
- **Configurable Instances**: Different configs for dev/test/prod
- **Dependency Injection**: Easy testing and mocking
- **Lifecycle Management**: Proper startup/shutdown handling
- **Modular Registration**: Clean separation of concerns

#### **Application Lifecycle** (`lifespan` function):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("건설업 보건관리 시스템 시작")
    
    # Database initialization with retry logic
    await init_db()
    
    # Database optimization (non-critical)
    optimize_database()
    
    yield
    
    # Shutdown
    logger.info("건설업 보건관리 시스템 종료")
```

#### **Component Registration Order**:
1. **Error Handlers**: Global exception handling
2. **Middleware**: Security, logging, performance (order matters)
3. **CORS**: Cross-origin request handling
4. **Static Files**: React build serving
5. **API Routes**: Domain-specific endpoints

## 🛡️ Advanced Middleware System

### **Middleware Stack** (Order is Critical)

#### **1. SecurityLoggingMiddleware**
- **Purpose**: Security event detection and logging
- **Features**: 
  - Suspicious pattern detection (SQL injection, XSS)
  - Rate limiting monitoring
  - Authentication failure tracking
  - IP-based threat detection

#### **2. PerformanceMiddleware**
- **Purpose**: Request performance monitoring
- **Configuration**: `slow_request_threshold: 1000.0ms`
- **Features**:
  - Response time measurement
  - Slow request alerts
  - Performance headers injection
  - Resource usage tracking

#### **3. LoggingMiddleware**
- **Purpose**: Request/response lifecycle tracking
- **Features**:
  - Unique request ID generation
  - Comprehensive request logging
  - Error context capture
  - Response metadata tracking

### **Middleware Implementation Patterns**

#### **Request ID Tracking**:
```python
request_id = str(uuid.uuid4())
request.state.request_id = request_id
response.headers["X-Request-ID"] = request_id
```

#### **Performance Measurement**:
```python
start_time = time.time()
response = await call_next(request)
duration_ms = (time.time() - start_time) * 1000

if duration_ms > self.slow_request_threshold:
    logger.warning("Slow request detected", ...)
```

#### **Error Context Capture**:
```python
try:
    response = await call_next(request)
except Exception as e:
    logger.error("Request failed", 
                error=e, 
                request_id=request_id,
                duration=duration_ms)
    raise
```

## 🔄 Route Organization

### **Domain-Based Route Registration**:
```python
# API versioning and Korean tags
app.include_router(workers_router, 
                   prefix="/api/v1/workers", 
                   tags=["근로자관리"])
app.include_router(health_exams_router, 
                   tags=["건강진단"])
app.include_router(documents_router, 
                   tags=["문서관리"])
```

### **Static File Serving**:
```python
# React build files serving
app.mount("/", StaticFiles(directory="dist", html=True), name="static")
```

## 🏥 Health Check System

### **Comprehensive Health Endpoint**:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "건설업 보건관리 시스템",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "timezone": "Asia/Seoul (KST)",
        "components": {
            "database": "connected",
            "api": "running", 
            "frontend": "active"
        }
    }
```

## 🔧 Configuration Management

### **Environment-Based Configuration**:
- **Development**: Debug logging, CORS wildcards
- **Testing**: In-memory databases, mock services
- **Production**: Optimized logging, strict CORS

### **Settings Management** (`src/config/settings.py`):
- **Pydantic Settings**: Type-safe configuration
- **Environment Variables**: 12-factor app compliance
- **Secret Management**: Secure credential handling
- **Korean Locale**: Asia/Seoul timezone, UTF-8 encoding

## 🚀 Deployment Architecture

### **Container Health Checks**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### **Service Dependencies**:
```yaml
depends_on:
  postgres:
    condition: service_healthy
  redis:
    condition: service_healthy
```

### **Volume Management**:
- **Application Logs**: `./logs:/app/logs`
- **File Uploads**: `./uploads:/app/uploads`
- **React Build**: `./dist:/app/dist` (critical for UI updates)