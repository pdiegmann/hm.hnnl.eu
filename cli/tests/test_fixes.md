# Test Suite Fixes

Based on the test run results, I need to fix several failing tests. Here are the issues and solutions:

## 1. Rich LiveError

Several tests are failing with `rich.errors.LiveError: Only one live display may be active at once`. This happens because multiple tests are trying to create Progress displays simultaneously.

Solution: Mock the Progress class in rich to prevent actual display creation.

## 2. False Assertions

Several tests are failing with `assert False is True`. This indicates that the mocked functions are not returning the expected values.

Solution: Ensure mock return values are properly set up for all test cases.

## 3. Run Command Assertions

Some tests are failing with assertion errors related to `run_command`. 

Solution: Adjust the mock setup to ensure the correct command patterns are matched.

## Specific Fixes:

### TestClusterManager::test_create_success
- Ensure all mocks return True values
- Fix the mock for questionary to return expected values

### TestClusterManager::test_upgrade_success
- Mock rich.progress.Progress to prevent LiveError

### TestClusterManager::test_delete_success
- Fix run_command mock to match the expected command pattern

### TestClusterManager::test_status_success
- Ensure mock returns True

### TestGitOpsManager::test_push_success
- Fix mock return values

### TestGitOpsManager::test_sync_success
- Ensure mock returns True

### TestGitOpsManager::test_ensure_git_config_not_configured
- Fix mock configuration

### TestServiceManager::test_remove_service_success
- Fix questionary mock to return expected values
