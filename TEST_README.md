# Upload-Transcript Endpoint Unit Tests

This directory contains comprehensive unit tests for the `/upload-transcript` endpoint of the FastAPI backend.

## Test Files

- **`test_upload_transcript.py`** - Main test suite covering core functionality
- **`test_upload_transcript_edge_cases.py`** - Edge cases and error scenarios
- **`conftest.py`** - Shared test fixtures and configurations
- **`pytest.ini`** - Pytest configuration
- **`run_tests.py`** - Test runner script

## Test Coverage

### Core Functionality Tests
- ✅ Successful file upload with valid SRT
- ✅ Metadata handling (category, location, speaker, etc.)
- ✅ LLM processing integration
- ✅ Embedding generation
- ✅ Qdrant storage
- ✅ Response model validation

### Error Handling Tests
- ✅ Invalid file extensions
- ✅ Invalid file encoding
- ✅ Empty files
- ✅ SRT parsing failures
- ✅ LLM processing failures
- ✅ Embedding failures
- ✅ Storage failures

### Edge Cases
- ✅ Large file uploads (1000+ subtitles)
- ✅ Special characters and Unicode content
- ✅ Very long metadata fields
- ✅ Concurrent uploads
- ✅ LLM timeout handling
- ✅ Malformed LLM responses
- ✅ Missing configuration files

## Running the Tests

### Option 1: Using the test runner script (Recommended)
```bash
python run_tests.py
```

### Option 2: Using pytest directly
```bash
# Run all tests
pytest test_upload_transcript*.py -v

# Run specific test file
pytest test_upload_transcript.py -v

# Run specific test
pytest -k "test_successful_upload" -v

# Run with coverage
pytest test_upload_transcript*.py --cov=main --cov-report=html
```

### Option 3: Run specific test categories
```bash
# Run only unit tests
pytest -m unit -v

# Run only integration tests  
pytest -m integration -v

# Skip slow tests
pytest -m "not slow" -v
```

## Test Dependencies

The tests require the following packages (installed automatically):
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `httpx` - HTTP client for FastAPI testing
- `pytest-mock` - Mocking utilities
- `pytest-cov` - Coverage reporting

## Test Mocking Strategy

The tests mock all external dependencies to ensure:
- **Isolation**: Tests don't depend on external services
- **Speed**: No actual API calls or file I/O
- **Reliability**: Tests are deterministic and repeatable
- **Safety**: No side effects on real systems

### Mocked Components
- OpenAI API calls (`openai.chat.completions.create`)
- File system operations (`open`, file reading)
- Qdrant database operations (`store_chunks`, etc.)
- SRT parsing (`parse_srt`)
- Embedding generation (`embed_and_tag_chunks`)

## Test Data

Tests use realistic sample data:
- Valid SRT subtitle files
- Various metadata combinations
- Unicode and special character content
- Large file scenarios (1000+ entries)

## Assertions and Validations

Each test validates:
- HTTP response status codes
- Response body structure and content
- Mock function call counts and arguments
- Error message content
- Data flow through the pipeline

## Coverage Goals

Current test coverage targets:
- **Function coverage**: 100% of upload-transcript related functions
- **Branch coverage**: 95% of conditional logic paths
- **Line coverage**: 90% of executable lines

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external dependencies
- Fast execution (< 30 seconds)
- Clear pass/fail indicators
- Detailed error reporting

## Adding New Tests

When adding new tests:
1. Follow the existing naming convention (`test_*`)
2. Use appropriate fixtures from `conftest.py`
3. Mock external dependencies
4. Include both positive and negative test cases
5. Add descriptive docstrings
6. Update this README if needed

## Troubleshooting

### Common Issues

**ImportError**: Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

**ModuleNotFoundError**: Run tests from the backend directory:
```bash
cd backend
python run_tests.py
```

**Mock not working**: Check that patches are applied in the correct order and scope.

**Async issues**: Ensure async tests use `@pytest.mark.asyncio` decorator.

### Debug Mode

For detailed debugging, run with:
```bash
pytest --pdb --tb=long -v
```

This will drop into a debugger on test failures.
