"""Test resume service with CrewAI integration."""
import os
import uuid
import asyncio
from dotenv import load_dotenv
from app.infrastructure.document_processor import DocumentProcessor
from app.services.document_storage_service import DocumentStorageService
from app.services.task_service import TaskService
from app.services.resume_service import ResumeService
from app.core.logging import logger

async def test_resume_service():
    """Test resume service functionality."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Log API key status
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
        if not api_key:
            print("No API key found in environment variables. CrewAI functionality will fail.")
        else:
            print(f"API key loaded: {api_key[:5]}...{api_key[-5:]}")
        
        # Initialize services
        document_processor = DocumentProcessor()
        storage_service = DocumentStorageService()
        task_service = TaskService(storage_service=storage_service)
        resume_service = ResumeService(
            document_processor=document_processor,
            storage_service=storage_service,
            task_service=task_service
        )
        
        # Test resume processing
        print("Testing resume processing...")
        with open("test_resume.txt", "rb") as f:
            content = f.read()
        
        task_id = str(uuid.uuid4())
        process_result = await resume_service.process_resume(
            file_content=content,
            filename="test_resume.txt",
            task_id=task_id
        )
        
        print(f"Resume processing result: {process_result}")
        
        # Get resume data
        resume_data = await resume_service.get_resume_data(task_id)
        print(f"Resume data: {resume_data}")
        
        # Test resume customization (if API key is available)
        if api_key:
            print("Testing resume customization...")
            customization_task_id = str(uuid.uuid4())
            job_description = """
            Software Engineer Position
            
            Requirements:
            - Python programming skills
            - Experience with FastAPI
            - Knowledge of AI and automation
            - Good communication skills
            """
            
            try:
                customize_result = await resume_service.customize_resume(
                    resume_id=task_id,
                    job_description=job_description,
                    task_id=customization_task_id
                )
                
                print(f"Customization initiated: {customize_result}")
                
                # Wait for result
                print("Waiting for customization to complete...")
                for _ in range(10):
                    result = await resume_service.get_customization_result(customization_task_id)
                    if result and result.get("status") in ["completed", "failed"]:
                        print(f"Final customization result: {result}")
                        break
                    print(f"Status: {result.get('status')}, Progress: {result.get('progress')}")
                    await asyncio.sleep(5)
            except Exception as e:
                print(f"Error during customization: {str(e)}")
        else:
            print("Skipping customization test due to missing API key")
        
        return True
    except Exception as e:
        logger.error(f"Error testing resume service: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_resume_service())
    print(f"Test result: {'Success' if result else 'Failed'}")
