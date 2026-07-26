// ============================================================================
// ConstellationOverlayCard
// ----------------------------------------------------------------------------
// SECONDARY sky-observation layer — Ophiuchus-aware.
// This is NOT a 13-sign zodiac. It's a collapsible layer on top of the
// existing 12-sign True Sidereal identity frame.
//
// Data contract (from /api/astrology/constellations/{user_id} OR
// fullChartData.natal.constellations):
//   {
//     version: "iau_1930_v1",
//     bodies: {
//        Sun: { constellation, glyph, zodiac_sign, divergent, tropical_longitude },
//        ...
//     },
//     summary: { sun_constellation, moon_constellation, ascendant_constellation, mc_constellation },
//     ophiuchus_bodies: ["Ascendant", ...],
//     has_ophiuchus: bool,
//     overlay_narrative: string | null
//   }
// ============================================================================

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import api from '../../services/api';

interface BodyOverlay {
  constellation: string;
  glyph?: string;
  zodiac_sign?: string | null;
  divergent?: boolean;
  tropical_longitude?: number;
}

interface NarrativeItem {
  body: string;
  zodiac_sign: string;
  constellation: string;
  recognition: string;
  tension: string;
  reality_layer: string;
  how_this_shows_up: string[];
  the_shift: string;
}

interface OverlayNarrativeV2 {
  version?: string;
  items: NarrativeItem[];
}

interface ConstellationOverlay {
  version: string;
  bodies: Record<string, BodyOverlay>;
  summary: {
    sun_constellation?: string | null;
    moon_constellation?: string | null;
    ascendant_constellation?: string | null;
    mc_constellation?: string | null;
  };
  ophiuchus_bodies: string[];
  has_ophiuchus: boolean;
  overlay_narrative?: string | null;
  overlay_narrative_v2?: OverlayNarrativeV2 | null;
}

interface Props {
  userId: string;
  theme: any;
  // Optional: pass pre-loaded overlay (from /astrology/chart) to avoid
  // a second request. When absent, the card will fetch from
  // /astrology/constellations/{userId}.
  overlay?: ConstellationOverlay | null;
}

// Ordered list of bodies we surface in the table — matches Mirror's existing
// ordering conventions. Any body present in `overlay.bodies` but not listed
// here is appended after.
const PRIMARY_BODY_ORDER = [
  'Sun',
  'Moon',
  'Ascendant',
  'Midheaven',
  'Mercury',
  'Venus',
  'Mars',
  'Jupiter',
  'Saturn',
  'Uranus',
  'Neptune',
  'Pluto',
  'Chiron',
  'North Node',
  'South Node',
];

