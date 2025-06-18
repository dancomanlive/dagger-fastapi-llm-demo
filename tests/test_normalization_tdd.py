#!/usr/bin/env python3
"""
Test-Driven Development for Input Normalization

This file contains tests for the normalization functions that will eliminate
if/else chains in transforms. We'll write tests first, then implement.
"""

import pytest
from typing import Any, Dict, List

# We'll implement these functions after writing the tests
from services.temporal_service.normalization import (
    normalize_query_input,
    normalize_documents_input,
    normalize_args_input,
    simple_query_transform,
    simple_documents_transform
)

class TestQueryInputNormalization:
    """Test normalization of query inputs to standard format"""
    
    def test_normalize_string_query(self):
        """String input should become standard dict"""
        input_data = "machine learning"
        expected = {
            "query": "machine learning",
            "collection": "default",
            "top_k": 10
        }
        
        result = normalize_query_input(input_data)
        assert result == expected
    
    def test_normalize_list_query(self):
        """List input should extract first element as query"""
        input_data = ["machine learning"]
        expected = {
            "query": "machine learning", 
            "collection": "default",
            "top_k": 10
        }
        
        result = normalize_query_input(input_data)
        assert result == expected
    
    def test_normalize_dict_query_complete(self):
        """Complete dict should pass through with defaults filled"""
        input_data = {
            "query": "deep learning",
            "collection": "ai-papers", 
            "top_k": 5
        }
        expected = {
            "query": "deep learning",
            "collection": "ai-papers",
            "top_k": 5
        }
        
        result = normalize_query_input(input_data)
        assert result == expected
    
    def test_normalize_dict_query_partial(self):
        """Partial dict should get default values"""
        input_data = {"query": "neural networks"}
        expected = {
            "query": "neural networks",
            "collection": "default", 
            "top_k": 10
        }
        
        result = normalize_query_input(input_data)
        assert result == expected
    
    def test_normalize_empty_list(self):
        """Empty list should become empty query with defaults"""
        input_data = []
        expected = {
            "query": "",
            "collection": "default",
            "top_k": 10
        }
        
        result = normalize_query_input(input_data)
        assert result == expected
    
    def test_normalize_none_input(self):
        """None input should become empty query"""
        input_data = None
        expected = {
            "query": "",
            "collection": "default", 
            "top_k": 10
        }
        
        result = normalize_query_input(input_data)
        assert result == expected


class TestDocumentsInputNormalization:
    """Test normalization of documents inputs to standard format"""
    
    def test_normalize_retrieval_result(self):
        """Retrieved documents should extract from nested structure"""
        input_data = {
            "status": "success",
            "retrieved_documents": [
                {"id": "doc1", "text": "content1", "score": 0.9},
                {"id": "doc2", "text": "content2", "score": 0.8}
            ],
            "total_results": 2
        }
        expected = [
            {"id": "doc1", "text": "content1", "score": 0.9},
            {"id": "doc2", "text": "content2", "score": 0.8}
        ]
        
        result = normalize_documents_input(input_data)
        assert result == expected
    
    def test_normalize_documents_dict(self):
        """Dict with documents key should extract documents"""
        input_data = {
            "documents": [
                {"id": "doc1", "text": "content1"},
                {"id": "doc2", "text": "content2"}
            ]
        }
        expected = [
            {"id": "doc1", "text": "content1"},
            {"id": "doc2", "text": "content2"}
        ]
        
        result = normalize_documents_input(input_data)
        assert result == expected
    
    def test_normalize_direct_list(self):
        """Direct list should pass through unchanged"""
        input_data = [
            {"id": "doc1", "text": "content1"},
            {"id": "doc2", "text": "content2"}
        ]
        expected = [
            {"id": "doc1", "text": "content1"},
            {"id": "doc2", "text": "content2"}
        ]
        
        result = normalize_documents_input(input_data)
        assert result == expected
    
    def test_normalize_single_document(self):
        """Single document should become list of one"""
        input_data = {"id": "doc1", "text": "content1"}
        expected = [{"id": "doc1", "text": "content1"}]
        
        result = normalize_documents_input(input_data)
        assert result == expected
    
    def test_normalize_empty_retrieval(self):
        """Empty retrieval should return empty list"""
        input_data = {
            "status": "success",
            "retrieved_documents": [],
            "total_results": 0
        }
        expected = []
        
        result = normalize_documents_input(input_data)
        assert result == expected


