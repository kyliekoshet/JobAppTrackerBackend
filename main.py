from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import job_applications, follow_ups
from app.models import Base
from app.database import engine

# Create database tables
Base.metadata.create_all(bind=engine)

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