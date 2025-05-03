import React from 'react';
import { AppError } from '../../types/error.types';
import { getErrorMapping, isRecoverableError } from '../../utils/errorUtils';

interface ErrorDisplayProps {
  error: Error | AppError;
  onRetry?: () => void;
  fullPage?: boolean;
  className?: string;
}

/**
 * Reusable error display component
 * Shows user-friendly error messages with optional retry functionality
 */
export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onRetry,
  fullPage = false,
  className = ''
}) => {
  const appError = error as AppError;
  const errorMapping = getErrorMapping(appError.code);
  const isRecoverable = isRecoverableError(appError);

  // Get the appropriate icon based on error type
  const getErrorIcon = () => {
    switch (appError.code) {
      case 'NETWORK_ERROR':
        return (
          <svg 
            className="h-12 w-12 text-red-500" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
            aria-hidden="true"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" 
            />
          </svg>
        );
      case 'FILE_TOO_LARGE':
      case 'INVALID_FILE_TYPE':
        return (
          <svg 
            className="h-12 w-12 text-yellow-500" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
            aria-hidden="true"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" 
            />
          </svg>
        );
      default:
        return (
          <svg 
            className="h-12 w-12 text-red-500" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
            aria-hidden="true"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
            />
          </svg>
        );
    }
  };

  const content = (
    <div className="flex flex-col items-center text-center">
      <div className="mb-4">
        {getErrorIcon()}
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Oops! Something went wrong
      </h3>
      
      <p className="text-gray-600 mb-6 max-w-md">
        {errorMapping.userMessage}
      </p>
      
      {isRecoverable && onRetry && (
        <button
          onClick={onRetry}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors inline-flex items-center"
        >
          <svg 
            className="w-4 h-4 mr-2" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
            />
          </svg>
          {errorMapping.action || 'Try Again'}
        </button>
      )}
      
      {/* Error details for debugging (only in development) */}
      {process.env.NODE_ENV === 'development' && (
        <details className="mt-6 text-left w-full max-w-md">
          <summary className="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
            Technical Details
          </summary>
          <pre className="mt-2 text-xs bg-gray-100 p-4 rounded overflow-auto">
            {JSON.stringify({
              message: error.message,
              code: appError.code,
              context: appError.context,
              stack: error.stack?.split('\n').slice(0, 5)
            }, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );

  if (fullPage) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        {content}
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm p-8 ${className}`}>
      {content}
    </div>
  );
};
