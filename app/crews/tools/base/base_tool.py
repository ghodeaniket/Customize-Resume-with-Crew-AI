"""Base tool implementation with common functionality.

This module provides a base tool class with common functionality
shared by all Resume Customizer tools.
"""
from typing import Dict, Any, Optional
import time
import functools

from crewai.tools import tool
from pydantic import BaseModel, Field, ConfigDict

from app.core.logging import logger


class BaseResumeTool:
    """Base class for Resume Customizer tools.
    
    This class provides common functionality for all tools including:
    - Error handling
    - Logging
    - Caching
    - Performance monitoring
    """
    
    def __init__(self, name: str, description: str, cache_enabled: bool = True):
        """Initialize the base tool.
        
        Args:
            name: Name of the tool
            description: Description of the tool's functionality
            cache_enabled: Whether to enable caching for this tool
        """
        self.name = name
        self.description = description
        self.cache_enabled = cache_enabled
        self._cache = {}
        
        logger.info(f"Initialized {name} tool")
    
    def _cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            str: Cache key
        """
        # Simple cache key generation
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return "|".join(key_parts)
    
    def clear_cache(self) -> None:
        """Clear the tool's cache."""
        self._cache.clear()
        logger.info(f"Cleared cache for {self.name} tool")
    
    def with_cache(self, func):
        """Decorator for caching tool results.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function with caching
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.cache_enabled:
                return func(*args, **kwargs)
            
            cache_key = self._cache_key(*args, **kwargs)
            
            # Check cache
            if cache_key in self._cache:
                logger.debug(f"Cache hit for {self.name} tool")
                return self._cache[cache_key]
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            self._cache[cache_key] = result
            logger.debug(f"Cached result for {self.name} tool")
            
            return result
        
        return wrapper
    
    def with_error_handling(self, func):
        """Decorator for standardized error handling.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function with error handling
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {self.name} tool: {str(e)}", exc_info=True)
                return {"error": f"Error in {self.name}: {str(e)}"}
        
        return wrapper
    
    def with_performance_monitoring(self, func):
        """Decorator for monitoring tool performance.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function with performance monitoring
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                # Add performance metrics to result if it's a dict
                if isinstance(result, dict):
                    result["_performance"] = {
                        "execution_time_ms": (time.time() - start_time) * 1000
                    }
                
                return result
            finally:
                execution_time = (time.time() - start_time) * 1000
                logger.info(f"{self.name} tool executed in {execution_time:.2f}ms")
        
        return wrapper


class ToolRegistry:
    """Registry for managing tool instances."""
    
    _instance = None
    _tools = {}
    
    def __new__(cls):
        """Singleton pattern for tool registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, name: str, tool_instance: Any) -> None:
        """Register a tool.
        
        Args:
            name: Tool name
            tool_instance: Tool instance
        """
        cls._tools[name] = tool_instance
        logger.info(f"Registered tool: {name}")
    
    @classmethod
    def get(cls, name: str) -> Optional[Any]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Optional[Any]: Tool instance if found
        """
        return cls._tools.get(name)
    
    @classmethod
    def list_tools(cls) -> Dict[str, Any]:
        """List all registered tools.
        
        Returns:
            Dict[str, Any]: Dictionary of tool names and instances
        """
        return cls._tools.copy()
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools."""
        cls._tools.clear()
        logger.info("Cleared tool registry")
