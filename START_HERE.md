# Resume Customizer - Getting Started

This guide will help you start and test the Resume Customizer backend application.

## Starting the Server

There are two ways to start the development server:

### Option 1: Using the Python script

```bash
python3 start_server.py
```

### Option 2: Using the shell script

```bash
# For macOS/Linux:
./start_server.sh

# For Windows:
start_server.bat
```

### Command-line options

The server script supports several command-line options:

- `--open-docs`: Automatically open the API documentation in your web browser
  ```bash
  python3 start_server.py --open-docs
  ```

- `--port=XXXX`: Specify a custom port (if the default port 8000 is unavailable)
  ```bash
  python3 start_server.py --port=8080
  ```

You can combine multiple options:
```bash
python3 start_server.py --open-docs --port=8080
```

## Testing the API

Once the server is running, you can test the API using the following endpoints:

### 1. Health Check

Verify the server is running:

```bash
curl -X GET http://127.0.0.1:8000/health
```

Expected response:
```json
{"status":"ok"}
```

### 2. Upload a Resume

Upload a resume file for processing:

```bash
curl -X POST -F "resume=@test_data/test_resume.txt" http://127.0.0.1:8000/api/resumes/upload
```

Expected response (task_id will be different):
```json
{
  "task_id": "ade96508-dede-4954-931d-df7aa686d31d",
  "filename": "test_resume.txt",
  "status": "processing"
}
```

### 3. Check Status

Check the status of a resume processing task (replace TASK_ID with the ID from upload response):

```bash
curl -X GET http://127.0.0.1:8000/api/resumes/TASK_ID
```

Expected response:
```json
{
  "task_id": "ade96508-dede-4954-931d-df7aa686d31d",
  "status": "completed",
  "progress": 100.0,
  "created_at": "2025-04-29T19:15:07.513189",
  "updated_at": "2025-04-29T19:15:07.513192",
  "result_url": "/api/resumes/ade96508-dede-4954-931d-df7aa686d31d/download"
}
```

### 4. Get Extracted Text

Retrieve the extracted text from the processed resume:

```bash
curl -X GET http://127.0.0.1:8000/api/resumes/TASK_ID/text
```

## Test Data

Sample test files are provided in the `test_data` directory:

- `test_resume.txt`: A sample resume for testing the upload
- `test_job_description.txt`: A sample job description for testing Phase 2 functionality

### Creating a Test PDF Resume

If you need a PDF resume for testing, you can generate one using the included script:

```bash
python3 create_test_pdf.py
```

This will create a `test_resume.pdf` file in the `test_data` directory that you can use for testing. The script requires the `reportlab` package, which you can install with:

```bash
pip install reportlab
```

## API Documentation

The API documentation is available at:
http://127.0.0.1:8000/docs

This interactive documentation allows you to explore and test all available endpoints.

## Next Steps

Phase 1 of the application is currently implemented, which focuses on document processing and text extraction. Phase 2 will implement resume customization based on job descriptions using CrewAI.
