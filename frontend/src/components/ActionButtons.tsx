import { motion } from 'framer-motion';
import type { CSSProperties } from 'react';

interface ActionButtonsProps {
  handleProcessChunks: () => void;
  handleGenerateHeadings: () => void;
  processedChunks: unknown;
  segmenting: boolean;
  generatingHeadings: boolean;
  buttonStyle: CSSProperties;
}

export default function ActionButtons({
  handleProcessChunks,
  handleGenerateHeadings,
  processedChunks,
  segmenting,
  generatingHeadings,
  buttonStyle,
}: ActionButtonsProps) {
  const hasProcessedChunks = Boolean(processedChunks);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}
    >
      <motion.button
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleProcessChunks}
        disabled={hasProcessedChunks || segmenting}
        style={{
          ...buttonStyle,
          flex: '1',
          minWidth: '250px',
          padding: '1rem 1.5rem',
          fontSize: '1rem',
          fontWeight: '600',
          background: hasProcessedChunks
            ? 'linear-gradient(135deg, #10b981, #059669)'
            : segmenting
              ? 'linear-gradient(135deg, #2563eb, #3b82f6)'
              : 'linear-gradient(135deg, hsl(185, 100%, 50%), hsl(200, 100%, 60%))',
          opacity: hasProcessedChunks ? 0.8 : segmenting ? 0.9 : 1,
          cursor: hasProcessedChunks || segmenting ? 'not-allowed' : 'pointer',
          position: 'relative',
          overflow: 'hidden',
          animation: segmenting ? 'pulse-bg 1.1s ease-in-out infinite' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'center' }}>
          <span style={{ fontSize: '1.1rem' }}>{hasProcessedChunks ? '✅' : segmenting ? '⏳' : '🔧'}</span>
          <span>
            {hasProcessedChunks ? 'Transcript Segmented ✔' : segmenting ? 'Segmenting...' : 'Segment & Optimize Transcript'}
          </span>
          {segmenting && <span className="inline-loading-indicator" aria-hidden="true" />}
        </div>
        {!hasProcessedChunks && !segmenting && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: '-100%',
              width: '100%',
              height: '100%',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
              animation: 'shimmer 2s infinite',
            }}
          />
        )}
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleGenerateHeadings}
        disabled={!hasProcessedChunks || generatingHeadings}
        style={{
          ...buttonStyle,
          flex: '1',
          minWidth: '250px',
          padding: '1rem 1.5rem',
          fontSize: '1rem',
          fontWeight: '600',
          background:
            !hasProcessedChunks || generatingHeadings
              ? 'linear-gradient(135deg, #6b7280, #4b5563)'
              : 'linear-gradient(135deg, hsl(315, 100%, 60%), hsl(330, 100%, 70%))',
          opacity: !hasProcessedChunks || generatingHeadings ? 0.6 : 1,
          cursor: !hasProcessedChunks || generatingHeadings ? 'not-allowed' : 'pointer',
          position: 'relative',
          overflow: 'hidden',
          animation: generatingHeadings ? 'pulse-bg 1.1s ease-in-out infinite' : 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'center' }}>
          <span style={{ fontSize: '1.1rem' }}>{generatingHeadings ? '⏳' : '🧠'}</span>
          <span>{generatingHeadings ? 'Generating Topics...' : 'Generate Topics with AI'}</span>
          {generatingHeadings && <span className="inline-loading-indicator" aria-hidden="true" />}
        </div>
        {hasProcessedChunks && !generatingHeadings && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: '-100%',
              width: '100%',
              height: '100%',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
              animation: 'shimmer 2s infinite',
            }}
          />
        )}
      </motion.button>
    </motion.div>
  );
}
