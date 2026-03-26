/**
 * BaZi Lens View V2 - Stable v1.1
 * 
 * A sovereign lens for Four Pillars of Destiny.
 * 
 * Features:
 * - 3-tab structure: Summary, Snapshot, Deep Dive
 * - Classical Zi Ping calculations with Mirror language
 * - Day Master profile with behavioral descriptions
 * - Four Pillars with animal visuals
 * - Timing interactions (Today/Month/Year)
 * - Deep Dive: Ten Gods, Hidden Dynamics, Life Pattern
 * - Ask About This Lens → Opens MirrorChat (NOT reflection modal)
 * - Suggested questions as optional starters
 * 
 * Cross-Lens Architecture:
 * - Backend outputs `pattern_domains` for future synthesis
 * - Domains: self, relationships, work, stress, growth, timing
 * - NO forced mapping to other frameworks (HD, Enneagram, etc.)
 * - Each lens remains sovereign
 * 
 * @version 1.1
 * @date 2026-03-18
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
import api from '../services/api';
import KeystoneReferenceLink from './KeystoneReferenceLink';

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
  wow_line?: string;
  why_pattern?: string;
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
  deep_dive?: DeepDiveV2;
  birth_data: {
    date: string;
    time: string;
    timezone: string | null;
    chinese_year: number;
    bazi_month: number;
  };
  calculation_version: string;
}

// Deep Dive Interfaces
interface DayMasterAnalysis {
  strength_real: string;
  reasoning: string[];
  implication: string;
}

interface TenGodDetailed {
  name: string;
  label: string;
  wow_line?: string;
  strength: string;
  present_in: string[];
  behavioral_expression: string;
  stress_pattern: string;
  others_experience: string;
  risk: string;
  insight: string;
  tension: string;
  action: string;
  why_pattern?: string;
  go_deeper?: string;
}

interface HiddenDynamic {
  pillar: string;
  pillar_label: string;
  hidden_stem: string;
  hidden_stem_pinyin: string;
  element: string;
  ten_god: string;
  meaning: string;
  behavioral?: string;
  shows_up?: string;
}

interface LifePattern {
  core_drive: string;
  wow_line?: string;
  default_mode: string;
  under_pressure: string;
  growth_direction: string;
  why_pattern?: string;
}

interface DeepDiveV2 {
  day_master_analysis: DayMasterAnalysis;
  favorable_elements: string[];
  unfavorable_elements: string[];
  ten_gods_detailed: TenGodDetailed[];
  hidden_dynamics: HiddenDynamic[];
  life_pattern: LifePattern;
}

// Adaptive Intelligence Interfaces
interface RealLifeChecks {
  day_master: {
    work: string;
    relationships: string;
    leadership: string;
    stress: string;
  };
  ten_gods: Record<string, { work: string; relationships: string }>;
}

interface TodayConnections {
  main: string;
  core_pattern: string;
  ten_god_specific: string;
  pressure_note: string | null;
}

interface AdaptiveContent {
  real_life_checks: RealLifeChecks;
  today_connections: TodayConnections;
  contextual_prompts: string[];
  reflection_prompts: string[];
  language_modifiers: Record<string, {
    confidence: string;
    prefix: string;
    suffix: string;
    tone: string;
  }>;
}

interface FeedbackMap {
  [key: string]: 'yes' | 'somewhat' | 'no';
}

// BaZi Today interface - from unified timing intelligence
interface BaziTodayData {
  success: boolean;
  user_id: string;
  date: string;
  today_tone: {
    element: string;
    stem: string;
    branch: string;
    meaning: string;
  };
  what_is_active: {
    ten_gods: string[];
    interactions: string[];
    strength_shift: string;
    element_balance: {
      dominant: string;
      branch: string;
      relationship: string;
    };
  };
  where_it_lands: {
    implication: string;
    behavioral_hint: string;
  };
  what_to_watch: {
    pressure_points: string[];
    risk_note: string;
  };
  what_helps_now: {
    practical: string;
    element_support: string;
  };
  pattern_link: string;
}

interface BaziResponseV2 {
  success: boolean;
  user_id: string;
  has_birth_time: boolean;
  chart: BaziChartV2;
}

interface Props {
  userId: string;
  onOpenChat: (initialMessage?: string) => void;
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

type TabType = 'summary' | 'today' | 'snapshot' | 'deep_dive';

export default function BaziLensView({ userId, onOpenChat }: Props) {
  const { theme, isDark } = useTheme();
  
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [data, setData] = useState<BaziChartV2 | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Adaptive Intelligence State
  const [adaptive, setAdaptive] = useState<AdaptiveContent | null>(null);
  const [feedbackMap, setFeedbackMap] = useState<FeedbackMap>({});
  const [feedbackSubmitting, setFeedbackSubmitting] = useState<string | null>(null);
  
  // BaZi Today State
  const [baziToday, setBaziToday] = useState<BaziTodayData | null>(null);
  const [baziTodayLoading, setBaziTodayLoading] = useState(false);

  // Load BaZi data with adaptive content
  const loadBaziData = useCallback(async (refresh = false) => {
    if (refresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      // Load chart, adaptive content, feedback, and today data
      const [chartResponse, adaptiveResponse, feedbackResponse, todayResponse] = await Promise.all([
        api.get<BaziResponseV2>(`/bazi/${userId}/full`),
        api.get(`/bazi/${userId}/adaptive`).catch(() => null),
        api.get(`/bazi/${userId}/feedback`).catch(() => null),
        api.get<BaziTodayData>(`/bazi/${userId}/today`).catch(() => null),
      ]);
      
      if (chartResponse.data.success) {
        setData(chartResponse.data.chart);
      } else {
        setError('Failed to load BaZi chart');
      }
      
      // Load adaptive content
      if (adaptiveResponse?.data?.adaptive) {
        setAdaptive(adaptiveResponse.data.adaptive);
      }
      
      // Load existing feedback
      if (feedbackResponse?.data?.feedback_map) {
        setFeedbackMap(feedbackResponse.data.feedback_map);
      }
      
      // Load BaZi Today
      if (todayResponse?.data?.success) {
        setBaziToday(todayResponse.data);
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
  
  // Submit feedback handler
  const handleFeedback = async (section: string, rating: 'yes' | 'somewhat' | 'no', subsection?: string) => {
    const feedbackKey = subsection ? `${section}:${subsection}` : section;
    setFeedbackSubmitting(feedbackKey);
    
    try {
      await api.post(`/bazi/${userId}/feedback`, {
        section,
        rating,
        subsection: subsection || null,
      });
      
      // Update local state
      setFeedbackMap(prev => ({
        ...prev,
        [feedbackKey]: rating,
      }));
      
      // Refresh adaptive content after feedback
      const adaptiveResponse = await api.get(`/bazi/${userId}/adaptive`).catch(() => null);
      if (adaptiveResponse?.data?.adaptive) {
        setAdaptive(adaptiveResponse.data.adaptive);
      }
    } catch (err) {
      console.error('[BaZi Feedback] Error:', err);
    } finally {
      setFeedbackSubmitting(null);
    }
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
        style={[styles.tab, activeTab === 'today' && styles.activeTab]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'today' && { color: theme.text, fontWeight: '600' }]}>
          Today
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'snapshot' && styles.activeTab]}
        onPress={() => setActiveTab('snapshot')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'snapshot' && { color: theme.text, fontWeight: '600' }]}>
          Timing
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text, fontWeight: '600' }]}>
          Deep Dive
        </Text>
      </TouchableOpacity>
    </View>
  );
  
  // Tab blurbs - short descriptions of each tab's focus
  const TAB_BLURBS: Record<TabType, { title: string; blurb: string }> = {
    summary: {
      title: "Your Core Signature",
      blurb: "The fundamental energy that shapes how you move through life.",
    },
    today: {
      title: "Today's Element Energy",
      blurb: "What BaZi energy is active today and how it may affect you.",
    },
    snapshot: {
      title: "Current Timing",
      blurb: "What today, this month, and this year are activating in your chart.",
    },
    deep_dive: {
      title: "Deeper Patterns",
      blurb: "The behavioral tendencies and hidden dynamics that shape your experience.",
    },
  };
  
  const renderTabBlurb = () => {
    const content = TAB_BLURBS[activeTab];
    return (
      <View style={styles.tabBlurbContainer}>
        <Text style={[styles.tabBlurbTitle, { color: theme.text }]}>{content.title}</Text>
        <Text style={[styles.tabBlurbText, { color: theme.textTertiary }]}>{content.blurb}</Text>
      </View>
    );
  };

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

  // =============================================================================
  // UNIFIED ASK SECTION - Primary CTA + Suggested Questions
  // =============================================================================
  
  // Default prompts per tab (hidden context passed to chat)
  const getDefaultPromptForTab = (tab: TabType): string => {
    switch (tab) {
      case 'summary':
        return "What stands out most in my BaZi chart?";
      case 'today':
        return "How does today's BaZi energy affect me specifically?";
      case 'snapshot':
        return "What is my chart being asked to pay attention to right now?";
      case 'deep_dive':
        return "What deeper BaZi pattern is most important for me to understand?";
      default:
        return "Tell me about my BaZi chart.";
    }
  };
  
  // Get suggested questions based on tab
  const getSuggestedQuestions = (tab: TabType): string[] => {
    const contextualPrompts = adaptive?.contextual_prompts || [];
    
    // Tab-specific fallback suggestions
    const fallbackSuggestions: Record<TabType, string[]> = {
      summary: [
        "What does my Day Master mean in daily life?",
        "Which element should I focus on activating?",
        "How do my Four Pillars work together?",
      ],
      today: [
        "How should I approach today based on this energy?",
        "What pressure points should I watch for today?",
        "How does today's element interact with my chart?",
      ],
      snapshot: [
        "What should I pay attention to today?",
        "What's the main theme of this month for me?",
        "What is this year asking me to learn?",
      ],
      deep_dive: [
        "Why do I behave this way under pressure?",
        "What pattern keeps showing up in my life?",
        "What am I not seeing about myself?",
      ],
    };
    
    // Use contextual prompts if available, otherwise use fallbacks
    if (contextualPrompts.length > 0) {
      return contextualPrompts.slice(0, 4);
    }
    return fallbackSuggestions[tab] || fallbackSuggestions.summary;
  };
  
  // Open chat in open-ended mode (no pre-filled question)
  const handleOpenEndedAsk = () => {
    onOpenChat(); // Open chat without a pre-filled question
  };
  
  // Open chat with a specific question pre-filled
  const handleSuggestedQuestionTap = (question: string) => {
    onOpenChat(question); // Open chat with the tapped question pre-filled
  };
  
  // Render the unified Ask section for any tab
  const renderUnifiedAskSection = (tab: TabType) => {
    if (!data) return null;
    
    const suggestedQuestions = getSuggestedQuestions(tab);
    
    return (
      <View style={[styles.unifiedAskSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        {/* Primary CTA - Open-ended Ask */}
        <TouchableOpacity
          style={[styles.primaryAskButton, { backgroundColor: theme.accent }]}
          onPress={handleOpenEndedAsk}
          activeOpacity={0.8}
        >
          <Ionicons name="chatbubble-outline" size={20} color="#FFFFFF" />
          <Text style={styles.primaryAskButtonText}>Ask About This Lens</Text>
        </TouchableOpacity>
        
        <Text style={[styles.primaryAskSubtext, { color: theme.textTertiary }]}>
          Ask anything about this chart, this timing, or what it means in your life.
        </Text>
        
        {/* Suggested Questions - Optional Starters */}
        {suggestedQuestions.length > 0 && (
          <View style={styles.suggestedQuestionsSection}>
            <Text style={[styles.suggestedQuestionsLabel, { color: theme.textTertiary }]}>
              SUGGESTED QUESTIONS
            </Text>
            <View style={styles.suggestedQuestionsList}>
              {suggestedQuestions.map((question, idx) => (
                <TouchableOpacity
                  key={idx}
                  style={[styles.suggestedQuestionChip, { backgroundColor: theme.background, borderColor: theme.border }]}
                  onPress={() => handleSuggestedQuestionTap(question)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.suggestedQuestionText, { color: theme.text }]} numberOfLines={2}>
                    {question}
                  </Text>
                  <Ionicons name="arrow-forward" size={14} color={theme.textTertiary} style={{ marginLeft: 8 }} />
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
      </View>
    );
  };

  // =============================================================================
  // BAZI TODAY TAB COMPONENTS
  // =============================================================================

  // Today's Tone - Element energy card
  const renderTodayTone = () => {
    if (!baziToday) return null;
    const { today_tone } = baziToday;
    
    const elementColor = ELEMENT_COLORS[today_tone.element] || theme.text;
    
    return (
      <View style={[styles.todayToneCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={[styles.todayToneHeader, { borderBottomColor: theme.border }]}>
          <View style={[styles.todayElementBadge, { backgroundColor: elementColor + '20' }]}>
            <Text style={styles.todayElementIcon}>{ELEMENT_ICONS[today_tone.element]}</Text>
            <Text style={[styles.todayElementName, { color: elementColor }]}>{today_tone.element}</Text>
          </View>
          <View style={styles.todayDateInfo}>
            <Text style={[styles.todayDateLabel, { color: theme.textTertiary }]}>{baziToday.date}</Text>
            <Text style={[styles.todayStemBranch, { color: theme.textSecondary }]}>
              {today_tone.stem} {today_tone.branch}
            </Text>
          </View>
        </View>
        
        <Text style={[styles.todayToneMeaning, { color: theme.text }]}>
          {today_tone.meaning}
        </Text>
      </View>
    );
  };

  // What is Active - Ten Gods and Interactions
  const renderWhatIsActive = () => {
    if (!baziToday) return null;
    const { what_is_active } = baziToday;
    
    const getInteractionColor = (interaction: string) => {
      if (interaction === 'pressure' || interaction === 'drain') return '#FF5722';
      if (interaction === 'support' || interaction === 'opportunity') return '#4CAF50';
      return '#FF9800';
    };

    const getTenGodLabel = (god: string) => {
      const labels: Record<string, string> = {
        'officer': 'Officer (Authority)',
        'wealth': 'Wealth (Opportunity)',
        'output': 'Output (Expression)',
        'resource': 'Resource (Support)',
        'companion': 'Companion (Equality)',
      };
      return labels[god] || god.charAt(0).toUpperCase() + god.slice(1);
    };
    
    return (
      <View style={[styles.whatIsActiveCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>WHAT IS ACTIVE</Text>
        
        {/* Ten Gods */}
        <View style={styles.tenGodsRow}>
          {what_is_active.ten_gods.map((god, idx) => (
            <View key={idx} style={[styles.tenGodBadge, { backgroundColor: theme.background }]}>
              <Text style={[styles.tenGodBadgeText, { color: theme.text }]}>{getTenGodLabel(god)}</Text>
            </View>
          ))}
        </View>
        
        {/* Interactions */}
        <View style={styles.interactionsRow}>
          {what_is_active.interactions.map((interaction, idx) => (
            <View key={idx} style={[styles.interactionBadgeLg, { backgroundColor: getInteractionColor(interaction) + '15' }]}>
              <View style={[styles.interactionDotLg, { backgroundColor: getInteractionColor(interaction) }]} />
              <Text style={[styles.interactionLabelLg, { color: getInteractionColor(interaction) }]}>
                {interaction.charAt(0).toUpperCase() + interaction.slice(1)}
              </Text>
            </View>
          ))}
        </View>
        
        {/* Strength Shift */}
        <View style={[styles.strengthShiftBox, { backgroundColor: theme.background }]}>
          <Text style={[styles.strengthShiftLabel, { color: theme.textTertiary }]}>ENERGY SHIFT</Text>
          <Text style={[styles.strengthShiftValue, { 
            color: what_is_active.strength_shift === 'stronger' ? '#4CAF50' : 
                   what_is_active.strength_shift === 'weaker' ? '#FF5722' : theme.text 
          }]}>
            {what_is_active.strength_shift === 'stronger' ? '↑ Stronger' : 
             what_is_active.strength_shift === 'weaker' ? '↓ Weaker' : '→ Balanced'}
          </Text>
        </View>
      </View>
    );
  };

  // Where It Lands - Behavioral implications
  const renderWhereItLands = () => {
    if (!baziToday) return null;
    const { where_it_lands } = baziToday;
    
    return (
      <View style={[styles.whereItLandsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>WHERE IT MAY LAND</Text>
        
        <Text style={[styles.todayImplicationText, { color: theme.text }]}>
          {where_it_lands.implication}
        </Text>
        
        <View style={[styles.behavioralHintBox, { backgroundColor: theme.background }]}>
          <Ionicons name="body-outline" size={16} color={theme.textTertiary} />
          <Text style={[styles.behavioralHintText, { color: theme.textSecondary }]}>
            {where_it_lands.behavioral_hint}
          </Text>
        </View>
      </View>
    );
  };

  // What to Watch - Pressure points and risks
  const renderWhatToWatch = () => {
    if (!baziToday) return null;
    const { what_to_watch } = baziToday;
    
    return (
      <View style={[styles.whatToWatchCard, { backgroundColor: '#FF572208', borderColor: '#FF572230' }]}>
        <View style={styles.watchHeaderRow}>
          <Ionicons name="warning-outline" size={18} color="#FF5722" />
          <Text style={[styles.watchHeaderText, { color: '#FF5722' }]}>WHAT TO WATCH</Text>
        </View>
        
        {/* Pressure Points */}
        <View style={styles.pressurePointsList}>
          {what_to_watch.pressure_points.map((point, idx) => (
            <View key={idx} style={styles.pressurePointItem}>
              <Text style={[styles.pressurePointBullet, { color: '#FF5722' }]}>•</Text>
              <Text style={[styles.pressurePointText, { color: theme.text }]}>{point}</Text>
            </View>
          ))}
        </View>
        
        {/* Risk Note */}
        <View style={[styles.riskNoteBox, { backgroundColor: '#FF572210' }]}>
          <Text style={[styles.riskNoteText, { color: theme.textSecondary }]}>
            {what_to_watch.risk_note}
          </Text>
        </View>
      </View>
    );
  };

  // What Helps Now - Practical guidance
  const renderWhatHelpsNow = () => {
    if (!baziToday) return null;
    const { what_helps_now } = baziToday;
    
    const elementColor = ELEMENT_COLORS[baziToday.today_tone.element] || '#4CAF50';
    
    return (
      <View style={[styles.whatHelpsNowCard, { backgroundColor: '#4CAF5008', borderColor: '#4CAF5030' }]}>
        <View style={styles.helpsHeaderRow}>
          <Ionicons name="leaf-outline" size={18} color="#4CAF50" />
          <Text style={[styles.helpsHeaderText, { color: '#4CAF50' }]}>WHAT HELPS NOW</Text>
        </View>
        
        {/* Practical Guidance */}
        <Text style={[styles.practicalText, { color: theme.text }]}>
          {what_helps_now.practical}
        </Text>
        
        {/* Element Support */}
        <View style={[styles.elementSupportBox, { backgroundColor: elementColor + '10' }]}>
          <Text style={styles.elementSupportIcon}>{ELEMENT_ICONS[baziToday.today_tone.element]}</Text>
          <Text style={[styles.elementSupportText, { color: theme.textSecondary }]}>
            {what_helps_now.element_support}
          </Text>
        </View>
      </View>
    );
  };

  // Pattern Link - Connection to current pattern
  const renderPatternLink = () => {
    if (!baziToday?.pattern_link) return null;
    
    return (
      <View style={[styles.patternLinkCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.patternLinkHeader}>
          <Ionicons name="git-merge-outline" size={16} color={theme.accent} />
          <Text style={[styles.patternLinkLabel, { color: theme.accent }]}>PATTERN CONNECTION</Text>
        </View>
        <Text style={[styles.patternLinkText, { color: theme.textSecondary }]}>
          {baziToday.pattern_link}
        </Text>
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
      </View>
    );
  };

  // =============================================================================
  // DEEP DIVE TAB COMPONENTS
  // =============================================================================

  // Feedback Micro-Interaction Component
  const renderFeedbackBlock = (section: string, subsection?: string) => {
    const feedbackKey = subsection ? `${section}:${subsection}` : section;
    const currentRating = feedbackMap[feedbackKey];
    const isSubmitting = feedbackSubmitting === feedbackKey;
    
    if (currentRating) {
      // Show confirmed feedback
      return (
        <View style={[styles.feedbackConfirmed, { backgroundColor: theme.background }]}>
          <Ionicons 
            name={currentRating === 'yes' ? 'checkmark-circle' : currentRating === 'somewhat' ? 'remove-circle' : 'close-circle'} 
            size={16} 
            color={currentRating === 'yes' ? '#4CAF50' : currentRating === 'somewhat' ? '#FF9800' : '#FF5722'} 
          />
          <Text style={[styles.feedbackConfirmedText, { color: theme.textTertiary }]}>
            {currentRating === 'yes' ? 'This resonates with you' : 
             currentRating === 'somewhat' ? 'Partially resonates' : 
             'Noted — we\'ll adjust the framing'}
          </Text>
        </View>
      );
    }
    
    return (
      <View style={[styles.feedbackBlock, { backgroundColor: theme.background, borderColor: theme.border }]}>
        <Text style={[styles.feedbackQuestion, { color: theme.textSecondary }]}>Does this feel true?</Text>
        <View style={styles.feedbackButtons}>
          <TouchableOpacity 
            style={[styles.feedbackBtn, { backgroundColor: '#4CAF5015', borderColor: '#4CAF5030' }]}
            onPress={() => handleFeedback(section, 'yes', subsection)}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator size="small" color="#4CAF50" />
            ) : (
              <>
                <Ionicons name="checkmark" size={16} color="#4CAF50" />
                <Text style={[styles.feedbackBtnText, { color: '#4CAF50' }]}>Yes, this fits me</Text>
              </>
            )}
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.feedbackBtn, { backgroundColor: '#FF980015', borderColor: '#FF980030' }]}
            onPress={() => handleFeedback(section, 'somewhat', subsection)}
            disabled={isSubmitting}
          >
            <Ionicons name="remove" size={16} color="#FF9800" />
            <Text style={[styles.feedbackBtnText, { color: '#FF9800' }]}>Somewhat</Text>
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.feedbackBtn, { backgroundColor: '#FF572215', borderColor: '#FF572230' }]}
            onPress={() => handleFeedback(section, 'no', subsection)}
            disabled={isSubmitting}
          >
            <Ionicons name="close" size={16} color="#FF5722" />
            <Text style={[styles.feedbackBtnText, { color: '#FF5722' }]}>Not really</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  };
  
  // Real Life Check Component
  const renderRealLifeCheck = (section: 'day_master' | 'ten_gods', godName?: string) => {
    if (!adaptive?.real_life_checks) return null;
    
    let checks: { work: string; relationships: string; leadership?: string; stress?: string } | undefined;
    
    if (section === 'day_master') {
      checks = adaptive.real_life_checks.day_master;
    } else if (section === 'ten_gods' && godName) {
      checks = adaptive.real_life_checks.ten_gods[godName];
    }
    
    if (!checks) return null;
    
    return (
      <View style={[styles.realLifeCheckBox, { backgroundColor: theme.background, borderColor: theme.border }]}>
        <Text style={[styles.realLifeCheckTitle, { color: theme.textTertiary }]}>WHERE THIS SHOWS UP IN REAL LIFE</Text>
        <View style={styles.realLifeCheckItems}>
          {checks.work && (
            <View style={styles.realLifeCheckItem}>
              <Ionicons name="briefcase-outline" size={14} color={theme.textTertiary} />
              <Text style={[styles.realLifeCheckText, { color: theme.textSecondary }]}><Text style={{ fontWeight: '600' }}>Work:</Text> {checks.work}</Text>
            </View>
          )}
          {checks.relationships && (
            <View style={styles.realLifeCheckItem}>
              <Ionicons name="people-outline" size={14} color={theme.textTertiary} />
              <Text style={[styles.realLifeCheckText, { color: theme.textSecondary }]}><Text style={{ fontWeight: '600' }}>Relationships:</Text> {checks.relationships}</Text>
            </View>
          )}
          {checks.leadership && (
            <View style={styles.realLifeCheckItem}>
              <Ionicons name="flag-outline" size={14} color={theme.textTertiary} />
              <Text style={[styles.realLifeCheckText, { color: theme.textSecondary }]}><Text style={{ fontWeight: '600' }}>Leadership:</Text> {checks.leadership}</Text>
            </View>
          )}
          {checks.stress && (
            <View style={styles.realLifeCheckItem}>
              <Ionicons name="warning-outline" size={14} color={theme.textTertiary} />
              <Text style={[styles.realLifeCheckText, { color: theme.textSecondary }]}><Text style={{ fontWeight: '600' }}>Under Stress:</Text> {checks.stress}</Text>
            </View>
          )}
        </View>
      </View>
    );
  };
  
  // Today Connection Component
  const renderTodayConnection = () => {
    if (!adaptive?.today_connections || !data?.timing) return null;
    const { today_connections } = adaptive;
    const todayInteraction = data.timing.today.interaction;
    
    return (
      <View style={[styles.todayConnectionBox, { 
        backgroundColor: todayInteraction === 'pressure' ? '#FF572208' : todayInteraction === 'supporting' ? '#4CAF5008' : '#FF980008',
        borderColor: todayInteraction === 'pressure' ? '#FF572230' : todayInteraction === 'supporting' ? '#4CAF5030' : '#FF980030',
      }]}>
        <View style={styles.todayConnectionHeader}>
          <Ionicons 
            name="today-outline" 
            size={16} 
            color={todayInteraction === 'pressure' ? '#FF5722' : todayInteraction === 'supporting' ? '#4CAF50' : '#FF9800'} 
          />
          <Text style={[styles.todayConnectionLabel, { 
            color: todayInteraction === 'pressure' ? '#FF5722' : todayInteraction === 'supporting' ? '#4CAF50' : '#FF9800'
          }]}>
            TODAY CONNECTION
          </Text>
        </View>
        <Text style={[styles.todayConnectionText, { color: theme.text }]}>
          {today_connections.main}
        </Text>
        {today_connections.core_pattern && (
          <Text style={[styles.todayConnectionSubtext, { color: theme.textSecondary }]}>
            {today_connections.core_pattern}
          </Text>
        )}
        {today_connections.pressure_note && (
          <View style={[styles.pressureNoteBox, { backgroundColor: '#FF572210' }]}>
            <Text style={[styles.pressureNoteText, { color: '#FF5722' }]}>
              ⚠️ {today_connections.pressure_note}
            </Text>
          </View>
        )}
      </View>
    );
  };
  
  // Reflection Prompts Component
  const renderReflectionPrompts = () => {
    if (!adaptive?.reflection_prompts || !data) return null;
    const { reflection_prompts } = adaptive;
    
    return (
      <View style={[styles.reflectionPromptsBox, { backgroundColor: theme.background }]}>
        <Text style={[styles.reflectionPromptsTitle, { color: theme.textTertiary }]}>REFLECTION MODE</Text>
        {reflection_prompts.map((prompt, idx) => (
          <View key={idx} style={styles.reflectionPromptItem}>
            <Text style={[styles.reflectionPromptText, { color: theme.text }]}>• {prompt}</Text>
          </View>
        ))}
      </View>
    );
  };

  // 1. Your Core Engine
  const renderCoreEngine = () => {
    if (!data?.deep_dive) return null;
    const { day_master, deep_dive } = data;
    const { day_master_analysis } = deep_dive;
    
    return (
      <View style={[styles.deepDiveSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.deepDiveSectionTitle, { color: theme.text }]}>Your Core Engine</Text>
        
        {/* Day Master Identity */}
        <View style={styles.coreEngineHeader}>
          <View style={[styles.elementBadgeLarge, { backgroundColor: ELEMENT_COLORS[day_master.element] + '20' }]}>
            <Text style={styles.elementIconLarge}>{ELEMENT_ICONS[day_master.element]}</Text>
          </View>
          <View style={styles.coreEngineInfo}>
            <Text style={[styles.coreEngineName, { color: theme.text }]}>
              {day_master.stem_pinyin} {day_master.element}
            </Text>
            <View style={[styles.strengthBadge, { 
              backgroundColor: day_master_analysis.strength_real === 'strong' ? '#4CAF5020' : 
                               day_master_analysis.strength_real === 'weak' ? '#FF572220' : '#FF980020'
            }]}>
              <Text style={[styles.strengthBadgeText, { 
                color: day_master_analysis.strength_real === 'strong' ? '#4CAF50' : 
                       day_master_analysis.strength_real === 'weak' ? '#FF5722' : '#FF9800'
              }]}>
                {day_master_analysis.strength_real.toUpperCase()} Day Master
              </Text>
            </View>
          </View>
        </View>
        
        {/* Wow Line */}
        {day_master.wow_line && (
          <View style={[styles.wowLineBox, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
            <Text style={[styles.wowLineText, { color: theme.text }]}>
              "{day_master.wow_line}"
            </Text>
          </View>
        )}
        
        {/* Strength Reasoning */}
        <View style={[styles.reasoningBox, { backgroundColor: theme.background }]}>
          <Text style={[styles.reasoningTitle, { color: theme.textTertiary }]}>WHY YOUR DAY MASTER IS {day_master_analysis.strength_real.toUpperCase()}</Text>
          {day_master_analysis.reasoning.map((reason, idx) => (
            <View key={idx} style={styles.reasoningItem}>
              <Text style={[styles.reasoningBullet, { color: theme.textTertiary }]}>•</Text>
              <Text style={[styles.reasoningText, { color: theme.textSecondary }]}>{reason}</Text>
            </View>
          ))}
        </View>
        
        {/* Implication */}
        <View style={styles.implicationBox}>
          <Text style={[styles.implicationLabel, { color: theme.textTertiary }]}>WHAT THIS MEANS</Text>
          <Text style={[styles.implicationText, { color: theme.text }]}>
            {day_master_analysis.implication}
          </Text>
        </View>
        
        {/* Why This Pattern Exists */}
        {day_master.why_pattern && (
          <View style={[styles.whyPatternBox, { backgroundColor: theme.background }]}>
            <Text style={[styles.whyPatternLabel, { color: theme.textTertiary }]}>WHY THIS PATTERN EXISTS IN YOUR CHART</Text>
            <Text style={[styles.whyPatternText, { color: theme.textSecondary }]}>{day_master.why_pattern}</Text>
          </View>
        )}
        
        {/* Real Life Check */}
        {renderRealLifeCheck('day_master')}
        
        {/* Today Connection */}
        {renderTodayConnection()}
        
        {/* Feedback Micro-Interaction */}
        {renderFeedbackBlock('day_master')}
      </View>
    );
  };

  // 2. What Supports vs Drains
  const renderSupportsAndDrains = () => {
    if (!data?.deep_dive) return null;
    const { favorable_elements, unfavorable_elements } = data.deep_dive;
    
    return (
      <View style={[styles.deepDiveSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.deepDiveSectionTitle, { color: theme.text }]}>What Supports vs Drains You</Text>
        
        <View style={styles.supportsGrid}>
          {/* Supports */}
          <View style={[styles.supportsCard, { backgroundColor: '#4CAF5010', borderColor: '#4CAF5030' }]}>
            <Text style={[styles.supportsLabel, { color: '#4CAF50' }]}>SUPPORTS</Text>
            <Text style={[styles.supportsDescription, { color: theme.textTertiary }]}>
              What helps you function better
            </Text>
            <View style={styles.elementsList}>
              {favorable_elements.map((elem, idx) => (
                <View key={idx} style={styles.elementItem}>
                  <Text style={styles.elementItemIcon}>{ELEMENT_ICONS[elem]}</Text>
                  <Text style={[styles.elementItemName, { color: theme.text }]}>{elem}</Text>
                </View>
              ))}
            </View>
          </View>
          
          {/* Drains */}
          <View style={[styles.supportsCard, { backgroundColor: '#FF572210', borderColor: '#FF572230' }]}>
            <Text style={[styles.supportsLabel, { color: '#FF5722' }]}>DRAINS</Text>
            <Text style={[styles.supportsDescription, { color: theme.textTertiary }]}>
              What creates friction or fatigue
            </Text>
            <View style={styles.elementsList}>
              {unfavorable_elements.map((elem, idx) => (
                <View key={idx} style={styles.elementItem}>
                  <Text style={styles.elementItemIcon}>{ELEMENT_ICONS[elem]}</Text>
                  <Text style={[styles.elementItemName, { color: theme.text }]}>{elem}</Text>
                </View>
              ))}
            </View>
          </View>
        </View>
      </View>
    );
  };

  // 3. Behavioral Patterns (Ten Gods)
  const renderBehavioralPatterns = () => {
    if (!data?.deep_dive?.ten_gods_detailed) return null;
    const { ten_gods_detailed } = data.deep_dive;
    
    if (ten_gods_detailed.length === 0) return null;
    
    return (
      <View style={[styles.deepDiveSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.deepDiveSectionTitle, { color: theme.text }]}>Your Behavioral Patterns</Text>
        <Text style={[styles.deepDiveSubtitle, { color: theme.textTertiary }]}>
          How the Ten Gods express through you
        </Text>
        
        {ten_gods_detailed.slice(0, 3).map((god, idx) => (
          <View key={idx} style={[styles.tenGodCard, { backgroundColor: theme.background, borderColor: theme.border }]}>
            {/* Header */}
            <View style={styles.tenGodHeader}>
              <View>
                <Text style={[styles.tenGodName, { color: theme.text }]}>{god.label}</Text>
                <View style={styles.tenGodPresence}>
                  {god.present_in.length > 0 && (
                    <Text style={[styles.tenGodPresenceText, { color: theme.textTertiary }]}>
                      Present in: {god.present_in.join(', ')}
                    </Text>
                  )}
                </View>
              </View>
              <View style={[styles.tenGodStrengthBadge, { 
                backgroundColor: god.strength === 'high' ? '#4CAF5020' : god.strength === 'moderate' ? '#FF980020' : theme.surface
              }]}>
                <Text style={[styles.tenGodStrengthText, { 
                  color: god.strength === 'high' ? '#4CAF50' : god.strength === 'moderate' ? '#FF9800' : theme.textTertiary
                }]}>
                  {god.strength}
                </Text>
              </View>
            </View>
            
            {/* Behavioral Expression */}
            <Text style={[styles.tenGodBehavior, { color: theme.textSecondary }]}>
              {god.behavioral_expression}
            </Text>
            
            {/* Insight / Tension / Action */}
            <View style={styles.tenGodITA}>
              <View style={[styles.itaBox, { backgroundColor: theme.surface }]}>
                <Text style={[styles.itaLabel, { color: '#4CAF50' }]}>INSIGHT</Text>
                <Text style={[styles.itaText, { color: theme.text }]}>{god.insight}</Text>
              </View>
              <View style={[styles.itaBox, { backgroundColor: theme.surface }]}>
                <Text style={[styles.itaLabel, { color: '#FF9800' }]}>TENSION</Text>
                <Text style={[styles.itaText, { color: theme.text }]}>{god.tension}</Text>
              </View>
              <View style={[styles.itaBox, { backgroundColor: theme.surface }]}>
                <Text style={[styles.itaLabel, { color: '#2196F3' }]}>ACTION</Text>
                <Text style={[styles.itaText, { color: theme.text }]}>{god.action}</Text>
              </View>
            </View>
            
            {/* Under Pressure */}
            <View style={[styles.stressBox, { borderColor: theme.border }]}>
              <Text style={[styles.stressLabel, { color: theme.textTertiary }]}>UNDER PRESSURE</Text>
              <Text style={[styles.stressText, { color: theme.textSecondary }]}>{god.stress_pattern}</Text>
            </View>
          </View>
        ))}
      </View>
    );
  };

  // 4. Hidden Layers
  const renderHiddenLayers = () => {
    if (!data?.deep_dive?.hidden_dynamics) return null;
    const { hidden_dynamics } = data.deep_dive;
    
    if (hidden_dynamics.length === 0) return null;
    
    return (
      <View style={[styles.deepDiveSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.deepDiveSectionTitle, { color: theme.text }]}>Hidden Layers</Text>
        <Text style={[styles.deepDiveSubtitle, { color: theme.textTertiary }]}>
          Influences that aren't obvious but affect how you respond internally
        </Text>
        
        {hidden_dynamics.map((dynamic, idx) => (
          <View key={idx} style={[styles.hiddenCard, { backgroundColor: theme.background, borderColor: theme.border }]}>
            <View style={styles.hiddenHeader}>
              <View style={[styles.hiddenElementBadge, { backgroundColor: ELEMENT_COLORS[dynamic.element] + '20' }]}>
                <Text style={styles.hiddenElementIcon}>{ELEMENT_ICONS[dynamic.element]}</Text>
              </View>
              <View style={styles.hiddenInfo}>
                <Text style={[styles.hiddenPillar, { color: theme.textTertiary }]}>{dynamic.pillar_label}</Text>
                <Text style={[styles.hiddenStem, { color: theme.text }]}>
                  {dynamic.hidden_stem_pinyin} ({dynamic.element})
                </Text>
              </View>
              <View style={[styles.hiddenTenGod, { backgroundColor: theme.surface }]}>
                <Text style={[styles.hiddenTenGodText, { color: theme.textSecondary }]}>{dynamic.ten_god}</Text>
              </View>
            </View>
            <Text style={[styles.hiddenMeaning, { color: theme.textSecondary }]}>{dynamic.meaning}</Text>
            
            {/* Behavioral - How this shows up */}
            {dynamic.behavioral && (
              <View style={[styles.hiddenBehavioralBox, { backgroundColor: theme.background }]}>
                <Text style={[styles.hiddenBehavioralLabel, { color: theme.textTertiary }]}>HOW THIS SHOWS UP IN YOU:</Text>
                <Text style={[styles.hiddenBehavioralText, { color: theme.text }]}>{dynamic.behavioral}</Text>
              </View>
            )}
            
            {/* Shows Up - Specific behaviors */}
            {dynamic.shows_up && (
              <Text style={[styles.hiddenShowsUp, { color: theme.textTertiary }]}>
                Examples: {dynamic.shows_up}
              </Text>
            )}
          </View>
        ))}
      </View>
    );
  };

  // 5. Life Pattern
  const renderLifePattern = () => {
    if (!data?.deep_dive?.life_pattern) return null;
    const { life_pattern } = data.deep_dive;
    
    return (
      <View style={[styles.deepDiveSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.deepDiveSectionTitle, { color: theme.text }]}>Your Life Pattern</Text>
        <Text style={[styles.deepDiveSubtitle, { color: theme.textTertiary }]}>
          The core patterns that shape how you move through life
        </Text>
        
        {/* Wow Line */}
        {life_pattern.wow_line && (
          <View style={[styles.wowLineBox, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
            <Text style={[styles.wowLineText, { color: theme.text }]}>
              "{life_pattern.wow_line}"
            </Text>
          </View>
        )}
        
        {/* Core Drive */}
        <View style={[styles.lifePatternCard, { backgroundColor: theme.background }]}>
          <View style={styles.lifePatternHeader}>
            <Ionicons name="flash" size={18} color="#FF9800" />
            <Text style={[styles.lifePatternLabel, { color: '#FF9800' }]}>CORE DRIVE</Text>
          </View>
          <Text style={[styles.lifePatternText, { color: theme.text }]}>{life_pattern.core_drive}</Text>
        </View>
        
        {/* Default Mode */}
        <View style={[styles.lifePatternCard, { backgroundColor: theme.background }]}>
          <View style={styles.lifePatternHeader}>
            <Ionicons name="repeat" size={18} color="#2196F3" />
            <Text style={[styles.lifePatternLabel, { color: '#2196F3' }]}>DEFAULT MODE</Text>
          </View>
          <Text style={[styles.lifePatternText, { color: theme.text }]}>{life_pattern.default_mode}</Text>
        </View>
        
        {/* Under Pressure */}
        <View style={[styles.lifePatternCard, { backgroundColor: '#FF572208' }]}>
          <View style={styles.lifePatternHeader}>
            <Ionicons name="warning" size={18} color="#FF5722" />
            <Text style={[styles.lifePatternLabel, { color: '#FF5722' }]}>UNDER PRESSURE</Text>
          </View>
          <Text style={[styles.lifePatternText, { color: theme.text }]}>{life_pattern.under_pressure}</Text>
        </View>
        
        {/* Growth Direction */}
        <View style={[styles.lifePatternCard, { backgroundColor: '#4CAF5008' }]}>
          <View style={styles.lifePatternHeader}>
            <Ionicons name="trending-up" size={18} color="#4CAF50" />
            <Text style={[styles.lifePatternLabel, { color: '#4CAF50' }]}>GROWTH DIRECTION</Text>
          </View>
          <Text style={[styles.lifePatternText, { color: theme.text }]}>{life_pattern.growth_direction}</Text>
        </View>
        
        {/* Why This Pattern Exists */}
        {life_pattern.why_pattern && (
          <View style={[styles.whyPatternBox, { backgroundColor: theme.background }]}>
            <Text style={[styles.whyPatternLabel, { color: theme.textTertiary }]}>WHY THIS PATTERN EXISTS IN YOUR CHART</Text>
            <Text style={[styles.whyPatternText, { color: theme.textSecondary }]}>{life_pattern.why_pattern}</Text>
          </View>
        )}
        
        {/* Reflection Prompts */}
        {renderReflectionPrompts()}
        
        {/* Feedback Micro-Interaction */}
        {renderFeedbackBlock('life_pattern')}
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
            {renderTabBlurb()}
            {renderCoreSignature()}
            {renderChartPattern()}
            {renderFourPillars()}
            {renderTimingPreview()}
            {renderUnifiedAskSection('summary')}
          </>
        )}

        {activeTab === 'today' && baziToday && (
          <>
            {renderTabBlurb()}
            {renderTodayTone()}
            {renderWhatIsActive()}
            {renderWhereItLands()}
            {renderWhatToWatch()}
            {renderWhatHelpsNow()}
            {renderPatternLink()}
            {renderUnifiedAskSection('today')}
          </>
        )}
        
        {activeTab === 'today' && !baziToday && (
          <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
            <ActivityIndicator size="large" color={theme.accent} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              Loading today's energy...
            </Text>
          </View>
        )}

        {activeTab === 'snapshot' && data?.timing && (
          <>
            {renderTabBlurb()}
            {renderSnapshotPeriod(data.timing.today, 'Today', 'today')}
            {renderSnapshotPeriod(data.timing.month, 'This Month', 'month')}
            {renderSnapshotPeriod(data.timing.year, 'This Year', 'year')}
            {renderUnifiedAskSection('snapshot')}
          </>
        )}

        {activeTab === 'deep_dive' && data?.deep_dive && (
          <>
            {renderTabBlurb()}
            {renderCoreEngine()}
            {renderSupportsAndDrains()}
            {renderBehavioralPatterns()}
            {renderHiddenLayers()}
            {renderLifePattern()}
            {renderUnifiedAskSection('deep_dive')}
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
  
  // Tab Blurb
  tabBlurbContainer: {
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  tabBlurbTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 4,
  },
  tabBlurbText: {
    fontSize: 14,
    lineHeight: 20,
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
  
  // Unified Ask Section (Open-ended + Suggested Questions)
  unifiedAskSection: {
    padding: 20,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  primaryAskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    gap: 10,
  },
  primaryAskButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  primaryAskSubtext: {
    fontSize: 13,
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 20,
    lineHeight: 18,
  },
  suggestedQuestionsSection: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
    paddingTop: 20,
  },
  suggestedQuestionsLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  suggestedQuestionsList: {
    gap: 10,
  },
  suggestedQuestionChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  suggestedQuestionText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
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
  snapshotAskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginBottom: 16,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  snapshotAskEmoji: {
    fontSize: 16,
    marginRight: 10,
  },
  snapshotAskText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
  },

  // =============================================================================
  // DEEP DIVE STYLES
  // =============================================================================

  deepDiveSection: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  deepDiveSectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  deepDiveSubtitle: {
    fontSize: 13,
    marginBottom: 16,
  },

  // Core Engine
  coreEngineHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  elementBadgeLarge: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  elementIconLarge: {
    fontSize: 32,
  },
  coreEngineInfo: {
    flex: 1,
  },
  coreEngineName: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 6,
  },
  strengthBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  strengthBadgeText: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  reasoningBox: {
    padding: 14,
    borderRadius: 10,
    marginBottom: 16,
  },
  reasoningTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  reasoningItem: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  reasoningBullet: {
    fontSize: 14,
    marginRight: 8,
    lineHeight: 20,
  },
  reasoningText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  implicationBox: {
    marginBottom: 16,
  },
  implicationLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  implicationText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '500',
  },

  // Supports & Drains
  supportsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  supportsCard: {
    flex: 1,
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
  },
  supportsLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  supportsDescription: {
    fontSize: 12,
    marginBottom: 12,
  },
  elementsList: {
    gap: 8,
  },
  elementItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  elementItemIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  elementItemName: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Ten Gods
  tenGodCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 14,
  },
  tenGodHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  tenGodName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  tenGodPresence: {
    flexDirection: 'row',
  },
  tenGodPresenceText: {
    fontSize: 11,
  },
  tenGodStrengthBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  tenGodStrengthText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  tenGodBehavior: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 14,
  },
  tenGodITA: {
    gap: 10,
    marginBottom: 14,
  },
  itaBox: {
    padding: 12,
    borderRadius: 8,
  },
  itaLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  itaText: {
    fontSize: 13,
    lineHeight: 19,
  },
  stressBox: {
    padding: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  stressLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  stressText: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },

  // Hidden Layers
  hiddenCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  hiddenHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  hiddenElementBadge: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  hiddenElementIcon: {
    fontSize: 20,
  },
  hiddenInfo: {
    flex: 1,
  },
  hiddenPillar: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  hiddenStem: {
    fontSize: 15,
    fontWeight: '600',
  },
  hiddenTenGod: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  hiddenTenGodText: {
    fontSize: 11,
    fontWeight: '500',
  },
  hiddenMeaning: {
    fontSize: 13,
    lineHeight: 19,
  },

  // Life Pattern
  lifePatternCard: {
    padding: 14,
    borderRadius: 10,
    marginBottom: 12,
  },
  lifePatternHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  lifePatternLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginLeft: 8,
  },
  lifePatternText: {
    fontSize: 14,
    lineHeight: 21,
  },
  askButtonsRow: {
    marginTop: 8,
  },
  
  // Deep Dive Ask Button Style
  deepDiveAskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginTop: 16,
  },
  deepDiveAskEmoji: {
    fontSize: 16,
    marginRight: 10,
  },
  deepDiveAskText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
  },

  // =============================================================================
  // ADAPTIVE INTELLIGENCE STYLES
  // =============================================================================

  // Feedback Block
  feedbackBlock: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginTop: 16,
  },
  feedbackQuestion: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 12,
    textAlign: 'center',
  },
  feedbackButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  feedbackBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    gap: 4,
  },
  feedbackBtnText: {
    fontSize: 12,
    fontWeight: '500',
  },
  feedbackConfirmed: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginTop: 16,
    gap: 8,
  },
  feedbackConfirmedText: {
    fontSize: 12,
    fontStyle: 'italic',
  },

  // Real Life Check
  realLifeCheckBox: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginTop: 16,
  },
  realLifeCheckTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  realLifeCheckItems: {
    gap: 10,
  },
  realLifeCheckItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  realLifeCheckText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },

  // Today Connection
  todayConnectionBox: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginTop: 16,
  },
  todayConnectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  todayConnectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  todayConnectionText: {
    fontSize: 14,
    lineHeight: 21,
    fontWeight: '500',
  },
  todayConnectionSubtext: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 8,
  },
  pressureNoteBox: {
    padding: 10,
    borderRadius: 6,
    marginTop: 10,
  },
  pressureNoteText: {
    fontSize: 12,
    lineHeight: 18,
  },

  // Contextual Prompts
  contextualPromptsBox: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  contextualPromptsTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 14,
  },
  contextualPromptsList: {
    gap: 10,
  },

  // Reflection Prompts
  reflectionPromptsBox: {
    padding: 14,
    borderRadius: 10,
    marginTop: 16,
    marginBottom: 8,
  },
  reflectionPromptsTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  reflectionPromptItem: {
    marginBottom: 6,
  },
  reflectionPromptText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },

  // Wow Line
  wowLineBox: {
    padding: 16,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 16,
    alignItems: 'center',
  },
  wowLineText: {
    fontSize: 16,
    fontWeight: '600',
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 24,
  },

  // Why Pattern
  whyPatternBox: {
    padding: 14,
    borderRadius: 10,
    marginTop: 16,
  },
  whyPatternLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  whyPatternText: {
    fontSize: 13,
    lineHeight: 20,
  },

  // Hidden Layers Behavioral
  hiddenBehavioralBox: {
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
  },
  hiddenBehavioralLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  hiddenBehavioralText: {
    fontSize: 14,
    lineHeight: 20,
  },
  hiddenShowsUp: {
    fontSize: 12,
    marginTop: 8,
    fontStyle: 'italic',
  },

  // Contextual Prompts - Question Buttons
  contextualPromptsHeader: {
    marginBottom: 14,
  },
  contextualPromptsSubtitle: {
    fontSize: 12,
    marginTop: 4,
  },
  questionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  questionButtonContent: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  questionEmoji: {
    fontSize: 18,
    marginRight: 12,
  },
  questionText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '500',
  },
  
  // =============================================================================
  // BAZI TODAY TAB STYLES
  // =============================================================================
  
  // Today's Tone Card
  todayToneCard: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
    overflow: 'hidden',
  },
  todayToneHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  todayElementBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
    gap: 8,
  },
  todayElementIcon: {
    fontSize: 24,
  },
  todayElementName: {
    fontSize: 18,
    fontWeight: '700',
  },
  todayDateInfo: {
    alignItems: 'flex-end',
  },
  todayDateLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  todayStemBranch: {
    fontSize: 16,
    marginTop: 2,
  },
  todayToneMeaning: {
    fontSize: 15,
    lineHeight: 22,
    padding: 16,
  },
  
  // What Is Active Card
  whatIsActiveCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  tenGodsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
    marginBottom: 12,
  },
  tenGodBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  tenGodBadgeText: {
    fontSize: 13,
    fontWeight: '600',
  },
  interactionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 12,
  },
  interactionBadgeLg: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  interactionDotLg: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  interactionLabelLg: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  strengthShiftBox: {
    padding: 12,
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  strengthShiftLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  strengthShiftValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  
  // Where It Lands Card
  whereItLandsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  todayImplicationText: {
    fontSize: 15,
    lineHeight: 22,
    marginTop: 8,
    marginBottom: 12,
  },
  behavioralHintBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: 12,
    borderRadius: 8,
    gap: 10,
  },
  behavioralHintText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },
  
  // What To Watch Card
  whatToWatchCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  watchHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  watchHeaderText: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  pressurePointsList: {
    marginBottom: 12,
    gap: 8,
  },
  pressurePointItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  pressurePointBullet: {
    fontSize: 14,
    marginRight: 8,
    marginTop: 2,
  },
  pressurePointText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  riskNoteBox: {
    padding: 12,
    borderRadius: 8,
  },
  riskNoteText: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  
  // What Helps Now Card
  whatHelpsNowCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  helpsHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  helpsHeaderText: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  practicalText: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
  },
  elementSupportBox: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 10,
  },
  elementSupportIcon: {
    fontSize: 20,
  },
  elementSupportText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
  },
  
  // Pattern Link Card
  patternLinkCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  patternLinkHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  patternLinkLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  patternLinkText: {
    fontSize: 14,
    lineHeight: 20,
  },
});
