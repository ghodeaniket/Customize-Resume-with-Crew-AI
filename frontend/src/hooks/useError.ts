import { useState, useCallback } from 'react';
import { AppError } from '../types/error.types';
import { logError, parseApiError } from '../utils/errorUtils';

/**
 * Custom hook for handling errors at the component level
 * Provides consistent error handling pattern across the application
 */
export const useError = () => {
  const [error, setError] = useState<AppError | null>(null);

  /**
   * Handle error with logging and state update
   */
  const handleError = useCallback((err: any) => {
    const appError = parseApiError(err);
    
    // Log the error
    logError(appError, {
      component: 'useError hook',
      timestamp: new Date().toISOString()
    });
    
    setError(appError);
  }, []);

  /**
   * Clear current error
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Reset error state with optional callback
   */
  const resetError = useCallback((callback?: () => void) => {
    clearError();
    if (callback) {
      callback();
    }
  }, [clearError]);

  return {
    error,
    handleError,
    clearError,
    resetError,
    hasError: !!error
  };
};
