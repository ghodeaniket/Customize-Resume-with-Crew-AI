"""Document processing module for Resume Customizer."""
from app.infrastructure.document_processor.base import BaseDocumentExtractor
from app.infrastructure.document_processor.pdf_extractor import PDFExtractor
from app.infrastructure.document_processor.docx_extractor import DOCXExtractor
from app.infrastructure.document_processor.txt_extractor import TXTExtractor
from app.infrastructure.document_processor.factory import DocumentExtractorFactory
from app.infrastructure.document_processor.cache import DocumentCache, InMemoryDocumentCache

# Import DocumentProcessor for backward compatibility
from app.infrastructure.document_processor.processor import DocumentProcessor

__all__ = [
    'BaseDocumentExtractor',
    'PDFExtractor',
    'DOCXExtractor',
    'TXTExtractor',
    'DocumentExtractorFactory',
    'DocumentProcessor',
    'DocumentCache',
    'InMemoryDocumentCache',
]
