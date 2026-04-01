/**
 * TodayPatternCard - DIAGNOSIS-FIRST
 * 
 * Home screen keystone - Cross-Lens Synthesis
 * 
 * NEW STRUCTURE (replaces signal-summary approach):
 * 1. Pattern title
 * 2. DIAGNOSIS: What is happening
 * 3. GUIDANCE: What would be wise
 * 4. Supporting evidence (collapsed)
 * 5. CTA derived from diagnosis
 * 
 * MODE still controls verbosity, but ALL modes use diagnosis-first:
 * - GROUNDING: Shorter diagnosis, less evidence
 * - EXPLORATORY: Full diagnosis, rich evidence
 * - DIRECTIVE: Clear diagnosis, action-focused
 * 
 * V3.1: ANGLE SYSTEM - Prefers full_diagnosis.home fields when available
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, LayoutAnimation, Platform, UIManager } from 'react-native';
import { useRouter } from 'expo-router';
import { getPatternDiagnosis, PatternDiagnosisResponse, HomeInsightData, FullDiagnosisWithHome } from '../services/api';
import { useExperienceControls } from '../hooks/useExperienceControls';
import { useAdaptationCues, logAdaptationCues, AdaptationResponse } from '../hooks/useAdaptationCues';
import { trackHomeChatTap, updateTrackingContext } from '../services/actionTracking';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface TodayPatternCardProps {
  userId: string;
  theme: any;
  onReflect?: () => void;
}

export default function TodayPatternCard({ userId, theme, onReflect }: TodayPatternCardProps) {
  const router = useRouter();
  const [diagnosis, setDiagnosis] = useState<PatternDiagnosisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Experience controls for personalization - MODE is the primary driver
  const { mode, modeConfig } = useExperienceControls();
  
  // Expander state for supporting evidence
  const [isExpanded, setIsExpanded] = useState(false);
  
  // INTERACTION LOOP STATE (FIX 2)
  const [interactionStep, setInteractionStep] = useState<'initial' | 'yes_followup' | 'no_followup' | 'complete'>('initial');
  const [interactionResponse, setInteractionResponse] = useState<string | null>(null);
  
  // ADAPTATION CUES - Subtle visual changes based on engagement
  const adaptationResponse: AdaptationResponse = {
    adaptation_mode: diagnosis?.full_diagnosis?.home?.adaptation_mode || null,
    first_line_source: diagnosis?.full_diagnosis?.home?.first_line_source || null,
    behavior_snap: diagnosis?.full_diagnosis?.home?.behavior_snap || null,
    engagement_state: diagnosis?.full_diagnosis?.home?.engagement_state || null,
  };
  const adaptationCues = useAdaptationCues(adaptationResponse);
  
  // Log adaptation cues in dev
  useEffect(() => {
    if (diagnosis && adaptationCues) {
      logAdaptationCues(adaptationCues);
      
      // Update tracking context with current pattern info
      updateTrackingContext({
        patternShown: diagnosis.pattern_id,
        behaviorSnapShown: adaptationResponse.behavior_snap || undefined,
        lifeArenaShown: diagnosis?.full_diagnosis?.home?.life_arena || undefined,
      });
    }
  }, [diagnosis, adaptationCues]);

  useEffect(() => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    const fetchDiagnosis = async () => {
      try {
        setIsLoading(true);
        const response = await getPatternDiagnosis(userId);
        setDiagnosis(response);
        setError(null);
      } catch (err) {
        console.error('[TodayPatternCard] Error:', err);
        setError('Could not load diagnosis');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDiagnosis();
  }, [userId]);

  // Re-fetch diagnosis (for re-engagement)
  const handleRefetchDiagnosis = async () => {
    setInteractionStep('initial');
    setInteractionResponse(null);
    try {
      setIsLoading(true);
      const response = await getPatternDiagnosis(userId);
      setDiagnosis(response);
      setError(null);
    } catch (err) {
      console.error('[TodayPatternCard] Refetch Error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReflect = () => {
    if (onReflect) {
      onReflect();
    } else {
      router.push('/(tabs)/reflect?view=mirror');
    }
  };

  // Toggle expander for supporting evidence
  const handleExpandToggle = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIsExpanded(!isExpanded);
  };

  // Navigate to reflection with prefill (FIX 3)
  const handleMicroReflection = () => {
    router.push({
      pathname: '/reflection-chat',
      params: { prefill: "I'm noticing a pattern where I..." }
    });
  };

  // Navigate to full diagnosis page
  const handleSeeFullDiagnosis = () => {
    router.push('/signals');
  };

  // ============================================================
  // V3.1: HELPER - Extract home insight data from full_diagnosis
  // ============================================================
  const getHomeInsight = (): HomeInsightData | null => {
    if (!diagnosis?.full_diagnosis) return null;
    
    // Check if full_diagnosis is the new object format with home data
    if (typeof diagnosis.full_diagnosis === 'object' && diagnosis.full_diagnosis !== null) {
      const fd = diagnosis.full_diagnosis as FullDiagnosisWithHome;
      return fd.home || null;
    }
    
    return null;
  };

  // V3.1: Log angle debug info on render
  useEffect(() => {
    if (diagnosis) {
      const homeInsight = getHomeInsight();
      console.log('[TodayPatternCard] V3.1 ANGLE DEBUG:', {
        pattern_title: diagnosis.pattern_title,
        legacy_body: diagnosis.what_is_happening?.substring(0, 80) + '...',
        full_home_title: homeInsight?.title,
        full_home_body: homeInsight?.body?.substring(0, 80) + '...',
        full_home_bridge: homeInsight?.bridge,
        angle_id: homeInsight?.debug?.angle_system?.angle_id,
        angle_label: homeInsight?.debug?.angle_system?.angle_label,
        is_repeated_pattern: homeInsight?.debug?.angle_system?.is_repeated_pattern,
        card_version: homeInsight?.card_version,
      });
    }
  }, [diagnosis]);

  // ============================================================
  // MODE-BASED CONTENT FUNCTIONS
  // ============================================================

  // Get pattern title - uses exposure_copy headline if available (evolved messaging)
  // V3.1: Prefers full_diagnosis.home.title for angle-specific content
  const getPatternTitle = (): string => {
    // V3.1: PREFER angle-specific title from home insight
    const homeInsight = getHomeInsight();
    if (homeInsight?.title) {
      return homeInsight.title;
    }
    
    // Use exposure-aware headline if available
    if (diagnosis?.exposure_copy?.headline) {
      return diagnosis.exposure_copy.headline;
    }
    return diagnosis?.pattern_title || 'Pattern Active';
  };

  // Get "what is happening" text - uses exposure_copy opening if available
  // V3.1: Prefers full_diagnosis.home.body for angle-specific content
  const getWhatIsHappening = (): string => {
    // V3.1: PREFER angle-specific body from home insight
    const homeInsight = getHomeInsight();
    if (homeInsight?.body) {
      const text = homeInsight.body;
      if (mode === 'grounding') {
        const firstSentence = text.split(/[.!?]/)[0];
        return firstSentence ? firstSentence + '.' : text;
      }
      return text;
    }
    
    // Prioritize exposure-aware opening for evolved messaging
    if (diagnosis?.exposure_copy?.opening) {
      const text = diagnosis.exposure_copy.opening;
      if (mode === 'grounding') {
        const firstSentence = text.split(/[.!?]/)[0];
        return firstSentence ? firstSentence + '.' : text;
      }
      return text;
    }
    
    if (!diagnosis?.what_is_happening) return '';
    
    const text = diagnosis.what_is_happening;
    
    if (mode === 'grounding') {
      // Truncate to first sentence for grounding mode
      const firstSentence = text.split(/[.!?]/)[0];
      return firstSentence ? firstSentence + '.' : text;
    }
    
    return text;
  };

  // Get bridge text - V3.1: NEW - uses home insight bridge
  const getBridgeText = (): string => {
    const homeInsight = getHomeInsight();
    if (homeInsight?.bridge) {
      return homeInsight.bridge;
    }
    // Fallback to why_it_is_happening or empty
    return diagnosis?.why_it_is_happening || '';
  };

  // Get reflection prompt - uses exposure_copy if available
  const getReflectionPrompt = (): string => {
    if (diagnosis?.exposure_copy?.reflection_prompt) {
      return diagnosis.exposure_copy.reflection_prompt;
    }
    return "Does this feel true right now?";
  };

  // Get "what would be wise" text - truncated for grounding mode
  // V3.1: Prefers full_diagnosis.home.better_move for angle-specific action
  const getWhatWouldBeWise = (): string => {
    // V3.1: PREFER angle-specific action from home insight
    const homeInsight = getHomeInsight();
    if (homeInsight?.better_move) {
      const text = homeInsight.better_move;
      if (mode === 'grounding') {
        const firstSentence = text.split(/[.!?]/)[0];
        return firstSentence ? firstSentence + '.' : text;
      }
      return text;
    }
    
    if (!diagnosis?.what_would_be_wise) return '';
    
    const text = diagnosis.what_would_be_wise;
    
    if (mode === 'grounding') {
      // Truncate to first sentence
      const firstSentence = text.split(/[.!?]/)[0];
      return firstSentence ? firstSentence + '.' : text;
    }
    
    if (mode === 'directive') {
      // Keep full for directive - they want clarity
      return text;
    }
    
    return text;
  };

  // Get CTA text based on MODE and diagnosis (Scene-specific language)
  const getCtaText = (): string => {
    // Derive CTA from moment type when possible
    if (diagnosis?.moment_type) {
      const momentCtas: Record<string, Record<string, string>> = {
        premature_initiation: {
          grounding: 'Breathe first',
          exploratory: 'See what\'s not ready',
          directive: 'Name the unresolved part',
        },
        pause_stall: {
          grounding: 'Rest here',
          exploratory: 'See what\'s stuck',
          directive: 'Name what hasn\'t landed',
        },
        threshold_moment: {
          grounding: 'Notice without acting',
          exploratory: 'See both sides',
          directive: 'Name what you\'re leaving',
        },
        overreach_risk: {
          grounding: 'Let it be',
          exploratory: 'See the grip',
          directive: 'Release one thing',
        },
        unresolved_wave: {
          grounding: 'Wait for neutral',
          exploratory: 'Feel the wave',
          directive: 'Wait for clarity',
        },
        structure_not_ready: {
          grounding: 'Build slowly',
          exploratory: 'See what\'s missing',
          directive: 'Build one thing',
        },
        clean_initiation: {
          grounding: 'Move gently',
          exploratory: 'See the opening',
          directive: 'Take one step',
        },
        consolidation: {
          grounding: 'Rest and build',
          exploratory: 'See what\'s forming',
          directive: 'Strengthen one thing',
        },
        forcing_window: {
          grounding: 'Ride gently',
          exploratory: 'See the momentum',
          directive: 'Name the direction',
        },
        review_recalibration: {
          grounding: 'Reflect softly',
          exploratory: 'See what\'s true',
          directive: 'Question one thing',
        },
      };
      
      const momentType = diagnosis.moment_type;
      if (momentCtas[momentType] && momentCtas[momentType][mode]) {
        return momentCtas[momentType][mode];
      }
    }
    
    // Fallback to mode config CTA
    return modeConfig.ctaText;
  };

  // Get opener text based on MODE
  const getOpenerText = (): string => {
    if (mode === 'grounding') return 'TODAY';
    if (mode === 'directive') return 'TODAY\'S DIAGNOSIS';
    return 'WHAT MIRROR SEES TODAY';
  };

  // Should show "what kind of moment" line
  const shouldShowMomentType = (): boolean => {
    return mode !== 'grounding' && !!diagnosis?.what_kind_of_moment;
  };

  // Format evidence for display
  const getEvidenceItems = () => {
    if (!diagnosis?.evidence) return [];
    
    const items: { label: string; text: string }[] = [];
    
    if (diagnosis.evidence.timing) {
      items.push({
        label: 'TIMING',
        text: diagnosis.evidence.timing.summary,
      });
    }
    
    if (diagnosis.evidence.design) {
      items.push({
        label: 'YOUR DESIGN',
        text: diagnosis.evidence.design.summary,
      });
    }
    
    if (diagnosis.evidence.history) {
      items.push({
        label: 'PATTERN HISTORY',
        text: diagnosis.evidence.history.summary,
      });
    }
    
    // Limit based on mode
    if (mode === 'grounding') return items.slice(0, 1);
    if (mode === 'directive') return items.slice(0, 2);
    return items;
  };

  // Don't render if loading
  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Building diagnosis...
          </Text>
        </View>
      </View>
    );
  }

  // Don't render if no diagnosis
  if (!diagnosis) {
    return null;
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      
      {/* FIX 1: PRIMARY PATTERN ENTRY BUTTON */}
      <TouchableOpacity
        style={[styles.primaryEntryButton, { backgroundColor: theme.accent }]}
        onPress={handleRefetchDiagnosis}
        activeOpacity={0.8}
      >
        <Text style={[styles.primaryEntryText, { color: theme.textInverse }]}>
          What pattern is running me right now?
        </Text>
      </TouchableOpacity>
      
      {/* Opener */}
      <Text style={[styles.label, { color: theme.textTertiary, marginTop: 16 }]}>
        {getOpenerText()}
      </Text>
      
      {/* Pattern Title - uses exposure_copy headline for evolved messaging */}
      <Text style={[styles.title, { color: theme.text }]}>
        {getPatternTitle()}
      </Text>
      
      {/* CORE DIAGNOSIS: What is happening - uses exposure_copy opening for evolved messaging */}
      {/* V3.1: Now prefers full_diagnosis.home.body for angle-specific content */}
      <View style={styles.diagnosisSection}>
        <Text style={[styles.diagnosisText, { color: theme.text }]}>
          {getWhatIsHappening()}
        </Text>
      </View>
      
      {/* V3.1: BRIDGE TEXT - Gray callout with angle-specific bridge */}
      {getBridgeText() && (
        <View style={[styles.bridgeContainer, { backgroundColor: theme.cardBackground, borderLeftColor: theme.accent + '40' }]}>
          <Text style={[styles.bridgeText, { color: theme.textSecondary }]}>
            {getBridgeText()}
          </Text>
        </View>
      )}
      
      {/* V1: Pattern Memory Line (only if validated/earned) */}
      {diagnosis.memory && diagnosis.memory.memory_line && (
        <View style={styles.memoryLineContainer}>
          <Text style={[styles.memoryLineText, { color: theme.textTertiary }]}>
            {diagnosis.memory.memory_line}
          </Text>
        </View>
      )}
      
      {/* FIX 2: INTERACTION LOOP - uses exposure_copy reflection_prompt */}
      {interactionStep === 'initial' && (
        <View style={[styles.interactionBox, { backgroundColor: theme.background, borderColor: theme.border }]}>
          <Text style={[styles.interactionQuestion, { color: theme.text }]}>
            {getReflectionPrompt()}
          </Text>
          <View style={styles.interactionButtonsRow}>
            <TouchableOpacity
              style={[styles.interactionBtn, { backgroundColor: theme.accent + '15', borderColor: theme.accent + '30' }]}
              onPress={() => setInteractionStep('yes_followup')}
            >
              <Text style={[styles.interactionBtnText, { color: theme.accent }]}>Yes</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.interactionBtn, { backgroundColor: theme.border + '30', borderColor: theme.border }]}
              onPress={() => setInteractionStep('no_followup')}
            >
              <Text style={[styles.interactionBtnText, { color: theme.textSecondary }]}>Not really</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
      
      {/* YES FOLLOW-UP */}
      {interactionStep === 'yes_followup' && (
        <View style={[styles.interactionBox, { backgroundColor: theme.background, borderColor: theme.accent + '30' }]}>
          <Text style={[styles.interactionQuestion, { color: theme.text }]}>
            Where do you feel this most right now?
          </Text>
          <View style={styles.interactionOptionsCol}>
            {['Work', 'Relationships', 'Internal / Mental', 'Something else'].map((option) => (
              <TouchableOpacity
                key={option}
                style={[styles.interactionOption, { borderColor: theme.border }]}
                onPress={() => { setInteractionResponse(option); setInteractionStep('complete'); }}
              >
                <Text style={[styles.interactionOptionText, { color: theme.text }]}>{option}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
      
      {/* NO FOLLOW-UP */}
      {interactionStep === 'no_followup' && (
        <View style={[styles.interactionBox, { backgroundColor: theme.background, borderColor: theme.border }]}>
          <Text style={[styles.interactionQuestion, { color: theme.text }]}>
            What feels more true?
          </Text>
          <View style={styles.interactionOptionsCol}>
            {["I'm stuck in something else", "This doesn't apply", "Not sure yet"].map((option) => (
              <TouchableOpacity
                key={option}
                style={[styles.interactionOption, { borderColor: theme.border }]}
                onPress={() => { setInteractionResponse(option); setInteractionStep('complete'); }}
              >
                <Text style={[styles.interactionOptionText, { color: theme.text }]}>{option}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
      
      {/* FIX 3: MICRO-REFLECTION TRIGGER (after interaction complete) */}
      {interactionStep === 'complete' && (
        <View style={[styles.interactionBox, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.interactionAck, { color: theme.textSecondary }]}>
            {interactionResponse}
          </Text>
          <TouchableOpacity
            style={[styles.microReflectButton, { backgroundColor: theme.accent }]}
            onPress={handleMicroReflection}
          >
            <Text style={[styles.microReflectText, { color: theme.textInverse }]}>
              Name what is actually happening
            </Text>
          </TouchableOpacity>
        </View>
      )}
      
      {/* MOMENT TYPE: What kind of moment (not in grounding) */}
      {shouldShowMomentType() && (
        <View style={[styles.momentBadge, { backgroundColor: theme.accent + '12', borderColor: theme.accent + '25' }]}>
          <Text style={[styles.momentText, { color: theme.text }]}>
            {diagnosis.what_kind_of_moment}
          </Text>
        </View>
      )}
      
      {/* GUIDANCE: What would be wise */}
      <View style={styles.wisdomSection}>
        <Text style={[styles.wisdomLabel, { color: theme.textTertiary }]}>
          {mode === 'grounding' ? 'FOR NOW' : 'WHAT WOULD BE WISE'}
        </Text>
        <Text style={[styles.wisdomText, { color: theme.textSecondary }]}>
          {getWhatWouldBeWise()}
        </Text>
      </View>
      
      {/* Supporting Evidence Expander */}
      <TouchableOpacity
        style={[styles.expanderToggle, { borderTopColor: theme.border }]}
        onPress={handleExpandToggle}
        activeOpacity={0.7}
      >
        <Text style={[styles.expanderToggleText, { color: theme.textSecondary }]}>
          {isExpanded ? 'Hide supporting evidence' : 'Why this is showing up'}
        </Text>
        <Text style={[styles.expanderArrow, { color: theme.textTertiary }]}>
          {isExpanded ? '▲' : '▼'}
        </Text>
      </TouchableOpacity>
      
      {/* Expanded Evidence Section */}
      {isExpanded && (
        <View style={styles.expandedContent}>
          {getEvidenceItems().length > 0 ? (
            <>
              {getEvidenceItems().map((item, index) => (
                <View 
                  key={index} 
                  style={[styles.evidenceItem, { borderLeftColor: theme.accent + '50' }]}
                >
                  <Text style={[styles.evidenceLabel, { color: theme.textTertiary }]}>
                    {item.label}
                  </Text>
                  <Text style={[styles.evidenceText, { color: theme.textSecondary }]}>
                    {item.text}
                  </Text>
                </View>
              ))}
              
              {/* See full diagnosis link */}
              <TouchableOpacity
                style={styles.seeAllLink}
                onPress={handleSeeFullDiagnosis}
                activeOpacity={0.7}
              >
                <Text style={[styles.seeAllText, { color: theme.accent }]}>
                  See full diagnosis →
                </Text>
              </TouchableOpacity>
            </>
          ) : (
            <Text style={[styles.noEvidenceText, { color: theme.textTertiary }]}>
              Complete your profile to see deeper connections.
            </Text>
          )}
        </View>
      )}
      
      {/* Divider */}
      <View style={[styles.divider, { backgroundColor: theme.border }]} />
      
      {/* CTA - derived from diagnosis */}
      <TouchableOpacity
        style={styles.ctaContainer}
        onPress={handleReflect}
        activeOpacity={0.7}
      >
        <Text style={[styles.ctaText, { color: theme.text }]}>{getCtaText()}</Text>
        <Text style={[styles.ctaArrow, { color: theme.textTertiary }]}>→</Text>
      </TouchableOpacity>
      
      {/* FIX 7: WORK WITH THIS PATTERN - ALWAYS PRESENT */}
      <View style={[styles.workWithPatternSection, { borderTopColor: theme.border }]}>
        <Text style={[styles.workWithPatternLabel, { color: theme.textTertiary }]}>
          WORK WITH THIS PATTERN
        </Text>
        <View style={styles.workWithPatternButtons}>
          <TouchableOpacity
            style={[styles.workWithBtn, { backgroundColor: theme.accent + '15' }]}
            onPress={handleReflect}
          >
            <Text style={[styles.workWithBtnText, { color: theme.accent }]}>Reflect</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.workWithBtn, { backgroundColor: theme.surface, borderColor: theme.border, borderWidth: 1 }]}
            onPress={handleMicroReflection}
          >
            <Text style={[styles.workWithBtnText, { color: theme.text }]}>Ask Mirror</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.workWithBtn, { backgroundColor: theme.background }]}
            onPress={() => setInteractionStep('initial')}
          >
            <Text style={[styles.workWithBtnText, { color: theme.textTertiary }]}>Reset</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  
  // FIX 1: Primary entry button
  primaryEntryButton: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryEntryText: {
    fontSize: 16,
    fontWeight: '600',
  },
  
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingVertical: 20,
  },
  loadingText: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 14,
    letterSpacing: -0.3,
  },
  
  // Diagnosis section
  diagnosisSection: {
    marginBottom: 14,
  },
  diagnosisText: {
    fontSize: 15,
    lineHeight: 23,
    fontWeight: '500',
  },
  
  // V1: Memory line (quiet, under the main flow)
  memoryLineContainer: {
    marginBottom: 12,
    paddingHorizontal: 4,
  },
  memoryLineText: {
    fontSize: 13,
    fontStyle: 'italic',
    fontWeight: '400',
  },
  
  // FIX 2: Interaction loop styles
  interactionBox: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 14,
    borderWidth: 1,
  },
  interactionQuestion: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
  },
  interactionButtonsRow: {
    flexDirection: 'row',
    gap: 12,
    justifyContent: 'center',
  },
  interactionBtn: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
    borderWidth: 1,
    minWidth: 100,
    alignItems: 'center',
  },
  interactionBtnText: {
    fontSize: 15,
    fontWeight: '600',
  },
  interactionOptionsCol: {
    gap: 8,
  },
  interactionOption: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
  },
  interactionOptionText: {
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  interactionAck: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 12,
    textAlign: 'center',
  },
  
  // FIX 3: Micro-reflection button
  microReflectButton: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  microReflectText: {
    fontSize: 15,
    fontWeight: '600',
  },
  
  // Moment type badge
  momentBadge: {
    borderRadius: 10,
    padding: 12,
    marginBottom: 14,
    borderWidth: 1,
  },
  momentText: {
    fontSize: 13,
    lineHeight: 20,
    fontWeight: '500',
  },
  
  // FIX 7: Work with pattern section
  workWithPatternSection: {
    borderTopWidth: 1,
    paddingTop: 14,
    marginTop: 8,
  },
  workWithPatternLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 10,
    textAlign: 'center',
  },
  workWithPatternButtons: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
  },
  workWithBtn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  workWithBtnText: {
    fontSize: 13,
    fontWeight: '600',
  },
  
  // Wisdom section
  wisdomSection: {
    marginBottom: 14,
  },
  wisdomLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  wisdomText: {
    fontSize: 14,
    lineHeight: 21,
  },
  
  // Expander
  expanderToggle: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
  },
  expanderToggleText: {
    fontSize: 13,
    fontWeight: '500',
  },
  expanderArrow: {
    fontSize: 10,
  },
  
  // Expanded content
  expandedContent: {
    paddingBottom: 8,
  },
  evidenceItem: {
    borderLeftWidth: 2,
    paddingLeft: 12,
    marginBottom: 12,
  },
  evidenceLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  evidenceText: {
    fontSize: 13,
    lineHeight: 19,
  },
  seeAllLink: {
    paddingVertical: 8,
    alignItems: 'center',
  },
  seeAllText: {
    fontSize: 13,
    fontWeight: '500',
  },
  noEvidenceText: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
    paddingVertical: 8,
  },
  
  // Divider
  divider: {
    height: 1,
    marginVertical: 12,
    opacity: 0.5,
  },
  
  // CTA
  ctaContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '600',
  },
  ctaArrow: {
    fontSize: 16,
    fontWeight: '400',
  },
  
  // V3.1: Bridge container (gray callout)
  bridgeContainer: {
    marginTop: 12,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderLeftWidth: 3,
    borderRadius: 4,
  },
  bridgeText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
});
