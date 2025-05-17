"""
Integration tests for service commands.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, mock_open

from click.testing import CliRunner
from hm_cli.cli import cli


class TestServiceCommandsIntegration:
    """Integration tests for service commands."""
    
    def test_service_add_workflow(self, cli_runner, mock_repo_path):
        """Test the complete service addition workflow."""
        with patch('hm_cli.service.get_repo_path', return_value=mock_repo_path):
            with patch('questionary.text') as mock_text:
                with patch('questionary.select') as mock_select:
                    with patch('questionary.confirm') as mock_confirm:
                        # Set up mock responses for questionary
                        mock_text.return_value.ask.side_effect = [
                            "test-service",  # service name
                            "test-service",  # namespace
                            "80",            # port
                            "Test service"   # description
                        ]
                        mock_select.return_value.ask.side_effect = [
                            "web-app",                  # service type
                            "both (local and external)" # visibility
                        ]
                        mock_confirm.return_value.ask.return_value = False  # don't commit
                        
                        # Mock directory creation
                        with patch('os.makedirs'):
                            # Mock file writing
                            with patch('builtins.open', mock_open()):
                                # Run the command
                                result = cli_runner.invoke(cli, ['service', 'add'])
                                
                                assert result.exit_code == 0
                                
                                # Verify directories would be created
                                service_dir = os.path.join(mock_repo_path, "cluster", "apps", "test-service")
                                base_dir = os.path.join(service_dir, "base")
                                
                                # Check that the right files would be created
                                expected_files = [
                                    os.path.join(service_dir, "namespace.yaml"),
                                    os.path.join(service_dir, "kustomization.yaml"),
                                    os.path.join(base_dir, "kustomization.yaml"),
                                    os.path.join(base_dir, "deployment.yaml"),
                                    os.path.join(base_dir, "service.yaml"),
                                    os.path.join(service_dir, "README.md")
                                ]
    
    def test_service_add_with_commit_workflow(self, cli_runner, mock_repo_path, mock_git_repo):
        """Test service addition with commit workflow."""
        with patch('hm_cli.service.get_repo_path', return_value=mock_repo_path):
            with patch('questionary.text') as mock_text:
                with patch('questionary.select') as mock_select:
                    with patch('questionary.confirm') as mock_confirm:
                        # Set up mock responses for questionary
                        mock_text.return_value.ask.side_effect = [
                            "test-service",  # service name
                            "test-service",  # namespace
                            "80",            # port
                            "Test service"   # description
                        ]
                        mock_select.return_value.ask.side_effect = [
                            "web-app",                  # service type
                            "both (local and external)" # visibility
                        ]
                        mock_confirm.return_value.ask.return_value = True  # commit changes
                        
                        # Mock directory creation
                        with patch('os.makedirs'):
                            # Mock file writing
                            with patch('builtins.open', mock_open()):
                                # Mock GitOpsManager
                                with patch('hm_cli.service.GitOpsManager') as mock_gitops:
                                    mock_gitops_instance = mock_gitops.return_value
                                    mock_gitops_instance.commit.return_value = True
                                    
                                    # Run the command
                                    result = cli_runner.invoke(cli, ['service', 'add'])
                                    
                                    assert result.exit_code == 0
                                    
                                    # Verify GitOpsManager.commit was called
                                    mock_gitops_instance.commit.assert_called_once_with("Add service: test-service")
    
    def test_service_list_workflow(self, cli_runner, mock_repo_path):
        """Test the service listing workflow."""
        with patch('hm_cli.service.get_repo_path', return_value=mock_repo_path):
            # Mock services list
            with patch('os.path.exists', return_value=True):
                with patch('os.listdir', return_value=["service1", "service2", ".git"]):
                    with patch('os.path.isdir', return_value=True):
                        with patch('builtins.open', mock_open(read_data="This is a web-app service")):
                            # Run the command
                            result = cli_runner.invoke(cli, ['service', 'list'])
                            
                            assert result.exit_code == 0
    
    def test_service_remove_workflow(self, cli_runner, mock_repo_path):
        """Test the service removal workflow."""
        with patch('hm_cli.service.get_repo_path', return_value=mock_repo_path):
            # Mock services list
            with patch('os.path.exists', return_value=True):
                with patch('os.listdir', return_value=["service1", "service2", ".git"]):
                    with patch('os.path.isdir', return_value=True):
                        with patch('builtins.open', mock_open(read_data="This is a web-app service")):
                            with patch('questionary.select') as mock_select:
                                with patch('questionary.confirm') as mock_confirm:
                                    # User selects service1 and confirms removal
                                    mock_select.return_value.ask.return_value = 'service1'
                                    mock_confirm.return_value.ask.side_effect = [True, False]  # confirm removal, don't commit
                                    
                                    # Mock successful removal
                                    with patch('shutil.rmtree'):
                                        # Run the command
                                        result = cli_runner.invoke(cli, ['service', 'remove'])
                                        
                                        assert result.exit_code == 0
    
    def test_service_remove_with_commit_workflow(self, cli_runner, mock_repo_path, mock_git_repo):
        """Test service removal with commit workflow."""
        with patch('hm_cli.service.get_repo_path', return_value=mock_repo_path):
            # Mock services list
            with patch('os.path.exists', return_value=True):
                with patch('os.listdir', return_value=["service1", "service2", ".git"]):
                    with patch('os.path.isdir', return_value=True):
                        with patch('builtins.open', mock_open(read_data="This is a web-app service")):
                            with patch('questionary.select') as mock_select:
                                with patch('questionary.confirm') as mock_confirm:
                                    # User selects service1 and confirms removal
                                    mock_select.return_value.ask.return_value = 'service1'
                                    mock_confirm.return_value.ask.side_effect = [True, True]  # confirm removal, commit changes
                                    
                                    # Mock successful removal
                                    with patch('shutil.rmtree'):
                                        # Mock GitOpsManager
                                        with patch('hm_cli.service.GitOpsManager') as mock_gitops:
                                            mock_gitops_instance = mock_gitops.return_value
                                            mock_gitops_instance.commit.return_value = True
                                            
                                            # Run the command
                                            result = cli_runner.invoke(cli, ['service', 'remove'])
                                            
                                            assert result.exit_code == 0
                                            
                                            # Verify GitOpsManager.commit was called
                                            mock_gitops_instance.commit.assert_called_once_with("Remove service: service1")
