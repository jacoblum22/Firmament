import { motion } from 'framer-motion';
import { BRAND } from '../constants';
import { GoogleSignInButton } from './GoogleSignInButton';

type SignInScreenProps = {
  isLoading: boolean;
  successMessage: string | null;
  setSuccessMessage: React.Dispatch<React.SetStateAction<string | null>>;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
};

export function SignInScreen({ isLoading, successMessage, setSuccessMessage, setError }: SignInScreenProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '70vh',
        padding: '2rem',
        fontFamily: '"Outfit", sans-serif',
        textAlign: 'center',
        marginTop: '-3rem',
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <div
          className="label"
          style={{
            fontSize: '4.5rem',
            marginBottom: '-1rem',
            color: '#ffffff',
            fontWeight: '700',
            letterSpacing: '-0.02em',
          }}
        >
          {BRAND.NAME}
        </div>
        <div
          className="glow-text"
          data-text="Smarter Studying Starts Here."
          style={{
            fontSize: '2.5rem',
            marginBottom: '2rem',
            color: 'rgba(255, 255, 255, 0.9)',
            fontWeight: '500',
            letterSpacing: '-0.01em',
          }}
        >
          Smarter Studying Starts Here.
        </div>
        <p
          style={{
            fontSize: '1.2rem',
            color: '#ffffff',
            marginBottom: '3rem',
            maxWidth: '600px',
            lineHeight: '1.7',
            fontWeight: '400',
          }}
        >
          Upload your study materials and let AI help you create comprehensive study guides, summarize topics,
          and expand on key concepts.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div style={{ width: 'fit-content' }}>
            <GoogleSignInButton
              size="large"
              disabled={isLoading}
              onSuccess={() => {
                setSuccessMessage(`Successfully signed in! Welcome to ${BRAND.NAME}.`);
                setError(null);
                setTimeout(() => setSuccessMessage(null), 5000);
              }}
              onError={(error) => {
                console.error('Sign-in error:', error);
                setSuccessMessage(null);
                setError(
                  JSON.stringify({
                    title: 'Sign-in Failed',
                    details: error.message || 'Failed to sign in with Google. Please try again.',
                    action: 'Please check your internet connection and try again.',
                  })
                );
              }}
            />
          </div>
        </div>

        {successMessage && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            style={{
              marginTop: '1.5rem',
              padding: '1rem 1.5rem',
              backgroundColor: 'rgba(34, 197, 94, 0.1)',
              border: '1px solid rgba(34, 197, 94, 0.3)',
              borderRadius: '12px',
              color: 'rgb(34, 197, 94)',
              textAlign: 'center',
              fontFamily: '"Outfit", sans-serif',
              fontSize: '0.95rem',
              fontWeight: '500',
              backdropFilter: 'blur(8px)',
            }}
          >
            ✅ {successMessage}
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
