import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  ScrollView,
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

interface TodayInsight {
  headline: string;
  behavioral: string;
  pressure_note?: string | null;
}

interface BaZiInsightData {
  core_truth: CoreTruth;
  how_this_shows_up: string[];
  when_this_backfires: string[];
  what_this_costs_you: CostCategories;
  one_shift: string;
  why_showing_up: WhyShowingUp;
  chart_details: ChartDetails;
  today_insight?: TodayInsight;
}

// Colors
const COLORS = {
  accent: '#C4A484',
  accentLight: 'rgba(196, 164, 132, 0.12)',
  accentMedium: 'rgba(196, 164, 132, 0.25)',
  // Action sections
  showsUpBlue: '#64B5F6',
  showsUpBg: 'rgba(100, 181, 246, 0.08)',
  backfireRed: '#E57373',
  backfireBg: 'rgba(229, 115, 115, 0.08)',
  costOrange: '#FFB74D',
  costBg: 'rgba(255, 183, 77, 0.08)',
  shiftGreen: '#81C784',
  shiftBg: 'rgba(129, 199, 132, 0.08)',
  // Collapsible sections
  proofPurple: '#9B8AC4',
  proofBg: 'rgba(155, 138, 196, 0.08)',
  chartGray: '#9E9E9E',
  chartBg: 'rgba(158, 158, 158, 0.08)',
};

// Collapsible Section Component - Simple content-driven height
const CollapsibleSection: React.FC<{
  title: string;
  icon: string;
  color: string;
  bgColor: string;
  theme: any;
  children: React.ReactNode;
}> = ({ title, icon, color, bgColor, theme, children }) => {
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
    <View style={[styles.collapsibleContainer, { backgroundColor: bgColor, borderColor: color }]}>
      <TouchableOpacity 
        style={styles.collapsibleHeader} 
        onPress={toggleExpand}
        activeOpacity={0.7}
      >
        <View style={styles.collapsibleTitleRow}>
          <Ionicons name={icon as any} size={16} color={color} />
          <Text style={[styles.collapsibleTitle, { color }]}>{title}</Text>
        </View>
        <Animated.View style={animatedIconStyle}>
          <Ionicons name="chevron-forward" size={18} color={color} />
        </Animated.View>
      </TouchableOpacity>
      
      {isExpanded && (
        <View style={styles.collapsibleContent}>
          <View style={[styles.collapsibleDivider, { backgroundColor: color }]} />
          {children}
        </View>
      )}
    </View>
  );
};

