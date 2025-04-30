"""Test CrewAI integration."""
import os
import asyncio
from crewai import Agent, Task, Crew, Process

async def test_crewai_simple():
    """Test basic CrewAI functionality without our custom components."""
    try:
        # Print environment variables (without showing API keys)
        env_vars = {k: v if not k.endswith('API_KEY') else '[REDACTED]' 
                   for k, v in os.environ.items() 
                   if k.startswith(('OPENAI', 'LLM', 'AGENT'))}
        print(f"Environment variables: {env_vars}")
        
        # Create a simple agent
        researcher = Agent(
            role="Researcher",
            goal="Research and provide information",
            backstory="You are an expert researcher who can find and analyze information.",
            verbose=True
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
    result = asyncio.run(test_crewai_simple())
    print(f"Test result: {'Success' if result else 'Failed'}")
