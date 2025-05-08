# RAG Pipeline Module Usage

This document demonstrates how to use the advanced RAG pipeline modules directly in your code, bypassing the API endpoints. This is useful for integrating the RAG functionality into your own applications.

## Direct Module Usage

### Setting Up

First, ensure you have the Dagger client initialized:

```python
import asyncio
import dagger
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def main():
    # Initialize the Dagger client
    async with dagger.Connection() as client:
        # Your RAG pipeline code here
        
if __name__ == "__main__":
    asyncio.run(main())
```

### Document Ingestion

Here's how to ingest a document using the advanced RAG pipeline directly:

```python
from pipelines.rag_pipeline import ingest_document

async def ingest_example(client):
    # Document to ingest
    document = """
    # Dagger Overview
    
    Dagger is a programmable CI/CD engine that runs your pipelines in containers. 
    Dagger allows you to develop your CI/CD pipelines locally and run them anywhere.
    
    ## Key Features
    
    It provides a portable development kit for building CI/CD pipelines with reusable modules.
    This approach enables you to write your pipelines once and run them on any CI/CD platform.
    """
    
    # Ingest the document
    result = await ingest_document(
        client=client,
        text=document,
        document_id="dagger-intro-direct",
        project_id="your-superlinked-project-id",
        index_name="dagger_docs",
        chunk_size=500,
        overlap=100,
        respect_sections=True,  # Respects document section boundaries
        metadata={
            "source": "documentation",
            "topic": "dagger",
            "usage": "direct-module",
            "date": "2025-05-01"
        }
    )
    
    print("Document ingestion result:")
    print(json.dumps(result, indent=2))
```

### Querying the RAG System

Here's how to query the RAG system directly with advanced capabilities:

```python
from pipelines.rag_pipeline import query_rag

async def query_example(client):
    # Query the RAG system
    result = await query_rag(
        client=client,
        query="What is Dagger and how does it work?",
        project_id="your-superlinked-project-id",
        index_name="dagger_docs",
        use_nlq=True,  # Use natural language query processing
        weights={"vector": 0.8, "keyword": 0.2},  # Optional weights for search
        filters={"topic": "dagger"},  # Optional metadata filters
        limit=3,
        model="gpt-4o-mini"
    )
    
    print("\nQuery result:")
    print(f"Query: {result['query']}")
    print(f"Processed query: {result['processed_query']}")
    print(f"Extracted filters: {result['extracted_filters']}")
    print(f"\nResponse: {result['response']}")
    
    # Print citations
    print("\nCitations:")
    for citation in result.get("citations", []):
        chunk_id = citation.get('chunk_id', 'unknown')
        text_snippet = citation['text'][:100] + "..." if len(citation['text']) > 100 else citation['text']
        print(f"- [{chunk_id}]: {text_snippet}")
        print(f"  Metadata: {citation.get('metadata', {})}")
```

### Advanced Usage: Multi-Modal Search

The advanced RAG implementation supports multi-modal search combining vector similarity with keyword matching:

```python
from tools.superlinked_qdrant_connector import weighted_multi_search
from tools.text_embedder import embed_text
import json

async def advanced_search_example(client):
    # Generate embedding for the query
    query = "CI/CD pipelines with container support"
    embedding_result = await embed_text(client, [query])
    embedding_data = json.loads(embedding_result)
    query_embedding = embedding_data.get("embeddings", [[]])[0]
    
    # Perform weighted multi-modal search
    search_result = await weighted_multi_search(
        client=client,
        query_embedding=query_embedding,
        project_id="your-superlinked-project-id",
        index_name="dagger_docs",
        text_query=query,  # Optional text for hybrid search
        weights={
            "vector": 0.7,  # Weight for vector similarity
            "keyword": 0.3   # Weight for keyword matches
        },
        filters={
            "source": "documentation"  # Optional metadata filter
        },
        limit=5
    )
    
    search_data = json.loads(search_result)
    
    # Print search results
    print("\nMulti-modal search results:")
    for i, result in enumerate(search_data.get("results", [])):
        print(f"\nResult {i+1} (Score: {result.get('score', 0):.4f}):")
        print(f"Text: {result.get('text', '')[:150]}...")
        
        # Print metadata excluding common fields
        metadata = {k: v for k, v in result.items() 
                   if k not in ["text", "score", "document_id"]}
        print(f"Metadata: {metadata}")
```
from dotenv import load_dotenv
from pipelines.rag_pipeline import ingest_document, query_rag

# Load environment variables
load_dotenv()

