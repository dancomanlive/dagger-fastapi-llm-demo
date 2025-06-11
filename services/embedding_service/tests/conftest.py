"""
Pytest configuration and shared fixtures for embedding service tests.
"""

import pytest
import sys
from pathlib import Path

# Add the embedding service directory to Python path for imports
embedding_service_path = Path(__file__).parent.parent
sys.path.insert(0, str(embedding_service_path))


@pytest.fixture
def sample_documents():
    """Fixture providing sample documents for testing."""
    return [
        {"id": "doc1", "text": "This is a sample document about machine learning."},
        {"id": "doc2", "text": "This document discusses artificial intelligence concepts."},
        {"id": "doc3", "text": "A brief overview of neural networks and deep learning."}
    ]


@pytest.fixture
def sample_collection_name():
    """Fixture providing a test collection name."""
    return "test-collection"


@pytest.fixture
def mock_qdrant_client():
    """Fixture providing a mock QdrantClient for testing."""
    # This will be expanded when we start writing actual activity tests
    pass
