"""
Tests for workflow engine functionality.
"""
import tempfile
import os
import yaml
from workflow_engine import (
    load_workflow_definitions,
    save_workflow_definition,
    execute_workflow_sync
)

def test_load_workflow_definitions():
    """Test loading workflow definitions from YAML files"""
    # Reset the workflow cache first
    import workflow_engine
    workflow_engine._workflow_definitions = {}
    workflow_engine._workflow_cache_initialized = False
    
    # Create a temporary workflow file
    workflow_data = {
        "workflows": [
            {
                "name": "TestWorkflow",
                "description": "Test workflow",
                "version": "1.0.0",
                "activities": [
                    {
                        "id": "test_service.test_activity",
                        "result_key": "test_result",
                        "parameters": []
                    }
                ]
            }
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        workflow_file = os.path.join(temp_dir, "test_workflow.yaml")
        with open(workflow_file, 'w') as f:
            yaml.dump(workflow_data, f)
        
        # Load workflow definitions
        workflows = load_workflow_definitions(temp_dir)
        
        assert "TestWorkflow" in workflows
        assert workflows["TestWorkflow"]["description"] == "Test workflow"
        assert len(workflows["TestWorkflow"]["activities"]) == 1

def test_save_workflow_definition():
    """Test saving workflow definitions"""
    workflow_def = {
        "name": "SaveTestWorkflow",
        "description": "Workflow for save testing",
        "version": "1.0.0",
        "activities": []
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change to temp directory for saving
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Save the workflow
            filepath = save_workflow_definition(workflow_def)
            
            # Verify file was created
            assert os.path.exists(filepath)
            
            # Load and verify content
            with open(filepath, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert "workflows" in saved_data
            assert len(saved_data["workflows"]) == 1
            assert saved_data["workflows"][0]["name"] == "SaveTestWorkflow"
            
        finally:
            os.chdir(original_cwd)

def test_execute_workflow_sync():
    """Test synchronous workflow execution"""
    workflow_name = "TestWorkflow"
    inputs = {"param1": "value1"}
    
    result = execute_workflow_sync(workflow_name, inputs)
    
    assert result["status"] == "completed"
    assert result["workflow_name"] == workflow_name
    assert result["inputs"] == inputs