class TestArgsInputNormalization:
    """Test normalization of function arguments (for retriever service)"""
    
    def test_normalize_list_args(self):
        """List format args should be normalized"""
        input_args = (["machine learning", "test-collection", 5],)
        expected = {
            "query": "machine learning",
            "collection": "test-collection",
            "top_k": 5
        }
        
        result = normalize_args_input(*input_args)
        assert result == expected
    
    def test_normalize_direct_args(self):
        """Direct format args should be normalized"""
        input_args = ("machine learning", "test-collection", 5)
        expected = {
            "query": "machine learning",
            "collection": "test-collection",
            "top_k": 5
        }
        
        result = normalize_args_input(*input_args)
        assert result == expected
    
    def test_normalize_args_with_defaults(self):
        """Args without top_k should get default"""
        input_args = ("machine learning", "test-collection")
        expected = {
            "query": "machine learning", 
            "collection": "test-collection",
            "top_k": 5  # Default for retriever
        }
        
        result = normalize_args_input(*input_args)
        assert result == expected
    
    def test_normalize_list_args_with_defaults(self):
        """List args without top_k should get default"""
        input_args = (["machine learning", "test-collection"],)
        expected = {
            "query": "machine learning",
            "collection": "test-collection", 
            "top_k": 5  # Default for retriever
        }
        
        result = normalize_args_input(*input_args)
        assert result == expected
    
    def test_normalize_insufficient_args(self):
        """Insufficient args should raise clear error"""
        input_args = ("only one arg",)
        
        with pytest.raises(ValueError, match="Expected at least 2 arguments"):
            normalize_args_input(*input_args)


class TestNormalizationIntegration:
    """Test that normalized inputs work with existing transforms"""
    
    def test_query_normalization_integration(self):
        """Normalized query should work with query transform logic"""
        # Test the pattern: normalize -> simple transform
        
        # Various inputs
        string_input = "machine learning"
        list_input = ["machine learning"] 
        dict_input = {"query": "machine learning", "top_k": 5}
        
        # After normalization, all should produce same transform output
        norm1 = normalize_query_input(string_input)
        norm2 = normalize_query_input(list_input) 
        norm3 = normalize_query_input(dict_input)
        
        # Simple transform (no if/else needed!)
        result1 = simple_query_transform(norm1)
        result2 = simple_query_transform(norm2)
        result3 = simple_query_transform(norm3)
        
        # All should have same query
        assert result1[0] == result2[0] == result3[0] == "machine learning"
        # All should have same collection (default)
        assert result1[1] == result2[1] == "default"
        # Top_k values might differ but should be consistent with normalization
        assert result1[2] == 10  # string input gets default
        assert result2[2] == 10  # list input gets default
        assert result3[2] == 5   # dict input preserves its top_k
    
    def test_documents_normalization_integration(self):
        """Normalized documents should work with documents transform logic"""
        # Different input formats
        retrieval_result = {
            "status": "success",
            "retrieved_documents": [{"id": "doc1", "text": "content"}]
        }
        direct_list = [{"id": "doc1", "text": "content"}]
        
        # After normalization, both should produce same result
        norm1 = normalize_documents_input(retrieval_result)
        norm2 = normalize_documents_input(direct_list)
        
        # Simple transform (no if/else needed!)
        result1 = simple_documents_transform(norm1)
        result2 = simple_documents_transform(norm2)
        
        assert result1 == result2 == [{"id": "doc1", "text": "content"}]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
