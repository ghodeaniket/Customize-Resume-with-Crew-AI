/**
 * Resume Customizer API Integration Example
 * 
 * This file demonstrates how to integrate with the Resume Customizer API
 * using JavaScript/React. It includes examples for uploading resumes,
 * customizing them, and retrieving results.
 */

// API Configuration
const API_CONFIG = {
  BASE_URL: '/api/v1',
  TIMEOUT: 30000,  // 30 seconds
  POLL_INTERVAL: 2000,  // 2 seconds
  MAX_POLL_ATTEMPTS: 60  // 2 minutes with 2-second intervals
};

/**
 * Upload a resume file to the API
 * 
 * @param {File} file - The resume file to upload
 * @returns {Promise<Object>} The upload response with task_id
 */
async function uploadResume(file) {
  try {
    const formData = new FormData();
    formData.append('resume', file);
    
    const response = await fetch(`${API_CONFIG.BASE_URL}/resumes/upload`, {
      method: 'POST',
      body: formData,
      timeout: API_CONFIG.TIMEOUT
    });
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Resume upload failed');
    }
    
    return result.data;
  } catch (error) {
    console.error('Error uploading resume:', error);
    throw error;
  }
}

/**
 * Poll for the status of a task
 * 
 * @param {string} taskId - The ID of the task to check
 * @param {string} type - The type of task ('processing' or 'customization')
 * @param {function} progressCallback - Callback for progress updates
 * @returns {Promise<Object>} The completed task data
 */
async function pollTaskStatus(taskId, type = 'processing', progressCallback = null) {
  const endpoint = type === 'customization' 
    ? `${API_CONFIG.BASE_URL}/resumes/customization/${taskId}`
    : `${API_CONFIG.BASE_URL}/resumes/${taskId}`;
    
  let attempts = 0;
  let delay = API_CONFIG.POLL_INTERVAL;
  
  while (attempts < API_CONFIG.MAX_POLL_ATTEMPTS) {
    try {
      const response = await fetch(endpoint);
      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.error?.message || 'Unknown error');
      }
      
      const taskData = result.data;
      
      // Report progress if callback provided
      if (progressCallback && typeof progressCallback === 'function') {
        progressCallback(taskData.progress);
      }
      
      if (taskData.status === 'completed') {
        return taskData;
      }
      
      if (taskData.status === 'failed') {
        throw new Error(taskData.message || 'Task failed');
      }
      
      // Wait before next attempt
      await new Promise(resolve => setTimeout(resolve, delay));
      
      attempts++;
    } catch (error) {
      console.error(`Error checking task status:`, error);
      throw error;
    }
  }
  
  throw new Error('Task polling timed out');
}

/**
 * Get extracted text from a processed resume
 * 
 * @param {string} taskId - The ID of the processed resume task
 * @returns {Promise<Object>} The extracted text and metadata
 */
async function getResumeText(taskId) {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/resumes/${taskId}/text`);
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to get resume text');
    }
    
    return result.data;
  } catch (error) {
    console.error('Error getting resume text:', error);
    throw error;
  }
}

/**
 * Submit a customization request
 * 
 * @param {string} resumeId - The ID of the processed resume
 * @param {string} jobDescription - The job description text
 * @param {string} customizeLevel - Customization level (minimal, standard, comprehensive)
 * @returns {Promise<Object>} The customization task data
 */
async function customizeResume(resumeId, jobDescription, customizeLevel = 'standard') {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/resumes/customize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        resume_id: resumeId,
        job_description: jobDescription,
        customize_level: customizeLevel
      }),
      timeout: API_CONFIG.TIMEOUT
    });
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Customization request failed');
    }
    
    return result.data;
  } catch (error) {
    console.error('Error submitting customization:', error);
    throw error;
  }
}

/**
 * Get customization result
 * 
 * @param {string} taskId - The ID of the customization task
 * @returns {Promise<Object>} The customized resume data
 */
async function getCustomizationResult(taskId) {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/resumes/customization/${taskId}/result`);
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Failed to get customization result');
    }
    
    return result.data;
  } catch (error) {
    console.error('Error getting customization result:', error);
    throw error;
  }
}

/**
 * Check multiple task statuses in a single request
 * 
 * @param {Array<string>} taskIds - Array of task IDs to check
 * @param {boolean} includeMetadata - Whether to include full metadata
 * @returns {Promise<Object>} Batch status results
 */
