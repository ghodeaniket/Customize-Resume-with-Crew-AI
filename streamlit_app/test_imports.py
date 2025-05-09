"""
Test imports for the Resume Customizer application.

This script tests that all required imports are working properly.
"""

try:
    import streamlit as st
    print("✅ Successfully imported streamlit")
    
    from components.header import render_header
    print("✅ Successfully imported render_header")
    
    from components.upload_section import render_upload_section
    print("✅ Successfully imported render_upload_section")
    
    from components.status_section import render_status_section
    print("✅ Successfully imported render_status_section")
    
    from components.job_description_section import render_job_description_section
    print("✅ Successfully imported render_job_description_section")
    
    from components.customization_options import render_customization_options
    print("✅ Successfully imported render_customization_options")
    
    from components.customization_request_section import render_customization_request_section
    print("✅ Successfully imported render_customization_request_section")
    
    from components.customization_status_section import render_customization_status_section
    print("✅ Successfully imported render_customization_status_section")
    
    from components.results_section import render_results_section
    print("✅ Successfully imported render_results_section")
    
    from utils.session_state import initialize_session_state
    print("✅ Successfully imported initialize_session_state")
    
    from utils.error_handling import show_error_message
    print("✅ Successfully imported show_error_message")
    
    from utils.job_models import CustomizationRequest
    print("✅ Successfully imported CustomizationRequest")
    
    from utils.resume_models import ResumeUploadResponse
    print("✅ Successfully imported ResumeUploadResponse")
    
    from services.api_service import get_api_url
    print("✅ Successfully imported get_api_url")
    
    from services.job_description_service import submit_customization
    print("✅ Successfully imported submit_customization")
    
    print("\n🎉 All imports successful! The application should run properly.")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please check the module path and ensure all dependencies are installed.")
