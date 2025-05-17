"""
Fixtures and configuration for pytest.
"""

import os
import sys
import tempfile
import shutil
import yaml
import pytest
from unittest.mock import MagicMock, patch
from hm_cli.core import run_command as actual_run_command_for_spec # Added import

# Add the hm_cli package to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock rich.progress.Progress to prevent LiveError
pytest.importorskip("rich")
import rich.progress
original_progress = rich.progress.Progress
rich.progress.Progress = MagicMock()

from hm_cli.core import ConfigManager, run_command as actual_run_command


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_repo_path(temp_dir):
    """Create a mock repository structure."""
    repo_path = os.path.join(temp_dir, "hm.hnnl.eu")
    os.makedirs(repo_path)
    
    # Create basic directory structure
    os.makedirs(os.path.join(repo_path, "bootstrap", "talos"))
    os.makedirs(os.path.join(repo_path, "infrastructure", "talos", "controlplane"))
    os.makedirs(os.path.join(repo_path, "cluster", "apps"))
    os.makedirs(os.path.join(repo_path, "cluster", "core"))
    os.makedirs(os.path.join(repo_path, "cluster", "flux"))
    
    # Create a sample gen-config.sh script
    with open(os.path.join(repo_path, "bootstrap", "talos", "gen-config.sh"), 'w') as f:
        f.write("#!/bin/bash\necho 'Generating Talos configurations...'\nexit 0\n")
    
    # Make the script executable
    os.chmod(os.path.join(repo_path, "bootstrap", "talos", "gen-config.sh"), 0o755)
    
    return repo_path


@pytest.fixture
def mock_config_file(temp_dir):
    """Create a mock configuration file."""
    config_dir = os.path.join(temp_dir, ".config", "hm-cli")
    os.makedirs(config_dir, exist_ok=True)
    
    config_file = os.path.join(config_dir, "config.yaml")
    config = {
        "repo_path": os.path.join(temp_dir, "hm.hnnl.eu"),
        "git": {
            "user_name": "test-user",
            "user_email": "test@example.com",
            "remote": "origin",
            "branch": "main"
        },
        "cluster": {
            "name": "test-cluster",
            "network_prefix": "192.168.1",
            "control_plane_vip": "192.168.1.100"
        }
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return config_file


@pytest.fixture
def mock_config_manager(mock_config_file):
    """Create a ConfigManager with a mock configuration file."""
    return ConfigManager(config_file=mock_config_file)


@pytest.fixture
def mock_run_command(monkeypatch):
    """Unified mock for hm_cli.core.run_command, dispatching to tool-specific logic."""
    print("CONFTEST_DEBUG: mock_run_command fixture is being set up.")
    
    # Define a path for a temporary debug file
    # tempfile.gettempdir()
    side_effect_debug_file = os.path.join(".", "hm_cli_side_effect_debug.txt")
    # Clear the file at the start of each test that uses this fixture
    if os.path.exists(side_effect_debug_file):
        os.remove(side_effect_debug_file)

    def simple_side_effect(*args, **kwargs):
        # --- BEGIN FILE WRITE DEBUG ---
        with open(side_effect_debug_file, "a") as f:
            f.write(f"SIDE_EFFECT_EXECUTED: args={args}, kwargs={kwargs}\n")
        # --- END FILE WRITE DEBUG ---
        
        print(f"MINIMAL_SIDE_EFFECT CALLED (SHOULD BE REDUNDANT IF FILE WRITE WORKS): args={args}, kwargs={kwargs}") # Keep for now

        if args and "gen-config.sh" in args[0]:
            call_cwd = kwargs.get('cwd')
            if call_cwd:
                repo_root = None
                if "bootstrap" in call_cwd and "talos" in call_cwd:
                    path_parts = call_cwd.split(os.path.sep)
                    try:
                        talos_index = path_parts.index("talos")
                        bootstrap_index = path_parts.index("bootstrap")
                        if talos_index > 0 and bootstrap_index == talos_index - 1:
                            repo_root = os.path.sep.join(path_parts[:bootstrap_index])
                    except ValueError:
                        pass

                if repo_root:
                    talos_config_dir = os.path.join(repo_root, "infrastructure", "talos", "controlplane")
                    try:
                        os.makedirs(talos_config_dir, exist_ok=True)
                        node_names = ["talos-cp1", "talos-cp2", "talos-cp3"]
                        for node_name in node_names:
                            config_file_path = os.path.join(talos_config_dir, f"{node_name}.yaml")
                            with open(config_file_path, 'w') as f:
                                f.write(f"dummy_talos_config_for: {node_name}\nversion: vMinimalMock\n")
                            # print(f"MINIMAL_SIDE_EFFECT created dummy file: {config_file_path}") # Less critical now
                    except OSError as e:
                        with open(side_effect_debug_file, "a") as f: # Log errors to file too
                            f.write(f"SIDE_EFFECT_ERROR creating dummy files: {e}\n")
        return 0, "minimal_mocked_stdout", "minimal_mocked_stderr"

    mock = MagicMock(side_effect=simple_side_effect)
    
    monkeypatch.setattr('hm_cli.core.run_command', mock)
    monkeypatch.setattr('hm_cli.cluster.run_command', mock)
    # Also patch for gitops if it uses run_command directly from core or its own import
    monkeypatch.setattr('hm_cli.gitops.run_command', mock, raising=False) # Add raising=False in case gitops doesn't have it

    print(f"CONFTEST_DEBUG: mock_run_command.side_effect is: {mock.side_effect}")
    print(f"CONFTEST_DEBUG: Side effect debug file will be at: {side_effect_debug_file}")
        
    return mock


@pytest.fixture
def mock_git_repo():
    """Mock Git repository operations."""
    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = True
    mock_repo.git.add.return_value = None
    mock_repo.git.commit.return_value = None
    
    # Mock git.config to return values for both user.name and user.email
    def git_config_side_effect(config_key):
        if config_key == 'user.name':
            return "test-user"
        if config_key == 'user.email':
            return "test@example.com"
        return "" # Default for other keys
    mock_repo.git.config.side_effect = git_config_side_effect
    
    mock_remote = MagicMock()
    mock_remote.push.return_value = [MagicMock(flags=0, summary="Push successful")]
    mock_repo.remote.return_value = mock_remote
    
    mock_branch = MagicMock()
    mock_branch.name = "main"
    mock_repo.active_branch = mock_branch
    
    with patch('git.Repo') as mock_git:
        mock_git.return_value = mock_repo
        yield mock_repo


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()

