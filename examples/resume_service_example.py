"""Example usage of the refactored resume services.

This example demonstrates how to use the refactored resume services
to process and customize resumes.
"""
import asyncio
import time
import uuid
from pathlib import Path

from app.infrastructure.document_processor import DocumentProcessor
from app.repositories.factory import get_document_repository, get_task_repository
from app.services.resume.storage_service import ResumeStorageService, get_resume_storage_service
from app.services.resume.extraction_service import ResumeExtractionService, get_resume_extraction_service
from app.services.resume.customization_service import ResumeCustomizationService, get_resume_customization_service
from app.services.resume.service import ResumeService, get_resume_service


async def process_resume_example(file_path: str) -> str:
    """Process a resume file and return the task ID.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        str: Task ID for the processed resume
    """
    # Create dependencies
    document_repository = get_document_repository()
    task_repository = get_task_repository()
    document_processor = DocumentProcessor()
    
    # Create services
    storage_service = get_resume_storage_service(document_repository)
    extraction_service = get_resume_extraction_service(document_processor, storage_service)
    customization_service = get_resume_customization_service(extraction_service, storage_service, task_repository)
    resume_service = get_resume_service(storage_service, extraction_service, customization_service)
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Read file content
    with open(file_path, "rb") as f:
        file_content = f.read()
    
    # Process resume
    print(f"Processing resume: {Path(file_path).name}, task: {task_id}")
    result = await resume_service.process_resume(
        file_content=file_content,
        filename=Path(file_path).name,
        task_id=task_id
    )
    
    print(f"Resume processing completed: {result['status']}")
    print(f"Extracted text length: {len(result['text'])}")
    
    return task_id


async def customize_resume_example(resume_id: str, job_description: str) -> str:
    """Customize a resume based on a job description.
    
    Args:
        resume_id: Task ID for the processed resume
        job_description: Job description text
        
    Returns:
        str: Task ID for the customization task
    """
    # Create dependencies
    document_repository = get_document_repository()
    task_repository = get_task_repository()
    document_processor = DocumentProcessor()
    
    # Create services
    storage_service = get_resume_storage_service(document_repository)
    extraction_service = get_resume_extraction_service(document_processor, storage_service)
    customization_service = get_resume_customization_service(extraction_service, storage_service, task_repository)
    resume_service = get_resume_service(storage_service, extraction_service, customization_service)
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Customize resume
    print(f"Customizing resume: {resume_id}, task: {task_id}")
    task_id = await resume_service.customize_resume(
        resume_id=resume_id,
        job_description=job_description,
        task_id=task_id,
        customize_level="standard"
    )
    
    # Poll for completion
    max_retries = 60
    for i in range(max_retries):
        result = await resume_service.get_customization_result(task_id)
        
        if not result:
            print(f"No result for task {task_id}")
            break
        
        if result.get("status") == "completed":
            print(f"Customization completed: {task_id}")
            print(f"Optimized resume length: {len(result.get('result', ''))}")
            break
        
        if result.get("status") == "failed":
            print(f"Customization failed: {result.get('message', 'Unknown error')}")
            break
        
        print(f"Customization in progress: {result.get('progress', 0)}%")
        await asyncio.sleep(2)
    
    return task_id


async def main():
    """Run the example."""
    # Process a resume
    resume_path = Path(__file__).parent.parent / "test_data" / "example_resume.pdf"
    if not resume_path.exists():
        print(f"Resume file not found: {resume_path}")
        return
    
    try:
        # Process resume
        resume_id = await process_resume_example(str(resume_path))
        
        # Sample job description
        job_description = """
        Senior Backend Developer
        
        About Us:
        Our company is a leading software development firm specializing in AI-powered solutions for the finance industry. We're looking for a talented Senior Backend Developer to join our growing team.
        
        Responsibilities:
        • Design and develop scalable, high-performance RESTful APIs
        • Implement efficient database queries and data models
        • Collaborate with frontend developers and data scientists
        • Mentor junior developers and contribute to architecture decisions
        • Participate in code reviews and documentation
        
        Requirements:
        • 5+ years of experience in backend development
        • Strong proficiency in Python (FastAPI or Django)
        • Experience with PostgreSQL and database optimization
        • Familiarity with cloud services (AWS preferred)
        • Knowledge of containerization and orchestration tools
        • Experience with CI/CD pipelines
        • Excellent problem-solving and communication skills
        """
        
        # Customize resume
        customize_id = await customize_resume_example(resume_id, job_description)
        
        print(f"Example completed successfully!")
        print(f"Resume task ID: {resume_id}")
        print(f"Customization task ID: {customize_id}")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
