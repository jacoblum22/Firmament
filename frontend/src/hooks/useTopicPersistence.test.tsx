import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useTopicPersistence } from './useTopicPersistence';

const sampleTopics = {
  num_chunks: 1,
  num_topics: 1,
  total_tokens_used: 0,
  topics: {
    '1': {
      heading: 'Topic A',
      examples: ['e1'],
      chunks: [{ position: '0', text: 't' }],
    },
  },
};

describe('useTopicPersistence', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('hydrates topics from localStorage', async () => {
    localStorage.setItem('firmament_topics', JSON.stringify(sampleTopics));

    const { result } = renderHook(() => useTopicPersistence());

    await waitFor(() => {
      expect(result.current.topics?.topics['1']?.heading).toBe('Topic A');
    });
  });

  it('removes corrupt topics key from storage', async () => {
    localStorage.setItem('firmament_topics', 'not-json{');

    renderHook(() => useTopicPersistence());

    await waitFor(() => {
      expect(localStorage.getItem('firmament_topics')).toBeNull();
    });
  });

  it('persists after debounce when topics change', async () => {
    const { result } = renderHook(() => useTopicPersistence());

    await act(async () => {
      await Promise.resolve();
    });

    act(() => {
      result.current.setTopics(sampleTopics);
    });

    await act(async () => {
      await new Promise((r) => setTimeout(r, 600));
    });

    const raw = localStorage.getItem('firmament_topics');
    expect(raw).toBeTruthy();
    expect(raw).toContain('Topic A');
  }, 10_000);

  it('clearPersistedData clears storage and state', async () => {
    localStorage.setItem('firmament_topics', JSON.stringify(sampleTopics));

    const { result } = renderHook(() => useTopicPersistence());

    await act(async () => {
      await new Promise((r) => setTimeout(r, 0));
    });

    expect(result.current.topics).not.toBeNull();

    act(() => {
      result.current.clearPersistedData();
    });

    expect(localStorage.getItem('firmament_topics')).toBeNull();
    expect(result.current.topics).toBeNull();
    expect(result.current.lastSavedAt).toBeNull();
  });
});
