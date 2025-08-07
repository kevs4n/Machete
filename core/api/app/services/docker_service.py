"""
Enhanced Docker service for container and compose management
"""

import asyncio
import docker
import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from app.core.config import settings
from app.models.tool import Tool, ToolStatus
import logging

logger = logging.getLogger(__name__)

class DockerService:
    """Enhanced service for managing Docker containers and compose stacks"""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.network_name = settings.DOCKER_NETWORK
            self.is_available = True
            logger.info("Docker client connected successfully")
        except Exception as e:
            logger.warning(f"Docker client unavailable: {e}")
            self.client = None
            self.network_name = None
            self.is_available = False

    async def build_image(self, tool: Tool, build_context: str) -> Dict[str, Any]:
        """Build Docker image for a tool"""
        if not self.is_available:
            return {
                "success": False,
                "error": "Docker service is not available",
                "logs": ["Docker client could not connect to Docker daemon"]
            }
            
        try:
            image_name = f"machete-{tool.name}"
            
            # Build the image
            image, build_logs = self.client.images.build(
                path=build_context,
                dockerfile=tool.dockerfile_path,
                tag=image_name,
                rm=True,
                forcerm=True
            )
            
            # Parse build logs
            logs = []
            for log in build_logs:
                if 'stream' in log:
                    logs.append(log['stream'].strip())
            
            return {
                "success": True,
                "image_id": image.id,
                "image_name": image_name,
                "logs": logs
            }
            
        except docker.errors.BuildError as e:
            logger.error(f"Build failed for tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": [log.get('stream', '') for log in e.build_log if 'stream' in log]
            }
        except Exception as e:
            logger.error(f"Unexpected error building tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": []
            }

    async def start_container(self, tool: Tool) -> Dict[str, Any]:
        """Start a container for a tool"""
        if not self.is_available:
            return {
                "success": False,
                "error": "Docker service is not available"
            }
            
        try:
            image_name = f"machete-{tool.name}"
            container_name = f"machete-tool-{tool.name}"
            
            # Parse environment variables
            env_vars = {}
            if tool.environment_variables:
                env_vars = json.loads(tool.environment_variables)
            
            # Parse and prepare volumes
            volumes = {}
            if tool.volumes:
                volume_config = json.loads(tool.volumes)
                volumes = self._prepare_volumes(tool.name, volume_config)
            
            # Start the container
            container = self.client.containers.run(
                image_name,
                name=container_name,
                ports={f'{tool.port}/tcp': tool.port} if tool.port else None,
                environment=env_vars,
                volumes=volumes,
                network=self.network_name,
                detach=True,
                remove=False,
                command=tool.command if tool.command else None
            )
            
            return {
                "success": True,
                "container_id": container.id,
                "container_name": container_name
            }
            
        except docker.errors.ContainerError as e:
            logger.error(f"Container failed to start for tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error starting tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def start_compose_stack(self, tool: Tool, compose_path: str) -> Dict[str, Any]:
        """Start a Docker Compose stack for a tool"""
        try:
            # Prepare environment for compose
            env = os.environ.copy()
            
            # Add tool-specific environment variables
            if tool.environment_variables:
                env_vars = json.loads(tool.environment_variables)
                env.update(env_vars)
            
            # Add MACHETE-specific variables
            env.update({
                'MACHETE_TOOL_NAME': tool.name,
                'MACHETE_TOOL_PORT': str(tool.port) if tool.port else '8080',
                'MACHETE_NETWORK': self.network_name,
                'MACHETE_DATA_DIR': f'/app/data/tools/{tool.name}'
            })
            
            # Change to the tool's directory
            compose_dir = Path(compose_path).parent
            
            # Run docker-compose up
            result = subprocess.run([
                'docker-compose', 
                '-f', compose_path,
                '-p', f'machete-{tool.name}',  # Project name
                'up', '-d'
            ], 
            cwd=compose_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Get container information
                containers = self._get_compose_containers(tool.name)
                
                return {
                    "success": True,
                    "message": "Compose stack started successfully",
                    "containers": containers,
                    "logs": result.stdout
                }
            else:
                logger.error(f"Compose failed for tool {tool.name}: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "logs": result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Compose startup timed out (5 minutes)"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "docker-compose command not found"
            }
        except Exception as e:
            logger.error(f"Unexpected error starting compose for tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def stop_compose_stack(self, tool: Tool, compose_path: str) -> Dict[str, Any]:
        """Stop a Docker Compose stack for a tool"""
        try:
            compose_dir = Path(compose_path).parent
            
            result = subprocess.run([
                'docker-compose',
                '-f', compose_path,
                '-p', f'machete-{tool.name}',
                'down'
            ],
            cwd=compose_dir,
            capture_output=True,
            text=True,
            timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "message": "Compose stack stopped" if result.returncode == 0 else "Failed to stop compose stack",
                "logs": result.stdout if result.returncode == 0 else result.stderr
            }
            
        except Exception as e:
            logger.error(f"Error stopping compose for tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _prepare_volumes(self, tool_name: str, volume_config: dict) -> dict:
        """Prepare volumes for container, ensuring host directories exist"""
        prepared_volumes = {}
        
        # Base directory for tool data
        tool_data_dir = Path(settings.TOOLS_DATA_PATH) / tool_name
        
        for host_path, container_path in volume_config.items():
            # Handle relative paths - make them relative to tool data directory
            if not host_path.startswith('/') and not host_path.startswith('C:'):
                # Relative path - create under tool data directory
                full_host_path = tool_data_dir / host_path.lstrip('./')
            else:
                # Absolute path - use as-is (but be careful!)
                full_host_path = Path(host_path)
            
            # Ensure the host directory exists
            try:
                full_host_path.parent.mkdir(parents=True, exist_ok=True)
                if not full_host_path.exists():
                    if container_path.endswith('/'):
                        # Directory mount
                        full_host_path.mkdir(parents=True, exist_ok=True)
                    else:
                        # File mount - create parent directory only
                        full_host_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Convert to Docker API format
                prepared_volumes[str(full_host_path)] = {
                    'bind': container_path, 
                    'mode': 'rw'
                }
                
                logger.info(f"Prepared volume mount: {full_host_path} -> {container_path}")
                
            except Exception as e:
                logger.warning(f"Failed to prepare volume {host_path}: {e}")
                continue
        
        return prepared_volumes

    def _get_compose_containers(self, tool_name: str) -> List[Dict[str, Any]]:
        """Get information about containers in a compose stack"""
        try:
            if not self.is_available:
                return []
                
            # Find containers with the project label
            containers = self.client.containers.list(
                filters={'label': f'com.docker.compose.project=machete-{tool_name}'}
            )
            
            container_info = []
            for container in containers:
                info = {
                    'id': container.id,
                    'name': container.name,
                    'status': container.status,
                    'ports': container.ports,
                    'labels': container.labels
                }
                container_info.append(info)
            
            return container_info
            
        except Exception as e:
            logger.error(f"Error getting compose containers for {tool_name}: {e}")
            return []

    async def get_container_logs(self, container_name: str, lines: int = 100) -> Dict[str, Any]:
        """Get logs from a container"""
        try:
            if not self.is_available:
                return {"success": False, "error": "Docker service unavailable"}
                
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
            
            return {
                "success": True,
                "logs": logs,
                "container_status": container.status
            }
            
        except docker.errors.NotFound:
            return {"success": False, "error": "Container not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Backward compatibility alias
DockerServiceEnhanced = DockerService
