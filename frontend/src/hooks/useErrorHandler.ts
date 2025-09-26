import { useCallback } from 'react';
import { notificationService } from '@/services/notificationService';

interface ErrorHandlerOptions {
  showNotification?: boolean;
  customMessage?: string;
  logToAnalytics?: boolean;
  context?: string;
}

export const useErrorHandler = () => {
  const handleError = useCallback((error: any, options: ErrorHandlerOptions = {}) => {
    const {
      showNotification = true,
      customMessage,
      logToAnalytics = true,
      context = 'Unknown',
    } = options;

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error(`[${context}]`, error);
    }

    // Log to analytics
    if (logToAnalytics) {
      // Analytics logging removed
    }

    // Show user-friendly notification
    if (showNotification) {
      const message = getErrorMessage(error, customMessage);
      notificationService.error(message);
    }

    return message;
  }, []);

  return { handleError };
};

// Helper function to extract user-friendly error messages
function getErrorMessage(error: any, customMessage?: string): string {
  if (customMessage) return customMessage;

  // Handle Axios errors
  if (error?.response) {
    const status = error.response.status;
    const data = error.response.data;

    // Check for specific error messages from backend
    if (data?.detail) return data.detail;
    if (data?.message) return data.message;
    if (data?.error) return data.error;

    // Handle common HTTP status codes
    switch (status) {
      case 400:
        return 'Invalid request. Please check your input and try again.';
      case 401:
        return 'Authentication required. Please log in.';
      case 403:
        return 'You don\'t have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return 'This action conflicts with existing data.';
      case 422:
        return 'The provided data is invalid. Please check and try again.';
      case 429:
        return 'Too many requests. Please slow down and try again.';
      case 500:
        return 'Server error. Please try again later.';
      case 502:
      case 503:
      case 504:
        return 'Service temporarily unavailable. Please try again later.';
      default:
        return `An error occurred (${status}). Please try again.`;
    }
  }

  // Handle network errors
  if (error?.code === 'ECONNABORTED') {
    return 'Request timeout. Please check your connection and try again.';
  }
  
  if (error?.message === 'Network Error' || !window.navigator.onLine) {
    return 'Network error. Please check your internet connection.';
  }

  // Handle validation errors
  if (error?.name === 'ValidationError') {
    return 'Please check your input and try again.';
  }

  // Default error message
  return error?.message || 'An unexpected error occurred. Please try again.';
}

export default useErrorHandler;
