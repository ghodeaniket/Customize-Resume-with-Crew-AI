import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApplicationState, useApplicationActions } from '../contexts/ApplicationContext';

/**
 * Results page component - Final step in the workflow
 * Displays the customized resume and allows downloading
 */
export const ResultsPage: React.FC = () => {
  const navigate = useNavigate();
  const { customizationResult } = useApplicationState();
  const { resetState } = useApplicationActions();

  // Redirect if no customization result
  React.useEffect(() => {
    if (!customizationResult) {
      navigate('/');
    }
  }, [customizationResult, navigate]);

  const handleStartOver = () => {
    resetState();
    navigate('/');
  };

  if (!customizationResult) {
    return null; // Will redirect in useEffect
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Your Optimized Resume
      </h1>
      
      <div className="bg-white rounded-lg shadow-sm p-8">
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            ATS Score Improvement
          </h2>
          
          <div className="grid grid-cols-3 gap-4 mb-8">
            <div className="text-center">
              <p className="text-sm text-gray-600">Original Score</p>
              <p className="text-2xl font-bold text-red-600">54%</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Optimized Score</p>
              <p className="text-2xl font-bold text-green-600">89%</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Improvement</p>
              <p className="text-2xl font-bold text-blue-600">+35%</p>
            </div>
          </div>
        </div>
        
        {/* Comparison view will be implemented later */}
        <div className="border rounded-lg p-6 bg-gray-50 mb-8">
          <p className="text-gray-500">
            ComparisonView component will be implemented here
          </p>
        </div>
        
        <div className="flex justify-between items-center">
          <button
            onClick={handleStartOver}
            className="text-blue-600 hover:text-blue-700"
          >
            Start Over
          </button>
          
          <div className="space-x-4">
            <button
              className="bg-gray-200 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-300 transition-colors"
            >
              Download TXT
            </button>
            <button
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Download PDF
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
