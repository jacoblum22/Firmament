import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import styles from './GoogleSignInButton.module.css';

/**
 * Animation configuration for the Google Sign-In button glow effect.
 * 
 * This configuration defines the timing synchronization between the CSS animation
 * and JavaScript timing logic to ensure smooth transitions when users hover in/out.
 */
const ANIMATION_CONFIG = {
  /**
   * Total duration of one complete animation cycle in milliseconds.
   * Must match the CSS animation duration (4.5s).
   */
  DURATION_MS: 4500,
  
  /**
   * Animation delay in seconds - corresponds to CSS animation-delay: -0.75s.
   * This makes the animation start at the 16.7% keyframe (first zero-opacity point).
   */
  DELAY_SECONDS: 0.75,
  
  /**
   * Animation delay in milliseconds for JavaScript calculations.
   */
  DELAY_MS: 750,
  
  /**
   * Keyframe percentages where glow opacity reaches zero (transition points).
   * These correspond to the keyframes in the CSS animation where opacity = 0.
   */
  ZERO_OPACITY_KEYFRAMES: [16.7, 50, 83.3],
  
  /**
   * Minimum transition time to ensure visible animation before state change.
   */
  MIN_TRANSITION_MS: 50,
  
  /**
   * Fallback timeout when animation start time is not recorded.
   */
  FALLBACK_TIMEOUT_MS: 750,
};

/**
 * Calculated timing points in milliseconds for zero-opacity keyframes.
 * These are derived from ZERO_OPACITY_KEYFRAMES percentages × DURATION_MS.
 */
const ZERO_OPACITY_POINTS_MS = ANIMATION_CONFIG.ZERO_OPACITY_KEYFRAMES.map(
  percentage => (percentage / 100) * ANIMATION_CONFIG.DURATION_MS
);

/**
 * Button size variants with explicit styling configurations.
 * This replaces the complex ternary expressions and external CSS dependencies.
 */
type ButtonSize = 'small' | 'default' | 'large';

/**
 * Size configuration mapping for consistent styling across all button variants.
 * Eliminates code duplication and makes size management centralized.
 */
const SIZE_CONFIG: Record<ButtonSize, {
  padding: string;
  paddingLeft: string;
  fontSize: string;
  iconSize: string;
}> = {
  small: {
    padding: '8px 16px',
    paddingLeft: '12px',
    fontSize: '14px',
    iconSize: '16px'
  },
  default: {
    padding: '12px 24px',
    paddingLeft: '20px',
    fontSize: '16px',
    iconSize: '20px'
  },
  large: {
    padding: '16px 28px',
    paddingLeft: '24px',
    fontSize: '18px',
    iconSize: '24px'
  }
};

/**
 * Returns the appropriate size configuration based on the size prop and className.
 * Maintains backward compatibility with className-based sizing while preferring explicit size prop.
 */
const getSizeConfig = (size: ButtonSize, className?: string) => {
  // Explicit warning for deprecated usage
  if (className?.includes('text-xs') && size === 'default') {
    console.warn(
      'Using className for size detection is deprecated. Use the size prop instead.'
    );
    return SIZE_CONFIG.small;
  }
  return SIZE_CONFIG[size];
};
interface GoogleSignInButtonProps {
  onSuccess?: () => void;
  onError?: (error: Error) => void;
  disabled?: boolean;
  className?: string;
  size?: ButtonSize;
}

