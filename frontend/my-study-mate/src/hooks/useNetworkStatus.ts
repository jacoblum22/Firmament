import { useState, useEffect, useRef, useCallback } from 'react';
import NetworkUtils, { HealthStatus } from '../utils/networkUtils';
import config from '../config';

export interface ConnectionState {
  isOnline: boolean;
  isBackendReachable: boolean;
  isInitializing: boolean;
  latency?: number;
  lastChecked: Date;
  errorCount: number;
  retryAttempt: number;
}

export const useNetworkStatus = () => {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isOnline: navigator.onLine,
    isBackendReachable: false, // Start as false until first health check
    isInitializing: true, // Start in initializing state
    lastChecked: new Date(),
    errorCount: 0,
    retryAttempt: 0
  });

  const networkUtils = useRef<NetworkUtils | null>(null);
  // use the correct return type from setTimeout instead of a plain number
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // … elsewhere in your effect/cleanup …
        clearTimeout(retryTimeoutRef.current as ReturnType<typeof setTimeout>);
  useEffect(() => {
    // Initialize network utils
    networkUtils.current = NetworkUtils.getInstance(config.getApiBaseUrl());

    const scheduleRetryInternal = () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }

      setConnectionState(prev => {
        const nextRetryAttempt = prev.retryAttempt + 1;
        
        // Exponential backoff: 5s, 10s, 20s, 40s, max 60s
        const delay = Math.min(5000 * Math.pow(2, nextRetryAttempt - 1), 60000);
        
        retryTimeoutRef.current = window.setTimeout(() => {
          checkBackendHealthInternal();
        }, delay);

        return {
          ...prev,
          retryAttempt: nextRetryAttempt
        };
      });
    };

    const checkBackendHealthInternal = async () => {
      if (!networkUtils.current || !navigator.onLine) {
        return;
      }

      try {
        const healthStatus: HealthStatus = await networkUtils.current.checkBackendHealth();
        
        setConnectionState(prev => ({
          ...prev,
          isBackendReachable: healthStatus.isOnline,
          isInitializing: false, // First health check completed
          latency: healthStatus.latency,
          lastChecked: healthStatus.lastChecked,
          errorCount: healthStatus.errorCount,
          retryAttempt: healthStatus.isOnline ? 0 : prev.retryAttempt
        }));

        // If backend is down, schedule a retry
        if (!healthStatus.isOnline) {
          scheduleRetryInternal();
        }
      } catch (error) {
        console.error('Health check failed:', error);
        setConnectionState(prev => ({
          ...prev,
          isBackendReachable: false,
          isInitializing: false, // First health check completed
          lastChecked: new Date(),
          errorCount: prev.errorCount + 1
        }));
        scheduleRetryInternal();
      }
    };

    // Listen for browser online/offline events
    const handleOnline = () => {
      setConnectionState(prev => ({
        ...prev,
        isOnline: true,
        retryAttempt: 0
      }));
      
      // Check backend when browser comes online
      checkBackendHealthInternal();
    };

    const handleOffline = () => {
      setConnectionState(prev => ({
        ...prev,
        isOnline: false,
        isBackendReachable: false,
        isInitializing: false // Clear initializing when going offline
      }));
    };

    // Set up event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Initial backend health check
    checkBackendHealthInternal();

    // Set up periodic health checks
    const healthCheckInterval = setInterval(checkBackendHealthInternal, 30000); // Check every 30 seconds

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(healthCheckInterval);
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      networkUtils.current?.stopHealthCheck();
    };
  }, []);

  const forceHealthCheck = useCallback(async () => {
    if (!networkUtils.current || !navigator.onLine) {
      return;
    }

    try {
      const healthStatus: HealthStatus = await networkUtils.current.checkBackendHealth();
      
      setConnectionState(prev => ({
        ...prev,
        isBackendReachable: healthStatus.isOnline,
        isInitializing: false, // Manual health check completed
        latency: healthStatus.latency,
        lastChecked: healthStatus.lastChecked,
        errorCount: healthStatus.errorCount,
        retryAttempt: healthStatus.isOnline ? 0 : prev.retryAttempt
      }));
    } catch (error) {
      console.error('Health check failed:', error);
      setConnectionState(prev => ({
        ...prev,
        isBackendReachable: false,
        isInitializing: false, // Manual health check completed
        lastChecked: new Date(),
        errorCount: prev.errorCount + 1
      }));
    }
  }, []);

  const isFullyOnline = connectionState.isOnline && connectionState.isBackendReachable;

  return {
    connectionState,
    isFullyOnline,
    isOnline: connectionState.isOnline,
    isBackendReachable: connectionState.isBackendReachable,
    isInitializing: connectionState.isInitializing,
    latency: connectionState.latency,
    errorCount: connectionState.errorCount,
    retryAttempt: connectionState.retryAttempt,
    forceHealthCheck
  };
};
