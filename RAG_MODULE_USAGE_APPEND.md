"""
Natural Language Query Processing

You can also use the natural language query processing component separately:

```python
from tools.superlinked_qdrant_connector import process_natural_language_query
import json

async def nlq_example(client):
    # Process a natural language query
    queries = [
        "Find me documents about Dagger written after January 2025",
        "Show me technical information about CI/CD pipelines from the documentation",
        "What are the key features of Dagger mentioned in official sources?"
    ]
    
    for query in queries:
        nlq_result = await process_natural_language_query(
            client=client,
            query=query,
            model="gpt-4o-mini"
        )
        
        nlq_data = json.loads(nlq_result)
        
        print(f"\nOriginal query: {query}")
        print(f"Core query: {nlq_data.get('core_query', '')}")
        print(f"Extracted filters: {nlq_data.get('filters', {})}")
```

### Complete Example

```python
import asyncio
import dagger
import json
import os
from dotenv import load_dotenv

# Import advanced RAG modules
from pipelines.rag_pipeline import ingest_document, query_rag
from tools.text_chunker_advanced import chunk_text
from tools.superlinked_qdrant_connector import weighted_multi_search, process_natural_language_query

# Load environment variables
load_dotenv()

async def main():
    # Initialize the Dagger client
    async with dagger.Connection() as client:
        print("Connected to Dagger")
        
        # Configuration
        project_id = "your-superlinked-project-id"  # Replace with your actual project ID
        index_name = "rag_demo"
        
        # Example document
        document = """
        # Dagger - The Programmable CI/CD Engine
        
        ## Introduction
        
        Dagger is a programmable CI/CD engine that runs your pipelines in containers. 
        It allows you to develop your CI/CD pipelines locally and run them anywhere.
        
        ## Key Features
        
        - **Portability**: Write once, run anywhere - works with any CI/CD platform
        - **Programmability**: Use real programming languages instead of YAML
        - **Container-native**: All operations run in containers for consistency
        - **Caching**: Smart caching system that speeds up your pipelines
        
        ## Use Cases
        
        Dagger is ideal for teams looking to standardize their CI/CD workflows across
        different environments and platforms. It's particularly useful for complex
        projects with multiple services and dependencies.
        """
        
        # 1. Ingest document
        print("\n\n=== DOCUMENT INGESTION ===\n")
        ingest_result = await ingest_document(
            client=client,
            text=document,
            document_id="dagger-overview",
            project_id=project_id,
            index_name=index_name,
            chunk_size=500,
            overlap=100,
            respect_sections=True,
            metadata={
                "source": "documentation",
                "topic": "dagger",
                "date": "2025-05-01"
            }
        )
        
        print("Document ingestion result:")
        print(json.dumps(ingest_result, indent=2))
        
        # 2. Query the RAG system
        print("\n\n=== RAG QUERY ===\n")
        query = "What are the main benefits of using Dagger for CI/CD?"
        
        query_result = await query_rag(
            client=client,
            query=query,
            project_id=project_id,
            index_name=index_name,
            use_nlq=True,
            weights={"vector": 0.8, "keyword": 0.2},
            limit=3,
            model="gpt-4o-mini"
        )
        
        print(f"Query: {query}")
        print(f"\nResponse: {query_result.get('response', '')}")
        
        # Print citations
        print("\nCitations:")
        for citation in query_result.get("citations", []):
            print(f"- {citation}")
        
        # 3. Demonstrate natural language query processing
        print("\n\n=== NATURAL LANGUAGE QUERY PROCESSING ===\n")
        complex_query = "Find me information about container-native CI/CD in the documentation"
        
        nlq_result = await process_natural_language_query(
            client=client,
            query=complex_query,
            model="gpt-4o-mini"
        )
        
        nlq_data = json.loads(nlq_result)
        
        print(f"Original query: {complex_query}")
        print(f"Processed query: {nlq_data.get('core_query', '')}")
        print(f"Extracted filters: {nlq_data.get('filters', {})}")
        
        # 4. Demonstrate weighted multi-search
        # Not demonstrated here to keep example concise, but follows the pattern shown earlier

if __name__ == "__main__":
    asyncio.run(main())
```

## Using Individual Components

You can also use individual components of the RAG pipeline for more granular control:

### Advanced Text Chunking

```python
from tools.text_chunker_advanced import chunk_text
import json

async def chunking_example(client):
    # Document to chunk
    document = """
    # Dagger Documentation
    
    ## Getting Started
    
    To get started with Dagger, you'll need to install the Dagger CLI.
    Follow these steps to install and set up Dagger.
    
    ## Core Concepts
    
    Dagger operates on a few core concepts:
    - Containers
    - CI/CD Pipelines
    - Caching
    
    ## Best Practices
    
    When working with Dagger, consider these best practices...
    """
    
    # Chunk the document
    chunking_result = await chunk_text(
        client=client,
        text=document,
        chunk_size=300,
        overlap=50,
        respect_sections=True,
        document_metadata={"document_type": "guide", "topic": "dagger"}
    )
    
    chunking_data = json.loads(chunking_result)
    
    print("Chunking result:")
    print(f"Total chunks: {chunking_data.get('count', 0)}")
    
    # Print each chunk with its metadata
    for i, (chunk, metadata) in enumerate(zip(
            chunking_data.get("chunks", []), 
            chunking_data.get("metadata", [])
        )):
        print(f"\nChunk {i+1}:")
        print(f"Text: {chunk[:100]}...")
        print(f"Metadata: {metadata}")
```
