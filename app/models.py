from sqlalchemy import Column, Integer, String, DateTime, Text, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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
    # Referral information
    referred_by = Column(String(255), nullable=True)  # Name of the person who referred you
    referral_relationship = Column(String(100), nullable=True)  # e.g., "Former colleague", "Friend", "LinkedIn connection"
    referral_date = Column(DateTime, nullable=True)  # When the referral was made
    referral_notes = Column(Text, nullable=True)  # Additional notes about the referral
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship to follow-ups
    follow_ups = relationship("FollowUp", back_populates="job_application", cascade="all, delete-orphan")


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=False)
    follow_up_type = Column(String(50), nullable=False)  # e.g., "Phone Call", "Email", "Interview", "Follow-up"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False, default="Pending")  # e.g., "Pending", "Completed", "Cancelled"
    outcome = Column(String(255), nullable=True)  # e.g., "Scheduled next round", "Rejected", "No response"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship to job application
    job_application = relationship("JobApplication", back_populates="follow_ups") 