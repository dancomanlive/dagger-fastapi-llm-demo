# Temporal Document Processing Service

This service provides Temporal workflows for document processing, including chunking and embedding operations.

## Features

- Document chunking into paragraphs
- Integration with embedding service for vectorization
- Fault-tolerant workflow execution with retries
- HTTP API for workflow management
- Health monitoring

## Workflows

### DocumentProcessingWorkflow

Processes documents through a two-step pipeline:

1. **Chunking**: Splits documents into paragraphs for better processing
2. **Embedding**: Sends chunks to the embedding service for vectorization and storage

## API Endpoints

- `POST /process-documents` - Start a document processing workflow
- `GET /workflow/{workflow_id}/status` - Get workflow status
- `GET /workflow/{workflow_id}/result` - Get workflow result (blocking)
- `GET /health` - Health check

## Environment Variables

- `TEMPORAL_HOST` - Temporal server address (default: localhost:7233)
- `TEMPORAL_NAMESPACE` - Temporal namespace (default: default)
- `TEMPORAL_TASK_QUEUE` - Task queue name (default: document-processing-queue)
- `EMBEDDING_SERVICE_URL` - Embedding service URL (default: http://embedding-service:8000)

## Usage

### Start a workflow

```bash
curl -X POST "http://localhost:8003/process-documents" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "doc1",
        "text": "This is a sample document with multiple paragraphs.\n\nThis is the second paragraph that will be processed separately.",
        "metadata": {"source": "test"}
      }
    ]
  }'
```

### Check workflow status

```bash
curl "http://localhost:8003/workflow/{workflow_id}/status"
```
