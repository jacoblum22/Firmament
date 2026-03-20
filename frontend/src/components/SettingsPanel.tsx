import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import apiService, { LlmStatus } from '../services/apiService';

const KEY_STORAGE = 'firmament_openai_key';
const URL_STORAGE = 'firmament_llm_base_url';
const MODEL_STORAGE = 'firmament_llm_model';

interface ProviderPreset {
  label: string;
  baseUrl: string;
  placeholder: string;
  models: string[];
}

const PRESETS: Record<string, ProviderPreset> = {
  openai: { label: 'OpenAI', baseUrl: '', placeholder: 'sk-...', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4.1-nano'] },
  groq: { label: 'Groq', baseUrl: 'https://api.groq.com/openai/v1', placeholder: 'gsk_...', models: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'mixtral-8x7b-32768'] },
  openrouter: { label: 'OpenRouter', baseUrl: 'https://openrouter.ai/api/v1', placeholder: 'sk-or-...', models: ['openai/gpt-4o-mini', 'meta-llama/llama-3.3-70b-instruct', 'anthropic/claude-3.5-sonnet'] },
  together: { label: 'Together AI', baseUrl: 'https://api.together.xyz/v1', placeholder: 'tok_...', models: ['meta-llama/Llama-3.3-70B-Instruct-Turbo', 'mistralai/Mixtral-8x7B-Instruct-v0.1'] },
  custom: { label: 'Custom', baseUrl: '', placeholder: 'API key', models: [] },
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '7px 10px',
  fontSize: '12px',
  background: 'rgba(255,255,255,0.08)',
  border: '1px solid rgba(255,255,255,0.15)',
  borderRadius: '6px',
  color: '#fff',
  outline: 'none',
  boxSizing: 'border-box',
};

const labelStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'rgba(255,255,255,0.6)',
  display: 'block',
  marginBottom: '4px',
  marginTop: '10px',
};

