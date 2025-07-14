import React from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useNetworkStatus } from '../hooks/useNetworkStatus';

interface ConnectionStatusProps {
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ className = '' }) => {
  const { 
    isOnline, 
    isBackendReachable, 
    isFullyOnline, 
    latency, 
    retryAttempt,
    forceHealthCheck 
  } = useNetworkStatus();

  // Don't show anything if everything is working fine
  if (isFullyOnline) {
    return null;
  }

  const getStatusInfo = () => {
    if (!isOnline) {
      return {
        message: 'No internet connection',
        description: 'Please check your network connection and try again.',
        type: 'offline' as const,
        showRetry: false
      };
    }

    if (!isBackendReachable) {
      return {
        message: 'StudyMate is temporarily unavailable',
        description: retryAttempt > 0 
          ? `Trying to reconnect... (attempt ${retryAttempt})`
          : 'StudyMate services are currently unavailable. Please try again in a moment.',
        type: 'backend-down' as const,
        showRetry: true
      };
    }

    return {
      message: 'Connection is slow',
      description: 'StudyMate may respond slowly due to connection issues.',
      type: 'degraded' as const,
      showRetry: true
    };
  };

  const statusInfo = getStatusInfo();

  const getStatusColor = () => {
    switch (statusInfo.type) {
      case 'offline':
        return 'bg-red-100 border-red-400 text-red-800';
      case 'backend-down':
        return 'bg-orange-100 border-orange-400 text-orange-800';
      case 'degraded':
        return 'bg-yellow-100 border-yellow-400 text-yellow-800';
      default:
        return 'bg-gray-100 border-gray-400 text-gray-800';
    }
  };

  const getIconColor = () => {
    switch (statusInfo.type) {
      case 'offline':
        return 'text-red-500';
      case 'backend-down':
        return 'text-orange-500';
      case 'degraded':
        return 'text-yellow-500';
      default:
        return 'text-gray-500';
    }
  };

  return createPortal(
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -50 }}
        className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 ${className}`}
        role="alert"
        aria-live="polite"
        aria-atomic="true"
      >
        <div className={`border-l-4 p-4 rounded-lg shadow-lg backdrop-blur-sm ${getStatusColor()}`}>
          <div className="flex items-center">
            <div className="flex-shrink-0" aria-hidden="true">
              {statusInfo.type === 'offline' ? (
                <svg className={`h-5 w-5 ${getIconColor()}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <title>No internet connection</title>
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className={`h-5 w-5 ${getIconColor()}`} viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                  <title>Connection warning</title>
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium">
                {statusInfo.message}
              </h3>
              <p className="text-xs mt-1 opacity-80">
                {statusInfo.description}
              </p>
              {latency && (
                <p className="text-xs mt-1 opacity-60">
                  Response time: {latency}ms
                </p>
              )}
            </div>
            {statusInfo.showRetry && (
              <div className="ml-4">
                <button
                  onClick={forceHealthCheck}
                  className="text-xs bg-white bg-opacity-20 hover:bg-opacity-30 px-2 py-1 rounded transition-colors duration-200"
                  aria-label="Retry connection to StudyMate"
                  type="button"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>,
    document.body
  );
};
