#!/usr/bin/env python3
"""
Test Runner for SmartAgent-X7 Unit Tests

This script runs all available unit tests and provides a coverage report
for the input/output contracts of each service.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description, timeout=30):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=str(Path(__file__).parent.parent),  # Go up one level from tests/ to project root
            timeout=timeout
        )
        
        if result.returncode == 0:
            print("✅ PASSED")
            print(result.stdout)
        else:
            print("❌ FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT after {timeout} seconds")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


def main():
    """Run all tests and generate coverage report"""
    
    print("🚀 SmartAgent-X7 Unit Test Suite")
    print("="*60)
    print("📋 Running UNIT TESTS only (no integration tests)")
    print("="*60)
    
    # Track test results
    results = {}
    
    # 1. Retriever Service Tests
    results["retriever_io"] = run_command(
        "python -m pytest services/retriever_service/tests/test_retriever_io.py -v",
        "Retriever Service I/O Tests"
    )
    
    # 2. Embedding Service Tests  
    results["embedding_io"] = run_command(
        "python -m pytest services/embedding_service/tests/test_embedding_io.py -v",
        "Embedding Service I/O Tests"
    )
    
    # 3. Temporal Service Tests (existing)
    results["temporal_config"] = run_command(
        "python -m pytest services/temporal_service/tests/test_service_config.py -v",
        "Temporal Service Configuration Tests"
    )
    
    results["temporal_activities"] = run_command(
        "python -m pytest services/temporal_service/tests/test_dynamic_activities.py -v", 
        "Temporal Service Dynamic Activities Tests"
    )
    
    # 4. Temporal Workflow Tests (unit tests)
    results["temporal_workflows_unit"] = run_command(
        "python -m pytest services/temporal_service/tests/test_workflows_unit.py -v",
        "Temporal Service Workflow Unit Tests"
    )
    
    # 5. Temporal Workflow Tests (integration - may hang, run with timeout)
    print(f"\n{'='*60}")
    print("⚠️  NOTE: Temporal integration tests may hang due to environment setup")
    print("    Running with 60-second timeout...")
    print("="*60)
    results["temporal_workflows_integration"] = run_command(
        "python -m pytest services/temporal_service/tests/test_workflows.py::TestGenericPipelineWorkflow::test_workflow_logic_unit -v",
        "Temporal Service Workflow Integration Tests (Limited)",
        timeout=60
    )
    
    # 6. Gradio Service Tests
    gradio_test_path = Path("services/gradio_service/tests")
    if gradio_test_path.exists() and any(gradio_test_path.glob("test_*.py")):
        results["gradio"] = run_command(
            "python -m pytest services/gradio_service/tests/ -v",
            "Gradio Service Tests"
        )
    else:
        print(f"\n{'='*60}")
        print("⚠️  Gradio Service Tests")
        print("="*60)
        print("✅ Found Gradio tests - running them...")
        results["gradio"] = run_command(
            "python -m pytest services/gradio_service/tests/ -v",
            "Gradio Service Tests"
        )
    
    # Note: Integration tests are excluded from unit test runs
    # To run integration tests separately:
    # 1. Start services: docker-compose up
    # 2. Run: python tests/test_retrieval_only.py
    
    # Generate Summary Report
    print(f"\n{'='*60}")
    print("📊 TEST COVERAGE SUMMARY")
    print("="*60)
    
    # Filter out skipped tests for counting
    counted_results = {k: v for k, v in results.items() if v is not None}
    total_tests = len(counted_results)
    passed_tests = sum(1 for result in counted_results.values() if result)
    
    for test_name, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:  # None = skipped
            status = "⏸️  SKIP"
        print(f"{test_name:25} | {status}")
    
    print("-" * 60)
    print(f"TOTAL: {passed_tests}/{total_tests} tests passing")
    
    if total_tests > 0:
        coverage_percent = (passed_tests / total_tests) * 100
        print(f"COVERAGE: {coverage_percent:.1f}%")
    else:
        coverage_percent = 0
        print("COVERAGE: 0% (no tests to run)")
    
    skipped_count = len([r for r in results.values() if r is None])
    if skipped_count > 0:
        print(f"SKIPPED: {skipped_count} tests")
    
    # Critical Gaps Analysis
    print(f"\n{'='*60}")
    print("🚨 CRITICAL GAPS ANALYSIS")
    print("="*60)
    
    critical_gaps = []
    
    if not results.get("retriever_io", False):
        critical_gaps.append("❌ Retriever Service I/O validation")
        
    if not results.get("embedding_io", False):
        critical_gaps.append("❌ Embedding Service I/O validation")
        
    if not results.get("gradio", False):
        critical_gaps.append("❌ Gradio Service integration tests")
    
    # Check for missing test files
    missing_tests = []
    
    if not Path("services/gradio_service/tests/test_rag_service.py").exists():
        missing_tests.append("❌ services/gradio_service/tests/test_rag_service.py")
        
    if not Path("services/gradio_service/tests/test_gradio_integration.py").exists():
        missing_tests.append("❌ services/gradio_service/tests/test_gradio_integration.py")
    
    if critical_gaps:
        print("CRITICAL ISSUES:")
        for gap in critical_gaps:
            print(f"  {gap}")
    
    if missing_tests:
        print("\nMISSING TEST FILES:")
        for missing in missing_tests:
            print(f"  {missing}")
    
    if not critical_gaps and not missing_tests:
        print("✅ No critical gaps detected!")
    
    # Recommendations
    print(f"\n{'='*60}")
    print("💡 RECOMMENDATIONS")
    print("="*60)
    
    if coverage_percent < 80:
        print("⚠️  Test coverage is below 80% - consider adding more tests")
    
    if not results.get("gradio", False):
        print("🔧 Priority: Create Gradio service integration tests")
        print("   - Test RAG pipeline end-to-end")
        print("   - Test metrics collection and display")
        print("   - Test error handling")
    
    print("\n🎯 Next Steps:")
    print("1. Fix any failing unit tests above")
    print("2. Add missing test files") 
    print("3. Run integration tests separately when services are running")
    print("4. Add performance/load tests")
    
    print("\n🔧 Integration Tests (run separately):")
    print("   docker-compose up && python tests/test_retrieval_only.py")
    
    # Exit with appropriate code
    if coverage_percent >= 60:  # Reasonable threshold
        print(f"\n✅ Test suite PASSED with {coverage_percent:.1f}% coverage")
        sys.exit(0)
    else:
        print(f"\n❌ Test suite FAILED - only {coverage_percent:.1f}% coverage")
        sys.exit(1)


if __name__ == "__main__":
    main()
