import { TextStyle, Platform } from 'react-native';
import { Colors } from './colors';

/**
 * Typography Tokens - Centralized text styles for Mirror app
 * 
 * Design system for consistent typography across all screens.
 * Use these tokens instead of inline styles.
 */

// ============================================
// HERO & BODY TEXT
// ============================================

/** 
 * Primary mirror/hero text - large, light weight, serif-feel
 * Used for: Main keystone text, primary reflections
 */
export const heroSerif: TextStyle = {
  fontSize: 26,
  lineHeight: 40,
  fontWeight: '300',
  color: Colors.text,
  letterSpacing: 0.2,
};

/**
 * Secondary body text - standard readable size
 * Used for: Descriptions, content paragraphs
 */
export const bodyText: TextStyle = {
  fontSize: 16,
  lineHeight: 26,
  fontWeight: '400',
  color: Colors.text,
};

/**
 * Subtext italic - supportive, softer emphasis
 * Used for: Affirmations, secondary messages
 */
export const subtextItalic: TextStyle = {
  fontSize: 15,
  lineHeight: 24,
  fontWeight: '400',
  fontStyle: 'italic',
  color: Colors.textSecondary,
  opacity: 0.8,
};

// ============================================
// LABELS & HEADINGS
// ============================================

/**
 * Section label - uppercase, muted, structural
 * Used for: TODAY, REFLECT, THE MIRROR, etc.
 */
export const sectionLabel: TextStyle = {
  fontSize: 10,
  fontWeight: '600',
  color: Colors.textTertiary,
  letterSpacing: 1.5,
  textTransform: 'uppercase',
  opacity: 0.45,
};

/**
 * Card title - smaller label for cards
 * Used for: Today's Mirror, card headers
 */
export const cardTitle: TextStyle = {
  fontSize: 10,
  fontWeight: '500',
  color: Colors.textTertiary,
  letterSpacing: 0.8,
  textTransform: 'uppercase',
  opacity: 0.7,
};

/**
 * Screen header - app-level navigation labels
 * Used for: Tab labels, screen titles
 */
export const screenHeader: TextStyle = {
  fontSize: 12,
  fontWeight: '500',
  color: Colors.text,
  letterSpacing: 1.2,
};

// ============================================
// QUESTIONS & PROMPTS
// ============================================

/**
 * Reflect question - larger prompt text
 * Used for: Daily questions, reflection prompts
 */
export const reflectQuestion: TextStyle = {
  fontSize: 17,
  lineHeight: 28,
  fontWeight: '400',
  color: Colors.text,
};

/**
 * Intelligence signal - muted contextual hint
 * Used for: "Based on recent reflections", subtle adaptive cues
 */
export const intelligenceSignal: TextStyle = {
  fontSize: 11,
  fontWeight: '400',
  fontStyle: 'italic',
  color: Colors.textTertiary,
  opacity: 0.4,
};

// ============================================
// UTILITY TEXT
// ============================================

/**
 * Footer text - very muted, bottom of screen
 */
export const footerText: TextStyle = {
  fontSize: 11,
  color: Colors.textTertiary,
  opacity: 0.3,
};

/**
 * Debug text - monospace for technical info
 */
export const debugText: TextStyle = {
  fontSize: 8,
  color: 'rgba(255,255,255,0.4)',
  fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
};

/**
 * Button text - primary action
 */
export const buttonText: TextStyle = {
  fontSize: 15,
  fontWeight: '500',
  color: Colors.text,
};

/**
 * Button subtext - secondary action descriptor
 */
export const buttonSubtext: TextStyle = {
  fontSize: 12,
  fontStyle: 'italic',
  color: Colors.textTertiary,
};

// ============================================
// TYPOGRAPHY EXPORT
// ============================================

export const Typography = {
  heroSerif,
  bodyText,
  subtextItalic,
  sectionLabel,
  cardTitle,
  screenHeader,
  reflectQuestion,
  intelligenceSignal,
  footerText,
  debugText,
  buttonText,
  buttonSubtext,
};

export default Typography;
