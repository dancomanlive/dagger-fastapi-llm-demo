import pytest
from scripts.superlinked_qdrant_connector import SuperlinkedQdrantConnector

@pytest.fixture
def mock_connector():
    return SuperlinkedQdrantConnector(
        superlinked_api_key="mock_api_key",
        superlinked_url="https://mock.superlinked.com",
        qdrant_url="https://mock.qdrant.com",
        qdrant_api_key="mock_qdrant_key"
    )

def test_query_pipeline(mock_connector):
    query_embedding = [0.1, 0.2, 0.3]
    project_id = "test_project"
    index_name = "test_index"
    weights = {"field1": 1.0, "field2": 0.5}
    filters = {"field1": "value1"}
    limit = 5

    # Mock the API response
    mock_response = {
        "results": [
            {"text": "Result 1", "score": 0.95, "metadata": {"field1": "value1"}},
            {"text": "Result 2", "score": 0.89, "metadata": {"field1": "value1"}}
        ]
    }

    # Replace the actual API call with a mock
    mock_connector.query_pipeline = lambda *args, **kwargs: mock_response

    response = mock_connector.query_pipeline(query_embedding, project_id, index_name, weights, filters, limit)
    assert len(response["results"]) == 2
    assert response["results"][0]["text"] == "Result 1"
