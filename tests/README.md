# Resume Customizer Testing Infrastructure

This directory contains the comprehensive testing infrastructure for the Resume Customizer application. The testing framework is organized into different types of tests to ensure code quality, API contract stability, and application performance.

## Test Structure

```
tests/
├── conftest.py           # Common test fixtures and configuration
├── integration/          # Integration tests for API endpoints
├── unit/                 # Unit tests for individual components
├── contract/             # API contract tests
├── performance/          # Performance and load tests
└── README.md             # This file
```

## Test Scripts

For convenience, we provide several scripts to run the tests:

### Using the Python Test Runner

```bash
# Run all tests with coverage
python run_tests.py --all --coverage

# Run only unit tests
python run_tests.py --unit

# Run integration tests
python run_tests.py --integration

# Run contract tests
python run_tests.py --contract

# Run end-to-end tests
python run_tests.py --e2e

# Run performance tests
python run_tests.py --performance --users 20 --run-time 2m
```

### Using Shell Scripts

#### On Linux/macOS:

```bash
# Run all tests with coverage
./run_tests.sh --all --coverage

# Run specific test types
./run_tests.sh --unit
./run_tests.sh --integration
./run_tests.sh --e2e
```

#### On Windows:

```cmd
# Run all tests with coverage
run_tests.bat --all --coverage

# Run specific test types
run_tests.bat --unit
run_tests.bat --integration
run_tests.bat --e2e
```

## Test Types

### 1. Unit Tests

Unit tests focus on testing individual components in isolation. They ensure that each function or class behaves correctly according to its specification.

Run unit tests with:

```bash
pytest tests/unit
```

### 2. Integration Tests

Integration tests verify that different components work together correctly. These tests focus on API endpoints and the interaction between different services.

Run integration tests with:

```bash
pytest tests/integration
```

### 3. Contract Tests

Contract tests validate that the API adheres to its defined contract, ensuring backward compatibility and stable interfaces. These tests are essential for maintaining API stability during development.

Run contract tests with:

```bash
pytest tests/contract
```

Generate API contract documentation with:

```bash
python tests/contract/generate_contract_docs.py
```

### 4. Performance Tests

Performance tests measure the application's performance characteristics under various loads. These tests use Locust to simulate realistic user behaviors and measure response times.

Run performance tests with:

```bash
python tests/performance/run_performance_tests.py --users 20 --spawn-rate 5 --run-time 5m
```

Options:
- `--users`: Number of simulated users
- `--spawn-rate`: User spawn rate per second
- `--run-time`: Test duration (e.g., 30s, 5m)
- `--no-headless`: Run with Locust UI
- `--start-server`: Start the API server
- `--analyze-only`: Path to existing results file to analyze
- `--report-path`: Path for the output report

## Test Fixtures

The conftest.py file provides common fixtures for all test types, including:

- **Application fixtures**: TestClient instance, mock server
- **Service mocks**: Mocked service components
- **Test data**: Sample resumes, job descriptions
- **Utility fixtures**: Task tracking, assertion helpers

## Setting Up Test Environment

1. Install testing dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov locust
```

2. Generate test data files:

```bash
python create_test_pdf.py
python create_test_docx.py
```

3. Run the test suite:

```bash
python run_tests.py --all
```

## CI/CD Integration

The testing infrastructure is integrated with CI/CD pipelines in GitHub Actions. The workflow:

1. Runs linting and style checks
2. Executes unit tests
3. Runs integration tests
4. Validates API contracts
5. Performs basic performance tests
6. Generates and archives test reports

## Performance Benchmarks

Performance benchmarks are defined in `tests/performance/benchmarks.py`. These benchmarks establish the expected performance characteristics for each endpoint, including:

- Median response time
- 95th percentile response time
- Failure rate

When performance tests are run, the results are compared against these benchmarks to detect performance regressions.

## Adding New Tests

### Unit Tests

1. Create a new test file in `tests/unit/`
2. Use appropriate fixtures from conftest.py
3. Focus on testing a single component in isolation

### Integration Tests

1. Create a new test file in `tests/integration/`
2. Use the TestClient fixture for API requests
3. Mock external dependencies
4. Test full request-response cycles

### Contract Tests

1. Update the API contracts in `tests/contract/api_contracts.py`
2. Add tests in `tests/contract/test_api_contracts.py`
3. Regenerate API documentation

### Performance Tests

1. Add new user behaviors in `tests/performance/locustfile.py`
2. Update performance thresholds in `tests/performance/benchmarks.py`
3. Run the performance tests to establish a baseline

## Testing Best Practices

1. **Isolation**: Tests should be independent and not rely on the state from other tests
2. **Determinism**: Tests should produce the same results on each run
3. **Coverage**: Aim for high test coverage, especially for critical paths
4. **Readability**: Test names and assertions should clearly explain what's being tested
5. **Speed**: Tests should run quickly to enable fast feedback during development
