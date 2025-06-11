"""
Temporal activities for embedding service.

This file contains the Temporal activities that will be executed by workers
to handle document embedding and indexing operations.
"""

import os
import time
import logging
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from temporalio import activity

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment variables (same as main.py)
QDRANT_HOST = os.getenv("QDRANT_HOST_FOR_SERVICE", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "fast-bge-small-en") # Updated default model
# Clean up PAYLOAD_TEXT_FIELD_NAME by removing comments and extra quotes
_raw_payload_field = os.getenv("PAYLOAD_TEXT_FIELD_NAME", "document")
PAYLOAD_TEXT_FIELD_NAME = _raw_payload_field.split('#')[0].strip().strip('"')


@activity.defn
async def perform_embedding_and_indexing_activity(documents: List[Dict[str, Any]], collection_name: str) -> Dict[str, Any]:
    """
    Temporal activity for performing embedding and indexing of documents.
    
    This function replaces the HTTP endpoint-based embedding logic.
    It will be called by Temporal workflows instead of HTTP requests.
    
    Args:
        documents: List of document objects to embed and index
                  Each document should have 'id' and 'text' fields
        collection_name: Name of the collection to store embeddings in
        
    Returns:
        dict: Success response with indexed count and metadata
        
    Raises:
        Exception: If embedding or indexing fails
    """
    qdrant_client = None
    start_time = time.time()
    
    try:
        logger.info(f"Starting embedding and indexing for {len(documents)} documents in collection '{collection_name}'")
        
        # Initialize Qdrant client
        client_args = {"url": QDRANT_HOST, "prefer_grpc": True}
        if QDRANT_API_KEY:
            client_args["api_key"] = QDRANT_API_KEY
        
        qdrant_client = QdrantClient(**client_args)
        logger.info(f"Connected to Qdrant at {QDRANT_HOST}")
        
        # Prepare documents for FastEmbed integration
        documents_to_add = []
        ids_to_add = []
        metadata_to_add = []
        
        for doc in documents:
            documents_to_add.append(doc['text'])
            ids_to_add.append(doc['id'])
            metadata_to_add.append({
                PAYLOAD_TEXT_FIELD_NAME: doc['text'],
                'id': doc['id'],
                'indexed_at': time.time()
            })
        
        # Use FastEmbed integration to embed and index in one step
        logger.info(f"Adding {len(documents_to_add)} documents to collection '{collection_name}' with FastEmbed")
        qdrant_client.add(
            collection_name=collection_name,
            documents=documents_to_add,
            ids=ids_to_add,
            metadata=metadata_to_add
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Successfully indexed {len(documents)} documents in {elapsed_time:.2f}s")
        
        return {
            "status": "success",
            "indexed_count": len(documents),
            "collection_name": collection_name,
            "embedding_model": EMBEDDING_MODEL_NAME,
            "elapsed_time": elapsed_time,
            "timestamp": time.time()
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Failed to embed and index documents: {str(e)}"
        logger.error(f"{error_msg} (after {elapsed_time:.2f}s)")
        raise Exception(error_msg)
        
    finally:
        # Always close the client
        if qdrant_client:
            try:
                qdrant_client.close()
                logger.info("Qdrant client closed")
            except Exception as e:
                logger.warning(f"Error closing Qdrant client: {e}")
