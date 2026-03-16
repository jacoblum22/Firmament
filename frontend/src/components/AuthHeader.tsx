import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { GoogleSignInButton } from './GoogleSignInButton';
import { UserProfile } from './UserProfile';

export const AuthHeader: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

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
      {isAuthenticated ? (
        <UserProfile />
      ) : (
        <GoogleSignInButton 
          disabled={isLoading}
          onSuccess={() => {
            console.log('Sign-in successful');
          }}
          onError={(error) => {
            console.error('Sign-in error:', error);
          }}
        />
      )}
    </div>
  );
};
