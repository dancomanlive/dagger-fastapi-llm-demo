# RAG Chat Service - Modular Architecture

A clean, modular RAG (Retrieval-Augmented Generation) chat interface built with Gradio, designed for easy integration into larger applications.

## Architecture

The service is now organized into separate, focused modules with clean separation of concerns.

## Features

- **Modular Design**: Separated business logic from UI components
- **Real-time streaming responses** from OpenAI with RAG context
- **Interactive chat interface** with conversation history
- **Document collection selection** for targeted search
- **Comprehensive metrics display** showing all retrieval information
- **Retrieved documents panel** with scores and content
- **Easy integration** into larger applications
- **Temporal workflow integration** for distributed document retrieval
- **Response metrics and settings** configuration
- **Docker-ready** microservice architecture

## Architecture

The Gradio service provides a **web interface** that:
- Handles user chat interactions through a responsive UI
- Integrates with **Temporal workflows** for document retrieval (replacing direct HTTP calls)
- Streams AI responses using OpenAI's chat completion API
- Provides real-time debug information and system status
- Manages multiple document collections and user settings

## Temporal Integration

### Document Retrieval via Workflows

The service uses Temporal's **GenericPipelineWorkflow** with the `document_retrieval` pipeline instead of direct HTTP calls:

```python
async def get_context_via_temporal(query: str, collection: str) -> str:
    """Get context using GenericPipelineWorkflow with document_retrieval pipeline"""
    client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
    
    workflow_handle = await client.start_workflow(
        "GenericPipelineWorkflow",
        args=["document_retrieval", {"query": query, "top_k": 5}],
        args=[query, 5],  # query and top_k
        id=f"gradio-retrieval-{timestamp}",
        task_queue="workflow-task-queue"
    )
    
    result = await workflow_handle.result()
    return format_search_results(result)
```

### Benefits of Temporal Integration
- **Fault tolerance**: Automatic retries and error handling
- **Observability**: Full workflow execution visibility  
- **Scalability**: Distributed processing across service workers
- **Consistency**: Unified orchestration with other system components

## User Interface

The Gradio service provides a web interface at `http://localhost:7860` with:

- **Chat Interface**: Real-time conversation with streaming responses
- **Collection Selector**: Choose document collections for context retrieval
- **Debug Panel**: View retrieved documents, response times, and system status
- **Settings Panel**: Configure OpenAI parameters (temperature, max_tokens)
- **System Status**: Real-time Temporal connectivity and service health

## Environment Variables

### OpenAI Configuration
- `OPENAI_API_KEY` - OpenAI API key for chat completions (required)

### Temporal Configuration  
- `TEMPORAL_HOST` - Temporal server address (default: localhost:7233)
- `TEMPORAL_NAMESPACE` - Temporal namespace (default: default)

### Collection Configuration
- `DOCUMENT_COLLECTION_NAME` - Default document collection name (default: document_chunks)

### Legacy Configuration (Deprecated)
- `FASTAPI_SERVICE_URL` - Legacy FastAPI service URL (no longer used)
- `RETRIEVER_SERVICE_URL` - Legacy retriever service URL (replaced by Temporal workflows)

## Deployment

### Production Deployment

```bash
# Set environment variables
export OPENAI_API_KEY=your_openai_api_key
export TEMPORAL_HOST=localhost:7233
export TEMPORAL_NAMESPACE=default
export DOCUMENT_COLLECTION_NAME=document_chunks

# Start the service
python main.py
```

### Docker Deployment

The service is part of the Docker Compose stack:

```bash
docker-compose up gradio-chat
```

Access the chat interface at: http://localhost:7860

## Testing

### Unit Tests (pytest)
Focus on Temporal integration and core functionality:
```bash
cd services/gradio_service
python -m pytest tests/test_temporal_integration.py -v
```

### Test Categories

**Unit Tests (pytest)**:
- Temporal client integration
- Workflow execution and error handling
- OpenAI API integration
- Configuration and environment handling
- User query submission through Gradio interface
- Multi-user concurrent access scenarios
- Collection selection and search behavior  
- Graceful error handling and user feedback
- System status and connectivity monitoring

## Dependencies

### Core Dependencies
- `gradio>=4.0.0` - Web interface framework
- `openai>=1.0.0` - OpenAI API client for chat completions
- `temporalio>=1.0.0` - Temporal workflow client for distributed processing

### Testing Dependencies  
- `pytest>=7.0.0` - Unit testing framework
- `pytest-asyncio>=0.21.0` - Async testing support
- `pytest-mock>=3.10.0` - Mocking utilities

## Service Dependencies

This service integrates with:
- **Temporal Service**: Provides document processing and retrieval workflows
- **Embedding Service**: Handles document vectorization (via Temporal workflows)
- **Retrieval Service**: Handles document search (via Temporal workflows)
- **OpenAI API**: Provides chat completion and streaming responses
- **Temporal Server**: Orchestrates distributed workflow execution

## Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
export OPENAI_API_KEY=your_api_key
export TEMPORAL_HOST=localhost:7233

# Run the application
python main.py
```

### Adding New Features

When extending the service:

1. **Add unit tests** for new Temporal integrations in `tests/test_temporal_integration.py`
2. **Test thoroughly** before deployment

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Monitor Temporal workflows via the Temporal Web UI at `http://localhost:8080`
