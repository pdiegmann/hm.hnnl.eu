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

# Add the hm_cli package to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock rich.progress.Progress to prevent LiveError
pytest.importorskip("rich")
import rich.progress
original_progress = rich.progress.Progress
rich.progress.Progress = MagicMock()

from hm_cli.core import ConfigManager


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
def mock_talosctl():
    """Mock talosctl command execution."""
    with patch('hm_cli.core.run_command') as mock_run:
        def side_effect(cmd, cwd=None):
            if "talosctl apply-config" in cmd:
                return 0, "Applied configuration successfully", ""
            elif "talosctl bootstrap" in cmd:
                return 0, "Bootstrapped successfully", ""
            elif "talosctl health" in cmd:
                return 0, "Cluster is healthy", ""
            elif "talosctl kubeconfig" in cmd:
                # Create a dummy kubeconfig file
                if cwd:
                    with open(os.path.join(cwd, "kubeconfig"), 'w') as f:
                        f.write("apiVersion: v1\nkind: Config\n")
                return 0, "Kubeconfig retrieved", ""
            elif "talosctl get nodes" in cmd:
                return 0, "node1:\n  metadata:\n    hostname: talos-cp1\n  spec:\n    addresses:\n      - address: 192.168.1.101", ""
            elif "talosctl reset" in cmd:
                return 0, "Node reset successfully", ""
            else:
                return 1, "", f"Unknown talosctl command: {cmd}"
        
        mock_run.side_effect = side_effect
        yield mock_run


@pytest.fixture
def mock_kubectl():
    """Mock kubectl command execution."""
    with patch('hm_cli.core.run_command') as mock_run:
        def side_effect(cmd, cwd=None):
            if "kubectl get nodes" in cmd:
                return 0, "NAME       STATUS   ROLES                  AGE   VERSION\ntalos-cp1   Ready    control-plane,master   1d    v1.28.6", ""
            elif "kubectl get pods" in cmd:
                return 0, "NAMESPACE     NAME                                      READY   STATUS    RESTARTS   AGE\nkube-system   kube-apiserver-talos-cp1                    1/1     Running   0          1d", ""
            elif "kubectl apply" in cmd:
                return 0, "resource created", ""
            else:
                return 1, "", f"Unknown kubectl command: {cmd}"
        
        mock_run.side_effect = side_effect
        yield mock_run


@pytest.fixture
def mock_flux():
    """Mock flux command execution."""
    with patch('hm_cli.core.run_command') as mock_run:
        def side_effect(cmd, cwd=None):
            if "flux --version" in cmd:
                return 0, "flux version 2.0.0", ""
            elif "flux bootstrap" in cmd:
                return 0, "Flux bootstrapped successfully", ""
            elif "flux reconcile" in cmd:
                return 0, "Reconciliation triggered", ""
            elif "flux get" in cmd:
                return 0, "NAME          READY   MESSAGE                       REVISION        SUSPENDED\nflux-system   True    Applied revision: main/1234567   main/1234567   False", ""
            else:
                return 1, "", f"Unknown flux command: {cmd}"
        
        mock_run.side_effect = side_effect
        yield mock_run


@pytest.fixture
def mock_git_repo():
    """Mock Git repository operations."""
    mock_repo = MagicMock()
    mock_repo.is_dirty.return_value = True
    mock_repo.git.add.return_value = None
    mock_repo.git.commit.return_value = None
    mock_repo.git.config.return_value = "test-user"
    
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
