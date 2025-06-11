# Gradio Chat Service

A web-based chat interface for the RAG (Retrieval-Augmented Generation) pipeline that integrates with Temporal workflows for distributed document processing.

## Features

- **Real-time streaming responses** from OpenAI with RAG context
- **Interactive chat interface** with conversation history
- **Document collection selection** for targeted search
- **Debug information panel** showing retrieved documents and metrics
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

The service uses Temporal's **RetrievalWorkflow** instead of direct HTTP calls:

```python
async def get_context_via_temporal(query: str, collection: str) -> str:
    """Get context using Temporal RetrievalWorkflow"""
    client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
    
    workflow_handle = await client.start_workflow(
        "RetrievalWorkflow",
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

### Integration Tests (Behave BDD)  
Focus on user interaction and workflow behavior:
```bash
cd services/gradio_service
behave features/ -v

# Run specific scenarios
behave features/ --tags=@temporal      # Temporal workflow integration
behave features/ --tags=@ui           # User interface behavior
behave features/ --tags=@error        # Error handling scenarios
```

### Test Categories

**Unit Tests (pytest)**:
- Temporal client integration
- Workflow execution and error handling
- OpenAI API integration
- Configuration and environment handling

**BDD Tests (behave)**:
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
- `behave>=1.2.6` - BDD testing framework

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
2. **Add BDD scenarios** for new user workflows in `features/gradio_temporal_integration.feature`  
3. **Update step definitions** in `features/steps/gradio_temporal_steps.py`
4. **Test both** unit and integration layers before deployment

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Monitor Temporal workflows via the Temporal Web UI at `http://localhost:8080`
