"""Test document processing functionality."""
import asyncio
from app.infrastructure.document_processor import DocumentProcessor
from app.core.logging import logger

async def test_text_extraction():
    """Test extraction of text from a text file."""
    try:
        # Initialize document processor
        processor = DocumentProcessor()
        
        # Load sample resume
        with open("test_resume.txt", "rb") as f:
            content = f.read()
        
        # Extract text
        extracted_text = await processor.extract_text_from_bytes(
            content, 
            filename="test_resume.txt"
        )
        
        # Print results
        print(f"Extracted text length: {len(extracted_text)}")
        print(f"Extracted text: {extracted_text}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing document processing: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_text_extraction())
    print(f"Test result: {'Success' if result else 'Failed'}")
