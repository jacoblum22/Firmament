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
 * API/Service related constants
 */
export const SERVICE = {
  // Add service-related constants here as needed
} as const;
