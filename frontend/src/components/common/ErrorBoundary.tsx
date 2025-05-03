import React, { Component, ErrorInfo, ReactNode } from 'react';
import { ErrorState, ErrorFallbackProps } from '../../types/error.types';
import { logError } from '../../utils/errorUtils';
import { ErrorDisplay } from './ErrorDisplay';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  onReset?: () => void;
}

/**
 * Error boundary component that catches JavaScript errors in child components
 * Prevents the entire app from crashing and provides fallback UI
 * Follows React best practices for error boundaries
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: undefined,
      errorInfo: undefined
    };
  }

  /**
   * Update state to render fallback UI
   * This lifecycle is invoked after an error has been thrown by a descendant component
   */
  static getDerivedStateFromError(error: Error): Partial<ErrorState> {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error
    };
  }

  /**
   * Log error details and additional component stack information
   * This lifecycle is invoked after an error has been thrown by a descendant component
   */
  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error to our monitoring service
    logError(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: this.constructor.name
    });

    // Update state with error info for development debugging
    this.setState({
      errorInfo
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  /**
   * Reset error boundary state
   * Allows the application to recover from errors
   */
  resetErrorBoundary = (): void => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined
    });

    // Call custom reset handler if provided
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render(): ReactNode {
    const { hasError, error } = this.state;
    const { children, fallback: FallbackComponent } = this.props;

    if (hasError && error) {
      // Render custom fallback component if provided
      if (FallbackComponent) {
        return (
          <FallbackComponent
            error={error}
            resetErrorBoundary={this.resetErrorBoundary}
          />
        );
      }

      // Render default error display
      return (
        <ErrorDisplay
          error={error}
          onRetry={this.resetErrorBoundary}
          fullPage
        />
      );
    }

    // Render children when there's no error
    return children;
  }
}
