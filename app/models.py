from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from .database import Base

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    job_description = Column(Text)
    location = Column(String(255))
    salary = Column(Float)
    job_url = Column(String(500))
    date_applied = Column(DateTime, nullable=False)
    date_job_posted = Column(DateTime)
    application_status = Column(String(50), default="Applied")
    interview_stage = Column(String(50), default="None")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 