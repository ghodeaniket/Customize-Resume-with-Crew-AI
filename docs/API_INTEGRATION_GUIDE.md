# Resume Customizer API Integration Guide

## Overview

The Resume Customizer API provides endpoints for uploading resumes, customizing them based on job descriptions, and retrieving the results. This guide helps frontend developers integrate with the API effectively.

## Base URL

All API endpoints are relative to the base URL:

```
/api/v1
```

## Authentication

*Note: Authentication is not yet implemented. This section will be updated when available.*

## Common Response Format

All API responses follow a standard format:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { ... }
}
```

In case of an error:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "error_id": "unique_error_id",
    "path": "/api/v1/resumes/upload",
    "timestamp": "2025-05-03T00:00:00Z",
    "suggestion": "Suggestion to fix the error",
    "details": { ... }
  },
  "meta": { ... }
}
```

## API Endpoints

### Health Check

```
GET /api/v1/health
```

Returns the health status of the API.

**Response Example:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2025-05-03T00:00:00Z",
    "version": "1.0.0",
    "environment": "development",
    "checks": {
      "storage": {
        "status": "up",
        "description": "File system access"
      },
      "dependencies": {
        "status": "up"
      }
    }
  },
  "error": null,
  "meta": null
}
```

### Upload Resume

```
POST /api/v1/resumes/upload
```

Upload a resume document for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form with `resume` file field

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "john_doe_resume.pdf",
    "status": "processing",
    "upload_timestamp": "2025-05-03T00:00:00Z"
  },
  "error": null,
  "meta": null
}
```

### Check Resume Processing Status

```
GET /api/v1/resumes/{task_id}
```

Check the status of the resume processing task.

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "progress": 100.0,
    "created_at": "2025-05-03T00:00:00Z",
    "updated_at": "2025-05-03T00:05:00Z",
    "message": "Resume processing completed",
    "processing_time_ms": 1234.56
  },
  "error": null,
  "meta": null
}
```

### Get Extracted Resume Text

```
GET /api/v1/resumes/{task_id}/text
```

Get the extracted text from a processed resume.

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "John Doe\nSoftware Engineer\n...",
    "metadata": {
      "filename": "john_doe_resume.pdf",
      "file_size": 125648,
      "content_type": "application/pdf"
    },
    "word_count": 358,
    "character_count": 2541
  },
  "error": null,
  "meta": null
}
```

### Customize Resume

```
POST /api/v1/resumes/customize
```

Submit a job description to customize a previously uploaded resume.

**Request:**
- Content-Type: `application/json`
- Body:
  ```json
  {
    "resume_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_description": "Senior Backend Developer...",
    "customize_level": "standard",
    "industry": "Technology",
    "keywords": ["Python", "FastAPI", "Docker"]
  }
  ```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "processing",
    "customization_level": "standard",
    "estimated_completion_time": 120
  },
  "error": null,
  "meta": null
}
```

### Check Customization Status

```
GET /api/v1/resumes/customization/{task_id}
```

Check the status of the resume customization task.

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "completed",
    "progress": 100.0,
    "created_at": "2025-05-03T00:10:00Z",
    "updated_at": "2025-05-03T00:12:00Z",
    "message": "Resume customization completed",
    "processing_time_ms": 15678.90
  },
  "error": null,
  "meta": null
}
```

### Get Customization Result

```
GET /api/v1/resumes/customization/{task_id}/result
```

Get the customized resume result.

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": "550e8400-e29b-41d4-a716-446655440001",
    "original_resume_id": "550e8400-e29b-41d4-a716-446655440000",
    "customized_text": "John Doe\nSenior Backend Developer\n...",
    "customization_level": "standard",
    "changes_summary": {
      "skills_added": ["Docker", "Kubernetes"],
      "skills_emphasized": ["Python", "FastAPI"],
      "sections_modified": ["Skills", "Experience"]
    },
    "optimization_metrics": {
      "keyword_match_rate": 0.85,
      "ats_score_improvement": 0.32
    },
    "completion_timestamp": "2025-05-03T00:12:00Z"
  },
  "error": null,
  "meta": null
}
```

## Batch Operations

The API supports batch operations for checking the status of multiple tasks simultaneously.

### Batch Status Check

```
POST /api/v1/batch/status
```

Check the status of multiple tasks at once.

**Request:**
- Content-Type: `application/json`
- Body:
  ```json
  {
    "task_ids": [
      "550e8400-e29b-41d4-a716-446655440000",
      "550e8400-e29b-41d4-a716-446655440001"
    ],
    "include_metadata": true
  }
  ```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "progress": 100.0,
        "type": "resume_processing"
      },
      {
        "task_id": "550e8400-e29b-41d4-a716-446655440001",
        "status": "processing",
        "progress": 75.0,
        "type": "resume_customization"
      }
    ],
    "summary": {
      "total": 2,
      "completed": 1,
      "processing": 1,
      "failed": 0
    }
  },
  "error": null,
  "meta": null
}
```

