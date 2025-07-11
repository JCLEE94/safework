# Refactoring Recommendations for Better Testability

## Overview

Based on the comprehensive integration testing implementation, here are key refactoring recommendations to improve the testability of the SafeWork Pro codebase.

## 1. Dependency Injection Issues

### Current Problems

```python
# ❌ Current: Hard-coded dependencies
class WorkerService:
    def __init__(self):
        self.db = get_db()  # Direct database dependency
        self.cache = Redis()  # Hard-coded Redis client
        self.logger = logging.getLogger()  # Global logger
```

### Recommended Refactoring

```python
# ✅ Refactored: Dependency injection
from typing import Protocol

class DatabaseProtocol(Protocol):
    async def execute(self, query): ...
    async def commit(self): ...

class CacheProtocol(Protocol):
    async def get(self, key: str): ...
    async def set(self, key: str, value: Any, ttl: int): ...

class WorkerService:
    def __init__(
        self,
        db: DatabaseProtocol,
        cache: CacheProtocol,
        logger: logging.Logger
    ):
        self.db = db
        self.cache = cache
        self.logger = logger
```

### Benefits
- Easy to mock/stub in tests
- Better separation of concerns
- Supports multiple implementations

## 2. Middleware Testing Challenges

### Current Problems

```python
# ❌ Current: Middleware directly modifies request
async def auth_middleware(request: Request, call_next):
    token = request.headers.get("Authorization")
    # Complex logic mixed with request handling
    if not token:
        return JSONResponse(status_code=401)
    # ...
```

### Recommended Refactoring

```python
# ✅ Refactored: Extractable auth logic
class AuthService:
    async def validate_token(self, token: str) -> Optional[User]:
        """Pure business logic, easily testable"""
        # Token validation logic
        pass
    
    async def check_permissions(self, user: User, resource: str) -> bool:
        """Pure permission check"""
        # Permission logic
        pass

class AuthMiddleware:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
    
    async def __call__(self, request: Request, call_next):
        token = request.headers.get("Authorization")
        user = await self.auth_service.validate_token(token)
        if not user:
            return JSONResponse(status_code=401)
        request.state.user = user
        return await call_next(request)
```

### Benefits
- Business logic separated from HTTP handling
- Easy to unit test auth logic
- Middleware becomes thin wrapper

## 3. Database Repository Pattern

### Current Problems

```python
# ❌ Current: Direct SQLAlchemy queries in handlers
@router.get("/workers/{worker_id}")
async def get_worker(worker_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    worker = result.scalar_one_or_none()
    # Direct database access in handler
```

### Recommended Refactoring

```python
# ✅ Refactored: Repository pattern
class WorkerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, worker_id: int) -> Optional[Worker]:
        """Encapsulated database logic"""
        result = await self.session.execute(
            select(Worker).where(Worker.id == worker_id)
        )
        return result.scalar_one_or_none()
    
    async def search(
        self,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Worker], int]:
        """Complex query logic encapsulated"""
        query = select(Worker)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(Worker, field):
                query = query.where(getattr(Worker, field) == value)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        
        return result.scalars().all(), total

# Handler becomes thin
@router.get("/workers/{worker_id}")
async def get_worker(
    worker_id: int,
    repo: WorkerRepository = Depends(get_worker_repository)
):
    worker = await repo.get_by_id(worker_id)
    if not worker:
        raise HTTPException(status_code=404)
    return worker
```

### Benefits
- Database logic centralized
- Easy to mock repository in tests
- Supports different database backends

## 4. Cache Service Abstraction

### Current Problems

```python
# ❌ Current: Direct Redis calls scattered
@cache_result(key="worker:{worker_id}", ttl=300)
async def get_worker(worker_id: int):
    # Magic decorator handling
```

### Recommended Refactoring

```python
# ✅ Refactored: Explicit cache service
class CacheService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: int = 300
    ) -> Any:
        """Cache-aside pattern"""
        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Compute value
        value = await factory()
        
        # Cache it
        await self.redis.set(key, json.dumps(value), ex=ttl)
        
        return value
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate by pattern"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

# Usage in handler
async def get_worker(
    worker_id: int,
    repo: WorkerRepository = Depends(get_worker_repository),
    cache: CacheService = Depends(get_cache_service)
):
    return await cache.get_or_set(
        key=f"worker:{worker_id}",
        factory=lambda: repo.get_by_id(worker_id),
        ttl=300
    )
```

### Benefits
- Explicit cache operations
- Easy to test with mock cache
- Clear cache invalidation

## 5. WebSocket Handler Separation

### Current Problems

```python
# ❌ Current: WebSocket logic mixed with handler
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Complex business logic here
```

### Recommended Refactoring

