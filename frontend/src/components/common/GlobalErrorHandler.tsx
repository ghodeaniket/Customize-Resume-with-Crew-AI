import React from 'react';
import { useApplicationState, useApplicationActions } from '../../contexts/ApplicationContext';
import { ErrorToast } from './ErrorToast';

/**
 * Global error handler component
 * Displays errors from the application context as toast notifications
 */
export const GlobalErrorHandler: React.FC = () => {
  const { error } = useApplicationState();
  const { clearError } = useApplicationActions();

  return (
    <ErrorToast
      error={error ?? null}
      onDismiss={clearError}
      autoHideDuration={5000}
    />
  );
};
