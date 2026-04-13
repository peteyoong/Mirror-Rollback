/**
 * Mirror Typography System — Global Readability Tokens
 * 
 * DESIGN PRINCIPLE: Readability > Compactness
 * Reference: ChatGPT iPhone reading comfort
 * 
 * Usage: import { typo } from '../constants/typography';
 * Then: fontSize: typo.body, lineHeight: typo.bodyLine, etc.
 */

export const typo = {
  // === HEADLINES ===
  hero: 28,              // Major screen titles, rare
  heroLine: 36,
  
  h1: 24,                // Primary card/section headlines
  h1Line: 32,
  
  h2: 21,                // Secondary headlines
  h2Line: 29,
  
  h3: 18,                // Tertiary / subsection headers
  h3Line: 25,
  
  // === BODY TEXT ===
  body: 17,              // Primary body text — the most common size
  bodyLine: 26,          // ~1.53x ratio
  
  bodySmall: 16,         // Secondary body, supporting text
  bodySmallLine: 24,     // ~1.5x ratio
  
  // === BULLETS & LIST ITEMS ===
  bullet: 16,            // Bullet point text
  bulletLine: 24,
  bulletSpacing: 14,     // marginBottom between bullets
  
  // === SECTION LABELS ===
  label: 12,             // Eyebrow / section label text
  labelLine: 16,
  labelSpacing: 0.6,     // letterSpacing for labels
  
  // === METADATA / HELPER ===
  meta: 14,              // Metadata, timestamps, helper text
  metaLine: 20,
  
  caption: 13,           // Smallest readable text (proof layers, technical)
  captionLine: 19,
  
  // === INTERACTIVE ===
  button: 16,            // Button labels
  buttonLine: 22,
  
  toggle: 15,            // Toggle/expand labels
  toggleLine: 21,
  
  // === SPACING ===
  sectionGap: 28,        // Between major sections
  paragraphGap: 20,      // Between paragraphs
  cardPadding: 22,       // Internal card padding
  cardPaddingLarge: 26,  // Large cards with lots of text
};
