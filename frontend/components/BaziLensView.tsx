/**
 * BaZi Lens View
 * 
 * Displays the BaZi (Four Pillars of Destiny) lens with:
 * - Overview section with Day Master and element summary
 * - Four Pillars display
 * - Five Elements distribution
 * - Ten Gods section
 * - Reflection section
 * 
 * Uses grounded Mirror language principles.
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
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { InlineResonanceReflect } from './ResonanceReflectButtons';
import api from '../services/api';

// =============================================================================
// INTERFACES
// =============================================================================

interface Pillar {
  stem: string;
  stem_pinyin: string;
  branch: string;
  branch_pinyin: string;
  animal: string;
  stem_element: string;
  branch_element: string;
}

interface DayMaster {
  stem: string;
  stem_pinyin: string;
  element: string;
  polarity: string;
}

interface ElementAnalysis {
  dominant_element: string;
  weak_element: string;
  element_percentages: Record<string, number>;
  day_master_strength: string;
  supporting_elements: string[];
  balance_status: string;
}

interface TenGods {
  year_pillar_stem: string;
  month_pillar_stem: string;
  day_pillar_stem: string;
  hour_pillar_stem: string;
}

interface ElementDescription {
  nature: string;
  personality: string;
  body_parts: string;
  season: string;
  direction: string;
  color: string;
}

interface BaziChart {
  birth_data: {
    date: string;
    time: string;
    timezone: string | null;
    chinese_year: number;
    bazi_month: number;
  };
  pillars: {
    year_pillar: Pillar;
    month_pillar: Pillar;
    day_pillar: Pillar;
    hour_pillar: Pillar;
  };
  day_master: DayMaster;
  five_elements: Record<string, number>;
  element_analysis: ElementAnalysis;
  ten_gods: TenGods;
  summary: {
    day_master_description: string;
    dominant_element: string;
    weak_element: string;
    balance_status: string;
    day_master_strength: string;
    supporting_elements: string[];
  };
  calculation_version: string;
  element_descriptions: Record<string, ElementDescription>;
}

interface BaziResponse {
  success: boolean;
  user_id: string;
  has_birth_time: boolean;
  chart: BaziChart;
}

interface Props {
  userId: string;
  onOpenChat: () => void;
}

// =============================================================================
// ELEMENT COLORS
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
// TEN GODS SIMPLIFIED LABELS - Mirror Language Version
// =============================================================================

const TEN_GODS_LABELS: Record<string, { label: string; meaning: string }> = {
  '比肩 (Companion)': { 
    label: 'Companion', 
    meaning: 'Self-reliance, peers, and finding your own way' 
  },
  '劫财 (Rob Wealth)': { 
    label: 'Competitor', 
    meaning: 'Challenges that sharpen you and push growth' 
  },
  '食神 (Eating God)': { 
    label: 'Output', 
    meaning: 'What you naturally create and express' 
  },
  '伤官 (Hurting Officer)': { 
    label: 'Expression', 
    meaning: 'Ideas that flow freely, sometimes unconventionally' 
  },
  '偏财 (Indirect Wealth)': { 
    label: 'Opportunity', 
    meaning: 'Unexpected openings and side paths' 
  },
  '正财 (Direct Wealth)': { 
    label: 'Stability', 
    meaning: 'Steady effort that builds over time' 
  },
  '七杀 (Seven Killings)': { 
    label: 'Power', 
    meaning: 'Pressure that can transform or overwhelm' 
  },
  '正官 (Direct Officer)': { 
    label: 'Structure', 
    meaning: 'Rules and expectations you work within' 
  },
  '偏印 (Indirect Seal)': { 
    label: 'Insight', 
    meaning: 'Unconventional wisdom and inner knowing' 
  },
  '正印 (Direct Seal)': { 
    label: 'Resource', 
    meaning: 'Support, learning, and what replenishes you' 
  },
  'Self (Day Master)': { 
    label: 'Self', 
    meaning: 'Your center—how you naturally operate' 
  },
};

// =============================================================================
// REFLECTION CONTENT - Mirror Language System
// =============================================================================

const ELEMENT_REFLECTIONS: Record<string, { 
  happening: string; 
  notice: string; 
  question: string;
  tension: string;
}> = {
  Wood: {
    happening: 'Wood may show up as a drive toward growth, new projects, and forward movement. You might feel a natural pull to build, expand, or start fresh.',
    notice: 'Notice where this creative push serves you—and where it might become restlessness or impatience with slower processes.',
    question: 'Where in your life are you pushing for growth before the ground beneath you is ready?',
    tension: 'The tension with Wood is often between vision and timing—wanting to move before conditions allow.',
  },
  Fire: {
    happening: 'Fire may show up as warmth, enthusiasm, and a desire to be seen or to connect. You might naturally light up spaces or draw others toward you.',
    notice: 'Notice where this brightness serves you—and where it might become exhausting or leave you feeling exposed.',
    question: 'Where might your light be asking to be expressed—and where might you be burning more than you can sustain?',
    tension: 'The tension with Fire is often between shining and burning out—between inspiring others and depleting yourself.',
  },
  Earth: {
    happening: 'Earth may show up as steadiness, care for others, and a need for solid ground. You might be the one people rely on for stability.',
    notice: 'Notice where this grounding serves you—and where it might become heaviness, worry, or difficulty letting go.',
    question: 'Where might you be holding on too tightly—to people, situations, or outcomes?',
    tension: 'The tension with Earth is often between nurturing and over-giving—between supporting others and losing yourself.',
  },
  Metal: {
    happening: 'Metal may show up as a pull toward refinement, discernment, and clear standards. You might naturally seek precision and quality in what you do.',
    notice: 'Notice where this clarity serves you—and where high standards might become rigidity or self-criticism.',
    question: 'Where might your inner standards be helping you—and where might they be creating unnecessary pressure?',
    tension: 'The tension with Metal is often between excellence and perfectionism—between clarity and coldness.',
  },
  Water: {
    happening: 'Water may show up as depth, reflection, and adaptability. You might naturally observe before acting, preferring to flow around obstacles.',
    notice: 'Notice where this flexibility serves you—and where it might become avoidance or difficulty holding your position.',
    question: 'Where might you be flowing too easily with others—and where do you need to hold your own course?',
    tension: 'The tension with Water is often between wisdom and fear—between adaptability and losing direction.',
  },
};

// Day Master behavioral descriptions - Mirror Language
const DAY_MASTER_DESCRIPTIONS: Record<string, Record<string, string>> = {
  Wood: {
    Yang: 'may show up as pioneering energy—a drive to lead, build, and push through obstacles. You might find yourself naturally taking charge or starting new things.',
    Yin: 'may show up as flexible growth—adapting, connecting, and finding ways around resistance. You might be quietly persistent rather than forceful.',
  },
  Fire: {
    Yang: 'may show up as radiant energy—warmth, clarity, and a natural presence that others notice. You might illuminate situations just by being in them.',
    Yin: 'may show up as gentle warmth—soft light that nurtures without overwhelming. You might connect through quiet enthusiasm rather than dramatic expression.',
  },
  Earth: {
    Yang: 'may show up as mountain-like stability—a solid presence that others can rely on. You might be the grounding force in chaotic situations.',
    Yin: 'may show up as nurturing support—fertile ground that helps others grow. You might naturally care for people and create safe spaces.',
  },
  Metal: {
    Yang: 'may show up as decisive clarity—cutting through confusion to find what matters. You might naturally set standards and hold boundaries.',
    Yin: 'may show up as refined discernment—precision in thought and action. You might notice details others miss and hold yourself to quiet internal standards.',
  },
  Water: {
    Yang: 'may show up as flowing power—moving around obstacles rather than forcing through them. You might naturally adapt while maintaining momentum.',
    Yin: 'may show up as deep stillness—reflective and perceptive. You might understand things intuitively before you can explain them.',
  },
};

// Element behavioral qualities for display
const ELEMENT_QUALITIES: Record<string, string> = {
  Wood: 'growth, initiative, and creative vision',
  Fire: 'warmth, connection, and expressive energy',
  Earth: 'stability, nurturing, and grounded presence',
  Metal: 'precision, refinement, and clear standards',
  Water: 'depth, reflection, and adaptive wisdom',
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function BaziLensView({ userId, onOpenChat }: Props) {
  const { theme, isDark } = useTheme();
  
  const [data, setData] = useState<BaziChart | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>('overview');

  // Load BaZi data
  const loadBaziData = useCallback(async (refresh = false) => {
    if (refresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const response = await api.get<BaziResponse>(`/bazi/${userId}`);
      if (response.data.success) {
        setData(response.data.chart);
      } else {
        setError('Failed to load BaZi chart');
      }
    } catch (err: any) {
      console.error('[BaZi] Load error:', err);
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

  const toggleSection = (section: string) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  // =============================================================================
  // RENDER HELPERS
  // =============================================================================

  const renderSectionHeader = (title: string, section: string, icon: keyof typeof Ionicons.glyphMap) => (
    <TouchableOpacity
      style={[styles.sectionHeader, { backgroundColor: theme.surface, borderColor: theme.border }]}
      onPress={() => toggleSection(section)}
      activeOpacity={0.7}
    >
      <View style={styles.sectionHeaderLeft}>
        <Ionicons name={icon} size={20} color={theme.textSecondary} />
        <Text style={[styles.sectionTitle, { color: theme.text }]}>{title}</Text>
      </View>
      <Ionicons
        name={expandedSection === section ? 'chevron-up' : 'chevron-down'}
        size={20}
        color={theme.textTertiary}
      />
    </TouchableOpacity>
  );

  // =============================================================================
  // OVERVIEW SECTION
  // =============================================================================

  const renderOverview = () => {
    if (!data) return null;

    const { day_master, element_analysis } = data;
    const dmDescription = DAY_MASTER_DESCRIPTIONS[day_master.element]?.[day_master.polarity] || '';
    const elementQualities = ELEMENT_QUALITIES[day_master.element] || '';

    return (
      <View style={styles.sectionContent}>
        {/* Day Master Card */}
        <View style={[styles.dayMasterCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.dayMasterLabel, { color: theme.textTertiary }]}>YOUR DAY MASTER</Text>
          <View style={styles.dayMasterRow}>
            <Text style={[styles.dayMasterCharacter, { color: theme.text }]}>{day_master.stem}</Text>
            <View style={styles.dayMasterInfo}>
              <Text style={[styles.dayMasterPinyin, { color: theme.text }]}>
                {day_master.stem_pinyin} {day_master.element}
              </Text>
              <Text style={[styles.dayMasterPolarity, { color: theme.textSecondary }]}>
                {day_master.polarity} • {element_analysis.day_master_strength}
              </Text>
            </View>
            <View style={[styles.elementBadge, { backgroundColor: ELEMENT_COLORS[day_master.element] + '20' }]}>
              <Text style={{ fontSize: 20 }}>{ELEMENT_ICONS[day_master.element]}</Text>
            </View>
          </View>
        </View>

        {/* Day Master Description - Mirror Language */}
        <View style={[styles.summaryCard, { backgroundColor: theme.background, borderColor: theme.border }]}>
          <Text style={[styles.summaryText, { color: theme.textSecondary }]}>
            <Text style={{ fontWeight: '600', color: theme.text }}>{day_master.stem_pinyin} {day_master.element}</Text>{' '}
            {dmDescription}
          </Text>
        </View>

        {/* Element Balance - Mirror Language */}
        <View style={[styles.summaryCard, { backgroundColor: theme.background, borderColor: theme.border }]}>
          <Text style={[styles.summaryLabel, { color: theme.textTertiary }]}>ELEMENT BALANCE</Text>
          <Text style={[styles.summaryText, { color: theme.textSecondary, marginTop: 6 }]}>
            Your chart leans toward{' '}
            <Text style={{ fontWeight: '600', color: ELEMENT_COLORS[element_analysis.dominant_element] }}>
              {element_analysis.dominant_element}
            </Text>
            {element_analysis.supporting_elements.length > 1 && element_analysis.supporting_elements[0] !== element_analysis.dominant_element && (
              <Text> and <Text style={{ fontWeight: '600' }}>{element_analysis.supporting_elements[0]}</Text></Text>
            )}
            , with less{' '}
            <Text style={{ fontWeight: '600', color: ELEMENT_COLORS[element_analysis.weak_element] }}>
              {element_analysis.weak_element}
            </Text>.
          </Text>
          <Text style={[styles.summarySubtext, { color: theme.textTertiary, marginTop: 8 }]}>
            This can show up as a natural draw toward {ELEMENT_QUALITIES[element_analysis.dominant_element] || 'certain patterns'}
            —with {ELEMENT_QUALITIES[element_analysis.weak_element] || 'other qualities'} requiring more conscious attention.
          </Text>
        </View>

        {/* Balance Status */}
        <View style={[styles.balanceRow, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.balanceItem}>
            <Text style={[styles.balanceLabel, { color: theme.textTertiary }]}>Balance</Text>
            <Text style={[styles.balanceValue, { color: theme.text }]}>{element_analysis.balance_status}</Text>
          </View>
          <View style={styles.balanceItem}>
            <Text style={[styles.balanceLabel, { color: theme.textTertiary }]}>Supporting</Text>
            <Text style={[styles.balanceValue, { color: theme.text }]}>
              {element_analysis.supporting_elements.join(', ')}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  // =============================================================================
  // FOUR PILLARS SECTION
  // =============================================================================

  const renderPillar = (pillar: Pillar, label: string) => (
    <View style={[styles.pillarCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <Text style={[styles.pillarLabel, { color: theme.textTertiary }]}>{label}</Text>
      
      <View style={styles.pillarCharacters}>
        <View style={styles.pillarCharacter}>
          <Text style={[styles.characterChinese, { color: theme.text }]}>{pillar.stem}</Text>
          <Text style={[styles.characterPinyin, { color: theme.textSecondary }]}>{pillar.stem_pinyin}</Text>
          <View style={[styles.elementDot, { backgroundColor: ELEMENT_COLORS[pillar.stem_element] }]} />
        </View>
        <View style={styles.pillarCharacter}>
          <Text style={[styles.characterChinese, { color: theme.text }]}>{pillar.branch}</Text>
          <Text style={[styles.characterPinyin, { color: theme.textSecondary }]}>{pillar.branch_pinyin}</Text>
          <View style={[styles.elementDot, { backgroundColor: ELEMENT_COLORS[pillar.branch_element] }]} />
        </View>
      </View>
      
      <View style={styles.pillarAnimal}>
        <Text style={[styles.animalText, { color: theme.textTertiary }]}>{pillar.animal}</Text>
      </View>
    </View>
  );

  const renderPillars = () => {
    if (!data) return null;

    return (
      <View style={styles.sectionContent}>
        <View style={styles.pillarsGrid}>
          {renderPillar(data.pillars.year_pillar, 'YEAR')}
          {renderPillar(data.pillars.month_pillar, 'MONTH')}
          {renderPillar(data.pillars.day_pillar, 'DAY')}
          {renderPillar(data.pillars.hour_pillar, 'HOUR')}
        </View>
        
        <Text style={[styles.pillarsNote, { color: theme.textTertiary }]}>
          The Day Pillar stem ({data.day_master.stem_pinyin}) is your Day Master — the center of your chart.
        </Text>
      </View>
    );
  };

  // =============================================================================
  // FIVE ELEMENTS SECTION
  // =============================================================================

  const renderElements = () => {
    if (!data) return null;

    const elements = data.five_elements;
    const maxValue = Math.max(...Object.values(elements));
    const { dominant_element, weak_element } = data.element_analysis;

    return (
      <View style={styles.sectionContent}>
        {/* Element Bars */}
        <View style={styles.elementsContainer}>
          {['Wood', 'Fire', 'Earth', 'Metal', 'Water'].map((element) => {
            const value = elements[element] || 0;
            const percentage = maxValue > 0 ? (value / maxValue) * 100 : 0;
            const isDominant = element === dominant_element;
            const isWeak = element === weak_element;

            return (
              <View key={element} style={styles.elementRow}>
                <View style={styles.elementInfo}>
                  <Text style={{ fontSize: 16 }}>{ELEMENT_ICONS[element]}</Text>
                  <Text style={[
                    styles.elementName,
                    { color: isDominant ? ELEMENT_COLORS[element] : theme.text },
                    isDominant && { fontWeight: '600' },
                  ]}>
                    {element}
                  </Text>
                  {isDominant && (
                    <View style={[styles.elementTag, { backgroundColor: ELEMENT_COLORS[element] + '20' }]}>
                      <Text style={[styles.elementTagText, { color: ELEMENT_COLORS[element] }]}>Strong</Text>
                    </View>
                  )}
                  {isWeak && (
                    <View style={[styles.elementTag, { backgroundColor: theme.border }]}>
                      <Text style={[styles.elementTagText, { color: theme.textTertiary }]}>Weak</Text>
                    </View>
                  )}
                </View>
                
                <View style={styles.elementBarContainer}>
                  <View
                    style={[
                      styles.elementBar,
                      {
                        backgroundColor: ELEMENT_COLORS[element],
                        width: `${Math.max(percentage, 5)}%`,
                        opacity: isWeak ? 0.4 : 1,
                      },
                    ]}
                  />
                  <Text style={[styles.elementValue, { color: theme.textSecondary }]}>
                    {value.toFixed(1)}
                  </Text>
                </View>
              </View>
            );
          })}
        </View>

        {/* Summary Text */}
        <View style={[styles.elementSummary, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.elementSummaryText, { color: theme.textSecondary }]}>
            Your chart currently leans more toward{' '}
            <Text style={{ fontWeight: '600', color: ELEMENT_COLORS[dominant_element] }}>{dominant_element}</Text>
            {data.element_analysis.supporting_elements.length > 1 && (
              <Text> and <Text style={{ fontWeight: '600' }}>{data.element_analysis.supporting_elements[0]}</Text></Text>
            )}
            , with less <Text style={{ fontWeight: '600', color: ELEMENT_COLORS[weak_element] }}>{weak_element}</Text>.
          </Text>
        </View>
      </View>
    );
  };

  // =============================================================================
  // TEN GODS SECTION
  // =============================================================================

  const renderTenGods = () => {
    if (!data) return null;

    const { ten_gods } = data;
    const godEntries = [
      { pillar: 'Year', god: ten_gods.year_pillar_stem },
      { pillar: 'Month', god: ten_gods.month_pillar_stem },
      { pillar: 'Day', god: ten_gods.day_pillar_stem },
      { pillar: 'Hour', god: ten_gods.hour_pillar_stem },
    ];

    return (
      <View style={styles.sectionContent}>
        <Text style={[styles.tenGodsIntro, { color: theme.textSecondary }]}>
          The Ten Gods describe how different energies in your chart relate to you. 
          Think of them as themes that may show up in different areas of your life—not as fixed forces, but as patterns worth noticing.
        </Text>

        <View style={styles.tenGodsGrid}>
          {godEntries.map(({ pillar, god }) => {
            const godInfo = TEN_GODS_LABELS[god] || { label: god, meaning: '' };
            const isSelf = god === 'Self (Day Master)';

            return (
              <View
                key={pillar}
                style={[
                  styles.tenGodCard,
                  { backgroundColor: theme.surface, borderColor: isSelf ? theme.accent : theme.border },
                  isSelf && { borderWidth: 2 },
                ]}
              >
                <Text style={[styles.tenGodPillar, { color: theme.textTertiary }]}>{pillar}</Text>
                <Text style={[styles.tenGodLabel, { color: isSelf ? theme.accent : theme.text }]}>
                  {godInfo.label}
                </Text>
                {godInfo.meaning && (
                  <Text style={[styles.tenGodMeaning, { color: theme.textTertiary }]}>
                    {godInfo.meaning}
                  </Text>
                )}
              </View>
            );
          })}
        </View>

        <Text style={[styles.tenGodsNote, { color: theme.textTertiary }]}>
          Year often relates to early life and ancestors. Month to career and outer world. 
          Day to self and partnerships. Hour to later life and inner world.
        </Text>
      </View>
    );
  };

  // =============================================================================
  // REFLECTION SECTION
  // =============================================================================

  const renderReflection = () => {
    if (!data) return null;

    const dayMasterElement = data.day_master.element;
    const reflection = ELEMENT_REFLECTIONS[dayMasterElement] || ELEMENT_REFLECTIONS.Earth;
    const dominantElement = data.element_analysis.dominant_element;
    const weakElement = data.element_analysis.weak_element;

    return (
      <View style={styles.sectionContent}>
        <View style={[styles.reflectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          {/* What may be happening */}
          <View style={styles.reflectionSection}>
            <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>WHAT MAY BE HAPPENING</Text>
            <Text style={[styles.reflectionText, { color: theme.textSecondary }]}>
              {reflection.happening}
            </Text>
          </View>

          {/* How this may feel / Tension */}
          <View style={styles.reflectionSection}>
            <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>A TENSION TO NOTICE</Text>
            <Text style={[styles.reflectionText, { color: theme.textSecondary }]}>
              {reflection.tension}
            </Text>
            {dominantElement !== dayMasterElement && (
              <Text style={[styles.reflectionText, { color: theme.textSecondary, marginTop: 8 }]}>
                With <Text style={{ fontWeight: '500' }}>{dominantElement}</Text> strong in your chart, 
                you may find {ELEMENT_QUALITIES[dominantElement]} comes naturally—while{' '}
                {ELEMENT_QUALITIES[weakElement]} may require more conscious effort.
              </Text>
            )}
          </View>

          {/* What to notice */}
          <View style={styles.reflectionSection}>
            <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>WHAT TO NOTICE</Text>
            <Text style={[styles.reflectionText, { color: theme.textSecondary }]}>
              {reflection.notice}
            </Text>
          </View>

          {/* Reflection Question */}
          <View style={[styles.reflectionQuestion, { borderTopColor: theme.border }]}>
            <Text style={[styles.questionLabel, { color: theme.textTertiary }]}>REFLECTION</Text>
            <Text style={[styles.questionText, { color: theme.text }]}>
              {reflection.question}
            </Text>
            
            <View style={styles.reflectButtonContainer}>
              <InlineResonanceReflect
                source={{
                  lens: 'bazi',
                  type: 'reflection',
                  name: 'BaZi Day Master Reflection',
                  value: `Day Master: ${data.day_master.stem_pinyin} ${data.day_master.element}`,
                  id: `bazi_reflection_${userId}`,
                }}
                prompt={reflection.question}
              />
            </View>
          </View>
        </View>

        {/* Footer */}
        <Text style={[styles.reflectionFooter, { color: theme.textTertiary }]}>
          This is one lens among many. Take what resonates; leave what doesn't. 
          BaZi describes tendencies and patterns—not fixed outcomes.
        </Text>
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
        <Text style={[styles.loadingSubtext, { color: theme.textTertiary }]}>
          This takes a moment as we calculate your chart.
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
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
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
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>BaZi</Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          Four Pillars of Destiny
        </Text>
      </View>

      {/* Overview Section */}
      {renderSectionHeader('Overview', 'overview', 'compass-outline')}
      {expandedSection === 'overview' && renderOverview()}

      {/* Four Pillars Section */}
      {renderSectionHeader('Four Pillars', 'pillars', 'grid-outline')}
      {expandedSection === 'pillars' && renderPillars()}

      {/* Five Elements Section */}
      {renderSectionHeader('Five Elements', 'elements', 'leaf-outline')}
      {expandedSection === 'elements' && renderElements()}

      {/* Ten Gods Section */}
      {renderSectionHeader('Ten Gods', 'tengods', 'people-outline')}
      {expandedSection === 'tengods' && renderTenGods()}

      {/* Reflection Section */}
      {renderSectionHeader('Reflection', 'reflection', 'sparkles-outline')}
      {expandedSection === 'reflection' && renderReflection()}

      {/* Footer spacer */}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
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
  loadingSubtext: {
    marginTop: 6,
    fontSize: 12,
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
    marginBottom: 20,
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

  // Section Header
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 2,
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
  },
  sectionContent: {
    paddingVertical: 12,
    paddingHorizontal: 4,
    marginBottom: 12,
  },

  // Day Master Card
  dayMasterCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  dayMasterLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  dayMasterRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dayMasterCharacter: {
    fontSize: 40,
    fontWeight: '300',
    marginRight: 12,
  },
  dayMasterInfo: {
    flex: 1,
  },
  dayMasterPinyin: {
    fontSize: 18,
    fontWeight: '600',
  },
  dayMasterPolarity: {
    fontSize: 13,
    marginTop: 2,
  },
  elementBadge: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Summary Card
  summaryCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  summaryLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  summaryText: {
    fontSize: 14,
    lineHeight: 21,
  },
  summarySubtext: {
    fontSize: 13,
    lineHeight: 19,
  },

  // Balance Row
  balanceRow: {
    flexDirection: 'row',
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 24,
  },
  balanceItem: {
    flex: 1,
  },
  balanceLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  balanceValue: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Pillars
  pillarsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 12,
  },
  pillarCard: {
    flex: 1,
    minWidth: '22%',
    padding: 12,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  pillarLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  pillarCharacters: {
    flexDirection: 'row',
    gap: 4,
  },
  pillarCharacter: {
    alignItems: 'center',
  },
  characterChinese: {
    fontSize: 22,
    fontWeight: '300',
  },
  characterPinyin: {
    fontSize: 10,
    marginTop: 2,
  },
  elementDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 4,
  },
  pillarAnimal: {
    marginTop: 8,
  },
  animalText: {
    fontSize: 11,
  },
  pillarsNote: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
  },

  // Elements
  elementsContainer: {
    gap: 12,
    marginBottom: 16,
  },
  elementRow: {
    gap: 8,
  },
  elementInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  elementName: {
    fontSize: 14,
    minWidth: 50,
  },
  elementTag: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  elementTagText: {
    fontSize: 10,
    fontWeight: '600',
  },
  elementBarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  elementBar: {
    height: 8,
    borderRadius: 4,
  },
  elementValue: {
    fontSize: 12,
    minWidth: 30,
  },
  elementSummary: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  elementSummaryText: {
    fontSize: 14,
    lineHeight: 21,
  },

  // Ten Gods
  tenGodsIntro: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 16,
  },
  tenGodsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  tenGodCard: {
    flex: 1,
    minWidth: '45%',
    padding: 12,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  tenGodPillar: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  tenGodLabel: {
    fontSize: 15,
    fontWeight: '600',
  },
  tenGodMeaning: {
    fontSize: 11,
    marginTop: 4,
  },
  tenGodsNote: {
    fontSize: 12,
    fontStyle: 'italic',
    marginTop: 16,
    lineHeight: 18,
  },

  // Reflection
  reflectionCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  reflectionSection: {
    padding: 16,
  },
  reflectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  reflectionQuestion: {
    padding: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  questionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  questionText: {
    fontSize: 15,
    fontWeight: '500',
    fontStyle: 'italic',
    lineHeight: 22,
  },
  reflectButtonContainer: {
    marginTop: 16,
    alignItems: 'flex-start',
  },
  reflectionFooter: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 16,
  },
});
