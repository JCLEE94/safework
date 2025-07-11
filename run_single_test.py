#!/usr/bin/env python3
"""
Simple single test runner to isolate issues
"""
import os
import sys
import asyncio

# Set up environment
os.environ["RUN_INTEGRATION_TESTS"] = "1"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"

# Add path
sys.path.insert(0, "/app")

async def main():
    print("🧪 Running Single Integration Test\n")
    
    try:
        from src.handlers.test_workers import IntegrationTestWorkers
        
        test_instance = IntegrationTestWorkers()
        
        # Run just the error handling test first
        print("▶ Running test_worker_error_handling...")
        try:
            await test_instance.test_worker_error_handling()
            print("✅ test_worker_error_handling passed")
        except Exception as e:
            print(f"❌ test_worker_error_handling failed: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"Error loading tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())