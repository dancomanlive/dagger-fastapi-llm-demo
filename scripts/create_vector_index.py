"""
Script for creating a vector index in Qdrant with Superlinked.
This script creates a vector index in Qdrant for use with Superlinked.
"""
import os
import json
import sys
import argparse
from typing import Dict, Any, List

from superlinked import framework as sl

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Create a vector index in Qdrant")
    parser.add_argument("--qdrant_url", required=True, help="URL to the Qdrant instance")
    parser.add_argument("--qdrant_api_key", help="API key for Qdrant (optional)")
    parser.add_argument("--index_name", required=True, help="Name of the index to create")
    parser.add_argument("--schema", required=True, help="Schema definition in JSON format")
    parser.add_argument("--spaces", required=True, help="Vector spaces definition in JSON format")
    parser.add_argument("--fields", help="Fields to include for filtering in JSON format")
    
    args = parser.parse_args()
    
    try:
        # Parse JSON parameters
        schema_def = json.loads(args.schema)
        spaces_def = json.loads(args.spaces)
        fields_def = json.loads(args.fields) if args.fields else None
        
        # Initialize QdrantVectorDatabase
        vector_database = sl.QdrantVectorDatabase(
            args.qdrant_url,
            args.qdrant_api_key,
        )

        # Create schema from definition
        schema = sl.schema(**schema_def)

        # Create spaces
        spaces = []
        for space_config in spaces_def:
            space_type = space_config.pop('type')
            if space_type == 'TextSimilaritySpace':
                field_name = space_config.pop('field')
                spaces.append(sl.TextSimilaritySpace(
                    text=getattr(schema, field_name),
                    **space_config
                ))
            elif space_type == 'NumberSpace':
                field_name = space_config.pop('field')
                spaces.append(sl.NumberSpace(
                    getattr(schema, field_name),
                    **space_config
                ))

        # Create fields list if provided
        fields = None
        if fields_def:
            fields = []
            for field_config in fields_def:
                field_name = field_config['field']
                fields.append(getattr(schema, field_name))

        # Create index
        index = sl.Index(
            spaces=spaces,
            fields=fields
        )

        # Create a source and executor
        source = sl.InteractiveSource(schema)
        executor = sl.InteractiveExecutor(
            sources=[source],
            indices=[index],
            vector_database=vector_database,
        )

        # Register the executor
        sl.SuperlinkedRegistry.register(executor)

        print(json.dumps({
            "status": "success", 
            "message": f"Vector index '{args.index_name}' created successfully"
        }))
        
    except Exception as e:
        print(json.dumps({
            "status": "error", 
            "message": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
