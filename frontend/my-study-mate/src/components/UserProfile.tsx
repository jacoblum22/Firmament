import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

export const UserProfile: React.FC = () => {
  const { user, signOut, isAuthenticated } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  if (!isAuthenticated || !user) {
    return null;
  }

  const handleSignOut = async () => {
    try {
      await signOut();
      setIsMenuOpen(false);
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return (
    <div className="relative">
      <motion.button
        whileHover={{ scale: 1.02, y: -2 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '12px 20px',
          background: 'linear-gradient(135deg, #f59e0b, #d97706)',
          border: 'none',
          borderRadius: '12px',
          fontSize: '16px',
          fontWeight: '600',
          color: '#ffffff',
          cursor: 'pointer',
          transition: 'all 0.2s ease-in-out',
          whiteSpace: 'nowrap',
          minWidth: '220px',
          boxShadow: 'rgba(0, 0, 0, 0.24) 0px 3px 8px',
          fontFamily: '"Inter", sans-serif',
          letterSpacing: '-0.05em'
        }}
      >
        {user.picture ? (
          <img
            src={user.picture}
            alt={user.name || 'User avatar'}
            style={{
              width: '20px',
              height: '20px',
              borderRadius: '50%',
              flexShrink: 0
            }}
          />
        ) : null}
        <span style={{
          color: '#ffffff',
          fontWeight: '600',
          fontFamily: '"Inter", sans-serif'
        }}>
          {user.name?.split(' ')[0] || 'User'}
        </span>
        <svg
          style={{
            width: '16px',
            height: '16px',
            transform: isMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.2s',
            flexShrink: 0,
            color: '#ffffff'
          }}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </motion.button>

      {isMenuOpen && (
        <>
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 40
            }}
            onClick={() => setIsMenuOpen(false)}
          />
          
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'absolute',
              right: 0,
              marginTop: '8px',
              width: '200px',
              background: 'linear-gradient(135deg, #451a03, #292524)',
              borderRadius: '12px',
              boxShadow: 'rgba(0, 0, 0, 0.24) 0px 3px 8px, rgba(0, 0, 0, 0.1) 0px 8px 24px',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              zIndex: 50,
              overflow: 'hidden'
            }}
          >
            <div style={{ padding: '12px' }}>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSignOut}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '12px 16px',
                  fontSize: '14px',
                  fontWeight: '600',
                  background: 'linear-gradient(135deg, #dc2626, #b91c1c)',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  whiteSpace: 'nowrap',
                  fontFamily: '"Inter", sans-serif',
                  letterSpacing: '-0.05em',
                  boxShadow: 'rgba(0, 0, 0, 0.2) 0px 2px 4px'
                }}
              >
                <svg 
                  style={{ 
                    width: '18px', 
                    height: '18px', 
                    flexShrink: 0,
                    color: '#ffffff'
                  }} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013 3v1" />
                </svg>
                <span style={{
                  color: '#ffffff',
                  fontWeight: '600'
                }}>
                  Sign out
                </span>
              </motion.button>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
};
