"""
Unit tests for the core module.
"""

import os
import sys
import pytest
import yaml
import logging # Added for caplog
from unittest.mock import patch, mock_open, ANY # Added ANY for Popen call check
import subprocess # Added for subprocess.PIPE

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
        mock_process.communicate.return_value = ("stdout", "stderr") # Return strings
        mock_process.returncode = 0
        
        returncode, stdout, stderr = run_command("echo hello")
        
        assert returncode == 0
        assert stdout == "stdout"
        assert stderr == "stderr"
        mock_popen.assert_called_once_with(
            "echo hello",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=None,
            env=ANY, # Check that env is passed (will be os.environ.copy() by default)
            text=True
        )


def test_run_command_error():
    """Test run_command with a failing command."""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = ("", "error") # Return strings
        mock_process.returncode = 1
        
        returncode, stdout, stderr = run_command("invalid_command")
        
        assert returncode == 1
        assert stdout == ""
        assert stderr == "error"
        mock_popen.assert_called_once_with(
            "invalid_command",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=None,
            env=ANY,
            text=True
        )


def test_run_command_exception():
    """Test run_command when an exception occurs."""
    with patch('subprocess.Popen', side_effect=Exception("Test exception")):
        returncode, stdout, stderr = run_command("command")
        
        assert returncode == -1 # Updated expected return code
        assert stdout == ""
        assert "Test exception" in stderr


def test_run_command_filenotfound():
    """Test run_command when FileNotFoundError occurs."""
    with patch('subprocess.Popen', side_effect=FileNotFoundError("File not found")):
        returncode, stdout, stderr = run_command("nonexistent_command")
        assert returncode == -1
        assert stdout == ""
        assert "Command not found: nonexistent_command" in stderr


def test_run_command_with_env():
    """Test run_command with custom environment variables."""
    custom_env = {"CUSTOM_VAR": "value"}
    # Create a copy of current environment and update it, as run_command does
    expected_env = os.environ.copy()
    expected_env.update(custom_env)

    with patch('subprocess.Popen') as mock_popen:
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = ("stdout", "stderr") # Return strings
        mock_process.returncode = 0

        run_command("echo hello", env=custom_env)

        mock_popen.assert_called_once_with(
            "echo hello",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=None,
            env=expected_env, # Check that the merged env is passed
            text=True
        )

def test_run_command_suppress_output(caplog):
    """Test run_command with suppress_output=True and False."""
    with patch('subprocess.Popen') as mock_popen:
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = ("some output", "some error")
        mock_process.returncode = 0

        # Test with suppress_output=True
        with caplog.at_level(logging.DEBUG):
            run_command("echo test_suppressed", suppress_output=True)
        
        suppressed_logs = [rec for rec in caplog.records if "echo test_suppressed" in rec.message and rec.funcName == 'run_command']
        assert not suppressed_logs, "Log messages found when suppress_output was True"
        caplog.clear()

        # Test with suppress_output=False (default behavior)
        with caplog.at_level(logging.DEBUG):
            run_command("echo test_not_suppressed", suppress_output=False)

        not_suppressed_stdout_logs = [
            rec for rec in caplog.records
            if "echo test_not_suppressed" in rec.message and "STDOUT: some output" in rec.message and rec.funcName == 'run_command'
        ]
        not_suppressed_stderr_logs = [
            rec for rec in caplog.records
            if "echo test_not_suppressed" in rec.message and "STDERR: some error" in rec.message and rec.funcName == 'run_command'
        ]
        assert not_suppressed_stdout_logs, "STDOUT log not found when suppress_output was False"
        assert not_suppressed_stderr_logs, "STDERR log not found when suppress_output was False"


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
