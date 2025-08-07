"""
Simple system diagnostics API endpoints - test version
"""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime

router = APIRouter(tags=["system"])

@router.get("/diagnostics")
async def simple_diagnostics() -> Dict[str, Any]:
    """
    Simple system diagnostics endpoint for testing
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "message": "Simple diagnostics working"
    }
