# Resume Customizer

A backend application built with FastAPI and CrewAI that customizes resumes based on job descriptions.

## Project Overview

The Resume Customizer is an intelligent application that analyzes job descriptions and tailors resumes to match them, increasing the chances of getting past Applicant Tracking Systems (ATS) and catching the attention of recruiters.

### Key Features

- ✅ Resume parsing from PDF and DOCX formats
- ✅ Job description analysis to extract key requirements
- ✅ Resume customization with AI-powered agents
- 🔄 ATS simulation for resume scoring (planned)
- 🔄 Multi-format export (PDF, DOCX, TXT, HTML) (planned)

### How It Works

1. **Document Processing**: The system extracts text from uploaded resume files
2. **Job Analysis**: AI agents analyze job descriptions to identify key requirements
3. **Resume Optimization**: AI agents customize the resume to match job requirements
4. **Customization Level**: Choose from minimal, standard, or comprehensive customization

## Project Structure

The application follows a clean architecture with the following components:

- `app/api`: FastAPI routes and endpoints
- `app/core`: Application configuration and utilities
- `app/crews`: CrewAI agents and tasks for resume customization
- `app/infrastructure`: Document processing components
- `app/models`: Domain models and API schemas
- `app/services`: Business logic services

## Development Setup

### Prerequisites

- Python 3.10+
- Poetry for dependency management
- OpenAI API key (for CrewAI integration)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/resume-customizer.git
   cd resume-customizer
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   
4. Configure your API keys in the `.env` file:
   ```
   # Required for CrewAI integration
   OPENAI_API_KEY=your-api-key-here
   
   # Optional model specification (defaults to gpt-4o)
   AGENT_LLM=gpt-4o
   
   # Optional verbose settings
   AGENT_VERBOSE=True
   CREW_VERBOSE=True
   ```

5. Validate your environment setup:
   ```bash
   python validate_environment.py
   ```
   This will check if all required components are properly configured.

6. Run the application:
   ```bash
   ./start_server.sh
   ```
   Or with Python directly:
   ```bash
   python -m uvicorn main:app --reload
   ```

7. Access the API documentation at http://localhost:8000/docs

### Testing CrewAI Integration

You can test the CrewAI integration separately with:

```bash
python test_crewai_fixed_integration.py
```

This will verify that your API keys are properly configured and CrewAI is working correctly.

### Docker Setup

Alternatively, you can use Docker:

```bash
docker-compose up --build
```

## Testing

Run the tests with pytest:

```bash
poetry run pytest
```

Run tests with coverage report:

```bash
poetry run pytest --cov=app --cov-report=term-missing
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Check if the API is running |
| `/api/resumes/upload` | POST | Upload a resume file (PDF, DOCX, TXT) |
| `/api/resumes/{task_id}` | GET | Check the status of resume processing |
| `/api/resumes/{task_id}/text` | GET | Get the extracted text from a resume |
| `/api/resumes/customize` | POST | Submit a job description to customize a resume |
| `/api/resumes/customization/{task_id}` | GET | Check the status of customization |
| `/api/resumes/customization/{task_id}/result` | GET | Get the customized resume result |

### Example API Usage

1. **Upload a resume**:
   ```bash
   curl -X POST -F "resume=@/path/to/your/resume.pdf" http://localhost:8000/api/resumes/upload
   ```
   Response: `{"task_id": "4a7f6c8d-1b3a-4e5f-9c7d-2e3b4a5c6d7e", "filename": "resume.pdf", "status": "processing"}`

2. **Customize a resume**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     -d '{"resume_id": "4a7f6c8d-1b3a-4e5f-9c7d-2e3b4a5c6d7e", "job_description": "Senior Developer..."}' \
     http://localhost:8000/api/resumes/customize
   ```
   Response: `{"task_id": "8e7d6c5b-4a3f-2e1d-0c9b-8a7b6c5d4e3f", "status": "processing"}`

## CrewAI Integration

This application uses CrewAI to orchestrate AI agents that analyze job descriptions and customize resumes. The integration includes:

### AI Agents

1. **Resume Analyzer Agent**: Extracts key information from job descriptions
   - Role: Identify required skills, qualifications, and preferences
   - Tools: Job matching and resume processing tools

2. **Resume Optimizer Agent**: Tailors resumes to match job requirements
   - Role: Highlight relevant skills and experiences
   - Tools: Resume processing and formatting tools

### Customization Levels

- **Minimal**: Makes only essential changes while preserving 90% of original content
- **Standard**: Makes moderate changes while preserving 75% of original content
- **Comprehensive**: Makes extensive changes with complete restructuring where beneficial

### Resilient Implementation

The system includes multiple fallback mechanisms:
- Support for both class-based and function-based CrewAI tools
- Alternate job analysis approaches when primary approach fails
- Robust output extraction from various CrewAI versions

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git commit -m "Add your feature description"
   ```

3. Push your branch and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Ensure the CI pipeline passes before merging.

## Troubleshooting

### Common Issues

#### API Key Problems

**Symptom**: Error messages mentioning "API key" or "Authentication failed"

**Solution**:
1. Ensure your OpenAI API key is correctly set in the `.env` file
2. Verify the key has sufficient credits and permissions
3. Run `python validate_environment.py` to check configuration

#### CrewAI Integration Issues

**Symptom**: Errors about "BaseTool" or Pydantic validation errors

**Solution**:
1. Check your CrewAI version matches requirements (`pip show crewai`)
2. Try the fallback function-based approach by modifying `app/crews/tools/resume_processor.py`
3. Run `python test_crewai_fixed_integration.py` to isolate and test the integration

#### Document Processing Errors

**Symptom**: "Error processing document" or empty text extraction

**Solution**:
1. Verify the file format is supported (PDF, DOCX, TXT)
2. Check if the file can be opened manually
3. Try converting the file to a different format

### Performance Tuning

For better performance with large documents or many concurrent users:

1. Increase worker count in `start_server.sh`:
   ```bash
   --workers 4
   ```

2. Adjust async concurrency limits in `app/core/config.py`:
   ```python
   MAX_CONCURRENT_TASKS = 5
   ```

3. Configure model choice for different customization levels:
   - For faster processing: Use `gpt-3.5-turbo` for minimal customization
   - For better quality: Use `gpt-4o` for comprehensive customization

## Project Status

This project has implemented Phases 1 (Document Processing) and 2 (CrewAI Integration) from the implementation plan. Phase 3 (Extended Features) is currently in development.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
