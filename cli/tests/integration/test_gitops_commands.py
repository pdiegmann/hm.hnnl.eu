"""
Integration tests for gitops commands.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

from click.testing import CliRunner
from hm_cli.cli import cli


class TestGitOpsCommandsIntegration:
    """Integration tests for gitops commands."""
    
    def test_gitops_commit_workflow(self, cli_runner, mock_repo_path, mock_git_repo):
        """Test the gitops commit workflow."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            with patch('git.Repo', return_value=mock_git_repo):
                # Mock repo is dirty
                mock_git_repo.is_dirty.return_value = True
                
                # Mock git config
                mock_git_repo.git.config.return_value = "test-user"
                
                # Run the command with explicit message
                result = cli_runner.invoke(cli, ['gitops', 'commit', '-m', 'Test commit message'])
                
                assert result.exit_code == 0
                
                # Verify git add was called
                mock_git_repo.git.add.assert_called_once_with(A=True)
                # Verify git commit was called with the message
                mock_git_repo.git.commit.assert_called_once_with(m="Test commit message")
    
    def test_gitops_commit_interactive_workflow(self, cli_runner, mock_repo_path, mock_git_repo):
        """Test the gitops commit workflow with interactive message prompt."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            with patch('git.Repo', return_value=mock_git_repo):
                # Mock repo is dirty
                mock_git_repo.is_dirty.return_value = True
                
                # Mock git config
                mock_git_repo.git.config.return_value = "test-user"
                
                # Mock questionary for commit message
                with patch('questionary.text') as mock_text:
                    mock_text.return_value.ask.return_value = "Interactive commit message"
                    
                    # Run the command without message (will prompt)
                    result = cli_runner.invoke(cli, ['gitops', 'commit'])
                    
                    assert result.exit_code == 0
                    
                    # Verify git add was called
                    mock_git_repo.git.add.assert_called_once_with(A=True)
                    # Verify git commit was called with the interactive message
                    mock_git_repo.git.commit.assert_called_once_with(m="Interactive commit message")
    
    def test_gitops_commit_no_changes_workflow(self, cli_runner, mock_repo_path, mock_git_repo):
        """Test the gitops commit workflow when there are no changes."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            with patch('git.Repo', return_value=mock_git_repo):
                # Mock repo is not dirty
                mock_git_repo.is_dirty.return_value = False
                
                # Run the command
                result = cli_runner.invoke(cli, ['gitops', 'commit', '-m', 'Test commit message'])
                
                assert result.exit_code == 0
                
                # Verify git add was not called
                mock_git_repo.git.add.assert_not_called()
                # Verify git commit was not called
                mock_git_repo.git.commit.assert_not_called()
    
    def test_gitops_push_workflow(self, cli_runner, mock_repo_path, mock_git_repo):
        """Test the gitops push workflow."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            with patch('git.Repo', return_value=mock_git_repo):
                # Mock successful push
                push_info = MagicMock()
                push_info.flags = 0
                push_info.summary = "Push successful"
                mock_git_repo.remote().push.return_value = [push_info]
                
                # Run the command with explicit remote and branch
                result = cli_runner.invoke(cli, ['gitops', 'push', '--remote', 'origin', '--branch', 'main'])
                
                assert result.exit_code == 0
                
                # Verify remote push was called
                mock_git_repo.remote.assert_called_with('origin')
                mock_git_repo.remote().push.assert_called_once_with('main')
    
    def test_gitops_push_default_workflow(self, cli_runner, mock_repo_path, mock_git_repo, mock_config_manager):
        """Test the gitops push workflow with default remote and branch."""
        with patch('hm_cli.gitops.ConfigManager', return_value=mock_config_manager):
            with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
                with patch('git.Repo', return_value=mock_git_repo):
                    # Mock successful push
                    push_info = MagicMock()
                    push_info.flags = 0
                    push_info.summary = "Push successful"
                    mock_git_repo.remote().push.return_value = [push_info]
                    
                    # Run the command without specifying remote or branch
                    result = cli_runner.invoke(cli, ['gitops', 'push'])
                    
                    assert result.exit_code == 0
                    
                    # Verify remote push was called with defaults
                    mock_git_repo.remote.assert_called_with('origin')
                    mock_git_repo.remote().push.assert_called_once_with('main')
    
    def test_gitops_push_remote_not_found_workflow(self, cli_runner, mock_repo_path, mock_git_repo):
        """Test the gitops push workflow when remote is not found."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            with patch('git.Repo', return_value=mock_git_repo):
                # Mock remote not found initially, then allow it after creation
                # Mock remote interactions
                # This mock will be the return value of repo.remote()
                mock_upstream_remote_after_creation = MagicMock()
                mock_upstream_remote_after_creation.push.return_value = [MagicMock(flags=0, summary="Push successful")]

                def remote_side_effect(name):
                    if name == 'upstream':
                        if not mock_git_repo.create_remote.called:
                            raise ValueError("Remote not found")
                        else:
                            # After create_remote is called for 'upstream', return the specifically prepared mock
                            return mock_upstream_remote_after_creation
                    # For other remotes (e.g., 'origin' if used by default push)
                    default_mock_remote = MagicMock()
                    default_mock_remote.push.return_value = [MagicMock(flags=0, summary="Push successful")]
                    return default_mock_remote

                mock_git_repo.remote.side_effect = remote_side_effect
                
                # Mock questionary for adding remote
                with patch('questionary.confirm') as mock_confirm:
                    with patch('questionary.text') as mock_text:
                        # User confirms adding remote
                        mock_confirm.return_value.ask.return_value = True
                        mock_text.return_value.ask.return_value = "https://github.com/user/repo.git"
                        
                        # Mock create_remote to do nothing but allow tracking
                        mock_git_repo.create_remote.return_value = MagicMock()
                        
                        # Run the command
                        result = cli_runner.invoke(cli, ['gitops', 'push', '--remote', 'upstream'])
                        
                        assert result.exit_code == 0
                        
                        # Verify create_remote was called
                        mock_git_repo.create_remote.assert_called_once_with('upstream', url='https://github.com/user/repo.git')
    
    def test_gitops_sync_workflow(self, cli_runner, mock_repo_path, mock_run_command): # Changed fixture
        """Test the gitops sync workflow."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            # Mock kubeconfig exists
            with patch('os.path.exists', return_value=True):
                # Run the command
                result = cli_runner.invoke(cli, ['gitops', 'sync'])
                
                assert result.exit_code == 0
                
                # Verify flux was called to check version
                mock_run_command.assert_any_call( # Changed mock name
                    "flux --version",
                    cwd=mock_repo_path
                )
                
                # Verify flux was called to reconcile
                mock_run_command.assert_any_call( # Changed mock name
                    "flux reconcile source git flux-system",
                    cwd=mock_repo_path
                )
                
                # Verify flux was called to get status
                mock_run_command.assert_any_call( # Changed mock name
                    "flux get kustomizations --watch",
                    cwd=mock_repo_path
                )
    
    def test_gitops_sync_no_kubeconfig_workflow(self, cli_runner, mock_repo_path):
        """Test the gitops sync workflow when kubeconfig doesn't exist."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            # Mock kubeconfig doesn't exist
            with patch('os.path.exists', return_value=False):
                # Run the command
                result = cli_runner.invoke(cli, ['gitops', 'sync'])
                
                assert result.exit_code == 1
    
    def test_gitops_sync_flux_not_installed_workflow(self, cli_runner, mock_repo_path):
        """Test the gitops sync workflow when flux is not installed."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            # Mock kubeconfig exists
            with patch('os.path.exists', return_value=True):
                # Mock flux not installed
                with patch('hm_cli.core.run_command') as mock_run:
                    mock_run.return_value = (1, "", "flux: command not found")
                    
                    # Run the command
                    result = cli_runner.invoke(cli, ['gitops', 'sync'])
                    
                    assert result.exit_code == 1
    
    def test_end_to_end_gitops_workflow(self, cli_runner, mock_repo_path, mock_git_repo, mock_run_command): # Changed fixture
        """Test an end-to-end GitOps workflow: commit, push, sync."""
        with patch('hm_cli.gitops.get_repo_path', return_value=mock_repo_path):
            with patch('git.Repo', return_value=mock_git_repo):
                # Mock repo is dirty
                mock_git_repo.is_dirty.return_value = True
                
                # Mock git config
                mock_git_repo.git.config.return_value = "test-user"
                
                # Mock successful push
                push_info = MagicMock()
                push_info.flags = 0
                push_info.summary = "Push successful"
                mock_git_repo.remote().push.return_value = [push_info]
                
                # Mock kubeconfig exists
                with patch('os.path.exists', return_value=True):
                    # Step 1: Commit changes
                    commit_result = cli_runner.invoke(cli, ['gitops', 'commit', '-m', 'Update configuration'])
                    assert commit_result.exit_code == 0
                    
                    # Verify git add and commit were called
                    mock_git_repo.git.add.assert_called_once_with(A=True)
                    mock_git_repo.git.commit.assert_called_once_with(m="Update configuration")
                    
                    # Step 2: Push changes
                    push_result = cli_runner.invoke(cli, ['gitops', 'push'])
                    assert push_result.exit_code == 0
                    
                    # Verify remote push was called
                    mock_git_repo.remote().push.assert_called_once()
                    
                    # Step 3: Sync with Flux
                    sync_result = cli_runner.invoke(cli, ['gitops', 'sync'])
                    assert sync_result.exit_code == 0
                    
                    # Verify flux was called to reconcile
                    mock_run_command.assert_any_call( # Changed mock name
                        "flux reconcile source git flux-system",
                        cwd=mock_repo_path
                    )
