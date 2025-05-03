"""Centralized error handling middleware for standardized error responses.

This module serves as a compatibility layer after refactoring.
The original large error handler has been split into smaller, focused handlers.
"""
from .error_handlers.error_handler_middleware import ErrorHandlerMiddleware

__all__ = ["ErrorHandlerMiddleware"]
