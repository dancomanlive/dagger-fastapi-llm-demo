"""
Workflow execution tools for running planned activity sequences.
Part of the Pattern 2 workflow: ... → Execute/Report
"""
from typing import Dict, Any, Optional
from smolagents import tool


@tool
def execute_planned_workflow(plan: Dict[str, Any], input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a planned workflow sequence.
    
    Args:
        plan: Plan dictionary from plan_activity_sequence
        input_data: Optional input data for the workflow
        
    Returns:
        Dictionary with execution results
    """
    try:
        if not plan.get("is_executable", False):
            return {
                "status": "failed",
                "error": "Plan is not executable",
                "missing_activities": plan.get("missing_activities", []),
                "message": "Cannot execute workflow - missing required activities"
            }
        
        execution_result = {
            "status": "in_progress", 
            "steps_completed": 0,
            "total_steps": len(plan.get("sequence", [])),
            "results": [],
            "errors": []
        }
        
        sequence = plan.get("sequence", [])
        
        for i, step in enumerate(sequence):
            step_result = {
                "step": i + 1,
                "activity": step.get("activity"),
                "status": "pending"
            }
            
            try:
                # For now, simulate execution (in real implementation, would call actual activities)
                activity_name = step.get("activity")
                
                # Mock execution based on activity type
                if "validate" in activity_name.lower():
                    step_result["result"] = {"valid": True, "message": "Input validation passed"}
                elif "search" in activity_name.lower():
                    step_result["result"] = {"matches": 5, "top_result": "mock_result"}
                elif "generate" in activity_name.lower():
                    step_result["result"] = {"generated": True, "output": "mock_generation"}
                elif "format" in activity_name.lower():
                    step_result["result"] = {"formatted": True, "format": "json"}
                else:
                    step_result["result"] = {"processed": True, "output": f"Processed {activity_name}"}
                
                step_result["status"] = "completed"
                execution_result["steps_completed"] += 1
                
            except Exception as step_error:
                step_result["status"] = "failed"
                step_result["error"] = str(step_error)
                execution_result["errors"].append(step_result)
            
            execution_result["results"].append(step_result)
        
        # Determine final status
        if execution_result["errors"]:
            execution_result["status"] = "partial_success"
        elif execution_result["steps_completed"] == execution_result["total_steps"]:
            execution_result["status"] = "completed"
        else:
            execution_result["status"] = "failed"
        
        execution_result["success_rate"] = execution_result["steps_completed"] / execution_result["total_steps"] if execution_result["total_steps"] > 0 else 0.0
        
        return execution_result
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Execution failed: {str(e)}"
        }


def create_workflow_from_activities(workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a workflow from a list of activities.
    
    Args:
        workflow_config: Dictionary with name, description, and activities list
        
    Returns:
        Dictionary with workflow creation result
    """
    try:
        name = workflow_config.get("name", "unnamed_workflow")
        description = workflow_config.get("description", "")
        activities = workflow_config.get("activities", [])
        
        if not activities:
            return {
                "success": False,
                "error": "No activities provided for workflow",
                "workflow_name": name
            }
        
        # Create a simple workflow definition
        workflow_definition = {
            "name": name,
            "description": description,
            "activities": activities,
            "created_at": "now",  # In real implementation, use actual timestamp
            "type": "generated",
            "status": "ready"
        }
        
        return {
            "success": True,
            "workflow_name": name,
            "workflow_definition": workflow_definition,
            "activity_count": len(activities),
            "message": f"Successfully created workflow '{name}' with {len(activities)} activities"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create workflow: {str(e)}",
            "workflow_name": workflow_config.get("name", "unknown")
        }
