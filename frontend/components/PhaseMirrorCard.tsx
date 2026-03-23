/**
 * PhaseMirrorCard Component - UPGRADED
 * 
 * Appears after saving a journal entry, showing which timeline phase
 * the entry belongs to. Creates an emotionally meaningful bridge 
 * between Journal and Timeline.
 * 
 * Design philosophy:
 * - Feels like a reward, not an alert
 * - Human-readable, not overly astrological
 * - Reflects back what just happened
 * - Shows why it matters
 * - Provides clear next steps
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Colors } from '../constants/colors';
import { 
  getPhaseMirrorContent, 
  getPhaseIcon,
  getReversePrompt,
} from '../services/timelinePhaseUtils';

// ============================================
// TIMING CONSTANTS
// ============================================
const FADE_IN_DURATION = 350;
const FADE_IN_DELAY = 300; // Appears after MicroMirrorCard

// ============================================
// PHASE COLORS
// ============================================
const PHASE_COLORS: { [key: string]: string } = {
  q1: 'rgba(76, 175, 80, 0.12)',   // Green tint
  q2: 'rgba(255, 152, 0, 0.12)',   // Orange tint
  q3: 'rgba(139, 92, 246, 0.12)',  // Purple tint
  q4: 'rgba(33, 150, 243, 0.12)',  // Blue tint
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
  
  // Get a reverse prompt for the "Write deeper" CTA
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
      {/* Phase Landing Header */}
      <View style={styles.headerRow}>
        <View style={[styles.phaseTag, { backgroundColor: borderColor }]}>
          <Text style={styles.phaseIcon}>{icon}</Text>
          <Text style={[styles.phaseTagText, { color: theme.text }]}>{content.phaseName}</Text>
        </View>
        <Text style={[styles.humanMeaning, { color: theme.textSecondary }]}>
          {content.humanMeaning}
        </Text>
      </View>

      {/* What Just Happened */}
      <Text style={[styles.landingLine, { color: theme.text }]}>
        This entry lands in <Text style={{ color: accentColor, fontWeight: '600' }}>{content.phaseName}</Text>.
      </Text>

      {/* Why It Matters */}
      <Text style={[styles.whyMatters, { color: theme.textSecondary }]}>
        {content.whyItMatters}
      </Text>

      {/* Emotional Line */}
      <View style={[styles.emotionalContainer, { borderLeftColor: accentColor }]}>
        <Text style={[styles.emotionalLine, { color: theme.text }]}>
          "{content.emotionalLine}"
        </Text>
      </View>

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
  landingLine: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
  whyMatters: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 12,
  },
  emotionalContainer: {
    borderLeftWidth: 2,
    paddingLeft: 12,
    marginBottom: 16,
  },
  emotionalLine: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
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