async function batchCheckStatus(taskIds, includeMetadata = false) {
  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/batch/status`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        task_ids: taskIds,
        include_metadata: includeMetadata
      }),
      timeout: API_CONFIG.TIMEOUT
    });
    
    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error?.message || 'Batch status check failed');
    }
    
    return result.data;
  } catch (error) {
    console.error('Error checking batch status:', error);
    throw error;
  }
}

/**
 * Complete resume customization workflow
 * 
 * @param {File} resumeFile - The resume file to upload and customize
 * @param {string} jobDescription - The job description for customization
 * @param {function} progressCallback - Callback function for progress updates
 * @returns {Promise<Object>} The customized resume
 */
async function completeCustomizationWorkflow(resumeFile, jobDescription, progressCallback = null) {
  try {
    // Step 1: Upload resume
    progressCallback?.('upload', 0, 'Uploading resume...');
    const uploadData = await uploadResume(resumeFile);
    const resumeTaskId = uploadData.task_id;
    
    // Step 2: Wait for processing to complete
    progressCallback?.('processing', 10, 'Processing resume...');
    await pollTaskStatus(resumeTaskId, 'processing', progress => {
      progressCallback?.('processing', 10 + (progress * 0.3), `Processing resume: ${progress.toFixed(0)}%`);
    });
    
    // Step 3: Submit customization request
    progressCallback?.('customization', 40, 'Submitting customization request...');
    const customizationData = await customizeResume(resumeTaskId, jobDescription);
    const customizationTaskId = customizationData.task_id;
    
    // Step 4: Wait for customization to complete
    progressCallback?.('customization', 50, 'Customizing resume...');
    await pollTaskStatus(customizationTaskId, 'customization', progress => {
      progressCallback?.('customization', 50 + (progress * 0.4), `Customizing resume: ${progress.toFixed(0)}%`);
    });
    
    // Step 5: Get customization result
    progressCallback?.('result', 90, 'Retrieving customization result...');
    const result = await getCustomizationResult(customizationTaskId);
    
    progressCallback?.('complete', 100, 'Customization complete!');
    return result;
  } catch (error) {
    console.error('Error in customization workflow:', error);
    throw error;
  }
}

// Export all functions for use in React components
export {
  uploadResume,
  pollTaskStatus,
  getResumeText,
  customizeResume,
  getCustomizationResult,
  batchCheckStatus,
  completeCustomizationWorkflow
};

// Example React component usage:
/*
import React, { useState } from 'react';
import { completeCustomizationWorkflow } from './api/resume-customizer-api';

function ResumeCustomizerForm() {
  const [file, setFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ stage: '', percent: 0, message: '' });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const customizedResume = await completeCustomizationWorkflow(
        file, 
        jobDescription,
        (stage, percent, message) => {
          setProgress({ stage, percent, message });
        }
      );
      
      setResult(customizedResume);
    } catch (error) {
      setError(error.message || 'An error occurred during customization');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="resume-customizer-form">
      <h1>Resume Customizer</h1>
      
      {error && (
        <div className="error-alert">
          <p>{error}</p>
        </div>
      )}
      
      {loading ? (
        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress.percent}%` }}
            ></div>
          </div>
          <p>{progress.message}</p>
        </div>
      ) : !result ? (
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Upload Resume (PDF, DOCX, or TXT)</label>
            <input 
              type="file" 
              onChange={handleFileChange} 
              accept=".pdf,.docx,.doc,.txt" 
              required 
            />
          </div>
          
          <div className="form-group">
            <label>Job Description</label>
            <textarea 
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              rows="10"
              placeholder="Paste job description here..."
              required
            ></textarea>
          </div>
          
          <button 
            type="submit" 
            disabled={!file || !jobDescription}
            className="submit-button"
          >
            Customize Resume
          </button>
        </form>
      ) : (
        <div className="result-container">
          <h2>Your Customized Resume</h2>
          
          <div className="result-content">
            <pre>{result.customized_text}</pre>
          </div>
          
          <div className="optimization-metrics">
            <h3>Optimization Metrics</h3>
            <p>Keyword Match Rate: {(result.optimization_metrics.keyword_match_rate * 100).toFixed(0)}%</p>
            <p>ATS Score Improvement: {(result.optimization_metrics.ats_score_improvement * 100).toFixed(0)}%</p>
          </div>
          
          <button 
            onClick={() => setResult(null)} 
            className="reset-button"
          >
            Start Over
          </button>
        </div>
      )}
    </div>
  );
}

export default ResumeCustomizerForm;
*/
