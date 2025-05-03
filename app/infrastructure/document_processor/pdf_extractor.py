"""PDF document extraction implementation.

This module serves as a compatibility layer after refactoring.
The original large PDF extractor has been split into smaller, focused extractors.
"""
from .pdf.main_extractor import PDFExtractor
from .pdf.pymupdf_extractor import lazy_import_pymupdf

__all__ = ["PDFExtractor", "lazy_import_pymupdf"]
