import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';
import { useTheme } from '../contexts/ThemeContext';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
} from 'react-native-reanimated';

// API Configuration
const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL 
  || process.env.EXPO_PUBLIC_BACKEND_URL 
  || '';

const getBackendBaseUrl = () => {
  if (typeof window !== 'undefined' && !EXPO_PUBLIC_BACKEND_URL) {
    return '';
  }
  return EXPO_PUBLIC_BACKEND_URL;
};

const BACKEND_BASE_URL = getBackendBaseUrl();

// Types
interface CoreTruth {
  line1: string;
  line2: string;
}

interface CostCategories {
  energy: string;
  relationships: string;
  opportunities: string;
}

interface WhyShowingUp {
  explanation: string;
  pattern_note: string;
}

interface ChartDetails {
  day_master: string;
  day_master_chinese: string;
  strength: string;
  favorable_elements: string[];
  unfavorable_elements: string[];
  pillars?: {
    year: string;
    month: string;
    day: string;
    hour: string;
  };
  dominant_patterns?: string[];
}

interface BaZiInsightData {
  core_truth: CoreTruth;
  how_this_shows_up: string[];
  when_this_backfires: string[];
  what_this_costs_you: CostCategories;
  one_shift: string;
  why_showing_up: WhyShowingUp;
  chart_details: ChartDetails;
}

// =============================================================================
// BAZI DESIGN SYSTEM - Premium, Symbolic, Grounded
// =============================================================================

const BAZI_COLORS = {
  // Primary accent - warm earth tone (represents grounded wisdom)
  gold: '#C9A962',
  goldLight: 'rgba(201, 169, 98, 0.08)',
  goldMedium: 'rgba(201, 169, 98, 0.15)',
  goldStrong: 'rgba(201, 169, 98, 0.25)',
  
  // Element colors (subtle, refined)
  wood: '#7CB08A',
  fire: '#D4836A',
  earth: '#C4A484',
  metal: '#A8B5C4',
  water: '#6B8BA4',
  
  // Semantic (desaturated for elegance)
  subtle: 'rgba(255, 255, 255, 0.06)',
  divider: 'rgba(255, 255, 255, 0.08)',
  muted: 'rgba(255, 255, 255, 0.4)',
};

// Element Icon Mapping
const getElementIcon = (element: string): string => {
  const icons: Record<string, string> = {
    'Wood': 'leaf-outline',
    'Fire': 'flame-outline',
    'Earth': 'globe-outline',
    'Metal': 'diamond-outline',
    'Water': 'water-outline',
  };
  return icons[element] || 'ellipse-outline';
};

const getElementColor = (element: string): string => {
  const colors: Record<string, string> = {
    'Wood': BAZI_COLORS.wood,
    'Fire': BAZI_COLORS.fire,
    'Earth': BAZI_COLORS.earth,
    'Metal': BAZI_COLORS.metal,
    'Water': BAZI_COLORS.water,
  };
  return colors[element] || BAZI_COLORS.gold;
};

// =============================================================================
// PROOF LAYER DISCLOSURE - Elegant collapsible
// =============================================================================

