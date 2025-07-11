#!/usr/bin/env python3
"""
Simple test to verify inline testing works
"""
import os
import sys
import asyncio

# Set up path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Enable integration tests
os.environ["RUN_INTEGRATION_TESTS"] = "1"

# Import testing framework
from src.testing.inline_test_runner import integration_test, run_inline_tests

class TestSimple:
    """Simple test class"""
    
    @integration_test
    async def test_basic_addition(self):
        """Test basic math"""
        assert 2 + 2 == 4
        print("✅ Basic addition test passed!")
    
    @integration_test
    async def test_async_operation(self):
        """Test async operation"""
        await asyncio.sleep(0.1)
        assert True
        print("✅ Async operation test passed!")

# Run tests
if __name__ == "__main__":
    asyncio.run(run_inline_tests(__name__))