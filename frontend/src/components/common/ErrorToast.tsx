import React, { useEffect, useState } from 'react';
import { AppError } from '../../types/error.types';
import { getErrorMapping } from '../../utils/errorUtils';

interface ErrorToastProps {
  error: Error | AppError | null;
  onDismiss: () => void;
  autoHideDuration?: number;
}

/**
 * Toast notification for displaying non-critical errors
 * Automatically dismisses after a specified duration
 */
export const ErrorToast: React.FC<ErrorToastProps> = ({
  error,
  onDismiss,
  autoHideDuration = 5000
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (error) {
      setIsVisible(true);
      
      // Auto-dismiss after duration
      const timer = setTimeout(() => {
        handleDismiss();
      }, autoHideDuration);

      return () => clearTimeout(timer);
    } else {
      setIsVisible(false);
    }
  }, [error, autoHideDuration]);

  const handleDismiss = () => {
    setIsVisible(false);
    // Small delay before calling onDismiss for animation
    setTimeout(onDismiss, 300);
  };

  if (!error || !isVisible) return null;

  const appError = error as AppError;
  const errorMapping = getErrorMapping(appError.code);

  return (
    <div 
      className={`
        fixed bottom-4 right-4 z-50 max-w-sm w-full
        transform transition-all duration-300 ease-in-out
        ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'}
      `}
      role="alert"
      aria-live="polite"
    >
      <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded shadow-lg">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg 
              className="h-5 w-5 text-red-400" 
              viewBox="0 0 20 20" 
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">
              {errorMapping.userMessage}
            </p>
          </div>
          <div className="ml-auto pl-3">
            <div className="-mx-1.5 -my-1.5">
              <button
                onClick={handleDismiss}
                className="inline-flex rounded-md p-1.5 text-red-500 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-red-50 focus:ring-red-600"
                aria-label="Dismiss"
              >
                <svg 
                  className="h-5 w-5" 
                  viewBox="0 0 20 20" 
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
