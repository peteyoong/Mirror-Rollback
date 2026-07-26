/**
 * theme/tokens.ts
 * ===================================================================
 * Canonical design tokens for "The Mirror".
 *
 * Personality: "6 Glass / Luxe DARK" — cinematic, expansive, deeply
 * reflective sanctuary blending esoteric wisdom with premium moody
 * elegance.
 *
 * These tokens are the single source of truth for colour, typography,
 * spacing, radius, and elevation across every screen and component.
 * Any StyleSheet in the app should consume tokens from here instead of
 * inlining raw pixel or hex values.
 *
 * Reference: /app/design_guidelines.json (blueprint from the mobile
 * design specialist, generated 2026-07).
 */
import { Platform } from 'react-native';

// ─────────────────────────────────────────────────────────────
// COLOR — DARK is the primary experience.
// ─────────────────────────────────────────────────────────────
export const colorDark = {
  surface: '#111111',
  onSurface: '#F5F5F0',
  surfaceSecondary: '#1C1C1C',
  onSurfaceSecondary: '#A3A3A3',
  surfaceTertiary: '#262626',
  onSurfaceTertiary: '#737373',
  surfaceInverse: '#FDFCF8',
  onSurfaceInverse: '#111111',

  brand: '#C6A87C',
  brandPrimary: '#C6A87C',
  onBrandPrimary: '#111111',
  brandSecondary: '#967B54',
  onBrandSecondary: '#F5F5F0',
  brandTertiary: '#4A3E2A',
  onBrandTertiary: '#EAEAEA',

  success: '#3A5A40',
  onSuccess: '#D8F3DC',
  warning: '#8A6327',
  onWarning: '#FDF3E1',
  error: '#7A2E2E',
  onError: '#FBE9E9',
  info: '#2B4C5E',
  onInfo: '#E1F1F9',

  border: '#262626',
  borderStrong: '#404040',
  divider: '#1F1F1F',

  // Legacy compatibility keys used by many existing screens
  background: '#111111',
  text: '#F5F5F0',
  textSecondary: '#A3A3A3',
  textTertiary: '#737373',
  buttonPrimaryBg: '#F5F5F0',
  buttonPrimaryText: '#111111',
} as const;

export const colorLight = {
  surface: '#FDFCF8',
  onSurface: '#111111',
  surfaceSecondary: '#F5F5F0',
  onSurfaceSecondary: '#404040',
  surfaceTertiary: '#EAEAEA',
  onSurfaceTertiary: '#737373',
  surfaceInverse: '#111111',
  onSurfaceInverse: '#FDFCF8',

  brand: '#967B54',
  brandPrimary: '#967B54',
  onBrandPrimary: '#FDFCF8',
  brandSecondary: '#C6A87C',
  onBrandSecondary: '#111111',
  brandTertiary: '#EDE3D2',
  onBrandTertiary: '#4A3E2A',

  success: '#3A5A40',
  onSuccess: '#D8F3DC',
  warning: '#8A6327',
  onWarning: '#FDF3E1',
  error: '#7A2E2E',
  onError: '#FBE9E9',
  info: '#2B4C5E',
  onInfo: '#E1F1F9',

  border: '#E3DED4',
  borderStrong: '#B8B0A2',
  divider: '#EDE9DF',

  background: '#FDFCF8',
  text: '#111111',
  textSecondary: '#404040',
  textTertiary: '#737373',
  buttonPrimaryBg: '#111111',
  buttonPrimaryText: '#F5F5F0',
} as const;

// ─────────────────────────────────────────────────────────────
// TYPOGRAPHY
// Rule: weights capped at 500 (no 600/700/800). Family fallback
// pyramid guarantees rendering even without expo-font loading.
// ─────────────────────────────────────────────────────────────
export const fontFamily = {
  // Cormorant-Garamond-like: elegant serif for headlines
  display: Platform.select({
    ios: 'Cormorant Garamond, Baskerville, Georgia, serif',
    android: 'serif',
    default: 'Cormorant Garamond, Baskerville, Georgia, serif',
  }),
  // Satoshi-like: modern humanist sans for body
  text: Platform.select({
    ios: '-apple-system, "Satoshi", "Inter", "SF Pro Text", system-ui, sans-serif',
    android: 'sans-serif',
    default: 'Satoshi, Inter, -apple-system, system-ui, sans-serif',
  }),
} as const;

