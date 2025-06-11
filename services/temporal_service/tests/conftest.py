"""
Pytest configuration and shared fixtures for temporal service tests.
"""

import pytest
import sys
from pathlib import Path

# Add the temporal service directory to Python path for imports
temporal_service_path = Path(__file__).parent.parent
sys.path.insert(0, str(temporal_service_path))


@pytest.fixture
def sample_documents():
    """Fixture providing sample documents for workflow testing."""
    return [
        {"id": "doc1", "text": "This is a sample document about machine learning and AI."},
        {"id": "doc2", "text": "This document discusses neural networks and deep learning algorithms."},
        {"id": "doc3", "text": "A comprehensive guide to natural language processing and transformers."}
    ]


@pytest.fixture
def sample_collection_name():
    """Fixture providing a test collection name."""
    return "test-workflow-collection"


@pytest.fixture
def sample_embedding_service_url():
    """Fixture providing a test embedding service URL."""
    return "http://test-embedding-service:8000"
