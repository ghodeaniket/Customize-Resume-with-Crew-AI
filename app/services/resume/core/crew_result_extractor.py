"""Service for extracting results from CrewAI outputs."""
from typing import Any, List, Callable, Optional

from app.core.logging import logger


class CrewResultExtractor:
    """Service for extracting results from various CrewAI output formats."""
    
    @staticmethod
    def extract_crew_result(crew_output: Any) -> str:
        """Extract the result string from different CrewAI output formats.
        
        Args:
            crew_output: The output from crew.kickoff()
            
        Returns:
            str: Extracted result text or empty string if extraction fails
        """
        # Define extraction methods
        extraction_methods = CrewResultExtractor._get_extraction_methods()
        
        # Try each method and return the first successful result
        for i, method in enumerate(extraction_methods):
            try:
                result = method(crew_output)
                if result:
                    logger.info(f"Successfully extracted result using method {i+1}")
                    return result
            except (AttributeError, IndexError, TypeError) as e:
                logger.debug(f"Extraction method {i+1} failed: {str(e)}")
                continue
        
        # If all methods fail, return an empty string
        logger.warning("All extraction methods failed")
        return ""
    
    @staticmethod
    def _get_extraction_methods() -> List[Callable[[Any], Optional[str]]]:
        """Get list of extraction methods to try.
        
        Returns:
            List[Callable]: List of extraction functions
        """
        return [
            # Method 1: Access as tasks[0].output.raw
            lambda x: (x.tasks[0].output.raw 
                      if hasattr(x, 'tasks') and x.tasks and 
                      hasattr(x.tasks[0], 'output') and 
                      hasattr(x.tasks[0].output, 'raw') else None),
            
            # Method 2: Access as task_output
            lambda x: x.task_output if hasattr(x, 'task_output') else None,
            
            # Method 3: Access as raw
            lambda x: x.raw if hasattr(x, 'raw') else None,
            
            # Method 4: Access as output
            lambda x: x.output if hasattr(x, 'output') else None,
            
            # Method 5: Access as result
            lambda x: x.result if hasattr(x, 'result') else None,
            
            # Method 6: Convert to dict and stringify
            lambda x: str(x.to_dict()) if hasattr(x, 'to_dict') else None,
            
            # Method 7: Check for getattr with specific attributes
            lambda x: getattr(x, 'content', None),
            
            # Method 8: Access first element if it's a list
            lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None,
            
            # Method 9: Try __str__ method
            lambda x: str(x)
        ]
    
    @staticmethod
    def extract_job_analysis_result(crew_output: Any) -> str:
        """Extract job analysis result with specialized handling.
        
        Args:
            crew_output: The output from crew.kickoff()
            
        Returns:
            str: Extracted job analysis result
        """
        result = CrewResultExtractor.extract_crew_result(crew_output)
        
        if result:
            logger.info("Job analysis result extracted successfully")
            return result
        else:
            # If we couldn't extract a result, return the string representation
            logger.warning("Could not extract structured output, returning string representation")
            return str(crew_output)
    
    @staticmethod
    def extract_optimization_result(crew_output: Any) -> str:
        """Extract resume optimization result with specialized handling.
        
        Args:
            crew_output: The output from crew.kickoff()
            
        Returns:
            str: Extracted optimization result
        """
        result = CrewResultExtractor.extract_crew_result(crew_output)
        
        if result:
            logger.info("Resume optimization result extracted successfully")
            return result
        else:
            # If we couldn't extract a result, return the string representation
            logger.warning("Could not extract structured output from optimization, returning string representation")
            return str(crew_output)
