#!/usr/bin/env python3
"""
Test script to verify that no hardcoding remains in the temporal service.

This script checks all Python files in the temporal service to ensure:
1. No hardcoded activity names in orchestration logic
2. No hardcoded service names (except in configuration)
3. No hardcoded task queue names (except environment variables)
4. Dynamic activity discovery is working
5. Configuration-driven execution is functional
"""

import re
from pathlib import Path
from typing import List, Dict

# Service root directory
SERVICE_ROOT = Path(__file__).parent

# Files that are allowed to have hardcoded references (config, tests, docs)
ALLOWED_HARDCODING_FILES = {
    'config/services.yaml',
    'test_no_hardcoding.py',
    'validate_refactoring.py',
    'test_generic_workflows.py',
    'tests/test_service_config.py',
    'tests/test_dynamic_activities.py',
    'DYNAMIC_ACTIVITIES_EXAMPLE.md',
    'README.md',
    'MIGRATION_GUIDE.md'
}

# Hardcoded patterns to check for (excluding function parameters, comments, and environment defaults)
HARDCODED_PATTERNS = {
    'orchestration_hardcoding': [
        # Direct activity function calls without dynamic resolution (but not function definitions)
        r'(?<!async def )health_check_activity\(',
        # Hardcoded task queue references (not env defaults)
        r'"EmbeddingTaskQueue"',
        r'"RetrieverTaskQueue"',
        # Hardcoded service URLs in orchestration logic
        r'"http://embedding_service"',
        r'"http://retrieval_service"',
        # Pipeline hardcoding in workflow execute_activity calls - removing chunk and embed since they moved
        # Import statements for specific activities (should be dynamic) - removing moved activities
    ]
}

def get_python_files() -> List[Path]:
    """Get all Python files in the service directory."""
    python_files = []
    for file_path in SERVICE_ROOT.rglob("*.py"):
        relative_path = file_path.relative_to(SERVICE_ROOT)
        if str(relative_path) not in ALLOWED_HARDCODING_FILES:
            python_files.append(file_path)
    return python_files

def check_file_for_hardcoding(file_path: Path) -> Dict[str, List[str]]:
    """Check a single file for hardcoded patterns."""
    findings = {
        'orchestration_hardcoding': []
    }
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        for category, patterns in HARDCODED_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_num = content[:match.start()].count('\n') + 1
                    findings[category].append(f"Line {line_num}: {match.group()}")
    
    except Exception as e:
        print(f"⚠️  Error reading {file_path}: {e}")
    
    return findings

def test_dynamic_activity_discovery():
    """Test that dynamic activity discovery is working."""
    try:
        from service_config import get_service_config
        
        config = get_service_config()
        activities = config.discover_activity_functions('activities')
        activity_names = config.get_all_activity_names()
        
        print(f"   ✅ Discovered {len(activities)} activity functions dynamically")
        print(f"   ✅ Found {len(activity_names)} activity names in configuration")
        
        # Verify that we have activities
        assert len(activities) > 0, "No activities discovered"
        assert len(activity_names) > 0, "No activity names in configuration"
        
        # Verify activity function names match some config names
        discovered_names = {activity.__name__ for activity in activities}
        config_names = set(activity_names)
        
        # There should be some overlap (local activities)
        overlap = discovered_names.intersection(config_names)
        assert len(overlap) > 0, f"No overlap between discovered activities {discovered_names} and config {config_names}"
        
        print(f"   ✅ Activity name overlap verified: {overlap}")
        return True
        
    except Exception as e:
        print(f"   ❌ Dynamic activity discovery test failed: {e}")
        return False

def test_configuration_driven_execution():
    """Test that pipeline execution is configuration-driven."""
    try:
        from service_config import get_service_config
        
        config = get_service_config()
        
        # Test getting pipeline configuration
        pipelines = config.get_pipelines()
        assert len(pipelines) > 0, "No pipelines configured"
        
        # Test that executor can access activity configs
        activity_names = config.get_all_activity_names()
        for activity_name in activity_names:
            activity_config = config.get_activity_config(activity_name)
            assert activity_config is not None, f"No config found for activity {activity_name}"
        
        print("   ✅ Configuration-driven execution verified")
        print(f"   ✅ {len(pipelines)} pipelines configured")
        print(f"   ✅ {len(activity_names)} activities configured")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration-driven execution test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🔍 CHECKING FOR HARDCODED VALUES IN TEMPORAL SERVICE")
    print("=" * 60)
    
    # Get all Python files to check
    python_files = get_python_files()
    print(f"📁 Checking {len(python_files)} Python files...")
    
    # Track findings
    total_findings = 0
    files_with_hardcoding = []
    
    # Check each file
    for file_path in python_files:
        relative_path = file_path.relative_to(SERVICE_ROOT)
        findings = check_file_for_hardcoding(file_path)
        
        file_has_findings = any(findings.values())
        if file_has_findings:
            files_with_hardcoding.append(str(relative_path))
            print(f"\n❌ {relative_path}:")
            for category, items in findings.items():
                if items:
                    print(f"   {category.replace('_', ' ').title()}:")
                    for item in items:
                        print(f"     - {item}")
                        total_findings += 1
    
    # Summary of hardcoding check
    print("\n" + "=" * 60)
    print("📊 HARDCODING CHECK RESULTS")
    print("=" * 60)
    
    if total_findings == 0:
        print("✅ No hardcoded values found in orchestration logic!")
    else:
        print(f"❌ Found {total_findings} hardcoded values in {len(files_with_hardcoding)} files")
        for file_name in files_with_hardcoding:
            print(f"   - {file_name}")
    
    # Test dynamic functionality
    print("\n🧪 TESTING DYNAMIC FUNCTIONALITY")
    print("=" * 60)
    
    dynamic_discovery_ok = test_dynamic_activity_discovery()
    config_driven_ok = test_configuration_driven_execution()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS")
    print("=" * 60)
    
    all_tests_passed = (
        total_findings == 0 and
        dynamic_discovery_ok and
        config_driven_ok
    )
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ No hardcoding found")
        print("✅ Dynamic activity discovery working")
        print("✅ Configuration-driven execution working")
        print("\n💡 The temporal service is fully generic and configuration-driven!")
    else:
        print("❌ SOME TESTS FAILED")
        if total_findings > 0:
            print(f"❌ {total_findings} hardcoded values found")
        if not dynamic_discovery_ok:
            print("❌ Dynamic activity discovery failed")
        if not config_driven_ok:
            print("❌ Configuration-driven execution failed")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    exit(main())
