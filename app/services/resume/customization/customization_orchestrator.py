"""Orchestrator service for resume customization workflow."""
import time
from typing import Dict, Any, Optional

from app.core.logging import logger
from app.core.exceptions import CustomizationError
from app.services.resume.base import BaseService
from app.services.resume.storage_service import ResumeStorageService
from app.services.resume.extraction_service import ResumeExtractionService
from app.repositories.task_repository import TaskRepository
from app.services.resume.customization.state_models import CustomizationState
from app.services.resume.customization.crew_setup_service import CrewSetupService
from app.services.resume.customization.job_analysis_service import JobAnalysisService
from app.services.resume.customization.resume_optimization_service import ResumeOptimizationService
from app.services.resume.customization.task_progress_service import TaskProgressService
from app.services.resume.customization.validation_service import CustomizationValidationService
from app.services.resume.customization.error_handling_service import ErrorHandlingService


class CustomizationOrchestrator(BaseService[Dict[str, Any], str]):
    """Orchestrator service for coordinating the resume customization workflow.
    
    This service coordinates all the individual services involved in the
    resume customization process, from validation through completion.
    """
    
    def __init__(
        self,
        extraction_service: ResumeExtractionService,
        storage_service: ResumeStorageService,
        task_repository: TaskRepository
    ):
        """Initialize the customization orchestrator.
        
        Args:
            extraction_service: Extraction service for resume text
            storage_service: Storage service for persistence  
            task_repository: Repository for task data access
        """
        self.extraction_service = extraction_service
        self.storage_service = storage_service
        self.task_repository = task_repository
        
        # Initialize sub-services
        self.crew_setup = CrewSetupService()
        self.job_analysis = JobAnalysisService()
        self.resume_optimization = ResumeOptimizationService()
        self.task_progress = TaskProgressService(task_repository)
        self.validation = CustomizationValidationService(extraction_service)
        self.error_handler = ErrorHandlingService(task_repository)
        
        logger.info("Initialized CustomizationOrchestrator with all sub-services")
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        This method is required by the ResumeProcessorTool and delegates
        to the extraction service.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data including text and metadata
        """
        try:
            metadata = await self.storage_service.get_metadata(task_id)
            text = await self.storage_service.get_extracted_text(task_id)
            
            if not text:
                logger.warning(f"No extracted text found for task {task_id}")
                return None
            
            # Return the data in the format expected by the tool
            return {
                "status": metadata.get("status", "unknown"),
                "text": text,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting resume data for task {task_id}: {str(e)}", exc_info=True)
            return None
    
    async def customize_resume(
        self, 
        resume_id: str, 
        job_description: str, 
        task_id: str,
        customize_level: str = "standard"
    ) -> str:
        """Customize a resume based on a job description using CrewAI.
        
        Args:
            resume_id: Resume task identifier
            job_description: Job description text
            task_id: New task identifier for customization
            customize_level: Level of customization (minimal, standard, comprehensive)
            
        Returns:
            str: Task ID for the customization task
            
        Raises:
            ResumeNotFoundError: If the resume doesn't exist
            CustomizationError: If the customization process fails
        """
        start_time = time.time()
        logger.info(f"Starting resume customization for resume {resume_id}")
        
        # Create state object
        state = CustomizationState(
            task_id=task_id,
            resume_id=resume_id,
            customize_level=customize_level,
            started_at=start_time,
            progress=0.0
        )
        
        try:
            # Validate inputs
            await self.validation.validate_resume_exists(resume_id)
            self.validation.validate_job_description(job_description)
            self.validation.validate_customize_level(customize_level)
            
            # Initialize task tracking
            await self.task_progress.initialize_task(task_id, resume_id, customize_level)
            
            # Get and validate resume text
            resume_text = await self.validation.validate_resume_has_text(resume_id)
            state.resume_optimization.resume_text = resume_text
            state.progress = 10.0
            
            await self.task_progress.update_progress(
                task_id, 10.0, "Retrieved resume text"
            )
            
            # Set up CrewAI environment
            self.crew_setup.setup_environment()
            llm = self.crew_setup.create_llm()
            tools = await self.crew_setup.create_tools(self)
            agents = await self.crew_setup.create_agents(llm, tools)
            
            state.progress = 20.0
            await self.task_progress.update_progress(
                task_id, 20.0, "Created AI agents"
            )
            
            # Create job analysis task
            job_analysis_task = await self.job_analysis.create_analysis_task(
                agent=agents["analyzer"],
                job_description=job_description
            )
            
            state.job_analysis.job_description = job_description
            state.progress = 30.0
            
            await self.task_progress.update_progress(
                task_id, 30.0, "Analyzing job description"
            )
            
            # Create crew
            crew = self.crew_setup.create_crew(
                agents=[agents["analyzer"], agents["optimizer"]],
                tasks=[job_analysis_task]
            )
            
            # Run job analysis
            job_analysis_result = await self._run_job_analysis(crew, state)
            
            # Run resume optimization
            optimized_resume = await self._run_resume_optimization(
                crew=crew,
                agents=agents,
                job_analysis_result=job_analysis_result,
                state=state
            )
            
            # Store the result
            await self.storage_service.save_result(task_id, optimized_resume)
            
            # Mark task completed
            state.status = "completed"
            state.progress = 100.0
            state.completed_at = time.time()
            
            await self.task_progress.mark_completed(task_id, start_time)
            
            return task_id
            
        except Exception as e:
            # Handle errors
            await self.error_handler.handle_customization_error(
                error=e,
                task_id=task_id,
                start_time=start_time,
                state=state
            )
            raise CustomizationError(f"Resume customization failed: {str(e)}")
    
    async def _run_job_analysis(
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
            job_analysis_result = await self.job_analysis.analyze_job_description(
                crew, state.job_analysis.job_description
            )
            
            # Update state
            state.job_analysis.analysis_result = job_analysis_result
            state.job_analysis.completed = True
            state.progress = 60.0
            
            # Update task progress
            await self.task_progress.update_state_progress(self.task_repository, state)
            
            # Log the analysis result
            self.job_analysis.log_analysis_result(job_analysis_result)
            
            return job_analysis_result
            
        except AttributeError as e:
            # Handle specific error type
            if "'str' object has no attribute 'get'" in str(e):
                logger.warning("Handling AttributeError with job analysis result")
                
                # Mark job analysis as completed with formatting issues
                state.job_analysis.completed = True
                state.progress = 60.0
                
                await self.task_progress.update_progress(
                    self.task_repository, 
                    60.0, 
                    "Job analysis completed with formatting issues, optimizing resume"
                )
                
                # Return None to signal fallback should be used
                return None
            else:
                # Re-raise if it's not the specific error we're handling
                raise
    
    async def _run_resume_optimization(
        self,
        crew: Any,
        agents: Dict[str, Any],
        job_analysis_result: Optional[str],
        state: CustomizationState
    ) -> str:
        """Run the resume optimization phase.
        
        Args:
            crew: CrewAI crew instance
            agents: Dictionary of agents
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
                    optimizer_agent=agents["optimizer"],
                    resume_text=state.resume_optimization.resume_text,
                    job_analysis_result=job_analysis_result,
                    customize_level=state.customize_level
                )
            else:
                # Fallback optimization approach
                optimized_resume = await self.resume_optimization.optimize_resume_fallback(
                    crew=crew,
                    optimizer_agent=agents["optimizer"],
                    resume_text=state.resume_optimization.resume_text,
                    job_description_text=state.job_analysis.job_description,
                    customize_level=state.customize_level
                )
            
            # Update state
            state.resume_optimization.optimized_resume = optimized_resume
            state.resume_optimization.completed = True
            state.progress = 100.0
            
            return optimized_resume
            
        except Exception as e:
            # Update state with error
            state.resume_optimization.error = str(e)
            state.error_message = f"Resume optimization failed: {str(e)}"
            raise
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get customization task by ID.
        
        Args:
            id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Customization task data if found
        """
        try:
            task = await self.task_repository.get_task(id)
            
            if not task:
                logger.debug(f"No task found for ID {id}")
                return None
            
            # For completed tasks, include the result
            if task.get("status") == "completed":
                result_content = await self.storage_service.get_result(id)
                
                return {
                    "task_id": id,
                    "status": "completed",
                    "result": result_content,
                    "metadata": task
                }
            
            # For other task statuses
            return {
                "task_id": id,
                "status": task.get("status", "unknown"),
                "progress": task.get("progress", 0.0),
                "message": task.get("message", ""),
                "metadata": task
            }
            
        except Exception as e:
            logger.error(f"Error getting customization task {id}: {str(e)}", exc_info=True)
            return None
    
    async def exists(self, id: str) -> bool:
        """Check if a customization task exists.
        
        Args:
            id: Task identifier
            
        Returns:
            bool: True if the task exists, False otherwise
        """
        try:
            task = await self.task_repository.get_task(id)
            return task is not None
        except Exception as e:
            logger.error(f"Error checking if task {id} exists: {str(e)}", exc_info=True)
            return False
