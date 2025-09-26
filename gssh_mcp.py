#!/usr/bin/env python3
"""
SSH/GCloud MCP Server - Control remote systems via MCP
"""

import asyncio
import subprocess
import json
import os

from typing import Any, Dict, List, Optional
import paramiko

from google.cloud import compute_v1
from mcp.server import Server
from mcp.types import Tool, TextContent



# SSH Connection Manager
class SSHManager:
    def __init__(self):
        self.connections: Dict[str, paramiko.SSHClient] = {}
    
    async def connect(self, host: str, username: str, key_path: Optional[str] = None, password: Optional[str] = None):
        """Establish SSH connection"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            if key_path:
                client.connect(host, username=username, key_filename=key_path)
            else:
                client.connect(host, username=username, password=password)
            
            self.connections[host] = client
            return f"Connected to {host} as {username}"
        except Exception as e:
            return f"Failed to connect to {host}: {str(e)}"
    
    async def execute_command(self, host: str, command: str) -> Dict[str, Any]:
        """Execute command on remote host"""
        if host not in self.connections:
            return {"error": f"No connection to {host}"}
        
        try:
            stdin, stdout, stderr = self.connections[host].exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            exit_code = stdout.channel.recv_exit_status()
            
            return {
                "command": command,
                "exit_code": exit_code,
                "stdout": output,
                "stderr": error,
                "success": exit_code == 0
            }
        except Exception as e:
            return {"error": str(e), "success": False}



# GCloud Manager
class GCloudManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.compute_client = compute_v1.InstancesClient()
    
    async def list_instances(self, zone: str = "us-central1-a") -> List[Dict]:
        """List GCE instances"""
        try:
            instances = []
            for instance in self.compute_client.list(project=self.project_id, zone=zone):
                instances.append({
                    "name": instance.name,
                    "status": instance.status,
                    "machine_type": instance.machine_type.split('/')[-1],
                    "zone": zone,
                    "internal_ip": instance.network_interfaces[0].network_i_p if instance.network_interfaces else None,
                    "external_ip": instance.network_interfaces[0].access_configs[0].nat_i_p if instance.network_interfaces and instance.network_interfaces[0].access_configs else None
                })
            return instances
        except Exception as e:
            return [{"error": str(e)}]
    
    async def start_instance(self, instance_name: str, zone: str = "us-central1-a"):
        """Start GCE instance"""
        try:
            operation = self.compute_client.start(
                project=self.project_id, 
                zone=zone, 
                instance=instance_name
            )
            return f"Started instance {instance_name}"
        except Exception as e:
            return f"Failed to start {instance_name}: {str(e)}"
    
    async def stop_instance(self, instance_name: str, zone: str = "us-central1-a"):
        """Stop GCE instance"""
        try:
            operation = self.compute_client.stop(
                project=self.project_id, 
                zone=zone, 
                instance=instance_name
            )
            return f"Stopped instance {instance_name}"
        except Exception as e:
            return f"Failed to stop {instance_name}: {str(e)}"



# Initialize managers
ssh_manager = SSHManager()
gcloud_manager = None  # Initialized when project_id is provided

# MCP Server setup
server = Server("ssh-gcloud-mcp")

@server.tool()
async def ssh_connect(host: str, username: str, key_path: Optional[str] = None, password: Optional[str] = None) -> str:
    """Connect to remote host via SSH"""
    result = await ssh_manager.connect(host, username, key_path, password)
    return result


@server.tool()
async def ssh_execute(host: str, command: str) -> str:
    """Execute command on remote SSH host"""
    result = await ssh_manager.execute_command(host, command)
    return json.dumps(result, indent=2)


@server.tool()
async def gcloud_list_instances(project_id: str, zone: str = "us-central1-a") -> str:
    """List Google Cloud instances"""
    global gcloud_manager
    if not gcloud_manager:
        gcloud_manager = GCloudManager(project_id)
    
    instances = await gcloud_manager.list_instances(zone)
    return json.dumps(instances, indent=2)


@server.tool()
async def gcloud_start_instance(project_id: str, instance_name: str, zone: str = "us-central1-a") -> str:
    """Start Google Cloud instance"""
    global gcloud_manager
    if not gcloud_manager:
        gcloud_manager = GCloudManager(project_id)
    
    result = await gcloud_manager.start_instance(instance_name, zone)
    return result

@server.tool()
async def gcloud_stop_instance(project_id: str, instance_name: str, zone: str = "us-central1-a") -> str:
    """Stop Google Cloud instance"""
    global gcloud_manager
    if not gcloud_manager:
        gcloud_manager = GCloudManager(project_id)
    
    result = await gcloud_manager.stop_instance(instance_name, zone)
    return result


@server.tool()
async def deploy_to_gcloud(host: str, project_id: str, app_path: str, service_name: str) -> str:
    """Deploy application to Google Cloud via SSH"""
    commands = [
        f"cd {app_path}",
        f"gcloud app deploy --project {project_id} --quiet",
        f"gcloud app services set-traffic {service_name} --splits=DEPLOYED_VERSION=1"
    ]
    
    results = []
    for cmd in commands:
        result = await ssh_manager.execute_command(host, cmd)
        results.append(result)
        if not result.get("success", False):
            break
    
    return json.dumps(results, indent=2)


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as streams:
        await server.run(*streams)



if __name__ == "__main__":
    asyncio.run(main())
