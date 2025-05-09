"""
Superlinked Qdrant Connector Tool.
This module provides a reusable tool for integrating Qdrant with Superlinked.
"""
import os
import dagger
from typing import Dict, Any, Optional, List
import json

from .core import get_tool_base, run_container_and_check, SCRIPTS_DIR

async def initialize_qdrant(
    client: dagger.Client,
    qdrant_url: str,
    qdrant_api_key: Optional[str] = None,
    default_query_limit: int = 10,
    **kwargs: Dict[str, Any]
) -> str:
    """
    Initialize Qdrant vector database for use with Superlinked.
    
    Args:
        client: Dagger client
        qdrant_url: URL to the Qdrant instance (without extra fields)
        qdrant_api_key: API key for Qdrant (optional)
        default_query_limit: Maximum number of query results to return (default: 10)
        **kwargs: Additional parameters to pass to the Qdrant client
        
    Returns:
        String with initialization result
    """
    # Set up container with Python and required packages
    container = get_tool_base(
        client, 
        "python:3.11-slim", 
        SCRIPTS_DIR
    )
    
    container = (
        container
        .with_exec(["pip", "install", "superlinked", "qdrant-client"])
    )
    
    # Prepare parameters for the script
    params = {
        "qdrant_url": qdrant_url,
        "qdrant_api_key": qdrant_api_key,
        "default_query_limit": default_query_limit,
        **kwargs
    }
    
    # Write parameters to a file
    params_json = json.dumps(params)
    
    # Run the script to initialize the Qdrant connection
    result = await run_container_and_check(
        container,
        [
            "python", 
            "scripts/initialize_qdrant.py",
            "--qdrant_url", qdrant_url,
            "--qdrant_api_key", qdrant_api_key or "",
            "--default_query_limit", str(default_query_limit),
            "--params", params_json
        ]
    )
    
    return result

async def create_vector_index(
    client: dagger.Client,
    qdrant_url: str,
    index_name: str,
    schema_definition: Dict[str, Any],
    spaces: List[Dict[str, Any]],
    fields: Optional[List[Dict[str, Any]]] = None,
    qdrant_api_key: Optional[str] = None,
) -> str:
    """
    Create a vector index in Qdrant using Superlinked framework.
    
    Args:
        client: Dagger client
        qdrant_url: URL to the Qdrant instance
        index_name: Name of the index to create
        schema_definition: Schema definition for the index
        spaces: Vector spaces to include in the index
        fields: Fields to include for filtering (optional)
        qdrant_api_key: API key for Qdrant (optional)
        
    Returns:
        String with the result of the index creation
    """
    # Set up container with Python and required packages
    container = get_tool_base(
        client, 
        "python:3.11-slim", 
        SCRIPTS_DIR
    )
    
    container = (
        container
        .with_exec(["pip", "install", "superlinked", "qdrant-client"])
    )
    
    # Prepare parameters for the script
    params = {
        "qdrant_url": qdrant_url,
        "qdrant_api_key": qdrant_api_key,
        "index_name": index_name,
        "schema_definition": schema_definition,
        "spaces": spaces,
        "fields": fields
    }
    
    # Write parameters to a file
    params_json = json.dumps(params)
    
    # Run the script to create the index
    result = await run_container_and_check(
        container,
        [
            "python", 
            "scripts/create_vector_index.py",
            "--qdrant_url", qdrant_url,
            "--qdrant_api_key", qdrant_api_key or "",
            "--index_name", index_name,
            "--schema", json.dumps(schema_definition),
            "--spaces", json.dumps(spaces),
            "--fields", json.dumps(fields) if fields else ""
        ]
    )
    
    return result

async def query_qdrant(
    client: dagger.Client,
    qdrant_url: str,
    query_text: str,
    index_name: str,
    weights: Optional[Dict[str, float]] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    qdrant_api_key: Optional[str] = None,
) -> str:
    """
    Query the Qdrant vector database using Superlinked framework.
    
    Args:
        client: Dagger client
        qdrant_url: URL to the Qdrant instance
        query_text: Text to search for
        index_name: Name of the index to query
        weights: Weights to apply to different spaces (optional)
        filters: Filters to apply to the query (optional)
        limit: Maximum number of results to return
        qdrant_api_key: API key for Qdrant (optional)
        
    Returns:
        String with query results in JSON format
    """
    # Set up container with Python and required packages
    container = get_tool_base(
        client, 
        "python:3.11-slim", 
        SCRIPTS_DIR
    )
    
    container = (
        container
        .with_exec(["pip", "install", "superlinked", "qdrant-client"])
    )
    
    # Prepare parameters for the script
    params = {
        "qdrant_url": qdrant_url,
        "qdrant_api_key": qdrant_api_key,
        "query_text": query_text,
        "index_name": index_name,
        "weights": weights or {},
        "filters": filters or {},
        "limit": limit
    }
    
    # Write parameters to a file
    params_json = json.dumps(params)
    
    # Run the script to query the index
    result = await run_container_and_check(
        container,
        [
            "python", 
            "scripts/query_qdrant.py",
            "--qdrant_url", qdrant_url,
            "--qdrant_api_key", qdrant_api_key or "",
            "--query_text", query_text,
            "--index_name", index_name,
            "--weights", json.dumps(weights) if weights else "{}",
            "--filters", json.dumps(filters) if filters else "{}",
            "--limit", str(limit)
        ]
    )
    
    return result
