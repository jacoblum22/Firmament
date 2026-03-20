import { useState, useImperativeHandle, forwardRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { GoogleSignInButton } from './GoogleSignInButton';
import { UserProfile } from './UserProfile';
import { SettingsPanel } from './SettingsPanel';

export interface AuthHeaderHandle {
  openSettings: () => void;
}

export const AuthHeader = forwardRef<AuthHeaderHandle>((_, ref) => {
  const { isAuthenticated, isLoading } = useAuth();
  const [settingsOpen, setSettingsOpen] = useState(false);

  useImperativeHandle(ref, () => ({
    openSettings: () => setSettingsOpen(true),
  }));

  return (
    <div style={{
      position: "fixed",
      top: "1rem",
      right: "1rem", 
      zIndex: 1001,
      display: "flex",
      flexDirection: "column",
      alignItems: "flex-end",
      gap: "0.5rem"
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {isAuthenticated && (
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setSettingsOpen(!settingsOpen)}
              aria-label="Settings"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '40px',
                height: '40px',
                background: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255,255,255,0.15)',
                borderRadius: '10px',
                cursor: 'pointer',
                color: 'rgba(255,255,255,0.7)',
                transition: 'all 0.2s',
                padding: 0,
              }}
            >
              <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
            <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
          </div>
        )}
        {isAuthenticated ? (
          <UserProfile />
        ) : (
          <GoogleSignInButton 
            disabled={isLoading}
            onSuccess={() => {}}
            onError={(error) => {
              console.error('Sign-in error:', error);
            }}
          />
        )}
      </div>
    </div>
  );
});
