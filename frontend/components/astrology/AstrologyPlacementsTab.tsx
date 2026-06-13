// ============================================
// ASTROLOGY PLACEMENTS TAB
// Complete natal map: every planet, node, angle with sign / house / degree / retrograde.
// Forward-build of a previously-shipped feature (Variant A canonical, 13 signs incl. Ophiuchus).
// MARKER: placements-tab-v1
// ============================================

import React from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';

import { FullChartData, CorePlacements, PlanetData } from '../../services/astrology/astrologyTypes';

// Runtime build markers — referenced in the rendered tree below so they survive
// production minification (Metro's dead-code-elimination strips JS comments).
// Future forensic bundle-greps (placements-tab-v1, AstrologyPlacementsTab) hit these strings.
const BUILD_MARKER = 'placements-tab-v1';
const COMPONENT_MARKER = 'AstrologyPlacementsTab';

// ============================================
// PROPS
// ============================================

interface AstrologyPlacementsTabProps {
  placements: CorePlacements;
  fullChartData: FullChartData | null;
  theme: any;
  onOpenDeepDive?: (planetKey: string) => void;
}

// ============================================
// STATIC LOOKUPS
// ============================================

// Unicode glyphs for planets, nodes, angles. Plain ASCII fallback used inline for angles
// where Unicode astrological glyphs render inconsistently across web/native.
const GLYPH: Record<string, string> = {
  Sun: '☉',
  Moon: '☽',
  Ascendant: '↑',
  Mercury: '☿',
  Venus: '♀',
  Mars: '♂',
  Jupiter: '♃',
  Saturn: '♄',
  Uranus: '♅',
  Neptune: '♆',
  Pluto: '♇',
  'North Node': '☊',
  'South Node': '☋',
  Chiron: '⚷',
  MC: 'MC',
  IC: 'IC',
  DC: 'DC',
};

// Sign trait keyword pairs (Variant A canonical, 13 signs including Ophiuchus).
// Two-word descriptors keep cards scannable. Lowercase by intent — UI matches screenshot.
const SIGN_TRAITS: Record<string, [string, string]> = {
  Aries:       ['Initiating', 'direct'],
  Taurus:      ['Grounded', 'steady'],
  Gemini:      ['Curious', 'adaptive'],
  Cancer:      ['Tender', 'protective'],
  Leo:         ['Radiant', 'expressive'],
  Virgo:       ['Refining', 'discerning'],
  Libra:       ['Relational', 'harmonising'],
  Scorpio:     ['Probing', 'transformative'],
  Ophiuchus:   ['Healing', 'truth-seeking'],
  Sagittarius: ['Expansive', 'truth-seeking'],
  Capricorn:   ['Disciplined', 'enduring'],
  Aquarius:    ['Independent', 'visionary'],
  Pisces:      ['Imaginative', 'empathic'],
};

// Display name overrides (Ascendant is shown as "Rising (Ascendant)" per screenshot)
const DISPLAY_NAME: Record<string, string> = {
  Ascendant: 'Rising (Ascendant)',
};

// Section definitions. Each entry: section header + ordered list of placement keys.
// Keys map into either fullChartData.natal.planets or .nodes or .angles or
// a synthetic "Ascendant" entry assembled from angles.asc.
type SectionDef = { header: string; keys: string[] };

const SECTIONS: SectionDef[] = [
  { header: 'CORE IDENTITY',     keys: ['Sun', 'Moon', 'Ascendant'] },
  { header: 'PERSONAL PLANETS',  keys: ['Mercury', 'Venus', 'Mars'] },
  { header: 'SOCIAL PLANETS',    keys: ['Jupiter', 'Saturn'] },
  { header: 'OUTER PLANETS',     keys: ['Uranus', 'Neptune', 'Pluto'] },
  { header: 'NODES & POINTS',    keys: ['North Node', 'South Node', 'Chiron'] },
  { header: 'ANGLES',            keys: ['MC', 'IC', 'DC'] },
];

