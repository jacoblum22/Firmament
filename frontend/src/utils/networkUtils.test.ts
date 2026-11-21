import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import NetworkUtils from './networkUtils';
import type { NetworkError } from './networkUtils';

describe('NetworkUtils', () => {
  beforeEach(() => {
    NetworkUtils.clearInstances();
  });

  afterEach(() => {
    NetworkUtils.clearInstances();
    vi.unstubAllGlobals();
  });

  it('getInstance returns same ref per baseUrl', () => {
    const a = NetworkUtils.getInstance('http://a.test');
    const b = NetworkUtils.getInstance('http://a.test');
    const c = NetworkUtils.getInstance('http://b.test');
    expect(a).toBe(b);
    expect(a).not.toBe(c);
  });

  it('checkBackendHealth sets online when /health returns ok', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 200, statusText: 'OK' }))
    );

    const nu = NetworkUtils.getInstance('http://api.test');
    const status = await nu.checkBackendHealth();

    expect(fetch).toHaveBeenCalledWith(
      expect.stringMatching(/^http:\/\/api\.test\/health\?_=\d+$/),
      expect.objectContaining({ method: 'GET', cache: 'no-store' }),
    );
    expect(status.isOnline).toBe(true);
    expect(nu.getHealthStatus().isOnline).toBe(true);
  });

  it('getErrorMessage maps SERVER_ERROR with 429', () => {
    const nu = NetworkUtils.getInstance('http://x.test');
    const err = Object.assign(new Error('x'), {
      code: 'SERVER_ERROR',
      statusCode: 429,
      isRetryable: true,
    }) as NetworkError;

    const msg = nu.getErrorMessage(err);
    expect(msg.error_code).toBe('rate_limited');
  });

  it('getErrorMessage falls back for unknown code', () => {
    const nu = NetworkUtils.getInstance('http://y.test');
    const err = Object.assign(new Error('x'), {
      code: 'UNKNOWN' as NetworkError['code'],
      isRetryable: false,
    }) as NetworkError;

    expect(nu.getErrorMessage(err).error_code).toBe('unknown_error');
  });
});
