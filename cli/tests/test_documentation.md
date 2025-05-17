# Test Documentation and Coverage Guidelines

## Overview

This document provides comprehensive documentation for the hm-cli test suite, including guidelines for test coverage, instructions for running tests, and best practices for extending the test suite.

## Test Suite Structure

The test suite is organized into the following structure:

```
tests/
├── conftest.py                  # Shared fixtures and test configuration
├── unit/                        # Unit tests
│   ├── test_core.py             # Tests for core.py module
│   ├── test_cluster.py          # Tests for cluster.py module
│   ├── test_service.py          # Tests for service.py module
│   ├── test_gitops.py           # Tests for gitops.py module
│   └── test_cli.py              # Tests for cli.py module
├── integration/                 # Integration tests
│   ├── test_cluster_commands.py # Tests for cluster command workflows
│   ├── test_service_commands.py # Tests for service command workflows
│   └── test_gitops_commands.py  # Tests for gitops command workflows
└── test_suite_design.md         # Test suite design documentation
```

## Test Types

### Unit Tests

Unit tests focus on testing individual functions and methods in isolation:

- **Core Module Tests**: Configuration management, utility functions, error handling
- **Cluster Module Tests**: Cluster creation, upgrade, deletion, and status reporting
- **Service Module Tests**: Service addition, listing, and removal
- **GitOps Module Tests**: Git operations, commit, push, and Flux synchronization
- **CLI Module Tests**: Command registration, argument parsing, help text generation

### Integration Tests

Integration tests focus on testing command workflows and interactions between modules:

- **Cluster Command Workflows**: End-to-end cluster creation, upgrade, deletion, and status reporting
- **Service Command Workflows**: Service addition, listing, and removal with Git integration
- **GitOps Command Workflows**: Commit, push, and Flux synchronization processes

## Coverage Guidelines

The test suite aims to achieve 80-90% functional coverage, focusing on actual use cases rather than raw coverage percentage. The coverage targets for each module are:

- **Core Module**: 90% coverage
- **Cluster Module**: 85% coverage
- **Service Module**: 85% coverage
- **GitOps Module**: 85% coverage
- **CLI Module**: 80% coverage

## Running Tests

### Prerequisites

Before running tests, ensure you have the following installed:

- Python 3.8 or higher
- pytest
- pytest-cov (for coverage reports)

### Installation

Install the required dependencies:

```bash
pip install pytest pytest-cov
```

### Running All Tests

To run all tests:

```bash
cd /path/to/hm-cli
pytest
```

### Running Specific Test Categories

To run only unit tests:

```bash
pytest tests/unit/
```

To run only integration tests:

```bash
pytest tests/integration/
```

To run tests for a specific module:

```bash
pytest tests/unit/test_core.py
```

### Running with Coverage Reports

To run tests with coverage reporting:

```bash
pytest --cov=hm_cli
```

For a more detailed HTML coverage report:

```bash
pytest --cov=hm_cli --cov-report=html
```

This will generate an HTML report in the `htmlcov` directory.

## Mocking Strategy

The test suite uses extensive mocking to enable testing without actual infrastructure:

- **External Commands**: `talosctl`, `kubectl`, `flux`, etc. are mocked using the `run_command` function
- **Git Operations**: Git repository operations are mocked using `unittest.mock` and `MagicMock`
- **File System**: File operations are mocked using `mock_open` and patches for `os` functions
- **User Input**: Interactive prompts are mocked using patches for `questionary` functions

## Test Fixtures

The test suite provides several fixtures in `conftest.py`:

- `temp_dir`: Creates a temporary directory for tests
- `mock_repo_path`: Creates a mock repository structure
- `mock_config_file`: Creates a mock configuration file
- `mock_config_manager`: Creates a ConfigManager with a mock configuration file
- `mock_talosctl`: Mocks talosctl command execution
- `mock_kubectl`: Mocks kubectl command execution
- `mock_flux`: Mocks flux command execution
- `mock_git_repo`: Mocks Git repository operations
- `cli_runner`: Creates a Click CLI test runner

## Best Practices for Writing Tests

### General Guidelines

1. **Test One Thing at a Time**: Each test should focus on testing a single functionality or behavior.
2. **Use Descriptive Test Names**: Test names should clearly describe what is being tested.
3. **Follow AAA Pattern**: Arrange, Act, Assert - set up the test, perform the action, verify the results.
4. **Mock External Dependencies**: Always mock external dependencies to ensure tests are isolated and repeatable.
5. **Test Both Success and Failure Cases**: Ensure both successful and error scenarios are covered.

### Unit Test Guidelines

1. **Focus on Function Behavior**: Test the behavior of functions, not their implementation details.
2. **Test Edge Cases**: Include tests for edge cases and boundary conditions.
3. **Keep Tests Independent**: Each test should be independent of others and not rely on shared state.
4. **Use Appropriate Assertions**: Use specific assertions that clearly indicate what is being tested.

### Integration Test Guidelines

1. **Test Complete Workflows**: Focus on testing end-to-end workflows and command sequences.
2. **Verify Side Effects**: Check that all expected side effects (file creation, API calls, etc.) occur.
3. **Test Error Handling**: Ensure error conditions are properly handled and reported.
4. **Mock External Systems**: Use mocks for external systems to ensure tests are reliable and fast.

## Extending the Test Suite

### Adding New Unit Tests

1. Identify the module and functionality to test
2. Create a new test function in the appropriate test file
3. Use existing fixtures or create new ones as needed
4. Follow the AAA pattern (Arrange, Act, Assert)
5. Run the tests to ensure they pass

### Adding New Integration Tests

1. Identify the workflow or command sequence to test
2. Create a new test function in the appropriate integration test file
3. Mock external dependencies and user input
4. Verify all expected side effects and outputs
5. Run the tests to ensure they pass

### Adding New Fixtures

1. Identify common setup or resources needed by multiple tests
2. Add a new fixture function to `conftest.py`
3. Use the `@pytest.fixture` decorator
4. Document the fixture's purpose and usage
5. Use the fixture in your tests

## Troubleshooting

### Common Issues

1. **Test Failures Due to Missing Mocks**: Ensure all external dependencies are properly mocked.
2. **Fixture Scope Issues**: Check that fixture scopes (function, class, module, session) are appropriate.
3. **Path Issues**: Use absolute paths in tests to avoid path-related issues.
4. **Mock Side Effects**: Ensure mocks return appropriate values for different calls.

### Debugging Tips

1. Use `pytest -v` for verbose output
2. Use `pytest --pdb` to drop into the debugger on test failures
3. Add print statements with `pytest -s` to see output during test execution
4. Check mock call counts and arguments with `mock_function.assert_called_with(...)`

## Continuous Integration

While the current test suite is designed for local execution, it can be integrated into CI/CD pipelines:

1. Add a `.github/workflows/test.yml` file for GitHub Actions
2. Configure the workflow to install dependencies and run tests
3. Add coverage reporting to track test coverage over time
4. Set up notifications for test failures

## Conclusion

This test suite provides comprehensive coverage of the hm-cli tool's functionality, ensuring that it works correctly and reliably. By following these guidelines and best practices, you can maintain and extend the test suite to cover new features and functionality as they are added to the tool.
