"""Service for managing workflow setup phases."""
from typing import Dict, Any, Tuple, Optional

from app.core.logging import logger
from app.services.resume.customization.crew_setup_service import CrewSetupService
from app.services.resume.customization.task_progress_service import TaskProgressService
from app.services.resume.customization.validation_service import CustomizationValidationService
from app.services.resume.customization.state_management_service import StateManagementService
from app.services.resume.customization.state_models import CustomizationState
from app.services.resume.storage_service import ResumeStorageService


class WorkflowSetupService:
    """Service for managing workflow setup and crew environment phases."""
    
    def __init__(
        self,
        crew_setup: CrewSetupService,
        task_progress: TaskProgressService,  
        validation: CustomizationValidationService,
        state_manager: StateManagementService,
        storage_service: Optional[ResumeStorageService] = None
    ):
        """Initialize the workflow setup service.
        
        Args:
            crew_setup: CrewAI setup service
            task_progress: Task progress service
            validation: Validation service
            state_manager: State management service
            storage_service: Optional storage service for resume data access
        """
        self.crew_setup = crew_setup
        self.task_progress = task_progress
        self.validation = validation
        self.state_manager = state_manager
        self.storage_service = storage_service
    
    async def get_resume_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get resume data by task ID.
        
        This method is required by the ResumeProcessorTool and delegates
        to the storage service if available.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Optional[Dict[str, Any]]: Resume data including text and metadata
        """
        if not self.storage_service:
            logger.error("Storage service not available in WorkflowSetupService")
            return None
        
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
    
    async def validate_and_setup(
        self,
        resume_id: str,
        job_description: str,
        customize_level: str,
        task_id: str,
        state: CustomizationState
    ) -> None:
        """Phase 1: Validate inputs and setup initial state.
        
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
    
    async def setup_crew_environment(
        self,
        state: CustomizationState,
        task_id: str,
        resume_service_instance: Optional[Any] = None
    ) -> Tuple[Any, Dict[str, Any]]:
        """Phase 2: Set up CrewAI environment and agents.
        
        Args:
            state: Customization state
            task_id: Task identifier
            resume_service_instance: Instance with get_resume_data method, defaults to self
            
        Returns:
            Tuple: Crew instance and agents dictionary
        """
        # Set up environment
        self.crew_setup.setup_environment()
        
        # Create LLM and tools
        llm = self.crew_setup.create_llm()
        # If resume_service_instance is not provided, use self
        resume_service = resume_service_instance or self
        tools = await self.crew_setup.create_tools(resume_service)
        
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
