import { useCallback, useEffect, useRef, useState } from 'react';
import { TopicResponse } from '../services/apiService';
import { NestedExpansions } from './uploadPipelineTypes';

const TOPICS_STORAGE_KEY = 'firmament_topics';
const EXPANDED_BULLETS_STORAGE_KEY = 'firmament_expanded_bullets';
const LAST_SAVED_AT_STORAGE_KEY = 'firmament_topics_last_saved';
const SAVE_DEBOUNCE_MS = 500;
const MAX_STORAGE_BYTES = 5 * 1024 * 1024;

interface UseTopicPersistenceResult {
  topics: TopicResponse | null;
  setTopics: React.Dispatch<React.SetStateAction<TopicResponse | null>>;
  expandedBullets: NestedExpansions;
  setExpandedBullets: React.Dispatch<React.SetStateAction<NestedExpansions>>;
  lastSavedAt: string | null;
  clearPersistedData: () => void;
}

function parseStoredJson<T>(raw: string | null): T | null {
  if (!raw) return null;

  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function approximateSizeInBytes(value: string): number {
  return new Blob([value]).size;
}

function createCompactTopics(topics: TopicResponse | null): TopicResponse | null {
  if (!topics) return null;

  const compactTopics: TopicResponse = {
    num_chunks: topics.num_chunks,
    num_topics: topics.num_topics,
    total_tokens_used: topics.total_tokens_used,
    topics: {},
  };

  for (const [topicId, topic] of Object.entries(topics.topics)) {
    compactTopics.topics[topicId] = {
      heading: topic.heading,
      bullet_points: topic.bullet_points,
      concepts: topic.concepts,
      summary: topic.summary,
      keywords: topic.keywords,
      segment_positions: topic.segment_positions,
      cluster_id: topic.cluster_id,
      size: topic.size,
      examples: [],
      chunks: [],
    };
  }

  return compactTopics;
}

export function useTopicPersistence(): UseTopicPersistenceResult {
  const [topics, setTopics] = useState<TopicResponse | null>(null);
  const [expandedBullets, setExpandedBullets] = useState<NestedExpansions>({});
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
  const hasInitialized = useRef(false);

  const clearPersistedData = useCallback(() => {
    if (typeof window === 'undefined') return;

    window.localStorage.removeItem(TOPICS_STORAGE_KEY);
    window.localStorage.removeItem(EXPANDED_BULLETS_STORAGE_KEY);
    window.localStorage.removeItem(LAST_SAVED_AT_STORAGE_KEY);

    setTopics(null);
    setExpandedBullets({});
    setLastSavedAt(null);
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') {
      hasInitialized.current = true;
      return;
    }

    const parsedTopics = parseStoredJson<TopicResponse>(window.localStorage.getItem(TOPICS_STORAGE_KEY));
    const parsedExpanded = parseStoredJson<NestedExpansions>(window.localStorage.getItem(EXPANDED_BULLETS_STORAGE_KEY));
    const parsedTimestamp = window.localStorage.getItem(LAST_SAVED_AT_STORAGE_KEY);

    const hadRawTopics = window.localStorage.getItem(TOPICS_STORAGE_KEY) !== null;
    const hadRawExpanded = window.localStorage.getItem(EXPANDED_BULLETS_STORAGE_KEY) !== null;

    if (hadRawTopics && parsedTopics === null) {
      window.localStorage.removeItem(TOPICS_STORAGE_KEY);
    } else if (parsedTopics) {
      setTopics(parsedTopics);
    }

    if (hadRawExpanded && parsedExpanded === null) {
      window.localStorage.removeItem(EXPANDED_BULLETS_STORAGE_KEY);
    } else if (parsedExpanded) {
      setExpandedBullets(parsedExpanded);
    }

    if (parsedTimestamp) {
      setLastSavedAt(parsedTimestamp);
    }

    hasInitialized.current = true;
  }, []);

  useEffect(() => {
    if (!hasInitialized.current || typeof window === 'undefined') return;

    const timeoutId = window.setTimeout(() => {
      const topicsJson = JSON.stringify(topics);
      const expandedJson = JSON.stringify(expandedBullets);
      const combinedSize = approximateSizeInBytes(topicsJson) + approximateSizeInBytes(expandedJson);
      const now = new Date().toISOString();

      try {
        if (combinedSize <= MAX_STORAGE_BYTES) {
          window.localStorage.setItem(TOPICS_STORAGE_KEY, topicsJson);
          window.localStorage.setItem(EXPANDED_BULLETS_STORAGE_KEY, expandedJson);
        } else {
          // Storage budget exceeded, keep only the latest session with compacted topic data.
          const compactTopics = createCompactTopics(topics);
          const compactTopicsJson = JSON.stringify(compactTopics);

          if (approximateSizeInBytes(compactTopicsJson) <= MAX_STORAGE_BYTES) {
            window.localStorage.setItem(TOPICS_STORAGE_KEY, compactTopicsJson);
            window.localStorage.setItem(EXPANDED_BULLETS_STORAGE_KEY, JSON.stringify({}));
          } else {
            window.localStorage.setItem(TOPICS_STORAGE_KEY, JSON.stringify(null));
            window.localStorage.setItem(EXPANDED_BULLETS_STORAGE_KEY, JSON.stringify({}));
          }
        }

        window.localStorage.setItem(LAST_SAVED_AT_STORAGE_KEY, now);
        setLastSavedAt(now);
      } catch {
        // Quota errors can still happen across browsers; clear invalid persisted data.
        window.localStorage.removeItem(TOPICS_STORAGE_KEY);
        window.localStorage.removeItem(EXPANDED_BULLETS_STORAGE_KEY);
      }
    }, SAVE_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [topics, expandedBullets]);

  return {
    topics,
    setTopics,
    expandedBullets,
    setExpandedBullets,
    lastSavedAt,
    clearPersistedData,
  };
}
