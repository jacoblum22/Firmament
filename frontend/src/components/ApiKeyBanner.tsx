import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import apiService from '../services/apiService';

const KEY_STORAGE = 'firmament_openai_key';

export const ApiKeyBanner: React.FC<{ onOpenSettings: () => void }> = ({ onOpenSettings }) => {
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    // Only show if no key is stored and server requires one
    const stored = localStorage.getItem(KEY_STORAGE);
    if (stored || dismissed) { setVisible(false); return; }

    apiService.getLlmStatus().then((status) => {
      setVisible(status.requires_user_key);
    }).catch(() => {});
  }, [dismissed]);

  if (!visible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        style={{
          margin: '0 2rem',
          padding: '10px 16px',
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          fontFamily: '"Inter", sans-serif',
        }}
      >
        <span style={{ fontSize: '18px' }}>🔑</span>
        <div style={{ flex: 1, fontSize: '13px', color: 'rgba(255,255,255,0.85)' }}>
          <strong>API key needed</strong> — add your OpenAI, Groq, or other provider key to generate topics.
        </div>
        <button
          onClick={onOpenSettings}
          style={{
            padding: '5px 14px',
            fontSize: '12px',
            fontWeight: 600,
            background: 'linear-gradient(135deg, #f59e0b, #d97706)',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          Open Settings
        </button>
        <button
          onClick={() => { setDismissed(true); setVisible(false); }}
          style={{
            background: 'none',
            border: 'none',
            color: 'rgba(255,255,255,0.4)',
            fontSize: '16px',
            cursor: 'pointer',
            padding: '0 4px',
          }}
        >
          ×
        </button>
      </motion.div>
    </AnimatePresence>
  );
};
