"""Service for managing workflow execution phases."""
import time
from typing import Optional, Any, Dict

from app.core.logging import logger
from app.services.resume.storage_service import ResumeStorageService
from app.services.resume.customization.crew_execution_service import CrewExecutionService
from app.services.resume.customization.task_progress_service import TaskProgressService
from app.services.resume.customization.state_management_service import StateManagementService
from app.services.resume.customization.state_models import CustomizationState
from app.repositories.filesystem.customization_repository import CustomizationRepository


class WorkflowExecutionService:
    """Service for managing workflow execution phases."""
    
    def __init__(
        self,
        crew_execution: CrewExecutionService,
        task_progress: TaskProgressService,
        state_manager: StateManagementService,
        storage_service: ResumeStorageService,
        customization_repository: CustomizationRepository = None
    ):
        """Initialize the workflow execution service.
        
        Args:
            crew_execution: CrewAI execution service
            task_progress: Task progress service
            state_manager: State management service
            storage_service: Storage service
            customization_repository: Repository for customization results
        """
        self.crew_execution = crew_execution
        self.task_progress = task_progress
        self.state_manager = state_manager
        self.storage_service = storage_service
        self.customization_repository = customization_repository or CustomizationRepository()
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        This method is required by the ResumeProcessorTool and delegates
        to the storage service.
        
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
    
    async def perform_job_analysis(
        self,
        crew: Any,
        analyzer_agent: Any,
        job_description: str,
        task_id: str,
        state: CustomizationState
    ) -> Optional[str]:
        """Phase 3: Perform job analysis.
        
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
        from app.crews.tasks.analyze_job import create_job_analysis_task
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
    
    async def perform_resume_optimization(
        self,
        crew: Any,
        optimizer_agent: Any,
        job_analysis_result: Optional[str],
        task_id: str,
        state: CustomizationState
    ) -> str:
        """Phase 4: Perform resume optimization.
        
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
    
    async def finalize_customization(
        self,
        task_id: str,
        optimized_resume: str,
        start_time: float,
        state: CustomizationState
    ) -> None:
        """Phase 5: Finalize the customization process.
        
        Args:
            task_id: Task identifier
            optimized_resume: Optimized resume text
            start_time: Process start time
            state: Customization state
        """
        # Store the result in the original location
        await self.storage_service.save_result(task_id, optimized_resume)
        
        # Also save to the customizations directory
        await self.customization_repository.save_customized_text(optimized_resume, task_id)
        
        # Mark state as completed
        self.state_manager.mark_completed(state)
        
        # Mark task as completed
        await self.task_progress.mark_completed(task_id, start_time)
        
        logger.info(
            f"Resume customization completed for task {task_id}, "
            f"took {time.time() - start_time:.2f} seconds"
        )
