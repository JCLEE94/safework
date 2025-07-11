"""
Run All Integration Tests
Comprehensive test runner for all inline integration tests
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.testing import run_inline_tests


async def run_all_tests():
    """Run all integration tests across the codebase"""
    print("\n" + "=" * 80)
    print("🧪 SafeWork Pro - Comprehensive Integration Test Suite")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    # Test modules to run
    test_modules = [
        # API Handlers
        ("API - Workers", "src.handlers.workers"),
        ("API - Health Exams", "src.handlers.health_exams"),
        ("API - Work Environments", "src.handlers.work_environments"),
        ("API - Chemical Substances", "src.handlers.chemical_substances"),
        ("API - Accident Reports", "src.handlers.accident_reports"),
        ("API - PDF Generation", "src.handlers.pdf_integration"),
        ("API - WebSocket", "src.handlers.websocket_integration"),
        
        # Services
        ("Service - Authentication", "src.services.auth_integration"),
        ("Service - Redis Cache", "src.services.cache_integration"),
        
        # Database
        ("Database - Operations", "src.repositories.base_integration"),
    ]
    
    # Overall results tracking
    all_results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "modules": []
    }
    
    # Run tests for each module
    for module_name, module_path in test_modules:
        print(f"\n📦 Testing: {module_name}")
        print("-" * 60)
        
        try:
            # Import the module to register tests
            __import__(module_path)
            
            # Run tests
            results = await run_inline_tests(module_path, verbose=True)
            
            # Track results
            module_passed = sum(1 for r in results if r.passed)
            module_failed = len(results) - module_passed
            
            all_results["total_tests"] += len(results)
            all_results["passed"] += module_passed
            all_results["failed"] += module_failed
            all_results["modules"].append({
                "name": module_name,
                "total": len(results),
                "passed": module_passed,
                "failed": module_failed,
                "results": results
            })
            
        except ImportError as e:
            print(f"❌ Failed to import {module_path}: {e}")
            all_results["modules"].append({
                "name": module_name,
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 80)
    
    print(f"\nTotal Tests: {all_results['total_tests']}")
    print(f"✅ Passed: {all_results['passed']}")
    print(f"❌ Failed: {all_results['failed']}")
    
    if all_results['total_tests'] > 0:
        success_rate = (all_results['passed'] / all_results['total_tests']) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    # Module breakdown
    print("\nModule Results:")
    print("-" * 60)
    for module in all_results["modules"]:
        if "error" in module:
            print(f"  {module['name']}: ❌ Import Error")
        else:
            status = "✅" if module["failed"] == 0 else "❌"
            print(f"  {status} {module['name']}: {module['passed']}/{module['total']} passed")
    
    # Failed tests detail
    if all_results["failed"] > 0:
        print("\n❌ Failed Tests Detail:")
        print("-" * 60)
        for module in all_results["modules"]:
            if "results" in module:
                failed_tests = [r for r in module["results"] if not r.passed]
                if failed_tests:
                    print(f"\n{module['name']}:")
                    for test in failed_tests:
                        print(f"  - {test.name}: {test.error}")
    
    print("\n" + "=" * 80)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")
    
    # Exit code
    return 0 if all_results["failed"] == 0 else 1


def main():
    """Main entry point"""
    # Set environment variable to enable inline tests
    os.environ["RUN_INTEGRATION_TESTS"] = "1"
    
    # Run all tests
    exit_code = asyncio.run(run_all_tests())
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()