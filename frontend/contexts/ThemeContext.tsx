// Project Mirror - Theme Context with Debug Override
// Supports: System, Light, Dark modes with dev override

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { useColorScheme, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ============================================
// THEME TOKENS
// ============================================

// Light Theme - Calm, warm, paper-like (NO PURE WHITE)
export const LightTheme = {
  // Backgrounds - warm beige tones (replaces all white)
  background: '#F2ECE4',         // warm beige base
  surface: '#EAE3D9',            // warm beige for cards/surfaces
  surfaceElevated: '#F2ECE4',    // softer beige for elevated
  surfaceLight: '#F5EFE7',       // lightest warm tone
  surfaceMuted: '#E5DED4',       // muted warm
  
  // Text - dark on light
  text: '#1C1C1E',               // primary text on beige
  textSecondary: '#4A4A4A',
  textTertiary: '#6B6B6B',       // muted text on beige
  textDisabled: '#9A9A9A',
  textInverse: '#F2ECE4',        // light text for dark backgrounds
  
  // Accent
  accent: '#2A2A2A',
  accentMuted: '#5A5A5A',
  accentLight: '#DDD6CC',        // warm accent light
  
  // Borders - warm tinted
  border: '#D4CCC2',
  borderLight: '#E0D9CF',
  borderFocus: '#1C1C1E',
  
  // Semantic
  error: '#C62828',
  errorLight: '#F8E8E8',         // warm error bg
  success: '#2E7D32',
  successLight: '#E8F0E8',       // warm success bg
  warning: '#E65100',
  warningLight: '#F8F0E4',       // warm warning bg
  
  // Badges
  badgeBg: '#E4EDE4',
  badgeText: '#2E7D32',
  
  // Pattern Movement
  stressColor: '#C62828',
  stressColorBg: '#F8E8E8',
  growthColor: '#2E7D32',
  growthColorBg: '#E8F0E8',
  
  // Inputs - warm beige
  inputBg: '#F5EFE7',
  inputBorder: '#D4CCC2',
  inputPlaceholder: '#9A9A9A',
  
  // Tabs - warm tones
  tabActive: '#1C1C1E',
  tabInactive: '#6B6B6B',
  tabIndicator: '#1C1C1E',
  tabBg: '#EAE3D9',
  
  // Buttons
  buttonPrimaryBg: '#1C1C1E',
  buttonPrimaryText: '#F2ECE4',
  buttonSecondaryBg: 'transparent',
  buttonSecondaryText: '#1C1C1E',
  buttonSecondaryBorder: '#D4CCC2',
  
  // Cards - warm beige
  cardBg: '#EAE3D9',
  cardBorder: '#DDD6CC',
  cardShadow: 'rgba(0,0,0,0.06)',
  
  // Overlay
  overlay: 'rgba(0,0,0,0.5)',
  
  // Mode
  isDark: false,
};

// Dark Theme - Deep, calming, premium
export const DarkTheme = {
  // Backgrounds - warm-tinted dark (not pure black)
  background: '#0D0D0D',
  surface: '#1A1A1A',
  surfaceElevated: '#252525',
  surfaceLight: '#1F1F1F',
  surfaceMuted: '#151515',
  
  // Text - warm white
  text: '#F0EDE8',
  textSecondary: '#B5B2AD',
  textTertiary: '#7A7875',
  textDisabled: '#4A4845',
  textInverse: '#1A1A1A',
  
  // Accent - warm gold
  accent: '#D4C9B8',
  accentMuted: '#8A857A',
  accentLight: '#2A2825',
  
  // Borders
  border: '#333330',
  borderLight: '#2A2825',
  borderFocus: '#D4C9B8',
  
  // Semantic - adjusted for dark
  error: '#EF5350',
  errorLight: '#2C1A1A',
  success: '#66BB6A',
  successLight: '#1A2C1A',
  warning: '#FFA726',
  warningLight: '#2C2517',
  
  // Badges
  badgeBg: '#1A2C1A',
  badgeText: '#66BB6A',
  
  // Pattern Movement
  stressColor: '#EF5350',
  stressColorBg: '#2C1A1A',
  growthColor: '#66BB6A',
  growthColorBg: '#1A2C1A',
  
  // Inputs
  inputBg: '#1F1F1F',
  inputBorder: '#333330',
  inputPlaceholder: '#4A4845',
  
  // Tabs
  tabActive: '#F0EDE8',
  tabInactive: '#7A7875',
  tabIndicator: '#D4C9B8',
  tabBg: '#1A1A1A',
  
  // Buttons - inverted for dark
  buttonPrimaryBg: '#F0EDE8',
  buttonPrimaryText: '#1A1A1A',
  buttonSecondaryBg: 'transparent',
  buttonSecondaryText: '#D4C9B8',
  buttonSecondaryBorder: '#333330',
  
  // Cards
  cardBg: '#1A1A1A',
  cardBorder: '#2A2825',
  cardShadow: 'rgba(0,0,0,0.4)',
  
  // Overlay
  overlay: 'rgba(0,0,0,0.7)',
  
  // Mode
  isDark: true,
};

export type ThemeColors = typeof LightTheme;
export type ThemeMode = 'system' | 'light' | 'dark';

// ============================================
// CONTEXT
// ============================================

interface ThemeContextType {
  theme: ThemeColors;
  themeMode: ThemeMode;
  setThemeMode: (mode: ThemeMode) => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType>({
  theme: LightTheme,
  themeMode: 'system',
  setThemeMode: () => {},
  isDark: false,
});

export const useTheme = () => useContext(ThemeContext);

// ============================================
// PROVIDER
// ============================================

const THEME_STORAGE_KEY = '@mirror_theme_mode';

// PRODUCTION DEFAULT: Set to 'dark' to ensure dark mode is the default
// for new users and when system detection fails on mobile web.
// Users can always change this via Settings modal.
const PRODUCTION_DEFAULT_MODE: ThemeMode = 'dark';

// DEV OVERRIDE: Set to 'dark' or 'light' to force theme for testing
// Set to null to use normal system/stored preference (PRODUCTION MODE)
const DEV_THEME_OVERRIDE: ThemeMode | null = null;

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const systemColorScheme = useColorScheme();
  // Start with production default (dark) to prevent flash of light theme
  const [themeMode, setThemeModeState] = useState<ThemeMode>(PRODUCTION_DEFAULT_MODE);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load saved theme preference on mount
  useEffect(() => {
    const loadTheme = async () => {
      try {
        const saved = await AsyncStorage.getItem(THEME_STORAGE_KEY);
        console.log(`[Theme] Loaded from storage: ${saved}`);
        if (saved && ['system', 'light', 'dark'].includes(saved)) {
          setThemeModeState(saved as ThemeMode);
        } else {
          // No saved preference - keep production default (dark)
          // and save it for next time
          await AsyncStorage.setItem(THEME_STORAGE_KEY, PRODUCTION_DEFAULT_MODE);
          console.log(`[Theme] No saved preference, defaulting to: ${PRODUCTION_DEFAULT_MODE}`);
        }
      } catch (e) {
        console.log('[Theme] Failed to load saved theme, using default');
      }
      setIsLoaded(true);
    };
    loadTheme();
  }, []);

  // Save theme preference when changed
  const setThemeMode = async (mode: ThemeMode) => {
    console.log(`[Theme] User setting theme to: ${mode}`);
    setThemeModeState(mode);
    try {
      await AsyncStorage.setItem(THEME_STORAGE_KEY, mode);
      console.log(`[Theme] Saved to storage: ${mode}`);
    } catch (e) {
      console.log('[Theme] Failed to save theme');
    }
  };

  // Determine actual theme to apply
  const effectiveMode = DEV_THEME_OVERRIDE || themeMode;
  
  let isDark = false;
  if (effectiveMode === 'dark') {
    isDark = true;
  } else if (effectiveMode === 'light') {
    isDark = false;
  } else {
    // System mode - check system preference
    // useColorScheme returns 'dark', 'light', or null
    // On mobile web, this can be unreliable, but we respect user's explicit choice of "System"
    if (systemColorScheme === 'dark') {
      isDark = true;
    } else if (systemColorScheme === 'light') {
      isDark = false;
    } else {
      // null/undefined - system couldn't detect, fall back to dark
      isDark = true;
    }
  }

  const theme = isDark ? DarkTheme : LightTheme;

  // Enhanced logging for debugging
  useEffect(() => {
    console.log(`[Theme] ========================================`);
    console.log(`[Theme] isLoaded: ${isLoaded}`);
    console.log(`[Theme] themeMode (stored): ${themeMode}`);
    console.log(`[Theme] effectiveMode: ${effectiveMode}`);
    console.log(`[Theme] systemColorScheme: ${systemColorScheme}`);
    console.log(`[Theme] Platform: ${Platform.OS}`);
    console.log(`[Theme] Result isDark: ${isDark}`);
    console.log(`[Theme] Active theme: ${isDark ? 'DARK' : 'LIGHT'}`);
    if (DEV_THEME_OVERRIDE) {
      console.log(`[Theme] DEV OVERRIDE ACTIVE: ${DEV_THEME_OVERRIDE}`);
    }
    console.log(`[Theme] ========================================`);
  }, [effectiveMode, systemColorScheme, isDark, isLoaded, themeMode]);

  return (
    <ThemeContext.Provider value={{ theme, themeMode, setThemeMode, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Legacy export for components not yet migrated
export const Colors = LightTheme;
