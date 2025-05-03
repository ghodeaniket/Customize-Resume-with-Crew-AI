"""Refactored orchestrator service for resume customization workflow."""
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
from app.services.resume.customization.crew_execution_service import CrewExecutionService
from app.services.resume.customization.task_progress_service import TaskProgressService
from app.services.resume.customization.validation_service import CustomizationValidationService
from app.services.resume.customization.error_handling_service import ErrorHandlingService
from app.services.resume.customization.state_management_service import StateManagementService


class ResumeCustomizationOrchestrator(BaseService[Dict[str, Any], str]):
    """Orchestrator service for coordinating the resume customization workflow."""
    
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
        self.crew_execution = CrewExecutionService()
        self.task_progress = TaskProgressService(task_repository)
        self.validation = CustomizationValidationService(extraction_service)
        self.error_handler = ErrorHandlingService(task_repository)
        self.state_manager = StateManagementService()
        
        logger.info("Initialized ResumeCustomizationOrchestrator")
    
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
            customize_level: Level of customization
            
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
            # Phase 1: Validation and Setup
            await self._validate_and_setup(
                resume_id, job_description, customize_level, task_id, state
            )
            
            # Phase 2: CrewAI Setup
            crew, agents = await self._setup_crew_environment(state, task_id)
            
            # Phase 3: Job Analysis
            job_analysis_result = await self._perform_job_analysis(
                crew, agents["analyzer"], job_description, task_id, state
            )
            
            # Phase 4: Resume Optimization
            optimized_resume = await self._perform_resume_optimization(
                crew, agents["optimizer"], job_analysis_result, task_id, state
            )
            
            # Phase 5: Finalization
            await self._finalize_customization(
                task_id, optimized_resume, start_time, state
            )
            
            return task_id
            
        except Exception as e:
            await self.error_handler.handle_customization_error(
                error=e,
                task_id=task_id,
                start_time=start_time,
                state=state
            )
            raise CustomizationError(f"Resume customization failed: {str(e)}")
    
    async def _validate_and_setup(
        self,
        resume_id: str,
        job_description: str,
        customize_level: str,
        task_id: str,
        state: CustomizationState
    ) -> None:
        """Validate inputs and setup initial state.
        
        Args:
            resume_id: Resume identifier
            job_description: Job description text
            customize_level: Customization level
            task_id: Task identifier
            state: Customization state
        """
        # Validate inputs
        await self.validation.validate_resume_exists(resume_id)
        self.validation.validate_job_description(job_description)
        self.validation.validate_customize_level(customize_level)
        
        # Initialize task tracking
        await self.task_progress.initialize_task(task_id, resume_id, customize_level)
        
        # Get and validate resume text
        resume_text = await self.validation.validate_resume_has_text(resume_id)
        
        # Update state
        self.state_manager.update_optimization_state(
            state=state,
            resume_text=resume_text
        )
        self.state_manager.update_progress(state, 10.0)
        
        # Update task progress
        await self.task_progress.update_progress(
            task_id, 10.0, "Retrieved resume text"
        )
    
    async def _setup_crew_environment(
        self,
        state: CustomizationState,
        task_id: str
    ) -> tuple[Any, Dict[str, Any]]:
        """Set up CrewAI environment and agents.
        
        Args:
            state: Customization state
            task_id: Task identifier
            
        Returns:
            tuple: Crew instance and agents dictionary
        """
        # Set up environment
        self.crew_setup.setup_environment()
        
        # Create LLM and tools
        llm = self.crew_setup.create_llm()
        tools = await self.crew_setup.create_tools(self)
        
        # Create agents
        agents = await self.crew_setup.create_agents(llm, tools)
        
        # Update state and progress
        self.state_manager.update_progress(state, 20.0)
        await self.task_progress.update_progress(
            task_id, 20.0, "Created AI agents"
        )
        
        # Create crew with initial agents
        crew = self.crew_setup.create_crew(
            agents=[agents["analyzer"], agents["optimizer"]],
            tasks=[]  # Tasks will be added dynamically
        )
        
        return crew, agents
    
    async def _perform_job_analysis(
        self,
        crew: Any,
        analyzer_agent: Any,
        job_description: str,
        task_id: str,
        state: CustomizationState
    ) -> Optional[str]:
        """Perform job analysis phase.
        
        Args:
            crew: CrewAI crew instance
            analyzer_agent: Analyzer agent
            job_description: Job description text
            task_id: Task identifier
            state: Customization state
            
        Returns:
            Optional[str]: Job analysis result or None for fallback
        """
        # Create job analysis task
        from app.cores.tasks.analyze_job import create_job_analysis_task
        job_analysis_task = create_job_analysis_task(
            agent=analyzer_agent,
            job_description=job_description
        )
        
        # Update crew tasks
        crew.tasks = [job_analysis_task]
        
        # Update state and progress
        self.state_manager.update_job_analysis_state(
            state=state,
            job_description=job_description
        )
        self.state_manager.update_progress(state, 30.0)
        
        await self.task_progress.update_progress(
            task_id, 30.0, "Analyzing job description"
        )
        
        # Run job analysis
        return await self.crew_execution.run_job_analysis(crew, state)
    
    async def _perform_resume_optimization(
        self,
        crew: Any,
        optimizer_agent: Any,
        job_analysis_result: Optional[str],
        task_id: str,
        state: CustomizationState
    ) -> str:
        """Perform resume optimization phase.
        
        Args:
            crew: CrewAI crew instance
            optimizer_agent: Optimizer agent
            job_analysis_result: Job analysis result (may be None)
            task_id: Task identifier
            state: Customization state
            
        Returns:
            str: Optimized resume text
        """
        await self.task_progress.update_progress(
            task_id, 60.0, "Job analysis completed, optimizing resume"
        )
        
        # Run resume optimization
        return await self.crew_execution.run_resume_optimization(
            crew=crew,
            optimizer_agent=optimizer_agent,
            job_analysis_result=job_analysis_result,
            state=state
        )
    
    async def _finalize_customization(
        self,
        task_id: str,
        optimized_resume: str,
        start_time: float,
        state: CustomizationState
    ) -> None:
        """Finalize the customization process.
        
        Args:
            task_id: Task identifier
            optimized_resume: Optimized resume text
            start_time: Process start time
            state: Customization state
        """
        # Store the result
        await self.storage_service.save_result(task_id, optimized_resume)
        
        # Mark state as completed
        self.state_manager.mark_completed(state)
        
        # Mark task as completed
        await self.task_progress.mark_completed(task_id, start_time)
        
        logger.info(
            f"Resume customization completed for task {task_id}, "
            f"took {time.time() - start_time:.2f} seconds"
        )
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get customization task by ID."""
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
        """Check if a customization task exists."""
        try:
            task = await self.task_repository.get_task(id)
            return task is not None
        except Exception as e:
            logger.error(f"Error checking if task {id} exists: {str(e)}", exc_info=True)
            return False
