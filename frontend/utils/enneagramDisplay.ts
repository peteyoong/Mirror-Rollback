/**
 * Enneagram Display Utilities - SINGLE SOURCE OF TRUTH
 * =====================================================
 * 
 * Centralized logic for Enneagram header and wing display.
 * All Enneagram surfaces must use these helpers to prevent drift.
 * 
 * CANONICAL RULES:
 * 1. headerLabel never contains "balanced" or "wbalanced"
 * 2. headerLabel never contains "(6 & 8)" or similar wing enumeration
 * 3. Wing suffix only appears when wing is a numeric value
 * 4. wingHelperText only appears when wing is numeric and confidence is not "high"
 * 5. wingNote only appears when wing is balanced/null (for accordion sections)
 */

// =============================================================================
// TYPES
// =============================================================================

export type WingValue = number | 'balanced' | null | undefined;
export type ConfidenceTier = 'high' | 'moderate' | 'medium' | 'low' | 'exploratory' | null | undefined;
export type ConfidenceBadge = 'High' | 'Exploratory' | 'Low';

export interface EnneagramHeaderInput {
  coreType: number;
  wing: WingValue;
  confidenceTier: ConfidenceTier;
}

export interface EnneagramHeaderDisplay {
  /** 
   * The header label for display (e.g., "Type 7" or "Type 7w8")
   * NEVER contains "balanced" or "wbalanced"
   */
  headerLabel: string;
  
  /**
   * Confidence badge text
   */
  confidenceBadge: ConfidenceBadge;
  
  /**
   * Helper text shown below header when wing is uncertain
   * Only set when wing is numeric but confidence is not "high"
   */
  wingHelperText: string | null;
  
  /**
   * Note for accordion sections when wing is balanced/null
   * Not shown in header - only in dedicated wing section
   */
  wingNote: string | null;
  
  /**
   * Wing display state for conditional rendering
   */
  wingState: 'dominant' | 'leaning' | 'balanced' | 'not_clear';
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Determine confidence badge from tier
 */
function getConfidenceBadge(confidenceTier: ConfidenceTier): ConfidenceBadge {
  if (confidenceTier === 'high') return 'High';
  if (confidenceTier === 'moderate' || confidenceTier === 'medium') return 'Exploratory';
  return 'Low';
}

/**
 * Check if wing is a valid numeric value
 */
function isNumericWing(wing: WingValue): wing is number {
  return typeof wing === 'number' && !isNaN(wing);
}

/**
 * Check if confidence tier is high
 */
function isHighConfidence(confidenceTier: ConfidenceTier): boolean {
  return confidenceTier === 'high';
}

// =============================================================================
// MAIN EXPORT
// =============================================================================

/**
 * Get Enneagram header display values.
 * 
 * This is the SINGLE SOURCE OF TRUTH for all Enneagram header/wing display logic.
 * All Enneagram surfaces must use this helper.
 * 
 * @param input - Core type, wing value, and confidence tier
 * @returns Display values for header, helper text, and wing note
 * 
 * @example
 * // Wing is balanced
 * getEnneagramHeaderDisplay({ coreType: 7, wing: 'balanced', confidenceTier: 'moderate' })
 * // Returns: { headerLabel: "Type 7", wingHelperText: null, wingNote: "Both adjacent...", wingState: 'balanced' }
 * 
 * @example
 * // Wing is numeric with high confidence
 * getEnneagramHeaderDisplay({ coreType: 7, wing: 8, confidenceTier: 'high' })
 * // Returns: { headerLabel: "Type 7w8", wingHelperText: null, wingNote: null, wingState: 'dominant' }
 * 
 * @example
 * // Wing is numeric with low confidence
 * getEnneagramHeaderDisplay({ coreType: 7, wing: 8, confidenceTier: 'low' })
 * // Returns: { headerLabel: "Type 7w8", wingHelperText: "Leaning toward Wing 8", wingNote: "...", wingState: 'leaning' }
 */
export function getEnneagramHeaderDisplay(input: EnneagramHeaderInput): EnneagramHeaderDisplay {
  const { coreType, wing, confidenceTier } = input;
  const confidenceBadge = getConfidenceBadge(confidenceTier);
  
  // =========================================================================
  // CASE 1: Wing is null/undefined → No wing in header
  // =========================================================================
  if (wing === null || wing === undefined) {
    return {
      headerLabel: `Type ${coreType}`,
      confidenceBadge,
      wingHelperText: null,
      wingNote: 'Wing pattern is still emerging. Both adjacent types are available to you.',
      wingState: 'not_clear',
    };
  }
  
  // =========================================================================
  // CASE 2: Wing is "balanced" → No wing in header
  // =========================================================================
  if (wing === 'balanced') {
    return {
      headerLabel: `Type ${coreType}`,
      confidenceBadge,
      wingHelperText: null,
      wingNote: 'Both adjacent patterns appear accessible. This often clarifies over time.',
      wingState: 'balanced',
    };
  }
  
  // =========================================================================
  // CASE 3: Wing is numeric
  // =========================================================================
  if (isNumericWing(wing)) {
    // High confidence → dominant wing, no helper text
    if (isHighConfidence(confidenceTier)) {
      return {
        headerLabel: `Type ${coreType}w${wing}`,
        confidenceBadge,
        wingHelperText: null,
        wingNote: null,
        wingState: 'dominant',
      };
    }
    
    // Not high confidence → leaning wing, show helper text
    return {
      headerLabel: `Type ${coreType}w${wing}`,
      confidenceBadge,
      wingHelperText: `Leaning toward Wing ${wing}`,
      wingNote: 'One adjacent pattern appears slightly stronger, though not yet decisive.',
      wingState: 'leaning',
    };
  }
  
  // =========================================================================
  // FALLBACK: Unknown wing value → treat as not_clear
  // =========================================================================
  return {
    headerLabel: `Type ${coreType}`,
    confidenceBadge,
    wingHelperText: null,
    wingNote: 'Wing pattern is still emerging.',
    wingState: 'not_clear',
  };
}

// =============================================================================
// VALIDATION HELPERS (for testing and runtime checks)
// =============================================================================

/**
 * Assert that a header label is valid (never contains "balanced")
 * @throws Error if header label is invalid
 */
export function assertValidHeaderLabel(headerLabel: string): void {
  const lower = headerLabel.toLowerCase();
  
  if (lower.includes('balanced')) {
    throw new Error(`Invalid header label: "${headerLabel}" contains "balanced"`);
  }
  
  if (lower.includes('wbalanced')) {
    throw new Error(`Invalid header label: "${headerLabel}" contains "wbalanced"`);
  }
  
  // Check for wing enumeration patterns like "(6 & 8)"
  if (/\(\d+\s*&\s*\d+\)/.test(headerLabel)) {
    throw new Error(`Invalid header label: "${headerLabel}" contains wing enumeration`);
  }
}

/**
 * Safe wrapper that validates output before returning
 */
export function getValidatedEnneagramHeaderDisplay(input: EnneagramHeaderInput): EnneagramHeaderDisplay {
  const result = getEnneagramHeaderDisplay(input);
  assertValidHeaderLabel(result.headerLabel);
  return result;
}
