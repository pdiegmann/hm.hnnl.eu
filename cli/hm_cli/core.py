"""
Core module for the hm-cli tool.
Contains shared utilities and base functionality.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from rich.console import Console
from rich.logging import RichHandler

# Set up rich console for output
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)
logger = logging.getLogger("hm-cli")

# Constants
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/hm-cli")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "config.yaml")
DEFAULT_REPO_PATH = os.path.expanduser("~/hm.hnnl.eu")


class ConfigManager:
    """Manages configuration for the CLI tool."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file. If None, uses the default.
        """
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dict containing configuration values.
        """
        if not os.path.exists(self.config_file):
            self._create_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            "repo_path": DEFAULT_REPO_PATH,
            "git": {
                "user_name": "",
                "user_email": "",
                "remote": "origin",
                "branch": "main"
            },
            "cluster": {
                "name": "homelab",
                "network_prefix": "192.168.1",
                "control_plane_vip": "192.168.1.100"
            }
        }
        
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key, can use dot notation for nested keys.
            default: Default value if key is not found.
            
        Returns:
            Configuration value or default.
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key, can use dot notation for nested keys.
            value: Value to set.
        """
        keys = key.split('.')
        config = self.config
        
        for i, k in enumerate(keys[:-1]):
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)


def ensure_repo_exists(repo_path: str) -> bool:
    """Ensure the repository exists at the given path.
    
    Args:
        repo_path: Path to the repository.
        
    Returns:
        True if the repository exists, False otherwise.
    """
    return os.path.exists(os.path.join(repo_path, '.git'))


def run_command(cmd: str, cwd: Optional[str] = None) -> tuple:
    """Run a shell command and return the result.
    
    Args:
        cmd: Command to run.
        cwd: Working directory for the command.
        
    Returns:
        Tuple of (return_code, stdout, stderr).
    """
    import subprocess
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            cwd=cwd
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return 1, "", str(e)


def validate_ip_address(ip: str) -> bool:
    """Validate an IP address.
    
    Args:
        ip: IP address to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    import re
    
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    # Check each octet is in range 0-255
    return all(0 <= int(octet) <= 255 for octet in ip.split('.'))


def get_repo_path() -> str:
    """Get the repository path from configuration.
    
    Returns:
        Path to the repository.
    """
    config = ConfigManager()
    return config.get('repo_path', DEFAULT_REPO_PATH)
