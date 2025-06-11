"""
Temporal worker for embedding service.

This worker registers and runs the embedding activities that can be called
by Temporal workflows instead of HTTP endpoints.
"""

import asyncio
import logging
import os
from temporalio.client import Client
from temporalio.worker import Worker

from activities import perform_embedding_and_indexing_activity

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
EMBEDDING_TASK_QUEUE = "embedding-task-queue"


async def run_worker():
    """
    Set up and run the Temporal worker for embedding activities.
    
    This function:
    1. Connects to the Temporal server
    2. Creates a worker with the embedding activity registered
    3. Starts the worker to listen for activity executions
    """
    logger.info("Starting embedding worker...")
    logger.info(f"Temporal host: {TEMPORAL_HOST}")
    logger.info(f"Temporal namespace: {TEMPORAL_NAMESPACE}")
    logger.info(f"Task queue: {EMBEDDING_TASK_QUEUE}")
    
    # Connect to Temporal server
    client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
    logger.info("Connected to Temporal server")
    
    # Create worker with our activities
    worker = Worker(
        client,
        task_queue=EMBEDDING_TASK_QUEUE,
        activities=[perform_embedding_and_indexing_activity]
    )
    logger.info(f"Created worker for task queue '{EMBEDDING_TASK_QUEUE}'")
    logger.info(f"Registered activities: {[func.__name__ for func in [perform_embedding_and_indexing_activity]]}")
    
    # Start the worker (this will run indefinitely)
    logger.info("Starting worker...")
    try:
        await worker.run()
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise


if __name__ == "__main__":
    """
    Entry point for running the worker directly.
    """
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        raise
