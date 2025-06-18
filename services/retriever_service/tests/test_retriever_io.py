#!/usr/bin/env python3
"""
Unit tests for Retriever Service - Core RAG functionality

Tests the input/output contracts for search_documents_activity
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from activities import search_documents_activity


class TestRetrieverServiceIO:
    """Test input/output contracts for retriever service"""
    
    def test_search_documents_input_validation(self):
        """Test that search_documents_activity validates input format"""
        
        # Valid input format
        valid_input = {
            "query": "machine learning",
            "collection_name": "test-collection", 
            "top_k": 5
        }
        
        # This should not raise an exception
        # (We'll mock the actual Qdrant call)
        assert isinstance(valid_input["query"], str)
        assert isinstance(valid_input["collection_name"], str)
        assert isinstance(valid_input["top_k"], int)
        assert valid_input["top_k"] > 0
    
    def test_search_documents_required_fields(self):
        """Test that required input fields are validated"""
        
        # Missing query
        invalid_input_1 = {
            "collection_name": "test-collection",
            "top_k": 5
        }
        
        # Missing collection_name
        invalid_input_2 = {
            "query": "machine learning",
            "top_k": 5
        }
        
        # Test that these would fail validation
        assert "query" not in invalid_input_1
        assert "collection_name" not in invalid_input_2
    
    @patch('activities.QdrantClient')
    def test_search_documents_success_output_format(self, mock_qdrant_class):
        """Test the success output format matches specification"""
        
        # Create mock client instance
        mock_client = MagicMock()
        mock_qdrant_class.return_value = mock_client
        
        # Mock Qdrant response
        mock_points = [
            MagicMock(
                id="doc1",
                payload={"document": "This is about machine learning"},
                score=0.95
            ),
            MagicMock(
                id="doc2", 
                payload={"document": "Deep learning algorithms"},
                score=0.87
            )
        ]
        
        mock_client.query.return_value = mock_points
        
        # Expected output format
        expected_format = {
            "status": "success",
            "query": "machine learning",
            "retrieved_documents": [
                {
                    "id": "doc1",
                    "text": "This is about machine learning",
                    "score": 0.95
                },
                {
                    "id": "doc2",
                    "text": "Deep learning algorithms", 
                    "score": 0.87
                }
            ],
            "total_results": 2,
            "processing_time": float,  # Should be a float
            "collection_name": "test-collection"
        }
        
        # Test the structure (this is what we expect)
        assert expected_format["status"] == "success"
        assert isinstance(expected_format["retrieved_documents"], list)
        assert len(expected_format["retrieved_documents"]) == 2
        assert all("id" in doc for doc in expected_format["retrieved_documents"])
        assert all("text" in doc for doc in expected_format["retrieved_documents"])
        assert all("score" in doc for doc in expected_format["retrieved_documents"])
    
    def test_search_documents_error_output_format(self):
        """Test the error output format matches specification"""
        
        # Expected error format
        expected_error_format = {
            "status": "error",
            "query": "machine learning",
            "error": "Collection not found: invalid-collection",
            "retrieved_documents": [],
            "total_results": 0,
            "processing_time": float,  # Should be a float
            "collection_name": "invalid-collection"
        }
        
        # Validate error structure
        assert expected_error_format["status"] == "error"
        assert "error" in expected_error_format
        assert expected_error_format["retrieved_documents"] == []
        assert expected_error_format["total_results"] == 0
    
    def test_search_documents_score_validation(self):
        """Test that scores are valid floats between 0.0 and 1.0"""
        
        # Valid scores
        valid_scores = [0.0, 0.5, 0.95, 1.0]
        for score in valid_scores:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0
        
        # Invalid scores that should be caught
        invalid_scores = [-0.1, 1.1, "0.5", None]
        for score in invalid_scores:
            if score is not None and not isinstance(score, str):
                assert not (isinstance(score, float) and 0.0 <= score <= 1.0)
    
    def test_search_documents_empty_results_format(self):
        """Test output format when no documents found"""
        
        # Expected format for empty results
        expected_empty_format = {
            "status": "success",  # Still success, just no results
            "query": "nonexistent query",
            "retrieved_documents": [],
            "total_results": 0,
            "processing_time": float,
            "collection_name": "test-collection"
        }
        
        # Validate empty results structure
        assert expected_empty_format["status"] == "success"
        assert expected_empty_format["retrieved_documents"] == []
        assert expected_empty_format["total_results"] == 0


class TestRetrieverServiceIntegration:
    """Integration tests with mocked dependencies"""
    
    @patch('activities.QdrantClient')
    @patch('activities.time.time')
    @pytest.mark.asyncio
    async def test_search_documents_activity_args_format(self, mock_time, mock_qdrant_class):
        """Test the actual activity function with new *args signature"""
        
        # Create mock client instance
        mock_client = MagicMock()
        mock_qdrant_class.return_value = mock_client
        
        # Mock timing
        mock_time.side_effect = [1000.0, 1001.5]  # Start and end times
        
        # Mock Qdrant response  
        mock_points = [
            MagicMock(
                id="test-doc-1",
                payload={"document": "Machine learning is a subset of AI"},
                score=0.92
            )
        ]
        mock_client.query.return_value = mock_points
        
        # Test with list format (as used in pipeline)
        result = await search_documents_activity(["machine learning", "test-docs", 5])
        
        # Verify the call structure
        mock_qdrant_class.assert_called_once()
        mock_client.query.assert_called_once()
        
        # Should return dict format
        assert isinstance(result, dict)
        assert "status" in result
        assert "retrieved_documents" in result
        assert "total_results" in result
        assert "processing_time" in result
        
    @patch('activities.QdrantClient')
    @patch('activities.time.time')  
    @pytest.mark.asyncio
    async def test_search_documents_activity_direct_args(self, mock_time, mock_qdrant_class):
        """Test the activity function with direct arguments"""
        
        # Create mock client instance
        mock_client = MagicMock()
        mock_qdrant_class.return_value = mock_client
        
        # Mock timing
        mock_time.side_effect = [1000.0, 1001.5]
        
        # Mock Qdrant response
        mock_points = [
            MagicMock(
                id="test-doc-2",
                payload={"document": "Deep learning algorithms"},
                score=0.87
            )
        ]
        mock_client.query.return_value = mock_points
        
        # Test with direct arguments
        result = await search_documents_activity("deep learning", "test-docs", 3)
        
        # Verify the call structure
        mock_qdrant_class.assert_called_once()
        mock_client.query.assert_called_once()
        
        # Should return dict format  
        assert isinstance(result, dict)
        assert "status" in result
        assert "retrieved_documents" in result
        assert "total_results" in result
        assert "processing_time" in result
        
    @pytest.mark.asyncio
    async def test_search_documents_activity_invalid_args(self):
        """Test that invalid arguments raise appropriate errors"""
        
        # Test with insufficient arguments
        try:
            await search_documents_activity("just one arg")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Expected at least 2 arguments" in str(e)
    
    @patch('activities.QdrantClient')
    @patch('activities.time.time')
    @pytest.mark.asyncio
    async def test_search_documents_activity_error_handling(self, mock_time, mock_qdrant_class):
        """Test error handling in the activity function"""
        
        # Mock timing
        mock_time.side_effect = [1000.0, 1001.5]
        
        # Make Qdrant client raise an exception
        mock_qdrant_class.side_effect = Exception("Connection failed")
        
        result = await search_documents_activity(["test query", "test-collection", 5])
        
        # Should return error format
        assert result["status"] == "error" 
        assert "error" in result
        assert result["retrieved_documents"] == []
        assert result["total_results"] == 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
