# RAG Implementation with Superlinked and Qdrant

This document provides detailed information on how we've implemented Retrieval-Augmented Generation (RAG) in this project using Superlinked and Qdrant.

## Architecture

Our RAG implementation follows a modular, containerized approach using Dagger for execution:

1. **Text Processing** - Documents are chunked into manageable segments
2. **Vector Embedding** - Text segments are converted to vector embeddings
3. **Storage** - Embeddings and metadata are stored in Qdrant via Superlinked
4. **Retrieval** - Semantic search retrieves the most relevant information
5. **Generation** - LLM generates responses using retrieved context

## Superlinked + Qdrant Integration

### Configuration

To use Superlinked with Qdrant, we've implemented the following:

```python
from superlinked import framework as sl

# Initialize the vector database
vector_database = sl.QdrantVectorDatabase(
    "<qdrant_url>",  # URL to Qdrant instance
    "<api_key>",     # Optional API key (leave empty for local deployment)
    default_query_limit=10  # Max query results (optional)
)

# Pass to executor
executor = sl.RestExecutor(
    sources=[source],
    indices=[index],
    queries=[query],
    vector_database=vector_database
)
```

For our local Docker deployment, Qdrant doesn't require authentication, so we leave the API key empty. The Qdrant URL is set to `http://qdrant:6333` which points to the Qdrant container defined in our docker-compose.yml file.

### Core Components

1. **Schema Definition** - Defines the document structure and fields
2. **Vector Spaces** - Maps document fields to vector embeddings
3. **Index Creation** - Combines spaces for multi-modal search
4. **Query Creation** - Defines search parameters and weights

## API Endpoints

The following endpoints are available for interacting with the RAG system:

### Document Ingestion

```
POST /rag/ingest
Content-Type: application/json

{
  "text": "Document text content",
  "document_id": "unique_id",
  "project_id": "project_123",
  "index_name": "default_index",
  "chunk_size": 1000,
  "overlap": 200,
  "respect_sections": true,
  "metadata": {
    "author": "John Doe",
    "category": "documentation"
  }
}
```

### Query Processing

```
POST /rag/query
Content-Type: application/json

{
  "query": "What is Retrieval-Augmented Generation?",
  "project_id": "project_123",
  "index_name": "default_index",
  "use_nlq": true,
  "weights": {
    "text": 1.0
  },
  "filters": {
    "metadata.category": "documentation"
  },
  "limit": 5,
  "model": "gpt-4o"
}
```

## Implementation Details

Our implementation leverages the full power of the Superlinked framework:

1. **Multi-modal Search** - Combines text embeddings with numeric and categorical data
2. **Natural Language Querying** - Parses natural language into structured search parameters
3. **Score Weights** - Adjustable weights for different vector spaces at query time
4. **Metadata Filtering** - Hard filtering based on document metadata

## Environment Variables

The integration uses the following environment variables:

- `QDRANT_URL` - URL to the Qdrant instance (default: http://qdrant:6333 in Docker)
- `QDRANT_API_KEY` - API key for Qdrant (optional, leave empty for local Docker deployment)
- `OPENAI_API_KEY` - Required for LLM integration
- `LLM_MODEL` - Default model to use (default: gpt-4o)

## Local Development

For local development, ensure the Qdrant container is running. Our docker-compose.yml file includes the necessary configuration for Qdrant:

```yaml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
    - "6334:6334"
  volumes:
    - qdrant-data:/qdrant/storage
  networks:
    - dagger-net
```

## Implementation Patterns

Our RAG implementation follows several best practices:

1. **Builder + Executor Pattern** - Separate component creation from execution
2. **Containerized Functions** - Each processing step runs in isolated containers
3. **Non-persistent Storage** - Vector database runs in Docker with minimal configuration
4. **Functional Approach** - Pure functions create and execute containers
5. **Standardized I/O Contracts** - Well-defined input/output interfaces for all components
