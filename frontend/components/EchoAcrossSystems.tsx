/**
 * EchoAcrossSystems
 * =================
 * Build marker: cross-lens-atoms-v1
 *
 * Surfaces the Cross-Lens Synthesis V1 atoms (currently only the
 * "Certainty Pattern") on the Lifeline tab, directly below the daily
 * Phase Timeline card.
 *
 * Architectural rules (load-bearing):
 *   - Live compute via /api/synthesis/atoms/{userId}. No caching here.
 *   - If the API returns no atoms, this component renders NOTHING.
 *     It must never claim a pattern that didn't fully match.
 *   - Tone: recognition-first ("You tend to..."), never framework-first.
 *   - The framework labels ("Defined Ajna", "Gate 4", "Mercury Square
 *     Saturn", "Life Path 7") live INSIDE the collapsible "Why this
 *     pattern?" section — never in the recognition line.
 */
import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';

export interface AtomSignal {
  lens: string;
  label: string;
  evidence: string;
}

export interface CrossLensAtom {
  atom_id: string;
  name: string;
  framing: string;
  recognition: string;
  signals: AtomSignal[];
  matched: number;
  required: number;
  match_mode: string;
}

interface AtomsResponse {
  success: boolean;
  data_mode: string;
  build_marker: string;
  atoms: CrossLensAtom[];
  atom_count: number;
}

interface Props {
  userId: string;
}

const LENS_ICON: Record<string, keyof typeof Ionicons.glyphMap> = {
  'Human Design': 'shapes-outline',
  'Astrology':    'planet-outline',
  'Numerology':   'calculator-outline',
};

export default function EchoAcrossSystems({ userId }: Props) {
  const { theme } = useTheme();
  const [loading, setLoading] = useState<boolean>(true);
  const [atoms, setAtoms] = useState<CrossLensAtom[] | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    (async () => {
      try {
        const resp = await api.get<AtomsResponse>(`/synthesis/atoms/${userId}`);
        if (cancelled) return;
        setAtoms(resp.data?.atoms || []);
      } catch (err) {
        // Silent failure — synthesis is additive, never blocks Lifeline.
        if (!cancelled) setAtoms([]);
        // eslint-disable-next-line no-console
        console.warn('[EchoAcrossSystems] load failed:', err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  // Show nothing while loading (avoid layout jump) and when no atoms match.
  if (loading) return null;
  if (!atoms || atoms.length === 0) return null;

  const toggle = (atomId: string) => {
    setExpanded((s) => ({ ...s, [atomId]: !s[atomId] }));
  };

  return (
    <View style={[styles.wrap, { borderColor: theme.border, backgroundColor: theme.surface }]}>
      <View style={styles.header}>
        <View style={[styles.iconCircle, { backgroundColor: theme.background, borderColor: theme.border }]}>
          <Ionicons name="git-merge-outline" size={16} color={theme.text} />
        </View>
        <View style={styles.headerText}>
          <Text style={[styles.title, { color: theme.text }]}>Echo Across Systems</Text>
          <Text style={[styles.subtitle, { color: theme.textTertiary }]}>
            Where different systems point to the same thing
          </Text>
        </View>
      </View>

      {atoms.map((atom) => {
        const isOpen = !!expanded[atom.atom_id];
        return (
          <View key={atom.atom_id} style={[styles.atomCard, { borderTopColor: theme.border }]}>
            <Text style={[styles.atomName, { color: theme.textSecondary }]}>{atom.name}</Text>
            <Text style={[styles.recognition, { color: theme.text }]}>{atom.recognition}</Text>

            <TouchableOpacity
              activeOpacity={0.7}
              onPress={() => toggle(atom.atom_id)}
              hitSlop={8}
              style={styles.whyRow}
            >
              <Text style={[styles.whyLabel, { color: theme.textTertiary }]}>
                {isOpen ? 'Hide the systems' : `Why this pattern? (${atom.matched}/${atom.required} systems)`}
              </Text>
              <Ionicons
                name={isOpen ? 'chevron-up' : 'chevron-down'}
                size={14}
                color={theme.textTertiary}
              />
            </TouchableOpacity>

            {isOpen && (
              <View style={styles.signalsList}>
                {atom.signals.map((sig, idx) => {
                  const icon = LENS_ICON[sig.lens] || 'ellipse-outline';
                  return (
                    <View key={`${atom.atom_id}-${idx}`} style={styles.signalRow}>
                      <View style={[styles.signalIcon, { borderColor: theme.border }]}>
                        <Ionicons name={icon} size={12} color={theme.textSecondary} />
                      </View>
                      <View style={styles.signalBody}>
                        <Text style={[styles.signalLens, { color: theme.textTertiary }]}>
                          {sig.lens.toUpperCase()} · {sig.label}
                        </Text>
                        <Text style={[styles.signalEvidence, { color: theme.textSecondary }]}>
                          {sig.evidence}
                        </Text>
                      </View>
                    </View>
                  );
                })}
              </View>
            )}
          </View>
        );
      })}
    </View>
  );
}

// Exported only so tests / Storybook can render the same loading shape.
export const _EchoAcrossSystemsLoading = ({ color }: { color: string }) => (
  <View style={styles.loading}>
    <ActivityIndicator size="small" color={color} />
  </View>
);

const styles = StyleSheet.create({
  wrap: {
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 14,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  iconCircle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerText: {
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 11,
    marginTop: 1,
  },
  atomCard: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  atomName: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1.1,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  recognition: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '500',
  },
  whyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 12,
    paddingVertical: 4,
  },
  whyLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  signalsList: {
    marginTop: 4,
    gap: 10,
  },
  signalRow: {
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
  },
  signalIcon: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  signalBody: {
    flex: 1,
  },
  signalLens: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.8,
    marginBottom: 2,
  },
  signalEvidence: {
    fontSize: 13,
    lineHeight: 19,
  },
  loading: {
    paddingVertical: 8,
    alignItems: 'center',
  },
});
