"""
MACHETE Platform Configuration
Settings management with environment variable support
"""

from pathlib import Path
import os

class Settings:
    """Application settings with environment variable support"""
    
    def __init__(self):
        # Application
        self.APP_NAME = os.getenv("APP_NAME", "MACHETE Platform")
        self.VERSION = os.getenv("VERSION", "2.0.0")
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        
        # Server
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8000"))
        
        # CORS
        cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080")
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]
        
        # Database
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql+asyncpg://machete:machete@database:5432/machete"
        )
        
        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
        
        # Docker
        self.DOCKER_SOCKET = os.getenv("DOCKER_SOCKET", "/var/run/docker.sock")
        self.DOCKER_NETWORK = os.getenv("DOCKER_NETWORK", "machete_machete-network")
        
        # File System
        self.TOOLS_DIR = os.getenv("TOOLS_DIR", "/app/tools")
        self.DATA_DIR = os.getenv("DATA_DIR", "/app/data")
        self.LOGS_DIR = os.getenv("LOGS_DIR", "/app/logs")
        
        # Security
        self.SECRET_KEY = self._get_secret_key()
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Rate Limiting
        self.RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))
        
        # Tool Configuration
        self.TOOL_DEFAULT_PORT = int(os.getenv("TOOL_DEFAULT_PORT", "8080"))
        self.TOOL_DEFAULT_HEALTH_CHECK = os.getenv("TOOL_DEFAULT_HEALTH_CHECK", "/health")
        self.TOOL_BUILD_TIMEOUT = int(os.getenv("TOOL_BUILD_TIMEOUT", "300"))
        self.TOOL_START_TIMEOUT = int(os.getenv("TOOL_START_TIMEOUT", "60"))
        
        # Git Configuration
        self.GIT_CLONE_TIMEOUT = int(os.getenv("GIT_CLONE_TIMEOUT", "300"))
        self.GIT_CLONE_DEPTH = int(os.getenv("GIT_CLONE_DEPTH", "1"))
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
    
    def _get_secret_key(self) -> str:
        """Get secret key from environment or generate default"""
        secret = os.getenv("SECRET_KEY", "")
        if not secret:
            return "dev-secret-key-change-in-production-minimum-32-chars"
        if len(secret) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return secret
    
    @property
    def database_url_sync(self) -> str:
        """Synchronous database URL for migrations"""
        return self.DATABASE_URL.replace("+asyncpg", "")
    
    def create_directories(self) -> None:
        """Create necessary directories"""
        for directory in [self.TOOLS_DIR, self.DATA_DIR, self.LOGS_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()

# Create settings instance
settings = Settings()

# Ensure directories exist
settings.create_directories()
