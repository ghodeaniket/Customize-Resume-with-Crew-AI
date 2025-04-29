# CrewAI Integration for Resume Customizer

This document explains the implementation of Phase 2 of the Resume Customizer backend, which integrates CrewAI for intelligent resume customization based on job descriptions.

## Architecture Overview

The CrewAI integration follows these key design principles:

1. **Loosely coupled components**: Agents, tasks, and tools are implemented as separate modules, making the system flexible and maintainable.
2. **Asynchronous processing**: All customization operations run in background tasks to prevent blocking the API.
3. **Progressive status updates**: Task progress is tracked and made available through API endpoints.
4. **Error handling**: The system gracefully handles failures at all levels with appropriate error messages.
5. **Testing**: Unit and integration tests verify the behavior of all components.

## Key Components

### 1. CrewAI Agents

Two specialized agents are implemented:

- **Resume Analyzer Agent**: Analyzes job descriptions to extract key requirements and skills.
- **Resume Optimizer Agent**: Customizes resumes to match job requirements.

Both agents are configured with appropriate roles, goals, and backstories that guide their behavior.

### 2. CrewAI Tasks

Tasks are structured units of work assigned to agents:

- **Job Analysis Task**: Extracts key requirements from the job description.
- **Resume Optimization Task**: Tailors the resume to match the job requirements.

Each task has clear instructions, expected outputs, and contextual information.

### 3. Custom Tools

Custom tools extend the capabilities of the agents:

- **ResumeProcessorTool**: Allows agents to access and process resume text.
- **JobMatcherTool**: Analyzes the match between resumes and job requirements.

### 4. Service Layer

Services orchestrate the integration between FastAPI and CrewAI:

- **ResumeService**: Handles resume processing and customization with CrewAI.
- **TaskService**: Manages task status tracking and persistence.
- **DocumentStorageService**: Handles file storage and retrieval with new support for storing task results.

### 5. API Endpoints

New API endpoints enable resume customization:

- `POST /api/resumes/customize`: Submit a customization request.
- `GET /api/resumes/customization/{task_id}`: Check customization status.
- `GET /api/resumes/customization/{task_id}/result`: Retrieve the customized resume.

## Customization Process Flow

1. Client uploads a resume (Phase 1 functionality).
2. Client submits a job description and references the uploaded resume.
3. The system creates a customization task and processes it asynchronously:
   - The job description is analyzed by the Resume Analyzer Agent.
   - The extracted requirements are passed to the Resume Optimizer Agent.
   - The optimizer tailors the resume to match the job requirements.
4. The client can check the status of the customization task.
5. Once completed, the client can retrieve the customized resume.

## Configuration Options

The system supports several customization levels:

- **minimal**: Makes only essential changes to highlight relevant skills.
- **standard**: Makes moderate changes to optimize for the job description.
- **comprehensive**: Makes extensive changes for maximum job alignment.

Additional configuration options in `app/core/config.py` control CrewAI behavior, including:

- **AGENT_LLM**: The language model used by the agents.
- **AGENT_VERBOSE**: Whether to enable verbose logging for agents.
- **CREW_VERBOSE**: Whether to enable verbose logging for CrewAI crews.
- **MEMORY_ENABLED**: Whether to enable memory for agents.
- **MAX_EXECUTION_TIME**: Maximum execution time for CrewAI tasks.

## Testing Strategy

The implementation includes two types of tests:

1. **Unit Tests**: Verify the behavior of individual components:
   - CrewAI agent creation and configuration
   - Task definition and structure
   - Tool functionality

2. **Integration Tests**: Verify the API endpoints and service layer:
   - Resume customization request validation
   - Task status reporting
   - Result retrieval

## Error Handling

The system includes comprehensive error handling:

- **CustomizationError**: For errors in the customization process.
- **ResumeNotFoundError**: When a referenced resume doesn't exist.
- **TaskNotFoundError**: When a requested task doesn't exist.

HTTP error responses include descriptive messages to guide clients on resolving issues.

## Future Enhancements

Planned improvements for future phases:

1. Enhanced job matching with more advanced NLP techniques.
2. Support for different resume formats in the output.
3. ATS scoring and feedback on resume effectiveness.
4. Simultaneous optimization for multiple job descriptions.
5. Customization templates for different industries and roles.
