"""
API 성능 최적화 미들웨어
API Performance optimization middleware
"""

import time
import asyncio
from typing import Callable, Dict, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

from ..utils.logger import logger
from ..services.cache import cache_service


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    요청 속도 제한 미들웨어
    Rate limiting middleware to prevent API abuse
    """
    
    def __init__(self, app, rate_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque())
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for static files and health checks
        if request.url.path.startswith("/static") or request.url.path == "/health":
            return await call_next(request)
            
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        now = time.time()
        history = self.request_history[client_ip]
        
        # Remove old requests outside the window
        while history and history[0] < now - self.window_seconds:
            history.popleft()
            
        # Check if rate limit exceeded
        if len(history) >= self.rate_limit:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return Response(
                content=json.dumps({
                    "detail": "요청 속도 제한 초과. 잠시 후 다시 시도해주세요.",
                    "retry_after": self.window_seconds
                }),
                status_code=429,
                headers={"Retry-After": str(self.window_seconds)},
                media_type="application/json"
            )
            
        # Add current request to history
        history.append(now)
        
        # Process request
        response = await call_next(request)
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    응답 압축 미들웨어
    Response compression middleware for reducing bandwidth
    """
    
    MIN_SIZE = 1024  # Minimum size to compress (1KB)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if client accepts gzip
        accept_encoding = request.headers.get("accept-encoding", "")
        
        response = await call_next(request)
        
        # Skip compression for small responses or non-text content
        if (
            "gzip" not in accept_encoding or
            response.status_code != 200 or
            "content-length" in response.headers and 
            int(response.headers["content-length"]) < self.MIN_SIZE
        ):
            return response
            
        # For streaming responses, we can't compress
        if response.headers.get("transfer-encoding") == "chunked":
            return response
            
        # Compress response body
        try:
            import gzip
            
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
                
            # Compress
            compressed = gzip.compress(body)
            
            # Only use compressed if it's smaller
            if len(compressed) < len(body):
                return Response(
                    content=compressed,
                    status_code=response.status_code,
                    headers={
                        **dict(response.headers),
                        "content-encoding": "gzip",
                        "content-length": str(len(compressed))
                    },
                    media_type=response.media_type
                )
        except Exception as e:
            logger.error(f"Compression error: {e}")
            
        return response


class ConnectionPoolMiddleware(BaseHTTPMiddleware):
    """
    데이터베이스 연결 풀 최적화 미들웨어
    Database connection pool optimization middleware
    """
    
    def __init__(self, app, pool_size: int = 20, max_overflow: int = 10):
        super().__init__(app)
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.active_connections = 0
        self.connection_wait_times: deque = deque(maxlen=100)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Track active connections
        self.active_connections += 1
        
        try:
            # Set connection pool info in request state
            request.state.pool_info = {
                "active": self.active_connections,
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow
            }
            
            response = await call_next(request)
            
            # Record connection time
            connection_time = time.time() - start_time
            self.connection_wait_times.append(connection_time)
            
            # Add pool metrics to response headers
            response.headers["X-Pool-Active"] = str(self.active_connections)
            response.headers["X-Pool-Wait-Avg"] = f"{sum(self.connection_wait_times) / len(self.connection_wait_times):.3f}"
            
            return response
            
        finally:
            self.active_connections -= 1


class QueryOptimizationMiddleware(BaseHTTPMiddleware):
    """
    쿼리 최적화 미들웨어
    Query optimization middleware for monitoring slow queries
    """
    
    def __init__(self, app, slow_query_threshold: float = 1.0):
        super().__init__(app)
        self.slow_query_threshold = slow_query_threshold
        self.slow_queries: List[Dict] = []
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Inject query tracking into request
        request.state.queries = []
        request.state.query_start_time = time.time()
        
        response = await call_next(request)
        
        # Analyze queries
        if hasattr(request.state, "queries"):
            total_query_time = sum(q["duration"] for q in request.state.queries)
            slow_queries = [q for q in request.state.queries if q["duration"] > self.slow_query_threshold]
            
            if slow_queries:
                logger.warning(
                    f"Slow queries detected on {request.url.path}: "
                    f"{len(slow_queries)} queries took > {self.slow_query_threshold}s"
                )
                
                # Store for analysis
                self.slow_queries.extend([
                    {
                        **q,
                        "path": request.url.path,
                        "timestamp": datetime.now().isoformat()
                    }
                    for q in slow_queries
                ])
                
                # Keep only recent slow queries
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]
                    
            # Add query metrics to response
            response.headers["X-Query-Count"] = str(len(request.state.queries))
            response.headers["X-Query-Time"] = f"{total_query_time:.3f}"
            
        return response


