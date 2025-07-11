#!/usr/bin/env python3
"""
Simple direct test runner
"""
import os
import sys
import asyncio

# Set up environment
os.environ["RUN_INTEGRATION_TESTS"] = "1"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use test database

# Add path
sys.path.insert(0, "/app")

async def main():
    print("🧪 Running Integration Tests\n")
    
    # Import and run test
    try:
        from src.handlers.test_workers import IntegrationTestWorkers
        
        test_instance = IntegrationTestWorkers()
        
        # Run each test method
        test_methods = [
            method for method in dir(test_instance) 
            if method.startswith('test_') and callable(getattr(test_instance, method))
        ]
        
        print(f"Found {len(test_methods)} test methods")
        
        for method_name in test_methods:
            print(f"\n▶ Running {method_name}...")
            try:
                method = getattr(test_instance, method_name)
                await method()
                print(f"✅ {method_name} passed")
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"Error loading tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())