async def main():
    # Initialize the Dagger client
    async with dagger.Connection() as client:
        # Document to ingest
        document = """
        Dagger is a programmable CI/CD engine that runs your pipelines in containers. 
        Dagger allows you to develop your CI/CD pipelines locally and run them anywhere.
        It provides a portable development kit for building CI/CD pipelines with reusable modules.
        """
        
        # Ingest the document
        ingest_result = await ingest_document(
            client=client,
            text=document,
            document_id="dagger-intro-direct",
            project_id="your-superlinked-project-id",
            index_name="default_index",
            metadata={
                "source": "documentation",
                "topic": "dagger",
                "usage": "direct-module"
            }
        )
        
        print("Document ingestion result:")
        print(json.dumps(ingest_result, indent=2))
        
        # Query the RAG system with the advanced version
        query_result = await query_rag(
            client=client,
            query="What is Dagger and how does it work?",
            collection_name="superlinked_your-project-id_default_index",
            limit=3,
            model="gpt-4o-mini"
        )
        
        print("\nQuery result:")
        print(f"Query: {query_result['query']}")
        print(f"\nResponse: {query_result['response']}")
        
        # Print citations
        print("\nCitations:")
        for citation in query_result.get("citations", []):
            chunk_id = citation['chunk_id']
            text_snippet = citation['text'][:100] + "..." if len(citation['text']) > 100 else citation['text']
            print(f"- [{chunk_id}]: {text_snippet}")
            print(f"  Metadata: {citation['metadata']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Using the Individual Components

You can also use the individual components of the RAG pipeline:

### Text Chunking

```python
from tools.text_chunker import chunk_text

async def chunk_example(client):
    text = """
    This is a long document that needs to be split into smaller chunks.
    Chunking is an important part of the RAG pipeline, as it helps ensure
    that the context provided to the LLM is relevant and focused.
    """
    
    chunking_result = await chunk_text(
        client=client,
        text=text,
        chunk_size=100,
        overlap=20
    )
    
    chunks_data = json.loads(chunking_result)
    print(f"Generated {len(chunks_data['chunks'])} chunks")
    print(f"Average chunk size: {chunks_data['avg_chunk_size']:.2f} characters")
```

### Text Embedding

```python
from tools.text_embedder import embed_text

async def embed_example(client):
    chunks = [
        "This is the first chunk of text.",
        "This is the second chunk of text.",
        "This is the third chunk of text."
    ]
    
    embedding_result = await embed_text(
        client=client,
        chunks=chunks
    )
    
    embedding_data = json.loads(embedding_result)
    print(f"Generated {len(embedding_data['embeddings'])} embeddings")
    print(f"Embedding dimensions: {embedding_data['dimensions']}")
```

### Direct Storage in Qdrant

```python
from tools.qdrant_store import store_in_qdrant

async def store_qdrant_example(client, chunks, embeddings):
    storage_result = await store_in_qdrant(
        client=client,
        chunks=chunks,
        embeddings=embeddings,
        collection_name="my_collection",
        metadata={"source": "direct-example"}
    )
    
    storage_data = json.loads(storage_result)
    print(f"Stored {storage_data['points_added']} points in Qdrant collection: {storage_data['collection']}")
```

### Direct Storage in Superlinked with Qdrant

```python
from tools.superlinked_qdrant import store_in_superlinked_with_qdrant

async def store_superlinked_example(client, chunks, embeddings):
    storage_result = await store_in_superlinked_with_qdrant(
        client=client,
        chunks=chunks,
        embeddings=embeddings,
        project_id="your-superlinked-project-id",
        index_name="my_index",
        metadata={"source": "direct-example"}
    )
    
    storage_data = json.loads(storage_result)
    print(f"Stored {storage_data['documents_added']} documents in Superlinked with Qdrant connector")
```

### Retrieval from Qdrant

```python
from tools.qdrant_retriever import retrieve_from_qdrant

async def retrieve_example(client, query_vector):
    retrieval_result = await retrieve_from_qdrant(
        client=client,
        query_vector=query_vector,
        collection_name="my_collection",
        limit=5
    )
    
    retrieval_data = json.loads(retrieval_result)
    print(f"Retrieved {len(retrieval_data['results'])} results from Qdrant")
    
    for i, result in enumerate(retrieval_data['results']):
        print(f"Result {i+1}: Score {result['score']:.4f}")
        print(f"Text: {result['text'][:100]}...")
```

### Response Generation with Citations

```python
from tools.rag_generator import generate_rag_response_with_citations

async def generate_example(client, query, context_chunks, chunk_metadata):
    generation_result = await generate_rag_response_with_citations(
        client=client,
        query=query,
        context_chunks=context_chunks,
        chunk_metadata=chunk_metadata,
        model="gpt-4o-mini"
    )
    
    generation_data = json.loads(generation_result)
    print(f"Response: {generation_data['response']}")
    print(f"Used {generation_data['context_chunks_used']} context chunks")
    
    for citation in generation_data.get('citations', []):
        print(f"Citation: [{citation['chunk_id']}]")
```

## Advanced Use Cases

### Custom Embedding Models

You can modify the `embed_text.py` script to use a different embedding model:

```python
# In scripts/embed_text.py
def get_embeddings(texts):
    from sentence_transformers import SentenceTransformer
    
    # Use a different model
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Generate embeddings
    return model.encode(texts).tolist()
```

### Adding Custom Metadata

Enriching your documents with metadata can improve retrieval:

```python
metadata = {
    "document_id": "unique-doc-id",
    "source": "company-documentation",
    "author": "Engineering Team",
    "department": "DevOps",
    "creation_date": "2025-04-01",
    "version": "1.2.3",
    "tags": ["dagger", "ci-cd", "pipeline", "containers"],
    "relevance_score": 0.95
}

await ingest_document(client, text, document_id, project_id, index_name, metadata=metadata)
```

### Batch Processing

For processing multiple documents:

```python
async def batch_ingest(client, documents, project_id):
    results = []
    
    for doc in documents:
        result = await ingest_document(
            client=client,
            text=doc["text"],
            document_id=doc["id"],
            project_id=project_id,
            metadata=doc.get("metadata", {})
        )
        results.append(result)
    
    return results
```
