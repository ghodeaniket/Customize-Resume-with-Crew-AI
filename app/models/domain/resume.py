"""Domain model for a resume."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Education(BaseModel):
    """Education entry in a resume."""
    
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    gpa: Optional[float] = None
    achievements: List[str] = []


class Experience(BaseModel):
    """Work experience entry in a resume."""
    
    company: str
    title: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    current: bool = False
    location: Optional[str] = None
    responsibilities: List[str] = []
    achievements: List[str] = []


class Resume(BaseModel):
    """Domain model for a resume."""
    
    id: UUID = Field(default_factory=uuid4)
    filename: str
    content: str
    personal_info: Dict[str, Any] = {}
    skills: List[str] = []
    experience: List[Experience] = []
    education: List[Education] = []
    certifications: List[str] = []
    languages: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def update_content(self, new_content: str):
        """Update the resume content and updated_at timestamp."""
        self.content = new_content
        self.updated_at = datetime.now()
