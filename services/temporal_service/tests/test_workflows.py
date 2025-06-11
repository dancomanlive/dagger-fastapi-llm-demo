"""
Workflow orchestration tests for Temporal service.

These tests focus on workflow-level concerns:
- Activity sequencing and parameter passing
- Task queue routing
- Timeout and retry configuration
- Workflow-level error handling

Individual activity logic is tested in their respective services.
"""

import pytest
from unittest.mock import patch, Mock

# Import the workflows for orchestration testing
from workflows import DocumentProcessingWorkflow

# Task queue configurations for cross-service routing
EMBEDDING_SERVICE_TASK_QUEUE = "embedding-task-queue"
RETRIEVAL_SERVICE_TASK_QUEUE = "retrieval-task-queue"


@pytest.mark.asyncio
async def test_document_processing_workflow_orchestration(sample_documents):
    """
    Test DocumentProcessingWorkflow orchestration:
    - Correct activity sequencing (chunking -> embedding)
    - Proper parameter passing between activities  
    - Task queue routing to correct services
    - Timeout and retry configuration
    """
    
    # Mock the workflow.execute_activity calls
    with patch('workflows.workflow') as mock_workflow_context:
        # Setup workflow info mock
        mock_workflow_info = Mock()
        mock_workflow_info.workflow_id = "test-workflow-123"
        mock_workflow_context.info.return_value = mock_workflow_info
        
        # Setup logger mock
        mock_workflow_context.logger = Mock()
        
        # Define mock outputs (simulating what real activities would return)
        mock_chunked_documents = [
            {"id": "chunk1", "text": "Chunk 1 text", "metadata": {"original_doc_id": "doc1"}},
            {"id": "chunk2", "text": "Chunk 2 text", "metadata": {"original_doc_id": "doc2"}}
        ]
        mock_embedding_result = {
            "status": "success", 
            "indexed_count": len(mock_chunked_documents),
            "collection_name": "document_chunks"
        }

        activity_calls = []
        async def mock_execute_activity(activity_func_or_name, *args, **kwargs):
            # Store the call details for orchestration verification
            call_info = {
                'activity_func_or_name': activity_func_or_name,
                'args': args,
                'kwargs': kwargs
            }
            activity_calls.append(call_info)
            
            # Return different responses based on activity name/function
            if hasattr(activity_func_or_name, '__name__') and activity_func_or_name.__name__ == 'chunk_documents_activity':
                return mock_chunked_documents
            elif activity_func_or_name == "perform_embedding_and_indexing_activity":
                return mock_embedding_result
            return {"status": "mocked_activity_completed"}
        
        mock_workflow_context.execute_activity.side_effect = mock_execute_activity
        
        # Execute the workflow
        workflow_instance = DocumentProcessingWorkflow()
        result = await workflow_instance.run(documents=sample_documents)
        
        # === WORKFLOW ORCHESTRATION VERIFICATION ===
        
        # Verify workflow orchestration result structure
        assert result["status"] == "completed"
        assert result["chunks_created"] == len(mock_chunked_documents)
        assert result["original_documents"] == len(sample_documents)
        assert "workflow_id" in result
        assert "embedding_result" in result
        
        # Verify correct activity sequencing (exactly 2 activities called in order)
        assert len(activity_calls) == 2, f"Expected 2 activities, got {len(activity_calls)}"
        
        # --- CHUNKING ACTIVITY ORCHESTRATION ---
        chunking_call = activity_calls[0]
        
        # Verify chunking activity is called first with correct parameters
        assert hasattr(chunking_call['activity_func_or_name'], '__name__')
        assert chunking_call['activity_func_or_name'].__name__ == 'chunk_documents_activity'
        assert chunking_call['args'][0] == sample_documents
        
        # Verify chunking activity timeout configuration
        assert chunking_call['kwargs'].get('start_to_close_timeout') is not None
        assert chunking_call['kwargs'].get('retry_policy') is not None
        
        # --- EMBEDDING ACTIVITY ORCHESTRATION ---
        embedding_call = activity_calls[1]
        
        # Verify embedding activity is called second as string (cross-service call)
        assert embedding_call['activity_func_or_name'] == "perform_embedding_and_indexing_activity"
        
        # Verify parameter passing: chunked docs from first activity
        assert embedding_call['kwargs']['args'][0] == mock_chunked_documents
        
        # Verify collection name parameter
        collection_name = embedding_call['kwargs']['args'][1]
        assert collection_name in ["document_chunks", "document-chunks"]
        
        # Verify cross-service task queue routing
        assert embedding_call['kwargs'].get('task_queue') == EMBEDDING_SERVICE_TASK_QUEUE
        
        # Verify embedding activity timeout configuration (longer for embedding)
        assert embedding_call['kwargs'].get('start_to_close_timeout') is not None
        assert embedding_call['kwargs'].get('retry_policy') is not None


