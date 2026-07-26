import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { LifePhaseGap } from '../services/api';

/**
 * PhaseGapPrompt — soft, contextual invitation to add a missing moment.
 *
 * Renders INLINE under the PhaseTimeline cards. Not a modal. Not an alert.
 * Only shown when `gap.show === true`.
 *
 * IMPORTANT (UX integrity):
 * The prompt does NOT fabricate suggestions about WHAT happened. It only
 * invites the user to add a real lifeline event for an under-captured phase.
 * Reflections (thinking) live elsewhere — the "Reflect" button in each
 * domain tab. Lifeline (reality) is intentional, real-event-only.
 */

interface Props {
  gap?: LifePhaseGap | null;
  onAddMoment: (context: { suggested_domain?: string | null }) => void;
}

const PROMPT_COPY = 'There may be a moment that shaped this shift.';
const CTA_COPY = '+ Add Lifeline Event';

export default function PhaseGapPrompt({ gap, onAddMoment }: Props) {
  const { theme } = useTheme();

  if (!gap || !gap.show || !gap.reasons || gap.reasons.length === 0) return null;

  const handlePress = () => {
    onAddMoment({ suggested_domain: gap.dominant_domain ?? null });
  };

  return (
    <View style={styles.container}>
      <Text style={[styles.promptText, { color: theme.textSecondary }]}>
        {PROMPT_COPY}
      </Text>
      <Pressable
        onPress={handlePress}
        hitSlop={10}
        style={({ pressed }) => [
          styles.ctaWrap,
          { opacity: pressed ? 0.7 : 1 },
        ]}
      >
        <Text style={[styles.cta, { color: theme.text }]}>{CTA_COPY}</Text>
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
    fontWeight: '500',
    letterSpacing: 0.2,
  },
});
