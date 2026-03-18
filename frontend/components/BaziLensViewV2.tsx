/**
 * BaZi Lens View V2
 * 
 * Rebuilt BaZi lens with:
 * - 2-tab structure: Summary + Snapshot
 * - Classical Zi Ping calculations with Mirror language
 * - Day Master profile with behavioral descriptions
 * - Four Pillars with animal visuals
 * - Timing interactions (Today/Month/Year)
 * - Ask buttons with contextual prompts
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { InlineReflectButton } from './UniversalReflectButton';
import api from '../services/api';

// =============================================================================
// INTERFACES (V2 Response Shape)
// =============================================================================

interface DayMasterV2 {
  stem: string;
  stem_pinyin: string;
  element: string;
  polarity: string;
  strength: string;
  keywords: string[];
  description: string;
  strength_description: string;
}

interface PillarV2 {
  stem: string;
  stem_pinyin: string;
  branch: string;
  branch_pinyin: string;
  animal: string;
  animal_name: string;
  animal_emoji: string;
  hidden_stems: string[];
  hidden_stems_pinyin: string[];
  stem_element: string;
  branch_element: string;
  meaning_label: string;
  meaning_description: string;
}

interface ElementsV2 {
  wood: number;
  fire: number;
  earth: number;
  metal: number;
  water: number;
  dominant: string[];
  weak: string[];
  supporting: string[];
  balancing: string[];
}

interface TenGodsSummary {
  dominant: string[];
  dominant_raw: string[];
  present: string[];
  present_raw: string[];
  categories: string[];
}

interface StructureSummary {
  season: string;
  climate: string;
  supporting_elements: string[];
  balancing_elements: string[];
}

interface TimingPeriod {
  pillar: string;
  stem: string;
  branch: string;
  element: string;
  animal: { name: string; emoji: string } | string;
  ten_god: string;
  ten_god_name: string;
  element_relation: string;
  interaction: string;
  description: string;
}

interface Timing {
  today: TimingPeriod;
  month: TimingPeriod;
  year: TimingPeriod;
}

interface BaziChartV2 {
  day_master: DayMasterV2;
  pillars: {
    year: PillarV2;
    month: PillarV2;
    day: PillarV2;
    hour: PillarV2;
  };
  elements: ElementsV2;
  ten_gods_summary: TenGodsSummary;
  structure_summary: StructureSummary;
  timing: Timing;
  birth_data: {
    date: string;
    time: string;
    timezone: string | null;
    chinese_year: number;
    bazi_month: number;
  };
  calculation_version: string;
}

interface BaziResponseV2 {
  success: boolean;
  user_id: string;
  has_birth_time: boolean;
  chart: BaziChartV2;
}

interface Props {
  userId: string;
  onOpenChat: () => void;
}

// =============================================================================
// ELEMENT COLORS & ICONS
// =============================================================================

const ELEMENT_COLORS: Record<string, string> = {
  Wood: '#4CAF50',
  Fire: '#FF5722',
  Earth: '#8D6E63',
  Metal: '#9E9E9E',
  Water: '#2196F3',
};

const ELEMENT_ICONS: Record<string, string> = {
  Wood: '🌳',
  Fire: '🔥',
  Earth: '🏔️',
  Metal: '⚙️',
  Water: '💧',
};

// =============================================================================
// INTERACTION COLORS
// =============================================================================

const INTERACTION_COLORS = {
  supporting: '#4CAF50',
  pressure: '#FF5722',
  mixed: '#FF9800',
};

// =============================================================================
// ELEMENT INTERPRETATION (Mirror Language)
// =============================================================================

const ELEMENT_INTERPRETATIONS: Record<string, { strong: string; weak: string }> = {
  Wood: {
    strong: "Growth and initiative come naturally to you. You may find yourself often starting things or pushing forward.",
    weak: "Growth and forward movement may require more conscious effort. You might benefit from building momentum gradually.",
  },
  Fire: {
    strong: "Warmth, expression, and visibility come naturally to you. You may light up spaces without trying.",
    weak: "Warmth, expression, and outward energy may require more conscious activation. Creating space to shine helps.",
  },
  Earth: {
    strong: "Stability and structure come naturally to you. Others may rely on your grounded presence.",
    weak: "Stability and grounding may require more conscious cultivation. Building reliable routines can help.",
  },
  Metal: {
    strong: "Precision and discernment come naturally to you. You may naturally notice details and hold standards.",
    weak: "Precision and clear boundaries may require more conscious effort. Focus on what truly matters to you.",
  },
  Water: {
    strong: "Depth and adaptability come naturally to you. You may flow around obstacles with ease.",
    weak: "Depth and reflection may require more conscious cultivation. Creating stillness and space helps.",
  },
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

type TabType = 'summary' | 'snapshot';

export default function BaziLensView({ userId, onOpenChat }: Props) {
  const { theme, isDark } = useTheme();
  
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [data, setData] = useState<BaziChartV2 | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load BaZi data
  const loadBaziData = useCallback(async (refresh = false) => {
    if (refresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const response = await api.get<BaziResponseV2>(`/bazi/${userId}/full`);
      if (response.data.success) {
        setData(response.data.chart);
      } else {
        setError('Failed to load BaZi chart');
      }
    } catch (err: any) {
      console.error('[BaZi V2] Load error:', err);
      if (err.response?.status === 400) {
        setError('Birth date is required for BaZi calculation. Please complete your profile.');
      } else {
        setError('Unable to load your BaZi chart right now.');
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [userId]);

  useEffect(() => {
    loadBaziData();
  }, [loadBaziData]);

  const handleRefresh = () => {
    loadBaziData(true);
  };

  // =============================================================================
  // TAB BAR
  // =============================================================================

  const renderTabBar = () => (
    <View style={[styles.tabBar, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'summary' && { color: theme.text, fontWeight: '600' }]}>
          Summary
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'snapshot' && styles.activeTab]}
        onPress={() => setActiveTab('snapshot')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'snapshot' && { color: theme.text, fontWeight: '600' }]}>
          Snapshot
        </Text>
      </TouchableOpacity>
    </View>
  );

  // =============================================================================
  // SUMMARY TAB COMPONENTS
  // =============================================================================

  // A. Core Signature Card
  const renderCoreSignature = () => {
    if (!data) return null;
    const { day_master } = data;
    
    return (
      <View style={[styles.signatureCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.signatureHeader}>
          <View style={[styles.elementBadge, { backgroundColor: ELEMENT_COLORS[day_master.element] + '20' }]}>
            <Text style={styles.elementIcon}>{ELEMENT_ICONS[day_master.element]}</Text>
          </View>
          <View style={styles.signatureInfo}>
            <Text style={[styles.signatureName, { color: theme.text }]}>
              {day_master.stem_pinyin} {day_master.element}
            </Text>
            <Text style={[styles.signatureDetail, { color: theme.textSecondary }]}>
              {day_master.polarity} • {day_master.strength.charAt(0).toUpperCase() + day_master.strength.slice(1)}
            </Text>
          </View>
        </View>
        
        <View style={styles.keywordsRow}>
          {day_master.keywords.map((keyword, idx) => (
            <View key={idx} style={[styles.keywordBadge, { backgroundColor: theme.background }]}>
              <Text style={[styles.keywordText, { color: theme.textSecondary }]}>{keyword}</Text>
            </View>
          ))}
        </View>
        
        <Text style={[styles.signatureDescription, { color: theme.textSecondary }]}>
          {day_master.description}
        </Text>
        
        <View style={[styles.strengthNote, { backgroundColor: theme.background }]}>
          <Text style={[styles.strengthNoteText, { color: theme.textTertiary }]}>
            {day_master.strength_description}
          </Text>
        </View>
      </View>
    );
  };

  // B. Chart Pattern Overview
  const renderChartPattern = () => {
    if (!data) return null;
    const { elements, day_master } = data;
    
    // Build interpretation
    const dominantText = elements.dominant.length > 0 
      ? elements.dominant.map(e => `${ELEMENT_ICONS[e]} ${e}`).join(' and ')
      : 'balanced elements';
    
    const weakText = elements.weak.length > 0
      ? elements.weak[0]
      : 'none particularly weak';
    
    // Get behavioral interpretation
    const dominantElement = elements.dominant[0] || day_master.element;
    const interpretation = ELEMENT_INTERPRETATIONS[dominantElement];
    const dmStrength = day_master.strength === 'strong';
    
    return (
      <View style={[styles.patternCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>CHART PATTERN</Text>
        
        <View style={styles.patternGrid}>
          <View style={styles.patternItem}>
            <Text style={[styles.patternItemLabel, { color: theme.textTertiary }]}>Dominant</Text>
            <Text style={[styles.patternItemValue, { color: ELEMENT_COLORS[elements.dominant[0]] || theme.text }]}>
              {dominantText}
            </Text>
          </View>
          <View style={styles.patternItem}>
            <Text style={[styles.patternItemLabel, { color: theme.textTertiary }]}>Needs Activation</Text>
            <Text style={[styles.patternItemValue, { color: ELEMENT_COLORS[weakText] || theme.textSecondary }]}>
              {ELEMENT_ICONS[weakText] || '—'} {weakText}
            </Text>
          </View>
        </View>
        
        <Text style={[styles.patternInterpretation, { color: theme.textSecondary }]}>
          {dmStrength ? interpretation?.strong : interpretation?.weak}
        </Text>
      </View>
    );
  };

  // C. Four Pillars Overview
  const renderFourPillars = () => {
    if (!data) return null;
    const { pillars } = data;
    
    const pillarOrder: Array<'year' | 'month' | 'day' | 'hour'> = ['year', 'month', 'day', 'hour'];
    
    return (
      <View style={[styles.pillarsSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>FOUR PILLARS</Text>
        
        <View style={styles.pillarsGrid}>
          {pillarOrder.map((key) => {
            const pillar = pillars[key];
            return (
              <View key={key} style={[styles.pillarCard, { backgroundColor: theme.background, borderColor: theme.border }]}>
                <Text style={[styles.pillarMeaning, { color: theme.textTertiary }]}>
                  {pillar.meaning_label}
                </Text>
                <Text style={styles.pillarAnimal}>{pillar.animal_emoji}</Text>
                <Text style={[styles.pillarAnimalName, { color: theme.text }]}>
                  {pillar.animal_name}
                </Text>
                <Text style={[styles.pillarChars, { color: theme.textSecondary }]}>
                  {pillar.stem_pinyin}-{pillar.branch_pinyin}
                </Text>
                <View style={[styles.pillarElementDot, { backgroundColor: ELEMENT_COLORS[pillar.stem_element] }]} />
              </View>
            );
          })}
        </View>
        
        <Text style={[styles.pillarsNote, { color: theme.textTertiary }]}>
          Year = Roots • Month = Work • Day = Self • Hour = Inner World
        </Text>
      </View>
    );
  };

  // D. Timing Snapshot Preview (3 cards)
  const renderTimingPreview = () => {
    if (!data?.timing) return null;
    const { timing } = data;
    
    const periods: Array<{ key: 'today' | 'month' | 'year'; label: string }> = [
      { key: 'today', label: 'Today' },
      { key: 'month', label: 'This Month' },
      { key: 'year', label: 'This Year' },
    ];
    
    return (
      <View style={styles.timingPreviewSection}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary, marginBottom: 12, marginLeft: 4 }]}>
          TIMING
        </Text>
        
        <View style={styles.timingPreviewGrid}>
          {periods.map(({ key, label }) => {
            const period = timing[key];
            const interactionColor = INTERACTION_COLORS[period.interaction as keyof typeof INTERACTION_COLORS] || theme.textSecondary;
            
            return (
              <View key={key} style={[styles.timingPreviewCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                <View style={styles.timingPreviewHeader}>
                  <Text style={[styles.timingPreviewLabel, { color: theme.textTertiary }]}>{label}</Text>
                  <View style={[styles.interactionBadge, { backgroundColor: interactionColor + '20' }]}>
                    <Text style={[styles.interactionText, { color: interactionColor }]}>
                      {period.interaction}
                    </Text>
                  </View>
                </View>
                <Text style={[styles.timingPreviewDesc, { color: theme.textSecondary }]} numberOfLines={2}>
                  {period.description}
                </Text>
              </View>
            );
          })}
        </View>
        
        <TouchableOpacity 
          style={[styles.viewSnapshotButton, { borderColor: theme.border }]}
          onPress={() => setActiveTab('snapshot')}
        >
          <Text style={[styles.viewSnapshotText, { color: theme.text }]}>View Full Snapshot</Text>
          <Ionicons name="chevron-forward" size={16} color={theme.textTertiary} />
        </TouchableOpacity>
      </View>
    );
  };

  // E. Ask CTA
  const renderAskCTA = () => {
    if (!data) return null;
    
    const prompts = [
      "What does my Day Master mean in daily life?",
      "Which element should I focus on activating?",
      "How do my Four Pillars work together?",
    ];
    
    return (
      <View style={[styles.askSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.askTitle, { color: theme.text }]}>Ask About This Lens</Text>
        <Text style={[styles.askSubtitle, { color: theme.textTertiary }]}>
          Explore your chart with Mirror
        </Text>
        
        <View style={styles.promptsList}>
          {prompts.map((prompt, idx) => (
            <InlineReflectButton
              key={idx}
              source={{
                lens: 'bazi',
                type: 'day_master',
                name: 'BaZi Exploration',
                value: `${data.day_master.stem_pinyin} ${data.day_master.element}`,
                id: `bazi_ask_${idx}`,
              }}
              prompt={prompt}
              variant="compact"
            />
          ))}
        </View>
      </View>
    );
  };

  // =============================================================================
  // SNAPSHOT TAB COMPONENTS
  // =============================================================================

  const renderSnapshotPeriod = (
    period: TimingPeriod,
    label: string,
    periodKey: 'today' | 'month' | 'year'
  ) => {
    const interactionColor = INTERACTION_COLORS[period.interaction as keyof typeof INTERACTION_COLORS] || theme.textSecondary;
    const animalData = typeof period.animal === 'object' ? period.animal : { emoji: '', name: period.animal };
    
    // Generate content blocks based on period
    const getContentBlocks = () => {
      if (periodKey === 'today') {
        return {
          block1: { label: 'What may be happening', text: period.description },
          block2: { label: 'Tension to notice', text: period.interaction === 'pressure' 
            ? "You may feel more observed or held to expectations. Stay flexible with how things unfold."
            : "Energy may flow more easily, though watch for overcommitment or scattered focus." },
          block3: { label: 'Best use of today', text: period.interaction === 'supporting'
            ? "A good day for expression, collaboration, or moving things forward."
            : "Prioritize what matters most. Avoid forcing outcomes." },
          reflection: "What feels most important to give attention to today?",
        };
      } else if (periodKey === 'month') {
        return {
          block1: { label: 'Main theme', text: period.description },
          block2: { label: 'Opportunity', text: period.interaction === 'supporting'
            ? "This month may favor visible progress and meaningful connections."
            : "Challenge can clarify priorities. Use pressure to sharpen focus." },
          block3: { label: 'Watch for', text: period.interaction === 'pressure'
            ? "Overcommitment or taking on more than sustainable."
            : "Momentum without direction—stay intentional." },
          reflection: "What do you want this month to be remembered for?",
        };
      } else {
        return {
          block1: { label: 'Big theme', text: period.description },
          block2: { label: 'Growth edge', text: period.interaction === 'supporting'
            ? "This year supports expansion. Trust what's emerging."
            : "This year asks for adaptation. Growth through challenge." },
          block3: { label: 'Pressure pattern', text: period.interaction === 'pressure'
            ? "Increased responsibility or external demands may be present."
            : "Less external pressure, but avoid complacency." },
          reflection: "What are you building this year that matters?",
        };
      }
    };
    
    const content = getContentBlocks();
    
    return (
      <View style={[styles.snapshotCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Header */}
        <View style={styles.snapshotHeader}>
          <View>
            <Text style={[styles.snapshotLabel, { color: theme.textTertiary }]}>{label}</Text>
            <Text style={[styles.snapshotPillar, { color: theme.text }]}>
              {period.pillar} • {animalData.emoji} {animalData.name}
            </Text>
          </View>
          <View style={styles.snapshotMeta}>
            <View style={[styles.elementPill, { backgroundColor: ELEMENT_COLORS[period.element] + '20' }]}>
              <Text style={[styles.elementPillText, { color: ELEMENT_COLORS[period.element] }]}>
                {ELEMENT_ICONS[period.element]} {period.element}
              </Text>
            </View>
            <View style={[styles.tenGodPill, { backgroundColor: theme.background }]}>
              <Text style={[styles.tenGodPillText, { color: theme.textSecondary }]}>
                {period.ten_god_name}
              </Text>
            </View>
          </View>
        </View>
        
        {/* Interaction Badge */}
        <View style={[styles.interactionRow, { borderBottomColor: theme.border }]}>
          <View style={[styles.interactionBadgeLarge, { backgroundColor: interactionColor + '15' }]}>
            <View style={[styles.interactionDot, { backgroundColor: interactionColor }]} />
            <Text style={[styles.interactionLabelText, { color: interactionColor }]}>
              {period.interaction.charAt(0).toUpperCase() + period.interaction.slice(1)}
            </Text>
          </View>
        </View>
        
        {/* Content Blocks */}
        <View style={styles.contentBlocks}>
          <View style={styles.contentBlock}>
            <Text style={[styles.contentBlockLabel, { color: theme.textTertiary }]}>{content.block1.label}</Text>
            <Text style={[styles.contentBlockText, { color: theme.textSecondary }]}>{content.block1.text}</Text>
          </View>
          
          <View style={styles.contentBlock}>
            <Text style={[styles.contentBlockLabel, { color: theme.textTertiary }]}>{content.block2.label}</Text>
            <Text style={[styles.contentBlockText, { color: theme.textSecondary }]}>{content.block2.text}</Text>
          </View>
          
          <View style={styles.contentBlock}>
            <Text style={[styles.contentBlockLabel, { color: theme.textTertiary }]}>{content.block3.label}</Text>
            <Text style={[styles.contentBlockText, { color: theme.textSecondary }]}>{content.block3.text}</Text>
          </View>
        </View>
        
        {/* Reflection */}
        <View style={[styles.reflectionBox, { backgroundColor: theme.background }]}>
          <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>REFLECTION</Text>
          <Text style={[styles.reflectionText, { color: theme.text }]}>{content.reflection}</Text>
        </View>
        
        {/* Ask Button */}
        <View style={styles.askButtonContainer}>
          <InlineReflectButton
            source={{
              lens: 'bazi',
              type: 'timing',
              name: `BaZi ${label}`,
              value: `${period.pillar} - ${period.ten_god_name}`,
              id: `bazi_${periodKey}`,
            }}
            prompt={`Tell me more about ${label.toLowerCase()} and what I might notice.`}
          />
        </View>
      </View>
    );
  };

  // =============================================================================
  // LOADING / ERROR STATES
  // =============================================================================

  if (isLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Reading your Four Pillars...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.errorContainer, { backgroundColor: theme.background }]}>
        <Ionicons name="compass-outline" size={48} color={theme.textTertiary} />
        <Text style={[styles.errorTitle, { color: theme.text }]}>Unable to generate your chart</Text>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
        <TouchableOpacity
          style={[styles.retryButton, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={() => loadBaziData()}
        >
          <Text style={[styles.retryButtonText, { color: theme.text }]}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // =============================================================================
  // MAIN RENDER
  // =============================================================================

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>BaZi</Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          Four Pillars of Destiny
        </Text>
      </View>

      {/* Tab Bar */}
      {renderTabBar()}

      {/* Content */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={theme.textTertiary}
          />
        }
      >
        {activeTab === 'summary' && (
          <>
            {renderCoreSignature()}
            {renderChartPattern()}
            {renderFourPillars()}
            {renderTimingPreview()}
            {renderAskCTA()}
          </>
        )}

        {activeTab === 'snapshot' && data?.timing && (
          <>
            {renderSnapshotPeriod(data.timing.today, 'Today', 'today')}
            {renderSnapshotPeriod(data.timing.month, 'This Month', 'month')}
            {renderSnapshotPeriod(data.timing.year, 'This Year', 'year')}
          </>
        )}

        {/* Footer spacer */}
        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 80,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 14,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 80,
    paddingHorizontal: 32,
  },
  errorTitle: {
    marginTop: 16,
    fontSize: 16,
    fontWeight: '600',
  },
  errorText: {
    marginTop: 8,
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  headerSubtitle: {
    fontSize: 14,
    marginTop: 4,
  },

  // Tab Bar
  tabBar: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 14,
  },

  // Core Signature Card
  signatureCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  signatureHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  elementBadge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  elementIcon: {
    fontSize: 28,
  },
  signatureInfo: {
    flex: 1,
  },
  signatureName: {
    fontSize: 22,
    fontWeight: '700',
  },
  signatureDetail: {
    fontSize: 14,
    marginTop: 2,
  },
  keywordsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 14,
  },
  keywordBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  keywordText: {
    fontSize: 12,
    fontWeight: '500',
  },
  signatureDescription: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 12,
  },
  strengthNote: {
    padding: 12,
    borderRadius: 8,
  },
  strengthNoteText: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },

  // Pattern Card
  patternCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  patternGrid: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 14,
  },
  patternItem: {
    flex: 1,
  },
  patternItemLabel: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 4,
  },
  patternItemValue: {
    fontSize: 15,
    fontWeight: '600',
  },
  patternInterpretation: {
    fontSize: 14,
    lineHeight: 21,
  },

  // Pillars Section
  pillarsSection: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  pillarsGrid: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 12,
  },
  pillarCard: {
    flex: 1,
    padding: 12,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  pillarMeaning: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  pillarAnimal: {
    fontSize: 28,
    marginBottom: 4,
  },
  pillarAnimalName: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 2,
  },
  pillarChars: {
    fontSize: 10,
  },
  pillarElementDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 6,
  },
  pillarsNote: {
    fontSize: 11,
    textAlign: 'center',
    fontStyle: 'italic',
  },

  // Timing Preview
  timingPreviewSection: {
    marginBottom: 16,
  },
  timingPreviewGrid: {
    gap: 10,
  },
  timingPreviewCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  timingPreviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  timingPreviewLabel: {
    fontSize: 13,
    fontWeight: '600',
  },
  interactionBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  interactionText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  timingPreviewDesc: {
    fontSize: 13,
    lineHeight: 18,
  },
  viewSnapshotButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    marginTop: 12,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  viewSnapshotText: {
    fontSize: 14,
    fontWeight: '500',
    marginRight: 4,
  },

  // Ask Section
  askSection: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  askTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  askSubtitle: {
    fontSize: 13,
    marginBottom: 14,
  },
  promptsList: {
    gap: 10,
  },

  // Snapshot Cards
  snapshotCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
    overflow: 'hidden',
  },
  snapshotHeader: {
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  snapshotLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  snapshotPillar: {
    fontSize: 17,
    fontWeight: '600',
  },
  snapshotMeta: {
    alignItems: 'flex-end',
    gap: 6,
  },
  elementPill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  elementPillText: {
    fontSize: 12,
    fontWeight: '600',
  },
  tenGodPill: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  tenGodPillText: {
    fontSize: 11,
    fontWeight: '500',
  },
  interactionRow: {
    paddingHorizontal: 16,
    paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  interactionBadgeLarge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  interactionDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  interactionLabelText: {
    fontSize: 13,
    fontWeight: '600',
  },
  contentBlocks: {
    padding: 16,
    gap: 16,
  },
  contentBlock: {},
  contentBlockLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  contentBlockText: {
    fontSize: 14,
    lineHeight: 20,
  },
  reflectionBox: {
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 14,
    borderRadius: 10,
  },
  reflectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  reflectionText: {
    fontSize: 15,
    fontWeight: '500',
    fontStyle: 'italic',
    lineHeight: 22,
  },
  askButtonContainer: {
    padding: 16,
    paddingTop: 0,
  },
});
