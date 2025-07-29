from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..models import JobApplication
from ..schemas import JobApplicationCreate, JobApplicationUpdate, JobApplication as JobApplicationSchema, JobApplicationList

router = APIRouter()

@router.post("/job-applications", response_model=JobApplicationSchema)
def create_job_application(
    job_application: JobApplicationCreate,
    db: Session = Depends(get_db)
):
    """Create a new job application"""
    try:
        db_job_application = JobApplication(**job_application.dict())
        db.add(db_job_application)
        db.commit()
        db.refresh(db_job_application)
        return db_job_application
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job application: {str(e)}")

@router.get("/job-applications", response_model=JobApplicationList)
def get_job_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|date_applied|company|job_title|application_status)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    company: Optional[str] = None,
    job_title: Optional[str] = None,
    application_status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all job applications with filtering and sorting"""
    try:
        query = db.query(JobApplication)
        
        # Apply filters
        if company:
            query = query.filter(JobApplication.company.ilike(f"%{company}%"))
        if job_title:
            query = query.filter(JobApplication.job_title.ilike(f"%{job_title}%"))
        if application_status:
            query = query.filter(JobApplication.application_status == application_status)
        
        # Apply sorting
        sort_column = getattr(JobApplication, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        applications = query.offset(skip).limit(limit).all()
        
        return JobApplicationList(
            applications=applications,
            total=total,
            page=skip // limit + 1,
            per_page=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch job applications: {str(e)}")

@router.get("/job-applications/{job_application_id}", response_model=JobApplicationSchema)
def get_job_application(job_application_id: int, db: Session = Depends(get_db)):
    """Get a specific job application by ID"""
    try:
        job_application = db.query(JobApplication).filter(JobApplication.id == job_application_id).first()
        if job_application is None:
            raise HTTPException(status_code=404, detail="Job application not found")
        return job_application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch job application: {str(e)}")

@router.put("/job-applications/{job_application_id}", response_model=JobApplicationSchema)
def update_job_application(
    job_application_id: int,
    job_application_update: JobApplicationUpdate,
    db: Session = Depends(get_db)
):
    """Update a job application"""
    try:
        db_job_application = db.query(JobApplication).filter(JobApplication.id == job_application_id).first()
        if db_job_application is None:
            raise HTTPException(status_code=404, detail="Job application not found")
        
        update_data = job_application_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_job_application, field, value)
        
        db_job_application.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_job_application)
        return db_job_application
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update job application: {str(e)}")

@router.delete("/job-applications/{job_application_id}")
def delete_job_application(job_application_id: int, db: Session = Depends(get_db)):
    """Delete a job application"""
    try:
        db_job_application = db.query(JobApplication).filter(JobApplication.id == job_application_id).first()
        if db_job_application is None:
            raise HTTPException(status_code=404, detail="Job application not found")
        
        db.delete(db_job_application)
        db.commit()
        return {"message": "Job application deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete job application: {str(e)}")

@router.get("/job-applications/stats/summary")
def get_application_stats(db: Session = Depends(get_db)):
    """Get summary statistics for job applications"""
    try:
        total_applications = db.query(JobApplication).count()
        
        # Status breakdown
        status_counts = db.query(JobApplication.application_status, func.count(JobApplication.id)).group_by(JobApplication.application_status).all()
        status_breakdown = {status: count for status, count in status_counts}
        
        # Recent applications (last 30 days)
        thirty_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_applications = db.query(JobApplication).filter(JobApplication.date_applied >= thirty_days_ago).count()
        
        return {
            "total_applications": total_applications,
            "status_breakdown": status_breakdown,
            "recent_applications": recent_applications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}") 