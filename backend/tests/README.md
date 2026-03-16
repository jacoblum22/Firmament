# StudyMate Backend Tests

This directory contains all tests for the StudyMate backend, organized into logical categories for better maintainability and easier test execution.

## Test Organization

### Directory Structure
```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── __init__.py                 # Package initialization
├── config/                     # Configuration-related tests
│   ├── __init__.py
│   ├── test_config.py          # Main configuration tests
│   ├── test_config_validation.py # Configuration validation tests
│   ├── test_cors.py            # CORS configuration tests
│   ├── test_port_edge_cases.py # Port handling edge cases
│   ├── test_port_simple.py     # Basic port handling tests
│   └── test_port_validation.py # Port validation tests
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_routes.py          # API route integration tests
│   └── test_kmeans_integration.py # K-means clustering integration tests
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_cache.py           # Cache unit tests
│   ├── test_cache_security.py  # Cache security tests
│   ├── test_cleanup.py         # Cleanup utility tests
│   ├── test_content_cache.py   # Content-based cache tests
│   ├── test_import.py          # Import functionality tests
│   ├── test_kmeans.py          # K-means unit tests
│   └── test_thread_safety.py   # Thread safety tests
└── utils/                      # Utility and processing tests
    ├── __init__.py
    ├── test_bertopic_changes.py # BERTopic changes tests
    ├── test_bertopic_processor.py # BERTopic processor tests
    ├── test_bertopic_processor_new_features.py # New BERTopic features
    ├── test_chunk_analysis.py   # Text chunk analysis tests
    ├── test_chunk_size_optimizer.py # Chunk size optimization tests
    ├── test_clean_text.py       # Text cleaning utility tests
    ├── test_cluster_analysis.py # Cluster analysis tests
    ├── test_filter_chunks.py    # Chunk filtering tests
    ├── test_generate_cluster_heading.py # Cluster heading generation
    ├── test_rnnoise_process.py  # RNNoise processing tests
    ├── test_semantic_segmentation.py # Semantic segmentation tests
    └── test_transcribe_audio.py # Audio transcription tests
```

## Running Tests

### Using the deps.ps1 script (recommended on Windows):
```powershell
# Run all tests
.\deps.ps1 test

# Run specific test categories
.\deps.ps1 test-unit          # Unit tests only
.\deps.ps1 test-integration   # Integration tests only
.\deps.ps1 test-config        # Configuration tests only
.\deps.ps1 test-utils         # Utility/processing tests only
```

### Using pytest directly:
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/config/ -v
pytest tests/utils/ -v

# Run upload/security tests specifically
pytest tests/integration/test_file_upload_comprehensive.py tests/integration/test_file_upload_validation.py -v

# Run a specific test file
pytest tests/config/test_config.py -v
pytest tests/utils/test_bertopic_processor.py -v
```

### Manual live-server test (requires a running backend):
```bash
# Start the server first: python start.py --env development
python tests/manual_upload_test.py --server-url http://localhost:8000
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and classes in isolation
- **Scope**: Small, focused tests with minimal dependencies
- **Examples**: DateTime utilities, import functionality, individual algorithm components

### 2. Integration Tests (`tests/integration/`)
- **Purpose**: Test how different components work together
- **Scope**: Tests that involve multiple modules or external dependencies
- **Examples**: API route testing, end-to-end workflow tests

### 3. Configuration Tests (`tests/config/`)
- **Purpose**: Test all configuration-related functionality
- **Scope**: Configuration validation, CORS setup, port handling
- **Examples**: Environment variable handling, configuration file parsing

### 4. Utility/Processing Tests (`tests/utils/`)
- **Purpose**: Test data processing and utility functions
- **Scope**: Audio processing, text analysis, clustering algorithms
- **Examples**: BERTopic processing, audio transcription, text cleaning

## Test Markers

The tests use pytest markers for additional organization:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.config` - Configuration tests
- `@pytest.mark.utils` - Utility tests

## Best Practices

1. **Test Isolation**: Each test should be independent and not rely on other tests
2. **Descriptive Names**: Test function names should clearly describe what is being tested
3. **Arrange-Act-Assert**: Follow the AAA pattern for test structure
4. **Mock External Dependencies**: Use mocks for external services and file operations
5. **Test Edge Cases**: Include tests for boundary conditions and error scenarios

## Adding New Tests

When adding new tests:
1. Place them in the appropriate category directory
2. Follow the existing naming convention (`test_*.py`)
3. Add appropriate imports and fixtures
4. Include docstrings explaining the test purpose
5. Add relevant pytest markers if needed

## Continuous Integration

The test suite is designed to be run in CI/CD pipelines:
- All tests must pass before merging
- Tests are run in multiple categories to identify failures quickly
- Configuration tests validate deployment readiness
