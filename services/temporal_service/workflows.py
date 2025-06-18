"""
Generic Temporal workflows for distributed service orchestration.

This module contains generic orchestration workflows that can execute
pipelines defined through configuration, making the service extensible
without code changes.

Workflows:
- GenericPipelineWorkflow: Executes any configured pipeline
"""

import logging
from typing import Dict, Any
from temporalio import workflow

# Import pipeline executor through sandbox
with workflow.unsafe.imports_passed_through():
    from pipeline_executor import PipelineExecutor

logger = logging.getLogger(__name__)


@workflow.defn
class GenericPipelineWorkflow:
    """
    Generic workflow that can execute any configured pipeline.
    """
    
    @workflow.run
    async def run(self, pipeline_name: str, input_data: Any) -> Dict[str, Any]:
        """
        Execute a pipeline by name using configuration.
        
        Args:
            pipeline_name: Name of the pipeline to execute (from services.yaml)
            input_data: Input data for the pipeline
            
        Returns:
            Pipeline execution result with status and results
        """
        workflow.logger.info(f"Starting generic pipeline: {pipeline_name}")
        
        try:
            executor = PipelineExecutor()
            result = await executor.execute_pipeline(pipeline_name, input_data)
            
            workflow.logger.info(f"Generic pipeline {pipeline_name} completed successfully")
            return result
            
        except Exception as e:
            workflow.logger.error(f"Generic pipeline {pipeline_name} failed: {str(e)}")
            raise
