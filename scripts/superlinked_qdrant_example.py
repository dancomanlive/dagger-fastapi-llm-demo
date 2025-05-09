"""
Example script demonstrating Superlinked with Qdrant integration.
This script provides a simple example of how to use Superlinked with Qdrant in this project.
"""
import os
import json
import asyncio
import dagger
from dotenv import load_dotenv
import sys

from pipelines.rag_pipeline import RagPipeline
from utils.superlinked_utils import create_qdrant_connection

async def main():
    """Run the example script."""
    # Load environment variables
    load_dotenv()
    
    # Configure Qdrant
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "")  # Empty for local docker
    
    print(f"Connecting to Qdrant at: {qdrant_url}")
    
    # Initialize Dagger
    config = dagger.Config(log_output=sys.stdout)
    
    async with dagger.Connection(config) as client:
        # Create RAG pipeline
        rag = RagPipeline(
            client,
            qdrant_url,
            qdrant_api_key
        )
        
        # Initialize the pipeline
        init_result = await rag.initialize()
        print(f"Initialization result: {json.dumps(init_result, indent=2)}")
        
        # Ingest a sample document
        ingest_result = await rag.ingest_document(
            text="Qdrant is a vector database & vector similarity search engine. " + 
                "It deploys as an API service providing search for the nearest vectors " + 
                "using dot product, cosine, or Euclidean distance.",
            document_id="qdrant-info-1",
            metadata={"source": "example", "category": "vector-db"}
        )
        print(f"Ingestion result: {json.dumps(ingest_result, indent=2)}")
        
        # Perform a query
        query_result = await rag.process_query(
            query_text="What is Qdrant?",
            limit=3
        )
        print(f"Query result: {json.dumps(query_result, indent=2)}")
        
    # You can also use the utility function directly if needed
    # This doesn't use Dagger containers
    direct_vector_db = create_qdrant_connection(
        qdrant_url,
        qdrant_api_key
    )
    print(f"Direct initialization: Vector database instance created")

if __name__ == "__main__":
    import sys
    asyncio.run(main())
