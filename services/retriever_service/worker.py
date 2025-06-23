"""
Temporal worker for retriever service.

This module sets up and runs a Temporal worker that executes
search_documents_activity for document retrieval operations.
"""

import asyncio
import logging
import os
import json
from aiohttp import web
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
METADATA_PORT = int(os.getenv("METADATA_PORT", "8083"))


async def handle_metadata(request):
    """
    Expose worker metadata for service discovery.
    """
    metadata = {
        "service_name": "retrieval_service",
        "task_queue": RETRIEVAL_TASK_QUEUE,
        "worker_identity": f"1@{os.uname().nodename}",
        "activities": [
            {
                "name": "search_documents_activity",
                "description": "Searches for relevant documents using semantic similarity",
                "timeout_seconds": 300,
                "retry_attempts": 3,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text",
                            "minLength": 1,
                            "maxLength": 1000
                        },
                        "collection_name": {
                            "type": "string",
                            "description": "Collection to search in",
                            "pattern": "^[a-zA-Z0-9_-]+$"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 10
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "Minimum similarity score threshold",
                            "minimum": 0.0,
                            "maximum": 1.0,
                            "default": 0.7
                        }
                    },
                    "required": ["query", "collection_name"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "description": "Whether search completed successfully"},
                        "results": {
                            "type": "array",
                            "description": "List of relevant documents with similarity scores",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "description": "Document identifier"},
                                    "content": {"type": "string", "description": "Document content"},
                                    "metadata": {
                                        "type": "object",
                                        "description": "Document metadata",
                                        "additionalProperties": True
                                    },
                                    "similarity_score": {
                                        "type": "number",
                                        "description": "Similarity score between 0 and 1",
                                        "minimum": 0.0,
                                        "maximum": 1.0
                                    }
                                },
                                "required": ["id", "content", "similarity_score"]
                            }
                        },
                        "total_found": {"type": "integer", "description": "Total number of documents found"},
                        "query_embedding_model": {"type": "string", "description": "Model used for query embedding"},
                        "collection_name": {"type": "string", "description": "Collection that was searched"},
                        "execution_time_ms": {"type": "number", "description": "Search execution time in milliseconds"}
                    },
                    "required": ["success", "results", "total_found", "collection_name"]
                },
                "parameters": [
                    {
                        "name": "query",
                        "type": "string", 
                        "description": "Search query text",
                        "required": True
                    },
                    {
                        "name": "collection_name",
                        "type": "string",
                        "description": "Collection to search in", 
                        "required": True
                    },
                    {
                        "name": "limit",
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "required": False
                    }
                ],
                "returns": {
                    "type": "array",
                    "description": "List of relevant documents with similarity scores"
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
    3. Creates a worker with the retrieval task queue
    4. Registers the search_documents_activity
    5. Starts the worker to listen for tasks
    """
    logger.info("Starting retriever service worker with metadata server...")
    logger.info(f"Temporal host: {TEMPORAL_HOST}")
    logger.info(f"Temporal namespace: {TEMPORAL_NAMESPACE}")
    logger.info(f"Task queue: {RETRIEVAL_TASK_QUEUE}")
    logger.info(f"Metadata port: {METADATA_PORT}")
    
    # Start metadata server
    metadata_runner = await start_metadata_server()
    
    try:
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
        
    except Exception as e:
        logger.error(f"Worker error: {e}")
        raise
    finally:
        # Cleanup metadata server
        await metadata_runner.cleanup()


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
