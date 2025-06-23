"""
Temporal worker for embedding service.

This worker registers and runs the embedding activities that can be called
by Temporal workflows instead of HTTP endpoints.
"""

import asyncio
import logging
import os
from aiohttp import web
from temporalio.client import Client
from temporalio.worker import Worker

from activities import perform_embedding_and_indexing_activity, chunk_documents_activity

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")
EMBEDDING_TASK_QUEUE = "embedding-task-queue"
METADATA_PORT = int(os.getenv("METADATA_PORT", "8082"))


async def handle_metadata(request):
    """Expose worker metadata for service discovery."""
    return web.json_response({
        "service_name": "embedding_service",
        "task_queue": EMBEDDING_TASK_QUEUE,
        "worker_identity": f"1@{os.uname().nodename}",
        "activities": [
            {
                "name": "perform_embedding_and_indexing_activity",
                "description": "Generates embeddings for documents and indexes them in vector database",
                "timeout_seconds": 1800,
                "retry_attempts": 3
            },
            {
                "name": "chunk_documents_activity", 
                "description": "Chunks documents into smaller text segments for processing",
                "timeout_seconds": 600,
                "retry_attempts": 3
            }
        ],
        "health": "healthy",
        "version": "1.0.0"
    })


async def start_metadata_server():
    """Start HTTP metadata server for service discovery"""
    app = web.Application()
    app.router.add_get('/metadata', handle_metadata)
    app.router.add_get('/health', lambda r: web.json_response({"status": "healthy"}))
    
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', METADATA_PORT).start()
    
    logger.info(f"📡 Metadata server started on port {METADATA_PORT}")
    return runner


async def run_worker():
    """Set up and run the Temporal worker with metadata server."""
    logger.info(f"Starting embedding worker on {TEMPORAL_HOST} (queue: {EMBEDDING_TASK_QUEUE})")
    
    # Start metadata server
    metadata_runner = await start_metadata_server()
    
    try:
        # Connect to Temporal and create worker
        client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
        worker = Worker(
            client,
            task_queue=EMBEDDING_TASK_QUEUE,
            activities=[perform_embedding_and_indexing_activity, chunk_documents_activity]
        )
        
        logger.info(f"Registered activities: {[func.__name__ for func in [perform_embedding_and_indexing_activity, chunk_documents_activity]]}")
        logger.info("Starting worker...")
        await worker.run()
        
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        await metadata_runner.cleanup()


if __name__ == "__main__":
    """Entry point for running the worker directly."""
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        raise
