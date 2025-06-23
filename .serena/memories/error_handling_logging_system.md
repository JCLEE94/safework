# Advanced Error Handling & Logging System

## 🚨 Comprehensive Error Handling

### **Global Error Handler Registration**
**Location**: `src/utils/error_handlers.py`

#### **Error Handler Types**:
1. **Database Error Handler** - SQLAlchemyError
2. **Validation Error Handler** - Pydantic validation errors  
3. **HTTP Exception Handler** - FastAPI HTTP exceptions
4. **Integrity Error Handler** - Database constraint violations
5. **General Exception Handler** - Catch-all for unexpected errors

### **Error Handler Features**:
- **Structured Responses**: Consistent JSON error format
- **Korean/English Messages**: Bilingual error messages
- **Request Context**: Include request ID, endpoint, method
- **Timestamp**: KST timezone for all errors
- **Error Classification**: Categorize errors for monitoring

### **Middleware Integration**
**Location**: `src/middleware/logging.py`

#### **LoggingMiddleware**:
- Request/response lifecycle tracking
- Unique request ID generation
- Duration measurement
- Error context capture

#### **PerformanceMiddleware**:
- Slow request detection (>1000ms threshold)
- Response time headers
- Performance alerts

#### **SecurityLoggingMiddleware**:
- Security event detection
- Suspicious pattern monitoring
- Access control logging

## 📊 Advanced Logging System

### **HealthLogger Class** (`src/utils/logger.py`)

#### **Multi-Handler Setup**:
1. **Console Handler**: Development environment, colored output
2. **File Handler**: Production logs with rotation (30 days)
3. **Error Handler**: Dedicated error logs (90 day retention)

#### **JSON Structured Logging**:
```json
{
  "timestamp": "2025-06-23T10:30:45+09:00",
  "level": "INFO",
  "request_id": "uuid4-string",
  "endpoint": "/api/v1/workers",
  "method": "GET",
  "duration": 45.67,
  "status_code": 200,
  "user_agent": "browser-info",
  "client_ip": "192.168.1.100"
}
```

#### **Specialized Log Methods**:
- `api_request()`: API call tracking
- `security_event()`: Security incidents
- `database_operation()`: DB performance monitoring
- `pdf_generation()`: Document creation tracking
- `performance_log()`: Context manager for operation timing

### **Error Context Management**
- **Request ID Tracking**: Trace requests across services
- **Stack Trace Capture**: Full error context for debugging
- **Performance Correlation**: Link errors to slow requests
- **Business Context**: Include domain-specific information

## 🔍 Monitoring & Alerting

### **Performance Metrics**:
- Request duration tracking
- Slow query detection  
- Memory usage monitoring
- PDF generation performance

### **Error Classification**:
- **Critical**: Database failures, security breaches
- **Warning**: Slow requests, validation failures
- **Info**: Normal operations, user actions

### **Log Rotation & Retention**:
- **Application Logs**: 30 day rotation
- **Error Logs**: 90 day retention
- **Performance Logs**: Daily rotation
- **Security Logs**: Permanent retention