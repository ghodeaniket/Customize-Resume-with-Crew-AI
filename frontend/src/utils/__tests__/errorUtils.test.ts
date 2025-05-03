import { 
  createAppError, 
  parseApiError, 
  getErrorMapping, 
  isRecoverableError 
} from '../errorUtils';

describe('Error Utilities', () => {
  describe('createAppError', () => {
    it('creates an AppError with default values', () => {
      const error = createAppError('Test error');
      
      expect(error.message).toBe('Test error');
      expect(error.code).toBe('UNKNOWN_ERROR');
      expect(error.retry).toBe(true);
    });

    it('creates an AppError with custom values', () => {
      const error = createAppError('Network error', 'NETWORK_ERROR', { attempts: 3 }, false);
      
      expect(error.message).toBe('Network error');
      expect(error.code).toBe('NETWORK_ERROR');
      expect(error.context).toEqual({ attempts: 3 });
      expect(error.retry).toBe(false);
    });
  });

  describe('parseApiError', () => {
    it('returns AppError if already an AppError', () => {
      const appError = createAppError('Test error', 'VALIDATION_ERROR');
      const parsed = parseApiError(appError);
      
      expect(parsed).toBe(appError);
    });

    it('handles network errors', () => {
      const networkError = new Error('Network Error');
      const parsed = parseApiError(networkError);
      
      expect(parsed.code).toBe('NETWORK_ERROR');
      expect(parsed.message).toBe('Network connection error');
    });

    it('handles API validation errors (400)', () => {
      const apiError = {
        response: {
          status: 400,
          data: { detail: 'Invalid input' }
        }
      };
      const parsed = parseApiError(apiError);
      
      expect(parsed.code).toBe('VALIDATION_ERROR');
      expect(parsed.message).toBe('Invalid input');
    });

    it('handles authentication errors (401)', () => {
      const apiError = {
        response: {
          status: 401,
          data: {}
        }
      };
      const parsed = parseApiError(apiError);
      
      expect(parsed.code).toBe('AUTH_ERROR');
      expect(parsed.message).toBe('Authentication required');
    });

    it('handles server errors (500)', () => {
      const apiError = {
        response: {
          status: 500,
          data: {}
        }
      };
      const parsed = parseApiError(apiError);
      
      expect(parsed.code).toBe('SERVER_ERROR');
      expect(parsed.message).toBe('Server error');
    });

    it('handles unknown errors', () => {
      const unknownError = { message: 'Something went wrong' };
      const parsed = parseApiError(unknownError);
      
      expect(parsed.code).toBe('UNKNOWN_ERROR');
      expect(parsed.message).toBe('Something went wrong');
    });
  });

  describe('getErrorMapping', () => {
    it('returns correct mapping for known error code', () => {
      const mapping = getErrorMapping('NETWORK_ERROR');
      
      expect(mapping.code).toBe('NETWORK_ERROR');
      expect(mapping.userMessage).toContain('Unable to connect to the server');
      expect(mapping.recoverable).toBe(true);
    });

    it('returns unknown error mapping for undefined code', () => {
      const mapping = getErrorMapping(undefined);
      
      expect(mapping.code).toBe('UNKNOWN_ERROR');
      expect(mapping.userMessage).toContain('An unexpected error occurred');
    });

    it('returns unknown error mapping for unrecognized code', () => {
      const mapping = getErrorMapping('UNRECOGNIZED_CODE' as any);
      
      expect(mapping.code).toBe('UNKNOWN_ERROR');
    });
  });

  describe('isRecoverableError', () => {
    it('returns true for recoverable errors', () => {
      const error = createAppError('Network error', 'NETWORK_ERROR');
      
      expect(isRecoverableError(error)).toBe(true);
    });

    it('returns false when retry is explicitly false', () => {
      const error = createAppError('Fatal error', 'SERVER_ERROR', {}, false);
      
      expect(isRecoverableError(error)).toBe(false);
    });
  });
});
