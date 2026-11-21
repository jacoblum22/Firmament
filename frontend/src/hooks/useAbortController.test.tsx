import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import useAbortController from './useAbortController';

describe('useAbortController', () => {
  it('reset returns a fresh abort signal', () => {
    const { result } = renderHook(() => useAbortController());
    const s1 = result.current.reset();
    expect(s1.aborted).toBe(false);
    const s2 = result.current.reset();
    expect(s2).not.toBe(s1);
    expect(s2.aborted).toBe(false);
  });

  it('abort marks signal aborted', () => {
    const { result } = renderHook(() => useAbortController());
    const sig = result.current.reset();
    act(() => {
      result.current.abort();
    });
    expect(sig.aborted).toBe(true);
  });
});
