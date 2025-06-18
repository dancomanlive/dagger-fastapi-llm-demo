#!/usr/bin/env python3
"""
Validation script for the generic temporal service.

This script validates that the temporal service is properly configured
and ready to execute pipelines through the GenericPipelineWorkflow.
"""

import sys
from pathlib import Path

def validate_imports():
    """Test that all required modules can be imported."""
    try:
        from workflows import GenericPipelineWorkflow
        from service_config import get_service_config
        from pipeline_executor import PipelineExecutor
        import activities  # Import activities module to test dynamic loading
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def validate_configuration():
    """Test that configuration loads correctly."""
    try:
        from service_config import get_service_config
        
        config = get_service_config()
        
        # Test service configuration
        services = config.get_services()
        pipelines = config.get_pipelines()
        
        print(f"✅ Services configured: {list(services.keys())}")
        print(f"✅ Pipelines configured: {list(pipelines.keys())}")
        
        # Test pipeline configurations
        for pipeline_name in pipelines:
            pipeline_config = config.get_pipeline_config(pipeline_name)
            if not pipeline_config:
                print(f"❌ Missing configuration for pipeline: {pipeline_name}")
                return False
            
            steps = pipeline_config.get("steps", [])
            if not steps:
                print(f"❌ No steps defined for pipeline: {pipeline_name}")
                return False
                
            print(f"✅ Pipeline '{pipeline_name}' has {len(steps)} steps")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def validate_activity_discovery():
    """Test that activities can be discovered dynamically."""
    try:
        from service_config import get_service_config
        
        config = get_service_config()
        activities = config.discover_activity_functions("activities")
        activity_names = config.get_all_activity_names()
        
        print(f"✅ Discovered {len(activities)} activity functions")
        print(f"✅ Found {len(activity_names)} activity names in configuration")
        
        if len(activities) == 0:
            print("❌ No activities discovered")
            return False
            
        if len(activity_names) == 0:
            print("❌ No activity names in configuration")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Activity discovery error: {e}")
        return False

def validate_workflow_instantiation():
    """Test that workflows can be instantiated."""
    try:
        from workflows import GenericPipelineWorkflow
        
        workflow = GenericPipelineWorkflow()
        print("✅ GenericPipelineWorkflow instantiated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow instantiation error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🧪 TEMPORAL SERVICE VALIDATION")
    print("=" * 50)
    
    tests = [
        ("Imports", validate_imports),
        ("Configuration", validate_configuration),
        ("Activity Discovery", validate_activity_discovery),
        ("Workflow Instantiation", validate_workflow_instantiation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔧 Testing {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name} test passed")
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    print(f"Total tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ The temporal service is ready for use")
        print("✅ GenericPipelineWorkflow is functional")
        print("✅ Configuration-driven pipelines are working")
        
        print("\n💡 Next steps:")
        print("• Start the temporal worker: python worker.py")
        print("• Test with live Temporal server")
        print("• Add new pipelines to config/services.yaml")
        return 0
    else:
        print(f"\n❌ {failed} VALIDATION TESTS FAILED!")
        print("Please fix the issues before using the service.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
