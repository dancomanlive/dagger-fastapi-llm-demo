import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock workflow logger for transforms that use it
patch('temporalio.workflow.logger', MagicMock()).start()

from transforms.base_transform import BaseTransform
from transforms.documents_transform import DocumentsTransform
from transforms.chunked_docs_with_collection_transform import ChunkedDocsWithCollectionTransform
from transforms.query_with_collection_transform import QueryWithCollectionTransform
from transforms.passthrough_transform import PassthroughTransform
from transforms import get_transform

# Test data
TEST_DOCS = [{"id": "doc1", "text": "some text"}]
WORKFLOW_INPUT_WITH_COLLECTION = {"collection": "my_test_collection"}
DEFAULT_COLLECTION = "default_collection"

class TestTransforms:
    def test_get_transform(self):
        assert isinstance(get_transform("documents"), DocumentsTransform)
        assert isinstance(get_transform("chunked_docs_with_collection"), ChunkedDocsWithCollectionTransform)
        assert isinstance(get_transform("query_with_collection"), QueryWithCollectionTransform)
        assert isinstance(get_transform("passthrough"), PassthroughTransform)
        assert isinstance(get_transform("non_existent_transform"), PassthroughTransform)

    def test_documents_transform(self):
        transform = DocumentsTransform()
        
        # Test with dict containing 'documents'
        data = {"documents": TEST_DOCS}
        result = transform.transform(data, {}, {}, DEFAULT_COLLECTION)
        assert result == TEST_DOCS  # Updated: should return the documents directly, not wrapped in list

        # Test with list
        data = TEST_DOCS
        result = transform.transform(data, {}, {}, DEFAULT_COLLECTION)
        assert result == TEST_DOCS  # Updated: should return the list directly

    def test_chunked_docs_with_collection_transform(self):
        transform = ChunkedDocsWithCollectionTransform()

        # Test with nested list and custom collection
        data = [[{"id": "chunk1"}]]
        result = transform.transform(data, {}, WORKFLOW_INPUT_WITH_COLLECTION, DEFAULT_COLLECTION)
        assert result == [[{"id": "chunk1"}], "my_test_collection"]

        # Test with flat list and default collection
        data = [{"id": "chunk1"}]
        result = transform.transform(data, {}, {}, DEFAULT_COLLECTION)
        assert result == [[{"id": "chunk1"}], DEFAULT_COLLECTION]

    def test_query_with_collection_transform(self):
        transform = QueryWithCollectionTransform()

        # Test with dict and custom collection
        data = {"query": "my query", "top_k": 5, "collection": "custom_query_collection"}
        result = transform.transform(data, {}, {}, DEFAULT_COLLECTION)
        assert result == ["my query", "custom_query_collection", 5]

        # Test with string query and default collection
        data = "string query"
        result = transform.transform(data, {}, {}, DEFAULT_COLLECTION)
        assert result == ["string query", DEFAULT_COLLECTION, 10]

        # Test with list input (new case added for IO pipeline compatibility)
        data = ["list query"]
        result = transform.transform(data, {}, {}, DEFAULT_COLLECTION)
        assert result == ["list query", DEFAULT_COLLECTION, 10]

        # Test with list input containing non-string
        data = [{"nested": "query"}]
        result = transform.transform(data, {}, {}, DEFAULT_COLLECTION)
        assert result == ["{'nested': 'query'}", DEFAULT_COLLECTION, 10]

    def test_passthrough_transform(self):
        transform = PassthroughTransform()
        
        data = {"key": "value"}
        result = transform.transform(data, {}, {}, DEFAULT_COLLECTION)
        assert result == [{"key": "value"}]

        data_list = ["item1", "item2"]
        result = transform.transform(data_list, {}, {}, DEFAULT_COLLECTION)
        assert result == ["item1", "item2"]
