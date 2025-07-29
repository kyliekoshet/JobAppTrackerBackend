from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import math

from ..database import get_db
from ..models import JobApplication
from ..schemas import (
    JobApplicationCreate, JobApplicationUpdate, JobApplication, 
    JobApplicationList, ScrapingRequest, ScrapingResponse, SummaryStats
)
from ..ai_scraper import scrape_job_details_with_ai

router = APIRouter()


@router.post("/job-applications", response_model=JobApplication)
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


@router.get("/job-applications/{application_id}", response_model=JobApplication)
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


@router.put("/job-applications/{application_id}", response_model=JobApplication)
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


@router.get("/job-applications/stats/summary", response_model=SummaryStats)
async def get_application_stats(db: Session = Depends(get_db)):
    """Get summary statistics for job applications."""
    try:
        # Total applications
        total_applications = db.query(JobApplication).count()
        
        # Applications this month
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        applications_this_month = db.query(JobApplication).filter(
            JobApplication.created_at >= start_of_month
        ).count()
        
        # Applications this week
        start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        applications_this_week = db.query(JobApplication).filter(
            JobApplication.created_at >= start_of_week
        ).count()
        
        # Status breakdown
        status_breakdown = db.query(
            JobApplication.application_status,
            func.count(JobApplication.id)
        ).group_by(JobApplication.application_status).all()
        
        status_dict = {status: count for status, count in status_breakdown}
        
        # Top companies
        top_companies = db.query(
            JobApplication.company,
            func.count(JobApplication.id).label('count')
        ).group_by(JobApplication.company).order_by(
            func.count(JobApplication.id).desc()
        ).limit(5).all()
        
        top_companies_list = [
            {"company": company, "count": count} 
            for company, count in top_companies
        ]
        
        # Average applications per day (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_applications = db.query(JobApplication).filter(
            JobApplication.created_at >= thirty_days_ago
        ).count()
        
        average_per_day = recent_applications / 30 if recent_applications > 0 else 0
        
        return SummaryStats(
            total_applications=total_applications,
            applications_this_month=applications_this_month,
            applications_this_week=applications_this_week,
            status_breakdown=status_dict,
            top_companies=top_companies_list,
            average_applications_per_day=round(average_per_day, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}") 