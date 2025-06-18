"""
Temporal activities for retriever service.

This file contains the Temporal activities that will be executed by workers
to handle document retrieval operations.
"""

import os
import time
import logging
from typing import Dict, Any
from qdrant_client import QdrantClient
from temporalio import activity

# Import normalization function from temporal service
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'temporal_service'))
from normalization import normalize_args_input

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment variables
QDRANT_HOST = os.getenv("QDRANT_HOST_FOR_SERVICE", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
# Clean up EMBEDDING_MODEL_NAME by removing comments and extra quotes
_raw_embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
EMBEDDING_MODEL_NAME = _raw_embedding_model.split('#')[0].strip().strip('"')
# Clean up PAYLOAD_TEXT_FIELD_NAME by removing comments and extra quotes
_raw_payload_field = os.getenv("PAYLOAD_TEXT_FIELD_NAME", "document")
PAYLOAD_TEXT_FIELD_NAME = _raw_payload_field.split('#')[0].strip().strip('"')


@activity.defn
async def search_documents_activity(*args) -> Dict[str, Any]:
    """
    Temporal activity for searching documents in Qdrant using FastEmbed.
    
    Args:
        *args: Supports both direct arguments (query, collection_name, top_k) 
               and packed arguments ([query, collection_name, top_k])
        
    Returns:
        dict: Search results with status and retrieved documents

    Raises:
        Exception: If search fails
    """
    # Normalize arguments (eliminates all if/else chains!)
    normalized_args = normalize_args_input(*args)
    query = normalized_args["query"]
    collection_name = normalized_args["collection"]
    top_k = normalized_args["top_k"]
    
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
        
        # Set the FastEmbed model for embedding the query
        qdrant_client.set_model(EMBEDDING_MODEL_NAME)
        logger.info(f"Connected to Qdrant at {QDRANT_HOST} with embedding model: {EMBEDDING_MODEL_NAME}")

        # Use the simple query method from FastEmbed docs
        search_results = qdrant_client.query(
            collection_name=collection_name,
            query_text=query,
            limit=top_k
        )
        
        # Debug: log the response structure
        logger.info(f"Search results type: {type(search_results)}")
        if hasattr(search_results, '__dict__'):
            logger.info(f"Search results attributes: {list(search_results.__dict__.keys())}")
        if hasattr(search_results, 'points'):
            logger.info(f"Points type: {type(search_results.points)}, length: {len(search_results.points) if search_results.points else 0}")

        # Transform results - handle the QueryResponse format
        retrieved_documents = []
        
        # The query method returns a different format than search
        # It returns points directly, not in a hits format
        if hasattr(search_results, 'points') and search_results.points:
            hits = search_results.points
        elif isinstance(search_results, list):
            hits = search_results
        else:
            hits = []
            
        logger.info(f"Processing {len(hits)} hits")
        for i, hit in enumerate(hits):
            logger.info(f"Hit {i}: type={type(hit)}, id={getattr(hit, 'id', 'unknown')}")
            if hasattr(hit, '__dict__'):
                logger.info(f"Hit {i} attributes: {list(hit.__dict__.keys())}")
                
            payload_text = None
            
            # Handle QueryResponse objects from FastEmbed
            if hasattr(hit, 'document') and hit.document:
                payload_text = hit.document
                logger.info(f"Hit {i}: Found document text directly: {payload_text[:100]}...")
            elif hasattr(hit, 'metadata') and hit.metadata:
                # Try to get text from metadata
                payload_text = hit.metadata.get(PAYLOAD_TEXT_FIELD_NAME)
                if payload_text is None and PAYLOAD_TEXT_FIELD_NAME != "text":
                    payload_text = hit.metadata.get("text")  # Fallback
                logger.info(f"Hit {i}: Found text in metadata: {payload_text[:100] if payload_text else 'None'}...")
            elif hasattr(hit, 'payload') and hit.payload:
                # Fallback for traditional format
                payload_text = hit.payload.get(PAYLOAD_TEXT_FIELD_NAME)
                if payload_text is None and PAYLOAD_TEXT_FIELD_NAME != "text":
                    payload_text = hit.payload.get("text")  # Fallback
                logger.info(f"Hit {i}: Found text in payload: {payload_text[:100] if payload_text else 'None'}...")

            if payload_text:
                retrieved_documents.append({
                    "id": str(hit.id),
                    "text": payload_text,
                    "score": getattr(hit, 'score', 0.0)
                })
            else:
                logger.warning(f"Hit with ID {getattr(hit, 'id', 'unknown')} has no text content available")

        processing_time = time.time() - start_time
        logger.info(f"Search completed in {processing_time:.4f} seconds. Found {len(retrieved_documents)} results")

        return {
            "status": "success",
            "query": query,
            "retrieved_documents": retrieved_documents,
            "total_results": len(retrieved_documents),
            "processing_time": processing_time,
            "collection_name": collection_name
        }

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Search failed after {processing_time:.4f} seconds: {str(e)}"
        logger.error(error_msg)
        
        return {
            "status": "error",
            "query": query,
            "error": error_msg,
            "retrieved_documents": [],
            "total_results": 0,
            "processing_time": processing_time,
            "collection_name": collection_name
        }

    finally:
        if qdrant_client:
            try:
                qdrant_client.close()
                logger.info("Qdrant client closed")
            except Exception as e:
                logger.warning(f"Error closing Qdrant client: {e}")
