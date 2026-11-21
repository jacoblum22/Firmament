import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useNetworkStatus } from './useNetworkStatus';

const mockCheckBackendHealth = vi.hoisted(() =>
  vi.fn().mockResolvedValue({
    isOnline: true,
    lastChecked: new Date(),
    errorCount: 0,
  }),
);

vi.mock('../utils/networkUtils', () => ({
  default: class {
    static getInstance() {
      return {
        checkBackendHealth: mockCheckBackendHealth,
        stopHealthCheck: vi.fn(),
        fetchWithRetry: vi.fn(),
        getErrorMessage: vi.fn(),
        getHealthStatus: vi.fn(() => ({})),
      };
    }

    static clearInstances() {}
  },
  NetworkError: Error,
}));

describe('useNetworkStatus', () => {
  beforeEach(() => {
    mockCheckBackendHealth.mockClear();
    mockCheckBackendHealth.mockResolvedValue({
      isOnline: true,
      lastChecked: new Date(),
      errorCount: 0,
    });
    Object.defineProperty(navigator, 'onLine', { configurable: true, value: true });
  });

  it('marks backend reachable after health check', async () => {
    const { result } = renderHook(() => useNetworkStatus());

    await waitFor(
      () => {
        expect(result.current.isBackendReachable).toBe(true);
      },
      { timeout: 5000 },
    );

    expect(mockCheckBackendHealth).toHaveBeenCalled();
    expect(result.current.isInitializing).toBe(false);
  });
});