const ConstellationOverlayCard: React.FC<Props> = ({ userId, theme, overlay: preloaded }) => {
  const [overlay, setOverlay] = useState<ConstellationOverlay | null>(preloaded ?? null);
  const [loading, setLoading] = useState<boolean>(!preloaded);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<boolean>(false);

  useEffect(() => {
    if (preloaded) {
      setOverlay(preloaded);
      setLoading(false);
      return;
    }
    if (!userId) return;

    let cancelled = false;
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await api.get(`/astrology/constellations/${userId}`);
        if (cancelled) return;
        if (res.data?.success && res.data?.overlay) {
          setOverlay(res.data.overlay);
        } else {
          setError('Sky view unavailable');
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || 'Sky view unavailable');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [userId, preloaded]);

  if (loading) {
    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.headerRow}>
          <Text style={[styles.headerLabel, { color: theme.textTertiary }]}>SKY VIEW</Text>
          <ActivityIndicator size="small" color={theme.textTertiary} />
        </View>
      </View>
    );
  }

  if (error || !overlay || Object.keys(overlay.bodies || {}).length === 0) {
    // Quietly hide if the overlay is unavailable — it's a secondary layer.
    return null;
  }

  const hasOphiuchus = !!overlay.has_ophiuchus;
  const ophiBodies = overlay.ophiuchus_bodies || [];

  // Subtle teaser line — visible when collapsed, communicates that there's
  // something to see without forcing the user to expand.
  const teaserLine = hasOphiuchus
    ? `${ophiBodies.length === 1 ? ophiBodies[0] : `${ophiBodies.length} bodies`} passing through Ophiuchus in the actual sky`
    : 'How your placements map to the actual IAU constellations';

  // Ordered list of body rows
  const bodyKeys = [
    ...PRIMARY_BODY_ORDER.filter((k) => overlay.bodies[k]),
    ...Object.keys(overlay.bodies).filter((k) => !PRIMARY_BODY_ORDER.includes(k)),
  ];

  return (
    <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <TouchableOpacity
        onPress={() => setExpanded((v) => !v)}
        activeOpacity={0.7}
        style={styles.headerRow}
      >
        <View style={{ flex: 1 }}>
          <Text style={[styles.headerLabel, { color: theme.textTertiary }]}>
            SKY VIEW · CONSTELLATION OVERLAY
          </Text>
          <Text style={[styles.headerTeaser, { color: theme.textSecondary }]}>
            {teaserLine}
          </Text>
          <Text style={[styles.headerSubtle, { color: theme.textTertiary }]}>
            Secondary layer · the 12-sign True Sidereal frame is unchanged.
          </Text>
        </View>
        <Text style={[styles.chevron, { color: theme.textTertiary }]}>
          {expanded ? '▾' : '▸'}
        </Text>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.body}>
          {/* Per-body structured narratives — each Ophiuchus placement gets
              its own full 5-section block. Body-aware, sharp, lived. */}
          {hasOphiuchus && overlay.overlay_narrative_v2?.items?.length ? (
            overlay.overlay_narrative_v2.items.map((item, itemIdx) => (
              <View
                key={`${item.body}-${itemIdx}`}
                style={[
                  styles.narrativeBox,
                  { backgroundColor: theme.background, borderColor: theme.border },
                  itemIdx > 0 && { marginTop: 10 },
                ]}
              >
                {/* Body heading — only shown when there are multiple
                    Ophiuchus placements, to keep single-body view clean. */}
                {overlay.overlay_narrative_v2!.items.length > 1 ? (
                  <Text
                    style={[
                      styles.bodyHeading,
                      { color: theme.accent || theme.text },
                    ]}
                  >
                    {item.body} · {item.zodiac_sign} → Ophiuchus
                  </Text>
                ) : null}

                {/* 1. RECOGNITION */}
                <Text style={[styles.sectionLabel, { color: theme.accent || theme.textSecondary }]}>
                  RECOGNITION
                </Text>
                <Text style={[styles.narrativeText, { color: theme.text }]}>
                  {item.recognition}
                </Text>

                {/* 2. TENSION */}
                <Text style={[styles.sectionLabel, { color: theme.accent || theme.textSecondary }]}>
                  TENSION
                </Text>
                <Text style={[styles.narrativeText, { color: theme.text }]}>
                  {item.tension}
                </Text>

                {/* 3. REALITY LAYER */}
                <Text style={[styles.sectionLabel, { color: theme.accent || theme.textSecondary }]}>
                  REALITY LAYER
                </Text>
                <Text style={[styles.narrativeText, { color: theme.textSecondary }]}>
                  In the symbolic system, this reads as{' '}
                  <Text style={{ color: theme.text, fontWeight: '500' }}>{item.zodiac_sign}</Text>
                  .
                </Text>
                <Text
                  style={[
                    styles.narrativeText,
                    { color: theme.textSecondary, marginTop: 4 },
                  ]}
                >
                  But in the actual sky,{' '}
                  <Text style={{ color: theme.text, fontWeight: '500' }}>{item.body}</Text> is moving
                  through{' '}
                  <Text style={{ color: theme.accent || '#8B5CF6', fontWeight: '500' }}>
                    {item.constellation}
                  </Text>{' '}
                  — a region that doesn't follow the same clean boundaries.
                </Text>

                {/* 4. HOW THIS SHOWS UP */}
                <Text style={[styles.sectionLabel, { color: theme.accent || theme.textSecondary }]}>
                  HOW THIS SHOWS UP
                </Text>
                <Text
                  style={[styles.narrativeText, { color: theme.textSecondary, marginBottom: 4 }]}
                >
                  You may:
                </Text>
                {item.how_this_shows_up.map((b, bIdx) => (
                  <View key={bIdx} style={styles.bulletRow}>
                    <Text style={[styles.bullet, { color: theme.textTertiary }]}>•</Text>
                    <Text style={[styles.bulletText, { color: theme.textSecondary }]}>{b}</Text>
                  </View>
                ))}

                {/* 5. THE SHIFT */}
                <Text style={[styles.sectionLabel, { color: theme.accent || theme.textSecondary }]}>
                  THE SHIFT
                </Text>
                <Text style={[styles.narrativeText, { color: theme.text, fontStyle: 'italic' }]}>
                  {item.the_shift}
                </Text>
              </View>
            ))
          ) : null}

          {/* Body → constellation table */}
          <View style={styles.table}>
            <View style={[styles.tableHeader, { borderBottomColor: theme.border }]}>
              <Text style={[styles.th, styles.colBody, { color: theme.textTertiary }]}>Body</Text>
              <Text style={[styles.th, styles.colZodiac, { color: theme.textTertiary }]}>
                12-Sign
              </Text>
              <Text style={[styles.th, styles.colCon, { color: theme.textTertiary }]}>
                IAU Constellation
              </Text>
            </View>
            {bodyKeys.map((name) => {
              const b = overlay.bodies[name];
              if (!b) return null;
              const isOphi = b.constellation === 'Ophiuchus';
              return (
                <View key={name} style={styles.tr}>
                  <Text style={[styles.td, styles.colBody, { color: theme.text }]} numberOfLines={1}>
                    {name}
                  </Text>
                  <Text style={[styles.td, styles.colZodiac, { color: theme.textSecondary }]} numberOfLines={1}>
                    {b.zodiac_sign || '—'}
                  </Text>
                  <Text
                    style={[
                      styles.td,
                      styles.colCon,
                      {
                        color: isOphi ? theme.accent || '#8B5CF6' : theme.text,
                        fontWeight: isOphi ? '700' : (b.divergent ? '600' : '400'),
                      },
                    ]}
                    numberOfLines={1}
                  >
                    {b.glyph ? `${b.glyph} ` : ''}{b.constellation}
                    {isOphi ? ' ⟵' : ''}
                  </Text>
                </View>
              );
            })}
          </View>

          <Text style={[styles.footerNote, { color: theme.textTertiary }]}>
            IAU 1930 (Delporte) constellation boundaries, projected onto the
            ecliptic. Ophiuchus is not a 13th sign — just a constellation the
            Sun's path crosses between Scorpius and Sagittarius.
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  headerTeaser: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '500',
  },
  headerSubtle: {
    fontSize: 12,
    marginTop: 2,
    fontStyle: 'italic',
  },
  chevron: {
    fontSize: 18,
    marginLeft: 8,
    width: 16,
    textAlign: 'center',
  },
  body: {
    marginTop: 12,
    gap: 12,
  },
  narrativeBox: {
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
  },
  bodyHeading: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.4,
    marginBottom: 2,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1.0,
    marginTop: 14,
    marginBottom: 6,
  },
  realityLayer: {
    marginTop: 2,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 4,
    gap: 8,
  },
  bullet: {
    fontSize: 14,
    lineHeight: 20,
    marginRight: 0,
  },
  bulletText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  narrativeText: {
    fontSize: 14,
    lineHeight: 21,
  },
  table: {
    gap: 2,
  },
  tableHeader: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    paddingBottom: 6,
    marginBottom: 4,
  },
  th: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  tr: {
    flexDirection: 'row',
    paddingVertical: 5,
  },
  td: {
    fontSize: 13,
  },
  colBody: {
    flex: 1.1,
  },
  colZodiac: {
    flex: 1,
  },
  colCon: {
    flex: 1.4,
  },
  footerNote: {
    fontSize: 11,
    fontStyle: 'italic',
    lineHeight: 16,
    marginTop: 4,
  },
});

export default ConstellationOverlayCard;
