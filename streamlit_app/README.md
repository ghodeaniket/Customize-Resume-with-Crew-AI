# Resume Customizer - Streamlit Frontend

This application provides a user-friendly interface for the Resume Customizer backend service, allowing users to upload resumes and track their processing status.

## Features

- **Phase 1: Resume Upload & Processing**
  - File upload with drag-and-drop support
  - Client-side file validation
  - Real-time processing status tracking
  - Extracted text display

## Installation

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure the Resume Customizer backend is running (default: http://localhost:8000)

3. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

## Configuration

You can configure the application behavior using environment variables:

- `RESUME_CUSTOMIZER_API_URL`: Backend API URL (default: http://localhost:8000)
- `RESUME_CUSTOMIZER_API_TIMEOUT`: API request timeout in seconds (default: 30.0)
- `RESUME_CUSTOMIZER_API_RETRY_COUNT`: Number of API request retry attempts (default: 3)

## Project Structure

- `app.py`: Main application entry point
- `components/`: UI components
  - `header.py`: Application header
  - `upload_section.py`: Resume upload section
  - `status_section.py`: Status tracking section
- `services/`: API integration
  - `api_service.py`: Backend API client
- `utils/`: Utility functions
  - `file_validation.py`: File type and size validation
  - `resume_models.py`: Data models for API responses
  - `session_state.py`: Streamlit session state management
- `config.py`: Application configuration

## Development

To add new features or modify existing ones:

1. Create or modify components in the `components/` directory
2. Update API service methods in `services/api_service.py`
3. Add utility functions as needed
4. Update `app.py` to include new components or functionality

## Next Steps

Future phases will include:

- **Phase 2: Job Description Input**
  - Job description text input
  - JSON parsing error handling
  - Customization options

- **Phase 3: Results Display & Export**
  - Side-by-side comparison view
  - ATS score visualization
  - Export options
