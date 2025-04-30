"""Test CrewAI integration with environment variables."""
import os
import asyncio
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

async def test_crewai_with_env():
    """Test CrewAI functionality with environment variables."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Log loaded environment variables (without showing API keys)
        env_vars = {k: v if not k.endswith('API_KEY') else '[REDACTED]' 
                   for k, v in os.environ.items() 
                   if k.startswith(('OPENAI', 'LLM', 'AGENT'))}
        print(f"Environment variables: {env_vars}")
        
        # Set OpenAI API key explicitly
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            openai_api_key = os.getenv("LLM_API_KEY")
        
        if not openai_api_key:
            print("No API key found in environment variables.")
            return False
        
        print(f"API key loaded: {openai_api_key[:5]}...{openai_api_key[-5:]}")
        
        # Get model name from environment or use default
        model = os.getenv("AGENT_LLM", "gpt-4o")
        print(f"Using model: {model}")
        
        # Configure LLM
        llm = LLM(api_key=openai_api_key, model=model)
        
        # Create a simple agent
        researcher = Agent(
            role="Researcher",
            goal="Research and provide information",
            backstory="You are an expert researcher who can find and analyze information.",
            verbose=True,
            llm=llm
        )
        
        # Create a simple task
        research_task = Task(
            description="Research the topic 'AI and automation' and provide a brief summary.",
            expected_output="A brief summary of AI and automation.",
            agent=researcher
        )
        
        # Create a crew
        crew = Crew(
            agents=[researcher],
            tasks=[research_task],
            verbose=True,
            process=Process.sequential
        )
        
        # Run the crew
        print("Starting CrewAI execution...")
        result = crew.kickoff()
        
        # Print result
        print(f"CrewAI result type: {type(result)}")
        print(f"CrewAI result: {result}")
        
        return True
    except Exception as e:
        print(f"Error testing CrewAI: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_crewai_with_env())
    print(f"Test result: {'Success' if result else 'Failed'}")
