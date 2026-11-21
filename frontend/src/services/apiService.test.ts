import { describe, it, expect, vi, beforeEach } from 'vitest';

const hoisted = vi.hoisted(() => ({
  fetchWithRetry: vi.fn(),
  checkBackendHealth: vi.fn(),
  getErrorMessage: vi.fn(() => ({
    error: 'Network error',
    details: '',
    user_action: '',
    error_code: 'E',
  })),
  getHealthStatus: vi.fn(() => ({
    isOnline: true,
    lastChecked: new Date(),
    errorCount: 0,
  })),
  stopHealthCheck: vi.fn(),
}));

vi.mock('../utils/networkUtils', () => ({
  default: class {
    static getInstance() {
      return {
        fetchWithRetry: hoisted.fetchWithRetry,
        checkBackendHealth: hoisted.checkBackendHealth,
        getErrorMessage: hoisted.getErrorMessage,
        getHealthStatus: hoisted.getHealthStatus,
        stopHealthCheck: hoisted.stopHealthCheck,
      };
    }

    static clearInstances() {}
  },
  NetworkError: class NetworkError extends Error {
    code = 'NETWORK_ERROR';

    isRetryable = false;

    statusCode?: number;
  },
}));

import apiService from './apiService';

function okJson(data: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: 'OK',
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(typeof data === 'string' ? data : JSON.stringify(data)),
  } as Response;
}

function errJson(data: unknown, status: number): Response {
  return {
    ok: false,
    status,
    statusText: 'Error',
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(typeof data === 'string' ? data : JSON.stringify(data)),
  } as Response;
}

describe('apiService', () => {
  beforeEach(() => {
    hoisted.fetchWithRetry.mockReset();
    hoisted.checkBackendHealth.mockReset();
    hoisted.getHealthStatus.mockClear();
    localStorage.clear();
  });

  it('getLlmStatus returns parsed body', async () => {
    hoisted.fetchWithRetry.mockResolvedValue(
      okJson({
        provider: 'openai',
        has_server_key: true,
        requires_user_key: false,
        base_url: 'http://localhost',
      }),
    );
    const result = await apiService.getLlmStatus();
    expect(result.provider).toBe('openai');
  });

  it('getCurrentUser returns JSON', async () => {
    hoisted.fetchWithRetry.mockResolvedValue(okJson({ id: 'u1', email: 'a@b.c', name: 'N' }));
    localStorage.setItem('studymate_token', 'tok');
    const user = await apiService.getCurrentUser();
    expect(user.email).toBe('a@b.c');
  });

  it('signInWithGoogle validates response', async () => {
    hoisted.fetchWithRetry.mockResolvedValue(
      okJson({
        session_token: 'st',
        user: { id: 'u1', email: 'a@b.c', name: 'N' },
      }),
    );
    const auth = await apiService.signInWithGoogle('google-jwt');
    expect(auth.user.email).toBe('a@b.c');
  });

  it('checkHealth reflects backend online flag', async () => {
    hoisted.checkBackendHealth.mockResolvedValue({
      isOnline: true,
      lastChecked: new Date(),
      errorCount: 0,
    });
    await expect(apiService.checkHealth()).resolves.toBe(true);

    hoisted.checkBackendHealth.mockResolvedValue({
      isOnline: false,
      lastChecked: new Date(),
      errorCount: 1,
    });
    await expect(apiService.checkHealth()).resolves.toBe(false);
  });

  it('checkHealth returns false when health check throws', async () => {
    hoisted.checkBackendHealth.mockRejectedValue(new Error('down'));
    await expect(apiService.checkHealth()).resolves.toBe(false);
  });

  it('getNetworkStatus proxies utils', () => {
    apiService.getNetworkStatus();
    expect(hoisted.getHealthStatus).toHaveBeenCalled();
  });

  it('uploadFile posts multipart and parses response', async () => {
    hoisted.fetchWithRetry.mockResolvedValue(
      okJson({
        job_id: 'j1',
        filename: 'f.txt',
        filetype: 'text',
        message: 'ok',
      }),
    );
    const file = new File(['x'], 'f.txt', { type: 'text/plain' });
    const res = await apiService.uploadFile(file);
    expect(res.job_id).toBe('j1');
    expect(hoisted.fetchWithRetry).toHaveBeenCalled();
  });

  it('generateHeadings validates topics payload', async () => {
    hoisted.fetchWithRetry.mockResolvedValue(
      okJson({
        num_chunks: 1,
        num_topics: 1,
        total_tokens_used: 0,
        topics: {
          '1': { heading: 'H', examples: [] },
        },
      }),
    );
    const out = await apiService.generateHeadings('f.txt', 'pid');
    expect(out.topics['1'].heading).toBe('H');
  });

  it('throws user-facing message on HTTP 402', async () => {
    hoisted.fetchWithRetry.mockResolvedValue(errJson({ error: 'pay' }, 402));
    await expect(apiService.getLlmStatus()).rejects.toThrow(/API key/);
  });

  it('processChunks returns parsed body', async () => {
    hoisted.fetchWithRetry.mockResolvedValue(okJson({ num_chunks: 2, total_words: 10 }));
    const out = await apiService.processChunks('hello', 'doc.txt');
    expect(out.num_chunks).toBe(2);
  });

  it('signOut posts and returns message', async () => {
    hoisted.fetchWithRetry.mockResolvedValue(okJson({ message: 'bye' }));
    localStorage.setItem('studymate_token', 'tok');
    const out = await apiService.signOut();
    expect(out.message).toBe('bye');
  });

  it('createProgressEventSource parses SSE JSON', () => {
    const Original = globalThis.EventSource;

    class MockEventSource {
      url: string;
      onmessage: ((e: MessageEvent) => void) | null = null;
      onerror: ((e: Event) => void) | null = null;
      readyState = 0;
      close = vi.fn();
      addEventListener = vi.fn();
      removeEventListener = vi.fn();
      dispatchEvent = vi.fn();

      constructor(url: string) {
        this.url = url;
      }
    }

    globalThis.EventSource = MockEventSource as unknown as typeof EventSource;

    const onMessage = vi.fn();
    const es = apiService.createProgressEventSource('job-abc', onMessage) as unknown as MockEventSource;

    expect(es.url).toContain('progress/job-abc');
    es.onmessage?.({ data: JSON.stringify({ stage: 'upload' }) } as MessageEvent);
    expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({ stage: 'upload' }));

    globalThis.EventSource = Original;
  });
});
