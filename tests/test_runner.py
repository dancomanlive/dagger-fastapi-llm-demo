#!/usr/bin/env python3
"""
Comprehensive Test Runner for SmartAgent-X7 Project
Runs all tests across all services with coverage reporting
"""

import subprocess
import sys
from pathlib import Path
import argparse

def run_command(command, description, cwd=None):
    """Run a command and report results"""
    print(f"\n{'='*80}")
    print(f"🧪 {description}")
    print(f"{'='*80}")
    print(f"Running: {' '.join(command)}")
    if cwd:
        print(f"Working directory: {cwd}")
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
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

def run_service_tests(service_path, service_name):
    """Run tests for a specific service"""
    results = []
    
    print(f"\n🔧 Testing {service_name}")
    print(f"{'─'*60}")
    
    # Check if service has a test runner
    test_runner = service_path / "test_runner.py"
    if test_runner.exists():
        results.append(run_command(
            ["python", "test_runner.py"],
            f"{service_name} - Full Test Suite",
            cwd=service_path
        ))
    else:
        # Run pytest directly
        if (service_path / "tests").exists():
            results.append(run_command(
                ["python", "-m", "pytest", "tests/", "-v"],
                f"{service_name} - Unit Tests",
                cwd=service_path
            ))
    
    return results

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="SmartAgent-X7 Test Runner")
    parser.add_argument(
        "--service", 
        choices=["temporal", "embedding", "retriever", "gradio"],
        help="Run tests for a specific service only"
    )
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="Run quick tests without coverage"
    )
    parser.add_argument(
        "--coverage-only", 
        action="store_true",
        help="Run only tests with coverage reporting"
    )
    
    args = parser.parse_args()
    
    print("🚀 SmartAgent-X7 Comprehensive Test Runner")
    print("=" * 80)
    
    project_root = Path(__file__).parent
    services = {
        "temporal": project_root / "services" / "temporal_service",
        "embedding": project_root / "services" / "embedding_service", 
        "retriever": project_root / "services" / "retriever_service",
        "gradio": project_root / "services" / "gradio_service"
    }
    
    all_results = []
    
    # Run tests for specified service or all services
    if args.service:
        service_path = services[args.service]
        if service_path.exists():
            results = run_service_tests(service_path, args.service.title() + " Service")
            all_results.extend(results)
        else:
            print(f"❌ Service path not found: {service_path}")
            sys.exit(1)
    else:
        # Run tests for all services
        for service_name, service_path in services.items():
            if service_path.exists():
                results = run_service_tests(service_path, service_name.title() + " Service")
                all_results.extend(results)
            else:
                print(f"⚠️  Skipping {service_name} - path not found: {service_path}")
    
    # Run E2E tests if they exist
    e2e_script = project_root / "scripts" / "e2e_test.sh"
    if e2e_script.exists() and not args.service:
        all_results.append(run_command(
            ["bash", "scripts/e2e_test.sh"],
            "End-to-End Integration Tests",
            cwd=project_root
        ))
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(all_results)
    total = len(all_results)
    
    print(f"Total Tests Run: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")
    
    if passed == total and total > 0:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
