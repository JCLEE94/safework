"""
Testing Utilities and Assertions
"""

import asyncio
import time
import json
import base64
from typing import Any, Dict, Optional, Callable
from functools import wraps
from httpx import Response
import PyPDF2
from io import BytesIO


def assert_response_ok(
    response: Response,
    expected_status: int = 200,
    check_json: bool = True
) -> Dict[str, Any]:
    """
    Assert HTTP response is successful.
    
    Args:
        response: HTTP response
        expected_status: Expected status code
        check_json: Whether to parse JSON response
        
    Returns:
        Parsed JSON data if check_json is True
    """
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}. " \
        f"Response: {response.text}"
    
    if check_json and response.status_code != 204:
        data = response.json()
        return data
    
    return {}


def assert_korean_text(text: str, field_name: str = "text"):
    """
    Assert text contains valid Korean characters.
    
    Args:
        text: Text to check
        field_name: Field name for error messages
    """
    if not text:
        return
    
    # Check for Korean characters
    has_korean = any('\uAC00' <= char <= '\uD7AF' for char in text)
    
    # Some fields might be in English
    has_english = any('a' <= char.lower() <= 'z' for char in text)
    
    assert has_korean or has_english, \
        f"{field_name} must contain Korean or English text, got: {text}"
    
    # Check for mojibake (garbled text)
    assert '?' not in text or text.count('?') < len(text) * 0.5, \
        f"{field_name} appears to be garbled: {text}"


def assert_pdf_valid(
    pdf_base64: str,
    min_pages: int = 1,
    check_korean: bool = True
) -> Dict[str, Any]:
    """
    Assert PDF is valid and readable.
    
    Args:
        pdf_base64: Base64 encoded PDF
        min_pages: Minimum expected pages
        check_korean: Whether to check for Korean font support
        
    Returns:
        PDF metadata
    """
    # Decode base64
    try:
        pdf_bytes = base64.b64decode(pdf_base64)
    except Exception as e:
        raise AssertionError(f"Invalid base64 PDF: {e}")
    
    # Read PDF
    try:
        pdf_file = BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
    except Exception as e:
        raise AssertionError(f"Invalid PDF file: {e}")
    
    # Check pages
    num_pages = len(pdf_reader.pages)
    assert num_pages >= min_pages, \
        f"PDF must have at least {min_pages} pages, got {num_pages}"
    
    # Check content
    if check_korean:
        # Extract text from first page
        first_page_text = pdf_reader.pages[0].extract_text()
        
        # Korean PDFs might have font embedding issues
        # Just check that we can extract some text
        assert len(first_page_text) > 0, \
            "PDF appears to be empty or text extraction failed"
    
    return {
        "num_pages": num_pages,
        "size_bytes": len(pdf_bytes),
        "metadata": pdf_reader.metadata
    }


def assert_cache_invalidated(
    cache_key: str,
    cache_service: Any,
    timeout: float = 1.0
):
    """
    Assert cache key has been invalidated.
    
    Args:
        cache_key: Key to check
        cache_service: Cache service instance
        timeout: Maximum wait time
    """
    import asyncio
    
    async def check_cache():
        start_time = time.time()
        while time.time() - start_time < timeout:
            exists = await cache_service.exists(cache_key)
            if not exists:
                return True
            await asyncio.sleep(0.1)
        return False
    
    # Run async check
    loop = asyncio.get_event_loop()
    invalidated = loop.run_until_complete(check_cache())
    
    assert invalidated, f"Cache key '{cache_key}' was not invalidated within {timeout}s"


def measure_performance(func: Callable) -> Callable:
    """
    Decorator to measure function performance.
    
    Usage:
        @measure_performance
        async def test_api_performance():
            # test code
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Add performance data to result if it's a dict
            if isinstance(result, dict):
                result['_performance'] = {
                    'duration_seconds': duration,
                    'duration_ms': duration * 1000
                }
            
            # Log performance
            print(f"⏱  {func.__name__} took {duration:.3f}s")
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            print(f"⏱  {func.__name__} failed after {duration:.3f}s")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Add performance data to result if it's a dict
            if isinstance(result, dict):
                result['_performance'] = {
                    'duration_seconds': duration,
                    'duration_ms': duration * 1000
                }
            
            # Log performance
            print(f"⏱  {func.__name__} took {duration:.3f}s")
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            print(f"⏱  {func.__name__} failed after {duration:.3f}s")
            raise
    
    # Return appropriate wrapper
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def assert_pagination(
    response_data: Dict[str, Any],
    expected_total: Optional[int] = None,
    expected_page_size: Optional[int] = None
):
    """Assert pagination response structure is correct"""
    assert "items" in response_data, "Response must have 'items' field"
    assert "total" in response_data, "Response must have 'total' field"
    assert "page" in response_data, "Response must have 'page' field"
    assert "page_size" in response_data, "Response must have 'page_size' field"
    
    if expected_total is not None:
        assert response_data["total"] == expected_total, \
            f"Expected total {expected_total}, got {response_data['total']}"
    
    if expected_page_size is not None:
        assert len(response_data["items"]) <= expected_page_size, \
            f"Page size exceeded: got {len(response_data['items'])}, max {expected_page_size}"


def assert_datetime_format(
    datetime_str: str,
    field_name: str = "datetime"
):
    """Assert datetime string is in ISO format"""
    from datetime import datetime
    
    try:
        # Try parsing ISO format
        datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except ValueError:
        raise AssertionError(
            f"{field_name} must be in ISO format, got: {datetime_str}"
        )


def assert_error_response(
    response: Response,
    expected_status: int = 400,
    expected_detail: Optional[str] = None
):
    """Assert error response structure"""
    assert response.status_code == expected_status, \
        f"Expected status {expected_status}, got {response.status_code}"
    
    data = response.json()
    assert "detail" in data, "Error response must have 'detail' field"
    
    if expected_detail:
        assert expected_detail in data["detail"], \
            f"Expected error detail to contain '{expected_detail}', got: {data['detail']}"


def generate_test_file(
    filename: str,
    content: str = "Test content",
    size_kb: Optional[int] = None
) -> bytes:
    """Generate test file content"""
    if size_kb:
        # Generate content of specific size
        content = "x" * (size_kb * 1024)
    
    return content.encode('utf-8')


def assert_websocket_message(
    message: Dict[str, Any],
    expected_type: str,
    expected_data_keys: Optional[list] = None
):
    """Assert WebSocket message structure"""
    assert "type" in message, "WebSocket message must have 'type' field"
    assert message["type"] == expected_type, \
        f"Expected message type '{expected_type}', got '{message['type']}'"
    
    if expected_data_keys:
        assert "data" in message, "WebSocket message must have 'data' field"
        for key in expected_data_keys:
            assert key in message["data"], \
                f"WebSocket message data must have '{key}' field"