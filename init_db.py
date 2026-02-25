"""
Database Initialization Script

Run this script to initialize the database schema.
For production, use Alembic migrations instead: alembic upgrade head
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base, check_db_connection, init_db
from models import User, Document, Analysis, APILog


def main():
    """Initialize database tables"""
    print("=" * 50)
    print("Financial Document Analyzer - Database Setup")
    print("=" * 50)
    print()
    
    # Check database connection
    print("Checking database connection...")
    if not check_db_connection():
        print("❌ Failed to connect to database!")
        print("Please check your DATABASE_URL in .env file")
        sys.exit(1)
    
    print("✅ Database connection successful!")
    print()
    
    # Create tables
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        print()
        print("Tables created:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
        print()
        print("=" * 50)
        print("Database initialization complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