## Error Handling

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| VALIDATION_ERROR | Input validation failed | 400 |
| NOT_FOUND | Resource not found | 404 |
| FILE_TOO_LARGE | File size exceeds limit | 400 |
| UNSUPPORTED_FILE_TYPE | File type not supported | 400 |
| PROCESSING_ERROR | Error during processing | 500 |
| CUSTOMIZATION_ERROR | Error during customization | 500 |

### Error Response Example

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "The file type is not supported",
    "error_id": "err_1234567890",
    "path": "/api/v1/resumes/upload",
    "timestamp": "2025-05-03T00:00:00Z",
    "suggestion": "Please upload a PDF, DOCX, or TXT file",
    "details": {
      "supported_types": ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
      "provided_type": "image/jpeg"
    }
  },
  "meta": null
}
```

## Integration Workflow

### Resume Upload & Processing Workflow

1. **Upload Resume**:
   - `POST /api/v1/resumes/upload` with resume file
   - Store the returned `task_id`

2. **Check Processing Status** (poll until completed):
   - `GET /api/v1/resumes/{task_id}`
   - When `status` is `completed`, proceed

3. **Get Extracted Text** (optional):
   - `GET /api/v1/resumes/{task_id}/text`
   - Display or validate the extracted text

### Resume Customization Workflow

1. **Submit Customization Request**:
   - `POST /api/v1/resumes/customize` with resume_id and job_description
   - Store the returned `task_id`

2. **Check Customization Status** (poll until completed):
   - `GET /api/v1/resumes/customization/{task_id}`
   - When `status` is `completed`, proceed

3. **Get Customization Result**:
   - `GET /api/v1/resumes/customization/{task_id}/result`
   - Display or download the customized resume

## Polling Implementation

For long-running tasks, implement a polling strategy:

```javascript
async function pollTaskStatus(taskId, type = 'processing') {
  const endpoint = type === 'customization' 
    ? `/api/v1/resumes/customization/${taskId}` 
    : `/api/v1/resumes/${taskId}`;
    
  let attempts = 0;
  let delay = 1000; // Start with 1 second delay
  
  while (attempts < 60) { // Max 10 minutes (with backoff)
    try {
      const response = await fetch(endpoint);
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error?.message || 'Unknown error');
      }
      
      const taskData = result.data;
      
      if (taskData.status === 'completed') {
        return taskData;
      }
      
      if (taskData.status === 'failed') {
        throw new Error(taskData.message || 'Task failed');
      }
      
      // Update progress UI
      updateProgressIndicator(taskData.progress);
      
      // Wait before next attempt
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Increase delay with exponential backoff (max 10 seconds)
      delay = Math.min(delay * 1.5, 10000);
      attempts++;
    } catch (error) {
      console.error('Error polling task status:', error);
      throw error;
    }
  }
  
  throw new Error('Task timed out');
}
```

## Example Client Implementation

Here's a simple React client implementation for the resume upload and customization flow:

```javascript
import React, { useState } from 'react';
import axios from 'axios';

const API_BASE_URL = '/api/v1';

