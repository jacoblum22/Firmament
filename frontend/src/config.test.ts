import { describe, it, expect } from 'vitest';
import config from './config';

describe('config', () => {
  it('getApiBaseUrl is non-empty', () => {
    expect(config.getApiBaseUrl().length).toBeGreaterThan(0);
  });

  it('getApiUrl strips leading slash and joins base', () => {
    const base = config.getApiBaseUrl();
    expect(config.getApiUrl('/v1/health')).toBe(`${base}/v1/health`);
    expect(config.getApiUrl('v1/health')).toBe(`${base}/v1/health`);
  });

  it('getApiUrl with empty segment returns base only', () => {
    expect(config.getApiUrl('')).toBe(config.getApiBaseUrl());
  });
});
