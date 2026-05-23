// ============================================================================
// TimelineWhisper — Phase 1B/1C Frontend Expression Layer
// ============================================================================
//
// Build marker: timeline-frontend-soft-modulation-v1
//
// Renders the Timeline modulation thread as a single low-contrast atmospheric
// line. Only surfaces when:
//   - timeline_modulation.active === true
//   - timeline_modulation.strength === 'HIGH'
//   - timeline_modulation.thread is a non-empty string
//
// In ALL other cases (LOW / MEDIUM / no modulation block) this component
// returns null and consumes zero pixels. This is intentional:
//
//   * LOW    → chapter is irrelevant for this day; silence.
//   * MEDIUM → chapter is present in the payload as `bias` but should
//              never narrate. The bias is reserved for future server-side
//              content tilting (eyebrow phrasing, CTA orientation,
//              card-ordering). We do NOT surface it as UI text — that
//              would re-create the very narrative-dictatorship the
//              backend gate exists to prevent.
//   * HIGH   → one whisper. Smaller than body. Lower contrast. No badge.
//              No chapter label. No "you are in…" framing. Observational.
//
// The Whisper NEVER:
//   - shows the chapter title or arc_type
//   - uses chapter-family color coding (no archetype tagging in UI)
//   - sits in the headline area
//   - claims importance over the host card's main narrative
//
// Typography target: secondary text colour, italic, ~13px, leading-relaxed.
// ============================================================================

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

export interface TimelineModulation {
  active?: boolean;
  strength?: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  bias?: string;
  thread?: string | null;
  chapter_id?: string | null;
  chapter_title?: string | null;
}

interface TimelineWhisperProps {
  modulation?: TimelineModulation | null;
  theme: any;
  /**
   * Optional placement hint:
   *   - 'inline'  → no top divider, blends with surrounding paragraphs
   *   - 'spaced' → small vertical gap above (used between body sections)
   * Defaults to 'spaced'.
   */
  placement?: 'inline' | 'spaced';
}

/**
 * Single source of truth for whether the whisper should be shown.
 * Exported for use in conditional layout (e.g. spacing decisions in host
 * components) without requiring duplication of the rule.
 */
export function shouldRenderWhisper(modulation?: TimelineModulation | null): boolean {
  if (!modulation) return false;
  if (modulation.active !== true) return false;
  if (modulation.strength !== 'HIGH') return false;
  const t = modulation.thread;
  return typeof t === 'string' && t.trim().length > 0;
}

const TimelineWhisper: React.FC<TimelineWhisperProps> = ({
  modulation,
  theme,
  placement = 'spaced',
}) => {
  if (!shouldRenderWhisper(modulation)) return null;
  const thread = (modulation!.thread || '').trim();

  return (
    <View
      style={[
        styles.wrap,
        placement === 'spaced' ? styles.wrapSpaced : styles.wrapInline,
      ]}
      // Use accessibilityRole=text so screen readers don't announce it as
      // a heading or button. It is supplementary atmospheric text only.
      accessible
      accessibilityRole="text"
    >
      <Text
        style={[
          styles.whisper,
          { color: theme?.textTertiary || '#8A8A8A' },
        ]}
      >
        {thread}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  wrap: {
    paddingHorizontal: 0,
  },
  wrapSpaced: {
    marginTop: 12,
    marginBottom: 4,
  },
  wrapInline: {
    marginTop: 4,
    marginBottom: 4,
  },
  whisper: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
    // Deliberately understated: lower font weight + tertiary color in
    // host ensures the whisper visually recedes below the main body.
    fontWeight: '400',
    opacity: 0.9,
  },
});

export default TimelineWhisper;
