# Temporal Document Processing Service

This service provides Temporal workflows and activities for distributed document processing, including chunking, embedding, and retrieval operations.

## Features

- Document chunking into paragraphs with proper metadata
- Distributed workflow orchestration via Temporal
- Integration with embedding and retrieval services through Temporal activities
- Fault-tolerant workflow execution with retries and timeouts
- Health monitoring workflows
- BDD integration testing with Behave

## Architecture

This service implements a **worker-only architecture** that:
- Registers workflows and activities with the Temporal server
- Coordinates distributed processing across multiple services
- Uses Temporal's task queue routing for cross-service communication
- Provides workflow orchestration without direct HTTP endpoints

## Workflows

### DocumentProcessingWorkflow

Orchestrates document processing through a distributed pipeline:

1. **Chunking**: Splits documents into paragraphs using local `chunk_documents_activity`
2. **Embedding**: Routes chunks to the embedding service via Temporal task queue for vectorization and storage

**Parameters:**
- `documents`: List of documents with `id`, `text`, and optional `metadata`
- `embedding_service_url`: DEPRECATED (ignored - uses Temporal activity routing)

### RetrievalWorkflow

Orchestrates document search and retrieval:

1. **Search**: Routes search queries to the retrieval service via Temporal task queue

**Parameters:**
- `query`: Search query string
- `top_k`: Number of top results to return (default: 10)

### HealthCheckWorkflow

Simple health check workflow for monitoring:

1. **Health Check**: Executes local `health_check_activity` to verify worker health

## Activities

### Local Activities
- `chunk_documents_activity`: Splits documents into paragraphs with metadata
- `health_check_activity`: Returns health status
- `embed_documents_activity`: DEPRECATED (kept for backward compatibility)

### Distributed Activities (via Task Queues)
- `perform_embedding_and_indexing_activity`: Handled by embedding service worker
- `search_documents_activity`: Handled by retrieval service worker

## Deployment

### Worker Mode (Production)

```bash
# Set environment variables
export TEMPORAL_HOST=localhost:7233
export TEMPORAL_NAMESPACE=default
export TEMPORAL_TASK_QUEUE=document-processing-queue
export DOCUMENT_COLLECTION_NAME=document_chunks

# Start the worker
python worker.py
```

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Run BDD integration tests
behave features/ -v

# Run specific test scenarios
behave features/ --tags=@workflow
```

## Client Usage

Workflows are executed by Temporal clients (e.g., from the Gradio service or other applications):

```python
from temporalio.client import Client
from workflows import DocumentProcessingWorkflow

# Connect to Temporal
client = await Client.connect("localhost:7233")

# Start document processing workflow
result = await client.execute_workflow(
    DocumentProcessingWorkflow.run,
    args=[documents],
    id="document-processing-" + workflow_id,
    task_queue="document-processing-queue"
)
```

## Environment Variables

### Temporal Configuration
- `TEMPORAL_HOST` - Temporal server address (default: localhost:7233)
- `TEMPORAL_NAMESPACE` - Temporal namespace (default: default)
- `TEMPORAL_TASK_QUEUE` - Worker task queue name (default: document-processing-queue)

### Service Configuration  
- `DOCUMENT_COLLECTION_NAME` - Vector collection name for embeddings (default: document_chunks)

### Task Queue Routing
- `embedding-task-queue` - Routes embedding activities to embedding service workers
- `retrieval-task-queue` - Routes search activities to retrieval service workers

## Testing

### Unit Tests (pytest)
Focus on workflow orchestration:
```bash
cd services/temporal_service
python -m pytest tests/test_workflows.py -v
```

### Integration Tests (Behave BDD)
Focus on end-to-end workflow behavior:
```bash
cd services/temporal_service
behave features/ -v

# Run specific scenarios
behave features/ --tags=@workflow      # Workflow orchestration
behave features/ --tags=@health        # Health check workflows
behave features/ --tags=@retrieval     # Document retrieval
behave features/ --tags=@activity      # Direct activity testing
```

## Service Dependencies

This service coordinates with:
- **Embedding Service**: Handles vectorization and storage via `embedding-task-queue`
- **Retrieval Service**: Handles document search via `retrieval-task-queue`  
- **Temporal Server**: Provides workflow orchestration and task routing
- **Vector Database**: Accessed indirectly through embedding/retrieval services
