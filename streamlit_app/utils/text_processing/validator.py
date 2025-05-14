"""
Job description validation utilities.

This module provides functions to validate job description text
to ensure it meets the requirements for API submission.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
import logging
from .sanitizer import test_json_serialization

# Set up logger
logger = logging.getLogger(__name__)

# Validation constants
MIN_DESCRIPTION_LENGTH = 50
MAX_DESCRIPTION_LENGTH = 10000
RECOMMENDED_MIN_LENGTH = 200

def validate_job_description(text: str) -> Dict[str, Any]:
    """
    Validate a job description for API submission.
    
    Args:
        text: The job description text to validate
        
    Returns:
        dict: Validation results with status and any warnings/errors
    """
    if not text:
        return {
            "is_valid": False,
            "errors": ["Job description cannot be empty."],
            "warnings": [],
            "suggestions": ["Please paste a job description."]
        }
    
    errors = []
    warnings = []
    suggestions = []
    
    # Check length
    text_length = len(text)
    if text_length < MIN_DESCRIPTION_LENGTH:
        errors.append(f"Job description is too short ({text_length} characters). Minimum is {MIN_DESCRIPTION_LENGTH}.")
        suggestions.append("Please provide a more detailed job description.")
    elif text_length < RECOMMENDED_MIN_LENGTH:
        warnings.append(f"Job description is quite short ({text_length} characters). Recommended minimum is {RECOMMENDED_MIN_LENGTH}.")
        suggestions.append("A more detailed job description will yield better results.")
    elif text_length > MAX_DESCRIPTION_LENGTH:
        errors.append(f"Job description is too long ({text_length} characters). Maximum is {MAX_DESCRIPTION_LENGTH}.")
        suggestions.append(f"Please reduce the job description to {MAX_DESCRIPTION_LENGTH} characters or less.")
    
    # Check for unusual character distributions
    if contains_unusual_character_distribution(text):
        warnings.append("Job description contains an unusual distribution of characters.")
        suggestions.append("Check for encoding issues or remove special characters.")
    
    # Check for missing key sections
    required_sections = check_required_sections(text)
    if required_sections["missing"]:
        warnings.append(f"Job description may be missing key sections: {', '.join(required_sections['missing'])}.")
        suggestions.append("Consider adding the missing sections for better results.")
    
    # Test JSON serialization
    json_test = test_json_serialization(text)
    if not json_test["is_valid"]:
        errors.append(f"Job description contains characters that may cause JSON parsing issues: {json_test['error']}")
        suggestions.append("The text will be automatically processed to fix these issues.")
    
    # Determine overall validity
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions,
        "character_count": text_length
    }

def contains_unusual_character_distribution(text: str) -> bool:
    """
    Check if text contains an unusual distribution of characters.
    
    Args:
        text: The text to check
        
    Returns:
        bool: True if unusual character distribution detected
    """
    if not text:
        return False
    
    # Check for excessive special characters
    special_char_count = len(re.findall(r'[^\w\s]', text))
    special_char_ratio = special_char_count / len(text)
    
    # Check for excessive uppercase
    uppercase_count = len(re.findall(r'[A-Z]', text))
    uppercase_ratio = uppercase_count / len(text)
    
    return special_char_ratio > 0.3 or uppercase_ratio > 0.5

def check_required_sections(text: str) -> Dict[str, List[str]]:
    """
    Check if the job description contains commonly required sections.
    
    Args:
        text: The job description text
        
    Returns:
        dict: Dictionary with present and missing sections
    """
    # Common section keywords to look for
    sections = {
        "responsibilities": ["responsibilities", "duties", "what you'll do", "what you will do", "job duties"],
        "requirements": ["requirements", "qualifications", "skills", "what you need", "what we're looking for"],
        "company_info": ["about us", "company", "our team", "who we are"],
        "benefits": ["benefits", "perks", "what we offer", "compensation"]
    }
    
    present = []
    missing = []
    
    # Check each section type
    for section_type, keywords in sections.items():
        found = False
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text.lower()):
                found = True
                break
        
        if found:
            present.append(section_type)
        else:
            missing.append(section_type)
    
    return {"present": present, "missing": missing}
