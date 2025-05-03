import { AppError, ErrorCode, ErrorMapping } from '../types/error.types';

/**
 * Error mapping configuration for user-friendly messages
 * Maps technical errors to user-understandable messages
 */
const errorMappings: ErrorMapping[] = [
  {
    code: 'NETWORK_ERROR',
    message: 'Network connection error',
    userMessage: 'Unable to connect to the server. Please check your internet connection and try again.',
    recoverable: true,
    action: 'Retry'
  },
  {
    code: 'VALIDATION_ERROR',
    message: 'Validation failed',
    userMessage: 'The information provided is not valid. Please check your input and try again.',
    recoverable: true,
    action: 'Fix and retry'
  },
  {
    code: 'FILE_TOO_LARGE',
    message: 'File size exceeds limit',
    userMessage: 'The file you\'re trying to upload is too large. Please use a file smaller than 10MB.',
    recoverable: true,
    action: 'Choose another file'
  },
  {
    code: 'INVALID_FILE_TYPE',
    message: 'Invalid file type',
    userMessage: 'Please upload a PDF, DOCX, or TXT file.',
    recoverable: true,
    action: 'Choose another file'
  },
  {
    code: 'PROCESSING_ERROR',
    message: 'Error processing request',
    userMessage: 'We encountered an error while processing your request. Please try again.',
    recoverable: true,
    action: 'Retry'
  },
  {
    code: 'AUTH_ERROR',
    message: 'Authentication error',
    userMessage: 'Your session has expired. Please sign in again.',
    recoverable: true,
    action: 'Sign in'
  },
  {
    code: 'SERVER_ERROR',
    message: 'Server error',
    userMessage: 'Our servers are experiencing issues. Please try again later.',
    recoverable: true,
    action: 'Retry later'
  },
  {
    code: 'UNKNOWN_ERROR',
    message: 'Unknown error',
    userMessage: 'An unexpected error occurred. Please try again.',
    recoverable: true,
    action: 'Retry'
  }
];

/**
 * Get user-friendly error mapping for a given error code
 */
export const getErrorMapping = (code?: ErrorCode): ErrorMapping => {
  if (!code) {
    return errorMappings.find(m => m.code === 'UNKNOWN_ERROR')!;
  }
  
  return errorMappings.find(m => m.code === code) || errorMappings.find(m => m.code === 'UNKNOWN_ERROR')!;
};

/**
 * Create an application error with extended metadata
 */
export const createAppError = (
  message: string,
  code: ErrorCode = 'UNKNOWN_ERROR',
  context?: Record<string, unknown>,
  retry: boolean = true
): AppError => {
  const error = new Error(message) as AppError;
  error.code = code;
  error.context = context;
  error.retry = retry;
  return error;
};

/**
 * Parse error from API response
 * Handles different error formats from the backend
 */
export const parseApiError = (error: any): AppError => {
  // If it's already an AppError, return it
  if (error.code && error.message) {
    return error;
  }

  // Handle network errors
  if (error.message === 'Network Error' || !navigator.onLine) {
    return createAppError('Network connection error', 'NETWORK_ERROR');
  }

  // Handle API response errors
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return createAppError(
          data.detail || 'Invalid request',
          'VALIDATION_ERROR',
          { status, data }
        );
      case 401:
      case 403:
        return createAppError(
          'Authentication required',
          'AUTH_ERROR',
          { status }
        );
      case 404:
        return createAppError(
          'Resource not found',
          'PROCESSING_ERROR',
          { status }
        );
      case 500:
      case 502:
      case 503:
        return createAppError(
          'Server error',
          'SERVER_ERROR',
          { status },
          true
        );
      default:
        return createAppError(
          data.detail || 'Request failed',
          'PROCESSING_ERROR',
          { status, data }
        );
    }
  }

  // Handle unknown errors
  return createAppError(
    error.message || 'Unknown error occurred',
    'UNKNOWN_ERROR',
    { originalError: error }
  );
};

/**
 * Log error to monitoring service
 * In production, this would send to a service like Sentry
 */
export const logError = (error: Error, context?: Record<string, unknown>): void => {
  console.error('Application Error:', {
    message: error.message,
    stack: error.stack,
    context,
    timestamp: new Date().toISOString(),
  });

  // In production, send to error monitoring service
  // Example: Sentry.captureException(error, { extra: context });
};

/**
 * Check if an error is recoverable
 */
export const isRecoverableError = (error: AppError): boolean => {
  if (error.retry === false) return false;
  
  const mapping = getErrorMapping(error.code);
  return mapping.recoverable;
};
