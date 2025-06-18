#!/usr/bin/env python3
"""
Comprehensive Test Runner for Temporal Service

This script runs all tests for the temporal service:
- Unit tests (pytest)
- Configuration validation
- Hardcoding detection
- Activity discovery tests
- Pipeline execution tests

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --unit       # Run only unit tests
    python run_tests.py --validate   # Run only validation tests
    python run_tests.py --coverage   # Run with coverage reporting
"""

import subprocess
import sys
import argparse
from pathlib import Path

class TestRunner:
    """Manages and executes all temporal service tests."""
    
    def __init__(self, show_coverage=False):
        self.show_coverage = show_coverage
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def run_command(self, command, description, cwd=None):
        """Run a command and capture results."""
        print(f"\n{'='*80}")
        print(f"🧪 {description}")
        print(f"{'='*80}")
        print(f"Command: {' '.join(command)}")
        if cwd:
            print(f"Working directory: {cwd}")
        print()
        
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Print output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"STDERR:\n{result.stderr}")
            
            success = result.returncode == 0
            if success:
                print(f"✅ {description} - PASSED")
                self.passed_tests += 1
            else:
                print(f"❌ {description} - FAILED (exit code: {result.returncode})")
                self.failed_tests += 1
            
            self.test_results.append({
                'name': description,
                'success': success,
                'exit_code': result.returncode
            })
            
            return success
            
        except Exception as e:
            print(f"❌ {description} - ERROR: {e}")
            self.failed_tests += 1
            self.test_results.append({
                'name': description,
                'success': False,
                'error': str(e)
            })
            return False
    
    def run_unit_tests(self):
        """Run pytest unit tests."""
        if self.show_coverage:
            command = [
                sys.executable, "-m", "pytest", "tests/", 
                "-v", "--cov=.", "--cov-report=term-missing",
                "--cov-report=html:htmlcov"
            ]
        else:
            command = [sys.executable, "-m", "pytest", "tests/", "-v"]
        
        return self.run_command(
            command,
            "Unit Tests (pytest)",
            cwd=Path(__file__).parent
        )
    
    def run_validation_tests(self):
        """Run service validation."""
        command = [sys.executable, "validate.py"]
        return self.run_command(
            command,
            "Service Validation",
            cwd=Path(__file__).parent
        )
    
    def run_hardcoding_detection(self):
        """Run hardcoding detection tests."""
        command = [sys.executable, "test_no_hardcoding.py"]
        return self.run_command(
            command,
            "Hardcoding Detection",
            cwd=Path(__file__).parent
        )
    
    def run_workflow_tests(self):
        """Test workflow instantiation and basic functionality."""
        command = [
            sys.executable, "-c",
            """
import sys
try:
    from workflows import GenericPipelineWorkflow
    from service_config import get_service_config
    from pipeline_executor import PipelineExecutor
    
    # Test workflow instantiation
    workflow = GenericPipelineWorkflow()
    print('✅ GenericPipelineWorkflow instantiation: PASSED')
    
    # Test service config
    config = get_service_config()
    pipelines = config.get_pipelines()
    print(f'✅ Pipeline configuration loading: PASSED ({len(pipelines)} pipelines)')
    
    # Test pipeline executor
    executor = PipelineExecutor()
    print('✅ PipelineExecutor instantiation: PASSED')
    
    # Test activity discovery
    activities = config.discover_activity_functions('activities')
    print(f'✅ Activity discovery: PASSED ({len(activities)} activities)')
    
    print('\\n🎉 All workflow tests passed!')
    
except Exception as e:
    print(f'❌ Workflow test failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
        ]
        return self.run_command(
            command,
            "Workflow Functionality Tests",
            cwd=Path(__file__).parent
        )
    
    def run_import_tests(self):
        """Test that all modules can be imported correctly."""
        command = [
            sys.executable, "-c",
            """
import sys
modules_to_test = [
    'workflows',
    'service_config', 
    'pipeline_executor',
    'activities',
    'worker'
]

failed_imports = []
for module in modules_to_test:
    try:
        __import__(module)
        print(f'✅ Import {module}: PASSED')
    except Exception as e:
        print(f'❌ Import {module}: FAILED - {e}')
        failed_imports.append(module)

if failed_imports:
    print(f'\\n❌ Failed to import: {failed_imports}')
    sys.exit(1)
else:
    print('\\n🎉 All imports successful!')
"""
        ]
        return self.run_command(
            command,
            "Module Import Tests",
            cwd=Path(__file__).parent
        )
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        total_tests = self.passed_tests + self.failed_tests
        print(f"Total test suites: {total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ The temporal service is working correctly")
            if self.show_coverage:
                print("📊 Coverage report generated in htmlcov/")
        else:
            print(f"\n❌ {self.failed_tests} TEST SUITES FAILED!")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']}")
        
        print("\n💡 Test Details:")
        for result in self.test_results:
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"  - {result['name']}: {status}")
        
        return self.failed_tests == 0

def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run temporal service tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--validate", action="store_true", help="Run only validation tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only (skip slow ones)")
    
    args = parser.parse_args()
    
    runner = TestRunner(show_coverage=args.coverage)
    
    print("🚀 TEMPORAL SERVICE TEST RUNNER")
    print("="*80)
    print("Running comprehensive tests for the temporal service...")
    
    # Determine which tests to run
    if args.unit:
        runner.run_unit_tests()
    elif args.validate:
        runner.run_validation_tests()
        runner.run_hardcoding_detection()
    elif args.quick:
        runner.run_import_tests()
        runner.run_validation_tests()
    else:
        # Run all tests
        runner.run_import_tests()
        runner.run_unit_tests()
        runner.run_validation_tests()
        runner.run_hardcoding_detection()
        runner.run_workflow_tests()
    
    # Print summary and exit with appropriate code
    success = runner.print_summary()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
