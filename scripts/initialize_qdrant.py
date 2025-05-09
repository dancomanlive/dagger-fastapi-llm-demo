"""
Script for initializing a Qdrant vector database with Superlinked.
This script initializes a Qdrant vector database for use with Superlinked.
"""
import os
import json
import sys
import argparse
from typing import Dict, Any

from superlinked import framework as sl

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Initialize a Qdrant vector database")
    parser.add_argument("--qdrant_url", required=True, help="URL to the Qdrant instance")
    parser.add_argument("--qdrant_api_key", help="API key for Qdrant (optional)")
    parser.add_argument("--default_query_limit", type=int, default=10, 
                        help="Maximum number of query results to return")
    parser.add_argument("--params", help="Additional parameters in JSON format")
    
    args = parser.parse_args()
    
    # Parse additional parameters if provided
    extra_params = {}
    if args.params:
        try:
            extra_params = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(f"Error parsing params JSON: {e}", file=sys.stderr)
            sys.exit(1)
    
    try:
        # Initialize QdrantVectorDatabase
        vector_database = sl.QdrantVectorDatabase(
            args.qdrant_url,
            args.qdrant_api_key,
            default_query_limit=args.default_query_limit,
            **extra_params
        )
        
        # Confirm connection
        print(json.dumps({
            "status": "success", 
            "message": "Qdrant vector database initialized successfully"
        }))
        
    except Exception as e:
        print(json.dumps({
            "status": "error", 
            "message": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
