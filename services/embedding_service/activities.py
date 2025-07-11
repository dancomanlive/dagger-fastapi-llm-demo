"""
Temporal activities for embedding service.

This file contains the Temporal activities that will be executed by workers
to handle document embedding and indexing operations.
"""

import os
import time
import logging
import re
import uuid
from typing import Dict, Any, List
from qdrant_client import QdrantClient
from temporalio import activity

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment variables (same as main.py)
QDRANT_HOST = os.getenv("QDRANT_HOST_FOR_SERVICE", "http://qdrant:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5") # Updated default model
# Clean up PAYLOAD_TEXT_FIELD_NAME by removing comments and extra quotes
_raw_payload_field = os.getenv("PAYLOAD_TEXT_FIELD_NAME", "document")
PAYLOAD_TEXT_FIELD_NAME = _raw_payload_field.split('#')[0].strip().strip('"')


@activity.defn
async def chunk_documents_activity(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Chunk documents into paragraphs for better processing.
    
    Args:
        documents: List of documents with 'id', 'text', and optional 'metadata'
    
    Returns:
        List of chunked documents with chunk IDs
    """
    logger.info(f"Chunking {len(documents)} documents")
    
    chunked_docs = []
    
    for doc in documents:
        doc_id = doc["id"]
        text = doc["text"]
        metadata = doc.get("metadata", {})
        
        # Split text into paragraphs (by double newlines or single newlines followed by whitespace)
        paragraphs = re.split(r'\n\s*\n|\n(?=\s)', text.strip())
        
        # Filter out empty paragraphs and very short ones
        valid_paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 20]
        
        # Create chunks
        for chunk_idx, paragraph in enumerate(valid_paragraphs):
            # Generate a proper UUID for the chunk
            chunk_id = str(uuid.uuid4())
            
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "original_doc_id": doc_id,
                "chunk_index": chunk_idx,
                "total_chunks": len(valid_paragraphs)
            })
            
            chunked_docs.append({
                "id": chunk_id,
                "text": paragraph,
                "metadata": chunk_metadata
            })
    
    logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
    return chunked_docs


@activity.defn
async def perform_embedding_and_indexing_activity(
    *args, **kwargs
) -> Dict[str, Any]:
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
    # Handle the argument structure that Temporal passes
    # When called from a workflow with *args spreading, Temporal wraps the arguments in a single list
    if len(args) == 2:
        # Direct unpacking: documents, collection_name
        documents, collection_name = args
        activity.logger.info(f"Using direct args unpacking: {len(documents)} documents for collection '{collection_name}'")
    elif len(args) == 1 and isinstance(args[0], list) and len(args[0]) == 2:
        # Wrapped in an extra list: [[documents], collection_name]
        documents, collection_name = args[0]
        activity.logger.info(f"Using nested list unpacking: {len(documents)} documents for collection '{collection_name}'")
    else:
        raise ValueError(f"Unexpected arguments structure: args={args}, kwargs={kwargs}")
    
    activity.logger.info(f"Starting embedding and indexing for {len(documents)} documents in collection '{collection_name}'")
    
    qdrant_client = None
    start_time = time.time()
    
    try:
        logger.info(f"Starting embedding and indexing for {len(documents)} documents in collection '{collection_name}'")
        
        # Initialize Qdrant client
        client_args = {"url": QDRANT_HOST, "prefer_grpc": True}
        if QDRANT_API_KEY:
            client_args["api_key"] = QDRANT_API_KEY
        
        qdrant_client = QdrantClient(**client_args)
        
        # Set the FastEmbed model for this client instance
        qdrant_client.set_model(EMBEDDING_MODEL_NAME)
        logger.info(f"Connected to Qdrant at {QDRANT_HOST} with embedding model: {EMBEDDING_MODEL_NAME}")
        
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
