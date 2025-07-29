from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class JobApplicationBase(BaseModel):
    job_title: str
    company: str
    job_description: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[float] = None
    job_url: Optional[str] = None
    date_applied: datetime
    date_job_posted: Optional[datetime] = None
    application_status: str = "Applied"
    interview_stage: str = "None"
    notes: Optional[str] = None

    @validator('application_status')
    def validate_application_status(cls, v):
        valid_statuses = [
            "Applied", "Interview Scheduled", "Interview Completed", 
            "Offer Received", "Rejected", "Withdrawn"
        ]
        if v not in valid_statuses:
            raise ValueError(f'Application status must be one of: {", ".join(valid_statuses)}')
        return v

    @validator('interview_stage')
    def validate_interview_stage(cls, v):
        valid_stages = [
            "None", "Phone Screen", "Technical Interview", 
            "HR Interview", "Final Round", "Onsite"
        ]
        if v not in valid_stages:
            raise ValueError(f'Interview stage must be one of: {", ".join(valid_stages)}')
        return v

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationUpdate(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[float] = None
    job_url: Optional[str] = None
    date_applied: Optional[datetime] = None
    date_job_posted: Optional[datetime] = None
    application_status: Optional[str] = None
    interview_stage: Optional[str] = None
    notes: Optional[str] = None

class JobApplication(JobApplicationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JobApplicationList(BaseModel):
    applications: list[JobApplication]
    total: int
    page: int
    per_page: int 