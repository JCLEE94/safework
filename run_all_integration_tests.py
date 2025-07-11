#!/usr/bin/env python3
"""
Comprehensive integration test runner for all modules
"""
import os
import sys
import asyncio
import importlib
from datetime import datetime

# Set up environment
os.environ["RUN_INTEGRATION_TESTS"] = "1" 
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"

# Add path
sys.path.insert(0, "/app")

async def run_module_tests(module_name, test_class_name):
    """Run all tests in a specific module"""
    print(f"\n📦 Testing Module: {module_name}")
    print("=" * 60)
    
    try:
        module = importlib.import_module(module_name)
        test_class = getattr(module, test_class_name)
        test_instance = test_class()
        
        # Get all test methods
        test_methods = [
            method for method in dir(test_instance) 
            if method.startswith('test_') and callable(getattr(test_instance, method))
        ]
        
        passed = 0
        failed = 0
        
        for method_name in test_methods:
            print(f"  ▶ {method_name}...", end=" ", flush=True)
            try:
                method = getattr(test_instance, method_name)
                start_time = datetime.now()
                await method()
                duration = (datetime.now() - start_time).total_seconds()
                print(f"✅ PASSED ({duration:.2f}s)")
                passed += 1
            except Exception as e:
                print(f"❌ FAILED: {str(e)[:100]}...")
                failed += 1
        
        print(f"\n📊 Module Results: {passed} passed, {failed} failed")
        return passed, failed
        
    except Exception as e:
        print(f"❌ Module failed to load: {e}")
        return 0, 1

async def main():
    print("🧪 SafeWork Pro - Comprehensive Integration Test Suite")
    print("=" * 70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test modules to run
    test_modules = [
        ("src.handlers.test_workers", "IntegrationTestWorkers"),
        ("src.handlers.pdf_integration", "IntegrationTestPDFGeneration"),
        ("src.handlers.websocket_integration", "IntegrationTestWebSocket"),
        ("src.services.auth_integration", "IntegrationTestAuthentication"),
        ("src.services.cache_integration", "IntegrationTestCache"),
        ("src.repositories.base_integration", "IntegrationTestDatabase")
    ]
    
    total_passed = 0
    total_failed = 0
    
    for module_name, class_name in test_modules:
        passed, failed = await run_module_tests(module_name, class_name)
        total_passed += passed
        total_failed += failed
    
    print("\n" + "=" * 70)
    print("🏁 FINAL RESULTS")
    print("=" * 70)
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        success_rate = (total_passed / (total_passed + total_failed)) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
    
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main())