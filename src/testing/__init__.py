"""
SafeWork Pro Integration Testing Infrastructure
Provides inline testing capabilities similar to Rust's #[cfg(test)]
"""

from .inline_test_runner import run_inline_tests, integration_test
from .fixtures import (
    TestDatabase,
    TestClient,
    TestCache,
    TestAuth,
    create_test_worker,
    create_test_health_exam,
    create_test_environment_data,
    create_test_environment
)
from .utils import (
    assert_response_ok,
    assert_korean_text,
    assert_pdf_valid,
    assert_cache_invalidated,
    assert_error_response,
    measure_performance
)

__all__ = [
    'run_inline_tests',
    'integration_test',
    'TestDatabase',
    'TestClient',
    'TestCache',
    'TestAuth',
    'create_test_worker',
    'create_test_health_exam',
    'create_test_environment_data',
    'create_test_environment',
    'assert_response_ok',
    'assert_korean_text',
    'assert_pdf_valid',
    'assert_cache_invalidated',
    'assert_error_response',
    'measure_performance'
]