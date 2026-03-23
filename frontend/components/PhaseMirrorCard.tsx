/**
 * PhaseMirrorCard Component - V2 Pattern Detection Layer
 * 
 * Appears after saving a journal entry.
 * Mirror reflects, it does NOT declare.
 * Uses observational language throughout.
 * 
 * Design:
 * - Feels like a reward, not an alert
 * - Human-readable, not overly astrological
 * - Shows repeat detection ("You've been here before")
 * - Reflects back what just happened
 * - Provides clear next steps
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Colors } from '../constants/colors';
import { 
  getPhaseMirrorContent, 
  getPhaseIcon,
  getReversePrompt,
  getPhaseTensionInsight,
} from '../services/timelinePhaseUtils';
import { getJournalPatterns, JournalPatternAnalysis } from '../services/api';
import { useAppStore } from '../store';
import { cleanText } from '../utils/languageGuard';

// Timing
const FADE_IN_DURATION = 350;
const FADE_IN_DELAY = 300;

// Phase colors
const PHASE_COLORS: { [key: string]: string } = {
  q1: 'rgba(76, 175, 80, 0.12)',
  q2: 'rgba(255, 152, 0, 0.12)',
  q3: 'rgba(139, 92, 246, 0.12)',
  q4: 'rgba(33, 150, 243, 0.12)',
};

const PHASE_BORDER_COLORS: { [key: string]: string } = {
  q1: 'rgba(76, 175, 80, 0.25)',
  q2: 'rgba(255, 152, 0, 0.25)',
  q3: 'rgba(139, 92, 246, 0.25)',
  q4: 'rgba(33, 150, 243, 0.25)',
};

const PHASE_ACCENT_COLORS: { [key: string]: string } = {
  q1: '#4CAF50',
  q2: '#FF9800',
  q3: '#8B5CF6',
  q4: '#2196F3',
};

interface PhaseMirrorCardProps {
  phaseId: string;
  phaseName: string;
  visible: boolean;
  onViewTimeline?: () => void;
  onWriteDeeper?: (prompt: string) => void;
  onDismiss?: () => void;
}

const PhaseMirrorCard: React.FC<PhaseMirrorCardProps> = ({
  phaseId,
  phaseName,
  visible,
  onViewTimeline,
  onWriteDeeper,
  onDismiss,
}) => {
  const { theme, isDark } = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(10)).current;
  
  // Pattern detection state
  const [patternData, setPatternData] = useState<JournalPatternAnalysis | null>(null);
  const [loadingPatterns, setLoadingPatterns] = useState(false);
  const user = useAppStore(state => state.user);

  // Fetch pattern data
  useEffect(() => {
    if (visible && user?.id && !patternData) {
      setLoadingPatterns(true);
      getJournalPatterns(user.id)
        .then(data => {
          setPatternData(data);
        })
        .catch(err => {
          console.error('[PhaseMirrorCard] Failed to fetch patterns:', err);
        })
        .finally(() => {
          setLoadingPatterns(false);
        });
    }
  }, [visible, user?.id, patternData]);

  useEffect(() => {
    if (visible) {
      const timer = setTimeout(() => {
        Animated.parallel([
          Animated.timing(fadeAnim, {
            toValue: 1,
            duration: FADE_IN_DURATION,
            useNativeDriver: true,
          }),
          Animated.timing(slideAnim, {
            toValue: 0,
            duration: FADE_IN_DURATION,
            useNativeDriver: true,
          }),
        ]).start();
      }, FADE_IN_DELAY);

      return () => clearTimeout(timer);
    } else {
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }).start();
    }
  }, [visible, fadeAnim, slideAnim]);

  if (!visible || !phaseId || !phaseName) {
    return null;
  }

  const content = getPhaseMirrorContent(phaseId);
  const icon = getPhaseIcon(phaseId);
  const bgColor = PHASE_COLORS[phaseId] || 'rgba(139, 92, 246, 0.1)';
  const borderColor = PHASE_BORDER_COLORS[phaseId] || 'rgba(139, 92, 246, 0.25)';
  const accentColor = PHASE_ACCENT_COLORS[phaseId] || Colors.accent;
  
  // Check if this is a repeating phase
  const isRepeatingPhase = patternData?.repeating_phases?.includes(phaseId) || false;
  const phaseEntryCount = patternData?.phase_distribution?.[phaseId] || 0;
  
  // Get recurring patterns for this phase (Level 2)
  const recurringPatterns = patternData?.phase_patterns?.[phaseId] || [];
  
  // Get tension insight for this phase (Level 3)
  const tensionInsight = patternData?.phase_tensions?.[phaseId] || '';
  
  // Get compressed pattern line for this phase (V2.5 - Emotional centerpiece)
  const compressedPatternLine = patternData?.compressed_pattern_lines?.[phaseId] || '';
  
  // Get identity echo when threshold met (V2.6)
  const identityEcho = patternData?.identity_echo || null;
  
  // Get angle line from transits (V2.7 - Amplifier)
  const angleLine = patternData?.angle_line || null;
  
  // Get facet line (V3 - Facet Selection Engine)
  const facetLine = patternData?.facet_line || null;
  
  // Get identity tendency if threshold met (Level 4)
  const identityTendency = patternData?.identity_threshold_met ? patternData.identity_tendency : null;
  
  // Reverse prompt for "Write deeper"
  const deeperPrompt = getReversePrompt(phaseId, Date.now());

  return (
    <Animated.View
      style={[
        styles.container,
        {
          backgroundColor: isDark ? bgColor : bgColor,
          borderColor: borderColor,
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      {/* Phase Header */}
      <View style={styles.headerRow}>
        <View style={[styles.phaseTag, { backgroundColor: borderColor }]}>
          <Text style={styles.phaseIcon}>{icon}</Text>
          <Text style={[styles.phaseTagText, { color: theme.text }]}>{content.phaseName}</Text>
        </View>
        <Text style={[styles.humanMeaning, { color: theme.textSecondary }]}>
          {content.humanMeaning}
        </Text>
      </View>

      {/* "Sounds like" line - observational, not declarative */}
      <Text style={[styles.soundsLikeLine, { color: theme.text }]}>
        {content.soundsLikeLine}
      </Text>

      {/* Larger context line */}
      <Text style={[styles.largerContextLine, { color: theme.textSecondary }]}>
        {content.largerContextLine}
      </Text>

      {/* LEVEL 1: Repeat Detection */}
      {isRepeatingPhase && (
        <View style={[styles.repeatSection, { borderColor: accentColor + '30' }]}>
          <Text style={[styles.repeatLine, { color: accentColor }]}>
            {content.repeatLine}
          </Text>
          <Text style={[styles.repeatSubline, { color: theme.textSecondary }]}>
            This phase has shown up more than once.
          </Text>
        </View>
      )}

      {/* ====== V2.6 PATTERN SECTION - INSIGHT FIRST, PROOF SECOND ====== */}
      
      {/* LEVEL 2.6 STEP 1: Compressed Pattern Line (EMOTIONAL CENTERPIECE - FIRST) */}
      {compressedPatternLine && recurringPatterns.length > 0 && (
        <View style={styles.compressedPatternSection}>
          <Text style={[styles.compressedLeadIn, { color: theme.textTertiary }]}>
            This might be what's underneath:
          </Text>
          <View style={[styles.compressedPatternContainer, { borderColor: accentColor + '40' }]}>
            <Text style={[styles.compressedPatternLine, { color: theme.text }]}>
              {cleanText(compressedPatternLine)}
            </Text>
          </View>
        </View>
      )}

      {/* LEVEL 2.6 STEP 2: Identity Echo (when threshold met) */}
      {identityEcho && patternData?.identity_threshold_met && (
        <View style={[styles.identityEchoSection, { backgroundColor: accentColor + '08', borderColor: accentColor + '20' }]}>
          <Text style={[styles.identityEchoLabel, { color: accentColor }]}>
            A pattern in how you move:
          </Text>
          <Text style={[styles.identityEchoText, { color: theme.text }]}>
            {cleanText(identityEcho)}
          </Text>
        </View>
      )}

      {/* LEVEL 2.7 STEP 3: Angle Line - Transit-based amplifier (V1) */}
      {angleLine && compressedPatternLine && (
        <View style={styles.angleLineSection}>
          <Text style={[styles.angleLineLabel, { color: theme.textTertiary }]}>
            Why this may feel stronger right now:
          </Text>
          <Text style={[styles.angleLineText, { color: theme.textSecondary }]}>
            {cleanText(angleLine)}
          </Text>
        </View>
      )}

      {/* V3: Facet Line - Where the pattern is most active */}
      {facetLine && compressedPatternLine && (
        <View style={styles.facetLineSection}>
          <Text style={[styles.facetLineLabel, { color: theme.textTertiary }]}>
            Where this may be landing:
          </Text>
          <Text style={[styles.facetLineText, { color: theme.textSecondary }]}>
            {cleanText(facetLine)}
          </Text>
        </View>
      )}

      {/* LEVEL 2.6 STEP 3: Recurring Patterns (PROOF - AFTER INSIGHT) */}
      {recurringPatterns.length > 0 && (
        <View style={styles.patternsSection}>
          <Text style={[styles.patternsSectionTitle, { color: theme.textTertiary }]}>
            Threads that keep appearing:
          </Text>
          {recurringPatterns.map((pattern, i) => (
            <Text key={i} style={[styles.patternItem, { color: theme.textSecondary }]}>
              • {cleanText(pattern)}
            </Text>
          ))}
        </View>
      )}

      {/* LEVEL 2.6 STEP 4: Tension Insight */}
      {tensionInsight && recurringPatterns.length > 0 && (
        <View style={styles.tensionSection}>
          <Text style={[styles.tensionLabel, { color: theme.textTertiary }]}>
            What this might reflect:
          </Text>
          <Text style={[styles.tensionInsight, { color: theme.textSecondary }]}>
            {cleanText(tensionInsight)}
          </Text>
        </View>
      )}

      {/* ====== END V2.6 PATTERN SECTION ====== */}

      {/* Emotional Quote Line */}
      <View style={[styles.emotionalContainer, { borderLeftColor: accentColor }]}>
        <Text style={[styles.emotionalLine, { color: theme.text }]}>
          "{content.emotionalLine}"
        </Text>
      </View>

      {/* CTA Prefix */}
      {isRepeatingPhase && (
        <Text style={[styles.ctaPrefix, { color: theme.textTertiary }]}>
          {content.ctaPrefix}
        </Text>
      )}

      {/* CTAs */}
      <View style={styles.ctaRow}>
        <TouchableOpacity
          style={[styles.primaryCta, { backgroundColor: accentColor + '20', borderColor: accentColor + '40' }]}
          onPress={onViewTimeline}
          activeOpacity={0.7}
        >
          <Text style={[styles.primaryCtaText, { color: accentColor }]}>
            View this phase
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.secondaryCta, { borderColor: theme.border }]}
          onPress={() => onWriteDeeper?.(deeperPrompt)}
          activeOpacity={0.7}
        >
          <Text style={[styles.secondaryCtaText, { color: theme.textSecondary }]}>
            Write deeper
          </Text>
        </TouchableOpacity>
      </View>

      {/* Loading indicator for patterns */}
      {loadingPatterns && (
        <ActivityIndicator size="small" color={theme.textTertiary} style={{ marginTop: 8 }} />
      )}

      {/* Dismiss */}
      <TouchableOpacity
        style={styles.dismissButton}
        onPress={onDismiss}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        <Text style={[styles.dismissText, { color: theme.textTertiary }]}>dismiss</Text>
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 10,
    marginBottom: 10,
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
    overflow: 'hidden',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    marginBottom: 12,
    gap: 8,
  },
  phaseTag: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  phaseIcon: {
    fontSize: 12,
    marginRight: 5,
  },
  phaseTagText: {
    fontSize: 12,
    fontWeight: '600',
  },
  humanMeaning: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  soundsLikeLine: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 6,
  },
  largerContextLine: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 12,
  },
  // Level 1: Repeat Detection
  repeatSection: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 12,
  },
  repeatLine: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  repeatSubline: {
    fontSize: 12,
  },
  // Level 2: Recurring Patterns
  patternsSection: {
    marginBottom: 12,
  },
  patternsSectionTitle: {
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  patternItem: {
    fontSize: 12,
    lineHeight: 18,
    marginLeft: 4,
    marginBottom: 2,
  },
  // V2.6: Compressed Pattern Line (EMOTIONAL CENTERPIECE - FIRST)
  compressedPatternSection: {
    marginTop: 8,
    marginBottom: 16,
  },
  compressedLeadIn: {
    fontSize: 11,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  compressedPatternContainer: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderLeftWidth: 3,
  },
  compressedPatternLine: {
    fontSize: 16,
    lineHeight: 24,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  // V2.6: Identity Echo (when threshold met)
  identityEchoSection: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 14,
  },
  identityEchoLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  identityEchoText: {
    fontSize: 13,
    lineHeight: 19,
  },
  // V2.7: Angle Line - Transit-based amplifier
  angleLineSection: {
    marginBottom: 12,
    paddingLeft: 8,
  },
  angleLineLabel: {
    fontSize: 10,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  angleLineText: {
    fontSize: 12,
    lineHeight: 18,
    fontStyle: 'italic',
  },
  // V3: Facet Line - Where the pattern is most active
  facetLineSection: {
    marginBottom: 12,
    paddingLeft: 8,
  },
  facetLineLabel: {
    fontSize: 10,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  facetLineText: {
    fontSize: 12,
    lineHeight: 18,
  },
  // Level 3: Tension Insight
  tensionSection: {
    marginBottom: 12,
  },
  tensionLabel: {
    fontSize: 10,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  tensionInsight: {
    fontSize: 12,
    lineHeight: 18,
  },
  // Emotional quote
  emotionalContainer: {
    borderLeftWidth: 2,
    paddingLeft: 12,
    marginBottom: 12,
  },
  emotionalLine: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  // CTA area
  ctaPrefix: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
    marginBottom: 8,
  },
  ctaRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 8,
  },
  primaryCta: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  primaryCtaText: {
    fontSize: 13,
    fontWeight: '600',
  },
  secondaryCta: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  secondaryCtaText: {
    fontSize: 13,
    fontWeight: '500',
  },
  dismissButton: {
    alignSelf: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  dismissText: {
    fontSize: 11,
    fontStyle: 'italic',
  },
});

export default PhaseMirrorCard;
