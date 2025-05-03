import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApplicationActions } from '../contexts/ApplicationContext';

/**
 * Upload page component - First step in the workflow
 * Allows users to upload their resume
 */
export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const { setCurrentStep } = useApplicationActions();

  const handleUploadComplete = (taskId: string) => {
    // This will be implemented when we have the upload component
    console.log('Upload complete:', taskId);
    setCurrentStep('customize');
    navigate('/customize');
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Upload Your Resume
      </h1>
      
      <div className="bg-white rounded-lg shadow-sm p-8">
        <p className="text-gray-600 mb-6">
          Upload your resume in PDF, DOCX, or TXT format to get started.
        </p>
        
        {/* Upload component will be implemented later */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <p className="text-gray-500">
            ResumeUploader component will be implemented here
          </p>
          
          {/* Temporary button for navigation testing */}
          <button
            onClick={() => handleUploadComplete('test-id')}
            className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            Continue (Test)
          </button>
        </div>
      </div>
    </div>
  );
};
