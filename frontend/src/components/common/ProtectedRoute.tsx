import React from 'react';
import { Navigate } from 'react-router-dom';
import { useApplicationState } from '../../contexts/ApplicationContext';
import { ApplicationStep } from '../../types/application.types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredStep: ApplicationStep;
  redirectTo?: string;
}

/**
 * Protected route component that ensures users follow the correct workflow
 * Redirects users if they try to access steps out of order
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredStep,
  redirectTo = '/'
}) => {
  const { uploadTask, customizationResult } = useApplicationState();

  // Check if user has completed previous steps
  const canAccessStep = (): boolean => {
    switch (requiredStep) {
      case 'upload':
        // Upload page is always accessible
        return true;
      case 'customize':
        // Need uploaded resume text to access customize
        return !!uploadTask?.text;
      case 'results':
        // Need customization result to access results
        return !!customizationResult;
      default:
        return false;
    }
  };

  if (!canAccessStep()) {
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children}</>;
};
