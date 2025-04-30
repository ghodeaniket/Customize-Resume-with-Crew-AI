"""Validate the environment for the Resume Customizer application."""
import os
import sys
import json
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are installed."""
    required_packages = [
        "fastapi", 
        "uvicorn", 
        "pydantic", 
        "crewai", 
        "crewai-tools", 
        "PyPDF2", 
        "pymupdf", 
        "python-docx",
        "loguru"
    ]
    
    results = {}
    
    for package in required_packages:
        try:
            __import__(package)
            results[package] = True
            logger.info(f"✅ Package {package} is installed")
        except ImportError:
            results[package] = False
            logger.error(f"❌ Package {package} is missing")
    
    return results

def check_api_keys() -> Dict[str, bool]:
    """Check if required API keys are set."""
    # Use settings if available
    try:
        from app.core.config import settings
        
        openai_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        llm_key = os.environ.get("LLM_API_KEY") or settings.LLM_API_KEY
        
        has_openai_key = bool(openai_key)
        has_llm_key = bool(llm_key)
        has_any_key = has_openai_key or has_llm_key
        
        if has_openai_key:
            logger.info("✅ OPENAI_API_KEY is set")
        else:
            logger.warning("❌ OPENAI_API_KEY is not set")
            
        if has_llm_key:
            logger.info("✅ LLM_API_KEY is set")
        else:
            logger.warning("❌ LLM_API_KEY is not set")
            
        return {
            "has_openai_key": has_openai_key,
            "has_llm_key": has_llm_key,
            "has_any_key": has_any_key
        }
    except ImportError:
        # Fall back to environment variables only
        has_openai_key = bool(os.environ.get("OPENAI_API_KEY"))
        has_llm_key = bool(os.environ.get("LLM_API_KEY"))
        has_any_key = has_openai_key or has_llm_key
        
        if has_openai_key:
            logger.info("✅ OPENAI_API_KEY is set in environment")
        else:
            logger.warning("❌ OPENAI_API_KEY is not set in environment")
            
        if has_llm_key:
            logger.info("✅ LLM_API_KEY is set in environment")
        else:
            logger.warning("❌ LLM_API_KEY is not set in environment")
            
        return {
            "has_openai_key": has_openai_key,
            "has_llm_key": has_llm_key,
            "has_any_key": has_any_key
        }

def check_directory_structure() -> Dict[str, bool]:
    """Check if required directories exist."""
    required_dirs = [
        "app",
        "app/api",
        "app/core",
        "app/crews",
        "app/infrastructure",
        "app/models",
        "app/services",
        "uploads"
    ]
    
    results = {}
    
    for directory in required_dirs:
        exists = os.path.isdir(directory)
        results[directory] = exists
        
        if exists:
            logger.info(f"✅ Directory {directory} exists")
        else:
            logger.warning(f"❌ Directory {directory} does not exist")
    
    return results

def test_crewai_import() -> bool:
    """Test if CrewAI can be imported."""
    try:
        from crewai import Agent, Task, Crew
        logger.info("✅ CrewAI components imported successfully")
        return True
    except ImportError as e:
        logger.error(f"❌ Error importing CrewAI: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error importing CrewAI: {str(e)}")
        return False

def validate_environment() -> Dict[str, Any]:
    """Run full environment validation."""
    logger.info("Starting environment validation...")
    
    results = {
        "dependencies": check_dependencies(),
        "api_keys": check_api_keys(),
        "directories": check_directory_structure(),
        "crewai_import": test_crewai_import(),
        "python_version": sys.version,
        "environment_variables": {k: "[SET]" if v else "[NOT SET]" for k, v in {
            "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
            "LLM_API_KEY": bool(os.environ.get("LLM_API_KEY")),
            "AGENT_LLM": bool(os.environ.get("AGENT_LLM")),
            "AGENT_VERBOSE": bool(os.environ.get("AGENT_VERBOSE")),
            "CREW_VERBOSE": bool(os.environ.get("CREW_VERBOSE")),
        }.items()}
    }
    
    # Calculate overall validation status
    dependencies_ok = all(results["dependencies"].values())
    any_api_key = results["api_keys"].get("has_any_key", False)
    directories_ok = all(results["directories"].values())
    crewai_ok = results["crewai_import"]
    
    results["validation_passed"] = dependencies_ok and any_api_key and directories_ok and crewai_ok
    
    # Print summary
    logger.info("Environment validation summary:")
    logger.info(f"Dependencies: {'✅ OK' if dependencies_ok else '❌ FAILED'}")
    logger.info(f"API Keys: {'✅ OK' if any_api_key else '❌ FAILED'}")
    logger.info(f"Directories: {'✅ OK' if directories_ok else '❌ FAILED'}")
    logger.info(f"CrewAI Import: {'✅ OK' if crewai_ok else '❌ FAILED'}")
    logger.info(f"Overall: {'✅ PASSED' if results['validation_passed'] else '❌ FAILED'}")
    
    return results

if __name__ == "__main__":
    results = validate_environment()
    
    # Output JSON results if requested
    if "--json" in sys.argv:
        print(json.dumps(results, indent=2))
    
    # Set exit code based on validation result
    sys.exit(0 if results["validation_passed"] else 1)
