"""Configuration settings for the Resume Customizer Streamlit application."""
import os

# API configuration
API_CONFIG = {
    "base_url": os.environ.get("RESUME_CUSTOMIZER_API_URL", "http://localhost:8000"),
    "timeout": float(os.environ.get("RESUME_CUSTOMIZER_API_TIMEOUT", "30.0")),
    "retry_count": int(os.environ.get("RESUME_CUSTOMIZER_API_RETRY_COUNT", "3")),
}

# File validation settings
FILE_VALIDATION = {
    "max_file_size": 10 * 1024 * 1024,  # 10 MB
    "allowed_extensions": [".pdf", ".docx", ".txt"],
}

# Application settings
APP_CONFIG = {
    "title": "Resume Customizer",
    "app_icon": "📄",
    "primary_color": "#4263eb",
    "secondary_color": "#74c0fc",
    "error_color": "#f03e3e",
    "success_color": "#37b24d",
}

# Status polling settings
POLLING_CONFIG = {
    "initial_interval": 2.0,  # seconds
    "max_interval": 10.0,  # seconds
    "backoff_factor": 1.5,
    "auto_refresh_default": True,
}
