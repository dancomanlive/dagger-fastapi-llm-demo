"""
Temporal workflows for document processing pipeline.

This module contains orchestration workflows that coordinate activities
across distributed services using Temporal's workflow engine.

Workflows:
- DocumentProcessingWorkflow: Handles document chunking and embedding
- RetrievalWorkflow: Handles document search and retrieval  
- HealthCheckWorkflow: Simple health check workflow
"""

import logging
import os
from datetime import timedelta
from typing import List, Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities through sandbox
with workflow.unsafe.imports_passed_through():
    from activities import chunk_documents_activity, health_check_activity
    # Note: embed_documents_activity removed - now using Temporal activity instead

# Configuration for distributed services
EMBEDDING_SERVICE_TASK_QUEUE = "embedding-task-queue"
RETRIEVAL_SERVICE_TASK_QUEUE = "retrieval-task-queue"
DOCUMENT_COLLECTION_NAME = os.environ.get("DOCUMENT_COLLECTION_NAME", "document_chunks")

# Configuration for the retrieval service
RETRIEVAL_SERVICE_TASK_QUEUE = "retrieval-task-queue"

logger = logging.getLogger(__name__)

@workflow.defn
class DocumentProcessingWorkflow:
    """
    Workflow that processes documents through chunking and embedding steps.
    """
    
    @workflow.run
    async def run(self, documents: List[Dict[str, Any]], embedding_service_url: str | None = None) -> Dict[str, Any]:
        """
        Process documents through the pipeline.
        
        Args:
            documents: List of documents to process
            embedding_service_url: DEPRECATED - No longer used. Embedding is done via Temporal activities.
            
        Returns:
            Processing result summary
        """
        workflow.logger.info(f"Starting document processing workflow for {len(documents)} documents")
        
        if embedding_service_url:
            workflow.logger.warning("embedding_service_url parameter is deprecated and ignored. Using Temporal activities instead.")
        
        try:
            # Step 1: Chunk documents into paragraphs
            workflow.logger.info("Step 1: Chunking documents")
            chunked_docs = await workflow.execute_activity(
                chunk_documents_activity,
                documents,
                start_to_close_timeout=timedelta(minutes=10),
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3
                )
            )
            
            workflow.logger.info(f"Chunking completed: {len(chunked_docs)} chunks created")
            
            # Step 2: Embed the chunked documents using Temporal activity
            workflow.logger.info("Step 2: Embedding documents via Temporal activity")
            embedding_result = await workflow.execute_activity(
                "perform_embedding_and_indexing_activity",  # Activity name as string
                args=[chunked_docs, DOCUMENT_COLLECTION_NAME],  # Documents and collection name
                task_queue=EMBEDDING_SERVICE_TASK_QUEUE,  # Target the embedding service worker
                start_to_close_timeout=timedelta(minutes=30),  # Longer timeout for embedding
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=2),
                    maximum_interval=timedelta(minutes=1),
                    maximum_attempts=3
                )
            )
            
            workflow.logger.info("Embedding completed successfully")
            
            # Return summary
            result = {
                "status": "completed",
                "original_documents": len(documents),
                "chunks_created": len(chunked_docs),
                "embedding_result": embedding_result,
                "workflow_id": workflow.info().workflow_id
            }
            
            workflow.logger.info(f"Workflow completed successfully: {result}")
            return result
            
        except Exception as e:
            workflow.logger.error(f"Workflow failed: {str(e)}")
            raise


@workflow.defn
class HealthCheckWorkflow:
    """Simple health check workflow."""
    
    @workflow.run
    async def run(self) -> str:
        """Run health check."""
        return await workflow.execute_activity(
            health_check_activity,
            start_to_close_timeout=timedelta(seconds=30)
        )


# Configuration for the retrieval service
RETRIEVAL_SERVICE_TASK_QUEUE = "retrieval-task-queue"

@workflow.defn
class RetrievalWorkflow:
    """
    Workflow that performs document search and retrieval.
    """
    
    @workflow.run
    async def run(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Search for documents based on query using distributed retrieval service.
        
        Args:
            query: Search query string
            top_k: Number of top results to return (default: 10)
            
        Returns:
            Dict containing:
            - status: Workflow completion status
            - query: Original search query
            - top_k: Number of results requested
            - search_result: Results from retrieval service
            - workflow_id: Unique workflow identifier
            
        Raises:
            Exception: If retrieval activity fails
        """
        workflow.logger.info(f"Starting retrieval workflow for query: {query}")
        
        try:
            # Step 1: Search documents using Temporal activity
            workflow.logger.info("Searching documents via Temporal activity")
            search_result = await workflow.execute_activity(
                "search_documents_activity",  # Activity name as string
                args=[query, DOCUMENT_COLLECTION_NAME, top_k],  # Query, collection_name, and top_k parameters
                task_queue=RETRIEVAL_SERVICE_TASK_QUEUE,  # Target the retrieval service worker
                start_to_close_timeout=timedelta(minutes=5),  # Timeout for search
                retry_policy=RetryPolicy(
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30),
                    maximum_attempts=3
                )
            )
            
            workflow.logger.info("Search completed successfully")
            
            # Return result
            result = {
                "status": "completed",
                "query": query,
                "top_k": top_k,
                "search_result": search_result,
                "workflow_id": workflow.info().workflow_id
            }
            
            workflow.logger.info(f"Retrieval workflow completed successfully: {result}")
            return result
            
        except Exception as e:
            workflow.logger.error(f"Retrieval workflow failed: {str(e)}")
            raise
