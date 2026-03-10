// Project Mirror - Theme Context with Debug Override
// Supports: System, Light, Dark modes with dev override

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { useColorScheme, Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// ============================================
// THEME TOKENS
// ============================================

// Light Theme - Calm, warm, paper-like
export const LightTheme = {
  // Backgrounds
  background: '#F5F3EF',
  surface: '#FFFFFF',
  surfaceElevated: '#FFFFFF',
  surfaceLight: '#FAF9F7',
  surfaceMuted: '#F0EDE8',
  
  // Text
  text: '#1A1A1A',
  textSecondary: '#4A4A4A',
  textTertiary: '#6B6B6B',
  textDisabled: '#9A9A9A',
  textInverse: '#FFFFFF',
  
  // Accent
  accent: '#2A2A2A',
  accentMuted: '#5A5A5A',
  accentLight: '#E8E6E3',
  
  // Borders
  border: '#D8D5D0',
  borderLight: '#E5E3DF',
  borderFocus: '#1A1A1A',
  
  // Semantic
  error: '#C62828',
  errorLight: '#FFEBEE',
  success: '#2E7D32',
  successLight: '#E8F5E9',
  warning: '#E65100',
  warningLight: '#FFF3E0',
  
  // Badges
  badgeBg: '#E8F4E8',
  badgeText: '#2E7D32',
  
  // Pattern Movement
  stressColor: '#C62828',
  stressColorBg: '#FFEBEE',
  growthColor: '#2E7D32',
  growthColorBg: '#E8F5E9',
  
  // Inputs
  inputBg: '#FFFFFF',
  inputBorder: '#D8D5D0',
  inputPlaceholder: '#9A9A9A',
  
  // Tabs
  tabActive: '#1A1A1A',
  tabInactive: '#6B6B6B',
  tabIndicator: '#1A1A1A',
  tabBg: '#FFFFFF',
  
  // Buttons
  buttonPrimaryBg: '#1A1A1A',
  buttonPrimaryText: '#FFFFFF',
  buttonSecondaryBg: 'transparent',
  buttonSecondaryText: '#1A1A1A',
  buttonSecondaryBorder: '#D8D5D0',
  
  // Cards
  cardBg: '#FFFFFF',
  cardBorder: '#E5E3DF',
  cardShadow: 'rgba(0,0,0,0.08)',
  
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

// DEV OVERRIDE: Set to 'dark' or 'light' to force theme for testing
// Set to null to use normal system/stored preference (PRODUCTION MODE)
const DEV_THEME_OVERRIDE: ThemeMode | null = null;

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const systemColorScheme = useColorScheme();
  const [themeMode, setThemeModeState] = useState<ThemeMode>('system');
  const [isLoaded, setIsLoaded] = useState(false);

  // Load saved theme preference
  useEffect(() => {
    const loadTheme = async () => {
      try {
        const saved = await AsyncStorage.getItem(THEME_STORAGE_KEY);
        if (saved && ['system', 'light', 'dark'].includes(saved)) {
          setThemeModeState(saved as ThemeMode);
        }
      } catch (e) {
        console.log('[Theme] Failed to load saved theme');
      }
      setIsLoaded(true);
    };
    loadTheme();
  }, []);

  // Save theme preference
  const setThemeMode = async (mode: ThemeMode) => {
    setThemeModeState(mode);
    try {
      await AsyncStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch (e) {
      console.log('[Theme] Failed to save theme');
    }
  };

  // Determine actual theme
  const effectiveMode = DEV_THEME_OVERRIDE || themeMode;
  
  let isDark = false;
  if (effectiveMode === 'dark') {
    isDark = true;
  } else if (effectiveMode === 'light') {
    isDark = false;
  } else {
    // System mode - check system preference
    // useColorScheme returns 'dark', 'light', or null
    // On mobile web, null is common - default to DARK theme for better UX
    // (dark mode is the primary brand aesthetic for Mirror)
    isDark = systemColorScheme === 'dark' || systemColorScheme === null;
  }

  const theme = isDark ? DarkTheme : LightTheme;

  // Log for debugging
  useEffect(() => {
    if (isLoaded) {
      console.log(`[Theme] Mode: ${effectiveMode}, System: ${systemColorScheme}, Active: ${isDark ? 'DARK' : 'LIGHT'}`);
      if (DEV_THEME_OVERRIDE) {
        console.log(`[Theme] DEV OVERRIDE ACTIVE: ${DEV_THEME_OVERRIDE}`);
      }
    }
  }, [effectiveMode, systemColorScheme, isDark, isLoaded]);

  return (
    <ThemeContext.Provider value={{ theme, themeMode, setThemeMode, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Legacy export for components not yet migrated
export const Colors = LightTheme;
