"""
Temporal workflows for document processing pipeline.
"""

import logging
from datetime import timedelta
from typing import List, Dict, Any
from temporalio import workflow
from temporalio.common import RetryPolicy

# Import activities through sandbox
with workflow.unsafe.imports_passed_through():
    from activities import chunk_documents_activity, embed_documents_activity, health_check_activity

logger = logging.getLogger(__name__)

@workflow.defn
class DocumentProcessingWorkflow:
    """
    Workflow that processes documents through chunking and embedding steps.
    """
    
    @workflow.run
    async def run(self, documents: List[Dict[str, Any]], embedding_service_url: str) -> Dict[str, Any]:
        """
        Process documents through the pipeline.
        
        Args:
            documents: List of documents to process
            embedding_service_url: URL of the embedding service
            
        Returns:
            Processing result summary
        """
        workflow.logger.info(f"Starting document processing workflow for {len(documents)} documents")
        
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
            
            # Step 2: Embed the chunked documents
            workflow.logger.info("Step 2: Embedding documents")
            embedding_result = await workflow.execute_activity(
                embed_documents_activity,
                args=[chunked_docs, embedding_service_url],
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
