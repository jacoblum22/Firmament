/**
 * Application constants
 * This file contains reusable constants for the StudyMate application.
 * Centralizing these values makes it easier to maintain consistency
 * and prepare for future internationalization.
 */

/**
 * Brand-related constants
 */
export const BRAND = {
  /** The application/service brand name */
  NAME: 'Firmament',
  
  /** App tagline/slogan */
  TAGLINE: 'Smarter Studying Starts Here',
  
  /** App description for SEO and social media */
  DESCRIPTION: 'Transform your study materials into interactive learning experiences. Upload documents and get AI-powered insights, summaries, and personalized study guides.',
  
  /** Keywords for SEO */
  KEYWORDS: 'study, learning, AI, education, documents, notes, study guide, academic, research',
} as const;

/**
 * UI/UX related constants
 */
export const UI = {
  /** Primary theme color (dark) */
  THEME_COLOR: '#0a0a0a',
} as const;

/**
 * Color palette for dynamic UI accents.
 */
export const ACCENT_HUES = [185, 315, 35] as const; // cyan, pink, peach

/**
 * File validation and upload limits.
 */
export const FILE_VALIDATION = {
  /** Maximum file size in megabytes - balances usability with server resources */
  MAX_SIZE_MB: 100,
  /** Maximum file size in bytes (computed from MB) - used for precise validation */
  MAX_SIZE_BYTES: 100 * 1024 * 1024,
  /** Allowed file extensions (must include leading dot) - whitelist approach for security */
  ALLOWED_EXTENSIONS: ['.pdf', '.mp3', '.wav', '.txt', '.m4a'] as const,
  /**
   * Corresponding MIME types for additional validation if needed in future.
   * Note: MIME types can be spoofed, so we rely primarily on extension validation.
   */
  ALLOWED_MIME_TYPES: [
    'application/pdf',
    'audio/mpeg',
    'audio/wav',
    'audio/wave',
    'text/plain',
    'audio/mp4',
    'audio/x-m4a',
  ] as const,
} as const;

/**
 * API/Service related constants
 */
export const SERVICE = {
  // Add service-related constants here as needed
} as const;
