# RAG Pipeline Usage Examples

This document provides examples of how to use the Retrieval-Augmented Generation (RAG) pipeline implemented with Dagger, Qdrant, and Superlinked in this project.

## Prerequisites

Before using the RAG pipeline, ensure that you have:

1. Set up the required environment variables in your `.env` file:
   ```
   OPENAI_API_KEY="your-openai-api-key"
   LLM_MODEL="gpt-4o-mini"
   QDRANT_URL="http://localhost:6333"
   QDRANT_API_KEY=""  # Leave empty for local Qdrant
   SUPERLINKED_URL="https://api.superlinked.com"
   SUPERLINKED_API_KEY="your-superlinked-api-key"
   ```

2. Started the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Ingesting Documents

Before you can query the RAG system, you need to ingest documents. Here's how to do it:

### Using Python

```python
import requests
import json

# Document to ingest
document = """
Dagger is a programmable CI/CD engine that runs your pipelines in containers. 
Dagger allows you to develop your CI/CD pipelines locally and run them anywhere.
It provides a portable development kit for building CI/CD pipelines with reusable modules.
"""

# Ingest the document
response = requests.post(
    "http://localhost:8000/rag/ingest",
    json={
        "text": document,
        "document_id": "dagger-intro-doc",
        "project_id": "your-superlinked-project-id",  # Replace with your actual project ID
        "index_name": "dagger_docs",  # Optional, defaults to "default_index"
        "chunk_size": 500,  # Optional, defaults to 1000
        "overlap": 100,  # Optional, defaults to 200
        "respect_sections": True,  # Optional, defaults to True
        "metadata": {
            "source": "documentation",
            "topic": "dagger",
            "author": "Dagger Team",
            "date": "2025-05-01"
        }
    }
)

# Check the results
result = response.json()
print(json.dumps(result, indent=2))
```

### Using cURL

```bash
curl -X POST http://localhost:8000/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Dagger is a programmable CI/CD engine that runs your pipelines in containers. Dagger allows you to develop your CI/CD pipelines locally and run them anywhere.",
    "document_id": "dagger-intro-doc",
    "project_id": "your-superlinked-project-id",
    "index_name": "dagger_docs",
    "respect_sections": true,
    "metadata": {
      "source": "documentation",
      "topic": "dagger"
    }
  }'
```

## Querying the RAG System

Once you've ingested documents, you can query the system to get responses based on the stored knowledge:

### Using Python

```python
import requests
import json

# Query the RAG system
response = requests.post(
    "http://localhost:8000/rag/query",
    json={
        "query": "What is Dagger and what can I use it for?",
        "project_id": "your-superlinked-project-id",  # Your Superlinked project ID
        "index_name": "dagger_docs",  # The index name you used when ingesting
        "use_nlq": True,  # Use natural language query processing
        "weights": {  # Optional weights for multi-modal search
            "vector": 0.8,
            "keyword": 0.2
        },
        "filters": {  # Optional metadata filters
            "topic": "dagger"
        },
        "limit": 3,  # Number of chunks to retrieve
        "model": "gpt-4o-mini"  # Optionally specify the model to use
    }
)

# Process the response
result = response.json()["result"]

# Print the query and response
print(f"Query: {result['query']}")
print(f"\nResponse: {result['response']}")

# Print citations
print("\nCitations:")
for citation in result.get("citations", []):
    chunk_id = citation['chunk_id']
    text_snippet = citation['text'][:100] + "..." if len(citation['text']) > 100 else citation['text']
    print(f"- [{chunk_id}]: {text_snippet}")
    print(f"  Metadata: {citation['metadata']}")
```

### Using cURL

```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Dagger and what can I use it for?",
    "collection_name": "superlinked_your-project-id_default_index",
    "limit": 3
  }'
```

## Example Response

Here's what a typical response from the query endpoint looks like:

```json
{
  "result": {
    "status": "success",
    "query": "What is Dagger and what can I use it for?",
    "response": "Dagger is a programmable CI/CD engine that runs your pipelines in containers [dagger-intro-doc:0]. You can use it to develop your CI/CD pipelines locally and then run them anywhere [dagger-intro-doc:0]. It provides a portable development kit for building CI/CD pipelines with reusable modules [dagger-intro-doc:0].",
    "context_chunks": [
      "Dagger is a programmable CI/CD engine that runs your pipelines in containers. Dagger allows you to develop your CI/CD pipelines locally and run them anywhere. It provides a portable development kit for building CI/CD pipelines with reusable modules."
    ],
    "citations": [
      {
        "chunk_id": "dagger-intro-doc:0",
        "chunk_index": 0,
        "text": "Dagger is a programmable CI/CD engine that runs your pipelines in containers. Dagger allows you to develop your CI/CD pipelines locally and run them anywhere. It provides a portable development kit for building CI/CD pipelines with reusable modules.",
        "metadata": {
          "document_id": "dagger-intro-doc",
          "source": "documentation",
          "topic": "dagger",
          "author": "Dagger Team",
          "index": 0
        }
      }
    ]
  }
}
```

## Citations

The citations in the response allow you to:
1. Verify the source of information used in the response
2. Check if the model is faithfully using the provided context
3. Trace back to original documents for more information
4. Test the accuracy of the RAG system

## Advanced Usage

### Customizing Chunk Size

You can customize the chunking parameters when ingesting documents:

```python
response = requests.post(
    "http://localhost:8000/rag/ingest",
    json={
        "text": long_document,
        "document_id": "dagger-docs",
        "project_id": "your-superlinked-project-id",
        "chunk_size": 500,  # Smaller chunks
        "overlap": 100      # Overlap between chunks
    }
)
```

### Using Different Models

You can specify different LLM models for response generation:

```python
response = requests.post(
    "http://localhost:8000/rag/query",
    json={
        "query": "Explain how to use Dagger with GitHub Actions",
        "model": "gpt-4o"  # Use a more powerful model
    }
)
```

## References

- [Dagger Documentation](https://docs.dagger.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Superlinked Documentation](https://docs.superlinked.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
