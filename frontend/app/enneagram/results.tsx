import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { Ionicons } from '@expo/vector-icons';
import { getEnneagramResult, submitEnneagramFeedback } from '../../services/api';
import * as Clipboard from 'expo-clipboard';
import EnneagramUpgradeCTA from '../../components/EnneagramUpgradeCTA';
import PreliminaryLabel from '../../components/PreliminaryLabel';
import { getEnneagramUpgradeInfo, EnneagramGateInput } from '../../utils/enneagramGateLogic';
import { emitEnneagramGateCTAShown, EnneagramGateSurface } from '../../utils/analytics';
import { getEnneagramHeaderDisplay } from '../../utils/enneagramDisplay';

// Check if we're in development mode - DISABLED for tester builds
// const IS_DEV = process.env.NODE_ENV !== 'production' || __DEV__;
const IS_DEV = false; // Disabled for tester release

// ============================================
// DEBUG PANEL ACTIVATION CONDITIONS
// ============================================
// The tester debug panel renders ONLY if ALL conditions are true:
//   1. Server env flag: EXPO_PUBLIC_DEBUG_MIRROR === 'true'
//   2. Client-side trigger (one of):
//      a. URL query param: ?debug=1
//      b. Hidden gesture: Tap Confidence badge 7 times
//
// Logic: showDebug = DEBUG_MIRROR_ENV && (urlDebugParam || tapCount >= 7)
// ============================================

// Server-side environment flag (must be 'true' to enable debug capability)
const DEBUG_MIRROR_ENV = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// Client-side URL param check (?debug=1)
const getUrlDebugParam = (): boolean => {
  if (typeof window === 'undefined') return false;
  return new URLSearchParams(window.location?.search || '').get('debug') === '1';
};

// Required tap count for hidden gesture activation
const DEBUG_TAP_THRESHOLD = 7;

// ============================================
// DEBUG WING STATE OVERRIDE SYSTEM
// ============================================
// Purpose: Visual verification of P0 Wing UX Fix
// Active only when DEBUG_MIRROR_ENV === true
// UI-only, no backend, no persistence
// Zero impact on production logic
// ============================================

type DebugWingState = 'off' | 'dominant' | 'leaning' | 'balanced' | 'not_clear';

interface DebugWingOverride {
  state: DebugWingState;
  mockWing: number | 'balanced' | null;
  mockConfidenceTier: string;
}

// Mock data generator for each wing state
const getDebugWingOverride = (
  coreType: number,
  selectedState: DebugWingState
): DebugWingOverride | null => {
  if (selectedState === 'off') return null;
  
  // Use wing 6 as example for Type 7 (or left wing for other types)
  const leftWing = coreType === 1 ? 9 : coreType - 1;
  
  switch (selectedState) {
    case 'dominant':
      return { state: 'dominant', mockWing: leftWing, mockConfidenceTier: 'high' };
    case 'leaning':
      return { state: 'leaning', mockWing: leftWing, mockConfidenceTier: 'medium' };
    case 'balanced':
      return { state: 'balanced', mockWing: 'balanced', mockConfidenceTier: 'low' };
    case 'not_clear':
      return { state: 'not_clear', mockWing: null, mockConfidenceTier: 'low' };
    default:
      return null;
  }
};

// Debug state labels for UI
const DEBUG_WING_STATE_LABELS: Record<DebugWingState, string> = {
  off: 'OFF (Real Data)',
  dominant: 'Dominant Wing',
  leaning: 'Leaning Wing',
  balanced: 'Balanced Wings',
  not_clear: 'Wing Not Clear',
};

// Feedback types
type FeedbackValue = 'yes' | 'mostly' | 'no' | null;

// ============================================
// STATE CALIBRATION NORMALIZATION
// ============================================

// Allowed enum values for state calibration
const ALLOWED_ENERGY_STATES = ['low', 'neutral', 'high'] as const;
const ALLOWED_LIFE_CONTEXTS = ['surviving', 'managing', 'expanding'] as const;
const ALLOWED_ANSWER_FRAMES = ['best_self', 'recent_self'] as const;

type NormalizedEnergyState = typeof ALLOWED_ENERGY_STATES[number];
type NormalizedLifeContext = typeof ALLOWED_LIFE_CONTEXTS[number];
type NormalizedAnswerFrame = typeof ALLOWED_ANSWER_FRAMES[number];

interface NormalizedStateCalibration {
  energy_state: NormalizedEnergyState;
  life_context: NormalizedLifeContext;
  answer_frame: NormalizedAnswerFrame;
}

/**
 * Normalizes state calibration values to allowed enums.
 * Used for validation logging and feedback submission to keep dataset clean.
 */
function normalizeStateCalibration(state: {
  energy_state?: string | null;
  life_context?: string | null;
  answer_frame?: string | null;
} | null | undefined): NormalizedStateCalibration {
  const rawEnergy = state?.energy_state;
  const rawLifeContext = state?.life_context;
  const rawAnswerFrame = state?.answer_frame;
  
  const energy_state: NormalizedEnergyState = 
    rawEnergy && ALLOWED_ENERGY_STATES.includes(rawEnergy as NormalizedEnergyState)
      ? (rawEnergy as NormalizedEnergyState)
      : 'neutral';
  
  const life_context: NormalizedLifeContext = 
    rawLifeContext && ALLOWED_LIFE_CONTEXTS.includes(rawLifeContext as NormalizedLifeContext)
      ? (rawLifeContext as NormalizedLifeContext)
      : 'managing';
  
  const answer_frame: NormalizedAnswerFrame = 
    rawAnswerFrame && ALLOWED_ANSWER_FRAMES.includes(rawAnswerFrame as NormalizedAnswerFrame)
      ? (rawAnswerFrame as NormalizedAnswerFrame)
      : 'best_self';
  
  return { energy_state, life_context, answer_frame };
}

