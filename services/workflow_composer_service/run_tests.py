#!/usr/bin/env python3
"""
Test runner for the workflow composer service.
This script runs all tests from the main service directory.
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Run the integration tests."""
    service_dir = Path(__file__).parent
    tests_dir = service_dir / "tests"
    test_file = tests_dir / "test_integration_suite.py"
    
    if not test_file.exists():
        print("❌ Integration test suite not found!")
        sys.exit(1)
    
    print("🧪 Running workflow composer service integration tests...")
    print(f"📁 Tests directory: {tests_dir}")
    print("=" * 80)
    
    # Run the tests
    result = subprocess.run([
        sys.executable, 
        str(test_file)
    ], cwd=str(tests_dir))
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
