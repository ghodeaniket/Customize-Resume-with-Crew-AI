"""PDF extraction module."""
from .main_extractor import PDFExtractor
from .pymupdf_extractor import lazy_import_pymupdf

__all__ = ["PDFExtractor", "lazy_import_pymupdf"]
