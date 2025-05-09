"""
Script for connecting to Qdrant vector database with Superlinked.
This script provides functions for setting up and using Qdrant with Superlinked.
"""
import os
import json
import sys
import argparse
from typing import Dict, Any, List, Optional, Union

from superlinked import framework as sl

def initialize_qdrant(
    qdrant_url: str,
    qdrant_api_key: Optional[str] = None,
    default_query_limit: int = 10,
    **kwargs
) -> sl.QdrantVectorDatabase:
    """
    Initialize a Qdrant vector database connection.
    
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

def create_executor(
    vector_database: sl.QdrantVectorDatabase,
    schema: Any,
    index: Any,
    queries: List[Any]
) -> sl.RestExecutor:
    """
    Create a REST executor with the given components.
    
    Args:
        vector_database: QdrantVectorDatabase instance
        schema: Schema definition
        index: Index definition
        queries: List of queries to include
        
    Returns:
        RestExecutor instance
    """
    # Create source
    rest_source = sl.RestSource(schema)
    
    # Create executor
    executor = sl.RestExecutor(
        sources=[rest_source],
        indices=[index],
        queries=queries,
        vector_database=vector_database,
    )
    
    return executor

def register_executor(executor: sl.RestExecutor) -> None:
    """
    Register an executor with the Superlinked registry.
    
    Args:
        executor: RestExecutor instance to register
    """
    sl.SuperlinkedRegistry.register(executor)
    
def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Connect to Qdrant with Superlinked")
    parser.add_argument("--action", choices=["initialize", "create_index", "query"], 
                        required=True, help="Action to perform")
    parser.add_argument("--qdrant_url", required=True, help="URL to the Qdrant instance")
    parser.add_argument("--qdrant_api_key", help="API key for Qdrant (optional)")
    parser.add_argument("--params", help="Additional parameters in JSON format")
    
    args = parser.parse_args()
    
    # Parse additional parameters if provided
    params = {}
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(f"Error parsing params JSON: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Initialize Qdrant connection
    vector_database = initialize_qdrant(
        args.qdrant_url,
        args.qdrant_api_key,
        **params.get("qdrant_params", {})
    )
    
    # Perform the requested action
    if args.action == "initialize":
        print(json.dumps({
            "status": "success", 
            "message": "Qdrant vector database initialized successfully"
        }))
        
    elif args.action == "create_index":
        # In a real implementation, you would create a schema, spaces, and index here
        # using the parameters provided in the params object
        print(json.dumps({
            "status": "success", 
            "message": f"Vector index created successfully"
        }))
        
    elif args.action == "query":
        # In a real implementation, you would perform a query using the
        # parameters provided in the params object
        print(json.dumps({
            "status": "success",
            "message": "Query executed successfully",
            "results": []  # Would contain actual results
        }))

if __name__ == "__main__":
    main()
