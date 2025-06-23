#!/usr/bin/env python3
"""
Simple test runner for agent tool testing.
Provides clear pass/fail results for each test category.
"""
import sys
import subprocess
import os
from pathlib import Path

def run_test_script(script_name: str, description: str) -> bool:
    """Run a test script and return success status."""
    print(f"\n🧪 {description}")
    print("-" * 60)
    
    try:
        # Run the test script
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check if successful
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {description}")
        
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ FAILED - Test timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ FAILED - Error running test: {e}")
        return False


def check_prerequisites():
    """Check if all prerequisites are met for testing."""
    print("🔍 CHECKING PREREQUISITES")
    print("=" * 60)
    
    issues = []
    
    # Check if Python modules can be imported
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        sys.path.insert(0, str(Path(__file__).parent / "agents"))
        
        from agents.tools import infer_user_intent
        print("✅ Agent tools can be imported")
    except ImportError as e:
        issues.append(f"Cannot import agent tools: {e}")
        print(f"❌ Cannot import agent tools: {e}")
    
    # Check if required directories exist
    required_dirs = [
        Path(__file__).parent / "agents",
        Path(__file__).parent / "agents" / "tools",
        Path(__file__).parent / "generated"
    ]
    
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✅ Directory exists: {dir_path.name}")
        else:
            issues.append(f"Missing directory: {dir_path}")
            print(f"❌ Missing directory: {dir_path}")
            
            # Try to create generated directory if missing
            if dir_path.name == "generated":
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"✅ Created directory: {dir_path}")
                    issues = [i for i in issues if "generated" not in i]
                except Exception as e:
                    print(f"❌ Could not create directory: {e}")
    
    # Check if GraphQL server is running (optional)
    try:
        import requests
        response = requests.get("http://localhost:8002", timeout=2)
        print("✅ GraphQL server appears to be running")
    except:
        print("⚠️ GraphQL server may not be running (tests will show this)")
    
    if issues:
        print(f"\n❌ {len(issues)} prerequisite issues found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("\n✅ All prerequisites met")
        return True


def main():
    """Run all agent tool tests."""
    print("🚀 AGENT TOOL TEST RUNNER")
    print("=" * 60)
    print("Comprehensive testing of CodeAgent tool usage capabilities")
    print("")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix issues before running tests.")
        return False
    
    test_results = {}
    
    # Test 1: Individual tool functionality
    test_results["individual_tools"] = run_test_script(
        "test_agent_tools.py",
        "Testing Individual Tool Functionality and Agent Integration"
    )
    
    # Test 2: ReAct loop simulation
    test_results["react_loop"] = run_test_script(
        "test_react_loop.py", 
        "Testing ReAct Loop Pattern and Tool Compatibility"
    )
    
    # Summary
    print("\n\n📊 FINAL TEST RESULTS")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name.replace('_', ' ').title()}")
    
    overall_success = passed_tests == total_tests
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} test suites passed")
    
    if overall_success:
        print("✅ ALL TESTS PASSED - Agent is ready to use all tools!")
        print("\n🚀 Next steps:")
        print("   • Deploy the agent in a real scenario")
        print("   • Test with actual OpenAI API calls")
        print("   • Monitor ReAct loop performance")
    else:
        print("❌ SOME TESTS FAILED - Agent needs fixes before deployment")
        print("\n🔧 Next steps:")
        print("   • Review failed test outputs above")
        print("   • Fix identified issues")
        print("   • Re-run tests until all pass")
    
    return overall_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
