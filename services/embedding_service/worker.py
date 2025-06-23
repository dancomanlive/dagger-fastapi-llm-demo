"""
Temporal worker for embedding service.

This worker registers and runs the embedding activities that can be called
by Temporal workflows instead of HTTP endpoints.
"""

import asyncio
import logging
import os
import json
from aiohttp import web
from aiohttp.web_runner import GracefulExit
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
METADATA_PORT = int(os.getenv("METADATA_PORT", "8082"))


async def handle_metadata(request):
    """
    Expose worker metadata for service discovery.
    
    This endpoint allows other services to discover what activities
    this worker provides without needing static configuration.
    """
    metadata = {
        "service_name": "embedding_service",
        "task_queue": EMBEDDING_TASK_QUEUE,
        "worker_identity": f"1@{os.uname().nodename}",
        "activities": [
            {
                "name": "perform_embedding_and_indexing_activity",
                "description": "Generates embeddings for documents and indexes them in vector database",
                "timeout_seconds": 1800,
                "retry_attempts": 3,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "documents": {
                            "type": "array",
                            "description": "List of document objects to embed and index",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Unique document identifier"},
                                    "content": {"type": "string", "description": "Document text content"},
                                    "metadata": {
                                        "type": "object",
                                        "description": "Additional document metadata",
                                        "additionalProperties": True
                                    }
                                },
                                "required": ["id", "content"]
                            }
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "Name of the collection to store embeddings",
                            "pattern": "^[a-zA-Z0-9_-]+$"
                        }
                    },
                    "required": ["documents", "collection_name"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "description": "Whether indexing completed successfully"},
                        "indexed_count": {"type": "integer", "description": "Number of documents successfully indexed"},
                        "collection_name": {"type": "string", "description": "Name of the collection used"},
                        "embedding_model": {"type": "string", "description": "Model used for embeddings"},
                        "total_documents": {"type": "integer", "description": "Total number of documents processed"},
                        "errors": {
                            "type": "array",
                            "description": "List of any errors encountered",
                            "items": {"type": "string"}
                        },
                        "execution_time_ms": {"type": "number", "description": "Total execution time in milliseconds"}
                    },
                    "required": ["success", "indexed_count", "collection_name"]
                },
                "parameters": [
                    {
                        "name": "documents",
                        "type": "array",
                        "description": "List of document objects to embed and index",
                        "required": True
                    },
                    {
                        "name": "collection_name", 
                        "type": "string",
                        "description": "Name of the collection to store embeddings",
                        "required": True
                    }
                ],
                "returns": {
                    "type": "object",
                    "description": "Indexing result with document count and collection info"
                }
            }
        ],
        "health": "healthy",
        "version": "1.0.0"
    }
    
    return web.json_response(metadata)


async def start_metadata_server():
    """Start HTTP metadata server for service discovery"""
    app = web.Application()
    app.router.add_get('/metadata', handle_metadata)
    app.router.add_get('/health', lambda r: web.json_response({"status": "healthy"}))
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', METADATA_PORT)
    await site.start()
    
    logger.info(f"📡 Metadata server started on port {METADATA_PORT}")
    logger.info(f"   Metadata endpoint: http://0.0.0.0:{METADATA_PORT}/metadata")
    logger.info(f"   Health endpoint: http://0.0.0.0:{METADATA_PORT}/health")
    
    return runner


async def run_worker():
    """
    Set up and run the Temporal worker with metadata server.
    
    This function:
    1. Starts a metadata HTTP server for service discovery
    2. Connects to the Temporal server
    3. Creates a worker with the embedding activity registered
    4. Starts the worker to listen for activity executions
    """
    logger.info("Starting embedding worker with metadata server...")
    logger.info(f"Temporal host: {TEMPORAL_HOST}")
    logger.info(f"Temporal namespace: {TEMPORAL_NAMESPACE}")
    logger.info(f"Task queue: {EMBEDDING_TASK_QUEUE}")
    logger.info(f"Metadata port: {METADATA_PORT}")
    
    # Start metadata server
    metadata_runner = await start_metadata_server()
    
    try:
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
        await worker.run()
        
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        # Cleanup metadata server
        await metadata_runner.cleanup()


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