class BatchingMiddleware(BaseHTTPMiddleware):
    """
    요청 배치 처리 미들웨어
    Request batching middleware for bulk operations
    """
    
    def __init__(self, app, batch_window_ms: int = 50, max_batch_size: int = 100):
        super().__init__(app)
        self.batch_window_ms = batch_window_ms
        self.max_batch_size = max_batch_size
        self.batches: Dict[str, List] = defaultdict(list)
        self.batch_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this is a batchable endpoint
        if request.url.path.endswith("/batch") and request.method == "POST":
            try:
                # Parse request body
                body = await request.body()
                data = json.loads(body)
                
                # Get batch key (endpoint + method)
                batch_key = f"{data.get('endpoint')}:{data.get('method', 'GET')}"
                
                async with self.batch_locks[batch_key]:
                    # Add to batch
                    self.batches[batch_key].append({
                        "request": data,
                        "timestamp": time.time()
                    })
                    
                    # Check if batch should be processed
                    if len(self.batches[batch_key]) >= self.max_batch_size:
                        return await self._process_batch(batch_key, call_next)
                        
                    # Wait for batch window
                    await asyncio.sleep(self.batch_window_ms / 1000)
                    
                    # Process batch
                    return await self._process_batch(batch_key, call_next)
                    
            except Exception as e:
                logger.error(f"Batching error: {e}")
                
        return await call_next(request)
        
    async def _process_batch(self, batch_key: str, call_next: Callable) -> Response:
        """Process a batch of requests"""
        batch = self.batches.pop(batch_key, [])
        
        if not batch:
            return Response(
                content=json.dumps({"results": []}),
                media_type="application/json"
            )
            
        # Process batch (implementation depends on specific endpoints)
        results = []
        for item in batch:
            # Process each item
            results.append({
                "status": "processed",
                "data": item["request"]
            })
            
        return Response(
            content=json.dumps({
                "results": results,
                "batch_size": len(batch),
                "batch_key": batch_key
            }),
            media_type="application/json"
        )


class PaginationOptimizationMiddleware(BaseHTTPMiddleware):
    """
    페이지네이션 최적화 미들웨어
    Pagination optimization middleware with cursor-based pagination support
    """
    
    def __init__(self, app, default_page_size: int = 50, max_page_size: int = 200):
        super().__init__(app)
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract pagination parameters
        if request.method == "GET":
            params = dict(request.query_params)
            
            # Validate and set page size
            page_size = int(params.get("page_size", self.default_page_size))
            page_size = min(page_size, self.max_page_size)
            
            # Store in request state for handlers to use
            request.state.pagination = {
                "page_size": page_size,
                "page": int(params.get("page", 1)),
                "cursor": params.get("cursor"),
                "use_cursor": params.get("cursor") is not None
            }
            
        response = await call_next(request)
        
        # Add pagination headers
        if hasattr(request.state, "pagination_info"):
            info = request.state.pagination_info
            response.headers["X-Total-Count"] = str(info.get("total", 0))
            response.headers["X-Page-Count"] = str(info.get("pages", 0))
            response.headers["X-Current-Page"] = str(info.get("current", 1))
            response.headers["X-Page-Size"] = str(info.get("size", self.default_page_size))
            
            # Add Link header for navigation
            links = []
            if info.get("next"):
                links.append(f'<{info["next"]}>; rel="next"')
            if info.get("prev"):
                links.append(f'<{info["prev"]}>; rel="prev"')
            if info.get("first"):
                links.append(f'<{info["first"]}>; rel="first"')
            if info.get("last"):
                links.append(f'<{info["last"]}>; rel="last"')
                
            if links:
                response.headers["Link"] = ", ".join(links)
                
        return response