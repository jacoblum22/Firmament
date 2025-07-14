// Network utility functions for improved error handling and resilience

export interface NetworkError extends Error {
  code: 'NETWORK_ERROR' | 'TIMEOUT' | 'SERVER_ERROR' | 'CLIENT_ERROR' | 'UNKNOWN';
  statusCode?: number;
  isRetryable: boolean;
}

export interface RetryOptions {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryCondition?: (error: NetworkError) => boolean;
}

export interface HealthStatus {
  isOnline: boolean;
  lastChecked: Date;
  latency?: number;
  errorCount: number;
}

class NetworkUtils {
  private static instances: Map<string, NetworkUtils> = new Map();
  private healthStatus: HealthStatus = {
    isOnline: true,
    lastChecked: new Date(),
    errorCount: 0
  };
  private healthCheckInterval: number | null = null;
  private baseUrl: string;

  private constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
    // Remove automatic health checks - let the hook manage this
  }

  public static getInstance(baseUrl: string): NetworkUtils {
    // Check if an instance already exists for this baseUrl
    if (!NetworkUtils.instances.has(baseUrl)) {
      NetworkUtils.instances.set(baseUrl, new NetworkUtils(baseUrl));
    }
    return NetworkUtils.instances.get(baseUrl)!;
  }

  /**
   * Clear all instances (useful for testing or cleanup)
   */
  public static clearInstances(): void {
    // Stop health checks for all instances before clearing
    NetworkUtils.instances.forEach(instance => {
      instance.stopHealthCheck();
    });
    NetworkUtils.instances.clear();
  }

  /**
   * Enhanced fetch with automatic retry and better error handling
   */
  public async fetchWithRetry(
    url: string,
    options: RequestInit = {},
    retryOptions: Partial<RetryOptions> = {}
  ): Promise<Response> {
    const defaultRetryOptions: RetryOptions = {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 10000,
      backoffMultiplier: 2,
      retryCondition: (error) => error.isRetryable,
      ...retryOptions
    };

    const shouldRetry = defaultRetryOptions.retryCondition || ((error) => error.isRetryable);

    let lastError: NetworkError = this.createNetworkError(0, 'Request failed');

    for (let attempt = 0; attempt <= defaultRetryOptions.maxRetries; attempt++) {
      try {
        // Add timeout to fetch
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

        const response = await fetch(url, {
          ...options,
          signal: controller.signal
        });

        clearTimeout(timeoutId);

        // Update health status on successful response
        if (response.ok) {
          this.updateHealthStatus(true);
          return response;
        }

        // Handle HTTP errors
        const error = this.createNetworkError(response.status, `HTTP ${response.status}: ${response.statusText}`);
        
        if (attempt === defaultRetryOptions.maxRetries || !shouldRetry(error)) {
          this.updateHealthStatus(false);
          throw error;
        }

        lastError = error;

      } catch (err) {
        // Handle network errors, timeouts, etc.
        const error = this.handleFetchError(err);
        
        if (attempt === defaultRetryOptions.maxRetries || !shouldRetry(error)) {
          this.updateHealthStatus(false);
          throw error;
        }

        lastError = error;
      }

      // Calculate delay with exponential backoff
      if (attempt < defaultRetryOptions.maxRetries) {
        const delay = Math.min(
          defaultRetryOptions.baseDelay * Math.pow(defaultRetryOptions.backoffMultiplier, attempt),
          defaultRetryOptions.maxDelay
        );
        await this.delay(delay);
      }
    }

    throw lastError || new Error('Unexpected error in retry logic');
  }

  /**
   * Check if the backend is currently reachable
   */
  public async checkBackendHealth(): Promise<HealthStatus> {
    const startTime = Date.now();
    
    // Create AbortController for timeout handling
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
    
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: {
          'Cache-Control': 'no-cache'
        },
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      const latency = Date.now() - startTime;
      
      if (response.ok) {
        this.healthStatus = {
          isOnline: true,
          lastChecked: new Date(),
          latency,
          errorCount: 0
        };
      } else {
        this.healthStatus = {
          isOnline: false,
          lastChecked: new Date(),
          latency,
          errorCount: this.healthStatus.errorCount + 1
        };
      }
    } catch {
      clearTimeout(timeoutId);
      this.healthStatus = {
        isOnline: false,
        lastChecked: new Date(),
        errorCount: this.healthStatus.errorCount + 1
      };
    }

    return { ...this.healthStatus };
  }

  /**
   * Get current health status
   */
  public getHealthStatus(): HealthStatus {
    return { ...this.healthStatus };
  }

  /**
   * Stop health checks (cleanup)
   */
  public stopHealthCheck(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
      this.healthCheckInterval = null;
    }
  }

  /**
   * Create a standardized network error
   */
  private createNetworkError(statusCode: number, message: string): NetworkError {
    const error = new Error(message) as NetworkError;
    error.statusCode = statusCode;
    
    if (statusCode >= 500) {
      error.code = 'SERVER_ERROR';
      error.isRetryable = true;
    } else if (statusCode === 429) {
      error.code = 'SERVER_ERROR';
      error.isRetryable = true;
    } else if (statusCode >= 400) {
      error.code = 'CLIENT_ERROR';
      error.isRetryable = false;
    } else {
      error.code = 'UNKNOWN';
      error.isRetryable = false;
    }

    return error;
  }

  /**
   * Handle various fetch errors and categorize them
   */
  private handleFetchError(err: unknown): NetworkError {
    let message = 'Network request failed';
    let name = '';

    if (err instanceof Error) {
      message = err.message || message;
      name = err.name;
    } else if (typeof err === 'string') {
      message = err;
    }

    const error = new Error(message) as NetworkError;

    if (name === 'AbortError') {
      error.code = 'TIMEOUT';
      error.isRetryable = true;
    } else if (name === 'TypeError' && message?.includes('fetch')) {
      error.code = 'NETWORK_ERROR';
      error.isRetryable = true;
    } else {
      error.code = 'UNKNOWN';
      error.isRetryable = true;
    }

    return error;
  }

  /**
   * Update health status based on request success/failure
   */
  private updateHealthStatus(isSuccess: boolean): void {
    if (isSuccess) {
      this.healthStatus.isOnline = true;
      this.healthStatus.errorCount = Math.max(0, this.healthStatus.errorCount - 1);
    } else {
      this.healthStatus.errorCount += 1;
      // Mark as offline after 3 consecutive errors
      if (this.healthStatus.errorCount >= 3) {
        this.healthStatus.isOnline = false;
      }
    }
    this.healthStatus.lastChecked = new Date();
  }

  /**
   * Simple delay utility
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get user-friendly error message
   */
  public getErrorMessage(error: NetworkError): string {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return 'Unable to connect to the server. Please check your internet connection and try again.';
      case 'TIMEOUT':
        return 'The request timed out. The server might be experiencing high load.';
      case 'SERVER_ERROR':
        if (error.statusCode === 429) {
          return 'Too many requests. Please wait a moment and try again.';
        }
        return 'The server is experiencing issues. Please try again in a few moments.';
      case 'CLIENT_ERROR':
        if (error.statusCode === 404) {
          return 'The requested resource was not found.';
        }
        if (error.statusCode === 400) {
          return 'Invalid request. Please check your input and try again.';
        }
        return 'There was an error with your request. Please try again.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  }
}

export default NetworkUtils;
