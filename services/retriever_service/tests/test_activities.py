"""
Tests for retriever service Temporal activities.

This module tests the Temporal activities that will be executed by workers
to handle document search and retrieval operations.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestSearchDocumentsActivity:
    """Test suite for the search_documents_activity."""
    
    def test_search_documents_activity_structure(self):
        """
        Test that search_documents_activity can be imported and has correct signature.
        """
        # Import the activity (should succeed now)
        from activities import search_documents_activity
        
        # Test that it's callable
        assert callable(search_documents_activity)
    
    def test_search_documents_activity_signature(self):
        """
        Test that search_documents_activity has the correct function signature.
        """
        # This will also fail initially since the module doesn't exist
        try:
            from activities import search_documents_activity
            
            # Test that it's callable
            assert callable(search_documents_activity)
            
            # Test that it accepts the expected parameters
            # We expect: search_documents_activity(query: str, collection_name: str, top_k: int = 5)
            import inspect
            sig = inspect.signature(search_documents_activity)
            params = list(sig.parameters.keys())
            
            assert 'query' in params
            assert 'collection_name' in params
            assert 'top_k' in params
            
        except ImportError:
            pytest.fail("search_documents_activity not found - needs to be implemented")
    
    @patch('activities.QdrantClient')
    @patch.dict('os.environ', {'PAYLOAD_TEXT_FIELD_NAME': 'document', 'EMBEDDING_MODEL': 'test-model'}, clear=False)
    @pytest.mark.asyncio
    async def test_search_documents_activity_logic(self, mock_qdrant_client_class):
        """
        Test the core logic of search_documents_activity.
        This tests the Qdrant client interaction and result transformation.
        """
        # Skip if activity doesn't exist yet
        try:
            from activities import search_documents_activity, EMBEDDING_MODEL_NAME
        except ImportError:
            pytest.skip("search_documents_activity not implemented yet")
        
        # Setup mock Qdrant client
        mock_client_instance = MagicMock()
        mock_qdrant_client_class.return_value = mock_client_instance
        
        # Mock search results
        mock_hit_1 = MagicMock()
        mock_hit_1.id = "doc1"
        mock_hit_1.score = 0.95
        mock_hit_1.payload = {"document": "This is the first matching document."}
        
        mock_hit_2 = MagicMock()
        mock_hit_2.id = "doc2"
        mock_hit_2.score = 0.87
        mock_hit_2.payload = {"document": "This is the second matching document."}
        
        mock_search_results = MagicMock()
        mock_search_results.points = [mock_hit_1, mock_hit_2]
        mock_client_instance.query_points.return_value = mock_search_results
        
        # Test data
        query = "test search query"
        collection_name = "test_collection"
        top_k = 5
        
        # Call the activity and await it
        result = await search_documents_activity(query, collection_name, top_k)
        
        # Verify Qdrant client was called correctly
        mock_qdrant_client_class.assert_called_once()
        mock_client_instance.query_points.assert_called_once()
        
        # Verify query_points was called with correct parameters
        call_args = mock_client_instance.query_points.call_args
        assert call_args[1]['collection_name'] == collection_name
        assert call_args[1]['limit'] == top_k
        assert call_args[1]['with_payload'] is True
        assert call_args[1]['using'] == EMBEDDING_MODEL_NAME # Check for 'using'
        
        # Verify the query structure passed to query_points
        # In activities.py, it's: qdrant_models.Document(text=query, model=EMBEDDING_MODEL_NAME)
        # We need to ensure the 'query' argument to query_points matches this structure.
        # The actual 'query' argument in call_args[1]['query'] will be an object.
        # We can check its attributes if qdrant_models.Document is not easily mockable here.
        query_arg = call_args[1]['query']
        assert hasattr(query_arg, 'text') and query_arg.text == query
        assert hasattr(query_arg, 'model') and query_arg.model == EMBEDDING_MODEL_NAME


        # Verify result structure
        assert isinstance(result, dict)
        assert 'status' in result
        assert result['status'] == 'success'
        assert 'query' in result
        assert result['query'] == query
        assert 'collection_name' in result
        assert result['collection_name'] == collection_name
        assert 'results' in result
        assert isinstance(result['results'], list)
        assert len(result['results']) == 2
        
        # Verify result content
        first_result = result['results'][0]
        assert first_result['id'] == "doc1"
        assert first_result['text'] == "This is the first matching document."
        assert first_result['score'] == 0.95
        
        second_result = result['results'][1]
        assert second_result['id'] == "doc2"
        assert second_result['text'] == "This is the second matching document."
        assert second_result['score'] == 0.87
        
        # Verify client was closed
        mock_client_instance.close.assert_called_once()
    
    @patch('activities.QdrantClient')
    @pytest.mark.asyncio
    async def test_search_documents_activity_empty_results(self, mock_qdrant_client_class):
        """
        Test search_documents_activity handles empty search results gracefully.
        """
        try:
            from activities import search_documents_activity
        except ImportError:
            pytest.skip("search_documents_activity not implemented yet")

        # Setup mock for empty results
        mock_client_instance = MagicMock()
        mock_qdrant_client_class.return_value = mock_client_instance

        mock_search_results = MagicMock()
        mock_search_results.points = []  # Empty results
        mock_client_instance.query_points.return_value = mock_search_results

        # Call the activity and await it
        result = await search_documents_activity("no match query", "test_collection", 5)

        # Verify empty results are handled properly
        assert result['status'] == 'success'
        assert result['results'] == []
        assert len(result['results']) == 0
    
    @patch('activities.QdrantClient')
    @pytest.mark.asyncio
    async def test_search_documents_activity_error_handling(self, mock_qdrant_client_class): # Add async
        """
        Test search_documents_activity handles Qdrant errors gracefully.
        """
        try:
            from activities import search_documents_activity
        except ImportError:
            pytest.skip("search_documents_activity not implemented yet")

        # Setup mock to raise an exception
        mock_client_instance = MagicMock()
        mock_qdrant_client_class.return_value = mock_client_instance
        mock_client_instance.query_points.side_effect = Exception("Qdrant connection error")

        # Call the activity and await it
        result = await search_documents_activity("test query", "test_collection", 5)

        # Verify error is handled gracefully
        assert result['status'] == 'error'
        assert "Qdrant connection error" in result['error_message'] # Changed 'message' to 'error_message'
