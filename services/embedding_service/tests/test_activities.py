"""
Test for embedding activity interface - Phase 1, Step 1.1 of TDD refactoring.

This test follows the RED-GREEN-REFACTOR cycle:
1. RED: Test imports and basic structure (will fail initially)
2. GREEN: Create minimal implementation to make test pass
3. REFACTOR: Clean up implementation
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio # Mark test as async
async def test_perform_embedding_and_indexing_activity_structure(sample_documents, sample_collection_name):
    """
    Test that perform_embedding_and_indexing_activity can be imported and called.
    
    This is the RED phase - the test will fail because:
    1. activities.py doesn't exist yet
    2. perform_embedding_and_indexing_activity function doesn't exist
    
    According to the refactoring plan, this test should:
    - Try to import perform_embedding_and_indexing_activity from activities.py
    - Define sample input documents and collection name (using fixtures)
    - Assert that the activity would be callable with these arguments
    """
    # Import at module level to ensure clean import behavior
    from activities import perform_embedding_and_indexing_activity
    
    # Test that the function exists and is callable
    assert callable(perform_embedding_and_indexing_activity)
    
    # Test that we can call it with the expected signature
    # For now, we just test that it accepts the right arguments
    # We don't test the actual logic yet - that's for Step 1.2
    with patch('activities.QdrantClient') as MockQdrantClient, \
         patch('activities.time') as mock_time:
        
        # Setup minimal mocks to avoid actual network calls
        mock_qdrant_client = Mock()
        MockQdrantClient.return_value = mock_qdrant_client
        mock_time.time.return_value = 12345.0
        
        try:
            # Call with sample data - we just want to verify the signature is correct
            result = await perform_embedding_and_indexing_activity(
                documents=sample_documents,
                collection_name=sample_collection_name
            )
            # At this stage, we don't care about the exact return value
            # We just want to ensure the function signature is correct and it returns something
            assert result is not None
            assert True  # If we get here, the function signature is correct
        except TypeError as e:
            # If we get a TypeError, it means the function signature is wrong
            pytest.fail(f"Function signature is incorrect: {e}")


@pytest.mark.unit
@pytest.mark.asyncio # Mark test as async
async def test_perform_embedding_and_indexing_activity_logic(sample_documents, sample_collection_name):
    """
    Test the core logic of perform_embedding_and_indexing_activity.
    
    This is Step 1.2 - testing the actual embedding and indexing logic.
    According to the refactoring plan, this test should:
    - Mock QdrantClient and its methods (add)
    - Provide sample documents
    - Call perform_embedding_and_indexing_activity
    - Assert that Qdrant client add method is called with expected arguments
    - Assert the activity returns expected success structure
    """
    from activities import perform_embedding_and_indexing_activity, PAYLOAD_TEXT_FIELD_NAME
    
    # Mock QdrantClient and its methods
    mock_qdrant_client = Mock()
    mock_qdrant_client.add.return_value = None  # Qdrant add method doesn't return anything meaningful
    mock_qdrant_client.close.return_value = None
    
    # Prepare expected data for qdrant_client.add()
    expected_docs_to_add = [doc['text'] for doc in sample_documents]
    expected_ids_to_add = [doc['id'] for doc in sample_documents]
    
    with patch('activities.QdrantClient') as MockQdrantClient, \
         patch('activities.time') as mock_time: # Mock time to control timestamp
        
        # Setup mocks
        MockQdrantClient.return_value = mock_qdrant_client
        # Need to provide enough time values: start_time, indexed_at (per doc), elapsed_time calc, final timestamp
        # For 3 documents: start + 3 * indexed_at + elapsed + final = 6 calls minimum
        mock_time.time.side_effect = [12345.6789, 12346.0000, 12346.0000, 12346.0000, 12346.1000, 12346.1000]
        
        # Call the activity and await it
        result = await perform_embedding_and_indexing_activity(
            documents=sample_documents,
            collection_name=sample_collection_name
        )
        
        # Assert QdrantClient was initialized correctly
        MockQdrantClient.assert_called_once()
        call_kwargs = MockQdrantClient.call_args[1]
        assert 'url' in call_kwargs
        assert 'prefer_grpc' in call_kwargs
        assert call_kwargs['prefer_grpc'] is True

        # Assert qdrant_client.add was called correctly
        mock_qdrant_client.add.assert_called_once()
        call_args = mock_qdrant_client.add.call_args
        
        assert call_args[1]['collection_name'] == sample_collection_name
        assert call_args[1]['documents'] == expected_docs_to_add
        assert call_args[1]['ids'] == expected_ids_to_add
        
        # Check metadata structure for each document
        actual_metadata_list = call_args[1]['metadata']
        assert len(actual_metadata_list) == len(sample_documents)
        for i, doc in enumerate(sample_documents):
            expected_metadata = {
                PAYLOAD_TEXT_FIELD_NAME: doc['text'],
                'id': doc['id'],
                'indexed_at': 12346.0000 # from mock_time calls during metadata creation
            }
            assert actual_metadata_list[i] == expected_metadata
            
        # Assert the structure of the success response
        assert result["status"] == "success"
        assert result["indexed_count"] == len(sample_documents)
        assert result["collection_name"] == sample_collection_name
        assert "embedding_model" in result 
        assert "elapsed_time" in result
        assert result["timestamp"] == 12346.1000 # from mock_time final call
        
        # Assert client.close() was called
        mock_qdrant_client.close.assert_called_once()
