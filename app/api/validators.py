"""Custom validators for API requests."""
from fastapi import UploadFile, HTTPException


def validate_resume_file(file: UploadFile) -> bool:
    """Validate that the uploaded file is a supported resume format."""
    allowed_extensions = [".pdf", ".docx"]
    file_ext = file.filename.lower().split(".")[-1]
    
    if f".{file_ext}" not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Please upload one of: {', '.join(allowed_extensions)}"
        )
    
    return True
