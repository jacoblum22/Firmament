import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import apiService, { LlmStatus } from '../services/apiService';

const STORAGE_KEY = 'firmament_openai_key';

export const SettingsPanel: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const [apiKey, setApiKey] = useState('');
  const [saved, setSaved] = useState(false);
  const [llmStatus, setLlmStatus] = useState<LlmStatus | null>(null);

  useEffect(() => {
    setApiKey(localStorage.getItem(STORAGE_KEY) || '');
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      apiService.getLlmStatus().then(setLlmStatus).catch(() => {});
    }
  }, [isOpen]);

  const handleSave = () => {
    const trimmed = apiKey.trim();
    if (trimmed) {
      localStorage.setItem(STORAGE_KEY, trimmed);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleClear = () => {
    localStorage.removeItem(STORAGE_KEY);
    setApiKey('');
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const providerLabel = llmStatus?.provider === 'ollama' ? 'Ollama (Local)' : 'OpenAI';
  const needsKey = llmStatus?.requires_user_key ?? true;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 1100 }}
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'absolute',
              right: 0,
              top: '100%',
              marginTop: '8px',
              width: '340px',
              background: 'linear-gradient(135deg, #1c1917, #292524)',
              borderRadius: '12px',
              boxShadow: 'rgba(0,0,0,0.24) 0px 3px 8px, rgba(0,0,0,0.1) 0px 8px 24px',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              zIndex: 1200,
              padding: '16px',
              fontFamily: '"Inter", sans-serif',
            }}
          >
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff', marginBottom: '12px' }}>
              LLM Settings
            </div>

            {llmStatus && (
              <div style={{
                fontSize: '12px',
                color: 'rgba(255,255,255,0.6)',
                marginBottom: '12px',
                padding: '8px 10px',
                background: 'rgba(255,255,255,0.05)',
                borderRadius: '8px',
              }}>
                <div>Provider: <span style={{ color: '#f59e0b' }}>{providerLabel}</span></div>
                {llmStatus.has_server_key && (
                  <div style={{ marginTop: '4px', color: 'rgba(34, 197, 94, 0.9)' }}>
                    Server has a default API key configured
                  </div>
                )}
              </div>
            )}

            {needsKey && (
              <>
                <label style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)', display: 'block', marginBottom: '6px' }}>
                  OpenAI API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    fontSize: '13px',
                    background: 'rgba(255,255,255,0.08)',
                    border: '1px solid rgba(255,255,255,0.15)',
                    borderRadius: '8px',
                    color: '#fff',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
                <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.4)', marginTop: '4px' }}>
                  Stored locally in your browser. Never sent to our server.
                </div>

                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleSave}
                    style={{
                      flex: 1,
                      padding: '8px',
                      fontSize: '13px',
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                      color: '#fff',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: 'pointer',
                    }}
                  >
                    {saved ? 'Saved!' : 'Save'}
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleClear}
                    style={{
                      padding: '8px 12px',
                      fontSize: '13px',
                      fontWeight: 600,
                      background: 'rgba(255,255,255,0.08)',
                      color: 'rgba(255,255,255,0.7)',
                      border: '1px solid rgba(255,255,255,0.15)',
                      borderRadius: '8px',
                      cursor: 'pointer',
                    }}
                  >
                    Clear
                  </motion.button>
                </div>
              </>
            )}

            {!needsKey && (
              <div style={{ fontSize: '12px', color: 'rgba(34, 197, 94, 0.9)' }}>
                No API key needed — {providerLabel} is configured on the server.
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
