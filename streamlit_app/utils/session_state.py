"""Session state management utilities."""
import streamlit as st
import uuid
from datetime import datetime

def initialize_session_state():
    """Initialize all required session state variables if they don't exist."""
    
    # Upload state tracking
    if "upload_state" not in st.session_state:
        st.session_state.upload_state = {
            "task_id": None,
            "filename": None,
            "status": None,
            "progress": 0,
            "is_processing": False,
            "error": None,
            "current_file": None,
            "extracted_text": None,
            "auto_refresh": True,
        }
    
    # Job description state tracking
    if "job_description_state" not in st.session_state:
        st.session_state.job_description_state = {
            "raw_text": "",
            "processed_text": "",
            "is_processing": False,
            "is_valid": False,
            "error": None,
            "validation_result": None,
            "last_update": None,
            "keywords": [],
            "saved_descriptions": [],
            "customization_level": "standard",
            "industry": None,
            "customization_task_id": None,
            "customization_status": None,
            "customization_progress": 0,
            "customization_result": None,
            "last_status_check": None,
            "estimated_completion_time": None,
            "customization_processing_time": None,
            "customization_error": None,
            "customization_message": None,
            "customization_view_results": False,
            "step": "input",  # input, preview, submitting, submit, complete
            "auto_preview": True,
            "auto_refresh": True
        }
    
    # Customization options state (Phase 3)
    if "customization_state" not in st.session_state:
        st.session_state.customization_state = {
            "customization_level": "standard",
            "industry": None,
            "subindustry": None,
            "preferences": {
                "emphasize_leadership": False,
                "emphasize_technical_skills": True,
                "emphasize_soft_skills": False,
                "emphasize_achievements": True,
                "emphasize_education": False,
                "emphasize_remote_work": False,
                "academic_focus": False,
                "highlight_certifications": False,
                "career_transition": False,
                "ats_optimization": True
            },
            "custom_preferences": {},
            "custom_instructions": "",
            "keywords_to_include": [],
            "keywords_to_exclude": [],
            "saved_presets": {},
            "active_preset": None,
            "is_submitting": False,
            "error": None
        }
    
    # Navigation state
    if "nav_state" not in st.session_state:
        st.session_state.nav_state = {
            "current_step": 1,  # 1: Resume Upload, 2: Job Description, 3: Results
            "can_proceed": False,
            "steps_completed": [],
        }
    
    # Error tracking state
    if "error_state" not in st.session_state:
        st.session_state.error_state = {
            "last_error": None,
            "error_count": 0,
            "error_ids": [],
            "retry_attempts": {}
        }
    
    # API configuration
    if "api_config" not in st.session_state:
        st.session_state.api_config = {
            "base_url": "http://localhost:8000",
            "timeout": 10,  # seconds
            "retry_count": 3,
        }
