# End-to-End Testing for Pure Temporal Architecture

## Overview

The SmartÆgent X-7 system now uses a pure Temporal-based architecture for orchestrating document processing and retrieval workflows. This document explains how to run end-to-end tests to validate the complete pipeline.

## Architecture

The system consists of these key components:

- **Gradio Chat Interface** (`gradio-chat`): User-facing chat interface
- **Temporal Worker** (`temporal-worker`): Orchestrates workflows and activities
- **Embedding Service** (`embedding-service`): Provides document embedding activities
- **Retriever Service** (`retriever-service`): Provides document search activities
- **Qdrant Vector DB** (`qdrant`): Stores document vectors
- **Temporal Server** (`temporal`): Workflow execution engine
- **PostgreSQL** (`postgresql`): Temporal persistence
- **Temporal Web UI** (`temporal-ui`): Workflow monitoring interface

## Core Workflows

1. **DocumentProcessingWorkflow**: Processes documents through chunking and embedding
2. **RetrievalWorkflow**: Searches for relevant documents based on queries
3. **HealthCheckWorkflow**: Validates system health

## Running E2E Tests

### Quick Start

```bash
# Start all services and run automated tests
./scripts/e2e_test.sh
```

### Manual Testing

1. **Start Services**:
   ```bash
   docker-compose up -d
   ```

2. **Run Temporal Workflow Tests**:
   ```bash
   python tests/test_temporal_e2e.py
   ```

3. **Monitor via Web UI**:
   - Temporal: http://localhost:8081
   - Gradio Chat: http://localhost:7860

### Test Script Features

The `tests/test_temporal_e2e.py` script validates:

- ✅ Temporal connectivity
- ✅ HealthCheckWorkflow execution
- ✅ DocumentProcessingWorkflow with test document
- ✅ RetrievalWorkflow with search queries
- ✅ End-to-end pipeline validation
- ✅ Relevance checking of search results

## Environment Variables

```bash
# Required for testing
export TEMPORAL_HOST="localhost:7233"
export TEMPORAL_NAMESPACE="default"
export TEST_DOCUMENT_COLLECTION_NAME="test-document-chunks"
```

## Troubleshooting

### Services Not Starting
```bash
# Check container status
docker-compose ps

# View service logs
docker-compose logs -f [service-name]
```

### Workflow Failures
- Check Temporal Web UI at http://localhost:8081
- Look for worker registration and activity execution logs
- Ensure all services are healthy before running tests

### Test Collection Cleanup
```bash
curl -X DELETE http://localhost:6333/collections/test-document-chunks
```

## Architecture Benefits

- **Pure Temporal Orchestration**: No HTTP service-to-service calls
- **Reliable Workflows**: Built-in retry policies and error handling
- **Scalable**: Workers can be scaled independently
- **Observable**: Complete workflow visibility via Temporal Web UI
- **Testable**: Isolated workflow testing without service dependencies

## Service Dependencies

```
Gradio → Temporal Workflows → Activities (Embedding + Retrieval)
                                ↓
                         Qdrant Vector DB
```

All inter-service communication happens through Temporal activities, eliminating the need for HTTP service mesh complexity.
