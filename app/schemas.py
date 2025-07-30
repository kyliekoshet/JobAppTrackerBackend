from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime


# Base schema for job applications
class JobApplicationBase(BaseModel):
    job_title: str
    company: str
    job_description: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    job_url: Optional[str] = None
    date_applied: datetime
    date_job_posted: Optional[datetime] = None
    application_status: str = "Applied"
    interview_stage: str = "None"
    notes: Optional[str] = None

    @validator('application_status')
    def validate_application_status(cls, v):
        valid_statuses = [
            "Applied", "Interviewing", "Offer", "Rejected", "Withdrawn", "Pending"
        ]
        if v not in valid_statuses:
            raise ValueError(f'Application status must be one of: {", ".join(valid_statuses)}')
        return v

    @validator('interview_stage')
    def validate_interview_stage(cls, v):
        valid_stages = [
            "None", "Phone Screen", "Technical Interview", "Behavioral Interview", 
            "System Design", "Coding Challenge", "Onsite", "Final Round"
        ]
        if v not in valid_stages:
            raise ValueError(f'Interview stage must be one of: {", ".join(valid_stages)}')
        return v


# Schema for creating a new job application
class JobApplicationCreate(JobApplicationBase):
    pass


# Schema for updating a job application
class JobApplicationUpdate(BaseModel):
    job_title: Optional[str] = None
    company: Optional[str] = None
    job_description: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    job_url: Optional[str] = None
    date_applied: Optional[datetime] = None
    date_job_posted: Optional[datetime] = None
    application_status: Optional[str] = None
    interview_stage: Optional[str] = None
    notes: Optional[str] = None


# Schema for job application response
class JobApplication(JobApplicationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for list of job applications
class JobApplicationList(BaseModel):
    applications: List[JobApplication]
    total: int
    page: int
    size: int
    pages: int


# Schema for scraped job data
class ScrapedJobData(BaseModel):
    success: bool
    url: str
    job_board: Optional[str] = None
    scraped_at: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    job_description: Optional[str] = None
    salary: Optional[str] = None
    error: Optional[str] = None


# Schema for scraping request
class ScrapingRequest(BaseModel):
    url: str


# Schema for scraping response
class ScrapingResponse(BaseModel):
    success: bool
    data: Optional[ScrapedJobData] = None
    error: Optional[str] = None


# Schema for summary statistics
class SummaryStats(BaseModel):
    total_applications: int
    status_breakdown: dict
    recent_applications: int
    success_rate: float 