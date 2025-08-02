from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL - try PostgreSQL first, fallback to SQLite
POSTGRES_URL = "postgresql://postgres:JobAppTrack123!@db.gdpirggdsuphgtznfvvk.supabase.co:5432/postgres"
SQLITE_URL = "sqlite:///./job_applications.db"

def create_database_engine():
    """Create database engine with fallback logic"""
    
    # First, try PostgreSQL (Supabase)
    try:
        logger.info("Attempting to connect to PostgreSQL (Supabase)...")
        engine = create_engine(POSTGRES_URL)
        # Test the connection
        connection = engine.connect()
        connection.close()
        logger.info("✅ Connected to PostgreSQL (Supabase)")
        return engine
    except Exception as e:
        logger.warning(f"❌ PostgreSQL connection failed: {e}")
        logger.info("Falling back to SQLite for local development...")
        
        # Fallback to SQLite
        try:
            engine = create_engine(
                SQLITE_URL, 
                connect_args={"check_same_thread": False}  # Needed for SQLite
            )
            # Test the connection
            connection = engine.connect()
            connection.close()
            logger.info("✅ Connected to SQLite (local database)")
            return engine
        except Exception as sqlite_error:
            logger.error(f"❌ SQLite connection also failed: {sqlite_error}")
            raise sqlite_error

# Create engine with fallback
engine = create_database_engine()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 