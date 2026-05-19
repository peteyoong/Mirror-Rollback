/**
 * MicroReflectionBar — one-tap ambient reflection chips
 * =====================================================
 *
 * Build marker: micro-reflection-v2
 *
 * Renders UNDER each assistant message bubble.  Two modes:
 *
 *   isLatest=true   → full chip row visible: "That lands · Familiar ·
 *                     Resisting · True lately · Not sure · Changed ·
 *                     Less intense".  After a first tap, optionally a
 *                     soft second row of emotional textures fades in
 *                     (tense / distant / open / pressured / stuck /
 *                     clear / conflicted / softer) — one optional tap.
 *
 *   isLatest=false  → collapsed ghosted affordance ("Reflect ·") — single
 *                     tap to expand inline.
 *
 * Design rules (per spec):
 *   - One tap is enough — no journaling expected.
 *   - Post-tap acknowledgement is tiny ("Noted." / "I'll hold that.").
 *   - No counts, streaks, or rewards.
 *   - Visually softer than chat actions, lighter than buttons.
 *   - Stays silent on errors — the chat must not be disturbed.
 */
import React, { useState } from 'react';
import {
  LayoutAnimation,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  UIManager,
  View,
} from 'react-native';

import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// ---------------------------------------------------------------------------
// Types — keep aligned with services/micro_reflection_v2.py
// ---------------------------------------------------------------------------

export type ReflectionLabel =
  | 'lands'
  | 'familiar'
  | 'resisting'
  | 'true_lately'
  | 'not_sure'
  | 'changed'
  | 'less_intense';

export type ReflectionTexture =
  | 'tense'
  | 'distant'
  | 'open'
  | 'pressured'
  | 'stuck'
  | 'clear'
  | 'conflicted'
  | 'softer';

export type ReflectionSource = 'life_tab' | 'people' | 'mirror' | 'other';

const LABEL_DISPLAY: Record<ReflectionLabel, string> = {
  lands:        'That lands',
  familiar:     'Familiar',
  resisting:    'Resisting',
  true_lately:  'True lately',
  not_sure:     'Not sure',
  changed:      'Changed',
  less_intense: 'Less intense',
};

const TEXTURE_DISPLAY: Record<ReflectionTexture, string> = {
  tense:      'tense',
  distant:    'distant',
  open:       'open',
  pressured:  'pressured',
  stuck:      'stuck',
  clear:      'clear',
  conflicted: 'conflicted',
  softer:     'softer',
};

const LABELS: ReflectionLabel[] = [
  'lands', 'familiar', 'resisting', 'true_lately',
  'not_sure', 'changed', 'less_intense',
];

const TEXTURES: ReflectionTexture[] = [
  'tense', 'distant', 'open', 'pressured',
  'stuck', 'clear', 'conflicted', 'softer',
];

