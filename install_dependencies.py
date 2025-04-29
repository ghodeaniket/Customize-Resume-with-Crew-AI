#!/usr/bin/env python3
"""
Resume Customizer Dependency Installer
-------------------------------------
This script installs all required dependencies for the Resume Customizer application.
"""
import sys
import subprocess
import platform
import os

print("\n" + "=" * 80)
print("RESUME CUSTOMIZER - DEPENDENCY INSTALLER".center(80))
print("=" * 80)

# Determine the correct pip command
pip_cmd = "pip"
if platform.system() == "Windows":
    # Check if pip3 exists
    try:
        subprocess.run([pip_cmd, "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pip_cmd = "pip3"
else:
    pip_cmd = "pip3"

# Verify pip is available
try:
    subprocess.run([pip_cmd, "--version"], capture_output=True, check=True)
    print(f"\nUsing {pip_cmd} to install dependencies...")
except (subprocess.CalledProcessError, FileNotFoundError):
    print("\nERROR: pip not found. Please install Python and pip first.")
    print("Visit https://www.python.org/downloads/ for installation instructions.")
    sys.exit(1)

# Install dependencies
print("\nInstalling required dependencies...")
requirements = [
    "fastapi>=0.104.1",
    "uvicorn>=0.24.0",
    "pydantic>=2.4.2",
    "pydantic-settings>=2.0.3",
    "python-multipart>=0.0.6",
    "crewai>=0.28.8",
    "crewai-tools>=0.1.6",
    "PyPDF2>=3.0.0",
    "pymupdf>=1.23.0",
    "python-docx>=0.8.11",
    "loguru>=0.7.2",
    "aiofiles>=23.2.1",
    "httpx>=0.25.1",
    "asyncio>=3.4.3",
]

for req in requirements:
    print(f"Installing {req.split('>=')[0]}...")
    try:
        subprocess.run([pip_cmd, "install", req], check=True)
    except subprocess.CalledProcessError:
        print(f"WARNING: Failed to install {req}")

print("\n" + "=" * 80)
print("INSTALLATION COMPLETE".center(80))
print("=" * 80)
print("\nYou can now start the Resume Customizer server:")
print("  python3 start_server.py")
print("\nOr on Windows:")
print("  python start_server.py")
print("\n" + "=" * 80)
