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
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, LayoutAnimation, Platform, UIManager } from 'react-native';
import { useRouter } from 'expo-router';
import { getPatternDiagnosis, PatternDiagnosisResponse } from '../services/api';
import { useExperienceControls } from '../hooks/useExperienceControls';

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

  // Navigate to full diagnosis page
  const handleSeeFullDiagnosis = () => {
    router.push('/signals');
  };

  // ============================================================
  // MODE-BASED CONTENT FUNCTIONS
  // ============================================================

  // Get "what is happening" text - truncated for grounding mode
  const getWhatIsHappening = (): string => {
    if (!diagnosis?.what_is_happening) return '';
    
    const text = diagnosis.what_is_happening;
    
    if (mode === 'grounding') {
      // Truncate to first sentence for grounding mode
      const firstSentence = text.split(/[.!?]/)[0];
      return firstSentence ? firstSentence + '.' : text;
    }
    
    return text;
  };

  // Get "what would be wise" text - truncated for grounding mode
  const getWhatWouldBeWise = (): string => {
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

  // Get CTA text based on MODE and diagnosis
  const getCtaText = (): string => {
    // Derive CTA from moment type when possible
    if (diagnosis?.moment_type) {
      const momentCtas: Record<string, Record<string, string>> = {
        premature_initiation: {
          grounding: 'Breathe first',
          exploratory: 'Explore what is not ready',
          directive: 'Name what is blocking',
        },
        pause_stall: {
          grounding: 'Rest here',
          exploratory: 'Explore the pause',
          directive: 'Name the block',
        },
        threshold_moment: {
          grounding: 'Notice without acting',
          exploratory: 'Explore the threshold',
          directive: 'Decide one thing',
        },
        overreach_risk: {
          grounding: 'Let it be',
          exploratory: 'Explore the risk',
          directive: 'Identify what to release',
        },
        unresolved_wave: {
          grounding: 'Wait for neutral',
          exploratory: 'Feel the wave',
          directive: 'Wait for clarity',
        },
        structure_not_ready: {
          grounding: 'Build slowly',
          exploratory: 'Explore the foundation',
          directive: 'Strengthen one thing',
        },
        clean_initiation: {
          grounding: 'Move gently',
          exploratory: 'Explore the opening',
          directive: 'Take one step',
        },
        consolidation: {
          grounding: 'Rest and build',
          exploratory: 'Explore what is forming',
          directive: 'Strengthen foundation',
        },
        forcing_window: {
          grounding: 'Ride gently',
          exploratory: 'Explore the momentum',
          directive: 'Act now',
        },
        review_recalibration: {
          grounding: 'Reflect softly',
          exploratory: 'Review what is true',
          directive: 'Clarify one thing',
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
      {/* Opener */}
      <Text style={[styles.label, { color: theme.textTertiary }]}>
        {getOpenerText()}
      </Text>
      
      {/* Pattern Title */}
      <Text style={[styles.title, { color: theme.text }]}>
        {diagnosis.pattern_title}
      </Text>
      
      {/* CORE DIAGNOSIS: What is happening */}
      <View style={styles.diagnosisSection}>
        <Text style={[styles.diagnosisText, { color: theme.text }]}>
          {getWhatIsHappening()}
        </Text>
      </View>
      
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
});
