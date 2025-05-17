"""
Integration tests for cluster commands.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from click.testing import CliRunner
from hm_cli.cli import cli


class TestClusterCommandsIntegration:
    """Integration tests for cluster commands."""
    
    def test_cluster_create_workflow(self, cli_runner, mock_repo_path, mock_talosctl, mock_flux):
        """Test the complete cluster creation workflow."""
        with patch('hm_cli.cluster.get_repo_path', return_value=mock_repo_path):
            with patch('questionary.text') as mock_text:
                with patch('questionary.confirm') as mock_confirm:
                    # Set up mock responses for questionary
                    mock_text.return_value.ask.side_effect = [
                        "test-cluster",  # cluster name
                        "192.168.1",     # network prefix
                        "192.168.1.100", # control plane VIP
                        "192.168.1.101", # first CP IP
                        "192.168.1.102", # second CP IP
                        "192.168.1.103", # third CP IP
                        "test-user"      # GitHub username
                    ]
                    mock_confirm.return_value.ask.return_value = True
                    
                    # Run the command
                    result = cli_runner.invoke(cli, ['cluster', 'create'])
                    
                    assert result.exit_code == 0
                    
                    # Verify talosctl was called for config generation
                    mock_talosctl.assert_any_call(
                        f"cd {os.path.join(mock_repo_path, 'bootstrap', 'talos')} && ./gen-config.sh test-cluster 192.168.1 192.168.1.100 192.168.1.101 192.168.1.102 192.168.1.103",
                        cwd=mock_repo_path
                    )
                    
                    # Verify talosctl was called for bootstrapping
                    mock_talosctl.assert_any_call(
                        "talosctl bootstrap --nodes 192.168.1.101",
                        cwd=mock_repo_path
                    )
                    
                    # Verify talosctl was called for health check
                    mock_talosctl.assert_any_call(
                        "talosctl health --nodes 192.168.1.101,192.168.1.102,192.168.1.103 --wait-timeout 30m",
                        cwd=mock_repo_path
                    )
                    
                    # Verify flux was called for bootstrap
                    mock_flux.assert_any_call(
                        "flux bootstrap github --owner=test-user --repository=hm.hnnl.eu --path=cluster/flux --personal",
                        cwd=mock_repo_path
                    )
    
    def test_cluster_upgrade_workflow(self, cli_runner, mock_repo_path, mock_talosctl, mock_kubectl):
        """Test the complete cluster upgrade workflow."""
        with patch('hm_cli.cluster.get_repo_path', return_value=mock_repo_path):
            with patch('questionary.confirm') as mock_confirm:
                with patch('questionary.text') as mock_text:
                    # Set up mock responses
                    mock_confirm.return_value.ask.return_value = True
                    mock_text.return_value.ask.side_effect = [
                        "v1.29.0",  # k8s version
                        "v1.7.0"    # talos version
                    ]
                    
                    # Mock cluster info
                    with patch('os.path.exists', return_value=True):
                        with patch('yaml.safe_load', return_value={
                            'cluster': {
                                'name': 'test-cluster',
                                'network_prefix': '192.168.1',
                                'control_plane_vip': '192.168.1.100'
                            },
                            'nodes': [
                                {'name': 'talos-cp1', 'ip': '192.168.1.101', 'type': 'controlplane', 'hardware': 'ryzen'},
                                {'name': 'talos-cp2', 'ip': '192.168.1.102', 'type': 'controlplane', 'hardware': 'intel'},
                                {'name': 'talos-cp3', 'ip': '192.168.1.103', 'type': 'controlplane', 'hardware': 'mac-mini'}
                            ]
                        }):
                            # Run the command
                            result = cli_runner.invoke(cli, ['cluster', 'upgrade'])
                            
                            assert result.exit_code == 0
                            
                            # Verify talosctl was called for config generation
                            mock_talosctl.assert_any_call(
                                f"cd {os.path.join(mock_repo_path, 'bootstrap', 'talos')} && ./gen-config.sh test-cluster 192.168.1 192.168.1.100 192.168.1.101 192.168.1.102 192.168.1.103 v1.29.0 v1.7.0",
                                cwd=mock_repo_path
                            )
                            
                            # Verify talosctl was called for applying configs
                            mock_talosctl.assert_any_call(
                                "talosctl apply-config --insecure --nodes 192.168.1.101 --file infrastructure/talos/controlplane/talos-cp1.yaml",
                                cwd=mock_repo_path
                            )
                            
                            # Verify talosctl was called for health check
                            mock_talosctl.assert_any_call(
                                "talosctl health --nodes 192.168.1.101,192.168.1.102,192.168.1.103 --wait-timeout 30m",
                                cwd=mock_repo_path
                            )
    
    def test_cluster_delete_workflow(self, cli_runner, mock_repo_path, mock_talosctl):
        """Test the complete cluster deletion workflow."""
        with patch('hm_cli.cluster.get_repo_path', return_value=mock_repo_path):
            with patch('questionary.text') as mock_text:
                # User confirms deletion by typing cluster name
                mock_text.return_value.ask.return_value = "test-cluster"
                
                # Mock cluster info
                with patch('os.path.exists', return_value=True):
                    with patch('yaml.safe_load', return_value={
                        'cluster': {
                            'name': 'test-cluster',
                            'network_prefix': '192.168.1',
                            'control_plane_vip': '192.168.1.100'
                        },
                        'nodes': [
                            {'name': 'talos-cp1', 'ip': '192.168.1.101', 'type': 'controlplane', 'hardware': 'ryzen'},
                            {'name': 'talos-cp2', 'ip': '192.168.1.102', 'type': 'controlplane', 'hardware': 'intel'},
                            {'name': 'talos-cp3', 'ip': '192.168.1.103', 'type': 'controlplane', 'hardware': 'mac-mini'}
                        ]
                    }):
                        # Mock os.remove for kubeconfig cleanup
                        with patch('os.remove'):
                            # Run the command
                            result = cli_runner.invoke(cli, ['cluster', 'delete'])
                            
                            assert result.exit_code == 0
                            
                            # Verify talosctl was called for resetting nodes
                            mock_talosctl.assert_any_call(
                                "talosctl reset --graceful=false --reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --nodes 192.168.1.101",
                                cwd=mock_repo_path
                            )
                            mock_talosctl.assert_any_call(
                                "talosctl reset --graceful=false --reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --nodes 192.168.1.102",
                                cwd=mock_repo_path
                            )
                            mock_talosctl.assert_any_call(
                                "talosctl reset --graceful=false --reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --nodes 192.168.1.103",
                                cwd=mock_repo_path
                            )
    
    def test_cluster_status_workflow(self, cli_runner, mock_repo_path, mock_kubectl):
        """Test the cluster status workflow."""
        with patch('hm_cli.cluster.get_repo_path', return_value=mock_repo_path):
            # Mock kubeconfig existence
            with patch('os.path.exists', return_value=True):
                # Run the command
                result = cli_runner.invoke(cli, ['cluster', 'status'])
                
                assert result.exit_code == 0
                
                # Verify kubectl was called to get nodes and pods
                mock_kubectl.assert_any_call(
                    "kubectl get nodes -o wide",
                    cwd=mock_repo_path
                )
                mock_kubectl.assert_any_call(
                    "kubectl get pods -A",
                    cwd=mock_repo_path
                )
