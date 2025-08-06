"""
Tool model for the MACHETE platform
"""

from enum import Enum
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
import uuid

class ToolStatus(str, Enum):
    """Tool status enumeration"""
    PENDING = "pending"
    BUILDING = "building"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"

class ToolType(str, Enum):
    """Tool type enumeration"""
    WEB = "web"
    API = "api"
    CLI = "cli"
    DAEMON = "daemon"
    UTILITY = "utility"

class Tool(BaseModel):
    """Tool database model"""
    __tablename__ = "tools"
    
    # Tool identification
    name = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Git information
    git_url = Column(String(500), nullable=False)
    git_branch = Column(String(100), default="main")
    git_commit = Column(String(40))
    
    # Tool configuration
    tool_type = Column(SQLEnum(ToolType), nullable=False, default=ToolType.WEB)
    status = Column(SQLEnum(ToolStatus), nullable=False, default=ToolStatus.PENDING)
    
    # Docker configuration
    container_id = Column(String(64))
    container_name = Column(String(255))
    port = Column(Integer)
    health_check_endpoint = Column(String(255), default="/health")
    
    # Build configuration
    dockerfile_path = Column(String(500), default="Dockerfile")
    build_context = Column(String(500), default=".")
    build_args = Column(Text)  # JSON string
    
    # Runtime configuration
    environment_variables = Column(Text)  # JSON string
    volumes = Column(Text)  # JSON string
    command = Column(Text)
    
    # Metadata
    version = Column(String(50))
    author = Column(String(255))
    license = Column(String(100))
    tags = Column(Text)  # JSON array as string
    
    # Status tracking
    enabled = Column(Boolean, default=True)
    auto_start = Column(Boolean, default=False)
    last_health_check = Column(DateTime)
    build_log = Column(Text)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<Tool(name='{self.name}', status='{self.status}')>"
