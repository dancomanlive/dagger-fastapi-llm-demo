"""
Generic pipeline executor for Temporal workflows.

This module provides generic pipeline execution capabilities, allowing workflows
to be defined through configuration rather than hardcoded logic.
"""

import logging
import os
from typing import Dict, Any, List
from temporalio import workflow
from service_config import get_service_config
from transforms import get_transform

logger = logging.getLogger(__name__)

class PipelineExecutor:
    """Generic pipeline executor for workflows."""
    
    def __init__(self):
        """Initialize pipeline executor."""
        self.config = get_service_config()
        self.document_collection_name = os.environ.get("DOCUMENT_COLLECTION_NAME", "document_chunks")
        # Store original workflow input for transforms that need it
        self.workflow_input_data = None
    
    async def execute_activity_by_name(self, activity_name: str, args: List[Any]) -> Any:
        """
        Execute an activity by name using configuration.
        
        Args:
            activity_name: Name of the activity to execute
            args: Arguments to pass to the activity
            
        Returns:
            Activity execution result
        """
        activity_config = self.config.get_activity_config(activity_name)
        
        if not activity_config:
            raise ValueError(f"Activity '{activity_name}' not found in configuration")
        
        workflow.logger.info(f"Executing activity: {activity_name}")
        
        execution_params = {
            "start_to_close_timeout": self.config.get_timeout(activity_config),
            "retry_policy": self.config.get_retry_policy(activity_config)
        }
        
        # Unified invocation for both local and remote activities
        if activity_config["type"] == "local":
            with workflow.unsafe.imports_passed_through():
                import activities
            activity_func = getattr(activities, activity_name, None)
            if activity_func is None:
                raise ValueError(f"Local activity function '{activity_name}' not found in activities module")
            return await workflow.execute_activity(
                activity_func,
                args,
                **execution_params
            )
        else:
            execution_params["task_queue"] = activity_config["task_queue"]
            return await workflow.execute_activity(
                activity_name,
                args,
                **execution_params
            )
    
    async def execute_pipeline(self, pipeline_name: str, input_data: Any) -> Dict[str, Any]:
        """
        Execute a pipeline by name using configuration.
        
        Args:
            pipeline_name: Name of the pipeline to execute
            input_data: Input data for the pipeline
            
        Returns:
            Pipeline execution result
        """
        pipeline_config = self.config.get_pipeline_config(pipeline_name)
        
        if not pipeline_config:
            raise ValueError(f"Pipeline '{pipeline_name}' not found in configuration")
        
        # Store original input data for transforms
        self.workflow_input_data = input_data
        
        workflow.logger.info(f"Starting pipeline: {pipeline_name}")
        
        # Initialize pipeline state
        current_data = input_data
        results = {
            "pipeline_name": pipeline_name,
            "status": "running",
            "workflow_id": workflow.info().workflow_id,
            "steps_completed": 0,
            "step_results": []
        }
        
        try:
            # Execute each step in the pipeline
            for step_index, step in enumerate(pipeline_config.get("steps", [])):
                activity_name = step["activity"]
                transform_type = step.get("input_transform", "passthrough")
                
                workflow.logger.info(f"Step {step_index + 1}: {activity_name} with transform: {transform_type}")
                
                transform = get_transform(transform_type)
                step_args = transform.transform(current_data, step, self.workflow_input_data, self.document_collection_name)
                
                # Execute the activity
                step_result = await self.execute_activity_by_name(activity_name, step_args)
                
                # Update pipeline state
                current_data = step_result
                results["steps_completed"] = step_index + 1
                results["step_results"].append({
                    "step": step_index + 1,
                    "activity": activity_name,
                    "status": "completed"
                })
                
                workflow.logger.info(f"Step {step_index + 1} completed")
            
            # Pipeline completed successfully
            results["status"] = "completed"
            results["final_result"] = current_data
            
            workflow.logger.info(f"Pipeline {pipeline_name} completed successfully")
            return results
            
        except Exception as e:
            # Pipeline failed
            results["status"] = "failed"
            results["error"] = str(e)
            
            workflow.logger.error(f"Pipeline {pipeline_name} failed: {str(e)}")
            raise
    
    def transform_input(self, transform_type: str, input_data: Any, step_context: Dict[str, Any] = None) -> Any:
        """
        Transform input data using the specified transform type.
        
        This method is used for testing transform functionality in isolation.
        
        Args:
            transform_type: Type of transform to apply
            input_data: Input data to transform
            step_context: Optional step context for the transform
            
        Returns:
            Transformed data
        """
        transform = get_transform(transform_type)
        if step_context is None:
            step_context = {}
        
        # Use empty workflow input if not set
        workflow_input = self.workflow_input_data or {}
        
        return transform.transform(input_data, step_context, workflow_input, self.document_collection_name)
