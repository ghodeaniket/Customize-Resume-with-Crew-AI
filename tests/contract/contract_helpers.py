"""
Helper functions for API contract testing.

This module provides utilities for validating API responses against the defined contracts.
"""
from typing import Type, Dict, Any, List, Optional, Union
from pydantic import BaseModel, ValidationError


def validate_response(
    response_data: Dict[str, Any], 
    model_class: Type[BaseModel],
    context: str = ""
) -> Union[bool, Dict[str, Any]]:
    """
    Validate a response against a Pydantic model.
    
    Args:
        response_data: The response data to validate
        model_class: The Pydantic model class to validate against
        context: Optional context information for error messages
        
    Returns:
        bool: True if validation passed
        
    Raises:
        AssertionError: If validation fails
    """
    try:
        validated_data = model_class(**response_data)
        return validated_data.model_dump()
    except ValidationError as e:
        context_info = f" [{context}]" if context else ""
        error_message = f"Response validation failed{context_info}: {e}"
        raise AssertionError(error_message)


def assert_contract_compatibility(
    old_format: Dict[str, Any],
    current_response: Dict[str, Any],
    context: str = ""
) -> bool:
    """
    Assert that the current response is backward compatible with the old format.
    
    Args:
        old_format: The old response format
        current_response: The current response data
        context: Optional context information for error messages
        
    Returns:
        bool: True if compatible
        
    Raises:
        AssertionError: If compatibility check fails
    """
    context_info = f" [{context}]" if context else ""
    
    for key in old_format:
        if key not in current_response:
            raise AssertionError(
                f"Backward compatibility broken{context_info}: "
                f"Field '{key}' missing from current response"
            )
    
    return True


def verify_error_response(
    error_data: Dict[str, Any],
    expected_message: Optional[str] = None
) -> bool:
    """
    Verify that an error response matches the expected format.
    
    Args:
        error_data: The error response data
        expected_message: Optional specific error message to check for
        
    Returns:
        bool: True if verification passed
        
    Raises:
        AssertionError: If verification fails
    """
    # Check basic error structure
    if "detail" not in error_data:
        raise AssertionError("Error response missing 'detail' field")
    
    # Check specific error message if provided
    if expected_message and expected_message.lower() not in error_data["detail"].lower():
        raise AssertionError(
            f"Error message mismatch: Expected '{expected_message}' to be in '{error_data['detail']}'"
        )
    
    return True


def document_contract_details(model_class: Type[BaseModel]) -> Dict[str, Any]:
    """
    Generate documentation details for a contract model.
    
    Args:
        model_class: The Pydantic model class
        
    Returns:
        Dict: Documentation details including fields and examples
    """
    schema = model_class.model_json_schema()
    
    # Extract field information
    fields = {}
    for field_name, field_info in schema.get("properties", {}).items():
        fields[field_name] = {
            "type": field_info.get("type", "unknown"),
            "description": field_info.get("description", ""),
            "required": field_name in schema.get("required", [])
        }
    
    # Generate a simple example
    example = {}
    for field_name, field_info in fields.items():
        if field_info["type"] == "string":
            example[field_name] = f"sample_{field_name}"
        elif field_info["type"] == "number" or field_info["type"] == "integer":
            example[field_name] = 42
        elif field_info["type"] == "boolean":
            example[field_name] = True
        elif field_info["type"] == "object":
            example[field_name] = {"key": "value"}
        elif field_info["type"] == "array":
            example[field_name] = ["item1", "item2"]
        else:
            example[field_name] = None
    
    return {
        "name": model_class.__name__,
        "description": schema.get("description", ""),
        "fields": fields,
        "example": example
    }
