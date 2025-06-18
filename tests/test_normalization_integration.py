#!/usr/bin/env python3
"""
Integration Tests for Refactored Transforms

This file tests that the refactored transforms (which use normalization internally)
work correctly with various input types and demonstrate the benefits of the 
normalization pattern.
"""

import pytest
import sys
import os

# Add service paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'temporal_service'))

from services.temporal_service.normalization import (
    normalize_query_input,
    simple_query_transform
)
from services.temporal_service.transforms.query_with_collection_transform import QueryWithCollectionTransform


class TestRefactoredTransformIntegration:
    """Test that refactored transforms work correctly with different input types"""
    
    def test_refactored_transform_string_input(self):
        """Verify refactored transform handles string input correctly"""
        input_data = "machine learning"
        default_collection = "test-docs"
        
        # Refactored transform (uses normalization internally)
        transform = QueryWithCollectionTransform()
        result = transform.transform(input_data, {}, {}, default_collection)
        
        # Should produce correct output
        assert result == ["machine learning", "test-docs", 10]
    
    def test_refactored_transform_list_input(self):
        """Verify refactored transform handles list input correctly"""
        input_data = ["machine learning"]
        default_collection = "test-docs"
        
        # Refactored transform (uses normalization internally)
        transform = QueryWithCollectionTransform()
        result = transform.transform(input_data, {}, {}, default_collection)
        
        # Should produce correct output
        assert result == ["machine learning", "test-docs", 10]
    
    def test_refactored_transform_dict_input(self):
        """Verify refactored transform handles dict input correctly"""
        input_data = {"query": "deep learning", "top_k": 5, "collection": "ai-papers"}
        default_collection = "test-docs"
        
        # Refactored transform (uses normalization internally)
        transform = QueryWithCollectionTransform()
        result = transform.transform(input_data, {}, {}, default_collection)
        
        # Should produce correct output (preserves dict values)
        assert result == ["deep learning", "ai-papers", 5]
    
    def test_normalization_pattern_eliminates_complexity(self):
        """Demonstrate that the normalization pattern eliminates complex if/else logic"""
        
        # Various input types that would require if/else in old approach
        test_cases = [
            ("string input", "machine learning"),
            ("list input", ["machine learning"]),
            ("dict input", {"query": "machine learning", "top_k": 5}),
            ("none input", None),
            ("empty list", []),
            ("number input", 42)
        ]
        
        for description, input_data in test_cases:
            print(f"\nTesting {description}: {input_data}")
            
            # Normalize once (handles all the complexity)
            normalized = normalize_query_input(input_data)
            print(f"  Normalized: {normalized}")
            
            # Simple transform (no if/else needed!)
            result = simple_query_transform(normalized)
            print(f"  Result: {result}")
            
            # All results have the same structure
            assert isinstance(result, list)
            assert len(result) == 3
            assert isinstance(result[0], str)  # query
            assert isinstance(result[1], str)  # collection
            assert isinstance(result[2], int)  # top_k


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
