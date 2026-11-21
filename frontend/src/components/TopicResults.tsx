import { memo } from 'react';
import ReactMarkdown from 'react-markdown';
import { TopicResponse } from '../services/apiService';
import { NestedExpansions } from '../hooks/uploadPipelineTypes';

const buttonStyle: React.CSSProperties = {
  marginLeft: '1rem',
  padding: '0.5rem 1rem',
  color: 'white',
  border: 'none',
  cursor: 'pointer',
};

type TopicResultsProps = {
  topics: TopicResponse | null;
  expandedBullets: NestedExpansions;
  expandingBulletKey?: string | null;
  generateBulletKey: (bulletPoint: string) => string;
  handleExpandCluster: (clusterId: string) => Promise<void>;
  handleExpandBulletPoint: (bulletPoint: string, topicId: string) => Promise<void>;
  handleExpandSubBulletPoint: (
    subBullet: string,
    topicId: string,
    parentBulletKey: string,
    depth?: number
  ) => Promise<void>;
};

export function TopicResults({
  topics,
  expandedBullets,
  expandingBulletKey,
  generateBulletKey,
  handleExpandCluster,
  handleExpandBulletPoint,
  handleExpandSubBulletPoint,
}: TopicResultsProps) {
  if (!topics) {
    return null;
  }

  const renderSubBullets = (
    subBullets: string[],
    parentBulletKey: string,
    topicId: string,
    subExpansions: NestedExpansions = {},
    depth: number = 1
  ) => {
    return (
      <ul
        style={{
          margin: '0.5rem 0 0 0',
          paddingLeft: '1.5rem',
          listStyleType: depth === 1 ? 'circle' : 'square',
          color: '#ddd',
        }}
      >
        {subBullets.map((subBullet: string) => {
          const cleanedSubBullet = subBullet.replace(/^[-*+]\s*/, '').trim();
          const subBulletKey = `${parentBulletKey}_sub_${subBullet.slice(0, 30)}`;
          const subExpansion = subExpansions[subBulletKey];

          return (
            <li
              key={subBulletKey}
              style={{
                marginBottom: '0.5rem',
                fontSize: 'inherit',
                lineHeight: 'inherit',
                cursor: depth < 2 ? 'pointer' : 'default',
                opacity: depth < 2 ? 1 : 0.8,
              }}
              onClick={(e) => {
                e.stopPropagation();
                if (depth < 2) {
                  handleExpandSubBulletPoint(subBullet, topicId, parentBulletKey, depth);
                }
              }}
            >
              <div>
                <ReactMarkdown>{cleanedSubBullet}</ReactMarkdown>
                {expandingBulletKey === subBulletKey && (
                  <span className="inline-loading-indicator" aria-label="Expanding bullet" />
                )}
                {subExpansion &&
                  subExpansion.expansion.expanded_bullets &&
                  renderSubBullets(
                    subExpansion.expansion.expanded_bullets,
                    subBulletKey,
                    topicId,
                    subExpansion.subExpansions || {},
                    depth + 1
                  )}
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  const renderBulletPoints = (bulletPoints: string[], topicId: string) => {
    return (
      <ul
        style={{
          margin: '0.5rem 0 0 0',
          paddingLeft: '1.5rem',
          color: '#ddd',
          listStyleType: 'disc',
        }}
      >
        {bulletPoints.map((point) => {
          const cleanedPoint = point.replace(/^[-*+]\s*/, '').trim();
          const bulletKey = `${topicId}_${generateBulletKey(point)}`;
          const isExpanded = expandedBullets[bulletKey];

          return (
            <li
              key={bulletKey}
              style={{ marginBottom: '0.5rem', cursor: 'pointer' }}
              onClick={() => {
                handleExpandBulletPoint(point, topicId);
              }}
            >
              <div>
                <ReactMarkdown>{cleanedPoint}</ReactMarkdown>
                {expandingBulletKey === bulletKey && (
                  <span className="inline-loading-indicator" aria-label="Expanding bullet" />
                )}
                {isExpanded &&
                  isExpanded.expansion.expanded_bullets &&
                  renderSubBullets(
                    isExpanded.expansion.expanded_bullets,
                    bulletKey,
                    topicId,
                    isExpanded.subExpansions || {},
                    1
                  )}
              </div>
            </li>
          );
        })}
      </ul>
    );
  };

  return (
    <div style={{ marginTop: '2rem' }}>
      <h2>📊 Generated Topics</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        {Object.entries(topics.topics).map(([topicId, topic]) => (
          <div
            key={topicId}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '1.5rem',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              textAlign: 'left',
            }}
          >
            <h3 style={{ margin: '0 0 1rem 0', color: '#fff', fontSize: '1.4rem' }}>{topic.heading}</h3>

            {topic.concepts && topic.concepts.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <strong style={{ color: '#ccc', fontSize: '0.9rem' }}>Key Concepts:</strong>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.5rem' }}>
                  {topic.concepts.map((concept, idx) => (
                    <span
                      key={idx}
                      style={{
                        background: 'rgba(185, 100%, 50%, 0.2)',
                        color: 'hsl(185, 100%, 70%)',
                        padding: '0.3rem 0.8rem',
                        borderRadius: '20px',
                        fontSize: '0.85rem',
                        border: '1px solid rgba(185, 100%, 50%, 0.3)',
                      }}
                    >
                      {concept}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div
              style={{
                marginBottom: '1rem',
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '1rem',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
              }}
            >
              <strong style={{ color: '#ccc', fontSize: '0.9rem' }}>Summary:</strong>
              <p
                style={{
                  margin: '0.5rem 0 0 0',
                  color: topic.summary ? '#ddd' : '#888',
                  lineHeight: '1.5',
                  fontSize: '0.95rem',
                  fontStyle: topic.summary ? 'normal' : 'italic',
                }}
              >
                {topic.summary || 'Summary not available for this topic.'}
              </p>
            </div>

            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.8rem', color: '#999' }}>
              <span>{topic.stats?.num_chunks || 0} chunks</span>
              <span>Avg: {Math.round(topic.stats?.mean_size || 0)} words</span>
            </div>

            <div
              style={{
                marginTop: '1rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.5rem',
              }}
            >
              <button
                onClick={() => handleExpandCluster(topicId)}
                style={{
                  ...buttonStyle,
                  background: 'hsl(185, 100%, 50%)',
                }}
              >
                {topic.bullet_points ? 'Regenerate Insights' : 'Expand Cluster for More Insights'}
              </button>
            </div>

            {topic.bullet_points && topic.bullet_points.length > 0 && (
              <div
                style={{
                  marginTop: '1rem',
                  padding: '1rem',
                  background: 'rgba(255, 255, 255, 0.04)',
                  borderRadius: '8px',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                }}
              >
                <strong style={{ color: '#ccc', fontSize: '0.9rem' }}>Key Bullet Points:</strong>
                {renderBulletPoints(topic.bullet_points, topicId)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default memo(TopicResults);
