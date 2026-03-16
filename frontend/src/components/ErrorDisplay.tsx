import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ErrorDisplayProps {
  error: string | null;
  onDismiss?: () => void;
  className?: string;
  type?: 'error' | 'warning' | 'info';
  showIcon?: boolean;
  actionButton?: {
    label: string;
    action: () => void;
  };
}

interface ErrorInfo {
  error: string;
  details?: string;
  user_action?: string;
  error_code?: string;
  recoverable?: boolean;
  supported_formats?: string[];
}

const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onDismiss,
  className = '',
  type = 'error',
  showIcon = true,
  actionButton
}) => {
  if (!error) return null;

  // Try to parse error as structured error object
  let errorInfo: ErrorInfo;
  try {
    const parsed = JSON.parse(error);
    errorInfo = parsed;
  } catch {
    // If parsing fails, treat as simple string
    errorInfo = { error: error };
  }

  const getErrorColors = () => {
    switch (type) {
      case 'warning':
        return {
          border: 'border-yellow-400',
          bg: 'bg-yellow-50',
          text: 'text-yellow-800',
          icon: 'text-yellow-600'
        };
      case 'info':
        return {
          border: 'border-blue-400',
          bg: 'bg-blue-50',
          text: 'text-blue-800',
          icon: 'text-blue-600'
        };
      default:
        return {
          border: 'border-red-400',
          bg: 'bg-red-50',
          text: 'text-red-800',
          icon: 'text-red-600'
        };
    }
  };

  const colors = getErrorColors();

  const getIcon = () => {
    switch (type) {
      case 'warning':
        return (
          <svg className={`h-5 w-5 ${colors.icon}`} viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
        return (
          <svg className={`h-5 w-5 ${colors.icon}`} viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className={`h-5 w-5 ${colors.icon}`} viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3 }}
        className={`border-l-4 p-4 rounded-lg shadow-md ${colors.border} ${colors.bg} ${className}`}
        role="alert"
        aria-live="polite"
      >
        <div className="flex items-start">
          {showIcon && (
            <div className="flex-shrink-0 mr-3">
              {getIcon()}
            </div>
          )}
          
          <div className="flex-1">
            <div className={`text-sm font-medium ${colors.text}`}>
              {errorInfo.error}
            </div>
            
            {errorInfo.details && (
              <div className={`mt-1 text-sm ${colors.text} opacity-90`}>
                {errorInfo.details}
              </div>
            )}
            
            {errorInfo.user_action && (
              <div className={`mt-2 text-sm font-medium ${colors.text}`}>
                💡 {errorInfo.user_action}
              </div>
            )}
            
            {errorInfo.supported_formats && (
              <div className={`mt-2 text-xs ${colors.text} opacity-75`}>
                Supported formats: {errorInfo.supported_formats.map(format => format.toUpperCase()).join(', ')}
              </div>
            )}
          </div>
          
          <div className="flex-shrink-0 ml-3 flex space-x-2">
            {actionButton && (
              <button
                onClick={actionButton.action}
                className={`text-xs font-medium ${colors.text} hover:opacity-80 px-2 py-1 rounded border border-current transition-opacity duration-200`}
              >
                {actionButton.label}
              </button>
            )}
            
            {onDismiss && (
              <button
                onClick={onDismiss}
                className={`${colors.text} hover:opacity-70 transition-opacity duration-200`}
                aria-label="Dismiss error"
              >
                <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default ErrorDisplay;
