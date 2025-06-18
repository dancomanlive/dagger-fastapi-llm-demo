#!/usr/bin/env python3
"""
Test Runner Entry Point for SmartAgent-X7

This script runs the main test suite from the tests directory.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the main test suite"""
    tests_dir = Path(__file__).parent / "tests"
    test_runner = tests_dir / "run_tests.py"
    
    if not test_runner.exists():
        print("❌ Test runner not found at tests/run_tests.py")
        sys.exit(1)
    
    print("🚀 SmartAgent-X7 Test Suite")
    print("Running tests from tests/run_tests.py...")
    print()
    
    try:
        result = subprocess.run([sys.executable, str(test_runner)], cwd=str(Path(__file__).parent))
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