export const SettingsPanel: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  const [provider, setProvider] = useState('openai');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [model, setModel] = useState('');
  const [saved, setSaved] = useState(false);
  const [llmStatus, setLlmStatus] = useState<LlmStatus | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setApiKey(localStorage.getItem(KEY_STORAGE) || '');
    setBaseUrl(localStorage.getItem(URL_STORAGE) || '');
    setModel(localStorage.getItem(MODEL_STORAGE) || '');
    const storedUrl = localStorage.getItem(URL_STORAGE) || '';
    const found = Object.entries(PRESETS).find(([k, v]) => k !== 'custom' && v.baseUrl && storedUrl === v.baseUrl);
    setProvider(found ? found[0] : storedUrl ? 'custom' : 'openai');
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      apiService.getLlmStatus().then(setLlmStatus).catch(() => {});
    }
  }, [isOpen]);

  const handleProviderChange = (key: string) => {
    setProvider(key);
    const preset = PRESETS[key];
    if (key !== 'custom') {
      setBaseUrl(preset.baseUrl);
      if (preset.models.length > 0) setModel(preset.models[0]);
    }
  };

  const handleSave = () => {
    const trimmedKey = apiKey.trim();
    const trimmedUrl = baseUrl.trim();
    const trimmedModel = model.trim();
    if (trimmedKey) localStorage.setItem(KEY_STORAGE, trimmedKey);
    else localStorage.removeItem(KEY_STORAGE);
    if (trimmedUrl) localStorage.setItem(URL_STORAGE, trimmedUrl);
    else localStorage.removeItem(URL_STORAGE);
    if (trimmedModel) localStorage.setItem(MODEL_STORAGE, trimmedModel);
    else localStorage.removeItem(MODEL_STORAGE);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleClear = () => {
    localStorage.removeItem(KEY_STORAGE);
    localStorage.removeItem(URL_STORAGE);
    localStorage.removeItem(MODEL_STORAGE);
    setApiKey(''); setBaseUrl(''); setModel('');
    setProvider('openai');
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const preset = PRESETS[provider];
  const serverHasKey = llmStatus?.has_server_key ?? false;
  const hasStoredConfig = !!(localStorage.getItem(KEY_STORAGE) || localStorage.getItem(URL_STORAGE));

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <div style={{ position: 'fixed', inset: 0, zIndex: 1100 }} onClick={onClose} />
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'absolute', right: 0, top: '100%', marginTop: '8px',
              width: '360px',
              background: 'linear-gradient(135deg, #1c1917, #292524)',
              borderRadius: '12px',
              boxShadow: 'rgba(0,0,0,0.24) 0px 3px 8px, rgba(0,0,0,0.1) 0px 8px 24px',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              zIndex: 1200, padding: '16px',
              fontFamily: '"Inter", sans-serif',
              maxHeight: '80vh', overflowY: 'auto',
            }}
          >
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff', marginBottom: '8px' }}>
              AI Provider Settings
            </div>

            {serverHasKey && (
              <div style={{
                fontSize: '11px', color: 'rgba(34, 197, 94, 0.9)', marginBottom: '10px',
                padding: '6px 8px', background: 'rgba(34,197,94,0.08)', borderRadius: '6px',
              }}>
                Server has a default key &mdash; settings below are optional overrides
              </div>
            )}

            {/* Provider selector */}
            <label style={labelStyle}>Provider</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '2px' }}>
              {Object.entries(PRESETS).map(([key, p]) => (
                <button
                  key={key}
                  onClick={() => handleProviderChange(key)}
                  style={{
                    padding: '4px 10px', fontSize: '11px',
                    fontWeight: provider === key ? 600 : 400,
                    background: provider === key ? 'rgba(245,158,11,0.2)' : 'rgba(255,255,255,0.06)',
                    color: provider === key ? '#f59e0b' : 'rgba(255,255,255,0.6)',
                    border: `1px solid ${provider === key ? 'rgba(245,158,11,0.4)' : 'rgba(255,255,255,0.1)'}`,
                    borderRadius: '6px', cursor: 'pointer',
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {/* API Key */}
            <label style={labelStyle}>API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={preset.placeholder}
              style={{ ...inputStyle, border: `1px solid ${apiKey ? 'rgba(245,158,11,0.4)' : 'rgba(255,255,255,0.15)'}` }}
            />

            {/* Base URL */}
            {provider !== 'openai' && (
              <>
                <label style={labelStyle}>Base URL</label>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="https://api.example.com/v1"
                  style={inputStyle}
                />
              </>
            )}

            {/* Model */}
            <label style={labelStyle}>Model</label>
            {preset.models.length > 0 ? (
              <select
                value={preset.models.includes(model) ? model : ''}
                onChange={(e) => setModel(e.target.value)}
                style={{ ...inputStyle, appearance: 'auto' }}
              >
                <option value="">Default</option>
                {preset.models.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="Model name (e.g. llama3.1)"
                style={inputStyle}
              />
            )}

            <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.35)', marginTop: '6px' }}>
              Stored in your browser. Sent with AI requests &mdash; never stored on the server.
            </div>

            {/* Buttons */}
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSave}
                style={{
                  flex: 1, padding: '8px', fontSize: '13px', fontWeight: 600,
                  background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                  color: '#fff', border: 'none', borderRadius: '8px', cursor: 'pointer',
                }}
              >
                {saved ? 'Saved!' : 'Save'}
              </motion.button>
              {hasStoredConfig && (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleClear}
                  style={{
                    padding: '8px 12px', fontSize: '13px', fontWeight: 600,
                    background: 'rgba(255,255,255,0.08)',
                    color: 'rgba(255,255,255,0.7)',
                    border: '1px solid rgba(255,255,255,0.15)',
                    borderRadius: '8px', cursor: 'pointer',
                  }}
                >
                  Clear
                </motion.button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
