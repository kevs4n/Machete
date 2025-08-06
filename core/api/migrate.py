"""
Database migration script for MACHETE Platform
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import async_engine
from app.models.base import Base

async def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    
    try:
        async with async_engine.begin() as conn:
            # Import all models to ensure they are registered
            from app.models import Tool, User
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        await async_engine.dispose()

async def drop_tables():
    """Drop all database tables"""
    print("Dropping database tables...")
    
    try:
        async with async_engine.begin() as conn:
            # Import all models
            from app.models import Tool, User
            
            # Drop all tables
            await conn.run_sync(Base.metadata.drop_all)
            print("✅ Database tables dropped successfully")
            
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        raise
    finally:
        await async_engine.dispose()

async def reset_database():
    """Reset the database (drop and recreate)"""
    print("Resetting database...")
    await drop_tables()
    await create_tables()
    print("✅ Database reset completed")

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MACHETE Database Migration")
    parser.add_argument("action", choices=["create", "drop", "reset"], 
                       help="Migration action to perform")
    
    args = parser.parse_args()
    
    print(f"🔪 MACHETE Database Migration")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Action: {args.action}")
    print("-" * 50)
    
    if args.action == "create":
        asyncio.run(create_tables())
    elif args.action == "drop":
        asyncio.run(drop_tables())
    elif args.action == "reset":
        asyncio.run(reset_database())

if __name__ == "__main__":
    main()