// Type motivation labels
const TYPE_MOTIVATIONS: { [key: number]: string } = {
  1: 'integrity and high standards',
  2: 'being needed and connection through helping',
  3: 'value through success and achievement',
  4: 'identity, meaning, and emotional depth',
  5: 'competence, resources, and understanding',
  6: 'security, trust, and reliability',
  7: 'freedom, possibility, and stimulation',
  8: 'autonomy, control, and strength',
  9: 'peace, harmony, and inner stability',
};

// Type names
const TYPE_NAMES: { [key: number]: string } = {
  1: 'The Perfectionist',
  2: 'The Helper',
  3: 'The Achiever',
  4: 'The Individualist',
  5: 'The Investigator',
  6: 'The Loyalist',
  7: 'The Enthusiast',
  8: 'The Challenger',
  9: 'The Peacemaker',
};

interface EnneagramResult {
  inferred_core: number;
  inferred_wing: number | 'balanced' | null;
  confidence: number;
  confidence_tier: string;
  is_close: boolean;
  top_candidates: { type: number; probability: number }[];
  assessment_depth?: 'quick' | 'deep' | 'short';  // P2: track assessment type
  assessment_version?: string;  // P2: track assessment version (v2 = latest)
  state_calibration?: {
    energy_state: string;
    life_context: string;
    answer_frame: string;
  };
  debug_scores?: {
    raw_scores: { [key: string]: number };
    z_scores: { [key: string]: number };
    wing_scores: {
      left: number;
      right: number;
      diff: number;
    };
  };
  created_at?: string;
}

// P5: Longitudinal Data Interface (DEBUG-only)
// Shadow system data - never affects user-facing results
interface LongitudinalSummary {
  enabled: boolean;
  type_stability: number;
  wing_stability: number;
  evidence_volume: { total: number; last_30_days: number };
  top_types_over_time: Array<{ type: number; share: number }>;
  confidence_modifier: string;
  recommended_next_step: string;
}

// Helper to compute adjacent wing types (handles wraparound 9→1, 1→9)
function getWingTypes(coreType: number): { left: number; right: number } {
  const left = coreType === 1 ? 9 : coreType - 1;
  const right = coreType === 9 ? 1 : coreType + 1;
  return { left, right };
}

// ============================================
// WING DISPLAY SYSTEM
// ============================================
// Implements 4 display states based on wing data and confidence:
// A) Dominant Wing (high confidence) - "Type 7w6" (wing in header)
// B) Leaning Wing (moderate confidence) - "Type 7w6" + helper text
// C) Balanced Wings (adjacent scores close) - "Type 7" (NO wing in header)
// D) Wing Not Yet Clear (null/insufficient) - "Type 7" (NO wing in header)
// NOTE: "balanced" NEVER appears in headerLabel - see enneagramDisplay.ts
// ============================================

type WingDisplayState = 'dominant' | 'leaning' | 'balanced' | 'not_clear';

interface WingDisplayInfo {
  state: WingDisplayState;
  typeLabel: string;           // e.g., "Type 7w6" or "Type 7"
  confidenceBadge: 'High' | 'Exploratory' | 'Low';
  helperText: string | null;   // Explanatory text for non-dominant states
  wingNote?: string | null;    // Optional note for wing section (not header)
}

/**
 * Get wing display info using the CENTRALIZED helper.
 * This is a wrapper to maintain interface compatibility.
 * @see /utils/enneagramDisplay.ts for the canonical implementation
 */
function getWingDisplayInfo(
  coreType: number,
  wing: number | 'balanced' | null,
  confidenceTier: string,
  debugScores?: { wing_scores?: { left: number; right: number; diff: number } }
): WingDisplayInfo {
  // Use centralized helper - SINGLE SOURCE OF TRUTH
  const display = getEnneagramHeaderDisplay({
    coreType,
    wing,
    confidenceTier: confidenceTier as any,
  });
  
  return {
    state: display.wingState,
    typeLabel: display.headerLabel,
    confidenceBadge: display.confidenceBadge,
    helperText: display.wingHelperText,
    wingNote: display.wingNote,
  };
}

