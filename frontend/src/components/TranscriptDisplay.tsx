import { memo } from 'react';
import { motion } from 'framer-motion';
import { UploadResponse } from '../services/apiService';

type TranscriptDisplayProps = {
  response: UploadResponse;
};

export function TranscriptDisplay({ response }: TranscriptDisplayProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        marginTop: '3rem',
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%)',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        padding: '2rem',
        backdropFilter: 'blur(10px)',
      }}
    >
      <div
        style={{
          marginBottom: '2rem',
          background: 'rgba(0, 0, 0, 0.3)',
          borderRadius: '12px',
          padding: '1.5rem',
          border: '1px solid rgba(255, 255, 255, 0.1)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, hsl(185, 100%, 50%), hsl(200, 100%, 60%))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.2rem',
            }}
          >
            📄
          </div>
          <div>
            <h3 style={{ margin: 0, color: '#fff', fontSize: '1.2rem', fontWeight: '600' }}>
              File Successfully Processed
            </h3>
            <p style={{ margin: '0.2rem 0 0 0', color: '#999', fontSize: '0.9rem' }}>
              Ready for analysis and topic extraction
            </p>
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ccc' }}>
            <span style={{ fontSize: '0.9rem' }}>📁</span>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#999' }}>Filename</div>
              <div style={{ fontSize: '0.95rem', fontWeight: '500' }}>{response.filename}</div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ccc' }}>
            <span style={{ fontSize: '0.9rem' }}>🏷️</span>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#999' }}>File Type</div>
              <div style={{ fontSize: '0.95rem', fontWeight: '500' }}>{response.filetype}</div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ccc' }}>
            <span style={{ fontSize: '0.9rem' }}>✅</span>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#999' }}>Status</div>
              <div style={{ fontSize: '0.95rem', fontWeight: '500', color: '#4ade80' }}>{response.message}</div>
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, fontSize: '1.3rem', fontWeight: '600', color: '#fff' }}>
            📄 Extracted Transcript
          </h2>
          <div
            style={{
              background: 'rgba(185, 255, 255, 0.1)',
              color: 'hsl(185, 100%, 70%)',
              padding: '0.3rem 0.8rem',
              borderRadius: '20px',
              fontSize: '0.8rem',
              fontWeight: '500',
              border: '1px solid rgba(185, 255, 255, 0.2)',
            }}
          >
            {response.text ? `${Math.round(response.text.length / 1000)}k characters` : '0 characters'}
          </div>
        </div>

        <div
          style={{
            background: 'rgba(0, 0, 0, 0.4)',
            borderRadius: '12px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              padding: '0.75rem 1rem',
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#ef4444',
              }}
            ></div>
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#f59e0b',
              }}
            ></div>
            <div
              style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#10b981',
              }}
            ></div>
            <span
              style={{
                marginLeft: '0.5rem',
                fontSize: '0.8rem',
                color: '#999',
                fontFamily: 'monospace',
              }}
            >
              transcript.txt
            </span>
          </div>

          <div style={{ maxHeight: '400px', overflowY: 'auto', padding: '1.5rem', lineHeight: '1.6' }}>
            <pre
              style={{
                margin: 0,
                fontFamily: "'Fira Code', 'Consolas', monospace",
                fontSize: '0.9rem',
                color: '#e5e5e5',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {response.text || 'No transcript content available'}
            </pre>
          </div>
        </div>

        <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: '#888', textAlign: 'center' }}>
          💡 This transcript will be segmented and analyzed for key topics below
        </div>
      </div>
    </motion.div>
  );
}

export default memo(TranscriptDisplay);