// Tiny acknowledgements after a tap — soft, non-rewarding.
const POST_TAP_ACKS = [
  'Noted.',
  "I'll hold that.",
  'Something about this seems active.',
];

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** Owner user id (required). */
  userId: string;
  /** Where this bar lives — passed straight through to the API. */
  source: ReflectionSource;
  /**
   * Whether this bar belongs to the *latest* assistant message.
   * When false the bar starts collapsed as a small "Reflect" affordance.
   */
  isLatest: boolean;
  /** Optional chat session id for analytics continuity. */
  sourceSession?: string | null;
  /** Optional message id of the assistant bubble. */
  sourceMessage?: string | null;
  /** Optional snapshot of pattern keys active at this turn. */
  contextPatternKeys?: string[];
  /** Optional lens at this turn (astrology / human_design / …). */
  contextLens?: string | null;
  /** Optional life-tab domain at this turn (relationships / work / self). */
  contextLifeDomain?: string | null;
  /** Optional about-person id at this turn. */
  contextAboutPersonId?: string | null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function MicroReflectionBar({
  userId,
  source,
  isLatest,
  sourceSession,
  sourceMessage,
  contextPatternKeys,
  contextLens,
  contextLifeDomain,
  contextAboutPersonId,
}: Props) {
  const { theme } = useTheme();

  // Older bubbles start collapsed.  Tapping the affordance expands them.
  const [expanded, setExpanded] = useState<boolean>(isLatest);
  // A label was tapped: keep the bar visible (no chips) and offer a
  // texture row + a tiny acknowledgement.
  const [tappedLabel, setTappedLabel] = useState<ReflectionLabel | null>(null);
  const [tappedTexture, setTappedTexture] = useState<ReflectionTexture | null>(null);
  // For optimistic UX: hide the chip row immediately after first tap.
  const [posting, setPosting] = useState<boolean>(false);

  const ack = React.useMemo(
    () => POST_TAP_ACKS[Math.floor(Math.random() * POST_TAP_ACKS.length)],
    // Stable per mount.
    [],
  );

  const post = async (label: ReflectionLabel, texture?: ReflectionTexture) => {
    if (!userId) return;
    setPosting(true);
    try {
      await api.post('/micro-reflection', {
        user_id: userId,
        label,
        texture: texture ?? null,
        source,
        source_session: sourceSession ?? null,
        source_message: sourceMessage ?? null,
        context_pattern_keys: contextPatternKeys ?? [],
        context_lens: contextLens ?? null,
        context_life_domain: contextLifeDomain ?? null,
        context_about_person_id: contextAboutPersonId ?? null,
      });
    } catch {
      // Stay silent — reflection should never disturb the chat.
    } finally {
      setPosting(false);
    }
  };

  const onTapLabel = (label: ReflectionLabel) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setTappedLabel(label);
    void post(label);
  };

  const onTapTexture = (texture: ReflectionTexture) => {
    if (!tappedLabel) return;
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setTappedTexture(texture);
    void post(tappedLabel, texture);
  };

  // ── Collapsed (older assistant bubble) ──────────────────────────────
  if (!expanded) {
    return (
      <TouchableOpacity
        onPress={() => {
          LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
          setExpanded(true);
        }}
        hitSlop={8}
        accessibilityRole="button"
        accessibilityLabel="Reflect on this"
        style={styles.collapsedRow}
      >
        <Text style={[styles.collapsedDot, { color: theme.textTertiary }]}>·</Text>
        <Text style={[styles.collapsedText, { color: theme.textTertiary }]}>Reflect</Text>
      </TouchableOpacity>
    );
  }

  // ── Expanded: 3 sub-states  ─────────────────────────────────────────
  // 1. No tap yet  → chip row.
  // 2. Tapped a label → tiny ack + optional texture row.
  // 3. Tapped a texture → final tiny ack + nothing more.

  if (!tappedLabel) {
    return (
      <View style={styles.wrap}>
        <View style={styles.chipRow}>
          {LABELS.map((l) => (
            <TouchableOpacity
              key={l}
              activeOpacity={0.7}
              disabled={posting}
              onPress={() => onTapLabel(l)}
              accessibilityRole="button"
              accessibilityLabel={`Reflect: ${LABEL_DISPLAY[l]}`}
              style={[
                styles.chip,
                { borderColor: theme.border, backgroundColor: theme.surface },
              ]}
            >
              <Text style={[styles.chipText, { color: theme.textSecondary }]}>
                {LABEL_DISPLAY[l]}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );
  }

  // tappedLabel set
  return (
    <View style={styles.wrap}>
      <Text style={[styles.ackText, { color: theme.textTertiary }]}>
        {tappedTexture ? ack : ack}
      </Text>
      {!tappedTexture && (
        <>
          <Text style={[styles.textureHint, { color: theme.textTertiary }]}>
            Any texture to this? (optional)
          </Text>
          <View style={styles.textureRow}>
            {TEXTURES.map((t) => (
              <TouchableOpacity
                key={t}
                activeOpacity={0.7}
                disabled={posting}
                onPress={() => onTapTexture(t)}
                accessibilityRole="button"
                accessibilityLabel={`Texture: ${TEXTURE_DISPLAY[t]}`}
                style={[
                  styles.textureChip,
                  { borderColor: theme.border },
                ]}
              >
                <Text style={[styles.textureChipText, { color: theme.textTertiary }]}>
                  {TEXTURE_DISPLAY[t]}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </>
      )}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles — emotionally quiet, softer than buttons.
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  wrap: {
    marginTop: 8,
    gap: 6,
  },

  // Collapsed mode
  collapsedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 6,
    paddingVertical: 4,
  },
  collapsedDot: { fontSize: 16, lineHeight: 16, opacity: 0.5 },
  collapsedText: {
    fontSize: 11,
    fontStyle: 'italic',
    opacity: 0.7,
    letterSpacing: 0.3,
  },

  // Label chip row
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  chip: {
    paddingHorizontal: 11,
    paddingVertical: 5.5,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
    opacity: 0.85,
  },
  chipText: {
    fontSize: 11.5,
    letterSpacing: 0.2,
    fontWeight: '500',
  },

  // Post-tap ack
  ackText: {
    fontSize: 12,
    fontStyle: 'italic',
    letterSpacing: 0.3,
  },
  textureHint: {
    fontSize: 10.5,
    letterSpacing: 0.2,
    fontStyle: 'italic',
    opacity: 0.7,
    marginTop: 2,
  },
  textureRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
  },
  textureChip: {
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
    opacity: 0.7,
  },
  textureChipText: {
    fontSize: 11,
    letterSpacing: 0.2,
  },
});
