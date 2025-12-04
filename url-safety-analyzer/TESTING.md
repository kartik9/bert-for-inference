# URL Safety Analyzer - Testing Documentation

## 📋 Overview

This document describes the comprehensive test suite for the URL Safety Analyzer nightly tests. The test suite validates all critical functionality to ensure the system remains reliable as dependencies and code evolve.

## 🎯 Test Coverage

### Test Categories

The test suite is organized into the following categories:

#### 1. **Unit Tests** (`@pytest.mark.unit`)
- Test individual components in isolation
- Fast execution (< 1s per test)
- No external dependencies
- Covers:
  - URL structure parsing
  - DNS resolution logic
  - SSL certificate validation
  - HTTP response handling
  - Content analysis
  - AI agent initialization
  - Cache operations
  - Evaluation metrics

#### 2. **Integration Tests** (`@pytest.mark.integration`)
- Test interactions between components
- Moderate execution time
- May use mocked external services
- Covers:
  - End-to-end analysis pipeline
  - API endpoint interactions
  - Cache integration with analyzers
  - Component error propagation

#### 3. **Network Tests** (`@pytest.mark.network`)
- Test components requiring network access
- Depends on external services
- May be slower or flaky
- Covers:
  - Real DNS resolution
  - Live HTTP requests
  - SSL certificate checks

#### 4. **Smoke Tests** (`@pytest.mark.smoke`)
- Quick validation of basic functionality
- Run on every commit
- < 30 seconds total
- Covers:
  - Module imports
  - Configuration loading
  - Basic validation logic

#### 5. **Slow Tests** (`@pytest.mark.slow`)
- Performance and stress tests
- Long-running evaluations
- Run in separate job
- Covers:
  - Full evaluation pipeline
  - Large dataset processing
  - Performance benchmarks

#### 6. **Nightly Tests** (`@pytest.mark.nightly`)
- All tests tagged for nightly execution
- Comprehensive coverage
- Run daily at 2 AM UTC

## 🚀 Running Tests

### Prerequisites

```bash
cd url-safety-analyzer
pip install -r backend/requirements.txt
pip install -r test-requirements.txt
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/ -m "unit"

# Integration tests only
pytest tests/ -m "integration"

# Nightly tests (comprehensive)
pytest tests/ -m "nightly"

# Smoke tests (quick validation)
pytest tests/ -m "smoke"

# Exclude network-dependent tests
pytest tests/ -m "not network"
```

### Run Specific Test Files

```bash
# URL analyzer tests
pytest tests/test_url_analyzer.py -v

# AI agent tests
pytest tests/test_ai_agent.py -v

# Evaluation framework tests
pytest tests/test_evaluation.py -v

# Cache tests
pytest tests/test_cache.py -v

# Integration tests
pytest tests/test_integration.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=backend --cov-report=html --cov-report=term-missing
```

Coverage report will be generated in `htmlcov/index.html`.

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest tests/ -n auto
```

## 🔧 Configuration

### Environment Variables

```bash
# AI API keys (for AI-dependent tests)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Test configuration
export TEST_CACHE_DIR="/tmp/url_cache_test"
export TEST_TIMEOUT=300  # 5 minutes
```

### pytest.ini

Located at `url-safety-analyzer/pytest.ini`, this file configures:
- Test discovery patterns
- Markers for test categories
- Output formatting
- Timeout settings
- Coverage options

## 📊 Test Structure

```
url-safety-analyzer/tests/
├── __init__.py                # Test package init
├── conftest.py                # Shared fixtures and configuration
├── test_url_analyzer.py       # URL analysis tests
├── test_ai_agent.py          # AI agent tests
├── test_evaluation.py        # Evaluation framework tests
├── test_cache.py             # Caching system tests
└── test_integration.py       # End-to-end integration tests
```

## 🧪 Test Fixtures

### Available Fixtures (from conftest.py)

- `test_urls`: Dictionary of test URLs (safe, suspicious, invalid)
- `mock_http_response`: Creates mock HTTP responses
- `mock_dns_response`: Mock DNS resolution data
- `mock_ssl_info`: Mock SSL certificate information
- `mock_whois_info`: Mock WHOIS data
- `mock_ai_response`: Mock AI analysis response
- `mock_url_analyzer`: Mocked URL analyzer instance
- `mock_ai_client`: Mocked AI client (OpenAI/Anthropic)
- `temp_cache_dir`: Temporary cache directory
- `sample_technical_data`: Sample analysis data
- `sample_dataset_entry`: Sample dataset entry
- `mock_openai_key`: Sets mock OpenAI API key
- `mock_anthropic_key`: Sets mock Anthropic API key

## 📈 Continuous Integration

### GitHub Actions Workflow

The nightly test suite runs automatically via GitHub Actions:

**Schedule**: Every night at 2 AM UTC
**Manual Trigger**: Via workflow_dispatch
**On Push**: When code changes in `url-safety-analyzer/`

### Workflow Jobs

1. **test** (Matrix: Python 3.9, 3.10, 3.11)
   - Unit tests
   - Integration tests
   - Smoke tests
   - Coverage report (Python 3.11)

2. **network-tests**
   - Network-dependent tests
   - Continues on error (external factors)

3. **performance-tests**
   - Slow/performance tests
   - 30-minute timeout

4. **notification**
   - Checks results
   - Sends failure notifications

### Artifacts

- **Coverage Report**: HTML coverage report (30-day retention)
- **Test Results**: JUnit XML results per Python version (30-day retention)

## 🐛 Writing New Tests

### Test Structure Template

```python
import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


