"""Service for executing CrewAI workflows."""
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.core.exceptions import CustomizationError
from app.services.resume.customization.job_analysis_service import JobAnalysisService
from app.services.resume.customization.resume_optimization_service import ResumeOptimizationService
from app.services.resume.customization.state_management_service import StateManagementService
from app.services.resume.customization.state_models import CustomizationState


class CrewExecutionService:
    """Service for executing CrewAI analysis and optimization workflows."""
    
    def __init__(self):
        """Initialize the crew execution service."""
        self.job_analysis = JobAnalysisService()
        self.resume_optimization = ResumeOptimizationService()
        self.state_manager = StateManagementService()
    
    async def run_job_analysis(
        self, crew: Any, state: CustomizationState
    ) -> str:
        """Run the job analysis phase.
        
        Args:
            crew: CrewAI crew instance
            state: Customization state
            
        Returns:
            str: Job analysis result
        """
        try:
            # Perform job analysis
            job_analysis_result = await self.job_analysis.analyze_job_description(
                crew, state.job_analysis.job_description
            )
            
            # Update state
            self.state_manager.update_job_analysis_state(
                state=state,
                job_description=state.job_analysis.job_description,
                analysis_result=job_analysis_result,
                completed=True
            )
            
            # Log the analysis result
            self.job_analysis.log_analysis_result(job_analysis_result)
            
            return job_analysis_result
            
        except AttributeError as e:
            # Handle specific error type
            if "'str' object has no attribute 'get'" in str(e):
                logger.warning("Handling AttributeError with job analysis result")
                
                # Mark job analysis as completed with formatting issues
                self.state_manager.update_job_analysis_state(
                    state=state,
                    job_description=state.job_analysis.job_description,
                    completed=True
                )
                
                # Return None to signal fallback should be used
                return None
            else:
                # Re-raise if it's not the specific error we're handling
                raise
    
    async def run_resume_optimization(
        self,
        crew: Any,
        optimizer_agent: Any,
        job_analysis_result: Optional[str],
        state: CustomizationState
    ) -> str:
        """Run the resume optimization phase.
        
        Args:
            crew: CrewAI crew instance
            optimizer_agent: Optimizer agent instance
            job_analysis_result: Result from job analysis (may be None)
            state: Customization state
            
        Returns:
            str: Optimized resume text
        """
        try:
            if job_analysis_result:
                # Standard optimization approach
                optimized_resume = await self.resume_optimization.optimize_resume(
                    crew=crew,
                    optimizer_agent=optimizer_agent,
                    resume_text=state.resume_optimization.resume_text,
                    job_analysis_result=job_analysis_result,
                    customize_level=state.customize_level
                )
            else:
                # Fallback optimization approach
                optimized_resume = await self.resume_optimization.optimize_resume_fallback(
                    crew=crew,
                    optimizer_agent=optimizer_agent,
                    resume_text=state.resume_optimization.resume_text,
                    job_description_text=state.job_analysis.job_description,
                    customize_level=state.customize_level
                )
            
            # Update state
            self.state_manager.update_optimization_state(
                state=state,
                optimized_resume=optimized_resume,
                completed=True
            )
            
            return optimized_resume
            
        except Exception as e:
            # Update state with error
            self.state_manager.update_optimization_state(
                state=state,
                error=str(e)
            )
            raise CustomizationError(f"Resume optimization failed: {str(e)}")
