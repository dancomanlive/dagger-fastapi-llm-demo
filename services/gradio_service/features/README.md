# Gradio Service Integration Tests Documentation

## Overview

This directory contains Behavior-Driven Development (BDD) integration tests for the Gradio service Temporal workflow integration. These tests verify that the web interface correctly integrates with Temporal workflows for document retrieval.

## Purpose

The integration tests ensure that:

1. **Temporal Integration**: Gradio service correctly initiates RetrievalWorkflow instead of direct HTTP calls
2. **User Interface Behavior**: Chat interface responds appropriately to user queries and workflow results
3. **Error Handling**: Graceful handling of Temporal workflow failures and connectivity issues
4. **Multi-User Support**: Concurrent user sessions can execute independent workflows
5. **Collection Management**: Document collection selection works correctly with workflow parameters

## Test Structure

### Features (`features/`)
- `gradio_temporal_integration.feature`: Main BDD feature file defining test scenarios
- `environment.py`: Behave environment setup and teardown
- `steps/gradio_temporal_steps.py`: Step definitions implementing the test logic

### Test Scenarios

1. **User Query via Temporal**
   - Tests user submitting queries through Gradio interface
   - Verifies RetrievalWorkflow is started instead of HTTP calls
   - Validates OpenAI response includes workflow context

2. **Temporal Workflow Failure Handling**
   - Tests graceful handling of workflow failures
   - Verifies user receives appropriate error messages
   - Ensures interface remains functional after errors

3. **Concurrent Multi-User Access**
   - Tests multiple users querying simultaneously
   - Verifies independent workflow execution per user
   - Validates isolated user sessions and responses

4. **Collection-Specific Retrieval**
   - Tests document collection selection functionality
   - Verifies workflows use correct collection parameters
   - Validates collection-specific search results

## Running the Tests

### Prerequisites

Ensure you have the required dependencies:
```bash
pip install behave pytest pytest-asyncio pytest-mock
```

### Execution

1. **Using Behave directly:**
   ```bash
   behave features/
   ```

2. **With verbose output:**
   ```bash
   behave features/ -v
   ```

3. **Run specific scenarios:**
   ```bash
   behave features/ --tags=@temporal
   behave features/ --tags=@ui
   behave features/ --tags=@error
   ```

### Test Environment

The tests use mocked Temporal clients and OpenAI responses to provide:
- Isolated test execution without external dependencies
- Deterministic workflow results for consistent testing
- Controlled error simulation for failure scenarios
- Fast test execution without actual API calls

## Test Architecture

### Mocking Strategy

- **Temporal Client**: Mocked using `AsyncMock` to simulate workflow execution
- **OpenAI API**: Mocked responses for chat completions
- **Gradio Interface**: Direct function testing without UI rendering
- **Workflow Results**: Predefined responses simulating successful retrieval

### Async Support

The tests handle async/await patterns in:
- Temporal workflow client interactions
- OpenAI API calls
- Gradio interface functions
- Proper async context management

### Context Management

The Behave context object maintains:
- Mocked Temporal clients and workflow handles
- Simulated user sessions and queries
- Test data for collections and documents
- Error conditions and system states

## Test Data

Test scenarios use realistic data:
- **User Queries**: Sample questions about AI, machine learning, etc.
- **Document Collections**: Multiple collection names for testing selection
- **Workflow Results**: Mock search results with relevant documents
- **Error Conditions**: Various failure modes for robustness testing

## Maintenance

When adding new tests:

1. **Add scenarios** to `gradio_temporal_integration.feature`
2. **Implement steps** in `gradio_temporal_steps.py`
3. **Update mocks** for new Temporal workflow interactions
4. **Add documentation** explaining the test purpose and coverage

### Best Practices

- Mock external dependencies consistently (Temporal, OpenAI)
- Test both success and failure paths
- Use realistic test data that reflects actual usage
- Include comprehensive assertions for UI state and responses
- Maintain clear separation between unit and integration tests

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes the gradio service directory
2. **Async Issues**: Verify proper async mocking and context handling
3. **Mock Failures**: Check mock setup for Temporal and OpenAI clients
4. **Gradio Errors**: Ensure interface functions can be tested independently

### Debugging

Enable verbose logging:
```bash
behave features/ --logging-level DEBUG
```

Check test output for detailed execution flow and mock interactions.
