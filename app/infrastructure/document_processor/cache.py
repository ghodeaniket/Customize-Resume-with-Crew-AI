"""Caching functionality for document extraction."""
import abc
import time
import hashlib
from typing import Optional, Tuple, Dict, Any
import asyncio
import functools

from app.core.logging import logger


class DocumentCache(abc.ABC):
    """Abstract base class for document caching."""
    
    @abc.abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """Get cached document text by key.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[str]: Cached text or None if not found
        """
        pass
    
    @abc.abstractmethod
    async def set(self, key: str, text: str, ttl_seconds: Optional[int] = None) -> None:
        """Set cached document text.
        
        Args:
            key: Cache key
            text: Document text to cache
            ttl_seconds: Time-to-live in seconds (optional)
        """
        pass
    
    @abc.abstractmethod
    async def invalidate(self, key: str) -> None:
        """Invalidate cached document text.
        
        Args:
            key: Cache key
        """
        pass
    
    @abc.abstractmethod
    async def clear(self) -> None:
        """Clear all cached documents."""
        pass


class InMemoryDocumentCache(DocumentCache):
    """In-memory implementation of document cache."""
    
    def __init__(self, max_size: int = 16, ttl_seconds: int = 3600):
        """Initialize in-memory document cache.
        
        Args:
            max_size: Maximum number of documents to cache
            ttl_seconds: Default time-to-live in seconds
        """
        self._cache: Dict[str, Tuple[float, str]] = {}
        self._max_size = max_size
        self._default_ttl = ttl_seconds
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[str]:
        """Get cached document text by key.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[str]: Cached text or None if not found/expired
        """
        if key not in self._cache:
            logger.debug(f"Cache miss for key {key}")
            return None
        
        timestamp, text = self._cache[key]
        
        # Check if expired
        if time.time() - timestamp > self._default_ttl:
            logger.debug(f"Cache entry expired for key {key}")
            async with self._lock:
                if key in self._cache:  # Check again under lock
                    del self._cache[key]
            return None
        
        logger.debug(f"Cache hit for key {key}")
        return text
    
    async def set(self, key: str, text: str, ttl_seconds: Optional[int] = None) -> None:
        """Set cached document text.
        
        Args:
            key: Cache key
            text: Document text to cache
            ttl_seconds: Time-to-live in seconds (optional)
        """
        async with self._lock:
            # Add with current timestamp
            self._cache[key] = (time.time(), text)
            
            # Prune cache if it grows too large
            if len(self._cache) > self._max_size:
                # Remove the oldest entries
                sorted_keys = sorted(self._cache.keys(), 
                                  key=lambda k: self._cache[k][0])
                for old_key in sorted_keys[:len(self._cache) - self._max_size]:
                    logger.debug(f"Pruning cache entry for key {old_key}")
                    del self._cache[old_key]
    
    async def invalidate(self, key: str) -> None:
        """Invalidate cached document text.
        
        Args:
            key: Cache key
        """
        async with self._lock:
            if key in self._cache:
                logger.debug(f"Invalidating cache for key {key}")
                del self._cache[key]
    
    async def clear(self) -> None:
        """Clear all cached documents."""
        async with self._lock:
            logger.debug(f"Clearing cache with {len(self._cache)} entries")
            self._cache.clear()


def cached_extraction(cache: DocumentCache, ttl_seconds: Optional[int] = None):
    """Decorator for caching document extraction results.
    
    Args:
        cache: Document cache instance
        ttl_seconds: Time-to-live in seconds (optional)
        
    Returns:
        Callable: Decorated async function
    """
    def decorator(extraction_func):
        @functools.wraps(extraction_func)
        async def wrapper(self, content: bytes, *args, **kwargs):
            # Skip caching if disabled
            if not getattr(self, 'cache_enabled', True):
                return await extraction_func(self, content, *args, **kwargs)
            
            # Get cache key from extractor
            if hasattr(self, 'get_cache_key'):
                cache_key = self.get_cache_key(content)
            else:
                # Fallback cache key generation
                content_hash = hashlib.md5(content).hexdigest()
                func_name = extraction_func.__name__
                cache_key = f"{func_name}_{content_hash}"
            
            # Try to get from cache first
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached extraction result for {cache_key}")
                return cached_result
            
            # Not in cache, execute the function
            result = await extraction_func(self, content, *args, **kwargs)
            
            # Cache the result
            await cache.set(cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator
