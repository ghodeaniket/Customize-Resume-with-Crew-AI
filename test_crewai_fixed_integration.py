"""Test fixed CrewAI integration."""
import os
import asyncio
import logging
from typing import Dict, Any
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a simple tool using the functional approach
@tool("Calculate Tool")
def calculate_tool(operation: str, first_number: float, second_number: float) -> str:
    """Performs basic arithmetic operations.
    
    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        first_number: The first number
        second_number: The second number
        
    Returns:
        str: The result of the operation
    """
    operations = {
        'add': lambda a, b: a + b,
        'subtract': lambda a, b: a - b,
        'multiply': lambda a, b: a * b,
        'divide': lambda a, b: a / b if b != 0 else "Error: Division by zero"
    }
    
    if operation not in operations:
        return f"Error: Invalid operation '{operation}'. Use add, subtract, multiply, or divide."
    
    result = operations[operation](first_number, second_number)
    return f"The result of {operation} {first_number} and {second_number} is {result}"

async def test_crewai_simple():
    """Test basic CrewAI functionality with our fixed implementation."""
    try:
        # Print environment variables (without showing API keys)
        env_vars = {k: v if not k.endswith('API_KEY') else '[REDACTED]' 
                   for k, v in os.environ.items() 
                   if k.startswith(('OPENAI', 'LLM', 'AGENT'))}
        logger.info(f"Environment variables: {env_vars}")
        
        # Get API key from environment or settings
        api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY or settings.LLM_API_KEY
        if not api_key:
            logger.error("No API key found")
            return False
        
        # Get model name from settings or default
        model_name = os.environ.get("AGENT_LLM") or settings.AGENT_LLM or "gpt-4o"
        
        # Create LLM instance with explicit parameters
        llm = LLM(api_key=api_key, model=model_name)
        logger.info(f"Created LLM instance with model: {model_name}")
        
        # Create a simple agent
        researcher = Agent(
            role="Calculator",
            goal="Perform mathematical calculations",
            backstory="You are an expert mathematician who can perform accurate calculations.",
            tools=[calculate_tool],
            verbose=True,
            llm=llm
        )
        
        # Create a simple task
        calc_task = Task(
            description="Calculate the result of multiplying 123 by 456.",
            expected_output="The calculated result with explanation.",
            agent=researcher
        )
        
        # Create a crew
        crew = Crew(
            agents=[researcher],
            tasks=[calc_task],
            verbose=True,
            process=Process.sequential
        )
        
        # Run the crew
        logger.info("Starting CrewAI execution...")
        result = crew.kickoff()
        
        # Print result
        logger.info(f"CrewAI result type: {type(result)}")
        logger.info(f"CrewAI result: {result}")
        
        # Try to extract different output formats
        outputs = []
        try:
            if hasattr(result, 'tasks') and result.tasks:
                outputs.append(f"Task Output: {result.tasks[0].output.raw}")
        except:
            pass
            
        try:
            if hasattr(result, 'raw'):
                outputs.append(f"Raw Output: {result.raw}")
        except:
            pass
            
        try:
            outputs.append(f"String Output: {str(result)}")
        except:
            pass
        
        for output in outputs:
            logger.info(output)
            
        return True
    except Exception as e:
        logger.error(f"Error testing CrewAI: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # Ensure environment variables are set
    if not (os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY or settings.LLM_API_KEY):
        api_key = input("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = api_key
    
    result = asyncio.run(test_crewai_simple())
    logger.info(f"Test result: {'Success' if result else 'Failed'}")
