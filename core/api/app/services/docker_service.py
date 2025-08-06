"""
Docker service for container management
"""

import asyncio
import docker
from typing import Dict, List, Optional, Any
from app.core.config import settings
from app.models.tool import Tool, ToolStatus
import logging

logger = logging.getLogger(__name__)

class DockerService:
    """Service for managing Docker containers"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.network_name = settings.DOCKER_NETWORK
    
    async def build_image(self, tool: Tool, build_context: str) -> Dict[str, Any]:
        """Build Docker image for a tool"""
        try:
            image_name = f"machete-{tool.name}"
            
            # Build the image
            image, build_logs = self.client.images.build(
                path=build_context,
                dockerfile=tool.dockerfile_path,
                tag=image_name,
                rm=True,
                timeout=settings.TOOL_BUILD_TIMEOUT
            )
            
            # Collect build logs
            logs = []
            for log in build_logs:
                if 'stream' in log:
                    logs.append(log['stream'].strip())
            
            return {
                "success": True,
                "image_id": image.id,
                "image_name": image_name,
                "logs": "\n".join(logs)
            }
            
        except docker.errors.BuildError as e:
            logger.error(f"Build failed for tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": "\n".join([log.get('stream', '') for log in e.build_log if 'stream' in log])
            }
        except Exception as e:
            logger.error(f"Unexpected error building tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": ""
            }
    
    async def start_container(self, tool: Tool) -> Dict[str, Any]:
        """Start a container for a tool"""
        try:
            image_name = f"machete-{tool.name}"
            container_name = f"machete-tool-{tool.name}"
            
            # Parse environment variables
            env_vars = {}
            if tool.environment_variables:
                import json
                env_vars = json.loads(tool.environment_variables)
            
            # Parse volumes
            volumes = {}
            if tool.volumes:
                import json
                volumes = json.loads(tool.volumes)
            
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
            logger.error(f"Unexpected error starting container for tool {tool.name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stop_container(self, container_id: str) -> bool:
        """Stop a container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            return True
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return True  # Already stopped
        except Exception as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            return False
    
    async def remove_container(self, container_id: str) -> bool:
        """Remove a container"""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            return True
        except docker.errors.NotFound:
            logger.warning(f"Container {container_id} not found")
            return True  # Already removed
        except Exception as e:
            logger.error(f"Error removing container {container_id}: {e}")
            return False
    
    async def get_container_status(self, container_id: str) -> ToolStatus:
        """Get container status"""
        try:
            container = self.client.containers.get(container_id)
            status = container.status
            
            if status == "running":
                return ToolStatus.RUNNING
            elif status == "exited":
                return ToolStatus.STOPPED
            elif status in ["created", "restarting"]:
                return ToolStatus.PENDING
            else:
                return ToolStatus.UNKNOWN
                
        except docker.errors.NotFound:
            return ToolStatus.STOPPED
        except Exception as e:
            logger.error(f"Error getting container status {container_id}: {e}")
            return ToolStatus.UNKNOWN
    
    async def health_check(self, tool: Tool) -> bool:
        """Perform health check on a tool"""
        if not tool.container_id or not tool.port:
            return False
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                url = f"http://localhost:{tool.port}{tool.health_check_endpoint}"
                response = await client.get(url, timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Health check failed for tool {tool.name}: {e}")
            return False
    
    async def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """Get container logs"""
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True)
            return logs.decode('utf-8') if isinstance(logs, bytes) else str(logs)
        except Exception as e:
            logger.error(f"Error getting logs for container {container_id}: {e}")
            return f"Error retrieving logs: {e}"
    
    def cleanup_unused_images(self):
        """Clean up unused Docker images"""
        try:
            self.client.images.prune()
            logger.info("Cleaned up unused Docker images")
        except Exception as e:
            logger.error(f"Error cleaning up images: {e}")
    
    def ensure_network_exists(self):
        """Ensure the MACHETE network exists"""
        try:
            self.client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.client.networks.create(
                self.network_name,
                driver="bridge"
            )
            logger.info(f"Created Docker network: {self.network_name}")
        except Exception as e:
            logger.error(f"Error ensuring network exists: {e}")
