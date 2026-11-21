// Network utility functions for improved error handling and resilience

export interface NetworkError extends Error {
  code: 'NETWORK_ERROR' | 'TIMEOUT' | 'SERVER_ERROR' | 'CLIENT_ERROR' | 'UNKNOWN';
  statusCode?: number;
  isRetryable: boolean;
}

const NETWORK_ERROR_CODES: NetworkError['code'][] = [
  'NETWORK_ERROR',
  'TIMEOUT',
  'SERVER_ERROR',
  'CLIENT_ERROR',
  'UNKNOWN',
];

/** True when `fetchWithRetry` attached a network error code (vs a plain API/validation Error). */
export function isNetworkError(error: unknown): error is NetworkError {
  if (!(error instanceof Error)) return false;
  const code = (error as Partial<NetworkError>).code;
  return typeof code === 'string' && (NETWORK_ERROR_CODES as readonly string[]).includes(code);
}

export interface ErrorDetails {
  error: string;
  details: string;
  user_action: string;
  error_code: string;
}

export interface RetryOptions {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  timeout?: number;
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
        const timeoutMs = defaultRetryOptions.timeout ?? 30000;
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

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

        // Handle HTTP errors — surface JSON error bodies from the API when present
        let httpErrorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorText = await response.text();
          if (errorText.trim()) {
            try {
              const body = JSON.parse(errorText) as {
                error?: string;
                message?: string;
                details?: string;
              };
              if (typeof body.error === 'string' && body.error) {
                httpErrorMessage =
                  typeof body.details === 'string' && body.details
                    ? `${body.error} — ${body.details}`
                    : body.error;
              } else if (typeof body.message === 'string' && body.message) {
                httpErrorMessage = body.message;
              } else {
                httpErrorMessage = errorText.slice(0, 400);
              }
            } catch {
              httpErrorMessage = errorText.slice(0, 400);
            }
          }
        } catch {
          /* keep default httpErrorMessage */
        }

        const error = this.createNetworkError(response.status, httpErrorMessage);

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
      const url = `${this.baseUrl.replace(/\/$/, '')}/health?_=${Date.now()}`;
      const response = await fetch(url, {
        method: 'GET',
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store',
          Pragma: 'no-cache',
        },
        signal: controller.signal,
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
    const wasOnline = this.healthStatus.isOnline;
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

    if (
      typeof window !== 'undefined' &&
      wasOnline !== this.healthStatus.isOnline
    ) {
      window.dispatchEvent(
        new CustomEvent<{ isOnline: boolean }>('firmament-backend-reachability', {
          detail: { isOnline: this.healthStatus.isOnline },
        }),
      );
    }
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
  public getErrorMessage(error: NetworkError): ErrorDetails {
    switch (error.code) {
      case 'NETWORK_ERROR':
        return {
          error: 'Connection problem',
          details: 'Unable to connect to the server.',
          user_action: 'Please check your internet connection and try again.',
          error_code: 'network_error'
        };
      case 'TIMEOUT':
        return {
          error: 'Request timed out',
          details: 'The server took too long to respond.',
          user_action: 'The server might be experiencing high load. Please try again in a moment.',
          error_code: 'timeout'
        };
      case 'SERVER_ERROR':
        if (error.statusCode === 429) {
          return {
            error: 'Too many requests',
            details: 'You\'re making requests too quickly.',
            user_action: 'Please wait a moment and try again.',
            error_code: 'rate_limited'
          };
        }
        return {
          error: 'Server error',
          details:
            error.message && !/^HTTP \d{3}:/.test(error.message)
              ? error.message
              : 'The server is experiencing technical difficulties.',
          user_action: 'Please try again in a few moments.',
          error_code: 'server_error'
        };
      case 'CLIENT_ERROR':
        if (error.statusCode === 404) {
          return {
            error: 'Resource not found',
            details: 'The requested resource could not be found.',
            user_action: 'Please refresh the page and try again.',
            error_code: 'not_found'
          };
        }
        if (error.statusCode === 400) {
          return {
            error: 'Invalid request',
            details: 'There was an issue with your request.',
            user_action: 'Please check your input and try again.',
            error_code: 'bad_request'
          };
        }
        return {
          error: 'Request error',
          details: 'There was an error with your request.',
          user_action: 'Please try again.',
          error_code: 'client_error'
        };
      default:
        return {
          error: 'Unexpected error',
          details: 'An unexpected error occurred.',
          user_action: 'Please try again.',
          error_code: 'unknown_error'
        };
    }
  }
}

export default NetworkUtils;
