/**
 * Spacing Tokens - 8pt grid system for consistent rhythm
 * 
 * Premium apps use consistent vertical rhythm.
 * Use these tokens instead of hardcoded values.
 */

export const Spacing = {
  /** 4px - Micro spacing (icon gaps, tight items) */
  xxs: 4,
  
  /** 8px - Extra small (compact elements) */
  xs: 8,
  
  /** 12px - Small (list item padding, small gaps) */
  sm: 12,
  
  /** 16px - Medium (standard padding, section gaps) */
  md: 16,
  
  /** 24px - Large (section separations) */
  lg: 24,
  
  /** 32px - Extra large (major section breaks) */
  xl: 32,
  
  /** 40px - Extra extra large (hero spacing) */
  xxl: 40,
  
  /** 48px - Maximum (screen-level separations) */
  xxxl: 48,
};

// Screen-level constants
export const ScreenPadding = {
  horizontal: Spacing.lg, // 24px
  vertical: Spacing.md,   // 16px
};

// Section-level constants
export const SectionSpacing = {
  gap: Spacing.lg,        // 24px between sections
  internalGap: Spacing.md, // 16px within sections
};

// Component-level constants
export const ComponentSpacing = {
  buttonPaddingVertical: Spacing.md,   // 16px
  buttonPaddingHorizontal: Spacing.lg, // 24px
  cardPadding: Spacing.md,             // 16px
  inputPadding: Spacing.md,            // 16px
  listItemGap: Spacing.sm,             // 12px
  iconGap: Spacing.xs,                 // 8px
};

export default Spacing;
