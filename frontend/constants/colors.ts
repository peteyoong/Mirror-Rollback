// Project Mirror - Color palette with dark theme support
// FORCED DARK THEME for consistent experience

// Dark Theme Colors (PRIMARY - Always used)
export const DarkColors = {
  background: '#111214',
  surface: '#1A1C1E',
  surfaceLight: '#242628',
  text: '#F5F3EF',
  textSecondary: '#A0A0A0',
  textTertiary: '#666666',
  accent: '#D0D0D0',
  border: '#2A2C2E',
  error: '#FF6B6B',
  warning: '#FFB347',
  success: '#4CAF50',
  highlight: '#1E3A1E',
  cardShadow: 'rgba(0,0,0,0.3)',
};

// Light Theme Colors (kept for reference, not used)
export const LightColors = {
  background: '#F5F3EF',
  surface: '#FFFFFF',
  surfaceLight: '#FAF9F7',
  text: '#1A1A1A',
  textSecondary: '#666666',
  textTertiary: '#999999',
  accent: '#2A2A2A',
  border: '#E5E3DF',
  error: '#D32F2F',
  warning: '#F57C00',
  success: '#388E3C',
  highlight: '#E8F4E8',
  cardShadow: 'rgba(0,0,0,0.05)',
};

// FORCE DARK THEME - Export dark colors as the default
export const Colors = DarkColors;