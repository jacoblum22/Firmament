type UnknownRecord = Record<string, unknown>;

/** Safe client-side log summary — never log raw API payloads (tokens, PII). */
function summarizeRecordKeys(value: unknown): string {
  if (!isRecord(value)) {
    return typeof value;
  }
  const keys = Object.keys(value);
  const preview = keys.slice(0, 14).join(', ');
  return keys.length > 14 ? `${preview}, …` : preview || '(empty object)';
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === 'object' && value !== null;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string');
}

function asNumberOrDefault(value: unknown, fallback: number): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback;
}

export interface NormalizedAuthResponse {
  session_token: string;
  access_token: string;
  token_type: string;
  user_info: {
    user_id: string;
    email: string;
    name: string;
    picture?: string;
  };
  user: {
    id: string;
    email: string;
    name: string;
    picture?: string;
  };
}

function isAuthUser(
  value: unknown
): value is { user_id: string; email: string; name: string; picture?: string; id?: string } {
  if (!isRecord(value)) {
    return false;
  }

  const userId = typeof value.user_id === 'string' ? value.user_id : typeof value.id === 'string' ? value.id : null;

  return (
    typeof userId === 'string' &&
    typeof value.email === 'string' &&
    typeof value.name === 'string' &&
    (value.picture === undefined || typeof value.picture === 'string')
  );
}

export function validateAuthResponse(payload: unknown): NormalizedAuthResponse {
  if (!isRecord(payload)) {
    console.warn('Invalid auth response: expected an object.', summarizeRecordKeys(payload));
    throw new Error('Invalid authentication response from server.');
  }

  const token =
    typeof payload.session_token === 'string'
      ? payload.session_token
      : typeof payload.access_token === 'string'
        ? payload.access_token
        : typeof payload.token === 'string'
          ? payload.token
          : null;

  const rawUser = payload.user_info ?? payload.user;

  if (!token || !isAuthUser(rawUser)) {
    console.warn(
      'Invalid auth response shape: expected session_token and user_info/user fields.',
      summarizeRecordKeys(payload)
    );
    throw new Error('Authentication response is missing required fields (session_token and user_info).');
  }

  const userId =
    typeof rawUser.user_id === 'string'
      ? rawUser.user_id
      : typeof rawUser.id === 'string'
        ? rawUser.id
        : null;

  if (!userId) {
    console.warn(
      'Invalid auth response shape: expected user_id or id on user object.',
      summarizeRecordKeys(payload)
    );
    throw new Error('Authentication response is missing required user identifier fields.');
  }

  return {
    session_token: token,
    access_token: token,
    token_type: typeof payload.token_type === 'string' ? payload.token_type : 'Bearer',
    user_info: {
      user_id: userId,
      email: rawUser.email,
      name: rawUser.name,
      ...(typeof rawUser.picture === 'string' ? { picture: rawUser.picture } : {}),
    },
    user: {
      id: userId,
      email: rawUser.email,
      name: rawUser.name,
      ...(typeof rawUser.picture === 'string' ? { picture: rawUser.picture } : {}),
    },
  };
}

export interface NormalizedTopic {
  heading: string;
  examples: string[];
  bullet_points?: string[];
  [key: string]: unknown;
}

export interface NormalizedTopicResponse {
  num_chunks: number;
  num_topics: number;
  total_tokens_used: number;
  segments?: Array<{ position: string; text: string }>;
  topics: Record<string, NormalizedTopic>;
  [key: string]: unknown;
}

function isTopicShapeRecord(value: unknown): value is Record<string, UnknownRecord> {
  if (!isRecord(value)) {
    return false;
  }

  return Object.values(value).every((entry) => isRecord(entry));
}

function isIdTitleBulletsTopic(value: unknown): value is { id: string | number; title: string; bullets: string[] } {
  if (!isRecord(value)) {
    return false;
  }

  return (
    (typeof value.id === 'string' || typeof value.id === 'number') &&
    typeof value.title === 'string' &&
    isStringArray(value.bullets)
  );
}

function normalizeTopicEntry(entry: UnknownRecord): NormalizedTopic | null {
  if (typeof entry.heading === 'string' && isStringArray(entry.examples)) {
    const normalizedTopic: NormalizedTopic = {
      ...entry,
      heading: entry.heading,
      examples: entry.examples,
    };

    if (entry.bullet_points !== undefined && !isStringArray(entry.bullet_points)) {
      return null;
    }

    return normalizedTopic;
  }

  if (isIdTitleBulletsTopic(entry)) {
    return {
      ...entry,
      heading: entry.title,
      examples: entry.bullets,
      bullet_points: entry.bullets,
    };
  }

  return null;
}

function normalizeSegments(value: unknown): Array<{ position: string; text: string }> | undefined {
  if (!Array.isArray(value)) {
    return undefined;
  }

  const normalized = value.filter(
    (segment): segment is { position: string; text: string } =>
      isRecord(segment) && typeof segment.position === 'string' && typeof segment.text === 'string'
  );

  return normalized.length > 0 ? normalized : undefined;
}

export function validateTopicResponse(payload: unknown): NormalizedTopicResponse {
  if (!isRecord(payload)) {
    console.warn('Invalid topic response: expected an object.', summarizeRecordKeys(payload));
    throw new Error('Invalid topic response from server.');
  }

  if (payload && typeof payload === 'object' && 'error' in payload) {
    const errorPayload = payload as Record<string, unknown>;
    const message =
      typeof errorPayload.error === 'string' ? errorPayload.error : 'Topic generation failed on the server.';
    throw new Error(message);
  }

  const normalizedTopics: Record<string, NormalizedTopic> = {};
  const rawTopics = payload.topics;

  if (isTopicShapeRecord(rawTopics)) {
    for (const [topicId, topicEntry] of Object.entries(rawTopics)) {
      const normalizedTopic = normalizeTopicEntry(topicEntry);
      if (!normalizedTopic) {
        console.warn(`Invalid topic entry for id ${topicId}.`, summarizeRecordKeys(topicEntry));
        throw new Error(`Invalid topic entry in API response for topic ${topicId}.`);
      }
      normalizedTopics[topicId] = normalizedTopic;
    }
  } else if (Array.isArray(rawTopics) && rawTopics.every(isIdTitleBulletsTopic)) {
    rawTopics.forEach((topic) => {
      const topicId = String(topic.id);
      normalizedTopics[topicId] = {
        heading: topic.title,
        examples: topic.bullets,
        bullet_points: topic.bullets,
      };
    });
  } else {
    console.warn(
      'Invalid topic response shape: expected topics object or id/title/bullets array.',
      summarizeRecordKeys(payload)
    );
    const topicsType = rawTopics === undefined ? 'undefined' : typeof rawTopics;
    throw new Error(
      `Topic response format not recognized. Expected topics as Record or Array, got ${topicsType}.`
    );
  }

  return {
    ...payload,
    num_chunks: asNumberOrDefault(payload.num_chunks, 0),
    num_topics: asNumberOrDefault(payload.num_topics, Object.keys(normalizedTopics).length),
    total_tokens_used: asNumberOrDefault(payload.total_tokens_used, 0),
    segments: normalizeSegments(payload.segments),
    topics: normalizedTopics,
  };
}
