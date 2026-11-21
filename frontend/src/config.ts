// Configuration utility for API endpoints
class Config {
  private static instance: Config;
  private apiBaseUrl: string;

  private constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    this.apiBaseUrl = this.apiBaseUrl.replace(/\/$/, '');

    // Warn about missing environment variables in development
    if (import.meta.env.DEV) {
      if (!import.meta.env.VITE_API_BASE_URL) {
        console.warn('[Config] VITE_API_BASE_URL not set, using default: http://localhost:8000');
      }
      if (!import.meta.env.VITE_GOOGLE_CLIENT_ID) {
        console.warn('[Config] VITE_GOOGLE_CLIENT_ID not set - Google Sign-In will not work');
      }
    }
  }

  public static getInstance(): Config {
    if (!Config.instance) {
      Config.instance = new Config();
    }
    return Config.instance;
  }

  public getApiBaseUrl(): string {
    return this.apiBaseUrl;
  }

  public getApiUrl(endpoint: string): string {
    // If endpoint is falsy (empty string or undefined), return base URL unchanged
    if (!endpoint) {
      return this.apiBaseUrl;
    }
    
    // Remove leading slash if present
    const cleanEndpoint = endpoint.replace(/^\//, '');
    return `${this.apiBaseUrl}/${cleanEndpoint}`;
  }
}

export default Config.getInstance();
