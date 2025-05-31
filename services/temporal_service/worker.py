"""
Temporal worker for document processing workflows.
"""

import asyncio
import logging
import os
from temporalio.client import Client
from temporalio.worker import Worker
from dotenv import load_dotenv

from workflows import DocumentProcessingWorkflow, HealthCheckWorkflow
from activities import chunk_documents_activity, embed_documents_activity, health_check_activity

# Load environment variables (optional in production)
try:
    load_dotenv()
except Exception:
    # In production (like Koyeb), .env files might not exist
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "localhost:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
TASK_QUEUE = os.getenv("TEMPORAL_TASK_QUEUE", "document-processing-queue")

async def main():
    """Run the Temporal worker."""
    logger.info("Starting Temporal worker...")
    
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
        workflows=[DocumentProcessingWorkflow, HealthCheckWorkflow],
        activities=[
            chunk_documents_activity,
            embed_documents_activity,
            health_check_activity
        ],
        max_concurrent_workflow_tasks=10,
        max_concurrent_activities=20
    )
    
    logger.info(f"Worker started on task queue: {TASK_QUEUE}")
    
    # Run the worker
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
