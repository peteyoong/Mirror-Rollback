/**
 * PatternCard.tsx
 * ================
 * 
 * Pattern Mirror V5 - Two-Layer Mirror Output
 * 
 * Structure:
 * A. CORE PATTERN (always visible) - One sharp, behaviorally meaningful sentence
 * B. WHY THIS MAY BE SHOWING UP (always visible) - 1-2 sentences on timing/activation
 * C. HOW THIS WAS DERIVED (collapsible) - Cross-lens proof showing convergence
 * 
 * Design Principles:
 * - Insight creates resonance (top line)
 * - Explanation creates trust (proof layer)
 * - User should feel the system is thinking, not guessing
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';
import { InsightCardFooter } from './InsightCardFooter';

// ===== V6 THREE-LAYER INTERFACES =====

interface CoreInsight {
  title: string;
  text: string;
}

interface WhyShowingUp {
  text: string;
  is_timing_driven: boolean;
}

interface LensDerivation {
  lens: string;
  signal: string;
  contributed: boolean;
  // V7: Astrology can now include individual drivers
  drivers?: Array<{
    key: string;
    text: string;
    category: string;
    priority: number;
  }>;
  driver_count?: number;
}

interface CrossLensDerivation {
  lenses: LensDerivation[];
  convergence_count: number;
  shows_convergence: boolean;
  convergence_note: string | null;
}

// V6 NEW: Friction and Practical layers
interface FrictionLayer {
  text: string;
}

interface PracticalLayer {
  text: string;
}

interface TwoLayerOutput {
  core_insight: CoreInsight;
  why_showing_up: WhyShowingUp;
  cross_lens_derivation: CrossLensDerivation;
  // V6 NEW
  friction?: FrictionLayer;
  practical?: PracticalLayer;
  display_config: {
    core_always_visible: boolean;
    why_always_visible: boolean;
    derivation_collapsed_by_default: boolean;
    derivation_label: string;
    friction_always_visible?: boolean;
    practical_always_visible?: boolean;
  };
}

interface PatternGenius {
  description: string;
  archetype?: string | null;
}

interface Pattern {
  title: string;
  what_you_may_be: string;
  challenge: string[];
  genius: PatternGenius;
  micro_shifts: string[];
}

interface SignalsBySource {
  journal?: string[];
  mirror_chat?: string[];
  lifeline?: string[];
  timing?: string[];
}

// ===== V2 INTERFACES =====

interface PersonalPattern {
  selected_pattern_id: string;
  selected_pattern_title: string;
  selected_pattern_summary: string;
  primary_signal_sources: string[];
  primary_signal_evidence: Record<string, any>;
  signal_strength: string;
  signal_score: number;
}

interface TimingAmplifier {
  active_timing_themes: string[];
  timing_summary: string | null;
  transit_score: number;
  timing_role: 'amplifier' | 'fallback';
  lunar_phase?: string | null;
  seasonal_context?: string | null;
}

interface Narrative {
  main_explanation: string;
  timing_note: string | null;
  evidence_summary: string | null;
  combined: string;
}

interface EvidenceMatch {
  text: string;
  matched_keyword: string;
  strength: 'high' | 'moderate';
  date?: string | null;
  emotional_tone?: string | null;
}

interface Evidence {
  pattern_id: string;
  contributing_sources: string[];
  matched_evidence: Record<string, EvidenceMatch[]>;
  total_matches: number;
  primary_source: string | null;
}

interface SelectionDebug {
  top_3_by_signal_score: Array<{pattern_id: string; signal_score: number; title: string}>;
  top_3_by_final_score: Array<{pattern_id: string; final: number; signal: number; transit: number}>;
  fallback_mode: boolean;
  timing_changed_winner: boolean;
  timing_only_amplified: boolean;
  signal_winner: string;
  final_winner: string;
}

interface PatternData {
  // V5 Two-Layer Output
  two_layer_output?: TwoLayerOutput;
  
  // V2 Structure
  personal_pattern?: PersonalPattern;
  timing_amplifier?: TimingAmplifier;
  narrative?: Narrative;
  evidence?: Evidence;
  selection_debug?: SelectionDebug;
  
  // Legacy fields
  pattern: Pattern;
  pattern_id?: string;
  cached: boolean;
  generated_at: string;
  signal_strength?: string;
  signals_by_source?: SignalsBySource;
  timing_context?: string[];
  active_themes?: string[];
  personal_activations?: Array<{
    target: string;
    gene_key: number;
    score: number;
    name: string;
    description: string;
  }>;
  unified_narrative?: string;
  fallback?: boolean;
}

// Source display names
const SOURCE_LABELS: Record<string, string> = {
  journal: 'Your journal entries',
  mirror_chat: 'Mirror conversations',
  lifeline: 'Your lifeline events',
  timing: 'Current timing (amplifying)',
};

interface PatternCardProps {
  userId: string;
  onPatternLoaded?: (pattern: Pattern | null) => void;
}

export default function PatternCard({ userId, onPatternLoaded }: PatternCardProps) {
  const { theme } = useTheme();
  const router = useRouter();
  
  const [patternData, setPatternData] = useState<PatternData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [signalsExpanded, setSignalsExpanded] = useState(false);
  const [detailsExpanded, setDetailsExpanded] = useState(false);
  const [derivationExpanded, setDerivationExpanded] = useState(false);

  const loadPattern = useCallback(async () => {
    if (!userId) return;
    
    setIsLoading(true);
    setError(null);
    // ALWAYS reset details to collapsed when loading new pattern
    setDetailsExpanded(false);
    setSignalsExpanded(false);
    setDerivationExpanded(false);
    
    try {
      const response = await api.get(`/patterns/${userId}`);
      console.log('[PatternCard] RAW API RESPONSE:', JSON.stringify(response.data, null, 2).substring(0, 500));
      console.log('[PatternCard] two_layer_output KEY EXISTS:', 'two_layer_output' in response.data);
      console.log('[PatternCard] two_layer_output VALUE:', response.data?.two_layer_output);
      setPatternData(response.data);
      onPatternLoaded?.(response.data?.pattern || null);
    } catch (err: any) {
      console.error('[PatternCard] Load error:', err);
      setError('Unable to load pattern');
      onPatternLoaded?.(null);
    } finally {
      setIsLoading(false);
    }
  }, [userId, onPatternLoaded]);

  useEffect(() => {
    loadPattern();
  }, [loadPattern]);

  // Reset expanded states when userId changes
  useEffect(() => {
    setDetailsExpanded(false);
    setSignalsExpanded(false);
    setDerivationExpanded(false);
  }, [userId]);

  // Handle "Reflect on this" button
  const handleReflect = useCallback(() => {
    if (!patternData?.pattern) return;
    
    // Navigate to reflection-chat with seeded message about the pattern
    const seedMessage = `This pattern showed up:\n\n"${patternData.pattern.what_you_may_be}"\n\nHelp me see what I'm not seeing.`;
    
    router.push({
      pathname: '/reflection-chat',
      params: {
        context: 'pattern',
        seedMessage: seedMessage,
        autoSend: 'true',
      }
    });
  }, [patternData, router]);

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading your signals...
          </Text>
        </View>
      </View>
    );
  }

  // Error state
  if (error || !patternData?.pattern) {
    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.emptyContainer}>
          <Text style={[styles.emptyText, { color: theme.textTertiary }]}>
            Pattern will appear as you reflect more
          </Text>
        </View>
      </View>
    );
  }

  const { pattern } = patternData;
  
  // V5: Extract two-layer output (primary)
  const twoLayer = patternData.two_layer_output;
  const coreInsight = twoLayer?.core_insight;
  const whyShowingUp = twoLayer?.why_showing_up;
  const crossLensDerivation = twoLayer?.cross_lens_derivation;
  
  // V4: Extract two-timescale data (fallback)
  const v4 = (patternData as any).pattern_card_v4;
  const coreMemory = v4?.core_pattern_memory;
  const dailyAngle = v4?.daily_angle;
  const evidencePanel = v4?.evidence_panel;
  const v4TimingAmplifier = v4?.timing_amplifier;
  
  // V2 fallbacks
  const personalPattern = patternData.personal_pattern;
  const timingAmplifier = v4TimingAmplifier || patternData.timing_amplifier;
  const narrative = patternData.narrative;
  const evidence = patternData.evidence;
  const isAmplifierMode = timingAmplifier?.timing_role === 'amplifier';
  
  // ===== CRITICAL DEBUG LOGGING =====
  console.log('========================================');
  console.log('[PatternCard] USING_TWO_LAYER_OUTPUT:', !!twoLayer);
  console.log('[PatternCard] RENDERING_LEGACY_PATTERN_CARD:', !twoLayer);
  if (twoLayer) {
    console.log('[PatternCard] crossLensDerivation lenses count:', crossLensDerivation?.lenses?.length || 0);
    console.log('[PatternCard] derivationExpanded state:', derivationExpanded);
  }
  console.log('========================================');

  // ===== HELPER: Translate timing themes to plain English =====
  const translateWhyShowingUp = (text: string): string => {
    if (!text) return '';
    
    // Map of internal keys to plain English
    const translations: Record<string, string> = {
      'identity_shift': 'a shift in how you see yourself',
      'renewal_cycle': 'renewal and fresh beginnings',
      'transition_threshold': 'a threshold moment between phases',
      'emotional_sensitivity': 'heightened emotional awareness',
      'relational_harmony': 'connection and relationship energy',
      'relational_sensitivity': 'sensitivity in relationships',
      'pressure': 'building pressure',
      'expansion': 'expansion and growth',
      'contraction': 'consolidation and pulling inward',
      'reset_cycle': 'a natural reset',
      'softening_phase': 'softening and opening',
      'integration_phase': 'integration and bringing pieces together',
    };
    
    let result = text;
    
    // Replace internal tokens with plain English
    Object.entries(translations).forEach(([key, value]) => {
      const regex = new RegExp(key, 'gi');
      result = result.replace(regex, value);
    });
    
    // Clean up patterns like "(renewal and fresh beginnings, a shift in how you see yourself)"
    result = result.replace(/\(([^)]+)\)/g, (match, content) => {
      // If it looks like a list of themes, convert to prose
      const parts = content.split(/,\s*/);
      if (parts.length === 2) {
        return `${parts[0]} and ${parts[1]}`;
      } else if (parts.length > 2) {
        return parts.slice(0, -1).join(', ') + ', and ' + parts[parts.length - 1];
      }
      return content;
    });
    
    // Clean up "current timing themes" phrasing
    result = result.replace(/current timing themes?\s*/gi, 'current timing points to ');
    result = result.replace(/highlight this facet/gi, '');
    result = result.replace(/\s+/g, ' ').trim();
    
    // Remove trailing period if duplicated
    result = result.replace(/\.\s*$/, '');
    
    return result;
  };

  // ===== V6 THREE-LAYER RENDER (Insight + Proof + Usefulness) =====
  if (twoLayer) {
    const translatedWhyText = translateWhyShowingUp(whyShowingUp?.text || '');
    const contributingLenses = crossLensDerivation?.lenses?.filter(l => l.contributed && l.signal) || [];
    
    // V6: Extract friction and practical layers
    const frictionText = twoLayer.friction?.text || '';
    const practicalText = twoLayer.practical?.text || '';
    
    // Debug logging for V6
    console.log('[PatternCard] V6 RENDER - contributingLenses count:', contributingLenses.length);
    console.log('[PatternCard] V6 RENDER - derivationExpanded:', derivationExpanded);
    console.log('[PatternCard] V6 RENDER - frictionText:', frictionText?.substring(0, 50));
    console.log('[PatternCard] V6 RENDER - practicalText:', practicalText?.substring(0, 50));
    
    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>        
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.headerLabel, { color: theme.textTertiary }]}>PATTERN</Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            What may be happening right now
          </Text>
        </View>

        {/* ===== A. CORE PATTERN (always visible) ===== */}
        <Text style={[styles.patternTitle, { color: theme.text }]}>
          {coreInsight?.title || pattern.title}
        </Text>
        
        <View style={styles.section}>
          <Text style={[styles.coreInsightText, { color: theme.text }]}>
            {coreInsight?.text || pattern.what_you_may_be}
          </Text>
        </View>

        {/* ===== B. WHY THIS MAY BE SHOWING UP (always visible, plain English) ===== */}
        {translatedWhyText ? (
          <View style={[styles.whyShowingUpSection, { borderColor: theme.border }]}>
            <Text style={[styles.whyShowingUpLabel, { color: theme.textTertiary }]}>
              WHY THIS MAY BE SHOWING UP
            </Text>
            <Text style={[styles.whyShowingUpText, { color: theme.textSecondary }]}>
              {translatedWhyText}
            </Text>
          </View>
        ) : null}

        {/* ===== C. HOW THIS WAS DERIVED (collapsible accordion) ===== */}
        {contributingLenses.length > 0 ? (
          <View style={styles.derivationContainer}>
            <TouchableOpacity
              onPress={() => {
                console.log('[PatternCard] DERIVED_ACCORDION_TAPPED');
                console.log('[PatternCard] DERIVED_ACCORDION_EXPANDED =', !derivationExpanded);
                setDerivationExpanded(!derivationExpanded);
              }}
              activeOpacity={0.6}
              style={styles.derivationTrigger}
            >
              <View style={styles.derivationTriggerRow}>
                <Text style={[styles.derivationTriggerText, { color: theme.textTertiary }]}>
                  {derivationExpanded ? 'Hide how this was derived' : 'How this was derived'}
                </Text>
                <Text style={[styles.derivationArrow, { color: theme.textTertiary }]}>
                  {derivationExpanded ? '▲' : '▼'}
                </Text>
              </View>
              <Text style={[styles.convergenceBadge, { color: theme.accent }]}>
                {contributingLenses.length} {contributingLenses.length === 1 ? 'system points' : 'systems point'} to this theme
              </Text>
            </TouchableOpacity>

            {derivationExpanded && (
              <View style={[styles.derivationSection, { borderTopColor: theme.border }]}>
                {contributingLenses.map((lens, index) => {
                  // V7: For Astrology, show individual drivers if available
                  if (lens.lens === 'Astrology' && lens.drivers && lens.drivers.length > 0) {
                    return (
                      <View key={index} style={styles.lensItemWithDrivers}>
                        <Text style={[styles.lensName, { color: theme.textSecondary }]}>
                          {lens.lens}
                        </Text>
                        <View style={styles.driversContainer}>
                          {lens.drivers.slice(0, 3).map((driver, dIdx) => (
                            <View key={dIdx} style={styles.driverItem}>
                              <Text style={[styles.lensArrow, { color: theme.textTertiary }]}>
                                →
                              </Text>
                              <Text style={[styles.driverText, { color: theme.text }]}>
                                {driver.text}
                              </Text>
                            </View>
                          ))}
                        </View>
                      </View>
                    );
                  }
                  
                  // Default: single line for other lenses
                  return (
                    <View key={index} style={styles.lensItem}>
                      <Text style={[styles.lensName, { color: theme.textSecondary }]}>
                        {lens.lens}
                      </Text>
                      <Text style={[styles.lensArrow, { color: theme.textTertiary }]}>
                        →
                      </Text>
                      <Text style={[styles.lensSignal, { color: theme.text }]}>
                        {lens.signal}
                      </Text>
                    </View>
                  );
                })}
              </View>
            )}
          </View>
        ) : null}

        {/* ===== D. WHERE THE FRICTION MAY BE (V6 - always visible) ===== */}
        {frictionText ? (
          <View style={[styles.frictionSection, { borderColor: theme.border }]}>
            <Text style={[styles.frictionLabel, { color: theme.textTertiary }]}>
              WHERE THE FRICTION MAY BE
            </Text>
            <Text style={[styles.frictionText, { color: theme.textSecondary }]}>
              {frictionText}
            </Text>
          </View>
        ) : null}

        {/* ===== E. WHAT TO DO WITH IT (V6 - always visible) ===== */}
        {practicalText ? (
          <View style={[styles.practicalSection, { borderColor: theme.border }]}>
            <Text style={[styles.practicalLabel, { color: theme.textTertiary }]}>
              WHAT TO DO WITH IT
            </Text>
            <Text style={[styles.practicalText, { color: theme.text }]}>
              {practicalText}
            </Text>
          </View>
        ) : null}

        {/* ===== Unified Insight Card Footer (Resonate + Reflect) ===== */}
        <InsightCardFooter
          source={{
            lens: 'patterns',
            type: 'pattern_card',
            name: coreInsight?.title || pattern.title,
            value: coreInsight?.text || pattern.what_you_may_be,
            id: `pattern_${patternData.pattern_id || 'main'}`,
          }}
          patternSignature={`pattern_${patternData.pattern_id || 'main'}`}
          context="patterns_home"
          prompt={coreInsight?.text || pattern.what_you_may_be}
          showBorder={true}
          borderColor={theme.border}
        />

        {/* V6 Three-Layer mode: NO challenge/genius blocks, NO signals indicator */}
        {/* Friction and Practical are lightweight usefulness layers, not legacy blocks */}
      </View>
    );
  }

  // ===== LEGACY RENDER (V4/V3/V2 fallback) =====
  // This should NOT be used when two_layer_output is available!

  return (
    <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerLabel, { color: theme.textTertiary }]}>PATTERN</Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          What may be happening right now
        </Text>
      </View>

      {/* V4: Title from daily_angle (primary) or fallback */}
      <Text style={[styles.patternTitle, { color: theme.text }]}>
        {dailyAngle?.angle_title || personalPattern?.selected_pattern_title || pattern.title}
      </Text>

      {/* V4: Daily angle narrative */}
      {dailyAngle?.angle_summary ? (
        <View style={styles.section}>
          {/* Main explanation from daily angle */}
          <Text style={[styles.unifiedNarrative, { color: theme.text }]}>
            {dailyAngle.angle_summary}
          </Text>
          
          {/* Core connection subline */}
          {coreMemory?.title && dailyAngle.derived_from_core_pattern && (
            <Text style={[styles.coreConnection, { color: theme.textSecondary }]}>
              This seems connected to a broader pattern of {coreMemory.title.toLowerCase()}.
            </Text>
          )}
          
          {/* Timing note - SECONDARY */}
          {isAmplifierMode && (narrative?.timing_note || timingAmplifier?.timing_summary) && (
            <Text style={[styles.timingNote, { color: theme.textSecondary }]}>
              {narrative?.timing_note || `This may feel stronger right now because ${timingAmplifier?.timing_summary?.toLowerCase() || 'of current timing'}.`}
            </Text>
          )}
        </View>
      ) : narrative?.main_explanation ? (
        /* V2/V3 fallback */
        <View style={styles.section}>
          <Text style={[styles.unifiedNarrative, { color: theme.text }]}>
            {narrative.main_explanation}
          </Text>
          {isAmplifierMode && narrative.timing_note && (
            <Text style={[styles.timingNote, { color: theme.textSecondary }]}>
              {narrative.timing_note}
            </Text>
          )}
        </View>
      ) : patternData.unified_narrative ? (
        /* Legacy fallback */
        <View style={styles.section}>
          <Text style={[styles.unifiedNarrative, { color: theme.text }]}>
            {patternData.unified_narrative}
          </Text>
        </View>
      ) : (
        <View style={styles.section}>
          <Text style={[styles.whatYouMayBe, { color: theme.text }]}>
            {pattern.what_you_may_be}
          </Text>
        </View>
      )}

      {/* V4: Timing Context - SECONDARY */}
      {timingAmplifier && timingAmplifier.active_timing_themes && timingAmplifier.active_timing_themes.length > 0 && (
        <View style={[styles.timingContextSecondary, { backgroundColor: theme.surfaceAlt || theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.timingContextTitleSecondary, { color: theme.textTertiary }]}>
            {isAmplifierMode ? 'WHY THIS MAY FEEL STRONGER RIGHT NOW' : 'CURRENT TIMING'}
          </Text>
          {timingAmplifier.timing_summary && (
            <Text style={[styles.timingContextText, { color: theme.textSecondary }]}>
              {timingAmplifier.timing_summary}
            </Text>
          )}
        </View>
      )}

      {/* Challenge - keep but collapsed by default */}
      <TouchableOpacity
        onPress={() => setDetailsExpanded(!detailsExpanded)}
        activeOpacity={0.7}
        style={styles.detailsTrigger}
      >
        <Text style={[styles.detailsTriggerText, { color: theme.textTertiary }]}>
          {detailsExpanded ? 'Hide details ▲' : 'Show challenge & genius ▼'}
        </Text>
      </TouchableOpacity>

      {detailsExpanded && (
        <>
          {/* Challenge */}
          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              WHAT'S YOUR CHALLENGE
            </Text>
            <View style={styles.challengeList}>
              {pattern.challenge.map((item, index) => (
                <View key={index} style={styles.challengeItem}>
                  <Text style={[styles.bulletPoint, { color: theme.textTertiary }]}>•</Text>
                  <Text style={[styles.challengeText, { color: theme.textSecondary }]}>
                    {item}
                  </Text>
                </View>
              ))}
            </View>
          </View>

          {/* Genius */}
          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              WHAT'S YOUR GENIUS
            </Text>
            <Text style={[styles.geniusDescription, { color: theme.text }]}>
              {pattern.genius.description}
            </Text>
            {pattern.genius.archetype && (
              <Text style={[styles.archetype, { color: theme.accent }]}>
                {pattern.genius.archetype}
              </Text>
            )}
          </View>

          {/* Micro Shifts */}
          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
              PRACTICAL WAYS TO THINK ABOUT IT
            </Text>
            {pattern.micro_shifts.map((shift, index) => (
              <Text key={index} style={[styles.microShift, { color: theme.textSecondary }]}>
                {shift}
              </Text>
            ))}
          </View>
        </>
      )}

      {/* Unified Insight Card Footer (Resonate + Reflect) */}
      <InsightCardFooter
        source={{
          lens: 'patterns',
          type: 'pattern_card_legacy',
          name: dailyAngle?.angle_title || personalPattern?.selected_pattern_title || pattern.title,
          value: pattern.what_you_may_be,
          id: `pattern_legacy_${patternData.pattern_id || 'main'}`,
        }}
        patternSignature={`pattern_legacy_${patternData.pattern_id || 'main'}`}
        context="patterns_home"
        prompt={pattern.what_you_may_be}
        showBorder={true}
        borderColor={theme.border}
      />

      {/* V4: Signal strength indicator with clustered evidence counts */}
      {(evidencePanel || personalPattern?.signal_strength || patternData.signal_strength) && (
        <TouchableOpacity
          onPress={() => setSignalsExpanded(!signalsExpanded)}
          activeOpacity={0.7}
          style={styles.signalTrigger}
        >
          <Text style={[styles.signalIndicator, { color: theme.textTertiary }]}>
            {evidencePanel ? (
              // V4: Show clustered evidence summary
              `${evidencePanel.total_snippet_count} signals across ${
                Object.keys(evidencePanel.snippet_count_by_source || {}).join(' and ')
              }`
            ) : (
              // Fallback
              `Based on ${personalPattern?.signal_strength || patternData.signal_strength} signals`
            )}
            <Text style={styles.signalExpandHint}>
              {signalsExpanded ? '  ▲' : '  ▼'}
            </Text>
          </Text>
        </TouchableOpacity>
      )}

      {/* V4: CLUSTERED EVIDENCE PANEL */}
      {signalsExpanded && (
        <View style={[styles.signalsSection, { borderTopColor: theme.border }]}>
          <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>
            WHAT THIS IS BASED ON
          </Text>
          
          {/* V4: Evidence summary line */}
          {evidencePanel?.summary_line && (
            <Text style={[styles.evidenceSummaryLine, { color: theme.textSecondary }]}>
              {evidencePanel.summary_line}
            </Text>
          )}
          
          {/* V4: Render grouped evidence from source_sections */}
          {evidencePanel?.source_sections?.map((section: any) => {
            if (!section.sample_snippets || section.sample_snippets.length === 0) return null;
            
            return (
              <View key={section.source_name} style={styles.signalSourceGroup}>
                <View style={styles.sourceHeader}>
                  <Text style={[styles.signalSourceLabel, { color: theme.textSecondary }]}>
                    {SOURCE_LABELS[section.source_name] || section.source_name} ({section.snippet_count})
                  </Text>
                  <Text style={[styles.contributionBadge, { color: theme.textTertiary }]}>
                    {section.contribution_strength}
                  </Text>
                </View>
                {section.sample_snippets.slice(0, 3).map((snippet: any, index: number) => (
                  <View key={index} style={styles.evidenceItem}>
                    <Text style={[styles.signalBullet, { color: theme.textTertiary }]}>•</Text>
                    <View style={styles.evidenceContent}>
                      <Text style={[styles.signalText, { color: theme.textSecondary }]}>
                        {snippet.text}
                      </Text>
                      {snippet.date && (
                        <Text style={[styles.snippetDate, { color: theme.textTertiary }]}>
                          {snippet.date}
                        </Text>
                      )}
                    </View>
                  </View>
                ))}
                {section.snippet_count > 3 && (
                  <Text style={[styles.moreSnippets, { color: theme.textTertiary }]}>
                    +{section.snippet_count - 3} more
                  </Text>
                )}
              </View>
            );
          })}
          
          {/* Fallback to V2 evidence if no V4 */}
          {!evidencePanel?.source_sections && evidence?.matched_evidence && Object.entries(evidence.matched_evidence).map(([source, matches]) => {
            if (!matches || matches.length === 0) return null;
            if (source === 'timing') return null;
            
            return (
              <View key={source} style={styles.signalSourceGroup}>
                <View style={styles.sourceHeader}>
                  <Text style={[styles.signalSourceLabel, { color: theme.textSecondary }]}>
                    {SOURCE_LABELS[source] || source}
                  </Text>
                </View>
                {(matches as EvidenceMatch[]).map((match, index) => (
                  <View key={index} style={styles.evidenceItem}>
                    <Text style={[styles.signalBullet, { color: theme.textTertiary }]}>•</Text>
                    <View style={styles.evidenceContent}>
                      <Text style={[styles.signalText, { color: theme.textSecondary }]}>
                        {match.text}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 20,
    marginVertical: 12,
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
  },
  
  // Loading state
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  
  // Empty state
  emptyContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Header
  header: {
    marginBottom: 16,
  },
  headerLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  
  // Pattern title
  patternTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 20,
  },
  
  // Sections
  section: {
    marginBottom: 20,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  
  // What you may be
  whatYouMayBe: {
    fontSize: 16,
    lineHeight: 32,
  },
  
  // Challenge
  challengeList: {
    gap: 6,
  },
  challengeItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  bulletPoint: {
    fontSize: 16,
    marginRight: 8,
    marginTop: 2,
  },
  challengeText: {
    fontSize: 16,
    lineHeight: 32,
    flex: 1,
  },
  
  // Genius
  geniusDescription: {
    fontSize: 17,
    lineHeight: 30,
    marginBottom: 14,
  },
  archetype: {
    fontSize: 16,
    fontWeight: '600',
    fontStyle: 'italic',
  },
  
  // Micro shifts
  microShift: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
    marginBottom: 6,
  },
  
  // Timing Context (What's active right now)
  timingContext: {
    marginBottom: 20,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  timingContextTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  timingContextItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 5,
  },
  timingBullet: {
    fontSize: 14,
    marginRight: 6,
    marginTop: 2,
  },
  timingContextText: {
    fontSize: 14,
    lineHeight: 17,
    flex: 1,
    fontStyle: 'italic',
  },
  
  // CTA Button
  reflectButton: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  reflectButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  
  // Signal indicator with tap to expand
  signalTrigger: {
    marginTop: 16,
    alignItems: 'center',
  },
  signalIndicator: {
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  signalExpandHint: {
    fontSize: 14,
  },
  
  // Collapsible signals section
  signalsSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
  },
  signalsSectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 16,
  },
  signalSourceGroup: {
    marginBottom: 16,
  },
  signalSourceLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 14,
  },
  signalItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
    paddingLeft: 4,
  },
  signalBullet: {
    fontSize: 14,
    marginRight: 8,
    marginTop: 1,
  },
  signalText: {
    fontSize: 16,
    lineHeight: 32,
    flex: 1,
  },
  
  // V2: Timing note (secondary)
  timingNote: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
    marginTop: 16,
    paddingLeft: 12,
    borderLeftWidth: 2,
    borderLeftColor: 'rgba(128, 128, 128, 0.3)',
  },
  
  // V2: Evidence summary
  evidenceSummary: {
    fontSize: 14,
    marginTop: 12,
    fontStyle: 'italic',
  },
  
  // V2: Secondary timing context (downgraded)
  timingContextSecondary: {
    marginTop: 16,
    marginBottom: 14,
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    opacity: 0.8,
  },
  timingContextTitleSecondary: {
    fontSize: 8,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  
  // V2: Signal source hint
  signalSourceHint: {
    fontSize: 14,
    fontStyle: 'normal',
  },
  
  // V2: Source header with badge
  sourceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
    gap: 8,
  },
  primaryBadge: {
    fontSize: 9,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  
  // V2: Evidence item with keyword info
  evidenceItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
    paddingLeft: 4,
  },
  evidenceContent: {
    flex: 1,
  },
  matchedKeyword: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 2,
  },
  
  // V2: Total matches summary
  totalMatches: {
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
  
  // V4: Core connection subline
  coreConnection: {
    fontSize: 16,
    lineHeight: 32,
    marginTop: 12,
    fontStyle: 'italic',
  },
  
  // V4: Evidence summary line
  evidenceSummaryLine: {
    fontSize: 14,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  
  // V4: Contribution badge
  contributionBadge: {
    fontSize: 9,
    fontWeight: '500',
    textTransform: 'uppercase',
  },
  
  // V4: Snippet date
  snippetDate: {
    fontSize: 14,
    marginTop: 2,
  },
  
  // V4: More snippets indicator
  moreSnippets: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 4,
    paddingLeft: 16,
  },
  
  // ===== V5 TWO-LAYER OUTPUT STYLES =====
  
  // Core insight text (the one sharp sentence)
  coreInsightText: {
    fontSize: 17,
    lineHeight: 30,
    fontWeight: '500',
  },
  
  // Why showing up section
  whyShowingUpSection: {
    marginTop: 16,
    marginBottom: 16,
    paddingTop: 16,
    paddingBottom: 4,
    borderTopWidth: 1,
  },
  whyShowingUpLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  whyShowingUpText: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
  },
  
  // Derivation section (collapsible cross-lens proof)
  derivationContainer: {
    marginTop: 8,
    marginBottom: 16,
  },
  derivationTrigger: {
    paddingVertical: 14,
    paddingHorizontal: 4,
  },
  derivationTriggerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  derivationTriggerText: {
    fontSize: 16,
    fontWeight: '500',
  },
  derivationArrow: {
    fontSize: 14,
    marginLeft: 8,
  },
  convergenceBadge: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 6,
    textAlign: 'center',
  },
  derivationSection: {
    paddingTop: 16,
    borderTopWidth: 1,
    marginTop: 8,
  },
  lensItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
    paddingHorizontal: 4,
  },
  lensName: {
    fontSize: 16,
    fontWeight: '600',
    width: 100,
  },
  lensArrow: {
    fontSize: 16,
    marginHorizontal: 8,
    marginTop: 1,
  },
  lensSignal: {
    fontSize: 16,
    lineHeight: 32,
    flex: 1,
  },
  
  // ===== V6 USEFULNESS LAYER STYLES =====
  
  // Friction section (where the tension may be)
  frictionSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
  },
  frictionLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  frictionText: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
  },
  
  // Practical section (what to do with it)
  practicalSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    marginBottom: 14,
  },
  practicalLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  practicalText: {
    fontSize: 16,
    lineHeight: 30,
    fontWeight: '500',
  },
  
  // V7: Astrology drivers display
  lensItemWithDrivers: {
    marginBottom: 14,
    paddingHorizontal: 4,
  },
  driversContainer: {
    marginTop: 4,
    marginLeft: 100, // Align with other lens signals
  },
  driverItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 6,
  },
  driverText: {
    fontSize: 16,
    lineHeight: 32,
    flex: 1,
    marginLeft: 4,
  },
});