const ProofDisclosure: React.FC<{
  title: string;
  theme: any;
  children: React.ReactNode;
}> = ({ title, theme, children }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const rotation = useSharedValue(0);

  const toggleExpand = () => {
    const newState = !isExpanded;
    setIsExpanded(newState);
    rotation.value = withTiming(newState ? 90 : 0, { duration: 200 });
  };

  const animatedIconStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${rotation.value}deg` }],
  }));

  return (
    <View style={styles.proofContainer}>
      <TouchableOpacity 
        style={styles.proofHeader} 
        onPress={toggleExpand}
        activeOpacity={0.6}
      >
        <Text style={[styles.proofTitle, { color: theme.textTertiary }]}>{title}</Text>
        <Animated.View style={animatedIconStyle}>
          <Ionicons name="chevron-forward" size={14} color={theme.textTertiary} />
        </Animated.View>
      </TouchableOpacity>
      
      {isExpanded && (
        <View style={styles.proofContent}>
          {children}
        </View>
      )}
    </View>
  );
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function BaZiInsightDeepDive({
  userId,
  onOpenChat,
}: {
  userId: string;
  onOpenChat?: () => void;
}) {
  const { theme } = useTheme();
  const [data, setData] = useState<BaZiInsightData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchInsight = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${BACKEND_BASE_URL}/api/bazi/${userId}/insight`);
        const result = await response.json();
        
        if (result.success) {
          setData(result.insight);
        } else {
          setError(result.detail || 'Failed to load BaZi insight');
        }
      } catch (err) {
        setError('Failed to connect to server');
      } finally {
        setLoading(false);
      }
    };

    fetchInsight();
  }, [userId]);

  // Extract element from day master for symbolic accents
  const dayMasterElement = data?.chart_details?.day_master?.split(' ')[1] || 'Metal';
  const elementColor = getElementColor(dayMasterElement);
  const elementIcon = getElementIcon(dayMasterElement);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={BAZI_COLORS.gold} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Reading your pattern...
        </Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={28} color={theme.textTertiary} />
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Could not load insight'}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      
      {/* ================================================================== */}
      {/* HERO SECTION - Core Pattern (dominant visual weight) */}
      {/* ================================================================== */}
      <View style={styles.heroSection}>
        {/* Signature gold accent - top */}
        <View style={[styles.signatureAccent, { backgroundColor: BAZI_COLORS.gold }]} />
        
        {/* Element indicator */}
        <View style={styles.heroHeader}>
          <View style={[styles.elementBadge, { backgroundColor: BAZI_COLORS.goldLight }]}>
            <Ionicons name={elementIcon as any} size={12} color={elementColor} />
            <Text style={[styles.elementBadgeText, { color: elementColor }]}>
              {data.chart_details.day_master_chinese}
            </Text>
          </View>
        </View>
        
        {/* Core recognition */}
        <Text style={[styles.heroLine1, { color: theme.text }]}>
          {data.core_truth.line1}
        </Text>
        <Text style={[styles.heroLine2, { color: theme.textSecondary }]}>
          {data.core_truth.line2}
        </Text>
      </View>

      {/* ================================================================== */}
      {/* PATTERN LAYER - How this shows up + When it backfires */}
      {/* ================================================================== */}
      <View style={styles.patternLayer}>
        {/* How This Shows Up */}
        <View style={styles.patternSection}>
          <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
            HOW THIS SHOWS UP
          </Text>
          <View style={styles.patternList}>
            {data.how_this_shows_up.map((item, index) => (
              <View key={index} style={styles.patternItem}>
                <View style={[styles.patternDot, { backgroundColor: BAZI_COLORS.gold, opacity: 0.4 }]} />
                <Text style={[styles.patternText, { color: theme.textSecondary }]}>{item}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Divider */}
        <View style={[styles.sectionDivider, { backgroundColor: BAZI_COLORS.divider }]} />

        {/* When This Backfires */}
        <View style={styles.patternSection}>
          <Text style={[styles.patternLabel, { color: BAZI_COLORS.fire }]}>
            WHEN THIS BACKFIRES
          </Text>
          <View style={styles.patternList}>
            {data.when_this_backfires.map((item, index) => (
              <View key={index} style={styles.patternItem}>
                <View style={[styles.patternDot, { backgroundColor: BAZI_COLORS.fire, opacity: 0.6 }]} />
                <Text style={[styles.patternText, { color: theme.textSecondary }]}>{item}</Text>
              </View>
            ))}
          </View>
        </View>
      </View>

      {/* ================================================================== */}
      {/* COST LAYER - Lighter treatment */}
      {/* ================================================================== */}
      <View style={styles.costLayer}>
        <Text style={[styles.costHeader, { color: theme.textTertiary }]}>
          WHAT THIS COSTS YOU
        </Text>
        <View style={styles.costGrid}>
          <View style={styles.costItem}>
            <Text style={[styles.costCategory, { color: theme.textTertiary }]}>Energy</Text>
            <Text style={[styles.costValue, { color: theme.textSecondary }]}>
              {data.what_this_costs_you.energy}
            </Text>
          </View>
          <View style={styles.costItem}>
            <Text style={[styles.costCategory, { color: theme.textTertiary }]}>Relationships</Text>
            <Text style={[styles.costValue, { color: theme.textSecondary }]}>
              {data.what_this_costs_you.relationships}
            </Text>
          </View>
          <View style={styles.costItem}>
            <Text style={[styles.costCategory, { color: theme.textTertiary }]}>Opportunities</Text>
            <Text style={[styles.costValue, { color: theme.textSecondary }]}>
              {data.what_this_costs_you.opportunities}
            </Text>
          </View>
        </View>
      </View>

      {/* ================================================================== */}
      {/* SHIFT - Action callout with signature accent */}
      {/* ================================================================== */}
      <View style={styles.shiftWrapper}>
        <View style={[styles.signatureAccent, { backgroundColor: BAZI_COLORS.gold }]} />
        <View style={[styles.shiftSection, { borderLeftColor: BAZI_COLORS.gold }]}>
          <Text style={[styles.shiftLabel, { color: BAZI_COLORS.gold }]}>ONE SHIFT</Text>
          <Text style={[styles.shiftText, { color: theme.text }]}>
            {data.one_shift}
          </Text>
        </View>
      </View>

      {/* ================================================================== */}
      {/* PROOF LAYER - Collapsible disclosures */}
      {/* ================================================================== */}
      <View style={styles.proofLayer}>
        <View style={[styles.proofDivider, { backgroundColor: BAZI_COLORS.divider }]} />
        
        {/* Why This Is Showing Up */}
        <ProofDisclosure title="Why this is showing up" theme={theme}>
          <Text style={[styles.proofText, { color: theme.textSecondary }]}>
            {data.why_showing_up.explanation}
          </Text>
          <Text style={[styles.proofNote, { color: theme.textTertiary }]}>
            {data.why_showing_up.pattern_note}
          </Text>
        </ProofDisclosure>

        {/* Chart Details */}
        <ProofDisclosure title="See your chart details" theme={theme}>
          <View style={styles.chartGrid}>
            <View style={styles.chartRow}>
              <Text style={[styles.chartLabel, { color: theme.textTertiary }]}>Day Master</Text>
              <View style={styles.chartValueRow}>
                <Ionicons name={elementIcon as any} size={14} color={elementColor} />
                <Text style={[styles.chartValue, { color: theme.text }]}>
                  {data.chart_details.day_master_chinese}
                </Text>
              </View>
            </View>
            <View style={styles.chartRow}>
              <Text style={[styles.chartLabel, { color: theme.textTertiary }]}>Strength</Text>
              <Text style={[styles.chartValue, { color: theme.text }]}>
                {data.chart_details.strength}
              </Text>
            </View>
            {data.chart_details.dominant_patterns && data.chart_details.dominant_patterns.length > 0 && (
              <View style={styles.chartRow}>
                <Text style={[styles.chartLabel, { color: theme.textTertiary }]}>Dominant</Text>
                <Text style={[styles.chartValue, { color: theme.text }]}>
                  {data.chart_details.dominant_patterns.join(', ')}
                </Text>
              </View>
            )}
            {data.chart_details.favorable_elements && data.chart_details.favorable_elements.length > 0 && (
              <View style={styles.chartRow}>
                <Text style={[styles.chartLabel, { color: theme.textTertiary }]}>Favorable</Text>
                <View style={styles.elementPills}>
                  {data.chart_details.favorable_elements.map((el, i) => (
                    <View key={i} style={[styles.elementPill, { backgroundColor: BAZI_COLORS.subtle }]}>
                      <Ionicons name={getElementIcon(el) as any} size={10} color={getElementColor(el)} />
                      <Text style={[styles.elementPillText, { color: getElementColor(el) }]}>{el}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
            {data.chart_details.pillars && (
              <View style={styles.pillarsBox}>
                <Text style={[styles.pillarsLabel, { color: theme.textTertiary }]}>Four Pillars</Text>
                <View style={styles.pillarsRow}>
                  {['year', 'month', 'day', 'hour'].map((pillar) => (
                    <View key={pillar} style={styles.pillarItem}>
                      <Text style={[styles.pillarType, { color: theme.textTertiary }]}>
                        {pillar.charAt(0).toUpperCase() + pillar.slice(1)}
                      </Text>
                      <Text style={[styles.pillarValue, { color: theme.textSecondary }]}>
                        {data.chart_details.pillars?.[pillar as keyof typeof data.chart_details.pillars] || '—'}
                      </Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
          </View>
        </ProofDisclosure>
      </View>

      {/* ================================================================== */}
      {/* CTA - Explore with Mirror */}
      {/* ================================================================== */}
      {onOpenChat && (
        <TouchableOpacity
          style={[styles.ctaButton, { backgroundColor: theme.text }]}
          onPress={onOpenChat}
          activeOpacity={0.8}
        >
          <Ionicons name="chatbubble-outline" size={16} color={theme.background} />
          <Text style={[styles.ctaText, { color: theme.background }]}>
            Explore this pattern with Mirror
          </Text>
        </TouchableOpacity>
      )}

      {/* Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        A lens for noticing patterns, not a statement of identity.
      </Text>
    </View>
  );
}

// =============================================================================
// STYLES - Premium, spacious, hierarchical
// =============================================================================

const styles = StyleSheet.create({
  container: {
    paddingTop: 4,
  },
  
  // Loading / Error
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 13,
    letterSpacing: 0.3,
  },
  errorContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 13,
    textAlign: 'center',
  },

  // ==========================================================================
  // HERO SECTION (dominant)
  // ==========================================================================
  heroSection: {
    marginTop: 16,
    marginBottom: 48,
    paddingBottom: 12,
  },
  signatureAccent: {
    width: 32,
    height: 3,
    borderRadius: 2,
    marginBottom: 24,
    opacity: 0.7,
  },
  heroHeader: {
    flexDirection: 'row',
    marginBottom: 24,
  },
  elementBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
  },
  elementBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  heroLine1: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 32,
    marginBottom: 10,
    letterSpacing: -0.4,
  },
  heroLine2: {
    fontSize: 17,
    lineHeight: 26,
    fontStyle: 'italic',
    opacity: 0.75,
  },

  // ==========================================================================
  // PATTERN LAYER (medium weight)
  // ==========================================================================
  patternLayer: {
    marginBottom: 28,
  },
  patternSection: {
    marginBottom: 20,
  },
  patternLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 12,
  },
  patternList: {
    gap: 10,
  },
  patternItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  patternDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginTop: 7,
    opacity: 0.5,
  },
  patternText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },
  sectionDivider: {
    height: 1,
    marginVertical: 20,
  },

  // ==========================================================================
  // COST LAYER (lighter weight)
  // ==========================================================================
  costLayer: {
    marginBottom: 28,
  },
  costHeader: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 16,
  },
  costGrid: {
    gap: 16,
  },
  costItem: {
    gap: 4,
  },
  costCategory: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  costValue: {
    fontSize: 13,
    lineHeight: 19,
  },

  // ==========================================================================
  // SHIFT SECTION (pause moment)
  // ==========================================================================
  shiftWrapper: {
    marginTop: 16,
    marginBottom: 48,
  },
  shiftSection: {
    borderLeftWidth: 3,
    paddingLeft: 16,
    paddingVertical: 8,
    marginTop: 20,
  },
  shiftLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    marginBottom: 10,
  },
  shiftText: {
    fontSize: 16,
    lineHeight: 25,
    fontWeight: '500',
  },

  // ==========================================================================
  // PROOF LAYER (collapsibles)
  // ==========================================================================
  proofLayer: {
    marginBottom: 24,
  },
  proofDivider: {
    height: 1,
    marginBottom: 16,
  },
  proofContainer: {
    marginBottom: 8,
  },
  proofHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
  },
  proofTitle: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.2,
  },
  proofContent: {
    paddingBottom: 16,
    paddingTop: 4,
  },
  proofText: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 8,
  },
  proofNote: {
    fontSize: 12,
    lineHeight: 18,
    fontStyle: 'italic',
  },

  // ==========================================================================
  // CHART DETAILS (inside proof)
  // ==========================================================================
  chartGrid: {
    gap: 14,
  },
  chartRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  chartLabel: {
    fontSize: 12,
  },
  chartValue: {
    fontSize: 13,
    fontWeight: '500',
  },
  chartValueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  elementPills: {
    flexDirection: 'row',
    gap: 6,
  },
  elementPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
  },
  elementPillText: {
    fontSize: 10,
    fontWeight: '600',
  },
  pillarsBox: {
    marginTop: 8,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.06)',
  },
  pillarsLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  pillarsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  pillarItem: {
    alignItems: 'center',
    flex: 1,
  },
  pillarType: {
    fontSize: 9,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  pillarValue: {
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center',
  },

  // ==========================================================================
  // CTA
  // ==========================================================================
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 10,
    paddingVertical: 14,
    marginBottom: 16,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '600',
  },

  // ==========================================================================
  // FOOTER
  // ==========================================================================
  footer: {
    fontSize: 11,
    textAlign: 'center',
    fontStyle: 'italic',
    letterSpacing: 0.2,
    marginBottom: 8,
  },
});
