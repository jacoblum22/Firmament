import React from 'react';
import { motion } from 'framer-motion';

/**
 * Props interface for ConnectionScreen component
 */
export interface ConnectionScreenProps {
  /** Whether the app is still initializing the connection */
  isInitializing: boolean;
  /** Whether the backend is reachable */
  isBackendReachable: boolean;
  /** Function to force a health check/retry connection */
  forceHealthCheck: () => void;
}

/**
 * Styles for the ConnectionScreen component
 */
const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
    fontFamily: '"Outfit", sans-serif',
    background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%)',
    color: '#fff'
  },
  logo: {
    fontSize: '3rem',
    marginBottom: '1rem',
    textAlign: 'center' as const
  },
  statusMessage: {
    textAlign: 'center' as const,
    marginBottom: '3rem'
  },
  gradientText: {
    fontSize: '1.5rem',
    marginBottom: '1rem',
    background: 'linear-gradient(135deg, hsl(185, 100%, 70%), hsl(315, 100%, 70%))',
    backgroundClip: 'text',
    color: 'transparent',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent'
  },
  animatedDots: {
    fontSize: '1.2rem',
    color: '#888'
  },
  statusDetails: {
    background: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    padding: '2rem',
    backdropFilter: 'blur(10px)',
    textAlign: 'center' as const,
    maxWidth: '400px',
    marginBottom: '2rem'
  },
  retryButton: {
    background: 'linear-gradient(135deg, hsl(185, 100%, 50%), hsl(200, 100%, 60%))',
    border: 'none',
    borderRadius: '12px',
    padding: '1rem 2rem',
    color: '#fff',
    fontSize: '1.1rem',
    fontWeight: '600',
    cursor: 'pointer',
    boxShadow: '0 4px 20px rgba(0, 150, 255, 0.3)',
    fontFamily: 'inherit'
  },
  footer: {
    marginTop: '3rem',
    color: '#666',
    fontSize: '0.9rem',
    textAlign: 'center' as const
  }
};

/**
 * Connection screen component that displays connection status and retry options
 * Shown when the app is initializing or when the backend is unreachable
 */
export const ConnectionScreen: React.FC<ConnectionScreenProps> = ({
  isInitializing,
  isBackendReachable,
  forceHealthCheck
}) => {
  return (
    <div style={styles.container}>
      {/* Logo/Branding */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="label"
        style={styles.logo}
      >
        MyStudyMate
      </motion.div>

      {/* Status Message */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
        style={styles.statusMessage}
      >
        <div style={styles.gradientText}>
          Connecting to StudyMate...
        </div>
        
        {/* Animated dots */}
        <div style={styles.animatedDots}>
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 0 }}
          >
            •
          </motion.span>
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 0.5 }}
            style={{ margin: '0 0.5rem' }}
          >
            •
          </motion.span>
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.5, repeat: Infinity, delay: 1 }}
          >
            •
          </motion.span>
        </div>
      </motion.div>

      {/* Status Details */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        style={styles.statusDetails}
      >
        <div style={{ marginBottom: '1rem', fontSize: '1.1rem' }}>
          {!navigator.onLine ? (
            <>
              <div style={{ color: '#ff6b6b', marginBottom: '0.5rem' }}>
                🌐 No Internet Connection
              </div>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                Please check your internet connection and try again.
              </div>
            </>
          ) : isInitializing ? (
            <>
              <div style={{ color: '#6bcf7f', marginBottom: '0.5rem' }}>
                ✅ Establishing Connection
              </div>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                Just a moment while we connect to StudyMate...
              </div>
            </>
          ) : !isBackendReachable ? (
            <>
              <div style={{ color: '#ffd93d', marginBottom: '0.5rem' }}>
                🔧 Backend Unavailable
              </div>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                The StudyMate server is currently unreachable. We're working to reconnect automatically.
              </div>
            </>
          ) : (
            <>
              <div style={{ color: '#6bcf7f', marginBottom: '0.5rem' }}>
                ✅ Connection Established
              </div>
              <div style={{ color: '#888', fontSize: '0.9rem' }}>
                Connected to StudyMate! Redirecting...
              </div>
            </>
          )}
        </div>
      </motion.div>

      {/* Retry Button */}
      <motion.button
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={forceHealthCheck}
        style={styles.retryButton}
      >
        🔄 Retry Connection
      </motion.button>

      {/* Footer message */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.8 }}
        style={styles.footer}
      >
        StudyMate automatically retries the connection every few seconds.
      </motion.div>
    </div>
  );
};

export default ConnectionScreen;