export const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSuccess,
  onError,
  disabled = false,
  className = "",
  size = 'default',
}) => {
  const { signInWithGoogle, isLoading } = useAuth();
  const [isHovering, setIsHovering] = useState(false);
  const [isFinishing, setIsFinishing] = useState(false);
  const finishTimeoutRef = useRef<number | null>(null);
  const animationStartTimeRef = useRef<number | null>(null);

  // Get the appropriate size configuration
  const sizeConfig = getSizeConfig(size, className);

  const handleSignIn = async () => {
    try {
      await signInWithGoogle();
      onSuccess?.();
    } catch (error) {
      onError?.(error as Error);
    }
  };

  const handleMouseEnter = () => {
    if (finishTimeoutRef.current) {
      clearTimeout(finishTimeoutRef.current);
      finishTimeoutRef.current = null;
    }
    setIsFinishing(false);
    setIsHovering(true);
    
    /**
     * Synchronize JavaScript timing with CSS animation cycle.
     * 
     * The CSS animation uses animation-delay: -0.75s, which means it starts
     * at the 16.7% keyframe (first zero-opacity point). To align our JavaScript
     * timing calculations with this offset, we subtract the delay from the
     * current timestamp when recording the animation start time.
     */
    animationStartTimeRef.current = Date.now() - ANIMATION_CONFIG.DELAY_MS;
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    setIsFinishing(true);
    
    if (animationStartTimeRef.current) {
      /**
       * Calculate optimal timing for smooth animation exit.
       * 
       * When the user stops hovering, we want to transition the glow animation
       * to its "finishing" state at a natural point in the animation cycle.
       * The smoothest transitions occur at zero-opacity keyframes where the
       * glow effect is invisible, making the state change imperceptible.
       * 
       * Mathematical relationships:
       * - Animation cycle: 0% → 16.7% → 33.3% → 50% → 66.7% → 83.3% → 100%
       * - Zero-opacity points: 16.7%, 50%, 83.3% (transition opportunities)
       * - Timing formula: (keyframe_percentage / 100) × total_duration_ms
       */
      const currentTime = Date.now();
      const elapsed = currentTime - animationStartTimeRef.current;
      
      // Calculate current position within the animation cycle (0 to DURATION_MS)
      const currentPosition = elapsed % ANIMATION_CONFIG.DURATION_MS;
      
      // Find the nearest future zero-opacity point for smooth transition
      let timeToTarget = ANIMATION_CONFIG.DURATION_MS; // Default: complete full cycle
      
      for (const point of ZERO_OPACITY_POINTS_MS) {
        if (point > currentPosition) {
          const timeToThisPoint = point - currentPosition;
          if (timeToThisPoint < timeToTarget) {
            timeToTarget = timeToThisPoint;
          }
        }
      }
      
      /**
       * Handle cycle boundary case.
       * If no zero-opacity points remain in the current cycle,
       * transition at the first point of the next cycle.
       */
      if (timeToTarget === ANIMATION_CONFIG.DURATION_MS) {
        timeToTarget = ANIMATION_CONFIG.DURATION_MS - currentPosition + ZERO_OPACITY_POINTS_MS[0];
      }
      
      // Ensure minimum transition time for visual feedback
      timeToTarget = Math.max(timeToTarget, ANIMATION_CONFIG.MIN_TRANSITION_MS);
      
      finishTimeoutRef.current = window.setTimeout(() => {
        setIsFinishing(false);
      }, timeToTarget);
    } else {
      // Fallback: no animation start time recorded
      finishTimeoutRef.current = window.setTimeout(() => {
        setIsFinishing(false);
      }, ANIMATION_CONFIG.FALLBACK_TIMEOUT_MS);
    }
  };

  useEffect(() => {
    return () => {
      if (finishTimeoutRef.current) {
        clearTimeout(finishTimeoutRef.current);
      }
    };
  }, []);

  const buttonStyle: React.CSSProperties = {
    marginLeft: "1rem",
    padding: "0.5rem 1rem",
    color: "white",
    border: "none",
    cursor: "pointer",
  };

  return (
    <motion.button
        whileHover={{ 
          scale: 1.02, 
          y: -2
        }}
        whileTap={{ scale: 0.98 }}
        onClick={handleSignIn}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        disabled={disabled || isLoading}
        className={
          disabled || isLoading 
            ? '' 
            : `${styles.button} ${isHovering ? styles.hovering : ''} ${isFinishing ? styles.finishing : ''}`
        }
          style={{
        ...buttonStyle,
        minWidth: "240px",
        maxWidth: "240px",
        padding: sizeConfig.padding,
        paddingLeft: sizeConfig.paddingLeft,
        fontSize: sizeConfig.fontSize,
        fontWeight: "600",
        background: disabled || isLoading 
          ? "#f3f4f6"
          : "#ffffff",
        color: disabled || isLoading ? '#9ca3af' : '#000000',
        opacity: disabled || isLoading ? 0.6 : 1,
        borderRadius: "12px",
        border: disabled || isLoading ? '2px solid #e5e7eb' : '2px solid #e5e7eb',
        cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        whiteSpace: 'nowrap',
        boxShadow: disabled || isLoading 
          ? 'rgba(0, 0, 0, 0.1) 0px 2px 4px'
          : 'rgba(0, 0, 0, 0.1) 0px 4px 8px',
        transition: 'all 0.3s ease-in-out',
        position: 'relative',
        overflow: 'visible',
        zIndex: 1
      }}
    >
      <svg
        style={{
          width: sizeConfig.iconSize,
          height: sizeConfig.iconSize,
          flexShrink: 0
        }}
        viewBox="0 0 24 24"
        fill="none"
      >
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
      </svg>
      <span style={{
        fontFamily: '"Inter", sans-serif',
        letterSpacing: '-0.05em',
        fontWeight: '600',
        color: disabled || isLoading ? '#9ca3af' : '#000000'
      }}>
        {isLoading ? 'Signing in...' : 'Sign in with Google'}
      </span>
    </motion.button>
  );
};