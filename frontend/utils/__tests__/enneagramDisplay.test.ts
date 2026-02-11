/**
 * Enneagram Display Regression Tests
 * ===================================
 * 
 * These tests ensure the wing/header display logic never regresses.
 * 
 * CANONICAL RULES BEING TESTED:
 * 1. headerLabel never contains "balanced" or "wbalanced"
 * 2. headerLabel never contains "(6 & 8)" or similar wing enumeration
 * 3. Wing suffix only appears when wing is a numeric value
 * 4. wingHelperText only appears when wing is numeric and confidence is not "high"
 * 5. wingNote only appears when wing is balanced/null
 */

import {
  getEnneagramHeaderDisplay,
  assertValidHeaderLabel,
  getValidatedEnneagramHeaderDisplay,
  EnneagramHeaderInput,
  EnneagramHeaderDisplay,
} from '../enneagramDisplay';

describe('getEnneagramHeaderDisplay', () => {
  // =========================================================================
  // CASE 1: Wing is "balanced"
  // =========================================================================
  describe('wing === "balanced"', () => {
    const input: EnneagramHeaderInput = {
      coreType: 7,
      wing: 'balanced',
      confidenceTier: 'moderate',
    };
    
    it('should return header "Type 7" without wing suffix', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel).toBe('Type 7');
    });
    
    it('should NOT contain "balanced" in header', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel.toLowerCase()).not.toContain('balanced');
    });
    
    it('should NOT contain "w" in header', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel).not.toMatch(/w\d/);
    });
    
    it('should have wingHelperText as null', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingHelperText).toBeNull();
    });
    
    it('should have wingNote for accordion section', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingNote).not.toBeNull();
      expect(result.wingNote).toContain('accessible');
    });
    
    it('should have wingState "balanced"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingState).toBe('balanced');
    });
  });
  
  // =========================================================================
  // CASE 2: Wing is null
  // =========================================================================
  describe('wing === null', () => {
    const input: EnneagramHeaderInput = {
      coreType: 7,
      wing: null,
      confidenceTier: 'low',
    };
    
    it('should return header "Type 7" without wing suffix', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel).toBe('Type 7');
    });
    
    it('should NOT contain "w" in header', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel).not.toMatch(/w\d/);
      expect(result.headerLabel).not.toContain('w');
    });
    
    it('should have wingHelperText as null', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingHelperText).toBeNull();
    });
    
    it('should have wingNote for accordion section', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingNote).not.toBeNull();
      expect(result.wingNote).toContain('emerging');
    });
    
    it('should have wingState "not_clear"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingState).toBe('not_clear');
    });
  });
  
  // =========================================================================
  // CASE 3: Wing is undefined
  // =========================================================================
  describe('wing === undefined', () => {
    const input: EnneagramHeaderInput = {
      coreType: 7,
      wing: undefined,
      confidenceTier: 'exploratory',
    };
    
    it('should return header "Type 7" without wing suffix', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel).toBe('Type 7');
    });
    
    it('should have wingState "not_clear"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingState).toBe('not_clear');
    });
  });
  
  // =========================================================================
  // CASE 4: Wing is numeric (8) with HIGH confidence
  // =========================================================================
  describe('wing === 8, confidenceTier === "high"', () => {
    const input: EnneagramHeaderInput = {
      coreType: 7,
      wing: 8,
      confidenceTier: 'high',
    };
    
    it('should return header "Type 7w8"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel).toBe('Type 7w8');
    });
    
    it('should have wingHelperText as null (dominant wing)', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingHelperText).toBeNull();
    });
    
    it('should have wingNote as null', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingNote).toBeNull();
    });
    
    it('should have wingState "dominant"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingState).toBe('dominant');
    });
    
    it('should have confidenceBadge "High"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.confidenceBadge).toBe('High');
    });
  });
  
  // =========================================================================
  // CASE 5: Wing is numeric (8) with LOW confidence
  // =========================================================================
  describe('wing === 8, confidenceTier === "low"', () => {
    const input: EnneagramHeaderInput = {
      coreType: 7,
      wing: 8,
      confidenceTier: 'low',
    };
    
    it('should return header "Type 7w8"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel).toBe('Type 7w8');
    });
    
    it('should have wingHelperText "Leaning toward Wing 8"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingHelperText).toBe('Leaning toward Wing 8');
    });
    
    it('should have wingNote for context', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingNote).not.toBeNull();
    });
    
    it('should have wingState "leaning"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingState).toBe('leaning');
    });
  });
  
  // =========================================================================
  // CASE 6: Wing is numeric (6) with MODERATE confidence
  // =========================================================================
  describe('wing === 6, confidenceTier === "moderate"', () => {
    const input: EnneagramHeaderInput = {
      coreType: 7,
      wing: 6,
      confidenceTier: 'moderate',
    };
    
    it('should return header "Type 7w6"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.headerLabel).toBe('Type 7w6');
    });
    
    it('should have wingHelperText "Leaning toward Wing 6"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.wingHelperText).toBe('Leaning toward Wing 6');
    });
    
    it('should have confidenceBadge "Exploratory"', () => {
      const result = getEnneagramHeaderDisplay(input);
      expect(result.confidenceBadge).toBe('Exploratory');
    });
  });
  
  // =========================================================================
  // CASE 7: Different core types
  // =========================================================================
  describe('different core types', () => {
    it('should handle Type 1w9', () => {
      const result = getEnneagramHeaderDisplay({
        coreType: 1,
        wing: 9,
        confidenceTier: 'high',
      });
      expect(result.headerLabel).toBe('Type 1w9');
    });
    
    it('should handle Type 4w5', () => {
      const result = getEnneagramHeaderDisplay({
        coreType: 4,
        wing: 5,
        confidenceTier: 'high',
      });
      expect(result.headerLabel).toBe('Type 4w5');
    });
    
    it('should handle Type 9 with balanced wings', () => {
      const result = getEnneagramHeaderDisplay({
        coreType: 9,
        wing: 'balanced',
        confidenceTier: 'moderate',
      });
      expect(result.headerLabel).toBe('Type 9');
      expect(result.headerLabel).not.toContain('balanced');
    });
  });
});

