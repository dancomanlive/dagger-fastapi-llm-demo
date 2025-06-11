# Retriever Service

The Retriever Service provides document search and retrieval functionality for the SmartAgent-X7 system. It has been refactored to support both HTTP API endpoints and Temporal workflow activities.

## Features

- Document search functionality via HTTP API
- Temporal activity for workflow-based document retrieval
- Comprehensive test coverage with PyTest
- Asynchronous processing capabilities

## Architecture

### HTTP API
The service provides REST endpoints for document search operations.

### Temporal Integration
The service includes a Temporal worker that registers activities for workflow-based orchestration:

- **Activity**: `search_documents_activity` - Performs document search operations
- **Task Queue**: `retrieval-task-queue`
- **Worker**: Connects to Temporal server and processes activity tasks

## Files Structure

```
retriever_service/
├── main.py                 # HTTP API service
├── activities.py           # Temporal activities
├── worker.py              # Temporal worker setup
├── requirements.txt       # Dependencies
├── tests/
│   ├── __init__.py
│   ├── test_activities.py # Activity tests
│   └── test_worker.py     # Worker tests
└── README.md             # This file
```

## Dependencies

- `temporalio` - Temporal workflow SDK
- `pytest` - Testing framework
- `pytest-mock` - Mock utilities for testing
- `pytest-asyncio` - Async testing support

## Usage

### Running the HTTP Service
```bash
python main.py
```

### Running the Temporal Worker
```bash
python worker.py
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_activities.py -v
python -m pytest tests/test_worker.py -v
```

## Testing

The service includes comprehensive test coverage:

### Activity Tests (`test_activities.py`)
- Function signature validation
- Core search logic testing
- Error handling scenarios
- Empty result handling
- Input validation

### Worker Tests (`test_worker.py`)
- Worker module import verification
- Activity registration validation
- Temporal client configuration
- Task queue setup verification

## Development

This service follows Test-Driven Development (TDD) principles:

1. **RED**: Write failing tests first
2. **GREEN**: Implement minimal code to pass tests
3. **REFACTOR**: Improve code while keeping tests passing

## Integration

The retriever service can be integrated with workflows via Temporal activities:

```python
from temporalio import workflow
from temporalio.worker import Worker

@workflow.defn
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, query: str) -> dict:
        # Call the retrieval activity
        result = await workflow.execute_activity(
            search_documents_activity,
            query,
            start_to_close_timeout=timedelta(seconds=30)
        )
        return result
```

## Future Enhancements

- Enhanced search algorithms
- Caching mechanisms
- Performance monitoring
- Advanced error handling and retry policies
- Integration with additional document sources
