"""Document processing infrastructure for Resume Customizer (Backward Compatibility Layer)."""
from app.infrastructure.document_processor.processor import DocumentProcessor
from app.infrastructure.document_processor.factory import DocumentExtractorFactory
from app.infrastructure.document_processor.cache import DocumentCache, InMemoryDocumentCache

# Export the DocumentProcessor class for backward compatibility
__all__ = ['DocumentProcessor']

# Create a module-level instance of DocumentProcessor for importing
# This maintains backward compatibility with the original implementation
document_processor = DocumentProcessor()

# Re-export document_extraction_cache as a function for backward compatibility
def document_extraction_cache(extraction_func):
    """
    Deprecated: This function is maintained for backward compatibility.
    Please use app.infrastructure.document_processor.cache.cached_extraction instead.
    """
    import functools
    import warnings
    
    warnings.warn(
        "document_extraction_cache is deprecated. "
        "Please use app.infrastructure.document_processor.cache.cached_extraction instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    @functools.wraps(extraction_func)
    def wrapper(*args, **kwargs):
        return extraction_func(*args, **kwargs)
    
    return wrapper


# Re-export DocumentBuilder for backward compatibility
class DocumentBuilder:
    """
    Builder for creating documents in various formats.
    
    Deprecated: This class is maintained for backward compatibility.
    Please use app.infrastructure.document_builder.DocumentBuilder instead.
    """
    
    def __init__(self):
        """Initialize document builder."""
        import warnings
        
        warnings.warn(
            "DocumentBuilder in document_processor.py is deprecated. "
            "Please use app.infrastructure.document_builder.DocumentBuilder instead.",
            DeprecationWarning,
            stacklevel=2
        )
    
    def create_markdown(self, sections):
        """Create a markdown document from sections."""
        markdown = ""
        for title, content in sections:
            markdown += f"## {title}\n\n{content}\n\n"
        
        return markdown.strip()
