#!/usr/bin/env python3
"""
Quick test script to validate MACHETE Python backend imports
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all our modules can be imported"""
    print("🔪 MACHETE Backend Import Test")
    print("=" * 50)
    
    try:
        print("✓ Testing FastAPI import...")
        from fastapi import FastAPI
        
        print("✓ Testing app.core.config import...")
        from app.core.config import settings
        print(f"  - App Name: {settings.APP_NAME}")
        print(f"  - Port: {settings.PORT}")
        
        print("✓ Testing model imports...")
        from app.models.tool import Tool, ToolStatus, ToolType
        from app.models.user import User
        
        print("✓ Testing service imports...")
        from app.services.tool_service import ToolService
        from app.services.docker_service import DockerService
        from app.services.git_service import GitService
        
        print("✓ Testing API router imports...")
        from app.api.health import router as health_router
        from app.api.tools import router as tools_router
        
        print("\n🎉 All imports successful!")
        print("✅ Backend structure is valid")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"   Module: {e.name if hasattr(e, 'name') else 'Unknown'}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
