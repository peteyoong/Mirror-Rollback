import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';

// Enable LayoutAnimation for Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// ============================================================================
// INTERFACES
// ============================================================================

interface MatchedSignal {
  source: string;
  label: string;
  sphere_name?: string;
  detail?: string;
}

interface PatternDomain {
  category_id: string;
  category_name: string;
  signal_strength: 'quiet' | 'present' | 'recurring';
  pattern_score: number;
  signal_count: number;
  trend: 'rising' | 'steady' | 'fading';
  matched_sources: string[];
  matched_signals: MatchedSignal[];
  summary: string;
  synthesis?: string;
}

interface PatternGraphResponse {
  success: boolean;
  categories: PatternDomain[];
  summary: {
    active_categories: number;
    emerging_categories: number;
    total_signals: number;
  };
  pattern_tensions: any[];
  updated_at: string;
}

// ============================================================================
// DOMAIN CONTENT - Deeper synthesis and reflection prompts
// ============================================================================

interface DomainContent {
  quietSynthesis: string;
  quietShowUp?: string;
  presentSynthesis: string;
  presentShowUp?: string;
  recurringSynthesis: string;
  recurringShowUp?: string;
  reflectionPrompt: string;
}

const DOMAIN_CONTENT: Record<string, DomainContent> = {
  'energy_vitality': {
    quietSynthesis: "Your energy may be in a quieter phase right now. This doesn't mean something is wrong—sometimes the body and spirit need rest before the next movement becomes clear.",
    presentSynthesis: "Something around energy, vitality, or the pace of your life may be surfacing. This domain can become active when the body is asking for attention—whether through fatigue, restlessness, or a subtle sense that something needs to shift.",
    presentShowUp: "One way this pattern can appear is through the tension between what you want to do and what your energy actually allows. It might also show up as a question about sustainability, or a feeling that you're running on something other than your own rhythm.",
    recurringSynthesis: "A recurring theme around energy and vitality seems to be present across your reflections. This may point to a deeper question about how you sustain yourself—not just physically, but emotionally and spiritually.",
    recurringShowUp: "This pattern can sometimes show up as cycles of depletion and recovery, or as a growing awareness that something in how you're living may need to change. It might also be an invitation to notice where your energy comes from and where it goes.",
    reflectionPrompt: "What is your energy asking you to notice right now?"
  },
  'emotional_landscape': {
    quietSynthesis: "The emotional landscape may feel quieter at the moment. This can be a time of integration, or simply a pause between waves of feeling.",
    presentSynthesis: "Emotional themes may be moving through your inner world right now. This domain often becomes active when feelings are asking for acknowledgment—whether through intensity, numbness, or a sense that something unnamed is present.",
    presentShowUp: "One way this can show up is through mood shifts that feel disconnected from external events, or through recurring feelings that don't quite resolve. It might also appear as a growing sensitivity to your own inner weather.",
    recurringSynthesis: "Emotional patterns seem to be surfacing repeatedly in your reflections. This may suggest that something in your inner life is asking for deeper attention—not to be fixed, but to be witnessed and understood.",
    recurringShowUp: "Sometimes this pattern shows up as a particular emotion that keeps returning, or as a sense that your emotional life has its own rhythm that's different from your thinking mind. It can also appear as a growing capacity to be with feelings without needing to change them.",
    reflectionPrompt: "What emotion might be asking for your attention?"
  },
  'identity_direction': {
    quietSynthesis: "Questions of identity and direction may be resting for now. This can be a period of simply being, without the pressure of becoming.",
    presentSynthesis: "A quieter question may be surfacing around self-trust, worth, or permission to move forward. Sometimes this domain becomes active not because direction is absent, but because your sense of who you are becomes entangled with whether you feel ready, valid, or enough.",
    presentShowUp: "One way this pattern can appear is through hesitation that feels deeper than practical uncertainty—a sense that moving forward requires something from you that feels unavailable. It might also show up as questions about authenticity, or a feeling of being caught between who you've been and who you're becoming.",
    recurringSynthesis: "Themes around identity and direction seem to be recurring in your inner world. This may point to a deeper process of self-definition—one that isn't about finding the right path, but about learning to trust your own becoming.",
    recurringShowUp: "This pattern can sometimes show up as a persistent question about what you really want, or as a tension between external expectations and internal truth. It might also appear as a growing willingness to be uncertain without feeling lost.",
    reflectionPrompt: "What part of yourself is seeking expression or acknowledgment?"
  },
  'mind_meaning': {
    quietSynthesis: "The mind may be in a quieter phase right now—less focused on making sense of things, more present to experience itself.",
    presentSynthesis: "Something around thinking, understanding, or meaning-making may be active. This domain often surfaces when the mind is working through something—trying to understand, categorize, or find a framework that holds.",
    presentShowUp: "One way this can show up is through mental restlessness, overthinking, or a sense that understanding something will bring relief. It might also appear as a hunger for insight, or a feeling that something important is just out of reach.",
    recurringSynthesis: "Patterns around mind and meaning seem to be recurring in your reflections. This may suggest that your mind is processing something significant—not necessarily a problem to solve, but perhaps a new way of seeing that's trying to emerge.",
    recurringShowUp: "Sometimes this pattern shows up as a persistent question that doesn't have a clear answer, or as a gradual shift in how you make sense of your experience. It can also appear as a growing awareness of the limits of thinking alone.",
    reflectionPrompt: "What is your mind trying to understand or make sense of?"
  },
  'expression_action': {
    quietSynthesis: "Expression and action may be in a quieter phase. This can be a time of gathering, preparing, or simply being without the need to produce or perform.",
    presentSynthesis: "Something around expression, creativity, or taking action may be surfacing. This domain often becomes active when there's something inside asking to move outward—whether through words, work, or simply showing up differently in the world.",
    presentShowUp: "One way this can show up is through creative restlessness, or a feeling that something wants to be said or made but isn't quite finding its form. It might also appear as tension between the impulse to act and the fear of being seen.",
    recurringSynthesis: "Themes around expression and action seem to be recurring in your reflections. This may point to a deeper relationship with your own creative force—not just what you make, but how you allow yourself to be present in the world.",
    recurringShowUp: "Sometimes this pattern shows up as a persistent question about voice, visibility, or impact. It can also appear as a growing sense that how you express yourself matters—not for external validation, but for your own sense of aliveness.",
    reflectionPrompt: "What wants to be expressed or created through you?"
  },
  'relationships_boundaries': {
    quietSynthesis: "Relational themes may be quieter right now. This can be a time of being present with yourself, without the complexity of navigating others.",
    presentSynthesis: "Something around relationships, boundaries, or connection may be surfacing. This domain often becomes active when the space between self and other feels charged—whether through closeness, distance, or the subtle negotiations of being in relationship.",
    presentShowUp: "One way this can show up is through a sense of being pulled between your own needs and others' expectations. It might also appear as questions about trust, dependency, or how much of yourself to reveal.",
    recurringSynthesis: "Patterns around relationships and boundaries seem to be recurring in your reflections. This may suggest that something in how you connect with others is asking for deeper attention—not to change, necessarily, but to be understood.",
    recurringShowUp: "Sometimes this pattern shows up as a persistent question about where you end and others begin. It can also appear as a growing awareness of your own patterns in relationship—what you seek, what you avoid, and what you're learning.",
    reflectionPrompt: "Where might your connections be asking for care or attention?"
  },
  'growth_transformation': {
    quietSynthesis: "Growth and transformation may be in a quieter phase. Sometimes the most profound changes happen invisibly, in the spaces between effort.",
    presentSynthesis: "Something around change, growth, or transformation may be surfacing. This domain often becomes active during transitions—when the old way no longer fits, but the new way hasn't fully arrived.",
    presentShowUp: "One way this can show up is through a sense of being between identities, or through the discomfort that comes before a shift. It might also appear as a growing willingness to let go of what once defined you.",
    recurringSynthesis: "Themes around growth and transformation seem to be recurring in your reflections. This may point to a deeper process of becoming—one that asks for patience with your own unfolding and trust in what you can't yet see.",
    recurringShowUp: "Sometimes this pattern shows up as a feeling of being on the edge of something new, or as a recognition that certain ways of being no longer serve you. It can also appear as a quiet knowing that something inside you is changing, even if you can't name it yet.",
    reflectionPrompt: "What change might be ready to happen in you?"
  }
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function PatternsScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  
  // State
  const [domains, setDomains] = useState<PatternDomain[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null);

  // ============================================================================
  // DATA LOADING
  // ============================================================================

  useEffect(() => {
    if (user?.id) {
      loadPatternData();
    }
  }, [user?.id]);

  const loadPatternData = async (refresh = false) => {
    if (refresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    
    try {
      const response = await api.get<PatternGraphResponse>(`/pattern-graph/${user?.id}`);
      if (response.data.success) {
        setDomains(response.data.categories);
      } else {
        setError('Unable to load pattern data.');
      }
    } catch (err: any) {
      console.error('Pattern data load error:', err);
      setError('Unable to load patterns right now.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const onRefresh = () => loadPatternData(true);

  // ============================================================================
  // HELPERS
  // ============================================================================

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'recurring': return theme.accent;
      case 'present': return theme.textSecondary;
      default: return theme.textTertiary;
    }
  };

  const getStrengthLabel = (strength: string) => {
    switch (strength) {
      case 'recurring': return 'Recurring';
      case 'present': return 'Present';
      default: return 'Quiet';
    }
  };

  const getDomainContent = (domainId: string, strength: string): { synthesis: string; showUp?: string; prompt: string } => {
    const content = DOMAIN_CONTENT[domainId];
    if (!content) {
      return {
        synthesis: 'Patterns in this area may be emerging.',
        prompt: 'What might this pattern be showing you?'
      };
    }

    switch (strength) {
      case 'recurring':
        return {
          synthesis: content.recurringSynthesis,
          showUp: content.recurringShowUp,
          prompt: content.reflectionPrompt
        };
      case 'present':
        return {
          synthesis: content.presentSynthesis,
          showUp: content.presentShowUp,
          prompt: content.reflectionPrompt
        };
      default:
        return {
          synthesis: content.quietSynthesis,
          prompt: content.reflectionPrompt
        };
    }
  };

  const handleJournalTrigger = (domainName: string, prompt: string) => {
    router.push({
      pathname: '/(tabs)/journal',
      params: {
        prefillPrompt: prompt,
        journalSource: 'pattern_domain',
        category: domainName,
      }
    });
  };

  const toggleExpanded = (domainId: string, domainName: string) => {
    const newExpanded = expandedDomain === domainId ? null : domainId;
    console.log(`[PATTERN_ACCORDION_TAP] ${domainName}`);
    console.log(`[PATTERN_ACCORDION_STATE] ${domainName} expanded=${newExpanded !== null}`);
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedDomain(newExpanded);
  };

  const getSourceDisplayName = (source: string): string => {
    const sourceNames: Record<string, string> = {
      'gene_keys': 'Gene Keys',
      'human_design': 'Human Design',
      'journal': 'Journal & Reflections',
      'mirror_chat': 'Mirror Chat',
    };
    return sourceNames[source] || source;
  };

  const formatSignalLabel = (signal: MatchedSignal): string => {
    // For Gene Keys signals, format nicely
    if (signal.source === 'gene_keys') {
      if (signal.detail && signal.detail.includes('Gene Key')) {
        // Extract just the gene key number
        const match = signal.detail.match(/Gene Key (\d+)/);
        if (match) {
          return `Gene Key ${match[1]} — ${signal.label}`;
        }
      }
      if (signal.sphere_name) {
        return `${signal.label} · ${signal.sphere_name}`;
      }
    }
    // For Human Design signals
    if (signal.source === 'human_design') {
      return signal.label;
    }
    // For journal signals
    if (signal.source === 'journal') {
      return signal.label;
    }
    // Default
    if (signal.sphere_name) {
      return `${signal.label} · ${signal.sphere_name}`;
    }
    return signal.label;
  };

  // Count signals by source for debugging
  const countSignalsBySource = (signals: MatchedSignal[]): Record<string, number> => {
    const counts: Record<string, number> = {};
    signals.forEach(s => {
      counts[s.source] = (counts[s.source] || 0) + 1;
    });
    return counts;
  };

  // ============================================================================
  // RENDER: DOMAIN CARD
  // ============================================================================

  const renderDomainCard = (domain: PatternDomain) => {
    const strengthColor = getStrengthColor(domain.signal_strength);
    const { synthesis, showUp, prompt } = getDomainContent(domain.category_id, domain.signal_strength);
    const isExpanded = expandedDomain === domain.category_id;
    
    // Filter out enneagram signals for display (enneagram is invisible)
    const visibleSignals = domain.matched_signals?.filter(s => s.source !== 'enneagram') || [];
    const hasVisibleSignals = visibleSignals.length > 0;
    
    // Group signals by source for display
    const signalsBySource: Record<string, MatchedSignal[]> = {};
    visibleSignals.forEach(signal => {
      const source = signal.source;
      if (!signalsBySource[source]) {
        signalsBySource[source] = [];
      }
      signalsBySource[source].push(signal);
    });

    // Log signal counts for debugging when expanded changes
    if (isExpanded) {
      const counts = countSignalsBySource(visibleSignals);
      console.log(`[PATTERN_ACCORDION_SIGNALS] ${domain.category_name} gene_keys=${counts.gene_keys || 0} human_design=${counts.human_design || 0} journal=${counts.journal || 0}`);
    }

    return (
      <View
        key={domain.category_id}
        style={[styles.domainCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        {/* Tappable Header Area - includes name, strength and chevron */}
        <TouchableOpacity 
          style={styles.domainHeaderTouchable}
          onPress={() => toggleExpanded(domain.category_id, domain.category_name)}
          activeOpacity={0.7}
          disabled={!hasVisibleSignals}
        >
          <View style={styles.domainHeaderRow}>
            <Text style={[styles.domainName, { color: theme.text }]}>
              {domain.category_name}
            </Text>
            <View style={styles.headerRight}>
              <Text style={[styles.domainStrength, { color: strengthColor }]}>
                {getStrengthLabel(domain.signal_strength)}
              </Text>
              {hasVisibleSignals && (
                <Text style={[styles.expandChevron, { color: theme.textTertiary }]}>
                  {isExpanded ? '▲' : '▼'}
                </Text>
              )}
            </View>
          </View>
        </TouchableOpacity>

        {/* Primary Synthesis */}
        <Text style={[styles.domainSynthesis, { color: theme.textSecondary }]}>
          {synthesis}
        </Text>

        {/* Optional: How this may show up */}
        {showUp && (
          <Text style={[styles.domainShowUp, { color: theme.textSecondary }]}>
            {showUp}
          </Text>
        )}

        {/* Reflection Prompt + Journal Trigger */}
        <View style={styles.domainPromptRow}>
          <Text style={[styles.domainPrompt, { color: theme.accent, flex: 1 }]}>
            {prompt}
          </Text>
          <TouchableOpacity
            onPress={() => handleJournalTrigger(domain.category_name, prompt)}
            style={styles.journalTrigger}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={[styles.journalTriggerText, { color: theme.textTertiary }]}>
              ✏️ Reflect
            </Text>
          </TouchableOpacity>
        </View>

        {/* Expandable Signals Section - Only renders when expanded AND has visible signals */}
        {isExpanded && hasVisibleSignals && (
          <View style={[styles.signalsSection, { borderTopColor: theme.border }]}>
            <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>
              Signals contributing to this pattern
            </Text>
            
            {Object.entries(signalsBySource).map(([source, signals]) => (
              <View key={source} style={styles.sourceGroup}>
                <Text style={[styles.sourceLabel, { color: theme.textSecondary }]}>
                  {getSourceDisplayName(source)}
                </Text>
                {signals.slice(0, 4).map((signal, idx) => (
                  <View key={idx} style={styles.signalItem}>
                    <Text style={[styles.signalDot, { color: theme.textTertiary }]}>•</Text>
                    <Text style={[styles.signalText, { color: theme.textTertiary }]}>
                      {formatSignalLabel(signal)}
                    </Text>
                  </View>
                ))}
                {signals.length > 4 && (
                  <Text style={[styles.moreSignals, { color: theme.textTertiary }]}>
                    +{signals.length - 4} more
                  </Text>
                )}
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  // ============================================================================
  // RENDER: LOADING / ERROR STATES
  // ============================================================================

  if (isLoading) {
    return (
      <View style={[styles.container, styles.centerContent, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading patterns...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, styles.centerContent, { backgroundColor: theme.background }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
        <TouchableOpacity
          style={[styles.retryButton, { borderColor: theme.border }]}
          onPress={() => loadPatternData()}
        >
          <Text style={[styles.retryText, { color: theme.accent }]}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          refreshing={isRefreshing}
          onRefresh={onRefresh}
          tintColor={theme.accent}
        />
      }
    >
      {/* INTRO SECTION */}
      <View style={styles.introSection}>
        <Text style={[styles.introTitle, { color: theme.text }]}>
          Pattern Graph
        </Text>
        <Text style={[styles.introDescription, { color: theme.textSecondary }]}>
          Patterns can emerge across different parts of life.
        </Text>
        <Text style={[styles.introDescription, { color: theme.textSecondary }]}>
          This page gathers signals from your reflections, Human Design, Gene Keys and other lenses, and organizes them into seven life domains.
        </Text>
        <Text style={[styles.introNote, { color: theme.textTertiary }]}>
          Some areas may feel quiet. Others may be more active.
        </Text>
      </View>

      {/* PATTERN DOMAINS - The 7 Life Domains */}
      <View style={styles.domainsSection}>
        {domains.map(domain => renderDomainCard(domain))}
      </View>
    </ScrollView>
  );
}

// ============================================================================
// STYLES
// ============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 40,
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  // Loading & Error
  loadingText: {
    marginTop: 16,
    fontSize: 14,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Intro Section
  introSection: {
    marginBottom: 28,
  },
  introTitle: {
    fontSize: 26,
    fontWeight: '600',
    marginBottom: 14,
  },
  introDescription: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 8,
  },
  introNote: {
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic',
    marginTop: 4,
  },

  // Pattern Domains Section
  domainsSection: {
    marginBottom: 20,
  },
  domainCard: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 18,
    marginBottom: 16,
  },
  domainHeader: {
    marginBottom: 14,
  },
  domainHeaderTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  domainName: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 4,
    flex: 1,
  },
  domainStrength: {
    fontSize: 12,
    fontWeight: '500',
  },
  expandIcon: {
    fontSize: 10,
    marginLeft: 4,
  },
  domainSynthesis: {
    fontSize: 14,
    lineHeight: 23,
    marginBottom: 12,
  },
  domainShowUp: {
    fontSize: 14,
    lineHeight: 23,
    marginBottom: 14,
    opacity: 0.9,
  },
  domainPromptRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.08)',
  },
  domainPrompt: {
    fontSize: 13,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  journalTrigger: {
    paddingLeft: 12,
    paddingTop: 2,
  },
  journalTriggerText: {
    fontSize: 12,
  },
  
  // Accordion/Signals Section
  signalsSection: {
    marginTop: 16,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  signalsSectionTitle: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
    opacity: 0.7,
  },
  sourceGroup: {
    marginBottom: 12,
  },
  sourceLabel: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 6,
  },
  signalItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 3,
    paddingLeft: 4,
  },
  signalDot: {
    fontSize: 10,
    marginRight: 8,
    marginTop: 3,
  },
  signalText: {
    fontSize: 13,
    lineHeight: 18,
    flex: 1,
  },
  moreSignals: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 4,
    paddingLeft: 16,
  },
});
