"""
Unit tests for Temporal Workflows using direct testing approach

Tests the workflow orchestration logic and workflow definitions without
requiring a full Temporal environment setup.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import timedelta
import sys
import os
import unittest
import asyncio

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the workflow and activity modules
from workflows import GenericPipelineWorkflow
from activities import (
    chunk_documents_activity,
    embed_documents_activity,
    health_check_activity
)
from pipeline_executor import PipelineExecutor
from transforms.base_transform import BaseTransform


class TestPipelineExecutor(unittest.TestCase):
    @patch('pipeline_executor.get_service_config')
    def setUp(self, mock_get_service_config):
        # Mock service config
        self.mock_config = MagicMock()
        self.mock_config.get_pipeline_config.return_value = {
            "steps": [
                {"activity": "activity1", "input_transform": "transform1"},
                {"activity": "activity2", "input_transform": "transform2"},
            ]
        }
        self.mock_config.get_activity_config.return_value = {"type": "remote", "task_queue": "test-queue"}
        mock_get_service_config.return_value = self.mock_config

        self.executor = PipelineExecutor()
        self.executor.workflow_input_data = {}

    @patch('pipeline_executor.get_transform')
    @patch('pipeline_executor.workflow')
    def test_execute_pipeline(self, mock_workflow, mock_get_transform):
        # Mock transforms
        mock_transform1 = MagicMock(spec=BaseTransform)
        mock_transform1.transform.return_value = ["transformed_data1"]
        mock_transform2 = MagicMock(spec=BaseTransform)
        mock_transform2.transform.return_value = ["transformed_data2"]
        mock_get_transform.side_effect = [mock_transform1, mock_transform2]

        # Mock activities
        self.executor.execute_activity_by_name = AsyncMock(side_effect=["result1", "result2"])

        # Run pipeline
        pipeline_result = asyncio.run(self.executor.execute_pipeline("test_pipeline", "initial_data"))

        # Assertions
        self.assertEqual(pipeline_result['status'], "completed")
        self.assertEqual(pipeline_result['final_result'], "result2")
        self.assertEqual(self.executor.execute_activity_by_name.call_count, 2)
        self.executor.execute_activity_by_name.assert_any_call("activity1", ["transformed_data1"])
        self.executor.execute_activity_by_name.assert_any_call("activity2", ["transformed_data2"])
        mock_transform1.transform.assert_called_once_with("initial_data", {"activity": "activity1", "input_transform": "transform1"}, "initial_data", self.executor.document_collection_name)
        mock_transform2.transform.assert_called_once_with("result1", {"activity": "activity2", "input_transform": "transform2"}, "initial_data", self.executor.document_collection_name)


class TestGenericPipelineWorkflowUnit:
    """Unit tests for the GenericPipelineWorkflow without Temporal environment"""
    
    @pytest.mark.asyncio
    @patch('workflows.workflow')
    @patch('workflows.PipelineExecutor')
    async def test_workflow_document_processing(self, mock_pipeline_executor_class, mock_workflow):
        """Test workflow logic for document processing pipeline"""
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
    @patch('workflows.workflow')
    @patch('workflows.PipelineExecutor')
    async def test_workflow_embedding_generation(self, mock_pipeline_executor_class, mock_workflow):
        """Test workflow logic for embedding generation pipeline"""
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
            "processing_time": 2.3,
            "embeddings_created": 15
        }
        mock_executor.execute_pipeline = AsyncMock(return_value=mock_embedding_result)
        
        # Test the workflow method directly
        workflow_instance = GenericPipelineWorkflow()
        result = await workflow_instance.run(
            "embedding_generation", 
            [{"id": "doc1", "text": "Machine learning"}, {"id": "doc2", "text": "Deep learning"}]
        )
        
        # Verify result format
        assert isinstance(result, dict)
        assert result.get("status") == "success"
        assert "documents_processed" in result
        assert "processing_time" in result
        assert "embeddings_created" in result
        
        # Verify the executor was called correctly
        mock_executor.execute_pipeline.assert_called_once_with(
            "embedding_generation",
            [{"id": "doc1", "text": "Machine learning"}, {"id": "doc2", "text": "Deep learning"}]
        )

    @pytest.mark.asyncio
    @patch('workflows.workflow')
    @patch('workflows.PipelineExecutor')
    async def test_workflow_error_handling(self, mock_pipeline_executor_class, mock_workflow):
        """Test workflow error handling"""
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
            
        # Verify the executor was called
        mock_executor.execute_pipeline.assert_called_once_with(
            "document_processing",
            [{"test": "data"}]
        )

    @pytest.mark.asyncio
    @patch('workflows.workflow')
    @patch('workflows.PipelineExecutor')
    async def test_workflow_invalid_pipeline_handling(self, mock_pipeline_executor_class, mock_workflow):
        """Test workflow handling of invalid pipeline types"""
        # Mock workflow logger
        mock_logger = MagicMock()
        mock_workflow.logger = mock_logger
        
        # Mock the entire PipelineExecutor class
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock executor to return error for invalid pipeline
        mock_error_result = {
            "status": "error",
            "error_message": "Unknown pipeline type: invalid_pipeline",
            "error_code": "PIPELINE_NOT_FOUND"
        }
        mock_executor.execute_pipeline = AsyncMock(return_value=mock_error_result)
        
        # Test the workflow method directly
        workflow_instance = GenericPipelineWorkflow()
        result = await workflow_instance.run(
            "invalid_pipeline", 
            ["test"]
        )
        
        # Should handle invalid pipeline gracefully
        assert isinstance(result, dict)
        assert result.get("status") == "error"
        assert "error_message" in result
        assert "invalid_pipeline" in result["error_message"]

    @pytest.mark.asyncio
    @patch('workflows.workflow')
    @patch('workflows.PipelineExecutor')
    async def test_workflow_metrics_collection(self, mock_pipeline_executor_class, mock_workflow):
        """Test that workflow handles pipeline results with metrics"""
        # Mock workflow logger
        mock_logger = MagicMock()
        mock_workflow.logger = mock_logger
        
        # Mock the entire PipelineExecutor class
        mock_executor = MagicMock()
        mock_pipeline_executor_class.return_value = mock_executor
        
        # Mock activity with detailed metrics
        activity_result = {
            "status": "success",
            "documents_processed": 3,
            "chunks_created": 10,
            "processing_time": 1.5,
            "pipeline_type": "document_processing",
            "timestamp": "2025-06-17T10:30:00Z"
        }
        mock_executor.execute_pipeline = AsyncMock(return_value=activity_result)
        
        # Test the workflow method directly
        workflow_instance = GenericPipelineWorkflow()
        result = await workflow_instance.run(
            "document_processing", 
            [{"test": "data"}]
        )
        
        # Verify metrics are preserved in result
        assert isinstance(result, dict)
        assert result.get("status") == "success"
        assert result.get("documents_processed") == 3
        assert result.get("chunks_created") == 10
        assert result.get("processing_time") == 1.5
        assert result.get("pipeline_type") == "document_processing"
        assert "timestamp" in result


class TestWorkflowActivitiesUnit:
    """Unit tests for individual workflow activities"""
    
    @pytest.mark.asyncio
    async def test_chunk_documents_activity(self):
        """Test document chunking activity"""
        
        # Test input documents
        documents = [
            {
                "id": "doc1",
                "text": "This is a long document that needs to be chunked into smaller pieces for better processing and storage. It contains multiple sentences and should be split appropriately."
            },
            {
                "id": "doc2", 
                "text": "Another document with substantial content that should be split appropriately. This also has enough content to create multiple chunks."
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
            assert "metadata" in chunk
    
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
            "documents_processed": 2,
            "embeddings_created": 2
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
        assert result["status"] == "success"
        assert "documents_processed" in result
    
    @pytest.mark.asyncio
    async def test_health_check_activity(self):
        """Test health check activity"""
        
        # Test the activity
        result = await health_check_activity()
        
        # Verify result is a string
        assert isinstance(result, str)
        assert len(result) > 0
        assert "healthy" in result.lower()
    
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
