#!/usr/bin/env python3
"""
API Contract Documentation Generator

This script generates comprehensive documentation for the Resume Customizer API contracts.
It produces a Markdown document describing all API endpoints, their request and response models,
and includes examples and compatibility information.
"""
import json
import sys
from pathlib import Path

from tests.contract.api_contracts import (
    HealthResponse,
    ResumeUploadResponse,
    TaskStatusResponse,
    ResumeTextResponse,
    CustomizationRequest,
    CustomizationResponse,
    CustomizationResultResponse,
    ErrorResponse
)
from tests.contract.contract_helpers import document_contract_details


def generate_contract_documentation():
    """Generate the contract documentation."""
    # Define output path
    docs_dir = Path(__file__).parent.parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    output_file = docs_dir / "api_contracts.md"
    
    # Define the model classes and corresponding endpoint information
    endpoint_models = [
        {
            "endpoint": "GET /api/health",
            "description": "Check API health status",
            "response_model": HealthResponse,
            "response_example": {"status": "ok"}
        },
        {
            "endpoint": "POST /api/resumes/upload",
            "description": "Upload a resume for processing",
            "response_model": ResumeUploadResponse,
            "response_example": {
                "task_id": "79bfc09f-ce85-4b01-8ef3-5ba99b398755",
                "filename": "john_doe_resume.pdf",
                "status": "processing"
            }
        },
        {
            "endpoint": "GET /api/resumes/{task_id}",
            "description": "Get the status of a resume processing task",
            "response_model": TaskStatusResponse,
            "response_example": {
                "task_id": "79bfc09f-ce85-4b01-8ef3-5ba99b398755",
                "status": "completed",
                "progress": 100.0,
                "created_at": "2025-04-30T12:00:00Z",
                "updated_at": "2025-04-30T12:01:00Z",
                "result_url": "/api/resumes/79bfc09f-ce85-4b01-8ef3-5ba99b398755/download"
            }
        },
        {
            "endpoint": "GET /api/resumes/{task_id}/text",
            "description": "Get the extracted text from a processed resume",
            "response_model": ResumeTextResponse,
            "response_example": {
                "task_id": "79bfc09f-ce85-4b01-8ef3-5ba99b398755",
                "text": "Sample resume text...",
                "metadata": {
                    "filename": "john_doe_resume.pdf",
                    "created_at": "2025-04-30T12:00:00Z",
                    "updated_at": "2025-04-30T12:01:00Z"
                }
            }
        },
        {
            "endpoint": "POST /api/resumes/customize",
            "description": "Customize a resume based on a job description",
            "request_model": CustomizationRequest,
            "request_example": {
                "resume_id": "79bfc09f-ce85-4b01-8ef3-5ba99b398755",
                "job_description": "We are looking for a Python developer with FastAPI experience...",
                "customize_level": "standard"
            },
            "response_model": CustomizationResponse,
            "response_example": {
                "task_id": "53ad05ce-0a3b-4d5e-a01d-a0771de31df9",
                "status": "processing"
            }
        },
        {
            "endpoint": "GET /api/resumes/customization/{task_id}",
            "description": "Get the status of a customization task",
            "response_model": TaskStatusResponse,
            "response_example": {
                "task_id": "53ad05ce-0a3b-4d5e-a01d-a0771de31df9",
                "status": "completed",
                "progress": 100.0,
                "created_at": "2025-04-30T12:00:00Z",
                "updated_at": "2025-04-30T12:01:00Z",
                "result_url": "/api/resumes/customization/53ad05ce-0a3b-4d5e-a01d-a0771de31df9/result"
            }
        },
        {
            "endpoint": "GET /api/resumes/customization/{task_id}/result",
            "description": "Get the customized resume result",
            "response_model": CustomizationResultResponse,
            "response_example": {
                "task_id": "53ad05ce-0a3b-4d5e-a01d-a0771de31df9",
                "status": "completed",
                "result": "Customized resume text...",
                "metadata": {
                    "processing_time_ms": 15678.90,
                    "customize_level": "standard",
                    "completion_time": 1719759382.45
                }
            }
        },
        {
            "endpoint": "Error Response",
            "description": "Standard error response format",
            "response_model": ErrorResponse,
            "response_example": {
                "detail": "Error message describing what went wrong"
            }
        }
    ]
    
    # Generate documentation
    with open(output_file, "w") as f:
        f.write("# Resume Customizer API Contracts\n\n")
        f.write("This document describes the API contracts for the Resume Customizer application.\n")
        f.write("These contracts ensure API stability and backward compatibility.\n\n")
        
        f.write("## Table of Contents\n\n")
        for endpoint_info in endpoint_models:
            anchor = endpoint_info["endpoint"].lower().replace("/", "").replace("{", "").replace("}", "").replace(" ", "-")
            f.write(f"- [{endpoint_info['endpoint']}](#{anchor})\n")
        f.write("\n")
        
        for endpoint_info in endpoint_models:
            f.write(f"## {endpoint_info['endpoint']}\n\n")
            f.write(f"{endpoint_info['description']}\n\n")
            
            if "request_model" in endpoint_info:
                request_details = document_contract_details(endpoint_info["request_model"])
                f.write("### Request\n\n")
                f.write("```json\n")
                f.write(json.dumps(endpoint_info["request_example"], indent=2))
                f.write("\n```\n\n")
                
                f.write("#### Request Fields\n\n")
                f.write("| Field | Type | Required | Description |\n")
                f.write("|-------|------|----------|-------------|\n")
                for field_name, field_info in request_details["fields"].items():
                    required = "Yes" if field_info["required"] else "No"
                    f.write(f"| {field_name} | {field_info['type']} | {required} | {field_info['description']} |\n")
                f.write("\n")
            
            response_details = document_contract_details(endpoint_info["response_model"])
            f.write("### Response\n\n")
            f.write("```json\n")
            f.write(json.dumps(endpoint_info["response_example"], indent=2))
            f.write("\n```\n\n")
            
            f.write("#### Response Fields\n\n")
            f.write("| Field | Type | Required | Description |\n")
            f.write("|-------|------|----------|-------------|\n")
            for field_name, field_info in response_details["fields"].items():
                required = "Yes" if field_info["required"] else "No"
                f.write(f"| {field_name} | {field_info['type']} | {required} | {field_info['description']} |\n")
            f.write("\n")
        
        f.write("## Contract Stability Guarantees\n\n")
        f.write("The Resume Customizer API adheres to the following stability guarantees:\n\n")
        f.write("1. **Field Guarantees**:\n")
        f.write("   - Existing fields will not be removed from responses\n")
        f.write("   - Field types will not change in incompatible ways\n")
        f.write("   - New optional fields may be added to responses\n\n")
        f.write("2. **Endpoint Guarantees**:\n")
        f.write("   - Existing endpoints will not be removed without deprecation notice\n")
        f.write("   - Endpoint URLs will not change without deprecation notice\n")
        f.write("   - HTTP methods for endpoints will not change\n\n")
        f.write("3. **Versioning Strategy**:\n")
        f.write("   - Breaking changes will be introduced in new API versions\n")
        f.write("   - API versioning is implemented through URL prefixes (e.g., `/api/v2/`)\n")
        f.write("   - Older API versions remain supported for a defined deprecation period\n\n")
        
    print(f"Contract documentation generated at: {output_file}")
    return str(output_file)


if __name__ == "__main__":
    generate_contract_documentation()
