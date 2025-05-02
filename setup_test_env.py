#!/usr/bin/env python3
"""
Setup script for Resume Customizer test environment.
Installs required dependencies and verifies versions.
"""
import subprocess
import sys
import importlib.util
from packaging import version

# Required packages with minimum versions
REQUIRED_PACKAGES = {
    "pytest": "7.4.3",
    "pytest-asyncio": "0.21.1",
    "pytest-cov": "4.1.0",
    "fastapi": "0.104.1",
    "pydantic": "2.4.2",
    "crewai": "0.28.8",  # This should match your project requirements
    "locust": "2.20.0"
}

def check_and_install_package(package_name, min_version):
    """Check if package is installed with correct version, install/update if needed."""
    print(f"Checking {package_name}...")
    
    # Check if package is installed
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        print(f"{package_name} not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", f"{package_name}>={min_version}"], check=True)
        return
        
    # Check version
    try:
        pkg = __import__(package_name)
        pkg_version = getattr(pkg, "__version__", "0.0.0")
        
        if version.parse(pkg_version) < version.parse(min_version):
            print(f"{package_name} version {pkg_version} is older than required {min_version}. Updating...")
            subprocess.run([sys.executable, "-m", "pip", "install", f"{package_name}>={min_version}", "--upgrade"], check=True)
        else:
            print(f"{package_name} version {pkg_version} is compatible.")
    except (AttributeError, ModuleNotFoundError):
        print(f"Could not verify {package_name} version. Installing latest...")
        subprocess.run([sys.executable, "-m", "pip", "install", f"{package_name}>={min_version}", "--upgrade"], check=True)

def setup_environment():
    """Set up the test environment."""
    print("Setting up Resume Customizer test environment...\n")
    
    # Install packaging for version comparison
    try:
        __import__("packaging")
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "packaging"], check=True)
    
    # Check and install required packages
    for package, min_version in REQUIRED_PACKAGES.items():
        check_and_install_package(package, min_version)
    
    # Create test data if needed
    print("\nGenerating test data files...")
    try:
        subprocess.run([sys.executable, "create_test_pdf.py"], check=True)
        subprocess.run([sys.executable, "create_test_docx.py"], check=True)
        print("Test data generated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error generating test data: {e}")
    
    print("\nTest environment setup complete!")

if __name__ == "__main__":
    setup_environment()
