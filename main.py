from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import job_applications, follow_ups
from app.models import Base
from app.database import engine
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables with error handling
try:
    logger.info("Attempting to connect to database and create tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully!")
except Exception as e:
    logger.error(f"❌ Failed to create database tables: {e}")
    logger.error("Please check your database connection and try again.")
    logger.error("You can test the connection by running: python test_connection.py")
    # Don't exit - let the app start anyway so we can debug

app = FastAPI(
    title="Job Application Tracker API",
    description="A comprehensive API for tracking job applications with web scraping capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(job_applications.router, prefix="/api/v1", tags=["job-applications"])
app.include_router(follow_ups.router, prefix="/api/v1", tags=["follow-ups"])

@app.get("/")
async def root():
    return {"message": "Job Application Tracker API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/db-status")
async def database_status():
    """Check database connection status"""
    try:
        # Try a simple query
        from app.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"database": "connected", "status": "healthy"}
    except Exception as e:
        return {"database": "disconnected", "status": "error", "error": str(e)} 