"""
Utility functions for working with Superlinked and Qdrant.
This module provides reusable functions for interacting with Superlinked and Qdrant.
"""
from typing import Optional

from superlinked import framework as sl

def create_qdrant_connection(
    qdrant_url: str,
    qdrant_api_key: Optional[str] = None,
    default_query_limit: int = 10,
    **kwargs
) -> sl.QdrantVectorDatabase:
    """
    Create a Qdrant vector database connection.
    
    Args:
        qdrant_url: URL to the Qdrant instance (without extra fields)
        qdrant_api_key: API key for authentication (optional)
        default_query_limit: Maximum number of query results returned (default: 10)
        **kwargs: Additional parameters for the Qdrant client
        
    Returns:
        QdrantVectorDatabase instance
    """
    # Create and return the vector database connection
    vector_database = sl.QdrantVectorDatabase(
        qdrant_url,
        qdrant_api_key,
        default_query_limit=default_query_limit,
        **kwargs
    )
    
    return vector_database
