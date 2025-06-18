# Generic Temporal Orchestration Service

This service provides a **generic, configuration-driven** Temporal workflow orchestration system for distributed service coordination. The service can execute any pipeline defined through YAML configuration without requiring code changes.

## 🚀 Key Features

- **Configuration-Driven Pipelines**: Define workflows through YAML configuration
- **Generic Pipeline Execution**: Execute any configured pipeline via `GenericPipelineWorkflow`
- **Dynamic Service Routing**: Route activities to services via configurable task queues
- **Dynamic Activity Discovery**: Activities are discovered automatically from configuration
- **Fault-Tolerant**: Built-in retry policies, timeouts, and error handling
- **Extensible**: Add new pipelines and services without code changes
- **Type-Safe**: Full TypeScript-style type hints and validation

## 🏗️ Architecture

This service implements a **generic orchestrator pattern** that:
- Loads pipeline definitions from `config/services.yaml`
- Routes activities to appropriate services via Temporal task queues
- Provides generic workflow interfaces for any configured pipeline
- Supports local and remote activity execution
- Enables dynamic pipeline composition

## 📋 Workflows

### GenericPipelineWorkflow (NEW)

**The main workflow for generic pipeline execution:**

```python
# Execute any configured pipeline
result = await client.execute_workflow(
    "GenericPipelineWorkflow",
    args=[pipeline_name, input_data],
    id="workflow-id",
    task_queue="document-processing-queue"
)
```

**Examples:**
- `pipeline_name="document_processing"` - Process and embed documents
- `pipeline_name="document_retrieval"` - Search for documents
- `pipeline_name="health_check"` - Health monitoring
- `pipeline_name="custom_pipeline"` - Any pipeline you define in config

## Configuration
- **Purpose**: System health monitoring
- **Now Uses**: `health_check` pipeline from configuration
- **Interface**: Unchanged - returns simple health status

## ⚙️ Configuration

### Service Configuration (`config/services.yaml`)

Define services, activities, and pipelines through YAML configuration:

```yaml
services:
  embedding_service:
    task_queue: "embedding-task-queue"
    activities:
      perform_embedding_and_indexing_activity:
        timeout_minutes: 30
        retry_attempts: 3

  retrieval_service:
    task_queue: "retrieval-task-queue"  
    activities:
      search_documents_activity:
        timeout_minutes: 5
        retry_attempts: 3

  local_activities:
    chunk_documents_activity:
      timeout_minutes: 10
      retry_attempts: 3

pipelines:
  document_processing:
    name: "DocumentProcessingPipeline"
    steps:
      - activity: "chunk_documents_activity"
        type: "local"
        input_transform: "documents"
      - activity: "perform_embedding_and_indexing_activity"
        type: "remote"
        service: "embedding_service"
        input_transform: "chunked_docs_with_collection"

  custom_pipeline:
    name: "CustomPipeline"
    steps:
      - activity: "your_activity"
        type: "remote"
        service: "your_service"
```

### Adding New Pipelines

1. **Add Service** (if needed):
```yaml
services:
  analytics_service:
    task_queue: "analytics-task-queue"
    activities:
      analyze_data_activity:
        timeout_minutes: 15
        retry_attempts: 2
```

2. **Define Pipeline**:
```yaml
pipelines:
  data_analysis:
    name: "DataAnalysisPipeline" 
    steps:
      - activity: "analyze_data_activity"
        type: "remote"
        service: "analytics_service"
        input_transform: "passthrough"
```

3. **Execute Pipeline**:
```python
result = await client.execute_workflow(
    "GenericPipelineWorkflow",
    args=["data_analysis", your_data],
    id="analysis-workflow",
    task_queue="document-processing-queue"
)
```

## 🔧 Activities

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
```

## Client Usage

Workflows are executed by Temporal clients (e.g., from the Gradio service or other applications):

```python
from temporalio.client import Client

# Connect to Temporal
client = await Client.connect("localhost:7233")

# Start generic pipeline workflow
result = await client.start_workflow(
    "GenericPipelineWorkflow",
    args=["document_processing", documents],  # Pipeline name and input
    id="document-processing-" + workflow_id,
    task_queue="document-processing-queue"
)

result = await workflow_handle.result()
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

## Service Dependencies

This service coordinates with:
- **Embedding Service**: Handles vectorization and storage via `embedding-task-queue`
- **Retrieval Service**: Handles document search via `retrieval-task-queue`  
- **Temporal Server**: Provides workflow orchestration and task routing
- **Vector Database**: Accessed indirectly through embedding/retrieval services
