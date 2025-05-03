"""Slim orchestrator service for resume customization workflow."""
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
from app.services.resume.customization.workflow_setup_service import WorkflowSetupService
from app.services.resume.customization.workflow_execution_service import WorkflowExecutionService


class ResumeCustomizationService(BaseService[Dict[str, Any], str]):
    """Slim orchestrator for resume customization workflow."""
    
    def __init__(
        self,
        extraction_service: ResumeExtractionService,
        storage_service: ResumeStorageService,
        task_repository: TaskRepository
    ):
        """Initialize the customization service.
        
        Args:
            extraction_service: Extraction service for resume text
            storage_service: Storage service for persistence  
            task_repository: Repository for task data access
        """
        self.extraction_service = extraction_service
        self.storage_service = storage_service
        self.task_repository = task_repository
        
        # Initialize core services
        crew_setup = CrewSetupService()
        crew_execution = CrewExecutionService()
        task_progress = TaskProgressService(task_repository)
        validation = CustomizationValidationService(extraction_service)
        error_handler = ErrorHandlingService(task_repository)
        state_manager = StateManagementService()
        
        # Initialize workflow services
        self.workflow_setup = WorkflowSetupService(
            crew_setup=crew_setup,
            task_progress=task_progress,
            validation=validation,
            state_manager=state_manager
        )
        
        self.workflow_execution = WorkflowExecutionService(
            crew_execution=crew_execution,
            task_progress=task_progress,
            state_manager=state_manager,
            storage_service=storage_service
        )
        
        self.error_handler = error_handler
        
        logger.info("Initialized ResumeCustomizationService")
    
    async def customize_resume(
        self, 
        resume_id: str, 
        job_description: str, 
        task_id: str,
        customize_level: str = "standard"
    ) -> str:
        """Customize a resume based on a job description.
        
        Args:
            resume_id: Resume task identifier
            job_description: Job description text
            task_id: New task identifier for customization
            customize_level: Level of customization
            
        Returns:
            str: Task ID for the customization task
        """
        start_time = time.time()
        state = CustomizationState(
            task_id=task_id,
            resume_id=resume_id,
            customize_level=customize_level,
            started_at=start_time,
            progress=0.0
        )
        
        try:
            # Phase 1: Validation and Setup
            await self.workflow_setup.validate_and_setup(
                resume_id, job_description, customize_level, task_id, state
            )
            
            # Phase 2: CrewAI Setup
            crew, agents = await self.workflow_setup.setup_crew_environment(state, task_id)
            
            # Phase 3: Job Analysis
            job_analysis_result = await self.workflow_execution.perform_job_analysis(
                crew, agents["analyzer"], job_description, task_id, state
            )
            
            # Phase 4: Resume Optimization
            optimized_resume = await self.workflow_execution.perform_resume_optimization(
                crew, agents["optimizer"], job_analysis_result, task_id, state
            )
            
            # Phase 5: Finalization
            await self.workflow_execution.finalize_customization(
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


# Factory function for dependency injection
def get_resume_customization_service(
    extraction_service: ResumeExtractionService,
    storage_service: ResumeStorageService,
    task_repository: TaskRepository
) -> ResumeCustomizationService:
    """Get resume customization service instance."""
    return ResumeCustomizationService(
        extraction_service=extraction_service,
        storage_service=storage_service,
        task_repository=task_repository
    )
