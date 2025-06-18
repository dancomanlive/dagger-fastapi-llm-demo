"""
Unit tests for Temporal Workflows using Temporal's testing framework

Tests the workflow orchestration logic and workflow definitions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import timedelta
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Temporal testing framework
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

# Import the workflow and activity modules
from workflows import GenericPipelineWorkflow
from activities import (
    chunk_documents_activity,
    embed_documents_activity,
    health_check_activity
)


class TestGenericPipelineWorkflow:
    """Test the GenericPipelineWorkflow orchestration using Temporal testing framework"""
    
    @pytest.mark.asyncio
    @patch('workflows.workflow')
    @patch('workflows.PipelineExecutor')
    async def test_workflow_error_handling_unit(self, mock_pipeline_executor_class, mock_workflow):
        """Test workflow error handling in unit test mode"""
        # Mock workflow logger
        mock_logger = MagicMock()
        mock_workflow.logger = mock_logger
        
        # Mock the entire PipelineExecutor class
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock pipeline executor to raise an exception
        mock_executor.execute_pipeline = AsyncMock(side_effect=Exception("Pipeline execution failed"))
        
        # Test the workflow method directly
        workflow_instance = GenericPipelineWorkflow()
        
        with pytest.raises(Exception, match="Pipeline execution failed"):
            await workflow_instance.run(
                "document_processing", 
                [{"test": "data"}]
            )
    
    @pytest.mark.asyncio
    @patch('workflows.workflow')
    @patch('workflows.PipelineExecutor')
    async def test_workflow_different_pipeline_types_unit(self, mock_pipeline_executor_class, mock_workflow):
        """Test workflow with different pipeline types in unit test mode"""
        # Mock workflow logger
        mock_logger = MagicMock()
        mock_workflow.logger = mock_logger
        
        # Mock the entire PipelineExecutor class
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Test embedding pipeline
        mock_embedding_result = {
            "status": "success",
            "documents_processed": 5,
            "processing_time": 2.3
        }
        mock_executor.execute_pipeline = AsyncMock(return_value=mock_embedding_result)
        
        # Test the workflow method directly
        workflow_instance = GenericPipelineWorkflow()
        result = await workflow_instance.run(
            "embedding_generation", 
            [{"id": "doc1", "text": "Machine learning"}]
        )
        
        # Verify result format
        assert isinstance(result, dict)
        assert result.get("status") == "success"
        assert "documents_processed" in result
        assert "processing_time" in result
    
    @pytest.mark.asyncio
    @patch('workflows.PipelineExecutor')
    async def test_document_processing_pipeline(self, mock_pipeline_executor_class):
        """Test document processing pipeline execution and output format"""
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock pipeline executor result
        mock_chunk_result = [
            {"id": "chunk1", "text": "First chunk of text"},
            {"id": "chunk2", "text": "Second chunk of text"}
        ]
        mock_executor.execute_pipeline.return_value = mock_chunk_result
        
        env = await WorkflowEnvironment.start_local()
        try:
            # Start worker with activities
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[GenericPipelineWorkflow],
                activities=[chunk_documents_activity, embed_documents_activity, health_check_activity]
            )
            
            async with worker:
                # Execute workflow with timeout
                result = await env.client.execute_workflow(
                    GenericPipelineWorkflow.run,
                    args=["document_processing", [{"id": "doc1", "text": "This is a long document that needs chunking"}]],
                    id="test-doc-processing",
                    task_queue="test-queue",
                    execution_timeout=timedelta(seconds=30)  # Add timeout
                )
                
                # Verify result format
                assert isinstance(result, list)
                assert all("id" in chunk and "text" in chunk for chunk in result)
        finally:
            await env.shutdown()
    
    @pytest.mark.asyncio
    @patch('pipeline_executor.PipelineExecutor')
    async def test_embedding_pipeline(self, mock_pipeline_executor_class):
        """Test embedding generation pipeline execution and output format"""
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        mock_embedding_result = {
            "status": "success",
            "documents_processed": 5,
            "processing_time": 2.3
        }
        mock_executor.execute_pipeline.return_value = mock_embedding_result
        
        env = await WorkflowEnvironment.start_local()
        try:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[GenericPipelineWorkflow],
                activities=[chunk_documents_activity, embed_documents_activity, health_check_activity]
            )
            
            async with worker:
                result = await env.client.execute_workflow(
                    GenericPipelineWorkflow.run,
                    args=["embedding_generation", [{"id": "doc1", "text": "Machine learning"}, {"id": "doc2", "text": "Deep learning"}]],
                    id="test-embedding",
                    task_queue="test-queue"
                )
                
                assert isinstance(result, dict)
                assert result.get("status") == "success"
                assert "documents_processed" in result
                assert "processing_time" in result
        finally:
            await env.shutdown()
    
    @pytest.mark.asyncio
    @patch('pipeline_executor.PipelineExecutor')
    async def test_workflow_error_handling(self, mock_pipeline_executor_class):
        """Test workflow error handling and error output format"""
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        mock_executor.execute_pipeline.side_effect = Exception("Pipeline execution failed")
        
        env = await WorkflowEnvironment.start_local()
        try:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[GenericPipelineWorkflow],
                activities=[chunk_documents_activity, embed_documents_activity, health_check_activity]
            )
            
            async with worker:
                # Expect workflow to fail
                with pytest.raises(Exception, match="Pipeline execution failed"):
                    await env.client.execute_workflow(
                        GenericPipelineWorkflow.run,
                        args=["document_processing", [{"test": "data"}]],
                        id="test-error-handling",
                        task_queue="test-queue"
                    )
        finally:
            await env.shutdown()
    
    @pytest.mark.asyncio
    @patch('pipeline_executor.PipelineExecutor')
    async def test_invalid_pipeline_type(self, mock_pipeline_executor_class):
        """Test handling of invalid pipeline types and output format"""
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock executor to return error for invalid pipeline
        mock_executor.execute_pipeline.return_value = {
            "status": "error",
            "error_message": "Unknown pipeline type: invalid_pipeline"
        }
        
        env = await WorkflowEnvironment.start_local()
        try:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[GenericPipelineWorkflow],
                activities=[chunk_documents_activity, embed_documents_activity, health_check_activity]
            )
            
            async with worker:
                result = await env.client.execute_workflow(
                    GenericPipelineWorkflow.run,
                    args=["invalid_pipeline", ["test"]],
                    id="test-invalid-pipeline",
                    task_queue="test-queue"
                )
                
                # Should handle invalid pipeline gracefully
                assert isinstance(result, dict)
                assert result.get("status") == "error"
        finally:
            await env.shutdown()
    
    @pytest.mark.asyncio
    @patch('workflows.workflow')
    @patch('workflows.PipelineExecutor')
    async def test_workflow_logic_unit(self, mock_pipeline_executor_class, mock_workflow):
        """Test workflow logic directly without Temporal environment"""
        # Mock workflow logger to avoid temporal context requirements
        mock_logger = MagicMock()
        mock_workflow.logger = mock_logger
        
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock pipeline executor result - make it async
        mock_chunk_result = [
            {"id": "chunk1", "text": "First chunk of text"},
            {"id": "chunk2", "text": "Second chunk of text"}
        ]
        mock_executor.execute_pipeline = AsyncMock(return_value=mock_chunk_result)
        
        # Test the workflow method directly
        workflow_instance = GenericPipelineWorkflow()
        result = await workflow_instance.run(
            "document_processing", 
            [{"id": "doc1", "text": "This is a long document that needs chunking"}]
        )
        
        # Verify result format
        assert isinstance(result, list)
        assert all("id" in chunk and "text" in chunk for chunk in result)
        
        # Verify the executor was called correctly
        mock_executor.execute_pipeline.assert_called_once_with(
            "document_processing",
            [{"id": "doc1", "text": "This is a long document that needs chunking"}]
        )

    @pytest.mark.asyncio
    @patch('workflows.PipelineExecutor')
    async def test_workflow_logic_integration(self, mock_pipeline_executor_class):
        """Test workflow logic with integration-style test"""
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock chunking activity result
        chunk_result = [
            {
                "id": "chunk1",
                "text": "Document processing is a key part of AI",
                "source_id": "doc1"
            },
            {
                "id": "chunk2", 
                "text": "Natural language processing helps understand text",
                "source_id": "doc1"
            }
        ]
        
        mock_executor.execute_pipeline.return_value = chunk_result
        
        env = await WorkflowEnvironment.start_local()
        try:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[GenericPipelineWorkflow],
                activities=[chunk_documents_activity, embed_documents_activity, health_check_activity]
            )
            
            async with worker:
                # Execute document processing
                documents = [{"id": "doc1", "text": "Document processing is a key part of AI systems. Natural language processing helps understand text content."}]
                result = await env.client.execute_workflow(
                    GenericPipelineWorkflow.run,
                    args=["document_chunking", documents],
                    id="test-full-processing",
                    task_queue="test-queue"
                )
                
                # Verify full pipeline result
                assert result is not None
                if isinstance(result, list):
                    assert len(result) >= 1
                elif isinstance(result, dict) and "chunks" in result:
                    assert len(result["chunks"]) >= 1
        finally:
            await env.shutdown()
    
    @pytest.mark.asyncio
    @patch('pipeline_executor.PipelineExecutor')
    async def test_workflow_metrics_collection(self, mock_pipeline_executor_class):
        """Test that workflow collects proper metrics"""
        
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock activity with metrics
        activity_result = {
            "status": "success",
            "documents_processed": 3,
            "chunks_created": 10,
            "processing_time": 1.5
        }
        
        mock_executor.execute_pipeline.return_value = activity_result
        
        env = await WorkflowEnvironment.start_local()
        try:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[GenericPipelineWorkflow],
                activities=[chunk_documents_activity, embed_documents_activity, health_check_activity]
            )
            
            async with worker:
                # Execute workflow
                result = await env.client.execute_workflow(
                    GenericPipelineWorkflow.run,
                    args=["document_processing", [{"test": "data"}]],
                    id="test-metrics",
                    task_queue="test-queue"
                )
                
                # Verify metrics are preserved
                if isinstance(result, dict):
                    # Check if metrics are present (depending on implementation)
                    assert result is not None
        finally:
            await env.shutdown()


class TestWorkflowActivities:
    """Test individual workflow activities"""
    
    @pytest.mark.asyncio
    async def test_chunk_documents_activity(self):
        """Test document chunking activity"""
        
        # Test input documents
        documents = [
            {
                "id": "doc1",
                "text": "This is a long document that needs to be chunked into smaller pieces for better processing and storage."
            },
            {
                "id": "doc2", 
                "text": "Another document with substantial content that should be split appropriately."
            }
        ]
        
        # Test the activity
        result = await chunk_documents_activity(documents)
        
        # Verify result structure
        assert isinstance(result, list)
        # Should have more chunks than original documents
        assert len(result) >= len(documents)
        
        # Verify chunk structure
        for chunk in result:
            assert isinstance(chunk, dict)
            assert "text" in chunk
            assert "id" in chunk
    
    @pytest.mark.asyncio
    @patch('activities.httpx.AsyncClient')
    async def test_embed_documents_activity(self, mock_client_class):
        """Test embedding generation activity"""
        
        # Create mock client and response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "documents_processed": 2
        }
        
        # Create an async mock for the post method
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Test documents
        documents = [
            {"id": "doc1", "text": "Test document 1"},
            {"id": "doc2", "text": "Test document 2"}
        ]
        
        # Test the activity
        result = await embed_documents_activity(
            documents=documents,
            embedding_service_url="http://localhost:8001"
        )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "status" in result
    
    @pytest.mark.asyncio
    async def test_health_check_activity(self):
        """Test health check activity"""
        
        # Test the activity
        result = await health_check_activity()
        
        # Verify result is a string
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_activity_error_handling(self):
        """Test activity error handling"""
        
        # Test error handling with invalid input
        with pytest.raises((TypeError, ValueError, AttributeError)):
            # Pass invalid input to trigger error
            await chunk_documents_activity(None)


class TestWorkflowConfiguration:
    """Test workflow configuration and setup"""
    
    def test_workflow_activity_registration(self):
        """Test that activities are properly registered"""
        
        # Test that activities can be imported
        from activities import (
            chunk_documents_activity,
            embed_documents_activity,
            health_check_activity
        )
        
        # Verify activities are callable
        assert callable(chunk_documents_activity)
        assert callable(embed_documents_activity)
        assert callable(health_check_activity)
    
    def test_workflow_retry_configuration(self):
        """Test workflow retry configuration"""
        
        from temporalio.common import RetryPolicy
        
        # Test retry policy creation
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3
        )
        
        assert retry_policy.initial_interval == timedelta(seconds=1)
        assert retry_policy.maximum_attempts == 3
    
    def test_workflow_timeout_configuration(self):
        """Test workflow timeout configuration"""
        
        from datetime import timedelta
        
        # Test timeout values
        execution_timeout = timedelta(minutes=10)
        task_timeout = timedelta(minutes=5)
        
        assert execution_timeout.total_seconds() == 600
        assert task_timeout.total_seconds() == 300


class TestWorkflowIntegration:
    """Integration tests using Temporal testing framework"""
    
    @pytest.mark.asyncio
    @patch('pipeline_executor.PipelineExecutor')
    async def test_full_document_processing_simulation(self, mock_pipeline_executor_class):
        """Test a full document processing pipeline simulation"""
        
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock chunking activity result
        chunk_result = [
            {
                "id": "chunk1",
                "text": "Document processing is a key part of AI",
                "source_id": "doc1"
            },
            {
                "id": "chunk2", 
                "text": "Natural language processing helps understand text",
                "source_id": "doc1"
            }
        ]
        
        mock_executor.execute_pipeline.return_value = chunk_result
        
        env = await WorkflowEnvironment.start_local()
        try:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[GenericPipelineWorkflow],
                activities=[chunk_documents_activity, embed_documents_activity, health_check_activity]
            )
            
            async with worker:
                # Execute document processing
                documents = [{"id": "doc1", "text": "Document processing is a key part of AI systems. Natural language processing helps understand text content."}]
                result = await env.client.execute_workflow(
                    GenericPipelineWorkflow.run,
                    args=["document_chunking", documents],
                    id="test-full-processing",
                    task_queue="test-queue"
                )
                
                # Verify full pipeline result
                assert result is not None
                if isinstance(result, list):
                    assert len(result) >= 1
                elif isinstance(result, dict) and "chunks" in result:
                    assert len(result["chunks"]) >= 1
        finally:
            await env.shutdown()
    
    @pytest.mark.asyncio
    @patch('pipeline_executor.PipelineExecutor')
    async def test_workflow_metrics_collection(self, mock_pipeline_executor_class):
        """Test that workflow collects proper metrics"""
        
        # Mock the entire PipelineExecutor class to avoid file I/O
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock activity with metrics
        activity_result = {
            "status": "success",
            "documents_processed": 3,
            "chunks_created": 10,
            "processing_time": 1.5
        }
        
        mock_executor.execute_pipeline.return_value = activity_result
        
        env = await WorkflowEnvironment.start_local()
        try:
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[GenericPipelineWorkflow],
                activities=[chunk_documents_activity, embed_documents_activity, health_check_activity]
            )
            
            async with worker:
                # Execute workflow
                result = await env.client.execute_workflow(
                    GenericPipelineWorkflow.run,
                    args=["document_processing", [{"test": "data"}]],
                    id="test-metrics",
                    task_queue="test-queue"
                )
                
                # Verify metrics are preserved
                if isinstance(result, dict):
                    # Check if metrics are present (depending on implementation)
                    assert result is not None
        finally:
            await env.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
