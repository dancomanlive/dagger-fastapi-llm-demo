#!/usr/bin/env python3
"""
Unit tests for Embedding Service - Document chunking functionality

Tests the chunk_documents_activity that was moved from temporal service
"""

import pytest
import sys
import os
from uuid import UUID

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from activities import chunk_documents_activity


class TestChunkDocumentsActivity:
    """Test the chunk_documents_activity functionality"""
    
    @pytest.mark.asyncio
    async def test_chunk_single_document(self):
        """Test chunking a single document"""
        documents = [
            {
                'id': 'doc1',
                'text': 'This is a test document with multiple sentences. It should be chunked appropriately.',
                'metadata': {'source': 'test', 'author': 'test_user'}
            }
        ]
        
        result = await chunk_documents_activity(documents)
        
        # Validate output structure
        assert isinstance(result, list)
        assert len(result) >= 1
        
        # Check first chunk
        chunk = result[0]
        assert 'id' in chunk
        assert 'text' in chunk
        assert 'metadata' in chunk
        
        # Validate chunk ID is UUID
        chunk_id = chunk['id']
        assert isinstance(chunk_id, str)
        # Should be able to parse as UUID
        UUID(chunk_id)
        
        # Validate metadata preservation and enhancement
        metadata = chunk['metadata']
        assert metadata['source'] == 'test'
        assert metadata['author'] == 'test_user'
        assert 'original_doc_id' in metadata
        assert metadata['original_doc_id'] == 'doc1'
        assert 'chunk_index' in metadata
        assert 'total_chunks' in metadata
        assert isinstance(metadata['chunk_index'], int)
        assert isinstance(metadata['total_chunks'], int)
        assert metadata['chunk_index'] >= 0
        assert metadata['total_chunks'] >= 1
    
    @pytest.mark.asyncio
    async def test_chunk_multiple_documents(self):
        """Test chunking multiple documents"""
        documents = [
            {
                'id': 'doc1',
                'text': 'First document content here.',
                'metadata': {'source': 'file1.txt'}
            },
            {
                'id': 'doc2',
                'text': 'Second document with different content and maybe longer text to test chunking behavior.',
                'metadata': {'source': 'file2.txt'}
            }
        ]
        
        result = await chunk_documents_activity(documents)
        
        # Should have at least as many chunks as documents
        assert len(result) >= len(documents)
        
        # Verify all original doc IDs are preserved
        original_ids = {chunk['metadata']['original_doc_id'] for chunk in result}
        expected_ids = {'doc1', 'doc2'}
        assert original_ids == expected_ids
        
        # Verify each chunk has unique ID
        chunk_ids = [chunk['id'] for chunk in result]
        assert len(chunk_ids) == len(set(chunk_ids))  # All unique
    
    @pytest.mark.asyncio
    async def test_chunk_empty_document(self):
        """Test handling of document with empty text"""
        documents = [
            {
                'id': 'empty_doc',
                'text': '',
                'metadata': {'source': 'empty.txt'}
            }
        ]
        
        result = await chunk_documents_activity(documents)
        
        # Should handle empty documents gracefully
        assert isinstance(result, list)
        # Behavior depends on implementation - might create empty chunk or skip
        if len(result) > 0:
            chunk = result[0]
            assert chunk['metadata']['original_doc_id'] == 'empty_doc'
    
    @pytest.mark.asyncio
    async def test_chunk_document_without_metadata(self):
        """Test chunking document without metadata field"""
        documents = [
            {
                'id': 'no_meta_doc',
                'text': 'Document without metadata field.'
            }
        ]
        
        result = await chunk_documents_activity(documents)
        
        assert len(result) >= 1
        chunk = result[0]
        
        # Should have metadata added
        assert 'metadata' in chunk
        metadata = chunk['metadata']
        assert metadata['original_doc_id'] == 'no_meta_doc'
        assert 'chunk_index' in metadata
        assert 'total_chunks' in metadata
    
    @pytest.mark.asyncio
    async def test_chunk_large_document(self):
        """Test chunking a larger document that should be split"""
        # Create a document with enough content to likely be chunked
        large_text = " ".join([
            f"This is sentence {i} in a large document that should be chunked into multiple pieces."
            for i in range(50)
        ])
        
        documents = [
            {
                'id': 'large_doc',
                'text': large_text,
                'metadata': {'source': 'large.txt', 'length': len(large_text)}
            }
        ]
        
        result = await chunk_documents_activity(documents)
        
        # Should create chunks
        assert len(result) >= 1
        
        # All chunks should be from same document
        for chunk in result:
            assert chunk['metadata']['original_doc_id'] == 'large_doc'
            assert chunk['metadata']['source'] == 'large.txt'
            assert chunk['metadata']['length'] == len(large_text)
        
        # Chunk indices should be sequential and start from 0
        chunk_indices = [chunk['metadata']['chunk_index'] for chunk in result]
        chunk_indices.sort()
        expected_indices = list(range(len(result)))
        assert chunk_indices == expected_indices
        
        # All chunks should have same total_chunks count
        total_chunks_values = {chunk['metadata']['total_chunks'] for chunk in result}
        assert len(total_chunks_values) == 1  # All should be the same
        assert list(total_chunks_values)[0] == len(result)
    
    @pytest.mark.asyncio
    async def test_chunk_input_validation(self):
        """Test input validation for chunk_documents_activity"""
        
        # Test with invalid input types
        with pytest.raises((TypeError, ValueError, AttributeError)):
            await chunk_documents_activity(None)
        
        with pytest.raises((TypeError, ValueError, AttributeError)):
            await chunk_documents_activity("not a list")
        
        # Test empty list - should return empty list, not raise error
        result = await chunk_documents_activity([])
        assert result == []
    
    @pytest.mark.asyncio
    async def test_chunk_text_preservation(self):
        """Test that chunking preserves original text content"""
        original_text = "First sentence. Second sentence. Third sentence with more detail."
        documents = [
            {
                'id': 'preserve_test',
                'text': original_text,
                'metadata': {'source': 'preserve.txt'}
            }
        ]
        
        result = await chunk_documents_activity(documents)
        
        # Combine all chunk texts
        combined_text = " ".join([chunk['text'].strip() for chunk in result])
        
        # Should preserve the essential content (allowing for slight formatting differences)
        # Check that key words are preserved
        original_words = set(original_text.lower().split())
        combined_words = set(combined_text.lower().split())
        
        # Most original words should be preserved
        preserved_ratio = len(original_words & combined_words) / len(original_words)
        assert preserved_ratio >= 0.8  # At least 80% of words preserved


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
