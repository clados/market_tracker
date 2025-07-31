# File: database.py
# Description: SQLAlchemy database setup with debugging output.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import json
from dotenv import load_dotenv

# Create a base class for your ORM models
Base = declarative_base()

def get_database_url():
    """
    Constructs the database connection URL from environment variables.
    Includes detailed debugging print statements to be viewed in CloudWatch logs.
    """
    print("[DB DEBUG] --- Starting database URL configuration ---")

    # Load environment variables from .env.local if it exists (for local development)
    # In a deployed Copilot environment, this file won't exist.
    if os.path.exists('.env.local'):
        print("[DB DEBUG] Found .env.local file, loading it.")
        load_dotenv('.env.local', override=False)

    # First, check if a full DATABASE_URL is provided directly.
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        print(f"[DB DEBUG] Found DATABASE_URL directly: {DATABASE_URL}")
        print("[DB DEBUG] --- Using DATABASE_URL directly, skipping other variables. ---")
        return DATABASE_URL

    # If not, construct the URL from individual parts.
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "marketdb")

    # --- THIS IS THE MOST IMPORTANT DEBUGGING STEP ---
    # Print the values as read from the environment.
    print(f"[DB DEBUG] Value of DB_HOST from environment: {DB_HOST}")
    print(f"[DB DEBUG] Value of DB_PORT from environment: {DB_PORT}")
    print(f"[DB DEBUG] Value of DB_NAME from environment: {DB_NAME}")
    
    # Check if DB_HOST was actually found. If not, the connection will fail.
    if not DB_HOST:
        print("[DB DEBUG] FATAL: DB_HOST environment variable is missing or empty.")
        raise ValueError("DB_HOST environment variable is required")
    
    # Get credentials. The preferred method is parsing the DB_SECRET JSON object.
    DB_SECRET = os.getenv("DB_SECRET")
    DB_USER = None
    DB_PASSWORD = None

    if DB_SECRET:
        print("[DB DEBUG] Found DB_SECRET environment variable. Attempting to parse JSON.")
        # Note: Logging the raw secret is okay for temporary debugging but should be
        # removed from production code.
        print(f"[DB DEBUG] Raw content of DB_SECRET: {DB_SECRET}")
        try:
            secret_obj = json.loads(DB_SECRET)
            DB_PASSWORD = secret_obj.get("password")
            DB_USER = secret_obj.get("username", "dbadmin")
            print(f"[DB DEBUG] Parsed username from DB_SECRET: {DB_USER}")
            # Avoid printing the actual password, just confirm it was found.
            print(f"[DB DEBUG] Parsed password from DB_SECRET: {'Found' if DB_PASSWORD else 'Not Found'}")
        except Exception as e:
            print(f"[DB DEBUG] FATAL: Failed to parse DB_SECRET JSON: {e}")
            raise ValueError(f"Failed to parse DB_SECRET: {e}")
    else:
        # Fallback to individual user/password variables if DB_SECRET is not present.
        print("[DB DEBUG] DB_SECRET not found. Falling back to DB_USER/DB_PASSWORD variables.")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        DB_USER = os.getenv("DB_USER", "dbadmin")
        print(f"[DB DEBUG] Value of DB_USER from environment: {DB_USER}")
        print(f"[DB DEBUG] Value of DB_PASSWORD from environment: {'Found' if DB_PASSWORD else 'Not Found'}")
    
    # Final check to ensure a password was found one way or another.
    if not DB_PASSWORD:
        print("[DB DEBUG] FATAL: DB_PASSWORD could not be found in DB_SECRET or as an environment variable.")
        raise ValueError("DB_PASSWORD environment variable is required")
    
    # Construct the final URL.
    final_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    # Print the final constructed URL, hiding the password for security.
    print(f"[DB DEBUG] --- Final constructed database URL: postgresql://{DB_USER}:<password_hidden>@{DB_HOST}:{DB_PORT}/{DB_NAME} ---")
    
    return final_url

def get_engine():
    """Gets the SQLAlchemy database engine."""
    database_url = get_database_url()
    print("[DB DEBUG] Creating SQLAlchemy engine.")
    engine = create_engine(database_url)
    print("[DB DEBUG] SQLAlchemy engine created successfully.")
    return engine

def get_session_factory():
    """Gets the SQLAlchemy session factory."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

def get_db():
    """
    Dependency-style function to get a database session for a single request/operation.
    Ensures the session is always closed.
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()