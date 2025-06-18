"""
Temporal activities for document processing pipeline.
"""

import logging
import os
import re
import httpx
import uuid
from typing import List, Dict, Any
from temporalio import activity

# Get the document collection name from environment variable
DOCUMENT_COLLECTION_NAME = os.environ.get("DOCUMENT_COLLECTION_NAME", "document_chunks")

logger = logging.getLogger(__name__)

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
async def embed_documents_activity(documents: List[Dict[str, Any]], embedding_service_url: str) -> Dict[str, Any]:
    """
    Send documents to the embedding service for vectorization and storage.
    
    Args:
        documents: List of chunked documents
        embedding_service_url: URL of the embedding service
    
    Returns:
        Result from embedding service
    """
    logger.info(f"Embedding {len(documents)} document chunks")
    
    async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for large batches
        try:
            # Prepare the request payload to match embedding service API
            request_data = {
                "collection": DOCUMENT_COLLECTION_NAME,  # Use environment variable for collection name
                "documents": documents,
                "create_collection": True
            }
            
            # Send request to embedding service
            response = await client.post(
                f"{embedding_service_url}/index",
                json=request_data
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Successfully embedded {len(documents)} documents")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while embedding documents: {e}")
            raise Exception(f"Embedding service error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while embedding documents: {e}")
            raise Exception(f"Embedding error: {str(e)}")


@activity.defn
async def health_check_activity(input_data: Any = None) -> str:
    """Simple health check activity."""
    return "Activity worker is healthy"
