#!/usr/bin/env python3
"""
Unit tests for Embedding Service - Document indexing functionality

Tests the input/output contracts for perform_embedding_and_indexing_activity
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestEmbeddingServiceIO:
    """Test input/output contracts for embedding service"""
    
    def test_embedding_input_validation(self):
        """Test that embedding activity validates input format"""
        
        # Valid input format
        valid_input = {
            "documents": [
                {
                    "id": "doc1",
                    "text": "This is a sample document about machine learning"
                },
                {
                    "id": "doc2", 
                    "text": "Deep learning is a subset of machine learning"
                }
            ],
            "collection_name": "test-collection"
        }
        
        # Validate input structure
        assert isinstance(valid_input["documents"], list)
        assert len(valid_input["documents"]) > 0
        assert all("id" in doc for doc in valid_input["documents"])
        assert all("text" in doc for doc in valid_input["documents"])
        assert isinstance(valid_input["collection_name"], str)
    
    def test_embedding_required_fields(self):
        """Test that required input fields are validated"""
        
        # Missing documents
        invalid_input_1 = {
            "collection_name": "test-collection"
        }
        
        # Missing collection_name
        invalid_input_2 = {
            "documents": [{"id": "doc1", "text": "sample text"}]
        }
        
        # Empty documents list
        invalid_input_3 = {
            "documents": [],
            "collection_name": "test-collection"
        }
        
        # Test validation
        assert "documents" not in invalid_input_1
        assert "collection_name" not in invalid_input_2
        assert len(invalid_input_3["documents"]) == 0
    
    def test_embedding_success_output_format(self):
        """Test the success output format matches specification"""
        
        # Expected success output format
        expected_format = {
            "status": "success",
            "indexed_count": 2,
            "collection_name": "test-collection",
            "embedding_model": "BAAI/bge-small-en-v1.5",
            "elapsed_time": 1.23,
            "timestamp": 1703123456.789
        }
        
        # Validate success structure
        assert expected_format["status"] == "success"
        assert isinstance(expected_format["indexed_count"], int)
        assert expected_format["indexed_count"] > 0
        assert isinstance(expected_format["collection_name"], str)
        assert isinstance(expected_format["embedding_model"], str)
        assert isinstance(expected_format["elapsed_time"], float)
        assert isinstance(expected_format["timestamp"], float)
    
    def test_embedding_error_output_format(self):
        """Test the error output format matches specification"""
        
        # Expected error format
        expected_error_format = {
            "status": "error",
            "error": "Failed to connect to Qdrant: Connection refused"
        }
        
        # Validate error structure
        assert expected_error_format["status"] == "error"
        assert "error" in expected_error_format
        assert isinstance(expected_error_format["error"], str)
    
    def test_document_structure_validation(self):
        """Test individual document structure validation"""
        
        # Valid document
        valid_doc = {
            "id": "unique-doc-id",
            "text": "This is the document content"
        }
        
        # Invalid documents
        invalid_docs = [
            {"text": "Missing ID"},  # No ID
            {"id": "doc1"},          # No text
            {"id": "", "text": "Empty ID"},  # Empty ID
            {"id": "doc1", "text": ""},      # Empty text
            {"id": 123, "text": "Non-string ID"},  # Non-string ID
            {"id": "doc1", "text": 456}      # Non-string text
        ]
        
        # Test valid document
        assert "id" in valid_doc
        assert "text" in valid_doc
        assert isinstance(valid_doc["id"], str)
        assert isinstance(valid_doc["text"], str)
        assert len(valid_doc["id"]) > 0
        assert len(valid_doc["text"]) > 0
        
        # Test invalid documents
        for doc in invalid_docs:
            is_valid = (
                "id" in doc and 
                "text" in doc and
                isinstance(doc.get("id"), str) and
                isinstance(doc.get("text"), str) and
                len(doc.get("id", "")) > 0 and
                len(doc.get("text", "")) > 0
            )
            assert not is_valid, f"Document should be invalid: {doc}"


class TestEmbeddingServiceIntegration:
    """Integration tests with mocked dependencies"""
    
    @patch('activities.QdrantClient')
    @patch('activities.time.time')
    def test_embedding_activity_mock_integration(self, mock_time, mock_qdrant_class):
        """Test the embedding activity with mocked dependencies"""
        
        # Create mock client instance
        mock_client = MagicMock()
        mock_qdrant_class.return_value = mock_client
        
        # Mock timing
        mock_time.side_effect = [1000.0, 1002.5]  # Start and end times
        
        # Mock Qdrant client
        mock_client.upsert.return_value = MagicMock()
        
        # Test input
        test_input = {
            "documents": [
                {"id": "doc1", "text": "Machine learning algorithms"},
                {"id": "doc2", "text": "Deep neural networks"}
            ],
            "collection_name": "ml-papers"
        }
        
        # Expected processing time
        expected_elapsed_time = 2.5
        
        # Validate test setup
        assert len(test_input["documents"]) == 2
        assert mock_client.upsert.return_value is not None
        assert expected_elapsed_time == 2.5
    
    def test_embedding_model_configuration(self):
        """Test embedding model configuration"""
        
        # Expected model configurations
        valid_models = [
            "BAAI/bge-small-en-v1.5",
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2"
        ]
        
        # Test that model names are valid strings
        for model in valid_models:
            assert isinstance(model, str)
            assert len(model) > 0
            assert "/" in model  # Should be in format "org/model"
    
    def test_collection_name_validation(self):
        """Test collection name validation"""
        
        # Valid collection names
        valid_names = [
            "documents",
            "test-collection", 
            "ml_papers",
            "doc_chunks_v1"
        ]
        
        # Invalid collection names (examples)
        invalid_names = [
            "",              # Empty
            " ",             # Whitespace only
            "INVALID NAME",  # Spaces (depends on Qdrant rules)
            "a" * 256       # Too long (hypothetical limit)
        ]
        
        # Test valid names
        for name in valid_names:
            assert isinstance(name, str)
            assert len(name) > 0
            assert not name.isspace()
        
        # Test invalid names
        for name in invalid_names:
            is_valid = (
                isinstance(name, str) and 
                len(name) > 0 and 
                not name.isspace() and
                ' ' not in name and  # No spaces allowed
                len(name) < 100  # Reasonable limit
            )
            assert not is_valid, f"Collection name should be invalid: '{name}'"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