function ResumeCustomizer() {
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeTaskId, setResumeTaskId] = useState(null);
  const [resumeStatus, setResumeStatus] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [customizationTaskId, setCustomizationTaskId] = useState(null);
  const [customizationStatus, setCustomizationStatus] = useState(null);
  const [customizedResume, setCustomizedResume] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);

  // Step 1: Upload Resume
  const handleFileChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  const uploadResume = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const formData = new FormData();
      formData.append('resume', resumeFile);
      
      const response = await axios.post(`${API_BASE_URL}/resumes/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setResumeTaskId(response.data.data.task_id);
      setResumeStatus('processing');
      
      // Start polling for status
      pollResumeStatus(response.data.data.task_id);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Upload failed');
      setLoading(false);
    }
  };

  // Step 2: Poll Resume Status
  const pollResumeStatus = async (taskId) => {
    try {
      const checkStatus = async () => {
        const response = await axios.get(`${API_BASE_URL}/resumes/${taskId}`);
        const status = response.data.data;
        
        setResumeStatus(status.status);
        setProgress(status.progress);
        
        if (status.status === 'completed') {
          setLoading(false);
          return true;
        } else if (status.status === 'failed') {
          setError(status.message || 'Resume processing failed');
          setLoading(false);
          return true;
        }
        
        return false;
      };
      
      let isCompleted = await checkStatus();
      
      if (!isCompleted) {
        const interval = setInterval(async () => {
          const isCompleted = await checkStatus();
          
          if (isCompleted) {
            clearInterval(interval);
          }
        }, 2000);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Status check failed');
      setLoading(false);
    }
  };

  // Step 3: Submit Customization Request
  const submitCustomization = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post(`${API_BASE_URL}/resumes/customize`, {
        resume_id: resumeTaskId,
        job_description: jobDescription,
        customize_level: 'standard'
      });
      
      setCustomizationTaskId(response.data.data.task_id);
      setCustomizationStatus('processing');
      
      // Start polling for customization status
      pollCustomizationStatus(response.data.data.task_id);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Customization request failed');
      setLoading(false);
    }
  };

  // Step 4: Poll Customization Status
  const pollCustomizationStatus = async (taskId) => {
    try {
      const checkStatus = async () => {
        const response = await axios.get(`${API_BASE_URL}/resumes/customization/${taskId}`);
        const status = response.data.data;
        
        setCustomizationStatus(status.status);
        setProgress(status.progress);
        
        if (status.status === 'completed') {
          // Get customization result
          getCustomizationResult(taskId);
          return true;
        } else if (status.status === 'failed') {
          setError(status.message || 'Customization failed');
          setLoading(false);
          return true;
        }
        
        return false;
      };
      
      let isCompleted = await checkStatus();
      
      if (!isCompleted) {
        const interval = setInterval(async () => {
          const isCompleted = await checkStatus();
          
          if (isCompleted) {
            clearInterval(interval);
          }
        }, 3000);
      }
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Status check failed');
      setLoading(false);
    }
  };

  // Step 5: Get Customization Result
  const getCustomizationResult = async (taskId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/resumes/customization/${taskId}/result`);
      setCustomizedResume(response.data.data);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.error?.message || 'Failed to get result');
      setLoading(false);
    }
  };

  return (
    <div className="resume-customizer">
      <h1>Resume Customizer</h1>
      
      {error && (
        <div className="error-message">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      
      {loading && (
        <div className="progress-bar">
          <div className="progress" style={{ width: `${progress}%` }}></div>
          <p>{progress.toFixed(0)}% Complete</p>
        </div>
      )}
      
      <div className="upload-section">
        <h2>Step 1: Upload Your Resume</h2>
        <input type="file" onChange={handleFileChange} accept=".pdf,.docx,.txt" />
        <button onClick={uploadResume} disabled={!resumeFile || loading}>
          Upload Resume
        </button>
        
        {resumeStatus === 'completed' && (
          <div className="success-message">
            <p>Resume uploaded and processed successfully!</p>
          </div>
        )}
      </div>
      
      {resumeStatus === 'completed' && (
        <div className="customize-section">
          <h2>Step 2: Enter Job Description</h2>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste job description here..."
            rows={10}
          />
          <button onClick={submitCustomization} disabled={!jobDescription || loading}>
            Customize Resume
          </button>
        </div>
      )}
      
      {customizedResume && (
        <div className="result-section">
          <h2>Your Customized Resume</h2>
          <div className="resume-text">
            <pre>{customizedResume.customized_text}</pre>
          </div>
          <div className="changes-summary">
            <h3>Changes Made:</h3>
            <ul>
              {customizedResume.changes_summary.skills_added.map((skill, index) => (
                <li key={index}>Added skill: {skill}</li>
              ))}
              {customizedResume.changes_summary.skills_emphasized.map((skill, index) => (
                <li key={index}>Emphasized skill: {skill}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResumeCustomizer;
```

## Best Practices

1. **Error Handling**: Always implement proper error handling with user-friendly messages
2. **Progress Indicators**: Show progress for long-running tasks
3. **Exponential Backoff**: Use exponential backoff for polling to reduce server load
4. **Timeout Handling**: Implement timeouts for tasks that take too long
5. **File Validation**: Validate file types and sizes client-side before uploading
6. **Responsiveness**: Keep the UI responsive during long-running operations
7. **Retry Logic**: Add retry capabilities for transient errors

## Rate Limiting

The API implements rate limiting to ensure fair usage. The current limits are:

- 60 requests per minute per IP address
- 5 resume uploads per minute per IP address
- 10 customization requests per minute per IP address

Responses from rate-limited requests will include:

- HTTP Status: 429 Too Many Requests
- Headers:
  - X-RateLimit-Limit: [requests allowed per window]
  - X-RateLimit-Remaining: [requests remaining in current window]
  - X-RateLimit-Reset: [seconds until window resets]

## Security Considerations

1. **File Validation**: Always validate uploaded files client-side and server-side
2. **Input Sanitization**: Sanitize all user inputs before submission
3. **Content Security Policy**: Implement CSP headers for web clients
4. **HTTPS**: Always use HTTPS for communication
5. **Error Handling**: Avoid exposing sensitive information in error messages

## Support

For issues or questions about the API, please contact the development team at support@example.com.
