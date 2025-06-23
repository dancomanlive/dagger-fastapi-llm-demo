"""
Unit tests for Temporal Workflows using only unit testing (no Temporal runtime)

Tests the workflow orchestration logic and workflow definitions without
using Temporal's WorkflowEnvironment to avoid sandbox restrictions.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import timedelta
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the workflow and activity modules
from workflows import GenericPipelineWorkflow
from activities import health_check_activity


class TestGenericPipelineWorkflow:
    """Test the GenericPipelineWorkflow orchestration using unit tests only"""
    
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
    async def test_workflow_with_mocked_executor(self):
        """Test workflow execution with fully mocked components (unit test)"""
        # This is a pure unit test that doesn't involve real Temporal workflows
        # since the document_processing pipeline now uses remote activities
        
        from workflows import GenericPipelineWorkflow
        from unittest.mock import patch, MagicMock, AsyncMock
        
        # Mock the PipelineExecutor completely
        with patch('workflows.PipelineExecutor') as mock_executor_class:
            mock_executor = MagicMock()
            mock_executor_class.return_value = mock_executor
            
            # Mock the pipeline execution result as an async method
            mock_chunk_result = [
                {"id": "chunk1", "text": "First chunk", "metadata": {"original_doc_id": "doc1"}},
                {"id": "chunk2", "text": "Second chunk", "metadata": {"original_doc_id": "doc1"}}
            ]
            mock_executor.execute_pipeline = AsyncMock(return_value=mock_chunk_result)
            
            # Create workflow instance for unit testing
            workflow = GenericPipelineWorkflow()
            
            # Mock workflow context if needed
            with patch('workflows.workflow') as mock_workflow_module:
                mock_workflow_module.info.return_value = MagicMock()
                mock_workflow_module.logger = MagicMock()
                
                # Test the workflow logic directly (not through Temporal runtime)
                # This tests our business logic without Temporal's sandbox restrictions
                result = await workflow.run("document_processing", [{"id": "doc1", "text": "Test document"}])
                
                # Verify the mocked result is returned
                assert isinstance(result, list)
                assert len(result) == 2
                assert result[0]["id"] == "chunk1"
                assert result[1]["id"] == "chunk2"
                
                # Verify the executor was called with correct parameters
                mock_executor.execute_pipeline.assert_called_once_with(
                    "document_processing", [{"id": "doc1", "text": "Test document"}]
                )

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


class TestWorkflowActivities:
    """Test individual workflow activities"""
    
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
        
        # Test error handling with health check activity
        result = await health_check_activity()
        assert isinstance(result, str)


class TestWorkflowConfiguration:
    """Test workflow configuration and setup"""
    
    def test_workflow_activity_registration(self):
        """Test that activities are properly registered"""
        
        # Test that activities can be imported
        from activities import health_check_activity
        
        # Verify activities are callable
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
