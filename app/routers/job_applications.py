from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import math

from ..database import get_db
from ..models import JobApplication
from ..schemas import (
    JobApplicationCreate, JobApplicationUpdate, JobApplication as JobApplicationSchema, 
    JobApplicationList, JobApplicationWithFollowUps, ScrapingRequest, ScrapingResponse, SummaryStats,
    JobDescriptionEnhanceRequest, JobDescriptionEnhanceResponse
)
from ..ai_scraper import scrape_job_details_with_ai, enhance_job_description_with_ai

router = APIRouter()


@router.post("/job-applications", response_model=JobApplicationSchema)
async def create_job_application(
    application: JobApplicationCreate,
    db: Session = Depends(get_db)
):
    """Create a new job application."""
    try:
        db_application = JobApplication(**application.dict())
        db.add(db_application)
        db.commit()
        db.refresh(db_application)
        return db_application
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create job application: {str(e)}")


@router.get("/job-applications", response_model=JobApplicationList)
async def get_job_applications(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    job_title: Optional[str] = Query(None, description="Filter by job title"),
    status: Optional[str] = Query(None, description="Filter by application status"),
    sort_by: Optional[str] = Query("created_at", description="Sort by field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """Get all job applications with filtering, sorting, and pagination."""
    try:
        query = db.query(JobApplication)
        
        # Apply filters
        if company:
            query = query.filter(JobApplication.company.ilike(f"%{company}%"))
        if job_title:
            query = query.filter(JobApplication.job_title.ilike(f"%{job_title}%"))
        if status:
            query = query.filter(JobApplication.application_status == status)
        
        # Apply sorting
        if hasattr(JobApplication, sort_by):
            sort_field = getattr(JobApplication, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(sort_field)
        else:
            query = query.order_by(desc(JobApplication.created_at))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        applications = query.offset(skip).limit(limit).all()
        
        # Calculate pagination info
        pages = math.ceil(total / limit) if total > 0 else 0
        
        return JobApplicationList(
            applications=applications,
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch job applications: {str(e)}")


@router.get("/job-applications/stats", response_model=SummaryStats)
async def get_application_stats(db: Session = Depends(get_db)):
    """Get summary statistics for job applications."""
    try:
        # Total applications
        total_applications = db.query(JobApplication).count()
        
        # Recent applications (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_applications = db.query(JobApplication).filter(
            JobApplication.created_at >= thirty_days_ago
        ).count()
        
        # Status breakdown
        status_breakdown = db.query(
            JobApplication.application_status,
            func.count(JobApplication.id)
        ).group_by(JobApplication.application_status).all()
        
        status_dict = {status: count for status, count in status_breakdown}
        
        # Calculate success rate (offers / total applications)
        offers = status_dict.get('Offer', 0)
        success_rate = offers / total_applications if total_applications > 0 else 0
        
        return SummaryStats(
            total_applications=total_applications,
            status_breakdown=status_dict,
            recent_applications=recent_applications,
            success_rate=success_rate
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")


@router.get("/job-applications/{application_id}", response_model=JobApplicationSchema)
async def get_job_application(application_id: int, db: Session = Depends(get_db)):
    """Get a specific job application by ID."""
    try:
        application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Job application not found")
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch job application: {str(e)}")


@router.get("/job-applications/{application_id}/with-follow-ups", response_model=JobApplicationWithFollowUps)
async def get_job_application_with_follow_ups(application_id: int, db: Session = Depends(get_db)):
    """Get a specific job application by ID with all its follow-ups."""
    try:
        application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
        if not application:
            raise HTTPException(status_code=404, detail="Job application not found")
        return application
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch job application: {str(e)}")


@router.put("/job-applications/{application_id}", response_model=JobApplicationSchema)
async def update_job_application(
    application_id: int,
    application_update: JobApplicationUpdate,
    db: Session = Depends(get_db)
):
    """Update a job application."""
    try:
        db_application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
        if not db_application:
            raise HTTPException(status_code=404, detail="Job application not found")
        
        # Update only provided fields
        update_data = application_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_application, field, value)
        
        db_application.updated_at = datetime.now()
        db.commit()
        db.refresh(db_application)
        return db_application
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to update job application: {str(e)}")


@router.delete("/job-applications/{application_id}")
async def delete_job_application(application_id: int, db: Session = Depends(get_db)):
    """Delete a job application."""
    try:
        db_application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
        if not db_application:
            raise HTTPException(status_code=404, detail="Job application not found")
        
        db.delete(db_application)
        db.commit()
        return {"message": "Job application deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to delete job application: {str(e)}")


@router.post("/scrape-job", response_model=ScrapingResponse)
async def scrape_job_details(scraping_request: ScrapingRequest):
    """Scrape job details from a URL using AI."""
    try:
        scraped_data = scrape_job_details_with_ai(scraping_request.url)
        
        if scraped_data.get('success'):
            return ScrapingResponse(
                success=True,
                data=scraped_data
            )
        else:
            return ScrapingResponse(
                success=False,
                error=scraped_data.get('error', 'Unknown scraping error')
            )
    except Exception as e:
        return ScrapingResponse(
            success=False,
            error=f"Scraping failed: {str(e)}"
        )


@router.post("/enhance-job-description", response_model=JobDescriptionEnhanceResponse)
async def enhance_job_description(enhance_request: JobDescriptionEnhanceRequest):
    """Enhance a job description using AI to extract key information."""
    try:
        enhanced_data = enhance_job_description_with_ai(
            enhance_request.job_description,
            enhance_request.job_title,
            enhance_request.company
        )
        
        if enhanced_data.get('success'):
            return JobDescriptionEnhanceResponse(
                success=True,
                enhanced_description=enhanced_data.get('enhanced_description'),
                key_requirements=enhanced_data.get('key_requirements'),
                key_responsibilities=enhanced_data.get('key_responsibilities'),
                benefits=enhanced_data.get('benefits')
            )
        else:
            return JobDescriptionEnhanceResponse(
                success=False,
                error=enhanced_data.get('error', 'Unknown enhancement error')
            )
    except Exception as e:
        return JobDescriptionEnhanceResponse(
            success=False,
            error=f"Enhancement failed: {str(e)}"
        )


 