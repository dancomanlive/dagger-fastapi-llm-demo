"""
Temporal workflows for the workflow composer service.
These workflows orchestrate the dynamic workflow composition process.
"""
from temporalio import workflow
from typing import Dict, Any
from datetime import timedelta


@workflow.defn
class WorkflowCompositionWorkflow:
    """
    Main workflow for composing and executing dynamic workflows.
    This workflow coordinates the Pattern 2 process:
    1. Discover available activities
    2. Analyze requirements 
    3. Validate activity availability
    4. Generate workflow if complete
    """
    
    @workflow.run
    async def run(self, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow composition process."""
        
        workflow_name = workflow_request.get("workflow_name", "dynamic_workflow")
        workflow_description = workflow_request.get("workflow_description", "")
        requirements = workflow_request.get("requirements", [])
        
        try:
            # Step 1: Discover available activities
            discovery_result = await workflow.execute_activity(
                "discover_available_activities_activity",
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            # Step 2: Analyze requirements to determine needed activities
            analysis_result = await workflow.execute_activity(
                "analyze_workflow_requirements_activity",
                args=[workflow_description, requirements],
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            # Step 3: Validate that all required activities are available
            validation_result = await workflow.execute_activity(
                "validate_activity_availability_activity", 
                args=[
                    analysis_result.get("required_activities", []),
                    discovery_result.get("available_activities", {})
                ],
                start_to_close_timeout=timedelta(minutes=1)
            )
            
            # Step 4: Generate workflow if all activities are available
            generation_result = await workflow.execute_activity(
                "generate_workflow_if_complete_activity",
                args=[workflow_name, workflow_description, validation_result],
                start_to_close_timeout=timedelta(minutes=3)
            )
            
            return {
                "workflow_name": workflow_name,
                "composition_result": generation_result,
                "discovery_summary": {
                    "total_services": discovery_result.get("total_services", 0),
                    "total_activities": len(discovery_result.get("available_activities", {}))
                },
                "analysis_summary": {
                    "required_activities_count": len(analysis_result.get("required_activities", [])),
                    "analysis_method": analysis_result.get("analysis_method", "unknown")
                },
                "validation_summary": {
                    "is_complete": validation_result.get("is_complete", False),
                    "missing_count": len(validation_result.get("missing_activities", []))
                }
            }
            
        except Exception as e:
            return {
                "workflow_name": workflow_name,
                "error": f"Workflow composition failed: {str(e)}",
                "status": "FAILED"
            }
