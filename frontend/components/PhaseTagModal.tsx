/**
 * PhaseTagModal Component - V2 Pattern Detection Layer
 * 
 * Lightweight modal that appears when a user taps on a phase pill
 * in their journal entries.
 * 
 * V2 Language Updates:
 * - Uses "Entries like this often appear when..." (observational)
 * - NOT "This entry was created during..." (declarative)
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  TouchableWithoutFeedback,
  Animated,
  Dimensions,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Colors } from '../constants/colors';
import { 
  getPhaseTagExplanation, 
  getPhaseIcon,
} from '../services/timelinePhaseUtils';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

// Phase colors
const PHASE_ACCENT_COLORS: { [key: string]: string } = {
  q1: '#4CAF50',
  q2: '#FF9800',
  q3: '#8B5CF6',
  q4: '#2196F3',
};

interface PhaseTagModalProps {
  visible: boolean;
  phaseId: string;
  phaseName: string;
  entryDate: string;
  onClose: () => void;
  onSeeRelated: (phaseId: string) => void;
}

const PhaseTagModal: React.FC<PhaseTagModalProps> = ({
  visible,
  phaseId,
  phaseName,
  entryDate,
  onClose,
  onSeeRelated,
}) => {
  const { theme, isDark } = useTheme();
  const slideAnim = useRef(new Animated.Value(300)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.timing(backdropAnim, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.spring(slideAnim, {
          toValue: 0,
          tension: 65,
          friction: 11,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(backdropAnim, {
          toValue: 0,
          duration: 150,
          useNativeDriver: true,
        }),
        Animated.timing(slideAnim, {
          toValue: 300,
          duration: 150,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible, slideAnim, backdropAnim]);

  if (!phaseId) return null;

  const explanation = getPhaseTagExplanation(phaseId);
  const icon = getPhaseIcon(phaseId);
  const accentColor = PHASE_ACCENT_COLORS[phaseId] || Colors.accent;

  // Format entry date
  const formattedDate = new Date(entryDate).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <Modal
      visible={visible}
      transparent
      animationType="none"
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <Animated.View 
          style={[
            styles.backdrop, 
            { opacity: backdropAnim }
          ]}
        />
      </TouchableWithoutFeedback>
      
      <Animated.View
        style={[
          styles.drawer,
          {
            backgroundColor: theme.surface,
            transform: [{ translateY: slideAnim }],
          },
        ]}
      >
        {/* Drag Handle */}
        <View style={styles.handleContainer}>
          <View style={[styles.handle, { backgroundColor: theme.border }]} />
        </View>

        {/* Phase Header */}
        <View style={styles.header}>
          <View style={[styles.phaseTag, { backgroundColor: accentColor + '20' }]}>
            <Text style={styles.phaseIcon}>{icon}</Text>
            <Text style={[styles.phaseTagText, { color: accentColor }]}>{explanation.phaseName}</Text>
          </View>
          <Text style={[styles.humanMeaning, { color: theme.textSecondary }]}>
            {explanation.humanMeaning}
          </Text>
        </View>

        {/* Entry Date Context */}
        <View style={[styles.dateContext, { borderColor: theme.border }]}>
          <Text style={[styles.dateLabel, { color: theme.textTertiary }]}>
            Written on
          </Text>
          <Text style={[styles.dateValue, { color: theme.text }]}>
            {formattedDate}
          </Text>
        </View>

        {/* Why Tagged - V2 observational language */}
        <Text style={[styles.whyTagged, { color: theme.text }]}>
          {explanation.whyTagged}
        </Text>

        {/* Insight */}
        <View style={[styles.insightContainer, { borderLeftColor: accentColor }]}>
          <Text style={[styles.insight, { color: theme.textSecondary }]}>
            {explanation.insight}
          </Text>
        </View>

        {/* CTA */}
        <TouchableOpacity
          style={[styles.seeRelatedBtn, { backgroundColor: accentColor + '15', borderColor: accentColor + '30' }]}
          onPress={() => onSeeRelated(phaseId)}
          activeOpacity={0.7}
        >
          <Text style={[styles.seeRelatedText, { color: accentColor }]}>
            See related entries in this phase
          </Text>
        </TouchableOpacity>

        {/* Close */}
        <TouchableOpacity
          style={styles.closeBtn}
          onPress={onClose}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Text style={[styles.closeText, { color: theme.textTertiary }]}>close</Text>
        </TouchableOpacity>
      </Animated.View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  drawer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: 34,
    maxHeight: SCREEN_HEIGHT * 0.6,
  },
  handleContainer: {
    alignItems: 'center',
    paddingTop: 12,
    paddingBottom: 8,
  },
  handle: {
    width: 40,
    height: 4,
    borderRadius: 2,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    paddingHorizontal: 20,
    paddingBottom: 12,
    gap: 10,
  },
  phaseTag: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
  },
  phaseIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  phaseTagText: {
    fontSize: 14,
    fontWeight: '600',
  },
  humanMeaning: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  dateContext: {
    marginHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dateLabel: {
    fontSize: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  dateValue: {
    fontSize: 14,
  },
  whyTagged: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    fontSize: 14,
    lineHeight: 21,
  },
  insightContainer: {
    marginHorizontal: 20,
    paddingLeft: 12,
    borderLeftWidth: 2,
    marginBottom: 20,
  },
  insight: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  seeRelatedBtn: {
    marginHorizontal: 20,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
    marginBottom: 12,
  },
  seeRelatedText: {
    fontSize: 14,
    fontWeight: '600',
  },
  closeBtn: {
    alignSelf: 'center',
    paddingVertical: 8,
    paddingHorizontal: 20,
  },
  closeText: {
    fontSize: 12,
    fontStyle: 'italic',
  },
});

export default PhaseTagModal;
