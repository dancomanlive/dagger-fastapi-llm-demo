#!/usr/bin/env python3
"""
Test runner for Temporal Service
Runs both unit tests (pytest) and BDD tests (behave)
"""

import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Main test runner"""
    print("🚀 Temporal Service Test Runner")
    print("Running comprehensive test suite...")
    
    results = []
    
    # Run unit tests with coverage
    results.append(run_command(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
        "Unit Tests with Coverage"
    ))
    
    # Run BDD tests
    results.append(run_command(
        ["python", "-m", "behave", "features/", "-v"],
        "BDD Integration Tests"
    ))
    
    # Run integration test script if it exists
    integration_script = Path("run_integration_tests.py")
    if integration_script.exists():
        results.append(run_command(
            ["python", "run_integration_tests.py"],
            "Integration Test Suite"
        ))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
