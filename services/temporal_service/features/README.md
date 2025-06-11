# Integration Tests Documentation

## Overview

This directory contains Behavior-Driven Development (BDD) integration tests for the Temporal service document processing workflow. These tests verify the complete workflow-to-activity integration using Behave.

## Purpose

The integration tests ensure that:

1. **Workflow Orchestration**: The `DocumentProcessingWorkflow` correctly orchestrates the complete document processing pipeline
2. **Activity Integration**: Temporal activities are properly called and execute successfully
3. **Error Handling**: The system gracefully handles errors and timeouts
4. **End-to-End Flow**: Documents are processed from input through chunking, embedding, and indexing

## Test Structure

### Features (`features/`)
- `document_processing.feature`: Main BDD feature file defining test scenarios
- `environment.py`: Behave environment setup and teardown
- `steps/document_processing_steps.py`: Step definitions implementing the test logic

### Test Scenarios

1. **Complete Workflow Pipeline** (`@workflow @embedding`)
   - Tests the full document processing flow through DocumentProcessingWorkflow
   - Verifies chunking, embedding, and indexing activities
   - Validates processing statistics and workflow orchestration

2. **Health Check Workflow** (`@health`)
   - Tests the HealthCheckWorkflow execution
   - Validates system health reporting

3. **Document Retrieval Workflow** (`@workflow @retrieval`)
   - Tests the RetrievalWorkflow for document search
   - Verifies search activity execution and parameter passing
   - Validates search results and workflow completion

4. **Direct Activity Testing** (`@activity @chunking`)
   - Tests chunking activity execution directly
   - Validates activity inputs, outputs, and metadata generation
   - Verifies chunk structure and document processing

## Running the Tests

### Prerequisites

Ensure you have the required dependencies:
```bash
pip install behave behave-async
```

### Execution

1. **Using the test runner:**
   ```bash
   python run_integration_tests.py
   ```

2. **Direct Behave execution:**
   ```bash
   behave features/
   ```

3. **Run specific scenarios:**
   ```bash
   behave features/ --tags=@workflow
   behave features/ --tags=@embedding
   behave features/ --tags=@health
   behave features/ --tags=@retrieval
   behave features/ --tags=@activity
   behave features/ --tags=@chunking
   ```

### Test Environment

The tests use Temporal's `WorkflowEnvironment` for testing, which provides:
- In-memory Temporal server
- Deterministic workflow execution
- Activity mocking capabilities
- Isolated test execution

## Test Architecture

### Mocking Strategy

- **Cross-Service Activities**: Embedding and retrieval activities are mocked using `AsyncMock` to simulate distributed service calls
- **Activity Workers**: Mock workers are set up for embedding and retrieval services  
- **External Dependencies**: All external services are isolated to ensure test reliability
- **Deterministic Results**: Mocks provide consistent outputs for workflow verification

### Async Support

The tests use `behave-async` for proper async/await support in step definitions. Key features:
- `@async_run_until_complete` decorator for async steps
- Proper async context management
- Event loop handling

### Context Management

The Behave context object maintains:
- Temporal environment and workflow clients
- Mock workers for embedding and retrieval services
- Document processing test data and results
- Workflow execution results and verification data
- Environment setup and cleanup state

## Test Data

Test scenarios use table-driven data defined in the feature file:
- **Document Processing**: Documents with ID, text, and source fields
- **Document Chunking**: Simplified documents for direct activity testing  
- **Search Queries**: Text queries for retrieval workflow testing
- **Expected Results**: Mock responses simulating actual service outputs

## Maintenance

When adding new tests:

1. **Add scenarios** to `document_processing.feature`
2. **Implement steps** in `document_processing_steps.py`
3. **Update mocks** as needed for new functionality
4. **Add documentation** explaining the test purpose

### Best Practices

- Keep tests focused and independent
- Use descriptive scenario names
- Mock external dependencies consistently
- Verify both success and failure paths
- Include comprehensive assertions

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes the temporal service directory
2. **Async Issues**: Verify proper use of `@async_run_until_complete`
3. **Mock Failures**: Check mock setup in environment hooks
4. **Temporal Errors**: Ensure proper cleanup in teardown

### Debugging

Enable verbose logging:
```bash
behave features/ --logging-level DEBUG
```

Check test output for detailed error information and execution flow.
