from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    salary = Column(String(255), nullable=True)  # Changed from Float to String
    job_url = Column(String(500), nullable=True)
    date_applied = Column(DateTime, nullable=False)
    date_job_posted = Column(DateTime, nullable=True)
    application_status = Column(String(50), nullable=False, default="Applied")
    interview_stage = Column(String(50), nullable=False, default="None")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 