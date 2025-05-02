# Document Processor Module

This module provides functionality for extracting text from various document formats (PDF, DOCX, TXT) using a modular approach with the Strategy Pattern.

## Architecture

```
document_processor/
├── __init__.py              # Package exports
├── base.py                  # BaseDocumentExtractor abstract class
├── pdf_extractor.py         # PDF-specific extraction
├── docx_extractor.py        # DOCX-specific extraction
├── txt_extractor.py         # Text file extraction
├── factory.py               # Factory to create appropriate extractor
├── cache.py                 # Caching functionality
└── processor.py             # Main DocumentProcessor (backward compatible)
```

## Key Components

### BaseDocumentExtractor

Abstract base class that defines the common interface for all document extractors:

```python
class BaseDocumentExtractor(abc.ABC):
    @abc.abstractmethod
    async def extract_text(self, content: bytes, filename: Optional[str] = None) -> str:
        """Extract text from document content."""
        pass
```

### Specialized Extractors

- **PDFExtractor**: Handles PDF extraction with PyPDF2 and PyMuPDF (if available)
- **DOCXExtractor**: Handles DOCX extraction using python-docx
- **TXTExtractor**: Handles text file extraction with encoding detection

### DocumentExtractorFactory

Factory class that creates the appropriate extractor based on file type:

```python
factory = DocumentExtractorFactory()
extractor = factory.create_extractor(mime_type, filename)
text = await extractor.extract_text(content, filename)
```

### DocumentCache

Abstract base class for caching with an in-memory implementation:

```python
cache = InMemoryDocumentCache(max_size=16, ttl_seconds=3600)
await cache.set("key", "document text")
text = await cache.get("key")
```

### cached_extraction Decorator

Decorator for adding caching to extraction methods:

```python
@cached_extraction(cache)
async def extract_text(self, content: bytes, filename: Optional[str] = None) -> str:
    # Extraction implementation
```

## Migration Guide

### For Existing Code Using the Old Implementation

The old `DocumentProcessor` class is still available and works with the new implementation under the hood. No changes are required if you're using:

```python
from app.infrastructure.document_processor import DocumentProcessor

processor = DocumentProcessor()
text = await processor.extract_text_from_bytes(content, file_type, filename)
```

### For New Code

Use the new modular components directly:

```python
from app.infrastructure.document_processor import (
    DocumentExtractorFactory, PDFExtractor, DOCXExtractor, TXTExtractor
)
from app.core.utils.file_detection import detect_file_type

# Use the factory (recommended)
factory = DocumentExtractorFactory()
extractor = factory.create_extractor(mime_type, filename)
text = await extractor.extract_text(content, filename)

# Or use a specific extractor directly
pdf_extractor = PDFExtractor()
text = await pdf_extractor.extract_text(pdf_content, "document.pdf")
```

### Using Caching

The new implementation provides flexible caching:

```python
from app.infrastructure.document_processor import InMemoryDocumentCache
from app.infrastructure.document_processor.cache import cached_extraction

cache = InMemoryDocumentCache(max_size=32, ttl_seconds=7200)

# Use the cached_extraction decorator
@cached_extraction(cache)
async def my_extraction_function(content):
    # Custom extraction logic
    return text
```

## Error Handling

All extractors raise `DocumentProcessingError` with detailed error information:

```python
try:
    text = await extractor.extract_text(content, filename)
except DocumentProcessingError as e:
    print(f"Extraction failed: {e.detail}")
```

## Fallback Mechanisms

The implementation includes automatic fallback strategies:

- PDF extraction tries PyMuPDF first, then falls back to PyPDF2
- Text extraction tries UTF-8 first, then falls back to UTF-8 with replacement characters

## Performance Considerations

- All extraction operations run in thread pools using `asyncio.to_thread()` to avoid blocking the event loop
- Caching can be enabled/disabled per extractor instance
- Each extractor logs detailed performance metrics
