"""
Pytest configuration and shared fixtures for retriever service tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add the retriever service directory to Python path for imports
retriever_service_path = Path(__file__).parent.parent
sys.path.insert(0, str(retriever_service_path))


@pytest.fixture
def sample_query():
    """Fixture providing a sample search query for testing."""
    return "test search query"


@pytest.fixture
def sample_collection_name():
    """Fixture providing a test collection name."""
    return "test_collection"


@pytest.fixture
def sample_top_k():
    """Fixture providing a sample top_k value."""
    return 5


@pytest.fixture
def mock_search_results():
    """Fixture providing mock search results from Qdrant."""
    mock_hit_1 = MagicMock()
    mock_hit_1.id = "doc1"
    mock_hit_1.score = 0.95
    mock_hit_1.payload = {"document": "This is the first matching document."}
    
    mock_hit_2 = MagicMock()
    mock_hit_2.id = "doc2"
    mock_hit_2.score = 0.87
    mock_hit_2.payload = {"document": "This is the second matching document."}
    
    mock_search_results = MagicMock()
    mock_search_results.points = [mock_hit_1, mock_hit_2]
    
    return mock_search_results


@pytest.fixture
def empty_search_results():
    """Fixture providing empty search results from Qdrant."""
    mock_search_results = MagicMock()
    mock_search_results.points = []
    return mock_search_results
