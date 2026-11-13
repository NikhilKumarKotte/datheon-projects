from typing import List, Optional
from pydantic import Field
from src.extractor.schemas.base import StrictModel


class EducationItem(StrictModel):
    """Academic degree or qualification."""
    qualification: Optional[str] = Field(default=None, description="Degree or program title")
    institution: Optional[str] = Field(default=None, description="University, college or school")
    graduation_year: Optional[str] = Field(default=None, description="Year of graduation or expected year")
    score: Optional[str] = Field(default=None, description="GPA, percentage, or academic honors")


class ExperienceItem(StrictModel):
    """Professional employment history item."""
    job_title: Optional[str] = Field(default=None, description="Designation or job title")
    company: Optional[str] = Field(default=None, description="Organization or company name")
    start_date: Optional[str] = Field(default=None, description="Employment start date")
    end_date: Optional[str] = Field(default=None, description="Employment end date or 'Present'")
    description: Optional[str] = Field(default=None, description="Summary of responsibilities and achievements")


class ProjectItem(StrictModel):
    """Project completed by candidate."""
    name: Optional[str] = Field(default=None, description="Name or title of the project")
    description: Optional[str] = Field(default=None, description="Brief description of the project")
    technologies: List[str] = Field(default_factory=list, description="List of technologies, frameworks, or tools used")


class ResumeData(StrictModel):
    """Structured representation of a professional resume or CV."""
    full_name: Optional[str] = Field(default=None, description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Candidate's contact email address")
    phone: Optional[str] = Field(default=None, description="Candidate's phone number")
    location: Optional[str] = Field(default=None, description="City, state, or country of residence")
    professional_summary: Optional[str] = Field(default=None, description="Executive summary or objective")
    skills: List[str] = Field(default_factory=list, description="Technical, domain, or soft skills")
    education: List[EducationItem] = Field(default_factory=list, description="Academic history")
    experience: List[ExperienceItem] = Field(default_factory=list, description="Work experience")
    projects: List[ProjectItem] = Field(default_factory=list, description="Key projects completed")
