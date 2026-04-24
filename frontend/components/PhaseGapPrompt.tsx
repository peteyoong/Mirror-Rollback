import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { LifePhaseGap, LifePhaseGapReason } from '../services/api';

/**
 * PhaseGapPrompt — soft, contextual invitation to add a missing moment.
 *
 * Renders INLINE under the PhaseTimeline cards. Not a modal. Not an alert.
 * Only shown when `gap.show === true`.
 *
 * UX rules (strict):
 *  - Show ONE prompt at a time (pick highest-priority reason).
 *  - Language is observational, never system-y.
 *  - No icons, no warnings, no "missing data" language.
 *  - Easy to ignore — it stays quiet if the user doesn't act.
 */

interface Props {
  gap?: LifePhaseGap | null;
  onAddMoment: (context: { suggested_domain?: string | null }) => void;
}

// Priority order — we pick the first reason that's present.
// "weak_transition" first because that's the most specific / evocative.
const REASON_PRIORITY: LifePhaseGapReason[] = [
  'weak_transition',
  'sparse_lifeline',
  'low_confidence',
  'weak_memory',
];

const COPY: Record<LifePhaseGapReason, string> = {
  low_confidence:   "This part of your story feels a bit incomplete.",
  weak_transition:  "There's likely a moment where this started to shift.",
  sparse_lifeline:  "Something important here might not be captured yet.",
  weak_memory:      "This pattern is emerging, but there's not much history yet.",
};

function pickCopy(reasons: LifePhaseGapReason[]): string {
  for (const r of REASON_PRIORITY) {
    if (reasons.includes(r)) return COPY[r];
  }
  // Fallback — should not trigger because gap.show already guards
  return COPY.sparse_lifeline;
}

export default function PhaseGapPrompt({ gap, onAddMoment }: Props) {
  const { theme } = useTheme();

  if (!gap || !gap.show || !gap.reasons || gap.reasons.length === 0) return null;

  const message = pickCopy(gap.reasons);

  const handlePress = () => {
    onAddMoment({ suggested_domain: gap.dominant_domain ?? null });
  };

  return (
    <View style={styles.container}>
      <Text style={[styles.promptText, { color: theme.textSecondary }]}>
        {message}
      </Text>
      <Pressable
        onPress={handlePress}
        hitSlop={10}
        style={({ pressed }) => [
          styles.ctaWrap,
          { opacity: pressed ? 0.7 : 1 },
        ]}
      >
        <Text style={[styles.cta, { color: theme.text }]}>+ Add that moment</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginTop: 14,
    marginBottom: 4,
    paddingVertical: 2,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  promptText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
    fontStyle: 'italic',
    opacity: 0.85,
  },
  ctaWrap: {
    paddingVertical: 4,
    paddingHorizontal: 2,
  },
  cta: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
});