// ============================================
// HELPERS
// ============================================

const isFiniteNumber = (v: any): v is number => typeof v === 'number' && Number.isFinite(v);

const formatDegree = (deg: number | undefined): string => {
  if (!isFiniteNumber(deg)) return '';
  // Two-decimal display (matches screenshot: 22.25°, 11.31°, 26.92°, 0.81°)
  return `${deg.toFixed(2)}°`;
};

// Extract a PlanetData-shaped record for a given key from FullChartData.
// Returns null when the chart is missing the placement.
const extractPlacement = (
  key: string,
  full: FullChartData | null,
): (PlanetData & { _label: string }) | null => {
  if (!full || !full.natal) return null;
  const natal = full.natal as any;

  // Angles
  if (key === 'Ascendant') {
    const a = natal.angles?.asc;
    return a ? { ...a, _label: DISPLAY_NAME.Ascendant } : null;
  }
  if (key === 'MC' || key === 'IC' || key === 'DC') {
    const a = natal.angles?.[key.toLowerCase()];
    return a ? { ...a, _label: key } : null;
  }

  // Nodes — prefer natal.planets entry (some charts denormalize it), then natal.nodes
  if (key === 'North Node') {
    const p = natal.planets?.['North Node'] ?? natal.nodes?.north;
    return p ? { ...p, _label: 'North Node' } : null;
  }
  if (key === 'South Node') {
    const p = natal.planets?.['South Node'] ?? natal.nodes?.south;
    return p ? { ...p, _label: 'South Node' } : null;
  }

  // Standard planets
  const p = natal.planets?.[key];
  return p ? { ...p, _label: key } : null;
};

// ============================================
// PLACEMENT CARD
// ============================================

