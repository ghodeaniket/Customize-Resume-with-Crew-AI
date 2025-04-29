#!/usr/bin/env python3
"""
Resume Customizer Server Launcher
--------------------------------
This script starts the Resume Customizer backend server and provides
information about the available endpoints for testing.
"""
import os
import sys
import importlib
import webbrowser
from pathlib import Path

# Define package names and their pip install names (if different)
REQUIRED_PACKAGES = {
    "uvicorn": "uvicorn",
    "fastapi": "fastapi",
    "pydantic": "pydantic",
    "docx": "python-docx",
    "PyPDF2": "PyPDF2", 
    "fitz": "pymupdf",
    "loguru": "loguru",
    "aiofiles": "aiofiles",
    "crewai": "crewai",
    "crewai_tools": "crewai-tools"
}

missing_packages = []
for package_name, pip_name in REQUIRED_PACKAGES.items():
    try:
        importlib.import_module(package_name)
    except ImportError:
        missing_packages.append((package_name, pip_name))

if missing_packages:
    print("\n" + "!" * 80)
    print("MISSING DEPENDENCIES DETECTED".center(80))
    print("!" * 80)
    print("\nThe following required packages are missing:")
    for pkg_name, pip_name in missing_packages:
        print(f"  - {pkg_name}")
    
    # Ask user if they want to install automatically
    print("\nWould you like to install the missing dependencies automatically? (y/n)")
    response = input("> ").strip().lower()
    
    if response in ('y', 'yes'):
        print("\nInstalling missing dependencies...")
        import subprocess
        import sys
        
        # Determine pip command based on platform
        pip_cmd = "pip3" if sys.platform != "win32" else "pip"
        
        # Install each missing package
        for _, pip_name in missing_packages:
            print(f"Installing {pip_name}...")
            try:
                subprocess.check_call([pip_cmd, "install", pip_name])
                print(f"Successfully installed {pip_name}")
            except subprocess.CalledProcessError:
                print(f"Failed to install {pip_name}. Please install it manually.")
                print(f"Run: {pip_cmd} install {pip_name}")
                sys.exit(1)
        
        print("\nAll dependencies installed successfully!")
    else:
        print("\nPlease install the required dependencies manually using:")
        print("\npip install -r requirements.txt")
        print("\nor install them individually:")
        pip_packages = [pip_name for _, pip_name in missing_packages]
        print(f"\npip install {' '.join(pip_packages)}")
        print("\n" + "!" * 80 + "\n")
        sys.exit(1)

# Now all packages should be available
import uvicorn

# Create required directories if they don't exist
uploads_dir = Path("uploads")
logs_dir = Path("logs")
uploads_dir.mkdir(exist_ok=True)
logs_dir.mkdir(exist_ok=True)

# Print welcome banner
print("\n" + "=" * 80)
print("RESUME CUSTOMIZER BACKEND - DEVELOPMENT SERVER".center(80))
print("=" * 80)
print("\nStarting server...")

# Default port for instructions (will be updated if we use a different port)
port = 8000

# Print test instructions
print("\nAvailable endpoints for testing:")
print("-------------------------------")
print(f"1. Health Check:")
print(f"   GET http://127.0.0.1:{port}/health")
print(f"   curl -X GET http://127.0.0.1:{port}/health")
print(f"\n2. Upload Resume:")
print(f"   POST http://127.0.0.1:{port}/api/resumes/upload")
print(f"   curl -X POST -F \"resume=@test_data/test_resume.txt\" http://127.0.0.1:{port}/api/resumes/upload")
print(f"\n3. Check Status (replace TASK_ID with the ID from upload response):")
print(f"   GET http://127.0.0.1:{port}/api/resumes/TASK_ID")
print(f"   curl -X GET http://127.0.0.1:{port}/api/resumes/TASK_ID")
print(f"\n4. Get Extracted Text:")
print(f"   GET http://127.0.0.1:{port}/api/resumes/TASK_ID/text")
print(f"   curl -X GET http://127.0.0.1:{port}/api/resumes/TASK_ID/text")
print(f"\nAPI Documentation available at: http://127.0.0.1:{port}/docs")
print("=" * 80 + "\n")

# Process command line arguments
open_docs = "--open-docs" in sys.argv

# Check for custom port
custom_port = None
for arg in sys.argv:
    if arg.startswith("--port="):
        try:
            custom_port = int(arg.split("=")[1])
            print(f"Using custom port: {custom_port}")
        except (ValueError, IndexError):
            print("Invalid port format. Using default port.")

# Run the server
if __name__ == "__main__":
    # Use custom port if specified, otherwise use default
    port = custom_port if custom_port is not None else 8000
    max_port = port + 10 if custom_port is not None else 8010  # Try port range
    
    # Try to find an available port
    while port <= max_port:
        try:
            print(f"Attempting to start server on port {port}...")
            # Update the API documentation URLs based on the port
            if port != 8000:
                print(f"\nNOTE: Using alternative port {port} because port 8000 is busy.")
                print(f"API Documentation available at: http://127.0.0.1:{port}/docs")
                print("=" * 80 + "\n")
            
            # Open docs in browser if requested
            if open_docs:
                print("Opening API documentation in web browser...")
                webbrowser.open(f"http://127.0.0.1:{port}/docs")
            
            uvicorn.run(
                "main:app",
                host="127.0.0.1",
                port=port,
                reload=True,
                log_level="info"
            )
            break
        except OSError:
            print(f"Port {port} is busy, trying next port...")
            port += 1
    
    if port > max_port:
        print("ERROR: Could not find an available port in range 8000-8010.")
        print("\nTroubleshooting tips:")
        print("1. Close any existing FastAPI/Uvicorn instances")
        print("2. Find and kill the process using port 8000:")
        print("   - On macOS/Linux: lsof -i :8000")
        print("   - On Windows: netstat -ano | findstr :8000")
        print("3. Or manually specify a different port:")
        print("   python3 start_server.py --port 8080")
        sys.exit(1)
