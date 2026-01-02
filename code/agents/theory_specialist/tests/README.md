# Testing Guide for Cryptography RAG System

This directory contains comprehensive pytest tests for the Cryptography RAG System.

## Test Structure

```
tests/
├── __init__.py                 # Test package marker
├── conftest.py                 # Pytest fixtures and configuration
├── test_endpoints.py           # Tests for all API endpoints
├── test_document_discovery.py  # Tests for DocumentDiscoveryService component
└── test_integration.py         # End-to-end integration tests
```

## Test Coverage

### 1. `test_endpoints.py` - API Endpoint Tests

Tests every API endpoint comprehensively:

- **GET /health** - System health checks
- **POST /ingest** - Manual document ingestion
- **POST /auto-ingest** - Automatic document discovery and ingestion
- **GET /status** - Ingestion status and metrics
- **POST /generate** - Query answering with provider override
- **POST /provider** - LLM provider switching
- **POST /config** - Configuration updates
- **GET /config** - Configuration retrieval
- **GET /conversations/{id}** - Conversation history retrieval

Test classes:
- `TestHealthEndpoint` - 3 tests
- `TestIngestEndpoint` - 7 tests
- `TestAutoIngestEndpoint` - 3 tests
- `TestStatusEndpoint` - 3 tests
- `TestGenerateEndpoint` - 9 tests
- `TestProviderEndpoint` - 5 tests
- `TestConfigEndpoints` - 7 tests
- `TestConversationEndpoints` - 4 tests
- `TestEndpointValidation` - 3 tests

**Total: 44 endpoint tests**

### 2. `test_document_discovery.py` - Component Tests

Tests the `DocumentDiscoveryService` component:

- Document discovery from filesystem
- Database comparison and filtering
- Document queueing
- Edge cases (empty directories, nested files, special characters)

Test classes:
- `TestDocumentDiscoveryService` - 11 tests
- `TestDocumentDiscoveryIntegration` - 3 tests
- `TestDocumentDiscoveryEdgeCases` - 5 tests

**Total: 19 component tests**

### 3. `test_integration.py` - Integration Tests

Tests complete workflows and scenarios:

- Full ingestion workflow (discover → queue → process)
- Full generation workflow (query → retrieve → rerank → generate)
- Provider switching during operations
- Multi-turn conversations
- Error recovery scenarios
- End-to-end user scenarios

Test classes:
- `TestFullIngestionWorkflow` - 3 tests
- `TestFullGenerationWorkflow` - 4 tests
- `TestProviderSwitchingWorkflow` - 2 tests
- `TestConfigurationWorkflow` - 2 tests
- `TestErrorRecoveryWorkflow` - 3 tests
- `TestEndToEndScenarios` - 4 tests
- `TestConcurrentAccess` - 2 tests

**Total: 20 integration tests**

## Fixtures (conftest.py)

### Database Fixtures
- `test_db_url` - In-memory SQLite database
- `test_engine` - SQLAlchemy engine
- `test_db_session` - Database session for tests

### Settings & Directory Fixtures
- `temp_dir` - Temporary directory for test files
- `test_settings` - Test settings with temp directories
- `test_documents_dir` - Pre-populated test documents directory

### Application Fixtures
- `test_client` - FastAPI TestClient with database override
- `mock_rag_system` - Mocked RAG system (avoids loading models)
- `mock_aggregator` - Mocked document aggregator

### Helper Fixtures
- `create_test_document` - Helper to create test documents in database
- `create_test_conversation` - Helper to create test conversations

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

Or install only test dependencies:
```bash
pip install pytest==7.4.3 pytest-asyncio==0.21.1 pytest-cov==4.1.0 httpx==0.25.2
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# Run with verbose output
pytest -v
```

### Run Specific Test Files

```bash
# Run only endpoint tests
pytest tests/test_endpoints.py

# Run only component tests
pytest tests/test_document_discovery.py

# Run only integration tests
pytest tests/test_integration.py
```

### Run Specific Test Classes or Functions

```bash
# Run specific test class
pytest tests/test_endpoints.py::TestHealthEndpoint

# Run specific test
pytest tests/test_endpoints.py::TestHealthEndpoint::test_health_returns_200

# Run tests matching pattern
pytest -k "health"
```

### Run Tests by Marker

```bash
# Run only unit tests (when markers are added)
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Run Tests with Different Verbosity

```bash
# Quiet mode
pytest -q

# Verbose mode
pytest -v

# Extra verbose (show full output)
pytest -vv
```

### Stop on First Failure

```bash
# Stop at first failure
pytest -x

# Stop after N failures
pytest --maxfail=3
```

### Run Failed Tests Only

```bash
# Run tests that failed last time
pytest --lf

# Run tests that failed first, then others
pytest --ff
```

## Test Output

### Successful Run
```
tests/test_endpoints.py::TestHealthEndpoint::test_health_returns_200 PASSED
tests/test_endpoints.py::TestHealthEndpoint::test_health_response_structure PASSED
tests/test_endpoints.py::TestHealthEndpoint::test_health_contains_expected_values PASSED
...
================================ 83 passed in 2.45s ================================
```

### With Coverage
```
---------- coverage: platform linux, python 3.11 ----------
Name                                  Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
app/aggregator.py                       82     12    85%   23-45, 78-92
app/config.py                           68      8    88%   45-52, 139-145
app/document_discovery.py               58      2    97%   34-35
app/main.py                            450     45    90%   ...
...
------------------------------ HTML report: htmlcov/index.html ------------------------------
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Writing New Tests

### Endpoint Test Template

```python
def test_your_endpoint(test_client):
    """Test description."""
    response = test_client.post("/your-endpoint", json={...})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "expected_key" in data
```

### Component Test Template

```python
def test_your_component(discovery_service):
    """Test description."""
    result = discovery_service.your_method()
    assert result == expected_value
```

### Integration Test Template

```python
def test_your_workflow(test_client, mock_rag_system):
    """Test description."""
    # Step 1
    response1 = test_client.post(...)
    assert response1.status_code == status.HTTP_200_OK

    # Step 2
    response2 = test_client.post(...)
    assert response2.status_code == status.HTTP_200_OK
```

## Troubleshooting

### Import Errors
If you get import errors, ensure the project root is in your PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Database Lock Errors
Tests use in-memory databases, so if you see database errors, ensure
you're using the `test_db_session` fixture properly.

### Mock Not Working
If mocks aren't being applied, check:
1. Fixture order in test parameters
2. Import statements (should import from app.modules, not directly)
3. Monkeypatch is applied before the test runs

## Test Statistics

- **Total Test Files**: 3
- **Total Test Classes**: 20
- **Total Tests**: 83
- **Code Coverage Target**: >90%

## Best Practices

1. **Use fixtures** - Don't recreate setup code
2. **Mock external dependencies** - Avoid loading heavy models
3. **Test isolation** - Each test should be independent
4. **Descriptive names** - Test names should describe what they test
5. **One assertion per test** - Keep tests focused
6. **Arrange-Act-Assert** - Structure tests clearly

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-faq-whentocreate)
