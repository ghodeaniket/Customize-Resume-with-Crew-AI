import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApplicationState, useApplicationActions } from '../contexts/ApplicationContext';

/**
 * Customize page component - Second step in the workflow
 * Allows users to input job description for customization
 */
export const CustomizePage: React.FC = () => {
  const navigate = useNavigate();
  const { uploadTask } = useApplicationState();
  const { setCurrentStep, navigateToStep } = useApplicationActions();

  // Redirect to upload if no resume is uploaded
  React.useEffect(() => {
    if (!uploadTask?.text) {
      navigate('/');
    }
  }, [uploadTask, navigate]);

  const handleCustomizationComplete = () => {
    // This will be implemented when we have the customization component
    const success = navigateToStep('results');
    if (success) {
      navigate('/results');
    }
  };

  if (!uploadTask?.text) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Customize Your Resume
      </h1>
      
      <div className="bg-white rounded-lg shadow-sm p-8">
        <p className="text-gray-600 mb-6">
          Enter the job description for the position you're applying to, and we'll customize your resume to match.
        </p>
        
        {/* Job description input will be implemented later */}
        <div className="space-y-4">
          <div className="border rounded-lg p-6 bg-gray-50">
            <p className="text-gray-500">
              JobDescriptionInput component will be implemented here
            </p>
          </div>
          
          {/* Temporary button for navigation testing */}
          <button
            onClick={handleCustomizationComplete}
            className="w-full bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700 transition-colors"
          >
            Customize Resume (Test)
          </button>
        </div>
      </div>
    </div>
  );
};
