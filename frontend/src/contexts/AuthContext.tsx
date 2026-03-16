import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';

// User interface
export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

// JWT payload interface
interface JWTPayload {
  sub: string;
  email: string;
  name: string;
  picture?: string;
  exp: number;
  iat: number;
}

// Auth context interface
interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  signInWithGoogle: () => Promise<void>;
  signOut: () => void;
}

// Create the context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Custom hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth provider props
interface AuthProviderProps {
  children: ReactNode;
}

// Backend API base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is authenticated
  const isAuthenticated = !!user && !!token;

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    try {
      // Check for stored token
      const storedToken = localStorage.getItem('studymate_token');
      if (storedToken) {
        // Verify token is still valid
        if (isTokenValid(storedToken)) {
          const userData = getUserFromToken(storedToken);
          setToken(storedToken);
          setUser(userData);
        } else {
          // Token expired, remove it
          localStorage.removeItem('studymate_token');
        }
      }
    } catch (error) {
      console.error('Auth initialization error:', error);
      localStorage.removeItem('studymate_token');
    } finally {
      setIsLoading(false);
    }
  };

  const isTokenValid = (token: string): boolean => {
    try {
      const decoded = jwtDecode<JWTPayload>(token);
      const currentTime = Date.now() / 1000;
      return decoded.exp > currentTime;
    } catch {
      return false;
    }
  };

  const getUserFromToken = (token: string): User => {
    const decoded = jwtDecode<JWTPayload>(token);
    return {
      id: decoded.sub,
      email: decoded.email,
      name: decoded.name,
      picture: decoded.picture,
    };
  };

  const signInWithGoogle = async (): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        setIsLoading(true);
        if (import.meta.env.DEV) console.log('Starting Google sign-in process...');
        
        // Set a timeout to reset loading state if no response is received
        const timeoutId = setTimeout(() => {
          if (import.meta.env.DEV) console.log('Google sign-in timeout - resetting loading state');
          setIsLoading(false);
          reject(new Error('Sign-in timeout'));
        }, 15000); // 15 second timeout (increased from 5 seconds)
        
        const initializeGoogleAuth = async () => {
          // Load Google Sign-In script if not already loaded
          if (!window.google) {
            if (import.meta.env.DEV) console.log('Loading Google script...');
            await loadGoogleScript();
          }

          if (import.meta.env.DEV) {
            console.log('Initializing Google ID...');
            console.log('Google Client ID:', import.meta.env.VITE_GOOGLE_CLIENT_ID);
          }
          
          // Initialize Google ID
          window.google.accounts.id.initialize({
            client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
            callback: async (response: { credential: string; select_by: string }) => {
              clearTimeout(timeoutId);
              if (import.meta.env.DEV) console.log('Google ID response received:', response);
              try {
                if (!response.credential) {
                  throw new Error('No credential received from Google');
                }
                
                if (import.meta.env.DEV) console.log('Sign-in successful. Processing credential...');
                await handleGoogleSignIn(response);
                resolve();
              } catch (error) {
                console.error('Authentication error:', error);
                setIsLoading(false);
                reject(error);
              }
            },
            auto_select: false,
            cancel_on_tap_outside: true,
          });

          if (import.meta.env.DEV) console.log('Rendering Google sign-in button...');
          // Create a temporary container for the Google button
          const buttonContainer = document.createElement('div');
          buttonContainer.style.position = 'fixed';
          buttonContainer.style.top = '-9999px';
          buttonContainer.id = 'google-signin-button-temp';
          document.body.appendChild(buttonContainer);

          // Render the Google sign-in button
          window.google.accounts.id.renderButton(buttonContainer, {
            theme: 'outline',
            size: 'large',
            text: 'signin_with',
            shape: 'rectangular',
          });

          // Programmatically click the button
          setTimeout(() => {
            const button = buttonContainer.querySelector('div[role="button"]') as HTMLElement;
            if (button) {
              if (import.meta.env.DEV) console.log('Clicking Google sign-in button...');
              button.click();
            } else {
              // Fallback to prompt
              if (import.meta.env.DEV) console.log('Button not found, using prompt...');
              window.google.accounts.id.prompt();
            }
            
            // Clean up the temporary button after a delay
            setTimeout(() => {
              if (buttonContainer && buttonContainer.parentNode) {
                buttonContainer.parentNode.removeChild(buttonContainer);
              }
            }, 1000);
          }, 100);
        };

        initializeGoogleAuth().catch((error) => {
          clearTimeout(timeoutId);
          setIsLoading(false);
          reject(error);
        });
      } catch (error) {
        console.error('Google sign-in error:', error);
        setIsLoading(false);
        reject(error);
      }
    });
  };

  const handleGoogleSignIn = async (response: { credential: string; select_by: string }) => {
    if (import.meta.env.DEV) console.log('Google sign-in response received:', response);
    try {
      if (import.meta.env.DEV) console.log('Sending request to backend:', `${API_BASE_URL}/auth/google`);
      
      // Send Google token to our backend
      const backendResponse = await fetch(`${API_BASE_URL}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: response.credential,
        }),
      });

      if (import.meta.env.DEV) console.log('Backend response status:', backendResponse.status);
      
      if (!backendResponse.ok) {
        const errorText = await backendResponse.text();
        if (import.meta.env.DEV) console.error('Backend error response:', errorText);
        throw new Error(`Backend authentication failed: ${backendResponse.status} ${errorText}`);
      }

      // Validate response is JSON
      const contentType = backendResponse.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Invalid response format from backend');
      }

      const data = await backendResponse.json();
      if (import.meta.env.DEV) console.log('Backend success response:', data);
      
      // Store the JWT token (backend returns 'session_token')
      localStorage.setItem('studymate_token', data.session_token);
      setToken(data.session_token);
      
      // Extract user data from token
      const userData = getUserFromToken(data.session_token);
      setUser(userData);
      if (import.meta.env.DEV) console.log('Authentication successful for user:', userData);
    } catch (error) {
      console.error('Authentication error:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    try {
      // Call backend logout endpoint
      if (token) {
        await fetch(`${API_BASE_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state
      localStorage.removeItem('studymate_token');
      setToken(null);
      setUser(null);
      
      // Sign out from Google
      if (window.google) {
        window.google.accounts.id.disableAutoSelect();
      }
    }
  };

  const loadGoogleScript = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (document.getElementById('google-signin-script')) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.id = 'google-signin-script';
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error('Failed to load Google Sign-In script'));
      document.head.appendChild(script);
    });
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated,
    signInWithGoogle,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Extend Window interface for Google Sign-In
declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string; select_by: string }) => void;
            auto_select?: boolean;
            cancel_on_tap_outside?: boolean;
          }) => void;
          renderButton: (container: HTMLElement, options: { theme: string; size: string; text: string; shape: string }) => void;
          prompt: () => void;
          disableAutoSelect: () => void;
        };
      };
    };
  }
}