@pytest.mark.unit
@pytest.mark.nightly
class TestMyFeature:
    """Test my new feature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        # Arrange
        input_data = "test"

        # Act
        result = my_function(input_data)

        # Assert
        assert result is not None

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        result = await my_async_function()
        assert result == expected_value
```

### Best Practices

1. **Use descriptive names**: Test names should describe what is being tested
2. **One concept per test**: Each test should validate one specific behavior
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Use fixtures**: Reuse common setup via fixtures
5. **Mock external services**: Don't depend on external APIs in unit tests
6. **Add markers**: Tag tests appropriately (`@pytest.mark.unit`, etc.)
7. **Handle async**: Use `@pytest.mark.asyncio` for async tests
8. **Test edge cases**: Include invalid inputs, errors, edge cases

## 🔍 Debugging Tests

### Run Single Test

```bash
pytest tests/test_url_analyzer.py::TestURLStructureAnalysis::test_valid_https_url -v
```

### Run with Debugging

```bash
pytest tests/test_url_analyzer.py --pdb  # Drop into debugger on failure
```

### Verbose Output

```bash
pytest tests/ -vv  # Very verbose
pytest tests/ -s   # Show print statements
```

### Show Warnings

```bash
pytest tests/ -v --tb=long  # Full tracebacks
```

## 📊 Coverage Goals

### Target Coverage

- **Overall**: > 80%
- **Critical modules**:
  - `url_analyzer.py`: > 90%
  - `ai_agent.py`: > 85%
  - `url_cache.py`: > 90%
  - `evaluation_framework.py`: > 85%

### View Coverage

```bash
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

## 🚨 Common Issues

### Issue: Tests fail due to missing API keys

**Solution**: Set mock API keys or skip AI tests
```bash
export OPENAI_API_KEY="sk-test-mock-key"
pytest tests/ -m "not ai"
```

### Issue: Network tests fail

**Solution**: Network tests are flaky; run without network marker
```bash
pytest tests/ -m "not network"
```

### Issue: Async tests hang

**Solution**: Check for missing `await` or increase timeout
```python
@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_my_async_function():
    ...
```

### Issue: Import errors

**Solution**: Ensure backend is in Python path
```python
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
```

## 📝 Test Maintenance

### Regular Tasks

- **Weekly**: Review test failures and update flaky tests
- **Monthly**: Update test dependencies in `test-requirements.txt`
- **Quarterly**: Review coverage and add tests for uncovered code
- **On Feature Add**: Write tests before merging new features

### Updating Tests

When updating code:
1. Run existing tests first
2. Update tests to match new behavior
3. Add new tests for new functionality
4. Ensure coverage doesn't decrease

## 🎓 Learning Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)

## 📞 Support

For questions about the test suite:
1. Check this documentation
2. Review test examples in `tests/`
3. Check pytest output for detailed error messages
4. Review GitHub Actions logs for CI failures

---

**Last Updated**: 2024-12-04
**Maintainer**: Claude (Aurora Nightly Tests)
