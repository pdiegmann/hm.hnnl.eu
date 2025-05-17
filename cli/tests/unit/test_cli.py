"""
Unit tests for the CLI module.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from click.testing import CliRunner
from hm_cli.cli import cli, main


class TestCLI:
    """Tests for the CLI module."""
    
    def test_cli_version(self, cli_runner):
        """Test CLI version command."""
        result = cli_runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert 'version 0.1.0' in result.output
    
    def test_cli_help(self, cli_runner):
        """Test CLI help command."""
        result = cli_runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Homelab Kubernetes Cluster Management CLI' in result.output
        assert 'cluster' in result.output
        assert 'service' in result.output
        assert 'gitops' in result.output
        assert 'config' in result.output
    
    def test_cluster_commands_help(self, cli_runner):
        """Test cluster commands help."""
        result = cli_runner.invoke(cli, ['cluster', '--help'])
        assert result.exit_code == 0
        assert 'Manage Kubernetes cluster lifecycle' in result.output
        assert 'create' in result.output
        assert 'upgrade' in result.output
        assert 'delete' in result.output
        assert 'status' in result.output
    
    def test_service_commands_help(self, cli_runner):
        """Test service commands help."""
        result = cli_runner.invoke(cli, ['service', '--help'])
        assert result.exit_code == 0
        assert 'Manage cluster services' in result.output
        assert 'add' in result.output
        assert 'list' in result.output
        assert 'remove' in result.output
    
    def test_gitops_commands_help(self, cli_runner):
        """Test gitops commands help."""
        result = cli_runner.invoke(cli, ['gitops', '--help'])
        assert result.exit_code == 0
        assert 'Manage GitOps operations' in result.output
        assert 'commit' in result.output
        assert 'push' in result.output
        assert 'sync' in result.output
    
    def test_config_commands_help(self, cli_runner):
        """Test config commands help."""
        result = cli_runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
        assert 'Manage CLI configuration' in result.output
        assert 'show' in result.output
        assert 'set' in result.output
    
    def test_cluster_create_command(self, cli_runner):
        """Test cluster create command."""
        with patch('hm_cli.cli.ClusterManager') as mock_manager:
            # Mock create method to return True
            mock_instance = mock_manager.return_value
            mock_instance.create.return_value = True
            
            result = cli_runner.invoke(cli, ['cluster', 'create'])
            
            assert result.exit_code == 0
            mock_instance.create.assert_called_once()
    
    def test_cluster_create_command_failure(self, cli_runner):
        """Test cluster create command failure."""
        with patch('hm_cli.cli.ClusterManager') as mock_manager:
            # Mock create method to return False
            mock_instance = mock_manager.return_value
            mock_instance.create.return_value = False
            
            result = cli_runner.invoke(cli, ['cluster', 'create'])
            
            assert result.exit_code == 1
            mock_instance.create.assert_called_once()
    
    def test_cluster_upgrade_command(self, cli_runner):
        """Test cluster upgrade command."""
        with patch('hm_cli.cli.ClusterManager') as mock_manager:
            # Mock upgrade method to return True
            mock_instance = mock_manager.return_value
            mock_instance.upgrade.return_value = True
            
            result = cli_runner.invoke(cli, ['cluster', 'upgrade'])
            
            assert result.exit_code == 0
            mock_instance.upgrade.assert_called_once()
    
    def test_cluster_delete_command(self, cli_runner):
        """Test cluster delete command."""
        with patch('hm_cli.cli.ClusterManager') as mock_manager:
            # Mock delete method to return True
            mock_instance = mock_manager.return_value
            mock_instance.delete.return_value = True
            
            result = cli_runner.invoke(cli, ['cluster', 'delete'])
            
            assert result.exit_code == 0
            mock_instance.delete.assert_called_once()
    
    def test_cluster_status_command(self, cli_runner):
        """Test cluster status command."""
        with patch('hm_cli.cli.ClusterManager') as mock_manager:
            # Mock status method to return True
            mock_instance = mock_manager.return_value
            mock_instance.status.return_value = True
            
            result = cli_runner.invoke(cli, ['cluster', 'status'])
            
            assert result.exit_code == 0
            mock_instance.status.assert_called_once()
    
    def test_service_add_command(self, cli_runner):
        """Test service add command."""
        with patch('hm_cli.cli.ServiceManager') as mock_manager:
            # Mock add method to return True
            mock_instance = mock_manager.return_value
            mock_instance.add.return_value = True
            
            result = cli_runner.invoke(cli, ['service', 'add'])
            
            assert result.exit_code == 0
            mock_instance.add.assert_called_once()
    
    def test_service_list_command(self, cli_runner):
        """Test service list command."""
        with patch('hm_cli.cli.ServiceManager') as mock_manager:
            # Mock list method to return True
            mock_instance = mock_manager.return_value
            mock_instance.list.return_value = True
            
            result = cli_runner.invoke(cli, ['service', 'list'])
            
            assert result.exit_code == 0
            mock_instance.list.assert_called_once()
    
    def test_service_remove_command(self, cli_runner):
        """Test service remove command."""
        with patch('hm_cli.cli.ServiceManager') as mock_manager:
            # Mock remove method to return True
            mock_instance = mock_manager.return_value
            mock_instance.remove.return_value = True
            
            result = cli_runner.invoke(cli, ['service', 'remove'])
            
            assert result.exit_code == 0
            mock_instance.remove.assert_called_once()
    
    def test_gitops_commit_command(self, cli_runner):
        """Test gitops commit command."""
        with patch('hm_cli.cli.GitOpsManager') as mock_manager:
            # Mock commit method to return True
            mock_instance = mock_manager.return_value
            mock_instance.commit.return_value = True
            
            result = cli_runner.invoke(cli, ['gitops', 'commit', '-m', 'Test commit'])
            
            assert result.exit_code == 0
            mock_instance.commit.assert_called_once_with('Test commit')
    
    def test_gitops_push_command(self, cli_runner):
        """Test gitops push command."""
        with patch('hm_cli.cli.GitOpsManager') as mock_manager:
            # Mock push method to return True
            mock_instance = mock_manager.return_value
            mock_instance.push.return_value = True
            
            result = cli_runner.invoke(cli, ['gitops', 'push', '--remote', 'origin', '--branch', 'main'])
            
            assert result.exit_code == 0
            mock_instance.push.assert_called_once_with('origin', 'main')
    
    def test_gitops_sync_command(self, cli_runner):
        """Test gitops sync command."""
        with patch('hm_cli.cli.GitOpsManager') as mock_manager:
            # Mock sync method to return True
            mock_instance = mock_manager.return_value
            mock_instance.sync.return_value = True
            
            result = cli_runner.invoke(cli, ['gitops', 'sync'])
            
            assert result.exit_code == 0
            mock_instance.sync.assert_called_once()
    
    def test_config_show_command(self, cli_runner):
        """Test config show command."""
        with patch('hm_cli.cli.ConfigManager') as mock_manager:
            # Mock config
            mock_instance = mock_manager.return_value
            mock_instance.config = {'test': 'value'}
            
            result = cli_runner.invoke(cli, ['config', 'show'])
            
            assert result.exit_code == 0
            # Output should contain the config
            assert "{'test': 'value'}" in result.output
    
    def test_config_set_command(self, cli_runner):
        """Test config set command."""
        with patch('hm_cli.cli.ConfigManager') as mock_manager:
            # Mock set method
            mock_instance = mock_manager.return_value
            
            result = cli_runner.invoke(cli, ['config', 'set', 'test.key', 'test-value'])
            
            assert result.exit_code == 0
            mock_instance.set.assert_called_once_with('test.key', 'test-value')
    
    def test_main_success(self):
        """Test main function success."""
        with patch('hm_cli.cli.cli') as mock_cli:
            main()
            mock_cli.assert_called_once()
    
    def test_main_exception(self):
        """Test main function with exception."""
        with patch('hm_cli.cli.cli', side_effect=Exception("Test exception")):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)
