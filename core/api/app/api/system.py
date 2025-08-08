"""
System diagnostics API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from datetime import datetime
import platform
import subprocess

from app.core.database import get_db_session
from app.services.tool_service import ToolService
from app.models.tool import Tool

router = APIRouter(tags=["system"])
tool_service = ToolService()

@router.get("/diagnostics")
async def system_diagnostics(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """
    System diagnostics endpoint for troubleshooting
    """
    try:
        diagnostics: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "docker_status": {},
            "database_status": {},
            "git_status": {},
            "system_info": {}
        }
        
        # Check Docker availability
        try:
            docker_available = tool_service.docker_service.is_available
            docker_info = None
            if docker_available:
                try:
                    # Try to get basic Docker info
                    docker_info = {
                        "service_type": "DockerService",
                        "status": "available"
                    }
                except Exception:
                    docker_info = {"status": "available_but_limited"}
            
            diagnostics["docker_status"] = {
                "available": docker_available,
                "client_info": docker_info
            }
        except Exception as e:
            diagnostics["docker_status"] = {
                "available": False,
                "error": str(e)
            }
        
        # Check database connection
        try:
            result = await db.execute(select(Tool))
            tools = result.scalars().all()
            tool_count = len(tools)
            
            diagnostics["database_status"] = {
                "connected": True,
                "tool_count": tool_count
            }
        except Exception as e:
            diagnostics["database_status"] = {
                "connected": False,
                "error": str(e)
            }
        
        # Check Git availability
        try:
            git_result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
            diagnostics["git_status"] = {
                "available": git_result.returncode == 0,
                "version": git_result.stdout.strip() if git_result.returncode == 0 else None
            }
        except Exception as e:
            diagnostics["git_status"] = {
                "available": False,
                "error": str(e)
            }
        
        # System information
        diagnostics["system_info"] = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "architecture": platform.architecture()
        }
        
        return {
            "success": True,
            "diagnostics": diagnostics
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Diagnostics failed: {str(e)}"
        }