export default function EnneagramResults() {
  const router = useRouter();
  const { user } = useAppStore();
  const [result, setResult] = useState<EnneagramResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [showRetakeModal, setShowRetakeModal] = useState(false);
  const [debugExpanded, setDebugExpanded] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  
  // ============================================
  // DEBUG PANEL STATE
  // ============================================
  // Tap counter for hidden gesture activation (tap Confidence badge 7 times)
  const [debugTapCount, setDebugTapCount] = useState(0);
  const debugTapTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // ============================================
  // ANALYTICS REFS (must be at top level)
  // ============================================
  const hasEmittedResultsCTA = useRef(false);
  
  // ============================================
  // ANALYTICS: CTA Shown (once per mount)
  // ============================================
  // NOTE: This useEffect MUST be called before any early returns
  // to maintain consistent hook order
  useEffect(() => {
    // Only emit if we have result data and gate state
    if (!result) return;
    
    const gateInput: EnneagramGateInput = {
      assessment_depth: result.assessment_depth,
      confidence_tier: result.confidence_tier,
      confidence: result.confidence,
      created_at_iso: result.created_at,
    };
    const { gateState } = getEnneagramUpgradeInfo(gateInput);
    
    if (gateState.show_cta && gateState.cta_variant && !hasEmittedResultsCTA.current) {
      emitEnneagramGateCTAShown({
        variant: gateState.cta_variant,
        surface: 'results' as EnneagramGateSurface,
        assessment_depth: gateInput.assessment_depth || null,
        confidence_tier: gateInput.confidence_tier || null,
        result_age_days: gateState.result_age_days,
        has_saved_session: null,
      });
      hasEmittedResultsCTA.current = true;
    }
  }, [result]);
  
  // Computed: Should debug panel be shown?
  // Formula: showDebug = DEBUG_MIRROR_ENV && (urlDebugParam || tapCount >= 7)
  const showDebug = DEBUG_MIRROR_ENV && (getUrlDebugParam() || debugTapCount >= DEBUG_TAP_THRESHOLD);
  
  // ============================================
  // DEBUG WING STATE OVERRIDE
  // ============================================
  // For visual verification of P0 Wing UX Fix
  // Only active when DEBUG_MIRROR_ENV === true
  const [debugWingState, setDebugWingState] = useState<DebugWingState>('off');
  
  // ============================================
  // P5: LONGITUDINAL DATA (DEBUG-only)
  // ============================================
  // Shadow system data - never affects user-facing results
  const [longitudinalData, setLongitudinalData] = useState<LongitudinalSummary | null>(null);
  const [longitudinalLoading, setLongitudinalLoading] = useState(false);

  // Handler for Confidence badge taps (hidden gesture)
  const handleConfidenceTap = () => {
    // Only track taps if DEBUG_MIRROR_ENV is enabled
    if (!DEBUG_MIRROR_ENV) return;
    
    // Reset timeout on each tap (taps must be within 3 seconds)
    if (debugTapTimeoutRef.current) {
      clearTimeout(debugTapTimeoutRef.current);
    }
    
    setDebugTapCount(prev => prev + 1);
    
    // Reset tap count after 3 seconds of inactivity
    debugTapTimeoutRef.current = setTimeout(() => {
      setDebugTapCount(0);
    }, 3000);
  };
  
  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (debugTapTimeoutRef.current) {
        clearTimeout(debugTapTimeoutRef.current);
      }
    };
  }, []);
  const [selectedFeedback, setSelectedFeedback] = useState<FeedbackValue>(null);
  const hasSubmittedFeedbackRef = useRef(false);
  
  useEffect(() => {
    const fetchResult = async () => {
      if (!user?.id) return;
      
      try {
        const response = await getEnneagramResult(user.id);
        if (response.has_result && response.result) {
          setResult(response.result);
        }
      } catch (error) {
        console.error('Error fetching Enneagram result:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchResult();
  }, [user?.id]);
  
  // ============================================
  // P5: FETCH LONGITUDINAL DATA (DEBUG-only)
  // ============================================
  // Only fetch when debug mode is active to avoid unnecessary API calls
  useEffect(() => {
    const fetchLongitudinalData = async () => {
      if (!user?.id || !showDebug) return;
      
      setLongitudinalLoading(true);
      try {
        const response = await fetch(`/api/longitudinal/summary/${user.id}?days=30`);
        if (response.ok) {
          const data = await response.json();
          setLongitudinalData(data.longitudinal);
        }
      } catch (error) {
        console.error('[P5_LONGITUDINAL] Error fetching data:', error);
      } finally {
        setLongitudinalLoading(false);
      }
    };
    
    fetchLongitudinalData();
  }, [user?.id, showDebug]);

  // Redirect if no user
  if (!user) {
    router.replace('/onboarding');
    return null;
  }
  
  const handleViewLens = () => {
    router.replace('/enneagram');
  };
  
  const handleRetakeConfirm = () => {
    setShowRetakeModal(false);
    router.replace('/enneagram/assessment');
  };
  
  // Copy debug JSON to clipboard (dev only)
  const handleCopyDebugJSON = async () => {
    if (!result) return;
    try {
      await Clipboard.setStringAsync(JSON.stringify(result, null, 2));
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };
  
  // Handle feedback selection
  const handleFeedbackSelect = async (feedback: 'yes' | 'mostly' | 'no') => {
    if (!result || !user?.id || hasSubmittedFeedbackRef.current) return;
    
    setSelectedFeedback(feedback);
    hasSubmittedFeedbackRef.current = true;
    
    // Normalize state calibration for clean dataset
    const normalizedState = normalizeStateCalibration(result.state_calibration);
    
    const payload = {
      user_id: user.id,
      accuracy_feedback: feedback,
      timestamp: new Date().toISOString(),
      inferred_core: result.inferred_core,
      inferred_wing: result.inferred_wing,
      confidence: result.confidence,
      energy_state: normalizedState.energy_state,
      life_context: normalizedState.life_context,
      answer_frame: normalizedState.answer_frame,
    };
    
    try {
      await submitEnneagramFeedback(payload);
      
      // Dev logging (only on successful submission)
      if (IS_DEV) {
        console.log('ENNEAGRAM_FEEDBACK:', JSON.stringify(payload));
      }
    } catch (error) {
      // Fail silently - don't show error UI
      // Reset flag so user can retry if they want
      hasSubmittedFeedbackRef.current = false;
    }
  };
  
  // Render debug panel (dev only)
  const renderDebugPanel = () => {
    if (!IS_DEV || !result) return null;
    
    const { debug_scores, state_calibration, top_candidates } = result;
    
    return (
      <View style={styles.debugContainer}>
        <TouchableOpacity 
          style={styles.debugToggle}
          onPress={() => setDebugExpanded(!debugExpanded)}
        >
          <View style={styles.debugToggleLeft}>
            <Ionicons name="bug-outline" size={16} color={Colors.textTertiary} />
            <Text style={styles.debugToggleText}>
              {debugExpanded ? 'Hide Debug' : 'Show Debug'}
            </Text>
          </View>
          <Ionicons 
            name={debugExpanded ? 'chevron-up' : 'chevron-down'} 
            size={16} 
            color={Colors.textTertiary} 
          />
        </TouchableOpacity>
        
        {debugExpanded && (
          <View style={styles.debugContent}>
            {/* Core Result */}
            <View style={styles.debugSection}>
              <Text style={styles.debugSectionTitle}>Result</Text>
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>inferred_core</Text>
                <Text style={styles.debugValue}>{result.inferred_core}</Text>
              </View>
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>inferred_wing</Text>
                <Text style={styles.debugValue}>{result.inferred_wing === null ? '(none)' : String(result.inferred_wing)}</Text>
              </View>
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>confidence</Text>
                <Text style={styles.debugValue}>{result.confidence.toFixed(4)}</Text>
              </View>
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>confidence_tier</Text>
                <Text style={styles.debugValue}>{result.confidence_tier}</Text>
              </View>
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>is_close</Text>
                <Text style={styles.debugValue}>{String(result.is_close)}</Text>
              </View>
            </View>
            
            {/* Top Candidates */}
            <View style={styles.debugSection}>
              <Text style={styles.debugSectionTitle}>Top Candidates</Text>
              {top_candidates.map((c, i) => (
                <View key={i} style={styles.debugRow}>
                  <Text style={styles.debugLabel}>Type {c.type}</Text>
                  <Text style={styles.debugValue}>{(c.probability * 100).toFixed(1)}%</Text>
                </View>
              ))}
            </View>
            
            {/* Wing Scores */}
            {debug_scores?.wing_scores && (
              <View style={styles.debugSection}>
                <Text style={styles.debugSectionTitle}>Wing Scores</Text>
                <View style={styles.debugRow}>
                  <Text style={styles.debugLabel}>wing_left</Text>
                  <Text style={styles.debugValue}>
                    {typeof debug_scores.wing_scores.left === 'number' 
                      ? debug_scores.wing_scores.left.toFixed(3) 
                      : '-'}
                  </Text>
                </View>
                <View style={styles.debugRow}>
                  <Text style={styles.debugLabel}>wing_right</Text>
                  <Text style={styles.debugValue}>
                    {typeof debug_scores.wing_scores.right === 'number' 
                      ? debug_scores.wing_scores.right.toFixed(3) 
                      : '-'}
                  </Text>
                </View>
                <View style={styles.debugRow}>
                  <Text style={styles.debugLabel}>diff</Text>
                  <Text style={styles.debugValue}>
                    {typeof debug_scores.wing_scores.diff === 'number' 
                      ? debug_scores.wing_scores.diff.toFixed(3) 
                      : '-'}
                  </Text>
                </View>
              </View>
            )}
            
            {/* Raw Scores (compact) */}
            {debug_scores?.raw_scores && Object.keys(debug_scores.raw_scores).length > 0 && (
              <View style={styles.debugSection}>
                <Text style={styles.debugSectionTitle}>Raw Scores</Text>
                <Text style={styles.debugJson}>
                  {JSON.stringify(debug_scores.raw_scores, null, 1)}
                </Text>
              </View>
            )}
            
            {/* Z-Scores (compact) */}
            {debug_scores?.z_scores && Object.keys(debug_scores.z_scores).length > 0 && (
              <View style={styles.debugSection}>
                <Text style={styles.debugSectionTitle}>Z-Scores</Text>
                <Text style={styles.debugJson}>
                  {JSON.stringify(debug_scores.z_scores, null, 1)}
                </Text>
              </View>
            )}
            
            {/* State Calibration */}
            {state_calibration && (
              <View style={styles.debugSection}>
                <Text style={styles.debugSectionTitle}>State Calibration</Text>
                <View style={styles.debugRow}>
                  <Text style={styles.debugLabel}>energy_state</Text>
                  <Text style={styles.debugValue}>{state_calibration.energy_state || '-'}</Text>
                </View>
                <View style={styles.debugRow}>
                  <Text style={styles.debugLabel}>life_context</Text>
                  <Text style={styles.debugValue}>{state_calibration.life_context || '-'}</Text>
                </View>
                <View style={styles.debugRow}>
                  <Text style={styles.debugLabel}>answer_frame</Text>
                  <Text style={styles.debugValue}>{state_calibration.answer_frame || '-'}</Text>
                </View>
              </View>
            )}
            
            {/* Copy Button */}
            <TouchableOpacity 
              style={styles.debugCopyButton}
              onPress={handleCopyDebugJSON}
            >
              <Ionicons 
                name={copySuccess ? 'checkmark' : 'copy-outline'} 
                size={14} 
                color={copySuccess ? '#4CAF50' : Colors.textTertiary} 
              />
              <Text style={[
                styles.debugCopyText,
                copySuccess && styles.debugCopySuccess
              ]}>
                {copySuccess ? 'Copied!' : 'Copy debug JSON'}
              </Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };
  
  // ============================================
  // TESTER DEBUG PANEL
  // ============================================
  // Renders ONLY when: showDebug === true
  // showDebug = DEBUG_MIRROR_ENV && (urlDebugParam || tapCount >= 7)
  // Returns null (no layout space) when conditions not met
  // ============================================
  const renderTesterDebugPanel = () => {
    // Guard: Do not render if conditions not met (no empty space)
    if (!showDebug || !result) return null;
    
    const { top_candidates, debug_scores, inferred_core } = result;
    const wingTypes = getWingTypes(inferred_core);
    
    // Get primary and second type from top_candidates
    const primaryType = top_candidates[0]?.type ?? '-';
    const primaryScore = top_candidates[0]?.probability != null 
      ? (top_candidates[0].probability * 100).toFixed(1) + '%' 
      : '-';
    const secondType = top_candidates[1]?.type ?? '-';
    const secondScore = top_candidates[1]?.probability != null 
      ? (top_candidates[1].probability * 100).toFixed(1) + '%' 
      : '-';
    
    // Get wing scores
    const leftWingScore = debug_scores?.wing_scores?.left != null
      ? debug_scores.wing_scores.left.toFixed(3)
      : '-';
    const rightWingScore = debug_scores?.wing_scores?.right != null
      ? debug_scores.wing_scores.right.toFixed(3)
      : '-';
    
    // All possible debug wing states for toggle
    const debugWingStates: DebugWingState[] = ['off', 'dominant', 'leaning', 'balanced', 'not_clear'];
    
    return (
      <View style={styles.testerDebugContainer}>
        {/* DEBUG BADGE - clearly mark as mock data */}
        <View style={styles.debugBadge}>
          <Ionicons name="bug-outline" size={14} color="#FF6B6B" />
          <Text style={styles.debugBadgeText}>DEBUG MODE — MOCK DATA</Text>
        </View>
        
        {/* Wing State Override Section */}
        <View style={styles.debugWingOverrideSection}>
          <Text style={styles.debugSectionLabel}>WING STATE OVERRIDE (P0 Visual Test)</Text>
          <View style={styles.debugWingToggleRow}>
            {debugWingStates.map((state) => (
              <TouchableOpacity
                key={state}
                style={[
                  styles.debugWingToggleButton,
                  debugWingState === state && styles.debugWingToggleButtonActive,
                ]}
                onPress={() => setDebugWingState(state)}
              >
                <Text style={[
                  styles.debugWingToggleText,
                  debugWingState === state && styles.debugWingToggleTextActive,
                ]}>
                  {DEBUG_WING_STATE_LABELS[state]}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          {debugWingState !== 'off' && (
            <View style={styles.debugMockIndicator}>
              <Ionicons name="information-circle" size={14} color="#FFB800" />
              <Text style={styles.debugMockIndicatorText}>
                UI above shows MOCK wing state: {DEBUG_WING_STATE_LABELS[debugWingState]}
              </Text>
            </View>
          )}
        </View>
        
        {/* Raw Data Section */}
        <View style={styles.debugDataSection}>
          <Text style={styles.debugSectionLabel}>RAW RESULT DATA</Text>
          <Text style={styles.testerDebugText}>primary_type: {primaryType} (score: {primaryScore})</Text>
          <Text style={styles.testerDebugText}>second_type: {secondType} (score: {secondScore})</Text>
          <Text style={styles.testerDebugText}>left_wing_type: {wingTypes.left} (score: {leftWingScore})</Text>
          <Text style={styles.testerDebugText}>right_wing_type: {wingTypes.right} (score: {rightWingScore})</Text>
          <Text style={styles.testerDebugText}>inferred_wing (real): {result.inferred_wing === null ? '(none)' : String(result.inferred_wing)}</Text>
          <Text style={styles.testerDebugText}>confidence_tier (real): {result.confidence_tier}</Text>
        </View>
        
        {/* P5 Longitudinal Section (SHADOW SYSTEM) */}
        <View style={styles.debugDataSection}>
          <Text style={styles.debugSectionLabel}>P5 LONGITUDINAL (SHADOW)</Text>
          {longitudinalLoading ? (
            <ActivityIndicator size="small" color="#aaaacc" />
          ) : longitudinalData ? (
            <>
              <Text style={styles.testerDebugText}>type_stability: {longitudinalData.type_stability.toFixed(2)}</Text>
              <Text style={styles.testerDebugText}>wing_stability: {longitudinalData.wing_stability.toFixed(2)}</Text>
              <Text style={styles.testerDebugText}>evidence_count: {longitudinalData.evidence_volume.total} (last 30d: {longitudinalData.evidence_volume.last_30_days})</Text>
              <Text style={styles.testerDebugText}>top_types: {longitudinalData.top_types_over_time.map(t => `${t.type}(${(t.share * 100).toFixed(0)}%)`).join(', ') || '(none)'}</Text>
              <Text style={styles.testerDebugText}>confidence_modifier: {longitudinalData.confidence_modifier}</Text>
              <Text style={styles.testerDebugText}>recommended_next: {longitudinalData.recommended_next_step}</Text>
            </>
          ) : (
            <Text style={styles.testerDebugText}>No longitudinal data yet</Text>
          )}
          <Text style={[styles.testerDebugText, { marginTop: 6, color: '#888' }]}>
            ⚠️ Shadow only - does NOT affect displayed results
          </Text>
        </View>
      </View>
    );
  };
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.text} />
          <Text style={styles.loadingText}>Loading your results...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  if (!result) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.loadingContainer}>
          <Ionicons name="alert-circle-outline" size={48} color={Colors.textTertiary} />
          <Text style={styles.errorTitle}>No Results Found</Text>
          <Text style={styles.errorText}>
            It looks like you haven&apos;t completed the assessment yet.
          </Text>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => router.replace('/enneagram/assessment')}
          >
            <Text style={styles.primaryButtonText}>Take Assessment</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  const wingDisplay = result.inferred_wing === 'balanced' 
    ? 'Balanced Wings' 
    : `Wing ${result.inferred_wing}`;
  
  // ============================================
  // COMPUTE WING INFO (with debug override support)
  // ============================================
  // If debug override is active, use mock data
  // Otherwise use real result data
  const debugOverride = DEBUG_MIRROR_ENV ? getDebugWingOverride(result.inferred_core, debugWingState) : null;
  
  // Get comprehensive wing display info
  const wingInfo = debugOverride 
    ? getWingDisplayInfo(
        result.inferred_core,
        debugOverride.mockWing,
        debugOverride.mockConfidenceTier,
        result.debug_scores
      )
    : getWingDisplayInfo(
        result.inferred_core,
        result.inferred_wing,
        result.confidence_tier,
        result.debug_scores
      );
  
  const confidenceLabel = result.confidence_tier === 'high' 
    ? 'High' 
    : result.confidence_tier === 'medium' 
      ? 'Medium' 
      : 'Low';
  
  // ============================================
  // VERSION CHECK - Determine if this is the latest assessment
  // ============================================
  // Latest assessment requires both v2 AND deep depth
  const isLatestAssessment = 
    result.assessment_version === 'v2' && 
    result.assessment_depth === 'deep';
  
  // ============================================
  // ENNEAGRAM GATE STATE (Upgrade/Retake CTAs)
  // ============================================
  // Centralized logic for determining when to show upgrade CTAs
  // See utils/enneagramGateLogic.ts for rules
  const gateInput: EnneagramGateInput = {
    assessment_depth: result.assessment_depth,
    confidence_tier: result.confidence_tier,
    confidence: result.confidence,
    created_at_iso: result.created_at,
  };
  const { gateState, ctaCopy, showPreliminaryLabel } = getEnneagramUpgradeInfo(gateInput);
  
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
          <Ionicons name="close" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Your Results</Text>
        <View style={styles.headerSpacer} />
      </View>
      
      <ScrollView contentContainerStyle={styles.content}>
        {/* ============================================
            VERSION NUDGE CARD (Only if not latest assessment)
            ============================================
            Shows when assessment_version !== "v2" OR assessment_depth !== "deep"
            Calm, non-destructive prompt to retake with refined assessment.
        */}
        {!isLatestAssessment && (
          <View style={styles.versionNudgeCard}>
            <Ionicons name="sparkles-outline" size={22} color={Colors.accent} style={styles.versionNudgeIcon} />
            <Text style={styles.versionNudgeTitle}>Your mirror has evolved.</Text>
            <Text style={styles.versionNudgeBody}>
              We've refined how Enneagram patterns are assessed.{'\n'}
              A fresh pass can give you a clearer signal.
            </Text>
            <TouchableOpacity
              style={styles.versionNudgeButton}
              onPress={() => router.push('/enneagram/assessment')}
            >
              <Text style={styles.versionNudgeButtonText}>Retake the assessment</Text>
              <Ionicons name="arrow-forward" size={16} color={Colors.surface} />
            </TouchableOpacity>
          </View>
        )}

        {/* Main Result Card */}
        <View style={styles.resultCard}>
          <Text style={styles.pageTitle}>Your Enneagram Profile</Text>
          
          {/* Type Badge */}
          <View style={styles.typeBadge}>
            <Text style={styles.typeNumber}>{result.inferred_core}</Text>
          </View>
          
          {/* Type Title - Using new wing display system */}
          <Text style={styles.typeTitle}>
            {wingInfo.typeLabel}
          </Text>
          <Text style={styles.typeName}>
            {TYPE_NAMES[result.inferred_core]}
          </Text>
          
          {/* Preliminary Label - shown for short assessments */}
          <PreliminaryLabel 
            visible={showPreliminaryLabel} 
            testID="preliminary-label-results"
          />
          
          {/* Confidence Badge - Tappable for hidden debug gesture */}
          <View style={styles.confidenceRow}>
            <TouchableOpacity 
              onPress={handleConfidenceTap}
              activeOpacity={0.8}
              style={[
                styles.confidenceBadge,
                wingInfo.confidenceBadge === 'High' && styles.confidenceHigh,
                wingInfo.confidenceBadge === 'Exploratory' && styles.confidenceMedium,
                wingInfo.confidenceBadge === 'Low' && styles.confidenceLow,
              ]}
            >
              <Text style={styles.confidenceText}>
                {wingInfo.confidenceBadge}
              </Text>
            </TouchableOpacity>
          </View>
          
          {/* Helper text for non-dominant wing states */}
          {wingInfo.helperText && (
            <Text style={styles.wingHelperText}>
              {wingInfo.helperText}
            </Text>
          )}
        </View>
        
        {/* Upgrade CTA - shown based on gate logic */}
        {ctaCopy && gateState.cta_variant && (
          <EnneagramUpgradeCTA 
            ctaCopy={ctaCopy}
            surface="results"
            ctaVariant={gateState.cta_variant}
            assessmentDepth={gateInput.assessment_depth || null}
            confidenceTier={gateInput.confidence_tier || null}
            resultAgeDays={gateState.result_age_days}
            testID="upgrade-cta-results"
          />
        )}
        
        {/* Feedback Card */}
        <View style={styles.feedbackCard}>
          <Text style={styles.feedbackTitle}>Does this feel accurate?</Text>
          <View style={styles.feedbackButtons}>
            <TouchableOpacity
              style={[
                styles.feedbackButton,
                selectedFeedback === 'yes' && styles.feedbackButtonSelected,
              ]}
              onPress={() => handleFeedbackSelect('yes')}
              disabled={hasSubmittedFeedbackRef.current && selectedFeedback !== null}
            >
              {selectedFeedback === 'yes' && (
                <Ionicons name="checkmark" size={14} color={Colors.text} style={styles.feedbackCheckmark} />
              )}
              <Text style={[
                styles.feedbackButtonText,
                selectedFeedback === 'yes' && styles.feedbackButtonTextSelected,
              ]}>Yes</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[
                styles.feedbackButton,
                selectedFeedback === 'mostly' && styles.feedbackButtonSelected,
              ]}
              onPress={() => handleFeedbackSelect('mostly')}
              disabled={hasSubmittedFeedbackRef.current && selectedFeedback !== null}
            >
              {selectedFeedback === 'mostly' && (
                <Ionicons name="checkmark" size={14} color={Colors.text} style={styles.feedbackCheckmark} />
              )}
              <Text style={[
                styles.feedbackButtonText,
                selectedFeedback === 'mostly' && styles.feedbackButtonTextSelected,
              ]}>Mostly</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={[
                styles.feedbackButton,
                selectedFeedback === 'no' && styles.feedbackButtonSelected,
              ]}
              onPress={() => handleFeedbackSelect('no')}
              disabled={hasSubmittedFeedbackRef.current && selectedFeedback !== null}
            >
              {selectedFeedback === 'no' && (
                <Ionicons name="checkmark" size={14} color={Colors.text} style={styles.feedbackCheckmark} />
              )}
              <Text style={[
                styles.feedbackButtonText,
                selectedFeedback === 'no' && styles.feedbackButtonTextSelected,
              ]}>No</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        {/* Why Paragraph */}
        <View style={styles.whyCard}>
          <Text style={styles.whyTitle}>Why this type?</Text>
          <Text style={styles.whyText}>
            Your responses suggest that {TYPE_MOTIVATIONS[result.inferred_core]} are central to how you navigate the world. This core pattern shapes your decisions, relationships, and growth edges.
          </Text>
        </View>
        
        {/* Top Candidates */}
        <View style={styles.candidatesCard}>
          <Text style={styles.candidatesTitle}>Top Patterns</Text>
          {result.top_candidates.map((candidate, index) => (
            <View key={candidate.type} style={styles.candidateRow}>
              <View style={styles.candidateInfo}>
                <Text style={styles.candidateRank}>{index + 1}</Text>
                <Text style={styles.candidateType}>
                  Type {candidate.type} — {TYPE_NAMES[candidate.type]}
                </Text>
              </View>
              <Text style={styles.candidateProbability}>
                {Math.round(candidate.probability * 100)}%
              </Text>
            </View>
          ))}
        </View>
        
        {/* Close Call Notice */}
        {result.is_close && result.top_candidates.length >= 2 && (
          <View style={styles.closeCallCard}>
            <Ionicons name="information-circle-outline" size={18} color={Colors.textSecondary} />
            <Text style={styles.closeCallText}>
              Close call between Type {result.top_candidates[0].type} and Type {result.top_candidates[1].type} — your result may depend on context and development level.
            </Text>
          </View>
        )}
        
        {/* ============================================
            DEEP ASSESSMENT CTA (Mirror Voice)
            ============================================
            Show when:
            - confidence_tier is not 'high' OR
            - assessment_depth is not 'deep' (quick assessment was taken) OR
            - no assessment_depth field exists
            
            Uses neutral, observational language.
        */}
        {(result.confidence_tier !== 'high' || !result.assessment_depth || result.assessment_depth !== 'deep') && (
          <View style={styles.deepAssessmentCTA}>
            <Ionicons name="compass-outline" size={24} color={Colors.accent} style={{ marginBottom: 8 }} />
            <Text style={styles.deepAssessmentTitle}>Want a clearer mirror?</Text>
            <Text style={styles.deepAssessmentText}>
              If your result felt close or uncertain, a deeper assessment can sharpen the signal.
            </Text>
            <TouchableOpacity
              style={styles.deepAssessmentButton}
              onPress={() => router.push('/enneagram/assessment')}
            >
              <Text style={styles.deepAssessmentButtonText}>Take the deep assessment</Text>
              <Ionicons name="arrow-forward" size={16} color={Colors.background} />
            </TouchableOpacity>
          </View>
        )}
        
        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.primaryButton} onPress={handleViewLens}>
            <Text style={styles.primaryButtonText}>View Enneagram Lens</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.secondaryButton} 
            onPress={() => setShowRetakeModal(true)}
          >
            <Text style={styles.secondaryButtonText}>Retake Assessment</Text>
          </TouchableOpacity>
        </View>
        
        {/* Tester Debug Panel (DEBUG_MIRROR only) */}
        {renderTesterDebugPanel()}
        
        {/* Debug Panel (Dev Only) */}
        {renderDebugPanel()}
        
        <View style={styles.bottomSpacer} />
      </ScrollView>
      
      {/* Retake Confirmation Modal */}
      <Modal
        visible={showRetakeModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowRetakeModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Retake Assessment?</Text>
            <Text style={styles.modalText}>
              This will replace your current results. The assessment takes about 10-12 minutes.
            </Text>
            <View style={styles.modalActions}>
              <TouchableOpacity 
                style={styles.modalCancelButton}
                onPress={() => setShowRetakeModal(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.modalConfirmButton}
                onPress={handleRetakeConfirm}
              >
                <Text style={styles.modalConfirmText}>Retake</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  headerSpacer: {
    width: 32,
  },
  content: {
    padding: 24,
  },
  
  // Loading & Error
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
    color: Colors.textSecondary,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  
  // Result Card
  resultCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  pageTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textTertiary,
    marginBottom: 20,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  typeBadge: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  typeNumber: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.background,
  },
  typeTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
    textAlign: 'center',
  },
  typeName: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginBottom: 16,
  },
  confidenceRow: {
    flexDirection: 'row',
  },
  confidenceBadge: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: Colors.border,
  },
  confidenceHigh: {
    backgroundColor: '#D4EDDA',
  },
  confidenceMedium: {
    backgroundColor: '#FFF3CD',
  },
  confidenceLow: {
    backgroundColor: '#F8D7DA',
  },
  confidenceText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
  },
  wingHelperText: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 12,
    paddingHorizontal: 16,
  },
  
  // Why Card
  // Feedback Card
  feedbackCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  feedbackTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textSecondary,
    marginBottom: 12,
    textAlign: 'center',
  },
  feedbackButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 10,
  },
  feedbackButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.background,
    minWidth: 70,
  },
  feedbackButtonSelected: {
    borderColor: Colors.text,
    backgroundColor: Colors.surfaceLight,
  },
  feedbackButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  feedbackButtonTextSelected: {
    color: Colors.text,
  },
  feedbackCheckmark: {
    marginRight: 4,
  },
  
  // Why Card
  whyCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  whyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  whyText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  
  // Candidates Card
  candidatesCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  candidatesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 16,
  },
  candidateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  candidateInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  candidateRank: {
    width: 24,
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
  },
  candidateType: {
    fontSize: 14,
    color: Colors.text,
    flex: 1,
  },
  candidateProbability: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  
  // Close Call Card
  closeCallCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 10,
    padding: 14,
    marginBottom: 24,
  },
  closeCallText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  
  // Version Nudge Card
  versionNudgeCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.accent,
    borderStyle: 'dashed',
  },
  versionNudgeIcon: {
    marginBottom: 8,
  },
  versionNudgeTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  versionNudgeBody: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
  },
  versionNudgeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
  },
  versionNudgeButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.surface,
  },
  
  // Deep Assessment CTA
  deepAssessmentCTA: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  deepAssessmentTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  deepAssessmentText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
  },
  deepAssessmentButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: Colors.text,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
  },
  deepAssessmentButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.background,
  },
  
  // Actions
  actionsContainer: {
    gap: 12,
  },
  primaryButton: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  secondaryButton: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  
  bottomSpacer: {
    height: 20,
  },
  
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: Colors.background,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  modalText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 24,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalCancelButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  modalCancelText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },
  modalConfirmButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: Colors.text,
    borderRadius: 10,
  },
  modalConfirmText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.background,
  },
  
  // Debug Panel (Dev Only)
  debugContainer: {
    marginTop: 24,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    borderStyle: 'dashed',
    overflow: 'hidden',
  },
  debugToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: Colors.surfaceLight,
  },
  debugToggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  debugToggleText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.textTertiary,
  },
  debugContent: {
    padding: 12,
    backgroundColor: Colors.background,
  },
  debugSection: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  debugSectionTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  debugRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 3,
  },
  debugLabel: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  debugValue: {
    fontSize: 11,
    fontWeight: '500',
    color: Colors.text,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  debugJson: {
    fontSize: 10,
    color: Colors.textSecondary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 14,
    backgroundColor: Colors.surfaceLight,
    padding: 8,
    borderRadius: 4,
  },
  debugCopyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    marginTop: 4,
    borderRadius: 6,
    backgroundColor: Colors.surfaceLight,
  },
  debugCopyText: {
    fontSize: 11,
    fontWeight: '500',
    color: Colors.textTertiary,
  },
  debugCopySuccess: {
    color: '#4CAF50',
  },
  
  // Tester Debug Panel (DEBUG_MIRROR only)
  testerDebugContainer: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#FF6B6B',
    borderStyle: 'dashed',
  },
  debugBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#2d2d44',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  debugBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FF6B6B',
    letterSpacing: 1,
  },
  debugWingOverrideSection: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#3d3d5c',
  },
  debugSectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#8888aa',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  debugWingToggleRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  debugWingToggleButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: '#2d2d44',
    borderWidth: 1,
    borderColor: '#3d3d5c',
  },
  debugWingToggleButtonActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  debugWingToggleText: {
    fontSize: 11,
    fontWeight: '500',
    color: '#aaaacc',
  },
  debugWingToggleTextActive: {
    color: '#ffffff',
    fontWeight: '600',
  },
  debugMockIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
    padding: 10,
    backgroundColor: 'rgba(255, 184, 0, 0.15)',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 184, 0, 0.3)',
  },
  debugMockIndicatorText: {
    fontSize: 11,
    color: '#FFB800',
    flex: 1,
  },
  debugDataSection: {
    backgroundColor: '#2d2d44',
    borderRadius: 8,
    padding: 12,
  },
  testerDebugTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  testerDebugText: {
    fontSize: 11,
    color: '#ccccdd',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 18,
  },
});