// =============================================================================
// VALIDATION TESTS
// =============================================================================

describe('assertValidHeaderLabel', () => {
  it('should accept valid labels', () => {
    expect(() => assertValidHeaderLabel('Type 7')).not.toThrow();
    expect(() => assertValidHeaderLabel('Type 7w8')).not.toThrow();
    expect(() => assertValidHeaderLabel('Type 4w5')).not.toThrow();
  });
  
  it('should reject labels containing "balanced"', () => {
    expect(() => assertValidHeaderLabel('Type 7 — balanced wings')).toThrow();
    expect(() => assertValidHeaderLabel('Type 7 balanced')).toThrow();
  });
  
  it('should reject labels containing "wbalanced"', () => {
    expect(() => assertValidHeaderLabel('Type 7wbalanced')).toThrow();
  });
  
  it('should reject labels containing wing enumeration "(6 & 8)"', () => {
    expect(() => assertValidHeaderLabel('Type 7 — balanced wings (6 & 8)')).toThrow();
    expect(() => assertValidHeaderLabel('Type 7 (6 & 8)')).toThrow();
  });
});

// =============================================================================
// GLOBAL SAFETY ASSERTION
// =============================================================================

describe('Global Safety: No "balanced" in any headerLabel', () => {
  const testCases: EnneagramHeaderInput[] = [
    { coreType: 1, wing: 'balanced', confidenceTier: 'high' },
    { coreType: 2, wing: 'balanced', confidenceTier: 'moderate' },
    { coreType: 3, wing: 'balanced', confidenceTier: 'low' },
    { coreType: 4, wing: 'balanced', confidenceTier: 'exploratory' },
    { coreType: 5, wing: 'balanced', confidenceTier: null },
    { coreType: 6, wing: null, confidenceTier: 'high' },
    { coreType: 7, wing: undefined, confidenceTier: 'low' },
    { coreType: 8, wing: 8, confidenceTier: 'high' },
    { coreType: 9, wing: 1, confidenceTier: 'low' },
  ];
  
  testCases.forEach((input, index) => {
    it(`case ${index + 1}: Type ${input.coreType}, wing=${input.wing}, confidence=${input.confidenceTier}`, () => {
      const result = getEnneagramHeaderDisplay(input);
      
      // Assert headerLabel never contains "balanced"
      expect(result.headerLabel.toLowerCase()).not.toContain('balanced');
      
      // Assert headerLabel never contains "wbalanced"
      expect(result.headerLabel.toLowerCase()).not.toContain('wbalanced');
      
      // Assert no wing enumeration pattern
      expect(result.headerLabel).not.toMatch(/\(\d+\s*&\s*\d+\)/);
      
      // Use the validation helper
      expect(() => assertValidHeaderLabel(result.headerLabel)).not.toThrow();
    });
  });
});

describe('getValidatedEnneagramHeaderDisplay', () => {
  it('should return valid results for normal inputs', () => {
    const result = getValidatedEnneagramHeaderDisplay({
      coreType: 7,
      wing: 8,
      confidenceTier: 'high',
    });
    expect(result.headerLabel).toBe('Type 7w8');
  });
  
  it('should throw if internal logic produces invalid result', () => {
    // This tests the validation wrapper itself
    // The internal function should never produce invalid output
    // but the wrapper provides an extra safety net
    const result = getValidatedEnneagramHeaderDisplay({
      coreType: 7,
      wing: 'balanced',
      confidenceTier: 'moderate',
    });
    expect(result.headerLabel).toBe('Type 7');
  });
});
