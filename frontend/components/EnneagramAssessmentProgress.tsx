/**
 * EnneagramAssessmentProgress
 * ===========================
 * Stage-based progress indicator (not question count).
 * Provides reassurance without pressure.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../constants/colors';

interface Props {
  stage: string;
  estimatedMinutesRemaining: number;
}

// Map backend stages to user-friendly labels
const STAGE_MAP: Record<string, { label: string; order: number }> = {
  center: { label: 'Orientation', order: 1 },
  core: { label: 'Core Patterns', order: 2 },
  diff: { label: 'Refinement', order: 3 },
  wing: { label: 'Nuance', order: 4 },
  instinct: { label: 'Nuance', order: 4 }, // Same display as wing
  consistency: { label: 'Final Check', order: 5 },
  done: { label: 'Complete', order: 6 },
};

const VISIBLE_STAGES = [
  { key: 'orientation', label: 'Orientation', order: 1 },
  { key: 'core', label: 'Core Patterns', order: 2 },
  { key: 'refinement', label: 'Refinement', order: 3 },
  { key: 'nuance', label: 'Nuance', order: 4 },
  { key: 'final', label: 'Final Check', order: 5 },
];

export const EnneagramAssessmentProgress: React.FC<Props> = ({
  stage,
  estimatedMinutesRemaining,
}) => {
  const currentStageInfo = STAGE_MAP[stage] || { label: 'Assessment', order: 1 };
  const currentOrder = currentStageInfo.order;

  return (
    <View style={styles.container}>
      {/* Stage Indicators */}
      <View style={styles.stagesRow}>
        {VISIBLE_STAGES.map((s, index) => {
          const isActive = s.order === currentOrder;
          const isCompleted = s.order < currentOrder;
          
          return (
            <View key={s.key} style={styles.stageItem}>
              <View
                style={[
                  styles.stageDot,
                  isCompleted && styles.stageDotCompleted,
                  isActive && styles.stageDotActive,
                ]}
              />
              {index < VISIBLE_STAGES.length - 1 && (
                <View
                  style={[
                    styles.stageLine,
                    isCompleted && styles.stageLineCompleted,
                  ]}
                />
              )}
            </View>
          );
        })}
      </View>

      {/* Current Stage Label */}
      <Text style={styles.stageLabel}>{currentStageInfo.label}</Text>

      {/* Time Remaining */}
      {estimatedMinutesRemaining > 0 && (
        <Text style={styles.timeRemaining}>
          ~{Math.ceil(estimatedMinutesRemaining)} min remaining
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  stagesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  stageItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stageDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.border,
  },
  stageDotCompleted: {
    backgroundColor: Colors.textTertiary,
  },
  stageDotActive: {
    backgroundColor: Colors.accent,
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  stageLine: {
    width: 32,
    height: 2,
    backgroundColor: Colors.border,
    marginHorizontal: 4,
  },
  stageLineCompleted: {
    backgroundColor: Colors.textTertiary,
  },
  stageLabel: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 4,
  },
  timeRemaining: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
});

export default EnneagramAssessmentProgress;
