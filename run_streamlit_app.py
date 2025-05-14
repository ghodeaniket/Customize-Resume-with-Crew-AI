#!/usr/bin/env python
"""
Script to run the Resume Customizer Streamlit application.
This script ensures proper environment setup before launching the app.
"""
import os
import sys
import subprocess

def main():
    """Run the Streamlit application with proper configuration."""
    print("Starting Resume Customizer Streamlit Application...")
    
    # Check if Streamlit is installed
    try:
        import streamlit
        print(f"Streamlit version: {streamlit.__version__}")
    except ImportError:
        print("Streamlit is not installed. Installing required dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "streamlit_app/requirements.txt"])
    
    # Set environment variables if needed
    if "RESUME_CUSTOMIZER_API_URL" not in os.environ:
        os.environ["RESUME_CUSTOMIZER_API_URL"] = "http://localhost:8000"
        print(f"Using default API URL: {os.environ['RESUME_CUSTOMIZER_API_URL']}")
    
    # Launch the Streamlit app
    app_path = os.path.join("streamlit_app", "app.py")
    print(f"Launching Streamlit app: {app_path}")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])

if __name__ == "__main__":
    main()
