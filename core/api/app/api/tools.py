"""
Tool management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db_session
from app.services.tool_service import ToolService
from app.models.tool import Tool, ToolStatus, ToolType

router = APIRouter(prefix="/tools", tags=["tools"])
tool_service = ToolService()

# Pydantic models for request/response
class ToolCreate(BaseModel):
    git_url: str
    name: Optional[str] = None
    branch: str = "main"

class ToolResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    git_url: str
    git_branch: str
    status: ToolStatus
    tool_type: ToolType
    port: Optional[int] = None
    version: Optional[str] = None
    author: Optional[str] = None
    enabled: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ToolStatusUpdate(BaseModel):
    enabled: Optional[bool] = None
    auto_start: Optional[bool] = None

@router.get("/", response_model=List[ToolResponse])
async def get_tools(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Get all tools"""
    tools = await tool_service.get_tools(db, skip=skip, limit=limit)
    return tools

@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific tool"""
    tool = await tool_service.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    return tool

@router.post("/install")
async def install_tool(
    tool_data: ToolCreate,
    db: AsyncSession = Depends(get_db_session)
):
    """Install a tool from Git repository"""
    result = await tool_service.install_tool(
        db, 
        tool_data.git_url, 
        tool_data.name or "", 
        tool_data.branch
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/{tool_id}/build")
async def build_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Build a tool's Docker image"""
    result = await tool_service.build_tool(db, tool_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/{tool_id}/start")
async def start_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Start a tool container"""
    result = await tool_service.start_tool(db, tool_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/{tool_id}/stop")
async def stop_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Stop a tool container"""
    result = await tool_service.stop_tool(db, tool_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.post("/{tool_id}/restart")
async def restart_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Restart a tool"""
    result = await tool_service.restart_tool(db, tool_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result

@router.get("/{tool_id}/status")
async def get_tool_status(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Get current tool status"""
    result = await tool_service.update_tool_status(db, tool_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.get("/{tool_id}/logs")
async def get_tool_logs(
    tool_id: int,
    tail: int = 100,
    db: AsyncSession = Depends(get_db_session)
):
    """Get tool container logs"""
    result = await tool_service.get_tool_logs(db, tool_id, tail)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.get("/{tool_id}/health")
async def health_check_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Perform health check on a tool"""
    result = await tool_service.health_check_tool(db, tool_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result

@router.patch("/{tool_id}")
async def update_tool_settings(
    tool_id: int,
    settings: ToolStatusUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update tool settings"""
    tool = await tool_service.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    update_data = {}
    if settings.enabled is not None:
        update_data["enabled"] = settings.enabled
    if settings.auto_start is not None:
        update_data["auto_start"] = settings.auto_start
    
    if update_data:
        updated_tool = await tool_service.update_tool(db, tool_id, update_data)
        return updated_tool
    
    return tool

@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a tool"""
    success = await tool_service.delete_tool(db, tool_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tool not found"
        )
    
    return {"message": "Tool deleted successfully"}