@pytest.mark.asyncio
async def test_retrieval_workflow_orchestration():
    """
    Test RetrievalWorkflow orchestration:
    - Cross-service activity routing
    - Parameter passing to search activity
    - Task queue configuration for retrieval service
    """
    from workflows import RetrievalWorkflow
    
    # Test data
    sample_query = "test search query"
    sample_top_k = 10
    
    # Mock the workflow.execute_activity calls
    with patch('workflows.workflow') as mock_workflow_context:
        # Setup workflow info mock
        mock_workflow_info = Mock()
        mock_workflow_info.workflow_id = "test-retrieval-workflow-456"
        mock_workflow_context.info.return_value = mock_workflow_info
        
        # Setup logger mock
        mock_workflow_context.logger = Mock()
        
        # Define mock search result (simulating what search activity returns)
        mock_search_result = {
            "status": "success",
            "query": sample_query,
            "results": [
                {"id": "doc1", "text": "Matching document 1", "score": 0.95},
                {"id": "doc2", "text": "Matching document 2", "score": 0.87}
            ]
        }

        activity_calls = []
        async def mock_execute_activity(activity_func_or_name, *args, **kwargs):
            # Store the call details for orchestration verification
            call_info = {
                'activity_func_or_name': activity_func_or_name,
                'args': args,
                'kwargs': kwargs
            }
            activity_calls.append(call_info)
            
            # Return search result for search activity
            if activity_func_or_name == "search_documents_activity":
                return mock_search_result
            return {"status": "mocked_activity_completed"}
        
        mock_workflow_context.execute_activity.side_effect = mock_execute_activity
        
        # Execute the workflow
        workflow_instance = RetrievalWorkflow()
        result = await workflow_instance.run(query=sample_query, top_k=sample_top_k)
        
        # === WORKFLOW ORCHESTRATION VERIFICATION ===
        
        # Verify workflow orchestration result structure
        assert result["status"] == "completed"
        assert result["query"] == sample_query
        assert result["top_k"] == sample_top_k
        assert result["search_result"] == mock_search_result
        assert "workflow_id" in result
        
        # Verify single activity call (retrieval workflows call one search activity)
        assert len(activity_calls) == 1
        
        # --- SEARCH ACTIVITY ORCHESTRATION ---
        search_call = activity_calls[0]
        
        # Verify search activity called as string (cross-service call)
        assert search_call['activity_func_or_name'] == "search_documents_activity"
        
        # Verify parameter passing: query, collection_name, top_k
        assert search_call['kwargs']['args'][0] == sample_query
        
        # Verify collection name parameter (from environment)
        collection_name = search_call['kwargs']['args'][1]
        assert collection_name in ["document_chunks", "document-chunks"]
        
        # Verify top_k parameter
        assert search_call['kwargs']['args'][2] == sample_top_k
        
        # Verify cross-service task queue routing
        assert search_call['kwargs'].get('task_queue') == RETRIEVAL_SERVICE_TASK_QUEUE
        
        # Verify search activity timeout configuration
        assert search_call['kwargs'].get('start_to_close_timeout') is not None
        assert search_call['kwargs'].get('retry_policy') is not None


@pytest.mark.asyncio
async def test_health_check_workflow():
    """
    Test that HealthCheckWorkflow calls health_check_activity correctly.
    """
    # Import here to avoid circular import issues
    from workflows import HealthCheckWorkflow
    from activities import health_check_activity
    
    # Mock the workflow.execute_activity calls
    with patch('workflows.workflow') as mock_workflow_context:
        # Setup logger mock
        mock_workflow_context.logger = Mock()
        
        # Define mock health check result
        mock_health_result = "Activity worker is healthy"

        activity_calls = []
        async def mock_execute_activity(activity_func_or_name, *args, **kwargs):
            # Store the call details
            call_info = {
                'activity_func_or_name': activity_func_or_name,
                'args': args,
                'kwargs': kwargs
            }
            activity_calls.append(call_info)
            
            # Return health check result
            if activity_func_or_name == health_check_activity:
                return mock_health_result
            return "mocked_activity_completed"
        
        mock_workflow_context.execute_activity.side_effect = mock_execute_activity
        
        # Create and run the workflow
        workflow_instance = HealthCheckWorkflow()
        result = await workflow_instance.run()
        
        # Verify the workflow returned the health check result
        assert result == mock_health_result
        
        # Verify that execute_activity was called for health check
        assert len(activity_calls) == 1
        
        # --- Verify health_check_activity call ---
        health_activity_call = activity_calls[0]
        assert health_activity_call['activity_func_or_name'] == health_check_activity
        assert health_activity_call['kwargs'].get('start_to_close_timeout') is not None





