#!/usr/bin/env python3
"""
Simplified Pipeline IO Tests

Tests the core IO changes made to fix the end-to-end workflow,
focusing on the transforms and retriever service changes.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add service paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'temporal_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'retriever_service'))

# Mock workflow logger before importing transforms
with patch('temporalio.workflow.logger', MagicMock()):
    from services.temporal_service.transforms.documents_transform import DocumentsTransform
    from services.temporal_service.transforms.query_with_collection_transform import QueryWithCollectionTransform
    from services.temporal_service.transforms.chunked_docs_with_collection_transform import ChunkedDocsWithCollectionTransform

from services.retriever_service.activities import search_documents_activity


class TestCoreIOChanges:
    """Test the specific IO changes made to fix the pipeline"""
    
    def test_documents_transform_returns_unwrapped_list(self):
        """Test that DocumentsTransform returns documents directly, not wrapped in extra list"""
        
        transform = DocumentsTransform()
        test_documents = [
            {"id": "doc1", "text": "content1"},
            {"id": "doc2", "text": "content2"}
        ]
        
        # Test with list input (should return the list directly)
        result = transform.transform(test_documents, {}, {}, "test-collection")
        assert result == test_documents  # Should NOT be [test_documents]
        assert isinstance(result, list)
        assert len(result) == 2
        
        # Test with dict input containing 'documents' key
        dict_input = {"documents": test_documents}
        result = transform.transform(dict_input, {}, {}, "test-collection")
        assert result == test_documents  # Should extract and return documents directly
    
    @patch('temporalio.workflow.logger')
    def test_query_transform_handles_list_input(self, mock_logger):
        """Test that QueryWithCollectionTransform handles list input (pipeline format)"""
        
        transform = QueryWithCollectionTransform()
        
        # Test with list input (new functionality for pipeline compatibility)
        result = transform.transform(["machine learning"], {}, {}, "test-collection")
        assert result == ["machine learning", "test-collection", 10]
        
        # Test with string input (existing functionality)
        result = transform.transform("machine learning", {}, {}, "test-collection")
        assert result == ["machine learning", "test-collection", 10]
        
        # Test with dict input (existing functionality)
        dict_input = {"query": "machine learning", "top_k": 5, "collection": "custom"}
        result = transform.transform(dict_input, {}, {}, "test-collection")
        assert result == ["machine learning", "custom", 5]
    
    def test_chunked_docs_transform_handles_nested_lists(self):
        """Test ChunkedDocsWithCollectionTransform handles various list formats"""
        
        transform = ChunkedDocsWithCollectionTransform()
        test_chunks = [{"id": "chunk1", "text": "content"}]
        
        # Test with nested list (from some activities)
        result = transform.transform([test_chunks], {}, {}, "test-collection")
        assert result == [test_chunks, "test-collection"]
        
        # Test with flat list
        result = transform.transform(test_chunks, {}, {}, "test-collection")
        assert result == [test_chunks, "test-collection"]
    
    @patch('services.retriever_service.activities.QdrantClient')
    @patch('services.retriever_service.activities.time.time')
    @pytest.mark.asyncio
    async def test_retriever_activity_args_signature(self, mock_time, mock_qdrant_class):
        """Test that retriever activity accepts both argument formats"""
        
        # Mock Qdrant client
        mock_client = MagicMock()
        mock_qdrant_class.return_value = mock_client
        mock_time.side_effect = [1000.0, 1001.5]
        
        mock_points = [
            MagicMock(id="doc1", payload={"document": "content"}, score=0.95)
        ]
        mock_client.query.return_value = mock_points
        
        # Test with list format (pipeline style) - this is the key change
        result = await search_documents_activity(["machine learning", "test-collection", 5])
        assert isinstance(result, dict)
        assert result["status"] == "success"
        
        # Reset mocks for second test
        mock_qdrant_class.reset_mock()
        mock_client.reset_mock()
        mock_time.side_effect = [1000.0, 1001.5]
        
        # Test with direct arguments (traditional style)
        result = await search_documents_activity("machine learning", "test-collection", 5)
        assert isinstance(result, dict)
        assert result["status"] == "success"
    
    def test_pipeline_data_flow_integration(self):
        """Test that the complete data flow works end-to-end with our changes"""
        
        # Simulate the pipeline flow that was fixed
        initial_query = ["machine learning"]  # List format from pipeline
        collection_name = "test-docs"
        
        # Step 1: Query transform (handles list input now)
        with patch('temporalio.workflow.logger'):
            query_transform = QueryWithCollectionTransform()
            query_args = query_transform.transform(initial_query, {}, {}, collection_name)
        
        assert query_args == ["machine learning", collection_name, 10]
        
        # Step 2: Simulate retriever results -> documents transform  
        retriever_results = [
            {"id": "doc1", "text": "ML content", "score": 0.95},
            {"id": "doc2", "text": "AI content", "score": 0.87}
        ]
        
        docs_transform = DocumentsTransform()
        processed_docs = docs_transform.transform(retriever_results, {}, {}, collection_name)
        
        # Should return documents directly (not wrapped in extra list)
        assert processed_docs == retriever_results
        assert isinstance(processed_docs, list)
        assert len(processed_docs) == 2
        
        # Step 3: Test chunked docs handling
        chunked_results = [
            {"id": "chunk1", "text": "ML chunk"},
            {"id": "chunk2", "text": "AI chunk"}
        ]
        
        chunks_transform = ChunkedDocsWithCollectionTransform()
        embedding_args = chunks_transform.transform([chunked_results], {}, {}, collection_name)
        
        assert embedding_args == [chunked_results, collection_name]
        assert isinstance(embedding_args[0], list)
        assert embedding_args[1] == collection_name
    
    def test_argument_parsing_logic(self):
        """Test the argument parsing logic used in retriever service"""
        
        # This simulates the logic in search_documents_activity
        def parse_retriever_args(*args):
            if len(args) == 1 and isinstance(args[0], list) and len(args[0]) >= 2:
                # Arguments passed as a single list: [query, collection_name, top_k]
                query = args[0][0]
                collection_name = args[0][1]
                top_k = args[0][2] if len(args[0]) > 2 else 5
            elif len(args) >= 2:
                # Arguments passed directly: query, collection_name, top_k
                query = args[0]
                collection_name = args[1]
                top_k = args[2] if len(args) > 2 else 5
            else:
                raise ValueError(f"Expected at least 2 arguments, got {len(args)}")
            return query, collection_name, top_k
        
        # Test list format (fixed for pipeline compatibility)
        result = parse_retriever_args(["machine learning", "test-docs", 5])
        assert result == ("machine learning", "test-docs", 5)
        
        # Test direct format (existing compatibility)
        result = parse_retriever_args("machine learning", "test-docs", 5)
        assert result == ("machine learning", "test-docs", 5)
        
        # Test list format with defaults
        result = parse_retriever_args(["machine learning", "test-docs"])
        assert result == ("machine learning", "test-docs", 5)
        
        # Test error handling
        with pytest.raises(ValueError):
            parse_retriever_args("insufficient args")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
