// Configuration utility for API endpoints
class Config {
  private static instance: Config;
  private apiBaseUrl: string;

  private constructor() {
    // Get the API base URL from environment variables
    this.apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    
    // Remove trailing slash if present
    this.apiBaseUrl = this.apiBaseUrl.replace(/\/$/, '');
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
