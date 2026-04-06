/**
 * InsightCardFooter - Shared footer for all insight-style cards
 * 
 * SYSTEM-WIDE STANDARD:
 * Every insight card should use this footer:
 * [ ✨ That resonates ]   [ Reflect ]
 * 
 * - Resonate = low-friction signal / pattern-memory input
 * - Reflect = open journal / deeper response
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { InlineResonanceReflect } from './ResonanceReflectButtons';
import { ReflectionSource } from './UniversalReflectionModal';

interface InsightCardFooterProps {
  /** Source information for the reflection */
  source: ReflectionSource;
  /** Pattern signature for resonance tracking */
  patternSignature?: string;
  /** Context: home, astrology, lens, forum, etc. */
  context: string;
  /** Optional prompt for the Reflect modal */
  prompt?: string;
  /** Whether to show a border at top */
  showBorder?: boolean;
  /** Theme for border color */
  borderColor?: string;
}

/**
 * Standard insight card footer with Resonate + Reflect buttons.
 * 
 * Usage:
 * ```tsx
 * <InsightCardFooter
 *   source={{
 *     lens: 'astrology',
 *     type: 'today_synthesis',
 *     name: 'Today\'s Theme',
 *     value: content.todays_theme,
 *     id: 'astro_today_2024-01-01',
 *   }}
 *   patternSignature="astro_today_identity_pressure"
 *   context="astrology_today"
 *   prompt="What feels true about this?"
 * />
 * ```
 */
export function InsightCardFooter({
  source,
  patternSignature,
  context,
  prompt,
  showBorder = true,
  borderColor = 'rgba(0,0,0,0.1)',
}: InsightCardFooterProps) {
  return (
    <View style={[
      styles.container,
      showBorder && styles.withBorder,
      showBorder && { borderTopColor: borderColor },
    ]}>
      <InlineResonanceReflect
        source={source}
        patternSignature={patternSignature}
        context={context}
        prompt={prompt}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 16,
    paddingTop: 16,
  },
  withBorder: {
    borderTopWidth: StyleSheet.hairlineWidth,
  },
});

export default InsightCardFooter;
