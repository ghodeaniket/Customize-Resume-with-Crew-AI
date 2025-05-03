import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import {
  ApplicationState,
  ApplicationActions,
  ApplicationContextValue,
  ApplicationStep,
  ResumeTask,
  CustomizationTask,
  CustomizationResult,
} from '../types/application.types';

/**
 * Initial state for the application
 * Starts at the upload step with no data
 */
const initialState: ApplicationState = {
  currentStep: 'upload',
  uploadTask: undefined,
  customizationTask: undefined,
  customizationResult: undefined,
  error: undefined,
};

/**
 * Context with undefined as initial value
 * Using undefined allows us to detect if the context is used outside of the provider
 */
const ApplicationContext = createContext<ApplicationContextValue | undefined>(undefined);

/**
 * ApplicationProvider props interface
 */
interface ApplicationProviderProps {
  children: ReactNode;
}

/**
 * ApplicationProvider component that manages the application state
 * Provides both state values and actions to modify the state
 */
export const ApplicationProvider: React.FC<ApplicationProviderProps> = ({ children }) => {
  const [state, setState] = useState<ApplicationState>(initialState);

  /**
   * Sets the current step in the application workflow
   */
  const setCurrentStep = useCallback((step: ApplicationStep) => {
    setState(prevState => ({
      ...prevState,
      currentStep: step,
    }));
  }, []);

  /**
   * Updates the upload task data
   */
  const setUploadTask = useCallback((task: ResumeTask) => {
    setState(prevState => ({
      ...prevState,
      uploadTask: task,
    }));
  }, []);

  /**
   * Updates the customization task data
   */
  const setCustomizationTask = useCallback((task: CustomizationTask) => {
    setState(prevState => ({
      ...prevState,
      customizationTask: task,
    }));
  }, []);

  /**
   * Updates the customization result data
   */
  const setCustomizationResult = useCallback((result: CustomizationResult) => {
    setState(prevState => ({
      ...prevState,
      customizationResult: result,
    }));
  }, []);

  /**
   * Sets an error in the application state
   */
  const setError = useCallback((error: Error | undefined) => {
    setState(prevState => ({
      ...prevState,
      error,
    }));
  }, []);

  /**
   * Resets the application state to initial values
   */
  const resetState = useCallback(() => {
    setState(initialState);
  }, []);

  /**
   * Clears the current error
   */
  const clearError = useCallback(() => {
    setState(prevState => ({
      ...prevState,
      error: undefined,
    }));
  }, []);

  /**
   * Navigates to a specific step, validating the transition
   * Returns true if navigation was successful, false otherwise
   */
  const navigateToStep = useCallback((step: ApplicationStep): boolean => {
    // Check if the requested navigation is valid based on current state
    if (step === 'customize' && !state.uploadTask?.text) {
      // Cannot navigate to customize without uploaded resume text
      return false;
    }

    if (step === 'results' && !state.customizationResult) {
      // Cannot navigate to results without customization result
      return false;
    }

    setCurrentStep(step);
    return true;
  }, [state.uploadTask, state.customizationResult, setCurrentStep]);

  // Combine all actions into a single object
  const actions: ApplicationActions = {
    setCurrentStep,
    setUploadTask,
    setCustomizationTask,
    setCustomizationResult,
    setError,
    resetState,
    navigateToStep,
    clearError,
  };

  // Create the context value
  const contextValue: ApplicationContextValue = {
    state,
    actions,
  };

  return (
    <ApplicationContext.Provider value={contextValue}>
      {children}
    </ApplicationContext.Provider>
  );
};

/**
 * Custom hook to use the application context
 * Throws an error if used outside of the ApplicationProvider
 */
export const useApplication = (): ApplicationContextValue => {
  const context = useContext(ApplicationContext);
  
  if (context === undefined) {
    throw new Error('useApplication must be used within an ApplicationProvider');
  }
  
  return context;
};

/**
 * Custom hook to just get the application state
 * Useful when components only need to read state
 */
export const useApplicationState = (): ApplicationState => {
  const { state } = useApplication();
  return state;
};

/**
 * Custom hook to just get the application actions
 * Useful when components only need to dispatch actions
 */
export const useApplicationActions = (): ApplicationActions => {
  const { actions } = useApplication();
  return actions;
};
