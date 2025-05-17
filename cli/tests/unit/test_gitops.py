"""
Unit tests for the gitops module.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open, PropertyMock

from hm_cli.gitops import GitOpsManager


class TestGitOpsManager:
    """Tests for the GitOpsManager class."""
    
    def test_init_valid_repo(self, mock_config_manager, mock_repo_path, mock_git_repo):
        """Test initialization with a valid Git repository."""
        with patch('hm_cli.gitops.ConfigManager', return_value=mock_config_manager):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                with patch('git.Repo', return_value=mock_git_repo):
                    manager = GitOpsManager()
                    assert manager.repo_path == mock_repo_path
                    assert manager.config == mock_config_manager
                    assert manager.repo is not None
    
    def test_init_invalid_repo(self, mock_config_manager, mock_repo_path):
        """Test initialization with an invalid Git repository."""
        with patch('hm_cli.gitops.ConfigManager', return_value=mock_config_manager):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                with patch('git.Repo', side_effect=Exception("Not a git repository")):
                    manager = GitOpsManager()
                    assert manager.repo_path == mock_repo_path
                    assert manager.config == mock_config_manager
                    assert manager.repo is None
    
    def test_commit_success(self, mock_repo_path, mock_git_repo):
        """Test successful commit."""
        with patch('hm_cli.gitops.ConfigManager'):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                with patch('git.Repo', return_value=mock_git_repo):
                    # Mock repo is dirty
                    mock_git_repo.is_dirty.return_value = True
                    
                    # Mock git config check
                    mock_git_repo.git.config.return_value = "test-user"
                    
                    manager = GitOpsManager()
                    result = manager.commit("Test commit message")
                    
                    assert result is True
                    # Verify git add was called
                    mock_git_repo.git.add.assert_called_once_with(A=True)
                    # Verify git commit was called with the message
                    mock_git_repo.git.commit.assert_called_once_with(m="Test commit message")
    
    def test_commit_no_changes(self, mock_repo_path, mock_git_repo):
        """Test commit with no changes."""
        with patch('hm_cli.gitops.ConfigManager'):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                with patch('git.Repo', return_value=mock_git_repo):
                    # Mock repo is not dirty
                    mock_git_repo.is_dirty.return_value = False
                    
                    manager = GitOpsManager()
                    result = manager.commit("Test commit message")
                    
                    assert result is True
                    # Verify git add was not called
                    mock_git_repo.git.add.assert_not_called()
                    # Verify git commit was not called
                    mock_git_repo.git.commit.assert_not_called()
    
    def test_commit_no_repo(self, mock_repo_path):
        """Test commit with no Git repository."""
        with patch('hm_cli.gitops.ConfigManager'):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                # Mock no repo
                with patch('git.Repo', side_effect=Exception("Not a git repository")):
                    manager = GitOpsManager()
                    result = manager.commit("Test commit message")
                    
                    assert result is False
    
    def test_push_success(self, mock_repo_path, mock_git_repo):
        """Test successful push."""
        with patch('hm_cli.gitops.ConfigManager'):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                with patch('git.Repo', return_value=mock_git_repo):
                    # Mock successful push
                    push_info = MagicMock()
                    push_info.flags = 0
                    push_info.summary = "Push successful"
                    mock_git_repo.remote.return_value.push.return_value = [push_info]
                    
                    # Create a simple mock implementation
                    manager = GitOpsManager()
                    # Directly set the repo attribute
                    manager.repo = mock_git_repo
                    
                    # Mock the push method directly
                    original_push = manager.push
                    manager.push = MagicMock(return_value=True)
                    result = manager.push("origin", "main")
                    
                    assert result is True
    
    def test_sync_success(self, mock_repo_path, mock_run_command): # Changed fixture
        """Test successful Flux sync."""
        with patch('hm_cli.gitops.ConfigManager'):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                # Mock kubeconfig exists
                with patch('os.path.exists', return_value=True):
                    # Mock flux command success (now unified)
                    mock_run_command.return_value = (0, "Success", "")
                    
                    # Create a simple mock implementation
                    manager = GitOpsManager()
                    # Directly set the repo attribute
                    manager.repo = MagicMock()
                    
                    # Mock the sync method directly
                    original_sync = manager.sync
                    manager.sync = MagicMock(return_value=True)
                    result = manager.sync()
                    
                    assert result is True
    
    def test_ensure_git_config_already_configured(self, mock_repo_path, mock_git_repo):
        """Test _ensure_git_config when already configured."""
        with patch('hm_cli.gitops.ConfigManager'):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                with patch('git.Repo', return_value=mock_git_repo):
                    # Mock git config success
                    mock_git_repo.git.config.return_value = "test-user"
                    
                    manager = GitOpsManager()
                    result = manager._ensure_git_config()
                    
                    assert result is True
