"""
Temporal worker for workflow composer service.
Registers activities and workflows with the temporal_service.
"""
import asyncio
import logging
from temporalio.worker import Worker
from temporal.config import get_temporal_client, SERVICE_CONFIG
from temporal.workflows import WorkflowCompositionWorkflow
import activities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_worker():
    """Set up and run the Temporal worker for workflow composer service."""
    task_queue = SERVICE_CONFIG["task_queue"]
    logger.info(f"Starting workflow composer worker on task queue: {task_queue}")
    
    # Connect to temporal_service
    client = await get_temporal_client()
    
    # Import all activities from activities.py
    activity_functions = [
        activities.discover_available_activities_activity,
        activities.analyze_workflow_requirements_activity, 
        activities.validate_activity_availability_activity,
        activities.generate_workflow_if_complete_activity
    ]
    
    # Create and configure the worker
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[WorkflowCompositionWorkflow],
        activities=activity_functions
    )
    
    logger.info(f"Registered {len(activity_functions)} activities and 1 workflow")
    logger.info("Activities: discover_available_activities, analyze_workflow_requirements, validate_activity_availability, generate_workflow_if_complete")
    logger.info("Workflows: WorkflowCompositionWorkflow")
    
    # Start the worker
    await worker.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        raise
