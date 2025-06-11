"""
Temporal worker for retriever service.

This module sets up and runs a Temporal worker that executes
search_documents_activity for document retrieval operations.
"""

import asyncio
import logging
import os
from temporalio.client import Client
from temporalio.worker import Worker

from activities import search_documents_activity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
RETRIEVAL_TASK_QUEUE = "retrieval-task-queue"


async def run_worker():
    """
    Set up and run the Temporal worker for retrieval activities.
    
    This function:
    1. Connects to the Temporal server
    2. Creates a worker with the retrieval task queue
    3. Registers the search_documents_activity
    4. Starts the worker to listen for tasks
    """
    logger.info("Starting retriever service worker...")
    logger.info(f"Temporal host: {TEMPORAL_HOST}")
    logger.info(f"Temporal namespace: {TEMPORAL_NAMESPACE}")
    logger.info(f"Task queue: {RETRIEVAL_TASK_QUEUE}")
    
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
    logger.info("Connected to Temporal server")
    
    # Create and configure the worker
    worker = Worker(
        client,
        task_queue=RETRIEVAL_TASK_QUEUE,
        activities=[search_documents_activity]
    )
    
    logger.info(f"Worker configured for task queue: {RETRIEVAL_TASK_QUEUE}")
    logger.info("Registered activities: search_documents_activity")
    
    # Start the worker
    logger.info("Starting worker...")
    await worker.run()


if __name__ == "__main__":
    """
    Run the worker when this module is executed directly.
    """
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        raise
