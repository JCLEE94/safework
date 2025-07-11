"""
Inline Test Runner - Enables Rust-style inline testing in Python
"""

import asyncio
import inspect
import os
import sys
import time
import traceback
from typing import Callable, List, Dict, Any, Optional
from functools import wraps
from dataclasses import dataclass
import logging
logger = logging.getLogger(__name__)

# Test result tracking
@dataclass
class TestResult:
    name: str
    module: str
    passed: bool
    duration: float
    error: Optional[str] = None
    traceback: Optional[str] = None

# Global test registry
_integration_tests: Dict[str, List[Callable]] = {}

def integration_test(func: Callable) -> Callable:
    """
    Decorator to mark a method as an integration test.
    Similar to Rust's #[test] attribute.
    
    Usage:
        @integration_test
        async def test_worker_creation(self):
            # test implementation
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    # Register the test
    module = func.__module__
    if module not in _integration_tests:
        _integration_tests[module] = []
    _integration_tests[module].append(func)
    
    # Mark as integration test
    wrapper._is_integration_test = True
    return wrapper

async def run_inline_tests(module_name: Optional[str] = None, verbose: bool = True) -> List[TestResult]:
    """
    Run all inline integration tests.
    
    Args:
        module_name: Specific module to test (None for all)
        verbose: Print detailed output
        
    Returns:
        List of test results
    """
    results = []
    
    # Determine which modules to test
    if module_name:
        modules_to_test = [module_name] if module_name in _integration_tests else []
    else:
        modules_to_test = list(_integration_tests.keys())
    
    if not modules_to_test:
        logger.warning("No integration tests found")
        return results
    
    # Print header
    if verbose:
        print("\n" + "=" * 70)
        print("🧪 Running SafeWork Pro Integration Tests")
        print("=" * 70)
    
    total_start = time.time()
    
    for module in modules_to_test:
        if verbose:
            print(f"\n📦 Module: {module}")
            print("-" * 50)
        
        tests = _integration_tests[module]
        
        for test_func in tests:
            test_name = test_func.__name__
            if verbose:
                print(f"  ▶ {test_name}...", end=" ", flush=True)
            
            start_time = time.time()
            result = TestResult(
                name=test_name,
                module=module,
                passed=False,
                duration=0.0
            )
            
            try:
                # Create test instance if needed
                if inspect.ismethod(test_func) or 'self' in inspect.signature(test_func).parameters:
                    # Get the class
                    test_class = None
                    for name, obj in sys.modules[module].__dict__.items():
                        if inspect.isclass(obj) and hasattr(obj, test_func.__name__):
                            test_class = obj
                            break
                    
                    if test_class:
                        instance = test_class()
                        if asyncio.iscoroutinefunction(test_func):
                            await test_func(instance)
                        else:
                            test_func(instance)
                else:
                    # Function test
                    if asyncio.iscoroutinefunction(test_func):
                        await test_func()
                    else:
                        test_func()
                
                result.passed = True
                result.duration = time.time() - start_time
                
                if verbose:
                    print(f"✅ PASSED ({result.duration:.2f}s)")
                    
            except Exception as e:
                result.passed = False
                result.duration = time.time() - start_time
                result.error = str(e)
                result.traceback = traceback.format_exc()
                
                if verbose:
                    print(f"❌ FAILED ({result.duration:.2f}s)")
                    print(f"     Error: {result.error}")
                    if os.environ.get("SHOW_TRACEBACK"):
                        print(f"     Traceback:\n{result.traceback}")
            
            results.append(result)
    
    # Summary
    total_duration = time.time() - total_start
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    
    if verbose:
        print("\n" + "=" * 70)
        print("📊 Test Summary")
        print("=" * 70)
        print(f"Total: {len(results)} | ✅ Passed: {passed} | ❌ Failed: {failed}")
        print(f"Duration: {total_duration:.2f}s")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in results:
                if not r.passed:
                    print(f"  - {r.module}.{r.name}: {r.error}")
        
        print("=" * 70 + "\n")
    
    return results

def run_module_tests(module_path: str):
    """
    Run tests for a specific module file.
    
    Usage:
        python -m src.handlers.workers  # Runs inline tests in workers.py
    """
    # Import the module
    module_name = module_path.replace('/', '.').replace('.py', '')
    
    try:
        __import__(module_name)
    except ImportError as e:
        logger.error(f"Failed to import module {module_name}: {e}")
        return
    
    # Run tests
    asyncio.run(run_inline_tests(module_name))

# Enable running module directly
if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_module_tests(sys.argv[1])
    else:
        # Run all tests
        asyncio.run(run_inline_tests())