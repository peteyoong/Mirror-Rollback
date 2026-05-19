/**
 * EvidenceDrawer — "Why this is showing up"
 * =========================================
 *
 * Build marker: evidence-drawer-v2
 *
 * Calm, optional, progressive-disclosure UI that explains where an
 * insight came from — WITHOUT collapsing the chat into framework soup
 * or dashboard overload.
 *
 * Renders the curated `evidence` object returned by
 * `POST /api/mirror/chat` (NOT the raw `debug` payload).  Backend already
 * stripped jargon and translated framework signals to plain language —
 * this component just lays them out quietly.
 *
 * Usage:
 *   <EvidenceDrawer evidence={lastReply.evidence} />
 *
 * Visual posture:
 *   - Collapsed by default (single subtle row + chevron).
 *   - Expanded: dominant pattern → supporting signals → frameworks →
 *     recurrence → relational moderation → calibration.
 *   - Quiet, minimal, no "developer debug UI" feeling.
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

// Enable layout animation on Android.
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// ---------------------------------------------------------------------------
// Types — match the server-side curator shape (services/evidence_curator.py).
// ---------------------------------------------------------------------------

export interface CuratedEvidence {
  marker?: string;
  master_voice?: {
    domain?: string;
    dominant_pattern?: string;
    frameworks?: string[];
  };
  lens?: {
    framework?: string;
    focus?: string;
    focus_kind?: string;
  };
  relational?: {
    moderated_by?: string[];
    applied_intensity?: string;
  };
  recurrence?: string;
  calibration?: string[];
}

interface Props {
  evidence?: CuratedEvidence | null;
  /** Optional title override, e.g. "Why this is showing up" (default). */
  title?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function hasAnythingToShow(e?: CuratedEvidence | null): boolean {
  if (!e) return false;
  if (e.master_voice?.dominant_pattern || (e.master_voice?.frameworks?.length || 0) > 0) return true;
  if (e.lens?.framework) return true;
  if ((e.relational?.moderated_by?.length || 0) > 0) return true;
  if (e.recurrence) return true;
  if ((e.calibration?.length || 0) > 0) return true;
  return false;
}

function capitalizeFirst(s: string): string {
  if (!s) return s;
  return s[0].toUpperCase() + s.slice(1);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EvidenceDrawer({ evidence, title }: Props) {
  const { theme } = useTheme();
  const [expanded, setExpanded] = useState(false);

  if (!hasAnythingToShow(evidence)) return null;
  const e = evidence as CuratedEvidence;

  const onToggle = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded((v) => !v);
  };

  return (
    <View style={[styles.wrap, { borderColor: theme.border }]}>
      <TouchableOpacity
        onPress={onToggle}
        activeOpacity={0.7}
        accessibilityRole="button"
        accessibilityLabel={expanded ? 'Hide evidence' : 'Why this is showing up'}
        style={styles.header}
      >
        <Text style={[styles.headerText, { color: theme.textSecondary }]}>
          {title || 'Why this is showing up'}
        </Text>
        <Text style={[styles.chevron, { color: theme.textTertiary }]}>
          {expanded ? '▾' : '▸'}
        </Text>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.body}>
          {/* Dominant pattern (from Life Tab master voice). ----------------- */}
          {e.master_voice?.dominant_pattern && (
            <View style={styles.section}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                What this response is drawing on
              </Text>
              <Text style={[styles.dominantLine, { color: theme.text }]}>
                {capitalizeFirst(e.master_voice.dominant_pattern)}
              </Text>
            </View>
          )}

          {/* Single-lens focus (e.g. "Astrology · Sun"). ----------------- */}
          {e.lens?.framework && (
            <View style={styles.section}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                Lens
              </Text>
              <Text style={[styles.sectionLine, { color: theme.text }]}>
                {e.lens.framework}
                {e.lens.focus ? ` · ${e.lens.focus}` : ''}
              </Text>
            </View>
          )}

          {/* Framework attribution chips — only when 1+ contributing. ----- */}
          {e.master_voice?.frameworks && e.master_voice.frameworks.length > 0 && (
            <View style={styles.section}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                Interpretive sources
              </Text>
              <View style={styles.chipRow}>
                {e.master_voice.frameworks.map((f) => (
                  <View
                    key={f}
                    style={[
                      styles.chip,
                      { borderColor: theme.border, backgroundColor: theme.surface },
                    ]}
                  >
                    <Text style={[styles.chipText, { color: theme.textSecondary }]}>{f}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Soft recurrence line. -------------------------------------- */}
          {e.recurrence && (
            <View style={styles.section}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                A pattern over time
              </Text>
              <Text style={[styles.sectionLine, { color: theme.text }]}>
                {capitalizeFirst(e.recurrence)}.
              </Text>
            </View>
          )}

          {/* Relational moderation — only for Ask-about-person chats. --- */}
          {e.relational?.moderated_by && e.relational.moderated_by.length > 0 && (
            <View style={styles.section}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                Relational tone
              </Text>
              <Text style={[styles.sectionLine, { color: theme.text }]}>
                This response was tuned for {e.relational.moderated_by.join('; ')}.
              </Text>
            </View>
          )}

          {/* Calibration tags. ---------------------------------------- */}
          {e.calibration && e.calibration.length > 0 && (
            <View style={styles.section}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                Tone & depth
              </Text>
              <View style={styles.chipRow}>
                {e.calibration.map((c) => (
                  <View
                    key={c}
                    style={[
                      styles.chip,
                      { borderColor: theme.border, backgroundColor: 'transparent' },
                    ]}
                  >
                    <Text style={[styles.chipText, { color: theme.textTertiary }]}>{c}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Subtle footer reminder — not certainty. ------------------- */}
          <Text style={[styles.footnote, { color: theme.textTertiary }]}>
            Recognition, not verdict. Patterns shift; people are not single threads.
          </Text>
        </View>
      )}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles — quiet, hairline borders, no shadows, no chrome.
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  wrap: {
    marginTop: 6,
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 6,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 6,
    paddingHorizontal: 4,
  },
  headerText: {
    fontSize: 12,
    letterSpacing: 0.3,
    fontStyle: 'italic',
  },
  chevron: {
    fontSize: 14,
    fontWeight: '500',
  },
  body: {
    paddingTop: 4,
    paddingBottom: 8,
    paddingHorizontal: 4,
    gap: 10,
  },
  section: {
    gap: 4,
  },
  sectionLabel: {
    fontSize: 10,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  sectionLine: {
    fontSize: 13.5,
    lineHeight: 19,
  },
  dominantLine: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '500',
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 2,
  },
  chip: {
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  chipText: {
    fontSize: 11,
    letterSpacing: 0.2,
  },
  footnote: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 4,
    lineHeight: 16,
  },
});
