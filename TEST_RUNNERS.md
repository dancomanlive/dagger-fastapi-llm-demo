# Test Runners Documentation

This project now includes comprehensive test runners for all services and the entire project.

## Available Test Runners

### 1. Root-Level Test Runner
**File**: `/test_runner.py`
**Purpose**: Run tests for all services or specific services from the project root

```bash
# Run all tests for all services
python test_runner.py

# Run tests for a specific service
python test_runner.py --service temporal
python test_runner.py --service embedding
python test_runner.py --service retriever
python test_runner.py --service gradio

# Quick tests without coverage
python test_runner.py --quick

# Coverage-only tests
python test_runner.py --coverage-only
```

### 2. Service-Specific Test Runners

#### Temporal Service
**File**: `/services/temporal_service/test_runner.py`
- Runs unit tests with coverage
- Runs BDD tests (behave)
- Runs integration test suite

#### Embedding Service
**File**: `/services/embedding_service/test_runner.py`
- Runs unit tests with coverage
- Runs quick tests without coverage
- Runs individual test files

#### Retriever Service
**File**: `/services/retriever_service/test_runner.py`
- Runs unit tests with coverage
- Runs quick tests without coverage
- Runs individual test files

#### Gradio Service
**File**: `/services/gradio_service/test_runner.py`
- Runs unit tests with coverage
- Runs BDD tests (behave)
- Runs quick tests without coverage

## Test Coverage Thresholds

| Service | Coverage Threshold | Current Coverage |
|---------|-------------------|------------------|
| Gradio Service | 35% | 38.51% ✅ |
| Temporal Service | 60% | 62.00% ✅ |
| Embedding Service | 60% | 79.27% ✅ |
| Retriever Service | 60% | 84.62% ✅ |

**Note**: Individual test files run without coverage to avoid partial coverage threshold failures. Coverage is measured comprehensively when running the full test suite.

## Usage Examples

```bash
# Run all tests from project root
./test_runner.py

# Run tests for temporal service only
./test_runner.py --service temporal

# Run tests from within a service directory
cd services/embedding_service
python test_runner.py

# Run specific pytest commands
cd services/retriever_service
pytest tests/ -v --cov=activities --cov=worker

# Run BDD tests
cd services/gradio_service
behave features/ -v
```

## Test Types

### Unit Tests (pytest)
- Test individual functions and classes
- Mock external dependencies
- Fast execution
- High coverage requirements

### BDD Tests (behave)
- Test business scenarios and workflows
- Integration testing
- User story validation
- End-to-end behavior verification

### Integration Tests
- Test service interactions
- Temporal workflow integration
- External API integration
- Cross-service communication

## Coverage Reports

HTML coverage reports are generated in each service's `htmlcov/` directory:
- `/services/temporal_service/htmlcov/`
- `/services/embedding_service/htmlcov/`
- `/services/retriever_service/htmlcov/`
- `/services/gradio_service/htmlcov/`

Open `index.html` in any coverage directory to view detailed line-by-line coverage analysis.
