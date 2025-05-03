"""Resume processing tools using the modern decorator pattern.

This module provides tools for processing resumes and matching them
with job descriptions using CrewAI's tool decorator pattern.
"""
from typing import Dict, Any, TYPE_CHECKING
import asyncio

from crewai.tools import tool

from app.crews.tools.base import BaseResumeTool
from app.crews.tools.base.base_tool import ToolRegistry
from app.core.logging import logger

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from app.services.resume_service import ResumeService


class ResumeTools(BaseResumeTool):
    """Collection of resume processing tools."""
    
    def __init__(self, resume_service: "ResumeService" = None):
        """Initialize resume tools.
        
        Args:
            resume_service: Resume service instance for processing
        """
        super().__init__(
            name="ResumeTools",
            description="Collection of tools for processing resumes",
            cache_enabled=True
        )
        self.resume_service = resume_service
    
    def create_resume_processor_tool(self):
        """Create a resume processor tool with the decorator pattern."""
        
        @tool("Resume Processor")
        @self.with_error_handling
        @self.with_performance_monitoring
        @self.with_cache
        def process_resume(task_id: str) -> Dict[str, Any]:
            """Process a resume by task ID.
            
            Args:
                task_id: The ID of the uploaded resume task
                
            Returns:
                Dict: Extracted resume content and metadata
            """
            logger.info(f"Processing resume with task ID: {task_id}")
            
            # Run the async function synchronously
            resume_data = asyncio.run(self.resume_service.get_resume_data(task_id))
            
            if not resume_data:
                logger.warning(f"Resume not found or processing not complete: {task_id}")
                return {"error": "Resume not found or processing not complete"}
            
            if resume_data.get("status") != "completed":
                status = resume_data.get('status', 'unknown')
                logger.warning(f"Resume processing not complete: {task_id}, status: {status}")
                return {"error": f"Resume processing not complete. Status: {status}"}
            
            logger.info(f"Successfully retrieved resume data for task ID: {task_id}")
            
            return {
                "text": resume_data.get("text", ""),
                "metadata": resume_data.get("metadata", {})
            }
        
        # Register the tool
        ToolRegistry.register("resume_processor", process_resume)
        return process_resume
    
    def create_job_matcher_tool(self):
        """Create a job matcher tool with the decorator pattern."""
        
        @tool("Job Matcher")
        @self.with_error_handling
        @self.with_performance_monitoring
        def match_job(resume_text: str, job_description: str) -> Dict[str, Any]:
            """Analyze how well a resume matches job requirements.
            
            Args:
                resume_text: The resume text content
                job_description: The job description text
                
            Returns:
                Dict: Analysis of the match between resume and job description
            """
            logger.info("Analyzing resume-job match")
            
            # This is a placeholder for more sophisticated matching logic
            # In a real implementation, this would use NLP or ML techniques
            
            # Extract keywords from both texts (simplified)
            resume_words = set(resume_text.lower().split())
            job_words = set(job_description.lower().split())
            
            # Calculate simple match metrics
            common_words = resume_words.intersection(job_words)
            match_score = len(common_words) / len(job_words) if job_words else 0.0
            
            # Identify skills (simplified - looks for common tech terms)
            tech_keywords = {
                "python", "java", "javascript", "react", "docker", "kubernetes",
                "aws", "gcp", "azure", "sql", "nosql", "api", "rest", "graphql"
            }
            
            resume_skills = resume_words.intersection(tech_keywords)
            job_skills = job_words.intersection(tech_keywords)
            
            missing_skills = list(job_skills - resume_skills)
            matching_skills = list(resume_skills.intersection(job_skills))
            
            # Generate recommendations
            recommendations = []
            if missing_skills:
                recommendations.append(
                    f"Consider adding these skills if you have experience: {', '.join(missing_skills)}"
                )
            if match_score < 0.3:
                recommendations.append(
                    "The resume appears to have low keyword match. Consider reviewing the job "
                    "description and incorporating more relevant terms."
                )
            
            return {
                "match_score": round(match_score, 2),
                "match_analysis": (
                    f"Resume matches approximately {int(match_score * 100)}% of the job keywords."
                ),
                "missing_skills": missing_skills,
                "matching_skills": matching_skills,
                "recommendations": recommendations
            }
        
        # Register the tool
        ToolRegistry.register("job_matcher", match_job)
        return match_job
    
    def create_keyword_extractor_tool(self):
        """Create a keyword extractor tool."""
        
        @tool("Keyword Extractor")
        @self.with_error_handling
        @self.with_performance_monitoring
        def extract_keywords(text: str, max_keywords: int = 20) -> Dict[str, Any]:
            """Extract important keywords from text.
            
            Args:
                text: Text to extract keywords from
                max_keywords: Maximum number of keywords to return
                
            Returns:
                Dict: Extracted keywords and their importance
            """
            logger.info("Extracting keywords from text")
            
            # Simple keyword extraction (placeholder for more sophisticated NLP)
            # In a real implementation, this would use TF-IDF, RAKE, or other algorithms
            
            # Remove common stop words
            stop_words = {
                "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
                "of", "with", "by", "from", "up", "about", "into", "over", "after"
            }
            
            # Tokenize and filter
            words = text.lower().split()
            filtered_words = [
                word.strip(".,!?()[]{}\"'") 
                for word in words 
                if word.lower() not in stop_words and len(word) > 2
            ]
            
            # Count word frequency
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and get top keywords
            sorted_keywords = sorted(
                word_freq.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:max_keywords]
            
            # Format results
            keywords = [
                {"keyword": word, "frequency": count}
                for word, count in sorted_keywords
            ]
            
            return {
                "keywords": keywords,
                "total_words": len(words),
                "unique_words": len(word_freq)
            }
        
        # Register the tool
        ToolRegistry.register("keyword_extractor", extract_keywords)
        return extract_keywords
    
    def create_ats_optimizer_tool(self):
        """Create an ATS optimizer tool."""
        
        @tool("ATS Optimizer")
        @self.with_error_handling
        @self.with_performance_monitoring
        def optimize_for_ats(resume_text: str, job_keywords: list) -> Dict[str, Any]:
            """Optimize resume content for ATS systems.
            
            Args:
                resume_text: Original resume text
                job_keywords: List of keywords from job description
                
            Returns:
                Dict: ATS optimization suggestions
            """
            logger.info("Optimizing resume for ATS")
            
            # Check keyword presence
            resume_lower = resume_text.lower()
            keyword_matches = {}
            missing_keywords = []
            
            for keyword in job_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in resume_lower:
                    # Count occurrences
                    count = resume_lower.count(keyword_lower)
                    keyword_matches[keyword] = count
                else:
                    missing_keywords.append(keyword)
            
            # Generate optimization suggestions
            suggestions = []
            
            if missing_keywords:
                suggestions.append(
                    f"Add these missing keywords where relevant: {', '.join(missing_keywords[:5])}"
                )
            
            # Check for ATS-friendly formatting
            if resume_text.count('\n\n') < 3:
                suggestions.append(
                    "Use clear section breaks with blank lines between sections"
                )
            
            if not any(header in resume_lower for header in ["experience", "education", "skills"]):
                suggestions.append(
                    "Include standard section headers like 'Experience', 'Education', and 'Skills'"
                )
            
            # Calculate ATS score (simplified)
            total_keywords = len(job_keywords)
            matched_keywords = len(keyword_matches)
            ats_score = (matched_keywords / total_keywords) if total_keywords > 0 else 0.0
            
            return {
                "ats_score": round(ats_score, 2),
                "keyword_matches": keyword_matches,
                "missing_keywords": missing_keywords,
                "suggestions": suggestions,
                "optimized": ats_score > 0.7
            }
        
        # Register the tool
        ToolRegistry.register("ats_optimizer", optimize_for_ats)
        return optimize_for_ats


