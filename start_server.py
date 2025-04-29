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

# Check required dependencies
REQUIRED_PACKAGES = [
    "uvicorn", "fastapi", "pydantic", "docx", "PyPDF2", "fitz", 
    "loguru", "aiofiles", "crewai", "crewai_tools"
]

missing_packages = []
for package in REQUIRED_PACKAGES:
    try:
        importlib.import_module(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print("\n" + "!" * 80)
    print("MISSING DEPENDENCIES".center(80))
    print("!" * 80)
    print("\nThe following required packages are missing:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    print("\nPlease install the required dependencies using:")
    print("\npip install -r requirements.txt")
    print("\nor install them individually:")
    print(f"\npip install {' '.join(missing_packages)}")
    print("\n" + "!" * 80 + "\n")
    sys.exit(1)

# Import uvicorn after checking dependencies
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
