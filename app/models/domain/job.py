"""Domain model for a job description."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """Requirement in a job description."""
    
    text: str
    is_required: bool = True
    category: Optional[str] = None  # Skill, Experience, Education, etc.
    importance: float = 1.0  # 0.0 to 1.0


class JobDescription(BaseModel):
    """Domain model for a job description."""
    
    id: UUID = Field(default_factory=uuid4)
    title: str
    company: Optional[str] = None
    description: str
    requirements: List[Requirement] = []
    skills: List[str] = []
    experience_level: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary_range: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    keywords: List[str] = []
    
    def extract_requirements(self) -> List[Requirement]:
        """Extract requirements from the job description."""
        # This will be implemented with NLP in Phase 2
        return self.requirements
