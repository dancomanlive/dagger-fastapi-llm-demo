"""
Tests for the service registry functionality.
"""
import tempfile
import os
import yaml
from service_registry import (
    init_registry, 
    register_activity, 
    get_activity_metadata,
    export_registry_for_llm
)

def test_init_registry_with_file():
    """Test registry initialization from YAML file"""
    # Reset the global registry first
    import service_registry
    service_registry._activity_registry = {}
    service_registry._registry_initialized = False
    
    # Create a temporary registry file
    registry_data = {
        "services": {
            "test_service": {
                "activities": {
                    "test_activity": {
                        "description": "Test activity",
                        "task_queue": "test-queue",
                        "timeout_seconds": 60,
                        "parameters": [
                            {"name": "param1", "type": "string", "required": True}
                        ]
                    }
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(registry_data, f)
        temp_file = f.name
    
    try:
        # Initialize registry with the temp file
        registry = init_registry(temp_file)
        
        # Check that the activity was loaded
        assert "test_service.test_activity" in registry
        assert registry["test_service.test_activity"]["description"] == "Test activity"
        
    finally:
        os.unlink(temp_file)
        # Reset registry for other tests
        service_registry._activity_registry = {}
        service_registry._registry_initialized = False

def test_register_activity():
    """Test manual activity registration"""
    register_activity(
        service_name="manual_service",
        activity_name="manual_activity",
        description="Manually registered activity",
        parameters=[{"name": "input", "type": "string", "required": True}]
    )
    
    metadata = get_activity_metadata("manual_service.manual_activity")
    assert metadata["description"] == "Manually registered activity"
    assert metadata["service"] == "manual_service"

def test_export_registry_for_llm():
    """Test exporting registry in LLM-friendly format"""
    register_activity(
        service_name="llm_test_service",
        activity_name="llm_test_activity",
        description="Activity for LLM testing"
    )
    
    exported = export_registry_for_llm()
    
    assert "services" in exported
    assert "llm_test_service" in exported["services"]
    assert "llm_test_activity" in exported["services"]["llm_test_service"]["activities"]
