#!/usr/bin/env python3
"""
Simple runner for inline integration tests
"""
import os
import sys

# Set environment variable to enable inline tests
os.environ["RUN_INTEGRATION_TESTS"] = "1"

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import and run
from src.testing.run_all_integration_tests import main

if __name__ == "__main__":
    main()