export const fontSize = {
  sm: 12,
  base: 14,
  lg: 16,
  xl: 20,
  '2xl': 24,
  // Only used on hero headlines
  '3xl': 32,
} as const;

export const fontWeight = {
  regular: '400' as const,
  medium: '500' as const,
};

export const lineHeight = {
  tight: 1.2,
  snug: 1.35,
  normal: 1.5,
  relaxed: 1.6,
} as const;

// Ready-to-spread text roles.  Use these instead of composing raw
// fontSize + fontWeight in each StyleSheet.
export const textRole = {
  display: {
    fontFamily: fontFamily.display,
    fontSize: fontSize['3xl'],
    fontWeight: fontWeight.regular,
    letterSpacing: 0.4,
    lineHeight: fontSize['3xl'] * lineHeight.tight,
  },
  h1: {
    fontFamily: fontFamily.display,
    fontSize: fontSize['2xl'],
    fontWeight: fontWeight.regular,
    letterSpacing: 0.3,
    lineHeight: fontSize['2xl'] * lineHeight.snug,
  },
  h2: {
    fontFamily: fontFamily.display,
    fontSize: fontSize.xl,
    fontWeight: fontWeight.medium,
    letterSpacing: 0.2,
    lineHeight: fontSize.xl * lineHeight.snug,
  },
  bodyLg: {
    fontFamily: fontFamily.text,
    fontSize: fontSize.lg,
    fontWeight: fontWeight.regular,
    lineHeight: fontSize.lg * lineHeight.relaxed,
  },
  body: {
    fontFamily: fontFamily.text,
    fontSize: fontSize.base,
    fontWeight: fontWeight.regular,
    lineHeight: fontSize.base * lineHeight.relaxed,
  },
  caption: {
    fontFamily: fontFamily.text,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.regular,
    lineHeight: fontSize.sm * lineHeight.normal,
  },
  label: {
    fontFamily: fontFamily.text,
    fontSize: fontSize.sm,
    fontWeight: fontWeight.medium,
    textTransform: 'uppercase' as const,
    letterSpacing: 0.8,
    lineHeight: fontSize.sm * lineHeight.normal,
  },
  buttonPrimary: {
    fontFamily: fontFamily.text,
    fontSize: fontSize.lg,
    fontWeight: fontWeight.medium,
    letterSpacing: 0.3,
  },
  buttonSecondary: {
    fontFamily: fontFamily.text,
    fontSize: fontSize.base,
    fontWeight: fontWeight.regular,
    letterSpacing: 0.2,
  },
} as const;

// ─────────────────────────────────────────────────────────────
// SPACING (8pt-ish grid)
// ─────────────────────────────────────────────────────────────
export const space = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  '2xl': 32,
  '3xl': 48,
} as const;

// ─────────────────────────────────────────────────────────────
// RADIUS
// ─────────────────────────────────────────────────────────────
export const radius = {
  sm: 6,
  md: 12,
  lg: 20,
  pill: 999,
} as const;

// ─────────────────────────────────────────────────────────────
// ELEVATION (tier 0 — glass, not drop-shadow)
// ─────────────────────────────────────────────────────────────
export const glass = {
  // Card frostings for dark surface
  cardDark: {
    backgroundColor: 'rgba(28, 28, 28, 0.72)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
  },
  cardLight: {
    backgroundColor: 'rgba(245, 245, 240, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
  },
} as const;

// ─────────────────────────────────────────────────────────────
// TOUCH TARGET floor (accessibility)
// ─────────────────────────────────────────────────────────────
export const touchTarget = { minSize: 44 } as const;

// Convenience aggregate for callers that want everything.
export const tokens = {
  colorDark,
  colorLight,
  fontFamily,
  fontSize,
  fontWeight,
  lineHeight,
  textRole,
  space,
  radius,
  glass,
  touchTarget,
} as const;

export default tokens;
