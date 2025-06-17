"""
Tests for LLM composer functionality.
"""
from llm_composer import (
    get_available_services_and_activities,
    get_activity_details,
    compose_workflow,
    list_workflows
)

def test_get_available_services_and_activities():
    """Test getting available services and activities"""
    services = get_available_services_and_activities()
    
    assert "services" in services
    assert isinstance(services["services"], dict)

def test_get_activity_details():
    """Test getting activity details"""
    # Test with non-existent activity
    result = get_activity_details("nonexistent.activity")
    assert "error" in result
    
    # Test with existing activity (would need to be registered first in a real test)
    # This is a basic structure test

def test_compose_workflow():
    """Test workflow composition"""
    # Test with invalid activity
    result = compose_workflow(
        name="TestWorkflow",
        description="Test workflow",
        activities=[{"id": "nonexistent.activity"}]
    )
    
    assert result["success"] is False
    assert "error" in result

def test_list_workflows():
    """Test listing workflows"""
    workflows = list_workflows()
    assert isinstance(workflows, list)
