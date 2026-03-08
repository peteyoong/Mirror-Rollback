// Project Mirror - Theme System v2.0
// True dark mode support with calm, premium, reflective aesthetic
// Uses system color scheme detection

import { useColorScheme } from 'react-native';

// Light Theme - Calm, warm, paper-like
export const LightTheme = {
  // Backgrounds - warm, paper-like tones
  background: '#F5F3EF',
  surface: '#FFFFFF',
  surfaceElevated: '#FFFFFF',
  surfaceLight: '#FAF9F7',
  surfaceMuted: '#F0EDE8',
  
  // Text - high contrast for readability
  text: '#1A1A1A',
  textSecondary: '#4A4A4A',
  textTertiary: '#6B6B6B',
  textDisabled: '#9A9A9A',
  textInverse: '#FFFFFF',
  
  // Accent & Interactive
  accent: '#2A2A2A',
  accentMuted: '#5A5A5A',
  accentLight: '#E8E6E3',
  
  // Borders & Dividers
  border: '#D8D5D0',
  borderLight: '#E5E3DF',
  borderFocus: '#1A1A1A',
  
  // Semantic Colors
  error: '#C62828',
  errorLight: '#FFEBEE',
  success: '#2E7D32',
  successLight: '#E8F5E9',
  warning: '#E65100',
  warningLight: '#FFF3E0',
  info: '#1565C0',
  infoLight: '#E3F2FD',
  
  // Badges & Highlights
  badgeBg: '#E8F4E8',
  badgeText: '#2E7D32',
  highlightBg: '#FFF8E1',
  highlightText: '#F57C00',
  
  // Pattern Movement
  stressColor: '#C62828',
  stressColorBg: '#FFEBEE',
  growthColor: '#2E7D32',
  growthColorBg: '#E8F5E9',
  
  // Input & Forms
  inputBg: '#FFFFFF',
  inputBorder: '#D8D5D0',
  inputPlaceholder: '#9A9A9A',
  
  // Tabs & Navigation
  tabActive: '#1A1A1A',
  tabInactive: '#6B6B6B',
  tabIndicator: '#1A1A1A',
  
  // Buttons
  buttonPrimaryBg: '#1A1A1A',
  buttonPrimaryText: '#FFFFFF',
  buttonSecondaryBg: 'transparent',
  buttonSecondaryText: '#1A1A1A',
  buttonSecondaryBorder: '#D8D5D0',
  buttonDisabledBg: '#E5E3DF',
  buttonDisabledText: '#9A9A9A',
  
  // Special states
  cardShadow: 'rgba(0,0,0,0.08)',
  overlay: 'rgba(0,0,0,0.5)',
  shimmer: '#E5E3DF',
  
  // Mode identifier
  isDark: false,
};

// Dark Theme - Deep, calming, premium night mode
// NOT just inverted colors - carefully crafted for Mirror's aesthetic
export const DarkTheme = {
  // Backgrounds - deep, warm-tinted dark tones (not pure black)
  background: '#121212',           // Soft black, easier on eyes
  surface: '#1E1E1E',              // Elevated card surface
  surfaceElevated: '#2A2A2A',      // Higher elevation (modals, dropdowns)
  surfaceLight: '#252525',         // Subtle elevation
  surfaceMuted: '#1A1A1A',         // Lower emphasis areas
  
  // Text - carefully balanced for dark backgrounds
  text: '#F5F3EF',                 // Warm white, not pure white
  textSecondary: '#B8B5B0',        // Muted but readable
  textTertiary: '#8A8783',         // Subtle text
  textDisabled: '#5A5857',         // Disabled state
  textInverse: '#1A1A1A',          // For light backgrounds
  
  // Accent & Interactive - warm gold/amber accent for premium feel
  accent: '#E8DFD0',               // Warm light accent
  accentMuted: '#9A9590',
  accentLight: '#3A3836',
  
  // Borders & Dividers - subtle, not harsh
  border: '#3A3836',
  borderLight: '#2D2B29',
  borderFocus: '#E8DFD0',
  
  // Semantic Colors - adjusted for dark mode visibility
  error: '#EF5350',                // Lighter red for dark bg
  errorLight: '#2C1A1A',           // Dark red tint
  success: '#66BB6A',              // Lighter green
  successLight: '#1A2C1A',         // Dark green tint
  warning: '#FFA726',              // Warm orange
  warningLight: '#2C2517',         // Dark orange tint
  info: '#42A5F5',                 // Light blue
  infoLight: '#1A2530',            // Dark blue tint
  
  // Badges & Highlights - adjusted for dark mode
  badgeBg: '#1A2C1A',              // Dark green bg
  badgeText: '#66BB6A',            // Light green text
  highlightBg: '#2C2517',          // Dark amber bg
  highlightText: '#FFA726',        // Amber text
  
  // Pattern Movement - adjusted for dark mode
  stressColor: '#EF5350',          // Softer red
  stressColorBg: '#2C1A1A',        // Dark red tint
  growthColor: '#66BB6A',          // Softer green
  growthColorBg: '#1A2C1A',        // Dark green tint
  
  // Input & Forms
  inputBg: '#252525',
  inputBorder: '#3A3836',
  inputPlaceholder: '#5A5857',
  
  // Tabs & Navigation
  tabActive: '#F5F3EF',
  tabInactive: '#8A8783',
  tabIndicator: '#E8DFD0',
  
  // Buttons
  buttonPrimaryBg: '#E8DFD0',      // Warm light button
  buttonPrimaryText: '#1A1A1A',    // Dark text on light button
  buttonSecondaryBg: 'transparent',
  buttonSecondaryText: '#E8DFD0',
  buttonSecondaryBorder: '#3A3836',
  buttonDisabledBg: '#2A2A2A',
  buttonDisabledText: '#5A5857',
  
  // Special states
  cardShadow: 'rgba(0,0,0,0.3)',
  overlay: 'rgba(0,0,0,0.7)',
  shimmer: '#2A2A2A',
  
  // Mode identifier
  isDark: true,
};

// Type definition for theme
export type ThemeColors = typeof LightTheme;

// Hook to get current theme based on system preference
export const useTheme = (): ThemeColors => {
  const colorScheme = useColorScheme();
  return colorScheme === 'dark' ? DarkTheme : LightTheme;
};

// Legacy Colors export for backward compatibility
// Components should migrate to useTheme() hook
export const Colors = LightTheme;

// Helper to get theme by name
export const getTheme = (isDark: boolean): ThemeColors => {
  return isDark ? DarkTheme : LightTheme;
};