// Main Component
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

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading insight...
        </Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={32} color={COLORS.backfireRed} />
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Could not load insight'}
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* 1. CORE TRUTH - Always visible, top */}
      <View style={[styles.coreTruthSection, { backgroundColor: COLORS.accentLight, borderColor: COLORS.accent }]}>
        <Text style={[styles.coreTruthLine1, { color: theme.text }]}>
          {data.core_truth.line1}
        </Text>
        <Text style={[styles.coreTruthLine2, { color: theme.textSecondary }]}>
          {data.core_truth.line2}
        </Text>
      </View>

      {/* 2. HOW THIS SHOWS UP */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: COLORS.showsUpBlue }]}>HOW THIS SHOWS UP</Text>
        <View style={[styles.bulletList, { backgroundColor: COLORS.showsUpBg, borderColor: COLORS.showsUpBlue }]}>
          {data.how_this_shows_up.map((item, index) => (
            <View key={index} style={styles.bulletItem}>
              <View style={[styles.bulletDot, { backgroundColor: COLORS.showsUpBlue }]} />
              <Text style={[styles.bulletText, { color: theme.textSecondary }]}>{item}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* 3. WHEN THIS BACKFIRES */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: COLORS.backfireRed }]}>WHEN THIS BACKFIRES</Text>
        <View style={[styles.bulletList, { backgroundColor: COLORS.backfireBg, borderColor: COLORS.backfireRed }]}>
          {data.when_this_backfires.map((item, index) => (
            <View key={index} style={styles.bulletItem}>
              <View style={[styles.bulletDot, { backgroundColor: COLORS.backfireRed }]} />
              <Text style={[styles.bulletText, { color: theme.textSecondary }]}>{item}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* 4. WHAT THIS COSTS YOU */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: COLORS.costOrange }]}>WHAT THIS COSTS YOU</Text>
        <View style={[styles.costsCard, { backgroundColor: COLORS.costBg, borderColor: COLORS.costOrange }]}>
          <View style={styles.costItem}>
            <Text style={[styles.costLabel, { color: COLORS.costOrange }]}>ENERGY</Text>
            <Text style={[styles.costText, { color: theme.textSecondary }]}>{data.what_this_costs_you.energy}</Text>
          </View>
          <View style={styles.costItem}>
            <Text style={[styles.costLabel, { color: COLORS.costOrange }]}>RELATIONSHIPS</Text>
            <Text style={[styles.costText, { color: theme.textSecondary }]}>{data.what_this_costs_you.relationships}</Text>
          </View>
          <View style={styles.costItem}>
            <Text style={[styles.costLabel, { color: COLORS.costOrange }]}>OPPORTUNITIES</Text>
            <Text style={[styles.costText, { color: theme.textSecondary }]}>{data.what_this_costs_you.opportunities}</Text>
          </View>
        </View>
      </View>

      {/* 5. ONE SHIFT */}
      <View style={[styles.oneShiftSection, { backgroundColor: COLORS.shiftBg, borderColor: COLORS.shiftGreen }]}>
        <Text style={[styles.oneShiftLabel, { color: COLORS.shiftGreen }]}>ONE SHIFT</Text>
        <Text style={[styles.oneShiftText, { color: theme.text }]}>
          {data.one_shift}
        </Text>
      </View>

      {/* 6. WHY THIS IS SHOWING UP (Collapsible) */}
      <CollapsibleSection
        title="Why this is showing up"
        icon="information-circle-outline"
        color={COLORS.proofPurple}
        bgColor={COLORS.proofBg}
        theme={theme}
      >
        <Text style={[styles.collapsibleText, { color: theme.textSecondary }]}>
          {data.why_showing_up.explanation}
        </Text>
        <Text style={[styles.collapsibleTextNote, { color: theme.textTertiary }]}>
          {data.why_showing_up.pattern_note}
        </Text>
      </CollapsibleSection>

      {/* 7. SEE YOUR CHART DETAILS (Collapsible) */}
      <CollapsibleSection
        title="See your chart details"
        icon="analytics-outline"
        color={COLORS.chartGray}
        bgColor={COLORS.chartBg}
        theme={theme}
      >
        <View style={styles.chartDetailsGrid}>
          <View style={styles.chartDetailRow}>
            <Text style={[styles.chartDetailLabel, { color: theme.textTertiary }]}>Day Master</Text>
            <Text style={[styles.chartDetailValue, { color: theme.text }]}>
              {data.chart_details.day_master_chinese}
            </Text>
          </View>
          <View style={styles.chartDetailRow}>
            <Text style={[styles.chartDetailLabel, { color: theme.textTertiary }]}>Strength</Text>
            <Text style={[styles.chartDetailValue, { color: theme.text }]}>
              {data.chart_details.strength}
            </Text>
          </View>
          {data.chart_details.dominant_patterns && data.chart_details.dominant_patterns.length > 0 && (
            <View style={styles.chartDetailRow}>
              <Text style={[styles.chartDetailLabel, { color: theme.textTertiary }]}>Dominant</Text>
              <Text style={[styles.chartDetailValue, { color: theme.text }]}>
                {data.chart_details.dominant_patterns.join(', ')}
              </Text>
            </View>
          )}
          {data.chart_details.favorable_elements && data.chart_details.favorable_elements.length > 0 && (
            <View style={styles.chartDetailRow}>
              <Text style={[styles.chartDetailLabel, { color: theme.textTertiary }]}>Favorable</Text>
              <Text style={[styles.chartDetailValue, { color: theme.text }]}>
                {data.chart_details.favorable_elements.join(', ')}
              </Text>
            </View>
          )}
          {data.chart_details.pillars && (
            <View style={styles.pillarsSection}>
              <Text style={[styles.pillarsTitle, { color: theme.textTertiary }]}>Pillars</Text>
              <View style={styles.pillarsGrid}>
                <View style={styles.pillarItem}>
                  <Text style={[styles.pillarLabel, { color: theme.textTertiary }]}>Year</Text>
                  <Text style={[styles.pillarValue, { color: theme.text }]}>{data.chart_details.pillars.year}</Text>
                </View>
                <View style={styles.pillarItem}>
                  <Text style={[styles.pillarLabel, { color: theme.textTertiary }]}>Month</Text>
                  <Text style={[styles.pillarValue, { color: theme.text }]}>{data.chart_details.pillars.month}</Text>
                </View>
                <View style={styles.pillarItem}>
                  <Text style={[styles.pillarLabel, { color: theme.textTertiary }]}>Day</Text>
                  <Text style={[styles.pillarValue, { color: theme.text }]}>{data.chart_details.pillars.day}</Text>
                </View>
                <View style={styles.pillarItem}>
                  <Text style={[styles.pillarLabel, { color: theme.textTertiary }]}>Hour</Text>
                  <Text style={[styles.pillarValue, { color: theme.text }]}>{data.chart_details.pillars.hour}</Text>
                </View>
              </View>
            </View>
          )}
        </View>
      </CollapsibleSection>

      {/* Explore with Mirror CTA */}
      {onOpenChat && (
        <TouchableOpacity
          style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
          onPress={onOpenChat}
        >
          <Ionicons name="chatbubble-outline" size={18} color={theme.background} />
          <Text style={[styles.askMirrorText, { color: theme.background }]}>
            Explore this pattern with Mirror
          </Text>
        </TouchableOpacity>
      )}

      {/* Positioning Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        A lens for noticing patterns, not a statement of identity. Use it or leave it.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingTop: 8,
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },

  // Core Truth
  coreTruthSection: {
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
    padding: 16,
    marginBottom: 20,
  },
  coreTruthLine1: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 26,
    marginBottom: 4,
  },
  coreTruthLine2: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
  },

  // Section
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 8,
  },

  // Bullet List
  bulletList: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
    gap: 10,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 6,
  },
  bulletText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },

  // Costs
  costsCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    gap: 14,
  },
  costItem: {
    gap: 4,
  },
  costLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  costText: {
    fontSize: 13,
    lineHeight: 19,
  },

  // One Shift
  oneShiftSection: {
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
    padding: 14,
    marginBottom: 20,
  },
  oneShiftLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  oneShiftText: {
    fontSize: 14,
    lineHeight: 21,
    fontWeight: '500',
  },

  // Collapsible
  collapsibleContainer: {
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  collapsibleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  collapsibleTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  collapsibleTitle: {
    fontSize: 13,
    fontWeight: '600',
  },
  collapsibleContent: {
    paddingHorizontal: 14,
    paddingBottom: 16,
    paddingTop: 4,
  },
  collapsibleDivider: {
    height: 1,
    opacity: 0.2,
    marginBottom: 12,
    marginHorizontal: -14,
    marginLeft: -14,
    marginRight: -14,
  },
  collapsibleText: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 8,
  },
  collapsibleTextNote: {
    fontSize: 12,
    lineHeight: 18,
    fontStyle: 'italic',
  },

  // Chart Details
  chartDetailsGrid: {
    gap: 12,
  },
  chartDetailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  chartDetailLabel: {
    fontSize: 12,
  },
  chartDetailValue: {
    fontSize: 13,
    fontWeight: '600',
  },
  pillarsSection: {
    marginTop: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  pillarsTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  pillarsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pillarItem: {
    flex: 1,
    minWidth: '45%',
    alignItems: 'center',
  },
  pillarLabel: {
    fontSize: 10,
    marginBottom: 2,
  },
  pillarValue: {
    fontSize: 12,
    fontWeight: '500',
  },

  // Ask Mirror
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 12,
    paddingVertical: 14,
    marginBottom: 12,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
  },

  // Footer
  footer: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
    marginBottom: 16,
  },
});
