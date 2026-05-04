import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { TopicResponse } from '../services/apiService';
import { exportAsMarkdown, copyToClipboard } from './exportTopics';

describe('exportAsMarkdown', () => {
  it('returns placeholder when topics missing', () => {
    expect(exportAsMarkdown(null, {})).toContain('No topics available');
  });

  it('returns placeholder when topics object empty', () => {
    const empty: TopicResponse = {
      topics: {},
      num_topics: 0,
      num_chunks: 0,
      total_tokens_used: 0,
    };
    expect(exportAsMarkdown(empty, {})).toContain('No topics available');
  });

  it('renders headings and bullets from examples', () => {
    const topics: TopicResponse = {
      topics: {
        a1: {
          heading: 'Alpha',
          examples: ['First point'],
          chunks: [],
        },
      },
      num_topics: 1,
      num_chunks: 1,
      total_tokens_used: 5,
    };
    const md = exportAsMarkdown(topics, {});
    expect(md).toContain('# Firmament Notes');
    expect(md).toContain('## Alpha');
    expect(md).toContain('- First point');
  });
});

describe('copyToClipboard', () => {
  beforeEach(() => {
    vi.stubGlobal('navigator', {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('uses navigator.clipboard when available', async () => {
    const ok = await copyToClipboard('hello');
    expect(ok).toBe(true);
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('hello');
  });
});
