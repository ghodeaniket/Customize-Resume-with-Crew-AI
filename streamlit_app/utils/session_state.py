"""Session state management utilities."""
import streamlit as st

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
    
    # API configuration
    if "api_config" not in st.session_state:
        st.session_state.api_config = {
            "base_url": "http://localhost:8000",
            "timeout": 10,  # seconds
            "retry_count": 3,
        }
