"""Base extractor compatibility module.

This module serves as a compatibility layer after refactoring,
providing backward compatibility for imports.
"""
from app.infrastructure.document_processor.base_extractor import BaseDocumentExtractor

# Maintained for backward compatibility
__all__ = ['BaseDocumentExtractor']
