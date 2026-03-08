// Project Mirror - Theme Context Provider
// Provides theme colors throughout the app based on system preference

import React, { createContext, useContext, ReactNode } from 'react';
import { useColorScheme } from 'react-native';
import { LightTheme, DarkTheme, ThemeColors } from '../constants/theme';

// Create context with default light theme
const ThemeContext = createContext<ThemeColors>(LightTheme);

// Custom hook to use theme
export const useThemeColors = (): ThemeColors => {
  return useContext(ThemeContext);
};

// Theme provider component
interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const colorScheme = useColorScheme();
  const theme = colorScheme === 'dark' ? DarkTheme : LightTheme;
  
  return (
    <ThemeContext.Provider value={theme}>
      {children}
    </ThemeContext.Provider>
  );
};

// Export theme values for static usage (components that can't use hooks)
export { LightTheme, DarkTheme };
