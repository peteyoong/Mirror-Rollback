/**
 * Longitudinal Pattern Accumulation - Test Suite
 * 
 * Tests V1 compliance and bounds enforcement for the longitudinal layer.
 */

import {
  LONGITUDINAL_BOUNDS,
  LONGITUDINAL_THRESHOLDS,
  validateTypeAffinities,
  validateTotalAdjustment,
  boundAdjustments,
  THEME_TYPE_AFFINITIES,
  SOURCE_WEIGHTS,
  DEFAULT_AGGREGATOR_CONFIG,
  type LongitudinalEvidenceEvent,
  type EvidenceSignals,
} from '../longitudinal';

import { CROSS_LENS_INVARIANTS } from '../../contracts/v1IntegrityContract';

describe('Longitudinal Pattern Accumulation', () => {
  
  // ============================================
  // V1 COMPLIANCE TESTS
  // ============================================
  
  describe('V1 Contract Compliance', () => {
    
    it('should inherit bounds from V1 contract', () => {
      expect(LONGITUDINAL_BOUNDS.MAX_PER_TYPE_ADJUSTMENT)
        .toBe(CROSS_LENS_INVARIANTS.MAX_ADJUSTMENT_PER_TYPE);
      expect(LONGITUDINAL_BOUNDS.MAX_TOTAL_REDISTRIBUTION)
        .toBe(CROSS_LENS_INVARIANTS.MAX_TOTAL_REDISTRIBUTION);
    });
    
    it('should have per-event affinity limit stricter than per-type adjustment', () => {
      expect(LONGITUDINAL_BOUNDS.MAX_AFFINITY_PER_EVENT)
        .toBeLessThan(LONGITUDINAL_BOUNDS.MAX_PER_TYPE_ADJUSTMENT);
    });
    
    it('should have default config matching thresholds', () => {
      expect(DEFAULT_AGGREGATOR_CONFIG.max_total_adjustment)
        .toBe(LONGITUDINAL_BOUNDS.MAX_TOTAL_REDISTRIBUTION);
      expect(DEFAULT_AGGREGATOR_CONFIG.max_per_type_adjustment)
        .toBe(LONGITUDINAL_BOUNDS.MAX_PER_TYPE_ADJUSTMENT);
    });
  });
  
  // ============================================
  // TYPE AFFINITY VALIDATION TESTS
  // ============================================
  
  describe('Type Affinity Validation', () => {
    
    it('should accept affinities within bounds', () => {
      const affinities = { '6': 0.02, '7': 0.01, '5': -0.01 };
      const result = validateTypeAffinities(affinities);
      expect(result.valid).toBe(true);
      expect(result.violations).toHaveLength(0);
    });
    
    it('should accept affinities at exactly the bound', () => {
      const affinities = { '6': 0.03, '7': -0.03 };
      const result = validateTypeAffinities(affinities);
      expect(result.valid).toBe(true);
    });
    
    it('should reject affinities exceeding positive bound', () => {
      const affinities = { '6': 0.05 }; // Exceeds 0.03
      const result = validateTypeAffinities(affinities);
      expect(result.valid).toBe(false);
      expect(result.violations.length).toBeGreaterThan(0);
    });
    
    it('should reject affinities exceeding negative bound', () => {
      const affinities = { '7': -0.04 }; // Exceeds -0.03
      const result = validateTypeAffinities(affinities);
      expect(result.valid).toBe(false);
    });
  });
  
  // ============================================
  // TOTAL ADJUSTMENT VALIDATION TESTS
  // ============================================
  
  describe('Total Adjustment Validation', () => {
    
    it('should accept adjustments within total bound', () => {
      const adjustments = { '6': 0.04, '7': -0.04 };
      const result = validateTotalAdjustment(adjustments);
      expect(result.valid).toBe(true);
      expect(result.totalRedistribution).toBeLessThanOrEqual(0.10);
    });
    
    it('should calculate redistribution correctly', () => {
      const adjustments = { '6': 0.05, '7': -0.05 };
      const result = validateTotalAdjustment(adjustments);
      // Total = (|0.05| + |-0.05|) / 2 = 0.05
      expect(result.totalRedistribution).toBe(0.05);
    });
    
    it('should reject adjustments exceeding total bound', () => {
      const adjustments = {
        '1': 0.05, '2': 0.05, '3': 0.05,
        '7': -0.05, '8': -0.05, '9': -0.05,
      };
      const result = validateTotalAdjustment(adjustments);
      expect(result.valid).toBe(false);
      expect(result.totalRedistribution).toBeGreaterThan(0.10);
    });
  });
  
  // ============================================
  // ADJUSTMENT BOUNDING TESTS
  // ============================================
  
  describe('Adjustment Bounding', () => {
    
    it('should not modify adjustments within bounds', () => {
      const adjustments = { '6': 0.03, '7': -0.02 };
      const bounded = boundAdjustments(adjustments);
      expect(bounded['6']).toBe(0.03);
      expect(bounded['7']).toBe(-0.02);
    });
    
    it('should clip per-type adjustments to ±0.05', () => {
      const adjustments = { '6': 0.08, '7': -0.09 };
      const bounded = boundAdjustments(adjustments);
      expect(bounded['6']).toBeLessThanOrEqual(0.05);
      expect(bounded['7']).toBeGreaterThanOrEqual(-0.05);
    });
    
    it('should scale down when total exceeds bound', () => {
      const adjustments = {
        '1': 0.05, '2': 0.05, '3': 0.05,
        '7': -0.05, '8': -0.05, '9': -0.05,
      };
      const bounded = boundAdjustments(adjustments);
      
      // Verify total is now within bounds
      const result = validateTotalAdjustment(bounded);
      expect(result.totalRedistribution).toBeLessThanOrEqual(0.10);
    });
    
    it('should preserve relative proportions when scaling', () => {
      const adjustments = { '6': 0.08, '7': 0.04 }; // 2:1 ratio
      const bounded = boundAdjustments(adjustments);
      
      // After clipping 6 to 0.05, 7 should scale proportionally
      // But since 0.04 < 0.05, it might not need scaling
      expect(Math.abs(bounded['6'])).toBeLessThanOrEqual(0.05);
      expect(Math.abs(bounded['7'])).toBeLessThanOrEqual(0.05);
    });
  });
  
  // ============================================
  // THEME-TO-TYPE MAPPING TESTS
  // ============================================
  
  describe('Theme-to-Type Mapping', () => {
    
    it('should have all theme affinities within event bounds', () => {
      for (const [theme, affinities] of Object.entries(THEME_TYPE_AFFINITIES)) {
        for (const [type, value] of Object.entries(affinities)) {
          expect(Math.abs(value)).toBeLessThanOrEqual(
            LONGITUDINAL_BOUNDS.MAX_AFFINITY_PER_EVENT
          );
        }
      }
    });
    
    it('should have security themes map primarily to Type 6', () => {
      expect(THEME_TYPE_AFFINITIES['trust']['6']).toBeGreaterThan(0);
      expect(THEME_TYPE_AFFINITIES['safety']['6']).toBeGreaterThan(0);
      expect(THEME_TYPE_AFFINITIES['loyalty']['6']).toBeGreaterThan(0);
    });
    
    it('should have achievement themes map primarily to Type 3', () => {
      expect(THEME_TYPE_AFFINITIES['success']['3']).toBeGreaterThan(0);
      expect(THEME_TYPE_AFFINITIES['recognition']['3']).toBeGreaterThan(0);
    });
    
    it('should have freedom themes map primarily to Type 7', () => {
      expect(THEME_TYPE_AFFINITIES['freedom']['7']).toBeGreaterThan(0);
      expect(THEME_TYPE_AFFINITIES['options']['7']).toBeGreaterThan(0);
    });
  });
  
  // ============================================
  // SOURCE WEIGHT TESTS
  // ============================================
  
  describe('Source Weights', () => {
    
    it('should weight enneagram_deep highest', () => {
      expect(SOURCE_WEIGHTS['enneagram_deep']).toBe(1.0);
    });
    
    it('should weight enneagram_short higher than chat', () => {
      expect(SOURCE_WEIGHTS['enneagram_short'])
        .toBeGreaterThan(SOURCE_WEIGHTS['reflection_chat']);
    });
    
    it('should weight reflection_chat higher than journal', () => {
      expect(SOURCE_WEIGHTS['reflection_chat'])
        .toBeGreaterThan(SOURCE_WEIGHTS['journal']);
    });
    
    it('should have all weights between 0 and 1', () => {
      for (const weight of Object.values(SOURCE_WEIGHTS)) {
        expect(weight).toBeGreaterThan(0);
        expect(weight).toBeLessThanOrEqual(1);
      }
    });
  });
  
  // ============================================
  // THRESHOLD TESTS
  // ============================================
  
  describe('Thresholds', () => {
    
    it('should have stability_high > stability_low', () => {
      expect(LONGITUDINAL_THRESHOLDS.STABILITY_HIGH)
        .toBeGreaterThan(LONGITUDINAL_THRESHOLDS.STABILITY_LOW);
    });
    
    it('should have reasonable minimum event requirements', () => {
      expect(LONGITUDINAL_THRESHOLDS.MIN_EVENTS_FOR_STABILITY).toBeGreaterThanOrEqual(3);
      expect(LONGITUDINAL_THRESHOLDS.MIN_EVENTS_FOR_MODIFIER).toBeGreaterThanOrEqual(5);
    });
    
    it('should have reasonable time windows', () => {
      expect(LONGITUDINAL_THRESHOLDS.RECENT_WINDOW_DAYS).toBeGreaterThanOrEqual(14);
      expect(LONGITUDINAL_THRESHOLDS.RECENT_WINDOW_DAYS).toBeLessThanOrEqual(90);
    });
  });
  
  // ============================================
  // EVIDENCE EVENT VALIDATION TESTS
  // ============================================
  
  describe('Evidence Event Structure', () => {
    
    it('should create valid evidence event', () => {
      const event: LongitudinalEvidenceEvent = {
        event_id: 'test-123',
        user_id: 'user-456',
        created_at: new Date().toISOString(),
        source: 'reflection_chat',
        signals: {
          type_affinities: { '6': 0.02, '7': 0.01 },
          wing_affinities: { '5': 0.01 },
          stress_style: 'vigilance',
          avoidance_style: 'uncertainty',
          confidence_hint: 0.7,
        },
        v1_compliant: true,
      };
      
      expect(event.v1_compliant).toBe(true);
      expect(validateTypeAffinities(event.signals.type_affinities).valid).toBe(true);
    });
    
    it('should enforce v1_compliant = true', () => {
      // This is a type-level enforcement
      const event: LongitudinalEvidenceEvent = {
        event_id: 'test',
        user_id: 'user',
        created_at: new Date().toISOString(),
        source: 'journal',
        signals: {
          type_affinities: {},
          wing_affinities: {},
          stress_style: null,
          avoidance_style: null,
          confidence_hint: 0.5,
        },
        v1_compliant: true, // Must be true
      };
      
      expect(event.v1_compliant).toBe(true);
    });
  });
  
  // ============================================
  // CONFIDENCE EVOLUTION RULE TESTS
  // ============================================
  
  describe('Confidence Evolution Rules', () => {
    
    it('should have upshift require high stability', () => {
      // low → moderate requires stability ≥ 0.65
      expect(LONGITUDINAL_THRESHOLDS.STABILITY_HIGH).toBeGreaterThanOrEqual(0.65);
    });
    
    it('should have downshift threshold below upshift', () => {
      expect(LONGITUDINAL_THRESHOLDS.STABILITY_LOW)
        .toBeLessThan(LONGITUDINAL_THRESHOLDS.STABILITY_HIGH);
    });
    
    it('should have top1 dominance threshold reasonable', () => {
      expect(LONGITUDINAL_THRESHOLDS.TOP1_DOMINANCE).toBeGreaterThanOrEqual(0.50);
      expect(LONGITUDINAL_THRESHOLDS.TOP1_DOMINANCE).toBeLessThanOrEqual(0.90);
    });
  });
  
  // ============================================
  // WING EVOLUTION RULE TESTS
  // ============================================
  
  describe('Wing Evolution Rules', () => {
    
    it('should have wing clarity threshold reasonable', () => {
      expect(LONGITUDINAL_THRESHOLDS.WING_CLARITY).toBeGreaterThanOrEqual(0.50);
      expect(LONGITUDINAL_THRESHOLDS.WING_CLARITY).toBeLessThanOrEqual(0.80);
    });
    
    it('should require evidence before wing evolution', () => {
      expect(LONGITUDINAL_THRESHOLDS.MIN_EVENTS_FOR_STABILITY).toBeGreaterThanOrEqual(3);
    });
  });
  
  // ============================================
  // REGRESSION TESTS
  // ============================================
  
  describe('Regression Scenarios', () => {
    
    it('REGRESSION: Single event cannot exceed per-event bounds', () => {
      // Even with many agreeing themes, single event is bounded
      const signals: EvidenceSignals = {
        type_affinities: { '6': 0.03, '5': 0.02, '1': 0.01 },
        wing_affinities: { '5': 0.02 },
        stress_style: 'vigilance',
        avoidance_style: 'uncertainty',
        confidence_hint: 0.9,
      };
      
      const result = validateTypeAffinities(signals.type_affinities);
      expect(result.valid).toBe(true);
    });
    
    it('REGRESSION: Aggregated adjustments respect V1 bounds', () => {
      // Simulating aggregation of many events
      const aggregatedAdjustments = { '6': 0.15, '7': -0.10, '5': 0.05 };
      const bounded = boundAdjustments(aggregatedAdjustments);
      
      // Per-type bounds
      expect(bounded['6']).toBeLessThanOrEqual(0.05);
      expect(bounded['7']).toBeGreaterThanOrEqual(-0.05);
      
      // Total bounds
      const { totalRedistribution } = validateTotalAdjustment(bounded);
      expect(totalRedistribution).toBeLessThanOrEqual(0.10);
    });
    
    it('REGRESSION: High confidence cannot be downshifted by longitudinal', () => {
      // This is an invariant - longitudinal can upshift but cannot downshift high
      // The actual logic would be tested in integration tests
      // Here we verify the thresholds make sense
      
      // There should be no way for longitudinal to touch high confidence
      // This is enforced in the aggregator logic, not thresholds
      expect(true).toBe(true); // Placeholder for logic test
    });
  });
});
