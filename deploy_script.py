#!/usr/bin/env python3
"""Deploy K3 Locally Using VMs."""

import argparse
import json
import subprocess
import sys
import time

from loguru import logger

BASE_CONFIG = {"cpu": "2", "memory": "2G", "disk": "10G"}
VM_WAIT_TIME = 10
CLUSTER_WAIT_TIME = 30


class MultipassK3sDeployer:
    """Class for K3s VM Based Deployment."""

    def __init__(self, num_workers: int):
        """Init."""
        # Master node config
        self.nodes = [dict({"name": "k3s-master"}, **BASE_CONFIG)]
        # Config for the desired number of workers
        for i in range(num_workers):
            self.nodes.append(dict({"name": f"k3s-worker{i}"}, **BASE_CONFIG))

    @staticmethod
    def run_command(command: list, *, check: bool = True) -> subprocess.CompletedProcess:
        """Subprocess run command wrapper."""
        try:
            return subprocess.run(command, check=check, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running command: {' '.join(command)}")
            logger.info(f"Error output: {e.stderr}")
            raise

    def create_vms(self) -> None:
        """Create VM using multipass."""
        for node in self.nodes:
            logger.info(f"Creating VM: {node['name']}")
            try:
                self.run_command(
                    [
                        "multipass", "launch",
                        "--name", node["name"],
                        "--cpus", node["cpu"],
                        "--memory", node["memory"],
                        "--disk", node["disk"],
                    ]
                )
            except subprocess.CalledProcessError as e:
                if "already exists" in e.stderr:
                    logger.info(f"VM {node['name']} already exists, skipping creation")
                else:
                    raise

    def get_vm_ip(self, name: str) -> str:
        """Get VM IP Address from VM name."""
        result = self.run_command(["multipass", "info", name, "--format", "json"])
        info = json.loads(result.stdout)
        return info["info"][name]["ipv4"][0]

    def setup_k3s(self) -> None:
        """Set up the k3s."""
        master_ip = self.get_vm_ip("k3s-master")

        logger.debug("Installing k3s on master node...")
        self.run_command(["multipass", "exec", "k3s-master", "--", "bash", "-c", "curl -sfL https://get.k3s.io | sh -"])

        logger.debug("Getting node token...")
        result = self.run_command(
            ["multipass", "exec", "k3s-master", "--", "sudo", "cat", "/var/lib/rancher/k3s/server/node-token"]
        )
        node_token = result.stdout.strip()

        for node in self.nodes[1:]:  # Skip master node
            logger.debug(f"Installing k3s on {node['name']}...")
            self.run_command(
                [
                    "multipass",
                    "exec",
                    node["name"],
                    "--",
                    "bash",
                    "-c",
                    f'curl -sfL https://get.k3s.io | K3S_URL="https://{master_ip}:6443" K3S_TOKEN="{node_token}" sh -',
                ]
            )

    def setup_kubectl_locally(self) -> None:
        """Set up the kubectl config."""
        logger.debug("Setting up kubectl configuration locally...")

        # Get kubeconfig from master node
        result = self.run_command(["multipass", "exec", "k3s-master", "--", "sudo", "cat", "/etc/rancher/k3s/k3s.yaml"])

        # Replace default localhost with master node IP
        master_ip = self.get_vm_ip("k3s-master")
        kubeconfig = result.stdout.replace("127.0.0.1", master_ip)

        # Save to temporary file
        with open("k3s.yaml", "w") as f:
            f.write(kubeconfig)

        logger.debug("Kubeconfig saved to k3s.yaml")

    def deploy(self) -> None:
        """Start VMs and Deploy K3s."""
        logger.debug("Starting deployment of local k3s cluster...")
        self.create_vms()
        time.sleep(VM_WAIT_TIME)
        self.setup_k3s()
        time.sleep(CLUSTER_WAIT_TIME)
        self.setup_kubectl_locally()

        logger.info("Cluster deployment complete!")
        logger.info("To verify the cluster:")
        logger.info("1. export KUBECONFIG=$PWD/k3s.yaml")
        logger.info("2. kubectl get nodes")

        logger.debug("\nNode IPs:")
        for node in self.nodes:
            ip = self.get_vm_ip(node["name"])
            logger.debug(f"{node['name']}: {ip}")

    def cleanup(self) -> None:
        """Clean up existing vms."""
        logger.info("Cleaning up existing VMs...")
        for node in self.nodes:
            try:
                self.run_command(["multipass", "delete", node["name"]], check=False)
                self.run_command(["multipass", "purge"], check=False)
            except subprocess.CalledProcessError:
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy K3S cluster")
    parser.add_argument("--workers", type=int, help="Number of workers to deploy", default=3, required=False)
    parser.add_argument("--cleanup", action="store_true", required=False, help="Clean up existing cluster")
    parser.add_argument(
        "-l",
        "--log-level",
        default="INFO",  # Default log level
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stdout, colorize=True, format="<level>{message}</level>", level=args.log_level)

    deployer = MultipassK3sDeployer(args.workers)
    if args.cleanup:
        deployer.cleanup()
    else:
        deployer.deploy()
