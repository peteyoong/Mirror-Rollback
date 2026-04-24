import React, { useCallback, useMemo, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { LifePhase, LifePhaseDomain } from '../services/api';

/**
 * Phase Timeline — horizontal meaning layer above the Pattern stack.
 *
 * - Cards scroll horizontally with a thin line behind them.
 * - The is_current=true phase is slightly emphasised (scale, border, "Now" chip).
 * - Tap a card to expand inline (full description + pattern_expression).
 * - Domain tint is whisper-soft (small dot + border tint only).
 * - No dates, no confidence labels, no domain labels visible to user.
 */

if (
  Platform.OS === 'android' &&
  UIManager.setLayoutAnimationEnabledExperimental
) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface Props {
  phases: LifePhase[] | null | undefined;
  loading?: boolean;
}

const CARD_WIDTH = 208;
const CARD_GAP = 14;
const CURRENT_SCALE = 1.06;

type DomainTheme = {
  dot: string;
  tint: string;   // subtle border tint
  bgTint: string; // subtle card bg tint when current
};

// Whisper-soft domain palette — never loud.
function getDomainTheme(
  domain: LifePhaseDomain,
  isDark: boolean
): DomainTheme {
  if (domain === 'work') {
    return isDark
      ? { dot: '#6C8CB2', tint: 'rgba(108, 140, 178, 0.35)', bgTint: 'rgba(108, 140, 178, 0.08)' }
      : { dot: '#8FA8C4', tint: 'rgba(143, 168, 196, 0.45)', bgTint: 'rgba(143, 168, 196, 0.09)' };
  }
  if (domain === 'relationships') {
    return isDark
      ? { dot: '#C98E86', tint: 'rgba(201, 142, 134, 0.35)', bgTint: 'rgba(201, 142, 134, 0.08)' }
      : { dot: '#D0A299', tint: 'rgba(208, 162, 153, 0.45)', bgTint: 'rgba(208, 162, 153, 0.09)' };
  }
  // self
  return isDark
    ? { dot: '#9A9AA5', tint: 'rgba(154, 154, 165, 0.35)', bgTint: 'rgba(154, 154, 165, 0.08)' }
    : { dot: '#ADADB4', tint: 'rgba(173, 173, 180, 0.45)', bgTint: 'rgba(173, 173, 180, 0.09)' };
}

const PhaseCard = React.memo(function PhaseCard({
  phase,
  isExpanded,
  onPress,
}: {
  phase: LifePhase;
  isExpanded: boolean;
  onPress: () => void;
}) {
  const { theme, isDark } = useTheme();
  const dt = getDomainTheme(phase.dominant_domain, isDark);

  const isCurrent = !!phase.is_current;
  const showNow = isCurrent && phase.confidence !== 'low';

  const cardBorder = isCurrent ? dt.tint : theme.border;
  const cardBg = isCurrent ? dt.bgTint : theme.surface;
  const labelColor = isCurrent ? theme.text : theme.textSecondary;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.card,
        {
          width: CARD_WIDTH,
          backgroundColor: cardBg,
          borderColor: cardBorder,
          borderWidth: isCurrent ? 1.5 : StyleSheet.hairlineWidth,
          transform: [{ scale: isCurrent ? CURRENT_SCALE : 1 }],
          opacity: pressed ? 0.86 : 1,
        },
      ]}
      hitSlop={6}
    >
      {showNow && (
        <View style={[styles.nowPill, { backgroundColor: theme.text }]}>
          <Text style={[styles.nowPillText, { color: theme.background }]}>Now</Text>
        </View>
      )}
      <Text
        numberOfLines={2}
        style={[
          styles.label,
          {
            color: labelColor,
            fontWeight: isCurrent ? '700' : '600',
          },
        ]}
      >
        {phase.label}
      </Text>
      <Text
        numberOfLines={isExpanded ? 5 : 2}
        style={[styles.description, { color: theme.textSecondary }]}
      >
        {phase.description}
      </Text>
      {isExpanded && !!phase.pattern_expression && (
        <Text
          style={[
            styles.patternExpression,
            { color: theme.textTertiary, borderTopColor: theme.border },
          ]}
        >
          {phase.pattern_expression}
        </Text>
      )}
      <View style={[styles.dotRow]}>
        <View
          style={[
            styles.dot,
            {
              backgroundColor: dt.dot,
              transform: [{ scale: isCurrent ? 1.35 : 1 }],
              opacity: isCurrent ? 1 : 0.75,
            },
          ]}
        />
      </View>
    </Pressable>
  );
});

export default function PhaseTimeline({ phases, loading }: Props) {
  const { theme } = useTheme();
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  // Default-expand the current phase quietly (without auto-scroll).
  const currentIdx = useMemo(() => {
    if (!phases) return -1;
    return phases.findIndex(p => p.is_current);
  }, [phases]);

  const handlePress = useCallback(
    (idx: number) => {
      LayoutAnimation.configureNext(
        LayoutAnimation.create(180, LayoutAnimation.Types.easeInEaseOut, LayoutAnimation.Properties.opacity)
      );
      setExpandedIdx(prev => (prev === idx ? null : idx));
    },
    []
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={[styles.skeletonRow]}>
          {[0, 1, 2].map(i => (
            <View
              key={i}
              style={[
                styles.skeletonCard,
                {
                  backgroundColor: theme.surface,
                  borderColor: theme.border,
                  width: CARD_WIDTH,
                  marginRight: CARD_GAP,
                },
              ]}
            />
          ))}
        </View>
      </View>
    );
  }

  if (!phases || phases.length === 0) return null;

  return (
    <View style={styles.container}>
      <View style={styles.lineWrap} pointerEvents="none">
        <View style={[styles.line, { backgroundColor: theme.border }]} />
      </View>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {phases.map((phase, idx) => (
          <View
            key={`${idx}-${phase.label}`}
            style={{
              marginRight: idx === phases.length - 1 ? 0 : CARD_GAP,
              // leave headroom so the scale doesn't clip siblings
              paddingTop: 8,
              paddingBottom: 6,
            }}
          >
            <PhaseCard
              phase={phase}
              isExpanded={expandedIdx === idx || (expandedIdx === null && idx === currentIdx && phase.is_current && phase.confidence !== 'low')}
              onPress={() => handlePress(idx)}
            />
          </View>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    marginTop: 18,
    marginBottom: 6,
  },
  lineWrap: {
    position: 'absolute',
    left: 16,
    right: 16,
    top: 56,            // aligned with dot row (roughly middle of card)
    height: 1,
    zIndex: 0,
  },
  line: {
    height: 1,
    opacity: 0.6,
    borderRadius: 0.5,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingVertical: 2,
    zIndex: 1,
  },
  card: {
    borderRadius: 14,
    paddingVertical: 12,
    paddingHorizontal: 14,
    minHeight: 124,
  },
  nowPill: {
    position: 'absolute',
    top: 8,
    right: 8,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    opacity: 0.92,
  },
  nowPillText: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.4,
  },
  label: {
    fontSize: 15,
    lineHeight: 20,
    marginBottom: 6,
    marginRight: 32, // avoid colliding with Now pill
  },
  description: {
    fontSize: 13,
    lineHeight: 18,
  },
  patternExpression: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 8,
    paddingTop: 8,
    fontStyle: 'italic',
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  dotRow: {
    position: 'absolute',
    bottom: -6,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  skeletonRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
  },
  skeletonCard: {
    height: 124,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    opacity: 0.5,
  },
});
