import NetworkUtils, { NetworkError } from '../utils/networkUtils';
import config from '../config';

// Define proper types for API responses
export interface UploadResponse {
  job_id: string;
  filename: string;
  message: string;
}

export interface ProcessChunksResponse {
  num_chunks: number;
  total_words: number;
}

export interface TopicData {
  [key: string]: unknown;
}

export interface BulletPointData {
  [key: string]: unknown;
}

export interface ProgressData {
  stage: string;
  current?: number;
  total?: number;
  result?: unknown;
  error?: string;
}

class ApiService {
  private static instance: ApiService;
  private networkUtils: NetworkUtils;

  private constructor() {
    this.networkUtils = NetworkUtils.getInstance(config.getApiBaseUrl());
  }

  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  /**
   * Enhanced fetch wrapper with automatic retry and better error handling
   */
  private async enhancedFetch(
    endpoint: string,
    options: RequestInit = {},
    retryOptions?: { maxRetries?: number; baseDelay?: number }
  ): Promise<Response> {
    const url = config.getApiUrl(endpoint);
    
    return this.networkUtils.fetchWithRetry(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }, retryOptions);
  }

  /**
   * Handle response and extract JSON with proper error handling
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorText = await response.text();
      let errorData;
      
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { error: errorText || `HTTP ${response.status}: ${response.statusText}` };
      }

      throw new Error(errorData.error || errorData.message || `Request failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Upload file
   */
  public async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await this.enhancedFetch('upload', {
        method: 'POST',
        body: formData,
        headers: {}, // Don't set Content-Type for FormData
      }, {
        maxRetries: 2, // Fewer retries for uploads
        baseDelay: 2000 // Longer delay between retries
      });

      return this.handleResponse<UploadResponse>(response);
    } catch (error) {
      if (error instanceof Error) {
        const networkError = error as NetworkError;
        throw new Error(this.networkUtils.getErrorMessage(networkError));
      }
      throw new Error('Upload failed. Please try again.');
    }
  }

  /**
   * Process text chunks
   */
  public async processChunks(
    text: string,
    filename: string
  ): Promise<ProcessChunksResponse> {
    try {
      const response = await this.enhancedFetch('process-chunks', {
        method: 'POST',
        body: JSON.stringify({ text, filename }),
      });

      return this.handleResponse<ProcessChunksResponse>(response);
    } catch (error) {
      if (error instanceof Error) {
        const networkError = error as NetworkError;
        throw new Error(this.networkUtils.getErrorMessage(networkError));
      }
      throw new Error('Failed to process chunks. Please try again.');
    }
  }

  /**
   * Generate topic headings
   */
  public async generateHeadings(filename: string): Promise<TopicData> {
    try {
      const response = await this.enhancedFetch('generate-headings', {
        method: 'POST',
        body: JSON.stringify({ filename }),
      });

      return this.handleResponse<TopicData>(response);
    } catch (error) {
      if (error instanceof Error) {
        const networkError = error as NetworkError;
        throw new Error(this.networkUtils.getErrorMessage(networkError));
      }
      throw new Error('Failed to generate headings. Please try again.');
    }
  }

  /**
   * Expand cluster
   */
  public async expandCluster(data: BulletPointData): Promise<TopicData> {
    try {
      const response = await this.enhancedFetch('expand-cluster', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      return this.handleResponse<TopicData>(response);
    } catch (error) {
      if (error instanceof Error) {
        const networkError = error as NetworkError;
        throw new Error(this.networkUtils.getErrorMessage(networkError));
      }
      throw new Error('Failed to expand cluster. Please try again.');
    }
  }

  /**
   * Debug bullet point
   */
  public async debugBulletPoint(data: BulletPointData): Promise<BulletPointData> {
    try {
      const response = await this.enhancedFetch('debug-bullet-point', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      return this.handleResponse<BulletPointData>(response);
    } catch (error) {
      if (error instanceof Error) {
        const networkError = error as NetworkError;
        throw new Error(this.networkUtils.getErrorMessage(networkError));
      }
      throw new Error('Failed to debug bullet point. Please try again.');
    }
  }

  /**
   * Expand bullet point
   */
  public async expandBulletPoint(data: BulletPointData): Promise<BulletPointData> {
    try {
      const response = await this.enhancedFetch('expand-bullet-point', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      return this.handleResponse<BulletPointData>(response);
    } catch (error) {
      if (error instanceof Error) {
        const networkError = error as NetworkError;
        throw new Error(this.networkUtils.getErrorMessage(networkError));
      }
      throw new Error('Failed to expand bullet point. Please try again.');
    }
  }

  /**
   * Create Server-Sent Events connection for progress tracking
   */
  public createProgressEventSource(
    jobId: string,
    onMessage: (data: ProgressData) => void,
    onError?: (error: Error) => void,
    onClose?: () => void
  ): EventSource {
    const url = config.getApiUrl(`progress/${jobId}`);
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ProgressData;
        onMessage(data);
      } catch (error) {
        console.error('Failed to parse SSE data:', error);
        onError?.(new Error('Failed to parse server response'));
      }
    };

    eventSource.onerror = (event) => {
      console.error('SSE error:', event);
      const error = new Error('Connection to server lost. Please try refreshing the page.');
      onError?.(error);
      
      // Auto-close on error
      eventSource.close();
      onClose?.();
    };

    // Auto-cleanup after 10 minutes to prevent memory leaks
    setTimeout(() => {
      if (eventSource.readyState !== EventSource.CLOSED) {
        eventSource.close();
        onClose?.();
      }
    }, 10 * 60 * 1000);

    return eventSource;
  }

  /**
   * Check if the service is healthy
   */
  public async checkHealth(): Promise<boolean> {
    try {
      const healthStatus = await this.networkUtils.checkBackendHealth();
      return healthStatus.isOnline;
    } catch {
      return false;
    }
  }

  /**
   * Get current network status
   */
  public getNetworkStatus() {
    return this.networkUtils.getHealthStatus();
  }
}

export default ApiService.getInstance();
