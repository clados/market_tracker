from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Create base class for models
Base = declarative_base()

def get_database_url():
    """Get database URL from environment"""
    # Load environment variables from .env.local if it exists (local development)
    # In production, environment variables are set by Copilot
    load_dotenv('.env.local', override=False) if os.path.exists('.env.local') else None
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is required")
    return DATABASE_URL

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