const PlacementCard: React.FC<{
  placementKey: string;
  data: PlanetData & { _label: string };
  theme: any;
  onOpenDeepDive?: (planetKey: string) => void;
  isAngle: boolean;
}> = ({ placementKey, data, theme, onOpenDeepDive, isAngle }) => {
  const sign = data.sign || 'Unknown';
  const houseLabel = isFiniteNumber(data.house) && data.house > 0 ? `House ${data.house}` : null;
  const degreeLabel = formatDegree(data.degree);
  const retro = data.retrograde === true;
  const traits = SIGN_TRAITS[sign];
  const traitLine = traits ? `${traits[0]} · ${traits[1]}` : null;

  // Build the meta line: "Sign · House N · DD.DD°" — drop houseLabel for angles when missing.
  const metaParts: string[] = [];
  if (sign) metaParts.push(sign);
  if (houseLabel && !isAngle) metaParts.push(houseLabel);
  if (degreeLabel) metaParts.push(degreeLabel);
  if (retro) metaParts.push('℞ Retrograde');

  return (
    <View
      style={[
        styles.card,
        { backgroundColor: theme.surface, borderColor: theme.border },
      ]}
    >
      <View style={styles.cardHeader}>
        <Text style={[styles.glyph, { color: theme.text }]}>
          {GLYPH[placementKey] || ''}
        </Text>
        <Text style={[styles.cardTitle, { color: theme.text }]}>
          {data._label}
        </Text>
      </View>

      <View style={styles.metaRow}>
        {metaParts.map((part, idx) => (
          <React.Fragment key={`${placementKey}-meta-${idx}`}>
            {idx > 0 && (
              <Text style={[styles.metaDot, { color: theme.textTertiary }]}>·</Text>
            )}
            <Text style={[styles.metaText, { color: theme.textSecondary }]}>
              {part}
            </Text>
          </React.Fragment>
        ))}
      </View>

      {traitLine ? (
        <Text style={[styles.traitText, { color: theme.textTertiary }]}>
          {traitLine}
        </Text>
      ) : null}

      {onOpenDeepDive ? (
        <TouchableOpacity
          accessibilityRole="button"
          accessibilityLabel={`Open deep dive for ${data._label}`}
          onPress={() => onOpenDeepDive(placementKey)}
          style={styles.deepDiveButton}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Text style={[styles.deepDiveText, { color: theme.textSecondary }]}>
            Open deep dive
          </Text>
        </TouchableOpacity>
      ) : null}
    </View>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

const AstrologyPlacementsTab: React.FC<AstrologyPlacementsTabProps> = ({
  placements,
  fullChartData,
  theme,
  onOpenDeepDive,
}) => {
  // DEFENSIVE GUARDS
  const safeFull = fullChartData && typeof fullChartData === 'object' ? fullChartData : null;
  const safeCore = placements && typeof placements === 'object' ? placements : ({} as CorePlacements);

  // If we have no chart at all, fall back to the bare 3-placement summary
  // assembled from CorePlacements (so the page never goes blank).
  const fallbackOnly = !safeFull;

  // Empty state
  if (!safeFull && (!safeCore.sun || safeCore.sun === 'Unknown') &&
      (!safeCore.moon || safeCore.moon === 'Unknown') &&
      (!safeCore.ascendant || safeCore.ascendant === 'Unknown')) {
    return (
      <View style={styles.emptyState}>
        <Text style={[styles.emptyTitle, { color: theme.text }]}>Placements</Text>
        <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
          Your natal placements will appear here once your chart is generated.
        </Text>
      </View>
    );
  }

  // ----- Build a fallback PlanetData-like record from CorePlacements (no degree/longitude) -----
  const fallbackPlacement = (
    key: string,
  ): (PlanetData & { _label: string }) | null => {
    const c: any = safeCore;
    const make = (sign: any, house: any, label: string): (PlanetData & { _label: string }) | null =>
      sign
        ? {
            sign: String(sign),
            degree: NaN as any,
            longitude: NaN as any,
            house: isFiniteNumber(house) ? house : 0,
            retrograde: false,
            _label: label,
          }
        : null;

    switch (key) {
      case 'Sun':         return make(c.sun, c.sun_house, 'Sun');
      case 'Moon':        return make(c.moon, c.moon_house, 'Moon');
      case 'Ascendant':   return make(c.ascendant, undefined, DISPLAY_NAME.Ascendant);
      case 'Mercury':     return make(c.mercury, c.mercury_house, 'Mercury');
      case 'Venus':       return make(c.venus, c.venus_house, 'Venus');
      case 'Mars':        return make(c.mars, c.mars_house, 'Mars');
      case 'Jupiter':     return make(c.jupiter, c.jupiter_house, 'Jupiter');
      case 'Saturn':      return make(c.saturn, c.saturn_house, 'Saturn');
      case 'Chiron':      return make(c.chiron, c.chiron_house, 'Chiron');
      case 'North Node':  return make(c.north_node, c.north_node_house, 'North Node');
      case 'South Node':  return make(c.south_node, c.south_node_house, 'South Node');
      default:            return null;
    }
  };

  const resolvePlacement = (key: string) =>
    extractPlacement(key, safeFull) ?? fallbackPlacement(key);

  // ----- Render -----
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
      testID={`${COMPONENT_MARKER}--${BUILD_MARKER}`}
      accessibilityLabel={`${COMPONENT_MARKER} (${BUILD_MARKER})`}
    >
      {/* HEADER */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.text }]}>Placements</Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          Your complete natal map. Tap any placement with a deep dive to explore it.
        </Text>
        <View style={[styles.divider, { backgroundColor: theme.border }]} />
      </View>

      {/* SECTIONS */}
      {SECTIONS.map((section) => {
        const isAngleSection = section.header === 'ANGLES' ||
          (section.header === 'CORE IDENTITY' /* asc-only carve-out */);
        const cards = section.keys
          .map((k) => ({ k, data: resolvePlacement(k) }))
          .filter((c) => c.data !== null) as Array<{ k: string; data: PlanetData & { _label: string } }>;

        if (cards.length === 0) return null;

        return (
          <View key={section.header} style={styles.section}>
            <Text style={[styles.sectionHeader, { color: theme.textTertiary }]}>
              {section.header}
            </Text>
            <View style={styles.cardList}>
              {cards.map(({ k, data }) => (
                <PlacementCard
                  key={k}
                  placementKey={k}
                  data={data}
                  theme={theme}
                  onOpenDeepDive={onOpenDeepDive}
                  isAngle={k === 'Ascendant' || k === 'MC' || k === 'IC' || k === 'DC'}
                />
              ))}
            </View>
          </View>
        );
      })}

      {/* HOUSES (cusps) — collapsed-style flat list if data is present */}
      {safeFull?.natal?.houses?.cusps && safeFull.natal.houses.cusps.length > 0 ? (
        <View style={styles.section}>
          <Text style={[styles.sectionHeader, { color: theme.textTertiary }]}>
            HOUSE CUSPS
          </Text>
          <View
            style={[
              styles.cuspCard,
              { backgroundColor: theme.surface, borderColor: theme.border },
            ]}
          >
            {safeFull.natal.houses.cusps.map((cusp, idx) => (
              <View
                key={`cusp-${cusp.house}-${idx}`}
                style={[
                  styles.cuspRow,
                  idx < safeFull.natal.houses.cusps.length - 1 && {
                    borderBottomColor: theme.border,
                    borderBottomWidth: StyleSheet.hairlineWidth,
                  },
                ]}
              >
                <Text style={[styles.cuspHouse, { color: theme.text }]}>
                  House {cusp.house}
                </Text>
                <Text style={[styles.cuspMeta, { color: theme.textSecondary }]}>
                  {cusp.sign} · {formatDegree(cusp.degree)}
                </Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {fallbackOnly ? (
        <Text style={[styles.fallbackNote, { color: theme.textTertiary }]}>
          Showing a partial summary — full chart data is still loading.
        </Text>
      ) : null}
    </ScrollView>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: { flex: 1 },
  contentContainer: { padding: 16, paddingBottom: 40, gap: 20 },

  // Header
  header: { marginBottom: 4 },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 6, letterSpacing: -0.5 },
  subtitle: { fontSize: 15, lineHeight: 22, marginBottom: 16 },
  divider: { height: StyleSheet.hairlineWidth, marginTop: 4 },

  // Section
  section: { gap: 10 },
  sectionHeader: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 4,
  },
  cardList: { gap: 10 },

  // Placement card
  card: {
    borderRadius: 14,
    borderWidth: 1,
    paddingVertical: 14,
    paddingHorizontal: 16,
    gap: 6,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 2,
  },
  glyph: { fontSize: 18, fontWeight: '500', minWidth: 22, textAlign: 'center' },
  cardTitle: { fontSize: 17, fontWeight: '600' },

  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    gap: 6,
  },
  metaDot: { fontSize: 14, marginHorizontal: 2 },
  metaText: { fontSize: 14, fontWeight: '500' },

  traitText: { fontSize: 13, fontStyle: 'italic', marginTop: 2 },

  deepDiveButton: { marginTop: 6, alignSelf: 'flex-start' },
  deepDiveText: { fontSize: 13, fontWeight: '600', letterSpacing: 0.2 },

  // House cusps card
  cuspCard: { borderRadius: 14, borderWidth: 1, paddingHorizontal: 16 },
  cuspRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 11,
  },
  cuspHouse: { fontSize: 14, fontWeight: '600' },
  cuspMeta: { fontSize: 14 },

  // Empty / fallback
  emptyState: {
    flex: 1,
    paddingVertical: 60,
    paddingHorizontal: 24,
    alignItems: 'center',
    gap: 10,
  },
  emptyTitle: { fontSize: 22, fontWeight: '600' },
  emptySubtitle: { fontSize: 15, textAlign: 'center', lineHeight: 22 },

  fallbackNote: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 8,
  },
});

export default AstrologyPlacementsTab;
