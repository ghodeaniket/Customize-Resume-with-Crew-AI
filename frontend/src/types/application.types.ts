/**
 * Type definitions for the Resume Customizer application
 */

/** Task status types */
export type TaskStatus = 'created' | 'processing' | 'completed' | 'failed';

/** Customization level options */
export type CustomizationLevel = 'minimal' | 'standard' | 'comprehensive';

/** Resume processing task interface */
export interface ResumeTask {
  task_id: string;
  filename: string;
  status: TaskStatus;
  progress: number;
  message?: string;
  error?: string;
  processing_time_ms?: number;
  text?: string;
}

/** Customization request interface */
export interface CustomizationRequest {
  resume_id: string;
  job_description: string;
  customize_level?: CustomizationLevel;
}

/** Customization task interface */
export interface CustomizationTask {
  task_id: string;
  resume_id: string;
  status: TaskStatus;
  progress: number;
  customize_level?: CustomizationLevel;
  message?: string;
  error?: string;
  processing_time_ms?: number;
  result_available?: boolean;
}

/** Customization result interface */
export interface CustomizationResult {
  task_id: string;
  status: TaskStatus;
  result: string;
  metadata: {
    processing_time_ms: number;
    customize_level: string;
    completion_time: number;
    job_title?: string;
  };
}

/** Application workflow steps */
export type ApplicationStep = 'upload' | 'customize' | 'results';

/** Application state interface */
export interface ApplicationState {
  currentStep: ApplicationStep;
  uploadTask?: ResumeTask;
  customizationTask?: CustomizationTask;
  customizationResult?: CustomizationResult;
  error?: Error;
}

/** Application actions interface */
export interface ApplicationActions {
  setCurrentStep: (step: ApplicationStep) => void;
  setUploadTask: (task: ResumeTask) => void;
  setCustomizationTask: (task: CustomizationTask) => void;
  setCustomizationResult: (result: CustomizationResult) => void;
  setError: (error: Error | undefined) => void;
  resetState: () => void;
  navigateToStep: (step: ApplicationStep) => boolean;
  clearError: () => void;
}

/** Context value type that combines state and actions */
export interface ApplicationContextValue {
  state: ApplicationState;
  actions: ApplicationActions;
}
