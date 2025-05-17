"""
Unit tests for the core module.
"""

import os
import sys
import pytest
import yaml
from unittest.mock import patch, mock_open

from hm_cli.core import (
    ConfigManager, 
    ensure_repo_exists, 
    run_command, 
    validate_ip_address, 
    get_repo_path
)


class TestConfigManager:
    """Tests for the ConfigManager class."""
    
    def test_init_with_config_file(self, mock_config_file):
        """Test initialization with a specific config file."""
        config_manager = ConfigManager(config_file=mock_config_file)
        assert config_manager.config_file == mock_config_file
        assert isinstance(config_manager.config, dict)
        assert "repo_path" in config_manager.config
    
    def test_load_config_file_not_exists(self, temp_dir):
        """Test loading config when file doesn't exist."""
        config_file = os.path.join(temp_dir, "nonexistent.yaml")
        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs') as mock_makedirs:
                with patch('builtins.open', mock_open()) as mock_file:
                    config_manager = ConfigManager(config_file=config_file)
                    mock_makedirs.assert_called_once()
                    # Verify open was called at least once (for writing)
                    assert mock_file.call_count >= 1
    
    def test_get_existing_key(self, mock_config_manager):
        """Test getting an existing configuration key."""
        value = mock_config_manager.get("cluster.name")
        assert value == "test-cluster"
    
    def test_get_nested_key(self, mock_config_manager):
        """Test getting a nested configuration key."""
        value = mock_config_manager.get("git.user_name")
        assert value == "test-user"
    
    def test_get_nonexistent_key(self, mock_config_manager):
        """Test getting a nonexistent key."""
        value = mock_config_manager.get("nonexistent.key", "default")
        assert value == "default"
    
    def test_set_existing_key(self, mock_config_manager, temp_dir):
        """Test setting an existing key."""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_config_manager.set("cluster.name", "new-cluster")
            assert mock_config_manager.get("cluster.name") == "new-cluster"
            mock_file.assert_called_once()
    
    def test_set_new_key(self, mock_config_manager, temp_dir):
        """Test setting a new key."""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_config_manager.set("new.key", "new-value")
            assert mock_config_manager.get("new.key") == "new-value"
            mock_file.assert_called_once()
    
    def test_set_nested_key(self, mock_config_manager, temp_dir):
        """Test setting a nested key."""
        with patch('builtins.open', mock_open()) as mock_file:
            mock_config_manager.set("cluster.new_key", "new-value")
            assert mock_config_manager.get("cluster.new_key") == "new-value"
            mock_file.assert_called_once()


def test_ensure_repo_exists_true():
    """Test ensure_repo_exists when repo exists."""
    with patch('os.path.exists', return_value=True):
        assert ensure_repo_exists("/path/to/repo") is True


def test_ensure_repo_exists_false():
    """Test ensure_repo_exists when repo doesn't exist."""
    with patch('os.path.exists', return_value=False):
        assert ensure_repo_exists("/path/to/repo") is False


def test_run_command_success():
    """Test run_command with a successful command."""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = (b"stdout", b"stderr")
        mock_process.returncode = 0
        
        returncode, stdout, stderr = run_command("echo hello")
        
        assert returncode == 0
        assert stdout == "stdout"
        assert stderr == "stderr"
        mock_popen.assert_called_once()


def test_run_command_error():
    """Test run_command with a failing command."""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = (b"", b"error")
        mock_process.returncode = 1
        
        returncode, stdout, stderr = run_command("invalid_command")
        
        assert returncode == 1
        assert stdout == ""
        assert stderr == "error"
        mock_popen.assert_called_once()


def test_run_command_exception():
    """Test run_command when an exception occurs."""
    with patch('subprocess.Popen', side_effect=Exception("Test exception")):
        returncode, stdout, stderr = run_command("command")
        
        assert returncode == 1
        assert stdout == ""
        assert "Test exception" in stderr


def test_validate_ip_address_valid():
    """Test validate_ip_address with valid IPs."""
    assert validate_ip_address("192.168.1.1") is True
    assert validate_ip_address("10.0.0.1") is True
    assert validate_ip_address("172.16.0.1") is True
    assert validate_ip_address("255.255.255.255") is True


def test_validate_ip_address_invalid():
    """Test validate_ip_address with invalid IPs."""
    assert validate_ip_address("192.168.1") is False
    assert validate_ip_address("192.168.1.256") is False
    assert validate_ip_address("192.168.1.1.1") is False
    assert validate_ip_address("not-an-ip") is False
    assert validate_ip_address("") is False


def test_get_repo_path(mock_config_manager):
    """Test get_repo_path function."""
    with patch('hm_cli.core.ConfigManager', return_value=mock_config_manager):
        repo_path = get_repo_path()
        assert repo_path == mock_config_manager.get('repo_path')
