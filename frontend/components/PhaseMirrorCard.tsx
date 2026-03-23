/**
 * PhaseMirrorCard Component
 * 
 * Displays after saving a journal entry, showing which timeline phase
 * the entry belongs to. Creates a visual bridge between Journal and Timeline.
 * 
 * Part of the "Journal ↔ Timeline Connection" feature.
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

// ============================================
// TIMING CONSTANTS
// ============================================
const FADE_IN_DURATION = 300;
const FADE_IN_DELAY = 200; // Appears slightly after MicroMirrorCard

// ============================================
// PHASE ICONS MAPPING
// ============================================
const PHASE_ICONS: { [key: string]: string } = {
  q1: '🌱',  // Recognition - new growth
  q2: '⚡',  // Confrontation - energy
  q3: '🔀',  // The Crossroads - decision
  q4: '🌊',  // Integration - flow
};

const PHASE_COLORS: { [key: string]: string } = {
  q1: 'rgba(76, 175, 80, 0.15)',   // Green tint
  q2: 'rgba(255, 152, 0, 0.15)',   // Orange tint
  q3: 'rgba(139, 92, 246, 0.15)',  // Purple tint
  q4: 'rgba(33, 150, 243, 0.15)',  // Blue tint
};

const PHASE_BORDER_COLORS: { [key: string]: string } = {
  q1: 'rgba(76, 175, 80, 0.3)',
  q2: 'rgba(255, 152, 0, 0.3)',
  q3: 'rgba(139, 92, 246, 0.3)',
  q4: 'rgba(33, 150, 243, 0.3)',
};

interface PhaseMirrorCardProps {
  phaseId: string;
  phaseName: string;
  visible: boolean;
  onViewTimeline?: () => void;
  onDismiss?: () => void;
}

const PhaseMirrorCard: React.FC<PhaseMirrorCardProps> = ({
  phaseId,
  phaseName,
  visible,
  onViewTimeline,
  onDismiss,
}) => {
  const { theme, isDark } = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      // Delay then fade in
      const timer = setTimeout(() => {
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: FADE_IN_DURATION,
          useNativeDriver: true,
        }).start();
      }, FADE_IN_DELAY);

      return () => clearTimeout(timer);
    } else {
      // Fade out quickly
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }).start();
    }
  }, [visible, fadeAnim]);

  if (!visible || !phaseId || !phaseName) {
    return null;
  }

  const icon = PHASE_ICONS[phaseId] || '⭐';
  const bgColor = PHASE_COLORS[phaseId] || 'rgba(139, 92, 246, 0.1)';
  const borderColor = PHASE_BORDER_COLORS[phaseId] || 'rgba(139, 92, 246, 0.25)';

  // Get a phase-appropriate message
  const getPhaseMessage = (): string => {
    switch (phaseId) {
      case 'q1':
        return 'This entry lands in Recognition—when patterns first reveal themselves.';
      case 'q2':
        return 'This entry lands in Confrontation—when what was tolerable stops being so.';
      case 'q3':
        return 'This entry lands in The Crossroads—the year\'s primary choice point.';
      case 'q4':
        return 'This entry lands in Integration—where your choices begin to settle.';
      default:
        return `This entry is part of your ${phaseName} phase.`;
    }
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          backgroundColor: isDark ? bgColor : bgColor,
          borderColor: borderColor,
          opacity: fadeAnim,
        },
      ]}
    >
      {/* Phase Tag */}
      <View style={styles.phaseTagRow}>
        <View style={[styles.phaseTag, { backgroundColor: borderColor }]}>
          <Text style={styles.phaseIcon}>{icon}</Text>
          <Text style={[styles.phaseTagText, { color: theme.text }]}>{phaseName}</Text>
        </View>
      </View>

      {/* Message */}
      <Text style={[styles.message, { color: theme.textSecondary }]}>
        {getPhaseMessage()}
      </Text>

      {/* Actions */}
      <View style={styles.actionsRow}>
        <TouchableOpacity
          style={[styles.viewTimelineButton, { borderColor: theme.border }]}
          onPress={onViewTimeline}
          activeOpacity={0.7}
        >
          <Text style={[styles.viewTimelineText, { color: theme.textSecondary }]}>
            View Timeline
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.dismissButton}
          onPress={onDismiss}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Text style={[styles.dismissText, { color: theme.textTertiary }]}>dismiss</Text>
        </TouchableOpacity>
      </View>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 8,
    marginBottom: 8,
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    overflow: 'hidden',
  },
  phaseTagRow: {
    flexDirection: 'row',
    marginBottom: 10,
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
  message: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  actionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  viewTimelineButton: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
  },
  viewTimelineText: {
    fontSize: 12,
    fontWeight: '500',
  },
  dismissButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  dismissText: {
    fontSize: 11,
    fontStyle: 'italic',
  },
});

export default PhaseMirrorCard;
