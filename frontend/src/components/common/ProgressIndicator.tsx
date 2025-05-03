import React from 'react';
import { useApplicationState } from '../../contexts/ApplicationContext';
import { ApplicationStep } from '../../types/application.types';

interface StepConfig {
  id: ApplicationStep;
  label: string;
  order: number;
}

/**
 * Progress indicator component showing current step in the workflow
 * Provides visual feedback about the user's progress
 */
export const ProgressIndicator: React.FC = () => {
  const { currentStep } = useApplicationState();

  const steps: StepConfig[] = [
    { id: 'upload', label: 'Upload', order: 1 },
    { id: 'customize', label: 'Job Details', order: 2 },
    { id: 'results', label: 'Results', order: 3 },
  ];

  const getStepStatus = (step: StepConfig): 'current' | 'completed' | 'upcoming' => {
    const currentStepOrder = steps.find(s => s.id === currentStep)?.order || 1;
    
    if (step.id === currentStep) return 'current';
    if (step.order < currentStepOrder) return 'completed';
    return 'upcoming';
  };

  return (
    <div className="w-full py-6">
      <div className="max-w-3xl mx-auto px-4">
        <nav aria-label="Progress" className="relative">
          {/* Progress line */}
          <div 
            className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200" 
            aria-hidden="true"
          />
          
          {/* Step indicators */}
          <ol className="relative z-10 flex justify-between">
            {steps.map((step) => {
              const status = getStepStatus(step);
              
              return (
                <li key={step.id} className="flex flex-col items-center">
                  {/* Step circle */}
                  <div
                    className={`
                      w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold
                      ${status === 'current' ? 'bg-blue-600 text-white' : ''}
                      ${status === 'completed' ? 'bg-blue-600 text-white' : ''}
                      ${status === 'upcoming' ? 'bg-gray-200 text-gray-600' : ''}
                    `}
                    aria-current={status === 'current' ? 'step' : undefined}
                  >
                    {status === 'completed' ? (
                      <svg 
                        className="w-6 h-6" 
                        fill="currentColor" 
                        viewBox="0 0 20 20"
                        aria-hidden="true"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      step.order
                    )}
                  </div>
                  
                  {/* Step label */}
                  <span
                    className={`
                      mt-2 text-sm font-medium
                      ${status === 'current' ? 'text-blue-600' : ''}
                      ${status === 'completed' ? 'text-blue-600' : ''}
                      ${status === 'upcoming' ? 'text-gray-500' : ''}
                    `}
                  >
                    {step.label}
                  </span>
                </li>
              );
            })}
          </ol>
        </nav>
      </div>
    </div>
  );
};
