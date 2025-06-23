# Code Style & Conventions

## 🐍 Python Backend Conventions

### **File Organization**
- **Models**: SQLAlchemy ORM classes in `src/models/`
- **Schemas**: Pydantic request/response models in `src/schemas/`
- **Handlers**: FastAPI route handlers in `src/handlers/`
- **Services**: Business logic in `src/services/`
- **Repositories**: Data access layer in `src/repositories/`

### **Naming Conventions**
```python
# Classes: PascalCase
class WorkerService:
class HealthLogger:

# Functions/Methods: snake_case
async def create_worker():
async def get_worker_list():

# Constants: UPPER_SNAKE_CASE
DATABASE_URL = "postgresql://..."
MAX_RETRY_ATTEMPTS = 30

# Variables: snake_case
worker_data = {...}
async_session = AsyncSession()
```

### **Type Hints & Documentation**
```python
# Required type hints for all function signatures
async def create_worker(
    self, 
    db: AsyncSession, 
    worker_data: WorkerCreate
) -> Worker:
    """근로자 생성 (비즈니스 로직 포함)"""

# Optional parameters with defaults
async def get_multi(
    self,
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[T], int]:
```

### **Error Handling Pattern**
```python
async def service_method(self, db: AsyncSession, data: CreateSchema):
    try:
        # Business logic
        result = await self.repository.create(db, obj_in=data)
        logger.info(f"작업 완료: {result.id}")
        return result
    except Exception as e:
        logger.error(f"서비스 오류: {e}")
        raise
```

### **Korean Comments & Messages**
```python
# Korean comments for business logic
# 1. 사번 중복 검사
# 2. 데이터 번역 (한국어 -> 영어)
# 3. 비즈니스 규칙 적용

# Korean log messages
logger.info("근로자 생성 완료")
logger.error("데이터베이스 연결 실패")

# Korean docstrings
def normalize_phone(self, phone: str) -> str:
    """전화번호 정규화"""
```

## ⚛️ React Frontend Conventions

### **Component Organization**
```typescript
// Component files: PascalCase
Dashboard.tsx
WorkerManagement.tsx
HealthExamForm.tsx

// Hook files: camelCase starting with 'use'
useWorkers.ts
useHealthExams.ts
useApiCall.ts

// Utility files: camelCase
dateUtils.ts
validationUtils.ts
apiClient.ts
```

### **TypeScript Patterns**
```typescript
// Interface definitions
interface Worker {
  id: number;
  name: string;
  employee_id: string;
  health_status: HealthStatus;
}

// Component props with default values
interface WorkerFormProps {
  worker?: Worker;
  onSubmit: (data: WorkerCreate) => void;
  onCancel?: () => void;
}

// Custom hooks with proper return types
function useWorkers(): {
  workers: Worker[];
  loading: boolean;
  error: string | null;
  createWorker: (data: WorkerCreate) => Promise<void>;
} {
  // Implementation
}
```

### **Component Structure**
```typescript
// Consistent component structure
const WorkerManagement: React.FC = () => {
  // 1. State declarations
  const [workers, setWorkers] = useState<Worker[]>([]);
  
  // 2. Custom hooks
  const { data, loading, error } = useWorkers();
  
  // 3. Event handlers
  const handleCreateWorker = useCallback(async (data: WorkerCreate) => {
    // Implementation
  }, []);
  
  // 4. Effects
  useEffect(() => {
    // Side effects
  }, []);
  
  // 5. Render logic
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <div className="worker-management">
      {/* Component JSX */}
    </div>
  );
};
```

### **Styling Conventions**
```typescript
// Tailwind CSS classes with consistent patterns
<div className="bg-white rounded-lg shadow-md p-6 mb-4">
<button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">

// Component-specific CSS modules when needed
import styles from './Worker.module.css';
<div className={styles.workerCard}>
```

## 🗃️ Database Conventions

### **Model Definitions**
```python
class Worker(Base):
    __tablename__ = "workers"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Required fields
    name = Column(String(100), nullable=False, index=True)
    employee_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Optional fields with defaults
    is_active = Column(Boolean, default=True, nullable=False)
    health_status = Column(String(20), default="normal", nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    health_exams = relationship("HealthExam", back_populates="worker", cascade="all, delete-orphan")
```

### **Schema Patterns**
```python
class WorkerBase(BaseModel):
    """공통 필드 정의"""
    name: str = Field(..., min_length=1, max_length=100, description="근로자 이름")
    employee_id: str = Field(..., min_length=1, max_length=50, description="사번")

class WorkerCreate(WorkerBase):
    """생성 시 필요한 필드"""
    department: str = Field(..., description="부서")
    hire_date: date = Field(default_factory=date.today, description="입사일")

class WorkerResponse(WorkerBase):
    """응답 시 포함할 필드"""
    id: int
    is_active: bool
    health_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## 📝 Documentation Standards

### **API Documentation**
```python
@router.post("/", response_model=WorkerResponse)
async def create_worker(
    *,
    db: AsyncSession = Depends(get_db),
    worker_in: WorkerCreate
) -> WorkerResponse:
    """
    근로자 생성
    
    새로운 근로자를 등록합니다.
    - **name**: 근로자 이름 (필수)
    - **employee_id**: 사번 (필수, 중복 불가)
    - **department**: 소속 부서
    - **hire_date**: 입사일 (기본값: 오늘)
    """
```

### **Comment Guidelines**
```python
# Good: Explain business logic in Korean
# 특수건강진단 대상자 자동 판정
if work_type in hazardous_work_types:
    data["is_special_exam_target"] = True

# Good: Technical details in English
# NOTE: Using GIN index for Korean full-text search
CREATE INDEX ix_workers_name_search ON workers USING gin(to_tsvector('korean', name));

# Bad: Obvious comments
worker_id = 1  # Set worker ID to 1
```

## 🔧 Configuration Standards

### **Environment Variables**
```python
# Use Pydantic Settings for type safety
class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL") 
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### **Import Organization**
```python
# 1. Standard library imports
import asyncio
from datetime import datetime
from typing import List, Optional

# 2. Third-party imports
from fastapi import FastAPI, Depends
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel, Field

# 3. Local imports
from .config.database import get_db
from .models.worker import Worker
from .schemas.worker import WorkerCreate, WorkerResponse
```

## ✅ Quality Standards

### **Code Review Checklist**
- [ ] Type hints for all function signatures
- [ ] Korean comments for business logic
- [ ] Error handling with proper logging
- [ ] Input validation with Pydantic
- [ ] Database transactions properly managed
- [ ] Tests written for new functionality
- [ ] Documentation updated

### **Performance Guidelines**
- Use async/await for all I/O operations
- Implement proper database indexing
- Use connection pooling for database access
- Optimize SQL queries (avoid N+1 problems)
- Implement caching for frequently accessed data
- Use pagination for large result sets