```python
# ✅ Refactored: Separated message handling
class MessageBroker:
    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
    
    async def subscribe(self, ws: WebSocket, topics: List[str]):
        """Manage subscriptions"""
        for topic in topics:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(ws)
    
    async def publish(self, topic: str, message: Dict):
        """Publish to subscribers"""
        if topic in self.subscriptions:
            tasks = []
            for ws in self.subscriptions[topic]:
                tasks.append(ws.send_json(message))
            await asyncio.gather(*tasks, return_exceptions=True)

class MessageHandler:
    def __init__(self, broker: MessageBroker):
        self.broker = broker
    
    async def handle_message(self, ws: WebSocket, message: Dict):
        """Pure message handling logic"""
        msg_type = message.get("type")
        
        if msg_type == "subscribe":
            await self.broker.subscribe(ws, message["topics"])
        elif msg_type == "worker_update":
            await self.broker.publish("worker_updates", message)

# Thin WebSocket handler
@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    handler: MessageHandler = Depends(get_message_handler)
):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            await handler.handle_message(websocket, message)
    except WebSocketDisconnect:
        await handler.broker.unsubscribe(websocket)
```

### Benefits
- Message handling logic testable separately
- WebSocket transport separated from business logic
- Easy to add different transports (SSE, polling)

## 6. PDF Generation Service

### Current Problems

```python
# ❌ Current: PDF logic in handler
@router.post("/fill-pdf/{form_name}")
async def fill_pdf(form_name: str, data: dict):
    # Complex PDF manipulation here
    template_path = f"templates/{form_name}.pdf"
    # ...
```

### Recommended Refactoring

```python
# ✅ Refactored: PDF service
class PDFService:
    def __init__(self, template_loader: TemplateLoader):
        self.template_loader = template_loader
    
    async def generate_from_template(
        self,
        template_name: str,
        data: Dict[str, Any]
    ) -> bytes:
        """Generate PDF from template and data"""
        template = await self.template_loader.get_template(template_name)
        return await self._fill_template(template, data)
    
    async def _fill_template(self, template: PDFTemplate, data: Dict) -> bytes:
        """Pure PDF generation logic"""
        # PDF manipulation logic
        pass

class TemplateLoader:
    """Abstract template loading"""
    async def get_template(self, name: str) -> PDFTemplate:
        pass

class FileSystemTemplateLoader(TemplateLoader):
    """Concrete implementation"""
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
    
    async def get_template(self, name: str) -> PDFTemplate:
        path = self.template_dir / f"{name}.pdf"
        # Load template
```

### Benefits
- PDF logic separated from HTTP handling
- Template loading abstracted
- Easy to test with mock templates

## 7. Configuration Management

### Current Problems

```python
# ❌ Current: Direct settings access
from src.config.settings import settings

if settings.environment == "production":
    # Production logic
```

### Recommended Refactoring

```python
# ✅ Refactored: Configuration injection
from typing import Protocol

class ConfigProtocol(Protocol):
    @property
    def database_url(self) -> str: ...
    @property
    def redis_url(self) -> str: ...
    @property
    def is_production(self) -> bool: ...

class Settings(ConfigProtocol):
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

# Inject configuration
class Service:
    def __init__(self, config: ConfigProtocol):
        self.config = config
    
    async def process(self):
        if self.config.is_production:
            # Production logic
            pass
```

### Benefits
- Easy to provide test configuration
- No global state
- Type-safe configuration

## 8. Error Handling Standardization

### Current Problems

```python
# ❌ Current: Inconsistent error handling
try:
    # Some operation
except Exception as e:
    logger.error(f"Error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Recommended Refactoring

```python
# ✅ Refactored: Centralized error handling
class DomainError(Exception):
    """Base domain error"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)

class WorkerNotFoundError(DomainError):
    def __init__(self, worker_id: int):
        super().__init__(
            message=f"Worker {worker_id} not found",
            code="WORKER_NOT_FOUND"
        )

class ErrorHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def handle_domain_error(self, error: DomainError) -> JSONResponse:
        self.logger.warning(f"Domain error: {error.code} - {error.message}")
        return JSONResponse(
            status_code=self._get_status_code(error),
            content={"error": error.code, "message": error.message}
        )
    
    def _get_status_code(self, error: DomainError) -> int:
        error_mapping = {
            "WORKER_NOT_FOUND": 404,
            "UNAUTHORIZED": 401,
            "VALIDATION_ERROR": 422,
        }
        return error_mapping.get(error.code, 500)
```

### Benefits
- Consistent error responses
- Easy to test error scenarios
- Clear error semantics

## Implementation Priority

1. **High Priority** (Immediate benefits)
   - Dependency injection for services
   - Repository pattern for database access
   - Configuration injection

2. **Medium Priority** (Significant improvements)
   - Cache service abstraction
   - Error handling standardization
   - Middleware refactoring

3. **Low Priority** (Nice to have)
   - WebSocket handler separation
   - PDF service extraction
   - Complete protocol-based interfaces

## Migration Strategy

1. **Start with new features** - Implement patterns in new code
2. **Refactor during bug fixes** - Update code when touching it
3. **Dedicated refactoring sprints** - For critical components
4. **Maintain backwards compatibility** - Use adapters/facades

## Testing Benefits After Refactoring

- **Unit tests** become possible for business logic
- **Integration tests** can use test doubles
- **Performance tests** can isolate components
- **Debugging** becomes easier with clear boundaries

## Conclusion

These refactoring recommendations will significantly improve the testability of the SafeWork Pro codebase. The key principle is **separation of concerns** - keeping business logic separate from infrastructure concerns, making each component independently testable.