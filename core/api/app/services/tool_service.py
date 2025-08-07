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
from app.services.docker_service import DockerService, DockerServiceEnhanced
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
    
    async def install_tool(self, db: AsyncSession, git_url: str, name: Optional[str] = None, 
                          branch: str = "main") -> Dict[str, Any]:
        """
        Enhanced tool installation with comprehensive error handling and logging
        """
        from datetime import datetime
        import traceback
        
        installation_log: Dict[str, Any] = {
            "git_url": git_url,
            "requested_name": name,
            "branch": branch,
            "steps_completed": [],
            "errors": [],
            "warnings": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        try:
            logger.info(f"🚀 Starting tool installation: {git_url}")
            
            # Step 1: Enhanced repository validation and cloning
            installation_log["steps_completed"].append("repository_validation")
            logger.info(f"📋 Step 1: Repository validation and cloning")
            
            clone_result = await self.git_service.validate_and_clone_repository(git_url)
            
            if not clone_result["success"]:
                installation_log["errors"].append({
                    "step": "repository_validation",
                    "error": clone_result["error"],
                    "error_code": clone_result["error_code"],
                    "troubleshooting": clone_result.get("troubleshooting", {})
                })
                installation_log["end_time"] = datetime.now().isoformat()
                
                return {
                    "success": False,
                    "error": clone_result["error"],
                    "error_code": clone_result["error_code"],
                    "installation_log": installation_log,
                    "troubleshooting": clone_result.get("troubleshooting", {}),
                    "import_context": clone_result.get("import_context", {})
                }
            
            repo_path = clone_result["repo_path"]
            metadata = clone_result["metadata"]
            docker_config = clone_result["docker_config"]
            
            # Step 2: Tool name resolution
            installation_log["steps_completed"].append("name_resolution")
            tool_name = name or metadata.get("name") or git_url.split("/")[-1].replace(".git", "")
            logger.info(f"🏷️ Step 2: Tool name resolved to: {tool_name}")
            
            # Step 3: Check for existing tool
            installation_log["steps_completed"].append("duplicate_check")
            existing_tool = await self.get_tool_by_name(db, tool_name)
            if existing_tool:
                installation_log["warnings"].append(f"Tool with name '{tool_name}' already exists")
                logger.warning(f"⚠️ Tool '{tool_name}' already exists")
                
                # Return error for duplicate
                installation_log["end_time"] = datetime.now().isoformat()
                return {
                    "success": False,
                    "error": f"Tool '{tool_name}' already exists",
                    "error_code": "TOOL_EXISTS",
                    "installation_log": installation_log
                }
            
            # Step 4: Create tool record
            installation_log["steps_completed"].append("database_storage")
            logger.info(f"💾 Step 4: Creating tool record in database")
            
            # Prepare tool data for database
            tool_data = {
                "name": tool_name,
                "display_name": metadata.get("description", tool_name).split('.')[0][:255],
                "description": metadata.get("description"),
                "git_url": git_url,
                "git_branch": branch,
                "git_commit": clone_result.get("import_context", {}).get("metadata", {}).get("commit_hash"),
                "tool_type": self._determine_tool_type(metadata),
                "status": ToolStatus.PENDING,
                "dockerfile_path": metadata.get("dockerfile_path", "Dockerfile"),
                "port": metadata.get("port", settings.TOOL_DEFAULT_PORT),
                "health_check_endpoint": metadata.get("health_check", settings.TOOL_DEFAULT_HEALTH_CHECK),
                "version": metadata.get("version"),
                "author": metadata.get("author"),
                "license": metadata.get("license"),
                "has_compose": metadata.get("has_compose", False),
                "compose_file": metadata.get("compose_file")
            }
            
            # Add volumes configuration
            if metadata.get("volumes"):
                volumes_dict = {}
                for volume in metadata["volumes"]:
                    if ":" in volume:
                        host_path, container_path = volume.split(":", 1)
                        volumes_dict[host_path] = container_path
                tool_data["volumes"] = json.dumps(volumes_dict)
            
            # Add environment variables
            if metadata.get("environment"):
                env_dict = {}
                for env_var in metadata["environment"]:
                    if "=" in env_var:
                        key, value = env_var.split("=", 1)
                        env_dict[key] = value
                tool_data["environment_variables"] = json.dumps(env_dict)
            
            tool = await self.create_tool(db, tool_data)
            logger.info(f"✨ Created tool record: {tool_name} (ID: {tool.id})")
            
            # Step 5: Docker image building (optional, can be done later)
            installation_log["steps_completed"].append("docker_build_preparation")
            logger.info(f"🏗️ Step 5: Preparing for Docker build")
            
            build_result = {"success": True, "message": "Build prepared, use start_tool to build and run"}
            if docker_config and not docker_config.get("valid", True):
                installation_log["warnings"].append("Docker configuration has warnings, review before starting")
                build_result["warnings"] = docker_config.get("warnings", [])
            
            # Step 6: Cleanup
            installation_log["steps_completed"].append("cleanup")
            self.git_service.cleanup_repository(repo_path)
            
            installation_log["end_time"] = datetime.now().isoformat()
            
            logger.info(f"🎉 Tool installation successful: {tool_name}")
            
            return {
                "success": True,
                "tool_id": tool.id,
                "tool_name": tool.name,
                "tool": {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "version": tool.version,
                    "has_compose": tool.has_compose,
                    "status": tool.status.value
                },
                "metadata": metadata,
                "docker_config": docker_config,
                "installation_log": installation_log,
                "build_result": build_result
            }
            
        except Exception as e:
            installation_log["end_time"] = datetime.now().isoformat()
            installation_log["errors"].append({
                "step": "unexpected_error",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            
            logger.error(f"💥 Unexpected error during tool installation: {str(e)}")
            
            return {
                "success": False,
                "error": f"Installation failed: {str(e)}",
                "error_code": "INSTALLATION_FAILED",
                "installation_log": installation_log
            }
    
    def _determine_tool_type(self, metadata: Dict[str, Any]) -> ToolType:
        """Determine tool type based on metadata"""
        if metadata.get("has_compose"):
            return ToolType.COMPOSE
        elif metadata.get("port"):
            return ToolType.WEB
        else:
            return ToolType.CLI
    
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
