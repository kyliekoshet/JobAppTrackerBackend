from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import FollowUp, JobApplication
from ..schemas import FollowUpCreate, FollowUpUpdate, FollowUp as FollowUpSchema

router = APIRouter()


@router.post("/job-applications/{application_id}/follow-ups", response_model=FollowUpSchema)
def create_follow_up(
    application_id: int,
    follow_up: FollowUpCreate,
    db: Session = Depends(get_db)
):
    """Create a new follow-up for a job application"""
    # Check if job application exists
    job_app = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not job_app:
        raise HTTPException(status_code=404, detail="Job application not found")
    
    # Create new follow-up
    db_follow_up = FollowUp(
        job_application_id=application_id,
        **follow_up.dict()
    )
    
    db.add(db_follow_up)
    db.commit()
    db.refresh(db_follow_up)
    
    return db_follow_up


@router.get("/job-applications/{application_id}/follow-ups", response_model=List[FollowUpSchema])
def get_follow_ups(
    application_id: int,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    follow_up_type: Optional[str] = Query(None, description="Filter by follow-up type")
):
    """Get all follow-ups for a job application"""
    # Check if job application exists
    job_app = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not job_app:
        raise HTTPException(status_code=404, detail="Job application not found")
    
    # Build query
    query = db.query(FollowUp).filter(FollowUp.job_application_id == application_id)
    
    if status:
        query = query.filter(FollowUp.status == status)
    
    if follow_up_type:
        query = query.filter(FollowUp.follow_up_type == follow_up_type)
    
    # Order by date (most recent first)
    follow_ups = query.order_by(FollowUp.date.desc()).all()
    
    return follow_ups


@router.get("/follow-ups/{follow_up_id}", response_model=FollowUpSchema)
def get_follow_up(follow_up_id: int, db: Session = Depends(get_db)):
    """Get a specific follow-up by ID"""
    follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    return follow_up


@router.put("/follow-ups/{follow_up_id}", response_model=FollowUpSchema)
def update_follow_up(
    follow_up_id: int,
    follow_up_update: FollowUpUpdate,
    db: Session = Depends(get_db)
):
    """Update a follow-up"""
    db_follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not db_follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    # Update fields
    update_data = follow_up_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_follow_up, field, value)
    
    db_follow_up.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_follow_up)
    
    return db_follow_up


@router.delete("/follow-ups/{follow_up_id}")
def delete_follow_up(follow_up_id: int, db: Session = Depends(get_db)):
    """Delete a follow-up"""
    db_follow_up = db.query(FollowUp).filter(FollowUp.id == follow_up_id).first()
    if not db_follow_up:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    
    db.delete(db_follow_up)
    db.commit()
    
    return {"message": "Follow-up deleted successfully"}


@router.get("/follow-ups", response_model=List[FollowUpSchema])
def get_all_follow_ups(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by status"),
    follow_up_type: Optional[str] = Query(None, description="Filter by follow-up type"),
    application_id: Optional[int] = Query(None, description="Filter by job application ID")
):
    """Get all follow-ups with optional filtering"""
    query = db.query(FollowUp)
    
    if status:
        query = query.filter(FollowUp.status == status)
    
    if follow_up_type:
        query = query.filter(FollowUp.follow_up_type == follow_up_type)
    
    if application_id:
        query = query.filter(FollowUp.job_application_id == application_id)
    
    # Order by date (most recent first)
    follow_ups = query.order_by(FollowUp.date.desc()).all()
    
    return follow_ups 