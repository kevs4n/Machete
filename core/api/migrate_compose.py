#!/usr/bin/env python3
"""
Migration script to add Docker Compose support fields to the tools table.
"""

import asyncio
import asyncpg
import os
from app.core.config import settings

async def run_migration():
    """Add has_compose and compose_file fields to tools table."""
    
    # Connect to the database
    conn = await asyncpg.connect(
        host=settings.DATABASE_HOST,
        port=settings.DATABASE_PORT,
        user=settings.DATABASE_USER,
        password=settings.DATABASE_PASSWORD,
        database=settings.DATABASE_NAME
    )
    
    try:
        # Check if columns already exist
        existing_columns = await conn.fetch("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tools' 
            AND column_name IN ('has_compose', 'compose_file')
        """)
        
        existing_column_names = [col['column_name'] for col in existing_columns]
        
        # Add has_compose column if it doesn't exist
        if 'has_compose' not in existing_column_names:
            await conn.execute("""
                ALTER TABLE tools 
                ADD COLUMN has_compose BOOLEAN DEFAULT FALSE
            """)
            print("✅ Added has_compose column to tools table")
        else:
            print("ℹ️  has_compose column already exists")
        
        # Add compose_file column if it doesn't exist
        if 'compose_file' not in existing_column_names:
            await conn.execute("""
                ALTER TABLE tools 
                ADD COLUMN compose_file TEXT
            """)
            print("✅ Added compose_file column to tools table")
        else:
            print("ℹ️  compose_file column already exists")
        
        # Verify the migration
        result = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'tools' 
            ORDER BY ordinal_position
        """)
        
        print("\n📋 Current tools table schema:")
        for row in result:
            default = row['column_default'] or 'NULL'
            nullable = 'YES' if row['is_nullable'] == 'YES' else 'NO'
            print(f"  - {row['column_name']}: {row['data_type']} (nullable: {nullable}, default: {default})")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    print("🚀 Running Docker Compose migration...")
    asyncio.run(run_migration())
    print("✅ Migration completed successfully!")
