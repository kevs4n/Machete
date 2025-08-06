"""
User model for authentication and authorization
"""

from sqlalchemy import Column, String, Boolean
from .base import BaseModel

class User(BaseModel):
    """User database model"""
    __tablename__ = "users"
    
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    hashed_password = Column(String(255), nullable=False)
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"
