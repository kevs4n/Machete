"""
Tool service for managing MACHETE tools
"""

import asyncio
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.tool import Tool, ToolStatus, ToolType
from app.services.docker_service import DockerService
from app.services.docker_service_enhanced import DockerServiceEnhanced
from app.services.git_service import GitService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ToolService:
    """Service for managing tools"""
    
    def __init__(self):
        self.docker_service = DockerService()
        self.docker_service_enhanced = DockerServiceEnhanced()
        self.git_service = GitService()
    
    async def create_tool(self, db: AsyncSession, tool_data: Dict[str, Any]) -> Tool:
        """Create a new tool"""
        tool = Tool(**tool_data)
        db.add(tool)
        await db.commit()
        await db.refresh(tool)
        return tool
    
    async def get_tool(self, db: AsyncSession, tool_id: int) -> Optional[Tool]:
        """Get a tool by ID"""
        result = await db.execute(select(Tool).where(Tool.id == tool_id))
        return result.scalar_one_or_none()
    
    async def get_tool_by_name(self, db: AsyncSession, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        result = await db.execute(select(Tool).where(Tool.name == name))
        return result.scalar_one_or_none()
    
    async def get_tools(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Tool]:
        """Get all tools with pagination"""
        result = await db.execute(select(Tool).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update_tool(self, db: AsyncSession, tool_id: int, tool_data: Dict[str, Any]) -> Optional[Tool]:
        """Update a tool"""
        await db.execute(
            update(Tool)
            .where(Tool.id == tool_id)
            .values(**tool_data)
        )
        await db.commit()
        return await self.get_tool(db, tool_id)
    
    async def delete_tool(self, db: AsyncSession, tool_id: int) -> bool:
        """Delete a tool"""
        tool = await self.get_tool(db, tool_id)
        if not tool:
            return False
        
        # Stop and remove container if running
        if tool.container_id:
            await self.stop_tool(db, tool_id)
        
        await db.execute(delete(Tool).where(Tool.id == tool_id))
        await db.commit()
        return True
    
    async def install_tool(self, db: AsyncSession, git_url: str, name: str = None, 
                          branch: str = "main") -> Dict[str, Any]:
        """Install a tool from Git repository"""
        try:
            # Validate repository first
            validation = await self.git_service.validate_repository(git_url, branch)
            if not validation["success"]:
                return {
                    "success": False,
                    "error": f"Repository validation failed: {validation.get('error', 'Unknown error')}"
                }
            
            # Clone repository
            clone_result = await self.git_service.clone_repository(git_url, branch)
            if not clone_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to clone repository: {clone_result.get('error', 'Unknown error')}"
                }
            
            repo_path = clone_result["path"]
            
            try:
                # Extract tool metadata
                metadata = await self.git_service.extract_tool_metadata(repo_path)
                
                # Use provided name or extract from metadata
                tool_name = name or metadata.get("name") or git_url.split("/")[-1].replace(".git", "")
                
                # Check if tool already exists
                existing_tool = await self.get_tool_by_name(db, tool_name)
                if existing_tool:
                    return {
                        "success": False,
                        "error": f"Tool '{tool_name}' already exists"
                    }
                
                # Create tool record
                tool_data = {
                    "name": tool_name,
                    "display_name": metadata.get("description", tool_name).split('.')[0][:255],
                    "description": metadata.get("description"),
                    "git_url": git_url,
                    "git_branch": branch,
                    "git_commit": clone_result["commit_hash"],
                    "tool_type": ToolType.WEB,  # Default, can be configured later
                    "status": ToolStatus.PENDING,
                    "dockerfile_path": metadata.get("dockerfile_path", "Dockerfile"),
                    "port": metadata.get("port", settings.TOOL_DEFAULT_PORT),
                    "health_check_endpoint": metadata.get("health_check", settings.TOOL_DEFAULT_HEALTH_CHECK),
                    "version": metadata.get("version"),
                    "author": metadata.get("author"),
                    "license": metadata.get("license")
                }
                
                # Add Docker Compose support
                if metadata.get("has_compose"):
                    tool_data["has_compose"] = True
                    tool_data["compose_file"] = metadata.get("compose_file", "docker-compose.yml")
                
                # Add volumes configuration
                if metadata.get("volumes"):
                    import json
                    # Convert list format to dict format for Docker API
                    volumes_dict = {}
                    for volume in metadata["volumes"]:
                        if ":" in volume:
                            host_path, container_path = volume.split(":", 1)
                            volumes_dict[host_path] = container_path
                    tool_data["volumes"] = json.dumps(volumes_dict)
                
                # Add environment variables
                if metadata.get("environment"):
                    import json
                    env_dict = {}
                    for env_var in metadata["environment"]:
                        if "=" in env_var:
                            key, value = env_var.split("=", 1)
                            env_dict[key] = value
                    tool_data["environment_variables"] = json.dumps(env_dict)
                
                tool = await self.create_tool(db, tool_data)
                
                # Build the tool
                build_result = await self.build_tool(db, tool.id, repo_path)
                
                return {
                    "success": True,
                    "tool_id": tool.id,
                    "tool_name": tool.name,
                    "build_success": build_result["success"],
                    "build_message": build_result.get("message", "")
                }
                
            finally:
                # Clean up cloned repository
                self.git_service.cleanup_repository(repo_path)
                
        except Exception as e:
            logger.error(f"Error installing tool from {git_url}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def build_tool(self, db: AsyncSession, tool_id: int, build_context: str = None) -> Dict[str, Any]:
        """Build a tool's Docker image"""
        tool = await self.get_tool(db, tool_id)
        if not tool:
            return {"success": False, "error": "Tool not found"}
        
        try:
            # Update status to building
            await self.update_tool(db, tool_id, {"status": ToolStatus.BUILDING})
            
            # If no build context provided, clone the repository
            temp_repo = None
            if not build_context:
                clone_result = await self.git_service.clone_repository(tool.git_url, tool.git_branch)
                if not clone_result["success"]:
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.FAILED,
                        "error_message": f"Failed to clone repository: {clone_result.get('error')}"
                    })
                    return {"success": False, "error": clone_result.get("error")}
                
                build_context = clone_result["path"]
                temp_repo = build_context
            
            try:
                # Build Docker image
                build_result = await self.docker_service.build_image(tool, build_context)
                
                if build_result["success"]:
                    # Update tool with build success
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.STOPPED,
                        "build_log": build_result.get("logs", ""),
                        "error_message": None
                    })
                    return {"success": True, "message": "Build completed successfully"}
                else:
                    # Update tool with build failure
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.FAILED,
                        "build_log": build_result.get("logs", ""),
                        "error_message": build_result.get("error", "Build failed")
                    })
                    return {"success": False, "error": build_result.get("error", "Build failed")}
                    
            finally:
                # Clean up temporary repository if we created one
                if temp_repo:
                    self.git_service.cleanup_repository(temp_repo)
                    
        except Exception as e:
            logger.error(f"Error building tool {tool_id}: {e}")
            await self.update_tool(db, tool_id, {
                "status": ToolStatus.FAILED,
                "error_message": str(e)
            })
            return {"success": False, "error": str(e)}
    
    async def start_tool(self, db: AsyncSession, tool_id: int) -> Dict[str, Any]:
        """Start a tool container or compose stack"""
        tool = await self.get_tool(db, tool_id)
        if not tool:
            return {"success": False, "error": "Tool not found"}
        
        if tool.status == ToolStatus.RUNNING:
            return {"success": True, "message": "Tool is already running"}
        
        try:
            # Check if tool uses Docker Compose
            if getattr(tool, 'has_compose', False) and tool.compose_file:
                logger.info(f"Starting Docker Compose stack for tool {tool.name}")
                
                # Prepare tool directory path
                tool_path = f"{settings.TOOLS_DATA_PATH}/{tool.name}"
                
                # Start compose stack using enhanced service
                start_result = await self.docker_service_enhanced.start_compose_stack(
                    tool_path, 
                    tool.compose_file,
                    tool_name=tool.name
                )
                
                if start_result["success"]:
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.RUNNING,
                        "container_id": start_result.get("stack_id", f"compose-{tool.name}"),
                        "container_name": f"compose-stack-{tool.name}",
                        "error_message": None
                    })
                    return {
                        "success": True, 
                        "message": f"Docker Compose stack started successfully",
                        "services": start_result.get("services", [])
                    }
                else:
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.FAILED,
                        "error_message": start_result.get("error", "Failed to start compose stack")
                    })
                    return {"success": False, "error": start_result.get("error", "Failed to start compose stack")}
            
            else:
                # Use regular Docker service for single containers
                logger.info(f"Starting single container for tool {tool.name}")
                start_result = await self.docker_service.start_container(tool)
                
                if start_result["success"]:
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.RUNNING,
                        "container_id": start_result["container_id"],
                        "container_name": start_result["container_name"],
                        "error_message": None
                    })
                    return {"success": True, "message": "Tool started successfully"}
                else:
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.FAILED,
                        "error_message": start_result.get("error", "Failed to start container")
                    })
                    return {"success": False, "error": start_result.get("error", "Failed to start container")}
                
        except Exception as e:
            logger.error(f"Error starting tool {tool_id}: {e}")
            await self.update_tool(db, tool_id, {
                "status": ToolStatus.FAILED,
                "error_message": str(e)
            })
            return {"success": False, "error": str(e)}
    
    async def stop_tool(self, db: AsyncSession, tool_id: int) -> Dict[str, Any]:
        """Stop a tool container or compose stack"""
        tool = await self.get_tool(db, tool_id)
        if not tool:
            return {"success": False, "error": "Tool not found"}
        
        if not tool.container_id:
            return {"success": True, "message": "Tool is not running"}
        
        try:
            # Check if tool uses Docker Compose
            if getattr(tool, 'has_compose', False) and tool.compose_file:
                logger.info(f"Stopping Docker Compose stack for tool {tool.name}")
                
                # Prepare tool directory path
                tool_path = f"{settings.TOOLS_DATA_PATH}/{tool.name}"
                
                # Stop compose stack using enhanced service
                stop_result = await self.docker_service_enhanced.stop_compose_stack(
                    tool_path, 
                    tool.compose_file
                )
                
                if stop_result["success"]:
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.STOPPED,
                        "error_message": None
                    })
                    return {"success": True, "message": "Docker Compose stack stopped successfully"}
                else:
                    return {"success": False, "error": stop_result.get("error", "Failed to stop compose stack")}
            
            else:
                # Use regular Docker service for single containers
                logger.info(f"Stopping single container for tool {tool.name}")
                stop_result = await self.docker_service.stop_container(tool.container_id)
                
                if stop_result:
                    await self.update_tool(db, tool_id, {
                        "status": ToolStatus.STOPPED,
                        "error_message": None
                    })
                    return {"success": True, "message": "Tool stopped successfully"}
                else:
                    return {"success": False, "error": "Failed to stop container"}
                
        except Exception as e:
            logger.error(f"Error stopping tool {tool_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def restart_tool(self, db: AsyncSession, tool_id: int) -> Dict[str, Any]:
        """Restart a tool"""
        # Stop the tool first
        stop_result = await self.stop_tool(db, tool_id)
        if not stop_result["success"]:
            return stop_result
        
        # Wait a moment for cleanup
        await asyncio.sleep(2)
        
        # Start the tool
        return await self.start_tool(db, tool_id)
    
    async def update_tool_status(self, db: AsyncSession, tool_id: int) -> Dict[str, Any]:
        """Update tool status based on container state"""
        tool = await self.get_tool(db, tool_id)
        if not tool or not tool.container_id:
            return {"success": False, "error": "Tool not found or not containerized"}
        
        try:
            # Get current container status
            container_status = await self.docker_service.get_container_status(tool.container_id)
            
            # Update tool status if changed
            if tool.status != container_status:
                await self.update_tool(db, tool_id, {"status": container_status})
            
            return {
                "success": True,
                "status": container_status,
                "changed": tool.status != container_status
            }
            
        except Exception as e:
            logger.error(f"Error updating tool status {tool_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_tool_logs(self, db: AsyncSession, tool_id: int, tail: int = 100) -> Dict[str, Any]:
        """Get tool container logs"""
        tool = await self.get_tool(db, tool_id)
        if not tool or not tool.container_id:
            return {"success": False, "error": "Tool not found or not containerized"}
        
        try:
            logs = await self.docker_service.get_container_logs(tool.container_id, tail)
            return {"success": True, "logs": logs}
        except Exception as e:
            logger.error(f"Error getting tool logs {tool_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def health_check_tool(self, db: AsyncSession, tool_id: int) -> Dict[str, Any]:
        """Perform health check on a tool"""
        tool = await self.get_tool(db, tool_id)
        if not tool:
            return {"success": False, "error": "Tool not found"}
        
        try:
            is_healthy = await self.docker_service.health_check(tool)
            
            # Update last health check time
            from datetime import datetime
            await self.update_tool(db, tool_id, {"last_health_check": datetime.utcnow()})
            
            return {"success": True, "healthy": is_healthy}
        except Exception as e:
            logger.error(f"Error performing health check for tool {tool_id}: {e}")
            return {"success": False, "error": str(e)}
