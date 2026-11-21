import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { validateAuthResponse, validateTopicResponse } from './apiValidation';

describe('validateAuthResponse', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  const minimalValid = {
    session_token: 'tok',
    user_info: {
      user_id: 'u1',
      email: 'a@b.com',
      name: 'A',
    },
  };

  it('accepts session_token + user_info', () => {
    const out = validateAuthResponse(minimalValid);
    expect(out.session_token).toBe('tok');
    expect(out.user_info.email).toBe('a@b.com');
    expect(out.user.email).toBe('a@b.com');
  });

  it('accepts access_token as token source', () => {
    const out = validateAuthResponse({
      access_token: 'at',
      user: { id: 'u2', email: 'x@y.com', name: 'X' },
    });
    expect(out.session_token).toBe('at');
    expect(out.user_info.user_id).toBe('u2');
  });

  it('rejects non-object payload', () => {
    expect(() => validateAuthResponse(null)).toThrow(/Invalid authentication response/);
    expect(warnSpy).toHaveBeenCalled();
  });

  it('rejects missing token', () => {
    expect(() =>
      validateAuthResponse({
        user_info: { user_id: 'u', email: 'e', name: 'n' },
      })
    ).toThrow(/missing required fields/);
  });

  it('does not log raw payload on validation failure (only safe summary)', () => {
    const sensitive = { session_token: 'SECRET', user_info: { user_id: 'u', email: 'e', name: 'n' } };
    expect(() => validateAuthResponse(sensitive)).not.toThrow();
    warnSpy.mockClear();
    expect(() => validateAuthResponse({ bad: true })).toThrow();
    const calls = warnSpy.mock.calls;
    expect(calls.length).toBeGreaterThan(0);
    for (const args of calls) {
      const rest = args.slice(1);
      for (const arg of rest) {
        expect(JSON.stringify(arg)).not.toContain('SECRET');
      }
    }
  });
});

describe('validateTopicResponse', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it('normalizes topics record shape', () => {
    const out = validateTopicResponse({
      topics: {
        t1: { heading: 'H', examples: ['a', 'b'] },
      },
      num_chunks: 2,
      num_topics: 1,
      total_tokens_used: 10,
    });
    expect(out.topics.t1.heading).toBe('H');
    expect(out.num_topics).toBe(1);
    expect(out.total_tokens_used).toBe(10);
  });

  it('throws on server error field', () => {
    expect(() => validateTopicResponse({ error: 'fail' })).toThrow('fail');
  });

  it('rejects non-object', () => {
    expect(() => validateTopicResponse(null)).toThrow(/Invalid topic response/);
  });

  it('does not log raw payload on shape failure', () => {
    expect(() => validateTopicResponse({ topics: 'nope' })).toThrow();
    const logged = JSON.stringify(warnSpy.mock.calls);
    expect(logged).not.toContain('nope');
  });

  it('accepts id/title/bullets array topic format', () => {
    const out = validateTopicResponse({
      topics: [{ id: 1, title: 'One', bullets: ['a', 'b'] }],
      num_chunks: 0,
      num_topics: 1,
      total_tokens_used: 0,
    });
    expect(out.topics['1'].heading).toBe('One');
    expect(out.topics['1'].examples).toContain('a');
  });
});
