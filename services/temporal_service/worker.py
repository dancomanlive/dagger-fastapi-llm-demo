"""
Temporal worker for document processing workflows.
"""

import asyncio
import logging
import os
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import GenericPipelineWorkflow
from service_config import get_service_config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Also enable Temporal logging
logging.getLogger("temporalio").setLevel(logging.DEBUG)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "document-processing-queue")

async def main():
    """Run the Temporal worker."""
    logger.info("Starting Temporal worker...")
    
    # Get service configuration
    config = get_service_config()
    
    # Dynamically discover activity functions
    activity_functions = config.discover_activity_functions("activities")
    logger.info(f"Discovered {len(activity_functions)} activity functions")
    
    # Create client
    client = await Client.connect(
        TEMPORAL_HOST,
        namespace=TEMPORAL_NAMESPACE
    )
    
    logger.info(f"Connected to Temporal at {TEMPORAL_HOST}, namespace: {TEMPORAL_NAMESPACE}")
    
    # Create and run worker
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GenericPipelineWorkflow],
        activities=activity_functions,
        max_concurrent_workflow_tasks=10,
        max_concurrent_activities=20
    )
    
    logger.info(f"Worker started on task queue: {TASK_QUEUE}")
    
    # Run the worker
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
