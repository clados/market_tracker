from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json
from dotenv import load_dotenv

# Create base class for models
Base = declarative_base()

def get_database_url():
    """Get database URL from environment"""
    # Load environment variables from .env.local if it exists (local development)
    # In production, environment variables are set by Copilot
    load_dotenv('.env.local', override=False) if os.path.exists('.env.local') else None
    
    # Try to get the full DATABASE_URL first (for backward compatibility)
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        return DATABASE_URL
    
    # If not available, construct from individual components
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME")
    DB_SECRET = os.getenv("DB_SECRET")
    
    if not all([DB_HOST, DB_NAME, DB_SECRET]):
        raise ValueError("Either DATABASE_URL or all of DB_HOST, DB_NAME, and DB_SECRET environment variables are required")
    
        # Get password from environment variable (Copilot automatically resolves secrets)
    try:
        # DB_SECRET contains the actual secret value as JSON string
        secret_data = json.loads(DB_SECRET)
        password = secret_data['password']
    except Exception as e:
        raise ValueError(f"Failed to parse database password from environment: {e}")

    database_url = f"postgresql://postgres:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return database_url

def get_engine():
    """Get database engine"""
    return create_engine(get_database_url())

def get_session_factory():
    """Get session factory"""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

def get_db():
    """Dependency to get database session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 