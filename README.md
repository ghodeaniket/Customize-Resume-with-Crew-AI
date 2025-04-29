# Resume Customizer

A backend application built with FastAPI and CrewAI that customizes resumes based on job descriptions.

## Project Overview

The Resume Customizer is an intelligent application that analyzes job descriptions and tailors resumes to match them, increasing the chances of getting past Applicant Tracking Systems (ATS) and catching the attention of recruiters.

### Key Features (Planned)

- Resume parsing from PDF and DOCX formats
- Job description analysis to extract key requirements
- Resume customization with AI-powered agents
- ATS simulation for resume scoring
- Multi-format export (PDF, DOCX, TXT, HTML)

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
   Update the values in `.env` with your own configurations.

4. Run the application:
   ```bash
   poetry run uvicorn main:app --reload
   ```

5. Access the API documentation at http://localhost:8000/docs

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

## Project Status

This project is currently in Phase 0 (Project Setup). See the implementation plan for details on upcoming phases.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
