"""
Locust performance tests for the Resume Customizer API.

This file defines user behaviors for load testing the API.
It simulates realistic user flows for measuring performance.
"""
import os
import time
import json
import random
from pathlib import Path
from typing import Optional, Dict, Any, List

from locust import HttpUser, task, between, tag, events
from locust.env import Environment


class ResumeCustomizerUser(HttpUser):
    """User class that simulates a typical user interacting with the Resume Customizer API."""
    
    # Wait between 1 and 5 seconds between tasks
    wait_time = between(1, 5)
    
    # Store task IDs and status for workflow tracking
    resume_task_id: Optional[str] = None
    customization_task_id: Optional[str] = None
    polling_delay = 2.0  # Initial polling delay (seconds)
    max_polling_delay = 10.0  # Maximum polling delay (seconds)
    
    def on_start(self):
        """Initialize user session."""
        # Load test data files
        self.test_data_dir = Path(__file__).parent.parent.parent / "test_data"
        
        # Prepare resume file
        self.resume_path = self.test_data_dir / "test_resume.pdf"
        if not self.resume_path.exists():
            self.resume_path = None
            self.environment.runner.logger.error("Test resume file not found")
        
        # Prepare job description
        self.job_description_path = self.test_data_dir / "test_job_description.txt"
        if self.job_description_path.exists():
            with open(self.job_description_path, "r") as f:
                self.job_description = f.read()
        else:
            self.job_description = "Sample job description for performance testing."
            self.environment.runner.logger.warning("Using fallback job description")
        
        # Customization levels
        self.customize_levels = ["minimal", "standard", "comprehensive"]
    
    @tag("health")
    @task(10)  # Higher weight for health check (common operation)
    def check_health(self):
        """Check API health."""
        with self.client.get("/api/health", name="Health Check") as response:
            if response.status_code != 200:
                self.environment.runner.logger.error(f"Health check failed: {response.status_code}")
    
    @tag("upload")
    @task(5)
    def upload_resume(self):
        """Upload a resume file."""
        if not self.resume_path or not self.resume_path.exists():
            self.environment.runner.logger.error("Test resume file not available for upload")
            return
        
        with open(self.resume_path, "rb") as resume_file:
            files = {"resume": ("test_resume.pdf", resume_file, "application/pdf")}
            with self.client.post(
                "/api/resumes/upload", 
                files=files,
                name="Upload Resume"
            ) as response:
                if response.status_code == 200:
                    result = response.json()
                    self.resume_task_id = result.get("task_id")
                    self.environment.runner.logger.info(f"Uploaded resume, task ID: {self.resume_task_id}")
                else:
                    self.environment.runner.logger.error(f"Resume upload failed: {response.status_code}")
    
    @tag("status")
    @task(8)
    def check_resume_status(self):
        """Check the status of a resume processing task."""
        if not self.resume_task_id:
            return
        
        with self.client.get(
            f"/api/resumes/{self.resume_task_id}", 
            name="Check Resume Status"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                progress = result.get("progress", 0)
                
                if status == "completed":
                    self.environment.runner.logger.info(f"Resume processing completed: {self.resume_task_id}")
                elif status == "failed":
                    self.environment.runner.logger.error(f"Resume processing failed: {self.resume_task_id}")
                    self.resume_task_id = None  # Reset to trigger new upload
            elif response.status_code == 404:
                self.environment.runner.logger.warning(f"Resume task not found: {self.resume_task_id}")
                self.resume_task_id = None  # Reset to trigger new upload
            else:
                self.environment.runner.logger.error(f"Check resume status failed: {response.status_code}")
    
    @tag("extract")
    @task(3)
    def get_resume_text(self):
        """Get the extracted text from a processed resume."""
        if not self.resume_task_id:
            return
        
        with self.client.get(
            f"/api/resumes/{self.resume_task_id}/text", 
            name="Get Resume Text"
        ) as response:
            if response.status_code == 200:
                self.environment.runner.logger.debug(f"Retrieved resume text: {self.resume_task_id}")
            elif response.status_code == 400:
                self.environment.runner.logger.info("Resume processing not complete yet")
            elif response.status_code == 404:
                self.environment.runner.logger.warning(f"Resume text not found: {self.resume_task_id}")
                self.resume_task_id = None  # Reset to trigger new upload
            else:
                self.environment.runner.logger.error(f"Get resume text failed: {response.status_code}")
    
    @tag("customize")
    @task(4)
    def customize_resume(self):
        """Request resume customization."""
        if not self.resume_task_id:
            return
        
        # Randomly select a customization level
        customize_level = random.choice(self.customize_levels)
        
        request_data = {
            "resume_id": self.resume_task_id,
            "job_description": self.job_description,
            "customize_level": customize_level
        }
        
        with self.client.post(
            "/api/resumes/customize", 
            json=request_data,
            name="Customize Resume"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                self.customization_task_id = result.get("task_id")
                self.environment.runner.logger.info(
                    f"Customization requested: {self.customization_task_id}, "
                    f"level: {customize_level}"
                )
            elif response.status_code == 404:
                self.environment.runner.logger.warning(f"Resume not found for customization: {self.resume_task_id}")
                self.resume_task_id = None  # Reset to trigger new upload
            else:
                self.environment.runner.logger.error(f"Customize resume failed: {response.status_code}")
    
    @tag("customize_status")
    @task(7)
    def check_customization_status(self):
        """Check the status of a customization task."""
        if not self.customization_task_id:
            return
        
        with self.client.get(
            f"/api/resumes/customization/{self.customization_task_id}", 
            name="Check Customization Status"
        ) as response:
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                progress = result.get("progress", 0)
                
                if status == "completed":
                    self.environment.runner.logger.info(f"Customization completed: {self.customization_task_id}")
                elif status == "failed":
                    self.environment.runner.logger.error(f"Customization failed: {self.customization_task_id}")
                    self.customization_task_id = None
            elif response.status_code == 404:
                self.environment.runner.logger.warning(f"Customization task not found: {self.customization_task_id}")
                self.customization_task_id = None
            else:
                self.environment.runner.logger.error(f"Check customization status failed: {response.status_code}")
    
    @tag("result")
    @task(2)
    def get_customization_result(self):
        """Get the result of a completed customization task."""
        if not self.customization_task_id:
            return
        
        with self.client.get(
            f"/api/resumes/customization/{self.customization_task_id}/result", 
            name="Get Customization Result"
        ) as response:
            if response.status_code == 200:
                self.environment.runner.logger.debug(f"Retrieved customization result: {self.customization_task_id}")
                # Reset after getting result to trigger new cycle
                self.customization_task_id = None
            elif response.status_code == 400:
                self.environment.runner.logger.info("Customization not complete yet")
            elif response.status_code == 404:
                self.environment.runner.logger.warning(f"Customization result not found: {self.customization_task_id}")
                self.customization_task_id = None
            else:
                self.environment.runner.logger.error(f"Get customization result failed: {response.status_code}")
    
    @tag("workflow")
    @task(1)
    def complete_workflow(self):
        """Simulate a complete workflow from upload to result retrieval."""
        if not self.resume_path or not self.resume_path.exists():
            self.environment.runner.logger.error("Test resume file not available for upload")
            return
        
        # Upload resume
        with open(self.resume_path, "rb") as resume_file:
            files = {"resume": ("test_resume.pdf", resume_file, "application/pdf")}
            with self.client.post(
                "/api/resumes/upload", 
                files=files,
                name="Workflow - Upload Resume"
            ) as response:
                if response.status_code != 200:
                    self.environment.runner.logger.error(f"Workflow - Resume upload failed: {response.status_code}")
                    return
                
                workflow_resume_id = response.json().get("task_id")
        
        # Poll for resume processing completion
        polling_delay = self.polling_delay
        max_wait_time = 60  # Maximum wait time in seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            with self.client.get(
                f"/api/resumes/{workflow_resume_id}", 
                name="Workflow - Poll Resume Status"
            ) as response:
                if response.status_code != 200:
                    self.environment.runner.logger.error(
                        f"Workflow - Check resume status failed: {response.status_code}"
                    )
                    return
                
                result = response.json()
                status = result.get("status")
                
                if status == "completed":
                    break
                elif status == "failed":
                    self.environment.runner.logger.error(f"Workflow - Resume processing failed")
                    return
            
            # Wait with exponential backoff
            time.sleep(polling_delay)
            polling_delay = min(polling_delay * 1.5, self.max_polling_delay)
        
        # If timed out
        if time.time() - start_time >= max_wait_time:
            self.environment.runner.logger.warning("Workflow - Resume processing timed out")
            return
        
        # Request customization
        customize_level = random.choice(self.customize_levels)
        request_data = {
            "resume_id": workflow_resume_id,
            "job_description": self.job_description,
            "customize_level": customize_level
        }
        
        with self.client.post(
            "/api/resumes/customize", 
            json=request_data,
            name="Workflow - Customize Resume"
        ) as response:
            if response.status_code != 200:
                self.environment.runner.logger.error(f"Workflow - Customize resume failed: {response.status_code}")
                return
            
            workflow_customization_id = response.json().get("task_id")
        
        # Poll for customization completion
        polling_delay = self.polling_delay
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            with self.client.get(
                f"/api/resumes/customization/{workflow_customization_id}", 
                name="Workflow - Poll Customization Status"
            ) as response:
                if response.status_code != 200:
                    self.environment.runner.logger.error(
                        f"Workflow - Check customization status failed: {response.status_code}"
                    )
                    return
                
                result = response.json()
                status = result.get("status")
                
                if status == "completed":
                    break
                elif status == "failed":
                    self.environment.runner.logger.error("Workflow - Customization failed")
                    return
            
            # Wait with exponential backoff
            time.sleep(polling_delay)
            polling_delay = min(polling_delay * 1.5, self.max_polling_delay)
        
        # If timed out
        if time.time() - start_time >= max_wait_time:
            self.environment.runner.logger.warning("Workflow - Customization timed out")
            return
        
        # Get result
        with self.client.get(
            f"/api/resumes/customization/{workflow_customization_id}/result", 
            name="Workflow - Get Result"
        ) as response:
            if response.status_code == 200:
                self.environment.runner.logger.info("Workflow - Completed successfully")
            else:
                self.environment.runner.logger.error(
                    f"Workflow - Get customization result failed: {response.status_code}"
                )
