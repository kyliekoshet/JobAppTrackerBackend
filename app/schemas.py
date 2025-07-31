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
    # Referral information
    referred_by: Optional[str] = None
    referral_relationship: Optional[str] = None
    referral_date: Optional[datetime] = None
    referral_notes: Optional[str] = None

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
    # Referral information
    referred_by: Optional[str] = None
    referral_relationship: Optional[str] = None
    referral_date: Optional[datetime] = None
    referral_notes: Optional[str] = None


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


# Base schema for follow-ups
class FollowUpBase(BaseModel):
    follow_up_type: str
    title: str
    description: Optional[str] = None
    date: datetime
    status: str = "Pending"
    outcome: Optional[str] = None
    notes: Optional[str] = None

    @validator('follow_up_type')
    def validate_follow_up_type(cls, v):
        valid_types = [
            "Phone Call", "Email", "Interview", "Follow-up", "Technical Interview", 
            "Behavioral Interview", "System Design", "Coding Challenge", "Onsite", 
            "Final Round", "Reference Check", "Background Check", "Offer Discussion"
        ]
        if v not in valid_types:
            raise ValueError(f'Follow-up type must be one of: {", ".join(valid_types)}')
        return v

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["Pending", "Completed", "Cancelled", "Rescheduled"]
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


# Schema for creating a new follow-up
class FollowUpCreate(FollowUpBase):
    pass


# Schema for updating a follow-up
class FollowUpUpdate(BaseModel):
    follow_up_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    status: Optional[str] = None
    outcome: Optional[str] = None
    notes: Optional[str] = None


# Schema for follow-up response
class FollowUp(FollowUpBase):
    id: int
    job_application_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Schema for job application with follow-ups
class JobApplicationWithFollowUps(JobApplication):
    follow_ups: List[FollowUp] = []

    class Config:
        from_attributes = True 