def create_resume_tools(resume_service: "ResumeService" = None) -> Dict[str, Any]:
    """Create and register all resume processing tools.
    
    Args:
        resume_service: Resume service instance
        
    Returns:
        Dict[str, Any]: Dictionary of created tools
    """
    logger.info("Creating resume processing tools")
    
    # Create tools instance
    tools = ResumeTools(resume_service=resume_service)
    
    # Create all tools
    created_tools = {
        "resume_processor": tools.create_resume_processor_tool(),
        "job_matcher": tools.create_job_matcher_tool(),
        "keyword_extractor": tools.create_keyword_extractor_tool(),
        "ats_optimizer": tools.create_ats_optimizer_tool()
    }
    
    logger.info(f"Created {len(created_tools)} resume processing tools")
    return created_tools


# Standalone functions for backward compatibility
def create_resume_processor_tool(resume_service: "ResumeService") -> Any:
    """Create and return a resume processor tool.
    
    Backward compatibility function for existing code.
    
    Args:
        resume_service: Resume service instance
        
    Returns:
        Resume processor tool instance
    """
    tools = ResumeTools(resume_service=resume_service)
    return tools.create_resume_processor_tool()


def create_job_matcher_tool() -> Any:
    """Create and return a job matcher tool.
    
    Backward compatibility function for existing code.
    
    Returns:
        Job matcher tool instance
    """
    tools = ResumeTools()
    return tools.create_job_matcher_tool()
