# Embedding Service Tests

This directory contains comprehensive tests for the embedding service functionality. The tests ensure that the service can properly embed documents and store them in a vector database using Temporal activities.

## Test Structure

```
tests/
├── __init__.py          # Makes tests a Python package
├── conftest.py          # Shared test configuration and fixtures
├── test_activities.py   # Tests for document embedding and indexing
└── test_worker.py       # Tests for Temporal worker functionality
```

## Test Files Overview

### `test_activities.py` - Document Embedding Tests

Tests the core functionality of embedding documents and storing them in Qdrant vector database.

**What it tests:**
- **Document Processing**: Converting text documents into vector embeddings
- **Vector Storage**: Storing embeddings with metadata in Qdrant collections
- **Collection Management**: Creating collections if they don't exist
- **Data Validation**: Ensuring proper document structure and content preservation
- **Error Handling**: Graceful handling of embedding and storage failures

**Key test scenarios:**
- Basic activity interface and function signature
- Full embedding pipeline with mocked Qdrant client
- Point creation with correct vector and payload structure
- Resource cleanup (closing database connections)

### `test_worker.py` - Temporal Worker Tests

Tests the Temporal worker that runs the embedding activities.

**What it tests:**
- **Worker Registration**: Proper registration of embedding activities with Temporal
- **Task Queue Configuration**: Correct setup of task queues for activity execution
- **Connection Handling**: Establishing connections to Temporal server
- **Error Recovery**: Handling connection failures and worker errors
- **Service Configuration**: Validating worker settings and constants

**Key test scenarios:**
- Worker starts and registers activities correctly
- Task queue names and configuration are properly set
- Connection errors are handled gracefully
- Worker can be stopped and restarted

## Shared Test Infrastructure

### `conftest.py` - Test Configuration

Provides shared fixtures and configuration for all tests:

- **`sample_documents`**: Mock document data for testing embedding operations
- **`sample_collection_name`**: Test collection name to avoid conflicts with production data
- **Path setup**: Ensures proper import paths for test modules

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_activities.py
pytest tests/test_worker.py

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=activities --cov=worker
```

## Test Features

### Mocking Strategy
- **External Dependencies**: All external services (Qdrant, Temporal) are mocked
- **Async Operations**: Proper handling of async/await patterns in tests
- **Resource Isolation**: Tests don't depend on external infrastructure

### Data Safety
- **Test Isolation**: Each test uses fresh mock data
- **No Side Effects**: Tests don't modify production data or configurations
- **Clean State**: Tests clean up after themselves

### Coverage Areas
- ✅ **Happy Path**: Normal operation scenarios
- ✅ **Error Conditions**: Network failures, invalid data, connection issues
- ✅ **Edge Cases**: Empty documents, malformed input, resource limits
- ✅ **Configuration**: Environment variables, settings validation

## Understanding the Tests

The tests are designed to verify that:

1. **Documents can be reliably converted to embeddings** - Essential for search functionality
2. **Vector data is stored correctly** - Ensures search results will be accurate
3. **The service can handle failures gracefully** - Important for production reliability
4. **Worker processes can be managed** - Critical for scaling and deployment

Each test is focused on a specific aspect of functionality and includes clear documentation about what it validates and why that validation matters for the overall system.
