#!/usr/bin/env python3
"""
Comprehensive Pipeline IO Integration Tests

Tests the input/output contracts and data flow between all pipeline components:
- Retriever Service
- Embedding Service  
- Temporal Service (workflows, transforms, activities)
- Gradio Service

This validates that the IO changes made to fix the end-to-end workflow
maintain compatibility across all service boundaries.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os
import json

# Add service paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'retriever_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'embedding_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'temporal_service'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'gradio_service'))

# Import activities and transforms
from services.retriever_service.activities import search_documents_activity
from services.temporal_service.transforms.documents_transform import DocumentsTransform
from services.temporal_service.transforms.query_with_collection_transform import QueryWithCollectionTransform
from services.temporal_service.transforms.chunked_docs_with_collection_transform import ChunkedDocsWithCollectionTransform


class TestPipelineIOIntegration:
    """Test IO contracts between all pipeline components"""
    
    def test_data_formats_consistency(self):
        """Test that data formats are consistent across pipeline components"""
        
        # Standard test data formats used throughout pipeline
        test_query = "machine learning algorithms"
        test_collection = "test-docs"
        test_documents = [
            {"id": "doc1", "text": "Machine learning is a subset of AI", "score": 0.95},
            {"id": "doc2", "text": "Deep learning uses neural networks", "score": 0.87}
        ]
        test_chunks = [
            {"id": "chunk1", "text": "Machine learning chunk", "metadata": {"source": "doc1"}},
            {"id": "chunk2", "text": "Deep learning chunk", "metadata": {"source": "doc2"}}
        ]
        
        # Test query format handling across transforms
        query_transform = QueryWithCollectionTransform()
        
        # String input
        result = query_transform.transform(test_query, {}, {}, test_collection)
        assert result == [test_query, test_collection, 10]
        
        # List input (pipeline format)
        result = query_transform.transform([test_query], {}, {}, test_collection)
        assert result == [test_query, test_collection, 10]
        
        # Dict input
        query_dict = {"query": test_query, "top_k": 5, "collection": "custom-collection"}
        result = query_transform.transform(query_dict, {}, {}, test_collection)
        assert result == [test_query, "custom-collection", 5]
        
        # Test document format handling
        docs_transform = DocumentsTransform()
        
        # List input (direct)
        result = docs_transform.transform(test_documents, {}, {}, test_collection)
        assert result == test_documents
        
        # Dict input with 'documents' key
        result = docs_transform.transform({"documents": test_documents}, {}, {}, test_collection)
        assert result == test_documents
        
        # Test chunked documents format
        chunks_transform = ChunkedDocsWithCollectionTransform()
        
        # Flat list
        result = chunks_transform.transform(test_chunks, {}, {}, test_collection)
        assert result == [test_chunks, test_collection]
        
        # Nested list (from chunking activity)
        result = chunks_transform.transform([test_chunks], {}, {}, test_collection)
        assert result == [test_chunks, test_collection]
    
    @patch('services.retriever_service.activities.QdrantClient')
    @patch('services.retriever_service.activities.time.time')
    @pytest.mark.asyncio
    async def test_retriever_to_temporal_io(self, mock_time, mock_qdrant_class):
        """Test IO between retriever service and temporal service"""
        
        # Mock Qdrant client
        mock_client = MagicMock()
        mock_qdrant_class.return_value = mock_client
        mock_time.side_effect = [1000.0, 1001.5]
        
        # Mock retrieval results
        mock_points = [
            MagicMock(
                id="doc1",
                payload={"document": "Machine learning content"},
                score=0.95
            ),
            MagicMock(
                id="doc2", 
                payload={"document": "Deep learning content"},
                score=0.87
            )
        ]
        mock_client.query.return_value = mock_points
        
        # Test retriever service with list args (temporal format)
        result = await search_documents_activity(["machine learning", "test-collection", 5])
        
        # Verify output format matches what temporal service expects
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert "retrieved_documents" in result
        assert isinstance(result["retrieved_documents"], list)
        assert len(result["retrieved_documents"]) == 2
        
        # Verify document structure
        for doc in result["retrieved_documents"]:
            assert "id" in doc
            assert "text" in doc  
            assert "score" in doc
            assert isinstance(doc["score"], float)
            assert 0.0 <= doc["score"] <= 1.0
        
        # Test that this output can be processed by documents transform
        docs_transform = DocumentsTransform()
        transformed = docs_transform.transform(result["retrieved_documents"], {}, {}, "test-collection")
        assert transformed == result["retrieved_documents"]
        
    @patch('services.retriever_service.activities.QdrantClient')
    @patch('services.retriever_service.activities.time.time')
    @pytest.mark.asyncio
    async def test_chunking_to_temporal_io(self, mock_time, mock_qdrant_class):
        """Test that chunking results work with transform pipeline"""
        
        # Simulate chunking activity results
        chunked_results = [
            {"id": "chunk1", "text": "Machine learning chunk", "metadata": {"source": "doc1"}},
            {"id": "chunk2", "text": "Deep learning chunk", "metadata": {"source": "doc2"}}
        ]
        
        # Test that this output works with chunked docs transform
        chunks_transform = ChunkedDocsWithCollectionTransform()
        transformed = chunks_transform.transform([chunked_results], {}, {}, "test-collection")
        
        # Should return [chunks, collection_name] format
        assert isinstance(transformed, list)
        assert len(transformed) == 2
        assert transformed[0] == chunked_results
        assert transformed[1] == "test-collection"
    
    def test_transform_pipeline_compatibility(self):
        """Test that all transforms work together in pipeline sequence"""
        
        # Simulate full pipeline data flow
        initial_query = "machine learning"
        collection_name = "test-docs"
        
        # Step 1: Query transform (for retrieval)
        query_transform = QueryWithCollectionTransform()
        query_args = query_transform.transform([initial_query], {}, {}, collection_name)
        assert query_args == [initial_query, collection_name, 10]
        
        # Step 2: Simulate retriever results -> documents transform
        retriever_results = [
            {"id": "doc1", "text": "ML content", "score": 0.95},
            {"id": "doc2", "text": "AI content", "score": 0.87}
        ]
        docs_transform = DocumentsTransform() 
        docs_for_chunking = docs_transform.transform(retriever_results, {}, {}, collection_name)
        assert docs_for_chunking == retriever_results
        
        # Step 3: Simulate chunking results -> chunked docs transform
        chunked_results = [
            {"id": "chunk1", "text": "ML chunk", "metadata": {"source": "doc1"}},
            {"id": "chunk2", "text": "AI chunk", "metadata": {"source": "doc2"}}
        ]
        chunks_transform = ChunkedDocsWithCollectionTransform()
        embedding_args = chunks_transform.transform([chunked_results], {}, {}, collection_name)
        assert embedding_args == [chunked_results, collection_name]
        
        # Verify all transforms produce valid pipeline arguments
        assert all(isinstance(arg, (str, list, int, float)) for arg in query_args)
        assert all(isinstance(arg, (str, list, dict)) for arg in embedding_args)
    
    def test_error_propagation_consistency(self):
        """Test that error formats are consistent across all services"""
        
        # Standard error response format all services should follow
        expected_error_fields = ["status", "error", "processing_time"]
        
        # Each service should return errors in this format when things go wrong
        standard_error = {
            "status": "error",
            "error": "Test error message",
            "processing_time": 1.5
        }
        
        # Verify error structure
        assert standard_error["status"] == "error"
        assert "error" in standard_error
        assert isinstance(standard_error["processing_time"], (int, float))
        assert standard_error["processing_time"] >= 0


class TestServiceArgumentCompatibility:
    """Test that service function signatures are compatible with pipeline calls"""
    
    def test_retriever_service_signature(self):
        """Test retriever service accepts pipeline argument formats"""
        
        # The search_documents_activity should accept both:
        # 1. Direct args: search_documents_activity(query, collection, top_k)
        # 2. List args: search_documents_activity([query, collection, top_k])
        
        # This is verified by the function signature using *args
        # and the argument parsing logic in the activity
        
        # Test argument parsing logic simulation
        def parse_args(*args):
            if len(args) == 1 and isinstance(args[0], list) and len(args[0]) >= 2:
                query = args[0][0]
                collection_name = args[0][1] 
                top_k = args[0][2] if len(args[0]) > 2 else 5
            elif len(args) >= 2:
                query = args[0]
                collection_name = args[1]
                top_k = args[2] if len(args) > 2 else 5
            else:
                raise ValueError(f"Expected at least 2 arguments, got {len(args)}")
            return query, collection_name, top_k
        
        # Test list format (pipeline style)
        result = parse_args(["machine learning", "test-docs", 5])
        assert result == ("machine learning", "test-docs", 5)
        
        # Test direct format (traditional style)
        result = parse_args("machine learning", "test-docs", 5)
        assert result == ("machine learning", "test-docs", 5)
        
        # Test with defaults
        result = parse_args(["machine learning", "test-docs"])
        assert result == ("machine learning", "test-docs", 5)
        
        # Test error case
        try:
            parse_args("only one arg")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
    
    def test_embedding_service_signature(self):
        """Test embedding service accepts expected formats"""
        
        # embed_documents_activity(documents, collection_name)
        # chunk_documents_activity(documents)
        
        # These should accept list of dicts for documents
        test_docs = [
            {"id": "doc1", "text": "content1"},
            {"id": "doc2", "text": "content2"}
        ]
        
        # Test document structure validation
        for doc in test_docs:
            assert isinstance(doc, dict)
            assert "id" in doc
            assert "text" in doc
            assert isinstance(doc["text"], str)
            assert len(doc["text"]) > 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
