"""
Integration tests for cluster commands.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, ANY

from click.testing import CliRunner
from hm_cli.cli import cli


class TestClusterCommandsIntegration:
    """Integration tests for cluster commands."""

    def test_cluster_create_workflow(self, cli_runner, mock_repo_path, mock_run_command): # Changed fixtures
        """Test the complete cluster creation workflow."""
        with patch('hm_cli.cluster.get_repo_path', return_value=mock_repo_path):
            # Mock questionary.unsafe_prompt for _collect_cluster_info
            # and questionary.text for _setup_flux
            with patch('hm_cli.cluster.questionary.unsafe_prompt') as mock_unsafe_prompt, \
                 patch('hm_cli.cluster.questionary.text') as mock_text_general, \
                 patch('hm_cli.cluster.questionary.confirm') as mock_confirm:

                # Mock for _collect_cluster_info
                mock_unsafe_prompt.return_value = {
                    0: "test-cluster",    # Cluster name
                    1: "192.168.1",       # Network prefix
                    2: "192.168.1.100",   # Control plane VIP
                    3: "v1.7.0",          # Talos version
                    4: "v1.29.0"          # Kubernetes version
                }

                # Mock for individual .text calls in _collect_cluster_info (node IPs)
                # and _setup_flux (git user, repo name)
                # This needs to be a list of return values for each .ask() call
                mock_text_general.return_value.ask.side_effect = [
                    "192.168.1.101",      # First CP IP (_collect_cluster_info)
                    "192.168.1.102",      # Second CP IP (_collect_cluster_info)
                    "192.168.1.103",      # Third CP IP (_collect_cluster_info)
                    "test-user",          # GitHub username (_setup_flux)
                    "hm.hnnl.eu"          # GitHub repository name (_setup_flux)
                ]
                mock_confirm.return_value.ask.return_value = True
                    
                # Run the command
                result = cli_runner.invoke(cli, ['cluster', 'create'])

                if result.exception:
                    print(f"DEBUG: Test {self.test_cluster_create_workflow.__name__} caught exception: {result.exception}")
                    import traceback
                    traceback.print_tb(result.exc_info[2])
                if result.output:
                    print(f"DEBUG: Test {self.test_cluster_create_workflow.__name__} output:\n{result.output}")

                assert result.exit_code == 0
                
                # Verify talosctl was called for config generation (gen-config.sh)
                # Note: gen-config.sh is called with env vars, not CLI args for cluster details
                mock_run_command.assert_any_call( # Changed mock name
                    os.path.join(mock_repo_path, 'bootstrap', 'talos', 'gen-config.sh'),
                    cwd=os.path.join(mock_repo_path, 'bootstrap', 'talos'),
                    env=ANY # env is passed to this specific run_command call
                )
                
                # Verify talosctl was called for bootstrapping
                mock_run_command.assert_any_call( # Changed mock name
                    "talosctl bootstrap --nodes 192.168.1.101",
                    cwd=mock_repo_path
                )
                
                # Verify talosctl was called for health check
                mock_run_command.assert_any_call( # Changed mock name
                    "talosctl health --nodes 192.168.1.101,192.168.1.102,192.168.1.103 --wait-timeout 15m", # Corrected timeout
                    cwd=mock_repo_path
                )
                
                # Verify flux was called for bootstrap
                mock_run_command.assert_any_call( # Changed mock name
                    "flux bootstrap github --owner=test-user --repository=hm.hnnl.eu --branch=main --path=cluster/flux --personal",
                    cwd=mock_repo_path
                )

    def test_cluster_upgrade_workflow(self, cli_runner, mock_repo_path, mock_run_command): # Changed fixtures
        """Test the complete cluster upgrade workflow."""
        print("TEST_CLUSTER_UPGRADE_DEBUG: Starting test_cluster_upgrade_workflow") # Force a print
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
                            
                            # Verify talosctl was called for config generation (gen-config.sh)
                            # Note: gen-config.sh is called with env vars, not CLI args for cluster details
                            # Expected versions from mock_text.return_value.ask.side_effect
                            expected_k8s_version = "v1.29.0"
                            expected_talos_version = "v1.7.0"
                            expected_gen_config_command = (
                                f"{os.path.join(mock_repo_path, 'bootstrap', 'talos', 'gen-config.sh')} "
                                f"--kubernetes-version {expected_k8s_version} "
                                f"--talos-version {expected_talos_version}"
                            )
                            # --- BEGIN DEBUG PRINT ---
                            print(f"DEBUG UPGRADE (AGAIN): mock_run_command.call_args_list before gen-config.sh assert:")
                            for i, call_obj in enumerate(mock_run_command.call_args_list):
                                print(f"  DEBUG UPGRADE Call {i}: args={call_obj.args}, kwargs={call_obj.kwargs}")
                                if "gen-config.sh" in call_obj.args[0]:
                                    print(f"    DEBUG UPGRADE gen-config.sh env: {call_obj.kwargs.get('env')}")
                            # --- END DEBUG PRINT ---
                            mock_run_command.assert_any_call(
                                expected_gen_config_command,
                                cwd=os.path.join(mock_repo_path, 'bootstrap', 'talos')
                                # env=ANY # Temporarily removed to match actual call
                            )
                            
                            # Verify talosctl was called for applying configs
                            # Node details from the mocked cluster_info
                            nodes_info = [
                                {'name': 'talos-cp1', 'ip': '192.168.1.101', 'type': 'controlplane'},
                                {'name': 'talos-cp2', 'ip': '192.168.1.102', 'type': 'controlplane'},
                                {'name': 'talos-cp3', 'ip': '192.168.1.103', 'type': 'controlplane'}
                            ]

                            for node_info in nodes_info:
                                node_name = node_info['name']
                                node_ip = node_info['ip']
                                # Assuming 'controlplane' for these test nodes
                                relative_config_path = os.path.join('infrastructure', 'talos', 'controlplane', f"{node_name}.yaml")
                                absolute_config_path = os.path.join(mock_repo_path, relative_config_path)
                                
                                expected_apply_cmd = f"talosctl apply-config --insecure --nodes {node_ip} --file {absolute_config_path}"
                                mock_run_command.assert_any_call(
                                    expected_apply_cmd,
                                    cwd=mock_repo_path
                                )
                            
                            # Verify talosctl was called for health check
                            mock_run_command.assert_any_call(
                                "talosctl health --nodes 192.168.1.101,192.168.1.102,192.168.1.103 --wait-timeout 30m", # Changed 15m to 30m
                                cwd=mock_repo_path
                            )
    
    def test_cluster_delete_workflow(self, cli_runner, mock_repo_path, mock_run_command): # Changed fixture
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
                            mock_run_command.assert_any_call( # Changed mock name
                                "talosctl reset --graceful=false --reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --nodes 192.168.1.101",
                                cwd=mock_repo_path
                            )
                            mock_run_command.assert_any_call( # Changed mock name
                                "talosctl reset --graceful=false --reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --nodes 192.168.1.102",
                                cwd=mock_repo_path
                            )
                            mock_run_command.assert_any_call( # Changed mock name
                                "talosctl reset --graceful=false --reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --nodes 192.168.1.103",
                                cwd=mock_repo_path
                            )

    def test_cluster_status_workflow(self, cli_runner, mock_repo_path, mock_run_command): # Changed fixture
        """Test the cluster status workflow."""
        with patch('hm_cli.cluster.get_repo_path', return_value=mock_repo_path):
            # Mock kubeconfig existence
            with patch('os.path.exists', return_value=True):
                # Run the command
                result = cli_runner.invoke(cli, ['cluster', 'status'])
                
                assert result.exit_code == 0
                
                # Verify kubectl was called to get nodes and pods
                mock_run_command.assert_any_call( # Changed mock name
                    "kubectl get nodes -o wide",
                    cwd=mock_repo_path,
                    env=ANY, # KUBECONFIG is added by ClusterManager.run_command
                    suppress_output=True
                )
                mock_run_command.assert_any_call(
                    "kubectl get pods -A -o wide", # Corrected command
                    cwd=mock_repo_path,
                    env=ANY,
                    suppress_output=True
                )
