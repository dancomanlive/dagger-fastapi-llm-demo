#!/usr/bin/env python3
"""
Test for the refactored retriever service activities with normalization.
This ensures that the argument normalization works in the retriever service.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Import the function we want to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'retriever_service'))

from services.retriever_service.activities import search_documents_activity, normalize_args_input


class TestRetrieverServiceNormalization:
    """Test that retriever service works with normalized arguments"""
    
    def test_normalize_args_input_standalone(self):
        """Test the normalization function used in retriever service"""
        
        # Test list format
        list_args = (["machine learning", "test-collection", 5],)
        result = normalize_args_input(*list_args)
        expected = {
            "query": "machine learning",
            "collection": "test-collection",
            "top_k": 5
        }
        assert result == expected
        
        # Test direct format  
        direct_args = ("machine learning", "test-collection", 5)
        result = normalize_args_input(*direct_args)
        assert result == expected
        
        # Test with defaults
        default_args = ("machine learning", "test-collection")
        result = normalize_args_input(*default_args)
        expected_with_defaults = {
            "query": "machine learning",
            "collection": "test-collection", 
            "top_k": 5  # Default for retriever
        }
        assert result == expected_with_defaults

    @pytest.mark.asyncio
    async def test_search_documents_activity_with_normalization(self):
        """Test that search_documents_activity works with normalized arguments"""
        
        # Mock the QdrantClient and its methods
        mock_client = Mock()
        mock_client.query.return_value = [
            Mock(id="doc1", payload={"document": "test content"}, score=0.9)
        ]
        
        # Test different argument formats
        test_cases = [
            # List format
            (["machine learning", "test-collection", 5],),
            # Direct format  
            ("machine learning", "test-collection", 5),
            # With defaults
            ("machine learning", "test-collection"),
        ]
        
        for args in test_cases:
            with patch('services.retriever_service.activities.QdrantClient', return_value=mock_client):
                # The function should normalize args and work regardless of format
                result = await search_documents_activity(*args)
                
                # Check that we get a proper response structure
                assert "status" in result
                assert "retrieved_documents" in result
                assert "total_results" in result
                
                # The normalization should have extracted the query correctly
                expected_query = "machine learning"
                expected_collection = "test-collection"
                
                # Verify QdrantClient.query was called with correct parameters
                mock_client.query.assert_called()
                call_args = mock_client.query.call_args
                assert expected_collection in str(call_args)  # Collection name should be in the call


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
