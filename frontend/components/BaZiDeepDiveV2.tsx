/**
 * BaZi Deep Dive V2 - Confrontational Mirror Style
 * 
 * This is NOT a traditional BaZi reading.
 * This must feel like a master who sees patterns clearly and speaks directly.
 * 
 * Structure:
 * 1. Core Pattern - Sharp, confronting truth
 * 2. The Tension - Two forces pulling against each other
 * 3. What This Costs You - 3-5 real-life consequences
 * 4. Why This Exists - Light BaZi reference
 * 5. Your Chart, Read Simply - All 4 pillars interpreted + synthesis
 * 6. When This Backfires - Short bullets
 * 7. The Real Tension - Emotional landing paragraph
 * 8. One Shift - Clear behavioral move
 * 
 * @version 2.0
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Constants from 'expo-constants';
import { useTheme } from '../contexts/ThemeContext';
import InsightCardFooter from './InsightCardFooter';

// API Configuration
const EXPO_PUBLIC_BACKEND_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL 
  || process.env.EXPO_PUBLIC_BACKEND_URL 
  || '';

const getBackendBaseUrl = () => {
  // For web: ALWAYS use relative URLs so API calls go to same origin
  // This works for both preview and deployed domains
  if (typeof window !== 'undefined' && Platform.OS === 'web') {
    return '';
  }
  // For native apps, must use the configured backend URL
  return EXPO_PUBLIC_BACKEND_URL;
};

const BACKEND_BASE_URL = getBackendBaseUrl();

// =============================================================================
// TYPES - Deep Dive V2 Structure
// =============================================================================

interface PillarInterpretation {
  domain: string;
  animal: string;
  element_note: string;
  behavioral: string;
}

interface ChartReadSimply {
  year?: PillarInterpretation;
  month?: PillarInterpretation;
  day?: PillarInterpretation;
  hour?: PillarInterpretation;
  synthesis: string;
}

interface DeepDiveV2Data {
  core_pattern: string;
  the_tension: string;
  what_this_costs_you: string[];
  why_this_exists: string;
  your_chart_read_simply: ChartReadSimply;
  when_this_backfires: string[];
  the_real_tension: string;
  one_shift: string;
}

interface DayMaster {
  element: string;
  polarity: string;
  strength: string;
}

interface DeepDiveResponse {
  success: boolean;
  user_id: string;
  deep_dive: DeepDiveV2Data;
  day_master: DayMaster;
}

// Full chart pillar interface (from /api/bazi/{user_id}/full)
interface FullChartPillar {
  stem: string;
  stem_pinyin: string;
  branch: string;
  branch_pinyin: string;
  animal: string;
  animal_name: string;
  animal_emoji: string;
  stem_element: string;
  branch_element: string;
  meaning_label: string;
}

interface FullChartData {
  success: boolean;
  chart: {
    pillars: {
      year: FullChartPillar;
      month: FullChartPillar;
      day: FullChartPillar;
      hour: FullChartPillar;
    };
  };
}

// =============================================================================
// DESIGN SYSTEM - Premium, Grounded, Sharp
// =============================================================================

const BAZI_COLORS = {
  gold: '#C9A962',
  goldLight: 'rgba(201, 169, 98, 0.08)',
  goldMedium: 'rgba(201, 169, 98, 0.15)',
  goldStrong: 'rgba(201, 169, 98, 0.25)',
  wood: '#7CB08A',
  fire: '#D4836A',
  earth: '#C4A484',
  metal: '#A8B5C4',
  water: '#6B8BA4',
  subtle: 'rgba(255, 255, 255, 0.06)',
  divider: 'rgba(255, 255, 255, 0.08)',
  muted: 'rgba(255, 255, 255, 0.4)',
};

const ELEMENT_COLORS: Record<string, string> = {
  Wood: BAZI_COLORS.wood,
  Fire: BAZI_COLORS.fire,
  Earth: BAZI_COLORS.earth,
  Metal: BAZI_COLORS.metal,
  Water: BAZI_COLORS.water,
};

const PILLAR_ICONS: Record<string, string> = {
  year: 'leaf-outline',     // Roots
  month: 'briefcase-outline', // Work
  day: 'person-outline',    // Self
  hour: 'moon-outline',     // Inner World
};

// =============================================================================
// PILLAR CARD COMPONENT
// =============================================================================

const PillarCard: React.FC<{
  position: 'year' | 'month' | 'day' | 'hour';
  interpretation: PillarInterpretation;
  theme: any;
}> = ({ position, interpretation, theme }) => {
  return (
    <View style={[styles.pillarCard, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
      <View style={styles.pillarHeader}>
        <Ionicons 
          name={PILLAR_ICONS[position] as any} 
          size={16} 
          color={BAZI_COLORS.gold} 
        />
        <Text style={[styles.pillarDomain, { color: BAZI_COLORS.gold }]}>
          {interpretation.domain}
        </Text>
      </View>
      <Text style={[styles.pillarAnimal, { color: theme.text }]}>
        {interpretation.animal}
      </Text>
      <Text style={[styles.pillarBehavioral, { color: theme.textSecondary }]}>
        {interpretation.behavioral}
      </Text>
      {interpretation.element_note && (
        <Text style={[styles.pillarElementNote, { color: theme.textTertiary }]}>
          {interpretation.element_note}
        </Text>
      )}
    </View>
  );
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function BaZiDeepDiveV2({
  userId,
  onOpenChat,
}: {
  userId: string;
  onOpenChat?: () => void;
}) {
  const { theme } = useTheme();
  const [data, setData] = useState<DeepDiveResponse | null>(null);
  const [fullChart, setFullChart] = useState<FullChartData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDeepDive = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('[BaZi DeepDive V2] Starting fetch for userId:', userId);
        console.log('[BaZi DeepDive V2] BACKEND_BASE_URL:', BACKEND_BASE_URL);
        
        // Fetch both deep dive and full chart in parallel
        const [deepDiveRes, fullChartRes] = await Promise.all([
          fetch(`${BACKEND_BASE_URL}/api/bazi/${userId}/deep-dive`),
          fetch(`${BACKEND_BASE_URL}/api/bazi/${userId}/full`),
        ]);
        
        const deepDiveResult = await deepDiveRes.json();
        const fullChartResult = await fullChartRes.json();
        
        console.log('[BaZi DeepDive V2] Deep dive result:', deepDiveResult?.success ? 'SUCCESS' : 'FAILED');
        console.log('[BaZi DeepDive V2] Full chart result:', fullChartResult?.success ? 'SUCCESS' : 'FAILED');
        console.log('[BaZi DeepDive V2] Full chart pillars:', fullChartResult?.chart?.pillars ? 'PRESENT' : 'MISSING');
        console.log('[BaZi DeepDive V2] Full chart keys:', fullChartResult ? Object.keys(fullChartResult) : 'N/A');
        
        if (deepDiveResult.success) {
          setData(deepDiveResult);
        } else {
          setError(deepDiveResult.detail || 'Failed to load BaZi deep dive');
        }
        
        if (fullChartResult.success) {
          console.log('[BaZi DeepDive V2] Setting fullChart state');
          setFullChart(fullChartResult);
        } else {
          console.log('[BaZi DeepDive V2] Full chart fetch failed, pillars will be null');
        }
      } catch (err) {
        setError('Failed to connect to server');
        console.error('[BaZi DeepDive V2] Fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDeepDive();
  }, [userId]);

  const elementColor = data?.day_master?.element 
    ? ELEMENT_COLORS[data.day_master.element] 
    : BAZI_COLORS.gold;

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
        <Ionicons name="alert-circle-outline" size={32} color={theme.textTertiary} />
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to load deep dive'}
        </Text>
        <TouchableOpacity 
          style={[styles.retryButton, { borderColor: theme.border }]}
          onPress={() => {
            setLoading(true);
            setError(null);
            // Re-trigger fetch
            const fetchDeepDive = async () => {
              try {
                const response = await fetch(`${BACKEND_BASE_URL}/api/bazi/${userId}/deep-dive`);
                const result = await response.json();
                if (result.success) {
                  setData(result);
                } else {
                  setError(result.detail || 'Failed to load');
                }
              } catch (err) {
                setError('Failed to connect');
              } finally {
                setLoading(false);
              }
            };
            fetchDeepDive();
          }}
        >
          <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const deepDive = data.deep_dive;
  const dayMaster = data.day_master;
  const pillars = fullChart?.chart?.pillars;
  
  console.log('[BaZi DeepDive V2] Rendering with:');
  console.log('  - deepDive:', deepDive ? 'present' : 'missing');
  console.log('  - fullChart:', fullChart ? 'present' : 'missing');
  console.log('  - pillars:', pillars ? 'present' : 'missing');

  // Render the compact pillar cards for "Your Chart" section
  const renderChartPillars = () => {
    if (!pillars) return null;
    
    const pillarOrder: Array<'year' | 'month' | 'day' | 'hour'> = ['year', 'month', 'day', 'hour'];
    const pillarLabels: Record<string, string> = {
      year: 'Roots',
      month: 'Work',
      day: 'Self',
      hour: 'Inner World',
    };
    
    return (
      <View style={styles.chartPillarsRow}>
        {pillarOrder.map((key) => {
          const pillar = pillars[key];
          const isDay = key === 'day';
          
          return (
            <View 
              key={key} 
              style={[
                styles.chartPillarCard,
                { 
                  backgroundColor: theme.surfaceLight, 
                  borderColor: isDay ? elementColor : theme.border,
                  borderWidth: isDay ? 1.5 : StyleSheet.hairlineWidth,
                },
                isDay && { shadowColor: elementColor, shadowOpacity: 0.15, shadowRadius: 8, shadowOffset: { width: 0, height: 2 } },
              ]}
            >
              {/* Core label for Day pillar */}
              {isDay && (
                <View style={[styles.coreBadge, { backgroundColor: elementColor }]}>
                  <Text style={styles.coreBadgeText}>Core</Text>
                </View>
              )}
              
              {/* Pillar Label */}
              <Text style={[styles.chartPillarLabel, { color: theme.textTertiary }]}>
                {pillarLabels[key]}
              </Text>
              
              {/* Animal Emoji */}
              <Text style={styles.chartPillarEmoji}>{pillar.animal_emoji}</Text>
              
              {/* Animal Name */}
              <Text style={[styles.chartPillarAnimal, { color: theme.text }]}>
                {pillar.animal_name}
              </Text>
              
              {/* Stem-Branch Label */}
              <Text style={[styles.chartPillarStem, { color: theme.textTertiary }]}>
                {pillar.stem_pinyin}-{pillar.branch_pinyin}
              </Text>
              
              {/* Element dot */}
              <View style={[styles.chartPillarDot, { backgroundColor: ELEMENT_COLORS[pillar.stem_element] || BAZI_COLORS.muted }]} />
            </View>
          );
        })}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      
      {/* ============================================= */}
      {/* YOUR CHART - Visual Anchor at Top */}
      {/* ============================================= */}
      <View style={styles.yourChartSection}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>YOUR CHART</Text>
        {pillars ? (
          <>
            {renderChartPillars()}
            <Text style={[styles.chartHelperText, { color: theme.textTertiary }]}>
              Read as a whole — not one pillar alone.
            </Text>
          </>
        ) : (
          <View style={[styles.chartFallback, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
            <Text style={[styles.chartFallbackText, { color: theme.textTertiary }]}>
              Loading chart pillars...
            </Text>
          </View>
        )}
      </View>
      
      {/* ============================================= */}
      {/* THE PATTERN - Sharp Opening (No duplicate "Core Pattern") */}
      {/* ============================================= */}
      <View style={[styles.section, styles.corePatternSection, { borderLeftColor: elementColor }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>THE PATTERN</Text>
        <Text style={[styles.corePatternText, { color: theme.text }]}>
          {deepDive.core_pattern}
        </Text>
      </View>

      {/* ============================================= */}
      {/* THE TENSION - Two Forces Pulling */}
      {/* ============================================= */}
      <View style={[styles.section, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>THE TENSION</Text>
        <Text style={[styles.tensionText, { color: theme.text }]}>
          {deepDive.the_tension}
        </Text>
      </View>

      {/* ============================================= */}
      {/* WHAT THIS COSTS YOU - Consequences */}
      {/* ============================================= */}
      <View style={[styles.section, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>WHAT THIS COSTS YOU</Text>
        {deepDive.what_this_costs_you.map((cost, index) => (
          <View key={index} style={styles.costItem}>
            <View style={[styles.costBullet, { backgroundColor: BAZI_COLORS.fire }]} />
            <Text style={[styles.costText, { color: theme.textSecondary }]}>{cost}</Text>
          </View>
        ))}
      </View>

      {/* ============================================= */}
      {/* WHY THIS EXISTS - Light BaZi Reference */}
      {/* ============================================= */}
      <View style={[styles.section, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>WHY THIS EXISTS</Text>
        <Text style={[styles.whyText, { color: theme.textSecondary }]}>
          {deepDive.why_this_exists}
        </Text>
        <View style={[styles.dayMasterBadge, { backgroundColor: BAZI_COLORS.goldLight, borderColor: BAZI_COLORS.goldMedium }]}>
          <Text style={[styles.dayMasterLabel, { color: BAZI_COLORS.gold }]}>
            Core Element: {dayMaster.polarity} {dayMaster.element}
          </Text>
          <Text style={[styles.dayMasterStrength, { color: theme.textTertiary }]}>
            ({dayMaster.strength})
          </Text>
        </View>
      </View>

      {/* ============================================= */}
      {/* YOUR CHART, READ SIMPLY - All 4 Pillars */}
      {/* ============================================= */}
      <View style={[styles.section, styles.chartSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>YOUR CHART, READ SIMPLY</Text>
        
        {/* Four Pillars Grid */}
        <View style={styles.pillarsGrid}>
          {deepDive.your_chart_read_simply.year && (
            <PillarCard 
              position="year" 
              interpretation={deepDive.your_chart_read_simply.year} 
              theme={theme} 
            />
          )}
          {deepDive.your_chart_read_simply.month && (
            <PillarCard 
              position="month" 
              interpretation={deepDive.your_chart_read_simply.month} 
              theme={theme} 
            />
          )}
          {deepDive.your_chart_read_simply.day && (
            <PillarCard 
              position="day" 
              interpretation={deepDive.your_chart_read_simply.day} 
              theme={theme} 
            />
          )}
          {deepDive.your_chart_read_simply.hour && (
            <PillarCard 
              position="hour" 
              interpretation={deepDive.your_chart_read_simply.hour} 
              theme={theme} 
            />
          )}
        </View>

        {/* Synthesis - Combined Pattern */}
        <View style={[styles.synthesisContainer, { backgroundColor: BAZI_COLORS.goldLight, borderColor: BAZI_COLORS.goldMedium }]}>
          <Text style={[styles.synthesisLabel, { color: BAZI_COLORS.gold }]}>COMBINED PATTERN</Text>
          <Text style={[styles.synthesisText, { color: theme.text }]}>
            {deepDive.your_chart_read_simply.synthesis}
          </Text>
        </View>
      </View>

      {/* ============================================= */}
      {/* WHEN THIS BACKFIRES - Short Bullets */}
      {/* ============================================= */}
      <View style={[styles.section, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>WHEN THIS BACKFIRES</Text>
        {deepDive.when_this_backfires.map((item, index) => (
          <View key={index} style={styles.backfireItem}>
            <Ionicons name="warning-outline" size={14} color={BAZI_COLORS.fire} />
            <Text style={[styles.backfireText, { color: theme.textSecondary }]}>{item}</Text>
          </View>
        ))}
      </View>

      {/* ============================================= */}
      {/* THE REAL TENSION - Emotional Landing */}
      {/* ============================================= */}
      <View style={[styles.section, styles.realTensionSection, { borderLeftColor: elementColor }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>THE REAL TENSION</Text>
        <Text style={[styles.realTensionText, { color: theme.text }]}>
          {deepDive.the_real_tension}
        </Text>
      </View>

      {/* ============================================= */}
      {/* ONE SHIFT - Actionable Move */}
      {/* ============================================= */}
      <View style={[styles.section, styles.shiftSection, { backgroundColor: BAZI_COLORS.goldLight, borderColor: BAZI_COLORS.gold }]}>
        <View style={styles.shiftHeader}>
          <Ionicons name="flash-outline" size={18} color={BAZI_COLORS.gold} />
          <Text style={[styles.sectionLabel, { color: BAZI_COLORS.gold, marginLeft: 6 }]}>ONE SHIFT</Text>
        </View>
        <Text style={[styles.shiftText, { color: theme.text }]}>
          {deepDive.one_shift}
        </Text>
      </View>

      {/* ============================================= */}
      {/* UNIFIED FOOTER */}
      {/* ============================================= */}
      <InsightCardFooter 
        source={{
          lens: 'bazi',
          section: 'deep_dive',
          name: deepDive.core_pattern || 'BaZi Deep Dive',
          type: 'deep_dive',
          id: `bazi_deep_dive_${userId}`,
          value: deepDive.the_real_tension || deepDive.core_pattern || '',
        }}
        patternSignature={`bazi_deep_dive_${dayMaster.element.toLowerCase()}`}
        context="bazi_deep_dive"
        prompt="What stands out in this reading? What feels true?"
      />

      {/* Ask About This Pattern */}
      {onOpenChat && (
        <TouchableOpacity
          style={[styles.askButton, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
          onPress={onOpenChat}
        >
          <Ionicons name="chatbubble-outline" size={16} color={theme.textSecondary} />
          <Text style={[styles.askButtonText, { color: theme.textSecondary }]}>
            Ask about this pattern
          </Text>
        </TouchableOpacity>
      )}

      {/* Disclaimer */}
      <Text style={[styles.disclaimer, { color: theme.textTertiary }]}>
        Pattern notation, not destiny. A lens for noticing, not a truth to follow.
      </Text>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    paddingBottom: 16,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorText: {
    marginTop: 12,
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
  },
  retryText: {
    fontSize: 16,
    fontWeight: '500',
  },
  
  // Your Chart Section (Visual Anchor)
  yourChartSection: {
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(255, 255, 255, 0.06)',
  },
  chartPillarsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
    marginBottom: 14,
  },
  chartPillarCard: {
    flex: 1,
    paddingVertical: 7,
    paddingHorizontal: 5,
    borderRadius: 8,
    alignItems: 'center',
    position: 'relative',
  },
  coreBadge: {
    position: 'absolute',
    top: -5,
    right: -3,
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 3,
  },
  coreBadgeText: {
    fontSize: 7,
    fontWeight: '700',
    color: '#000',
    letterSpacing: 0.2,
  },
  chartPillarLabel: {
    fontSize: 7,
    fontWeight: '600',
    letterSpacing: 0.3,
    marginBottom: 2,
    textTransform: 'uppercase',
  },
  chartPillarEmoji: {
    fontSize: 22,
    marginBottom: 1,
  },
  chartPillarAnimal: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 1,
  },
  chartPillarStem: {
    fontSize: 8,
    opacity: 0.7,
  },
  chartPillarDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    marginTop: 3,
  },
  chartHelperText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
    opacity: 0.5,
  },
  chartFallback: {
    padding: 16,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 80,
  },
  chartFallbackText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  
  // Sections
  section: {
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 14,
  },
  
  // Core Pattern
  corePatternSection: {
    borderLeftWidth: 3,
    borderTopLeftRadius: 0,
    borderBottomLeftRadius: 0,
    backgroundColor: 'transparent',
    borderWidth: 0,
    paddingLeft: 14,
  },
  corePatternText: {
    fontSize: 24,
    fontWeight: '600',
    lineHeight: 32,
  },
  
  // Tension
  tensionText: {
    fontSize: 16,
    fontWeight: '500',
    fontStyle: 'italic',
    lineHeight: 32,
  },
  
  // Costs
  costItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
    gap: 10,
  },
  costBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 6,
  },
  costText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 30,
  },
  
  // Why This Exists
  whyText: {
    fontSize: 16,
    lineHeight: 30,
    marginBottom: 16,
  },
  dayMasterBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    borderWidth: 1,
    gap: 6,
  },
  dayMasterLabel: {
    fontSize: 14,
    fontWeight: '600',
  },
  dayMasterStrength: {
    fontSize: 14,
  },
  
  // Chart Section
  chartSection: {
    paddingBottom: 20,
  },
  pillarsGrid: {
    gap: 10,
  },
  pillarCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 2,
  },
  pillarHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  pillarDomain: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  pillarAnimal: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  pillarBehavioral: {
    fontSize: 16,
    fontStyle: 'italic',
    lineHeight: 32,
    marginBottom: 6,
  },
  pillarElementNote: {
    fontSize: 14,
    lineHeight: 31,
  },
  
  // Synthesis
  synthesisContainer: {
    marginTop: 14,
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
  },
  synthesisLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 14,
  },
  synthesisText: {
    fontSize: 17,
    fontWeight: '500',
    lineHeight: 31,
  },
  
  // Backfire
  backfireItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
    gap: 8,
  },
  backfireText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 32,
  },
  
  // Real Tension
  realTensionSection: {
    borderLeftWidth: 3,
    borderTopLeftRadius: 0,
    borderBottomLeftRadius: 0,
    backgroundColor: 'transparent',
    borderWidth: 0,
    paddingLeft: 14,
  },
  realTensionText: {
    fontSize: 17,
    lineHeight: 32,
  },
  
  // One Shift
  shiftSection: {
    borderWidth: 1,
  },
  shiftHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  shiftText: {
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 32,
  },
  
  // Ask Button
  askButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 8,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
  },
  askButtonText: {
    fontSize: 16,
  },
  
  // Disclaimer
  disclaimer: {
    marginTop: 16,
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
  },
});
