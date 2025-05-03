/**
 * Error types and interfaces for the application
 */

/** Application error codes for categorizing errors */
export type ErrorCode = 
  | 'NETWORK_ERROR'
  | 'VALIDATION_ERROR'
  | 'FILE_TOO_LARGE'
  | 'INVALID_FILE_TYPE'
  | 'PROCESSING_ERROR'
  | 'AUTH_ERROR'
  | 'SERVER_ERROR'
  | 'UNKNOWN_ERROR';

/** Extended error interface with additional metadata */
export interface AppError extends Error {
  code?: ErrorCode;
  context?: Record<string, unknown>;
  statusCode?: number;
  retry?: boolean;
}

/** Error boundary fallback props */
export interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

/** Error mapping configuration */
export interface ErrorMapping {
  code: ErrorCode;
  message: string;
  userMessage: string;
  recoverable: boolean;
  action?: string;
}

/** Error state for components */
export interface ErrorState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}
