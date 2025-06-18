"""
Temporal activities for retriever service.

This file contains the Temporal activities that will be executed by workers
to handle document search and retrieval operations.
"""

import os
import time
import logging
from typing import Dict, Any
from qdrant_client import QdrantClient
from temporalio import activity

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment variables (same as main.py)
QDRANT_HOST = os.getenv("QDRANT_HOST_FOR_SERVICE", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# Clean up PAYLOAD_TEXT_FIELD_NAME by removing comments and extra quotes
_raw_payload_field = os.getenv("PAYLOAD_TEXT_FIELD_NAME", "document")
PAYLOAD_TEXT_FIELD_NAME = _raw_payload_field.split('#')[0].strip().strip('"')


@activity.defn
async def search_documents_activity(query: str, collection_name: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Temporal activity for performing document search and retrieval.

    This function replaces the HTTP endpoint-based search logic.
    It will be called by Temporal workflows instead of HTTP requests.

    Args:
        query: The search query string
        collection_name: Name of the collection to search in
        top_k: Maximum number of results to return

    Returns:
        dict: Search results with status and retrieved documents

    Raises:
        Exception: If search fails
    """
    qdrant_client = None
    start_time = time.time()

    try:
        logger.info(f"Starting document search for query: '{query}' in collection '{collection_name}'")

        # Initialize Qdrant client with FastEmbed support
        client_args = {
            "url": QDRANT_HOST,
            "prefer_grpc": True,
        }
        if QDRANT_API_KEY:
            client_args["api_key"] = QDRANT_API_KEY

        qdrant_client = QdrantClient(**client_args)
        
        # Set the FastEmbed model exactly as shown in the documentation
        qdrant_client.set_model(EMBEDDING_MODEL_NAME)
        logger.info(f"Connected to Qdrant at {QDRANT_HOST} with embedding model: {EMBEDDING_MODEL_NAME}")

        # Use the simple query method from FastEmbed docs
        search_results = qdrant_client.query(
            collection_name=collection_name,
            query_text=query,
            limit=top_k
        )
                    collection_name=collection_name,
                    query_vector=NamedVector(
                        name="fast-bge-small-en",  # Use the actual vector name in the collection
                        vector=query_embedding.tolist()
                    ),
                    limit=top_k,
                    with_payload=True
                )
            else:
                raise e

        # Transform results
        retrieved_documents = []
        for hit in search_results:  # Direct iteration since query() returns the points directly
            payload_text = None
            if hit.payload:
                payload_text = hit.payload.get(PAYLOAD_TEXT_FIELD_NAME)
                if payload_text is None and PAYLOAD_TEXT_FIELD_NAME != "text":
                    payload_text = hit.payload.get("text")  # Fallback

            if payload_text:
                retrieved_documents.append({
                    "id": str(hit.id),
                    "text": payload_text,
                    "score": hit.score
                })
            else:
                logger.warning(f"Hit with ID {hit.id} has no '{PAYLOAD_TEXT_FIELD_NAME}' field in payload")

        processing_time = time.time() - start_time
        logger.info(f"Search completed in {processing_time:.4f} seconds. Found {len(retrieved_documents)} results")

        return {
            "status": "success",
            "query": query,
            "collection_name": collection_name,
            "results": retrieved_documents,
            "search_time": processing_time,
            "total_results": len(retrieved_documents)
        }

    except Exception as e:
        processing_time = time.time() - start_time
        error_message = f"Search failed after {processing_time:.4f} seconds: {str(e)}"
        logger.error(error_message)

        return {
            "status": "error",
            "query": query,
            "collection_name": collection_name,
            "results": [],
            "error_message": error_message,
            "search_time": processing_time
        }

    finally:
        if qdrant_client:
            try:
                qdrant_client.close()
            except Exception as e:
                logger.warning(f"Error closing Qdrant client: {e}")