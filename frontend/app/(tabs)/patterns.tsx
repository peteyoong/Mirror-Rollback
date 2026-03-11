import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';

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

interface PatternTension {
  category_a: string;
  category_b: string;
  combined_score: number;
  summary: string;
  reflection_prompt: string;
}

interface PatternGraphResponse {
  success: boolean;
  categories: PatternDomain[];
  summary: {
    active_categories: number;
    emerging_categories: number;
    total_signals: number;
  };
  pattern_tensions: PatternTension[];
  updated_at: string;
}

// ============================================================================
// DOMAIN REFLECTION PROMPTS
// ============================================================================

const DOMAIN_REFLECTION_PROMPTS: Record<string, string> = {
  'energy_vitality': 'What does your energy want you to notice right now?',
  'emotional_landscape': 'What emotion might be asking for your attention?',
  'identity_direction': 'What part of yourself is seeking expression?',
  'mind_meaning': 'What is your mind trying to understand?',
  'expression_action': 'What wants to be expressed or created through you?',
  'relationships_boundaries': 'Where might your connections be asking for care?',
  'growth_transformation': 'What change might be ready to happen?'
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
  const [tensions, setTensions] = useState<PatternTension[]>([]);
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
        // Limit tensions to max 2
        setTensions((response.data.pattern_tensions || []).slice(0, 2));
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

  const getReflectionPrompt = (domainId: string) => {
    return DOMAIN_REFLECTION_PROMPTS[domainId] || 'What might this pattern be showing you?';
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

  const toggleDomain = (domainId: string) => {
    setExpandedDomain(expandedDomain === domainId ? null : domainId);
  };

  // Extract signals grouped by source for Section 4
  const getSignalsBySource = () => {
    const geneKeys: { keyNumber: string; label: string; sphere?: string }[] = [];
    const humanDesign: { label: string; detail?: string }[] = [];
    const journal: string[] = [];
    
    const seenGeneKeys = new Set<string>();
    const seenHD = new Set<string>();
    
    domains.forEach(domain => {
      domain.matched_signals.forEach(signal => {
        if (signal.source === 'gene_keys') {
          const keyMatch = signal.detail?.match(/Gene Key (\d+)/);
          if (keyMatch && !seenGeneKeys.has(keyMatch[1])) {
            seenGeneKeys.add(keyMatch[1]);
            geneKeys.push({
              keyNumber: keyMatch[1],
              label: signal.label,
              sphere: signal.sphere_name
            });
          }
        } else if (signal.source === 'human_design' || signal.source === 'human_design_centers' || signal.source === 'human_design_gates') {
          if (!seenHD.has(signal.label)) {
            seenHD.add(signal.label);
            humanDesign.push({
              label: signal.label,
              detail: signal.detail
            });
          }
        } else if (signal.source === 'journal' || signal.source === 'mirror_chat') {
          if (!journal.includes(signal.label)) {
            journal.push(signal.label);
          }
        }
      });
    });
    
    return { geneKeys, humanDesign, journal };
  };

  const { geneKeys, humanDesign, journal } = getSignalsBySource();
  const hasSignals = geneKeys.length > 0 || humanDesign.length > 0 || journal.length > 0;

  // ============================================================================
  // RENDER: DOMAIN CARD
  // ============================================================================

  const renderDomainCard = (domain: PatternDomain) => {
    const isExpanded = expandedDomain === domain.category_id;
    const strengthColor = getStrengthColor(domain.signal_strength);
    const prompt = getReflectionPrompt(domain.category_id);
    const hasSignals = domain.matched_signals.length > 0;

    return (
      <View
        key={domain.category_id}
        style={[styles.domainCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        {/* Domain Header */}
        <TouchableOpacity
          style={styles.domainHeader}
          onPress={() => toggleDomain(domain.category_id)}
          activeOpacity={0.7}
        >
          <View style={styles.domainHeaderContent}>
            <Text style={[styles.domainName, { color: theme.text }]}>
              {domain.category_name}
            </Text>
            <Text style={[styles.domainStrength, { color: strengthColor }]}>
              {getStrengthLabel(domain.signal_strength)}
            </Text>
          </View>
          {hasSignals && (
            <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
              {isExpanded ? '▾' : '▸'}
            </Text>
          )}
        </TouchableOpacity>

        {/* Synthesis Text */}
        <Text style={[styles.domainSynthesis, { color: theme.textSecondary }]}>
          {domain.synthesis || domain.summary}
        </Text>

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

        {/* Expanded: Signals contributing to this pattern */}
        {isExpanded && hasSignals && (
          <View style={[styles.domainExpanded, { borderTopColor: theme.border }]}>
            <Text style={[styles.expandedTitle, { color: theme.textTertiary }]}>
              Signals contributing to this pattern
            </Text>
            {domain.matched_signals.slice(0, 6).map((signal, idx) => (
              <View key={idx} style={styles.expandedSignalRow}>
                <Text style={[styles.expandedSignalBullet, { color: theme.accent }]}>•</Text>
                <Text style={[styles.expandedSignalText, { color: theme.textSecondary }]}>
                  {signal.detail || signal.label}
                  {signal.sphere_name && ` (${signal.sphere_name})`}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  // ============================================================================
  // RENDER: INTERACTION CARD
  // ============================================================================

  const renderInteractionCard = (tension: PatternTension, index: number) => (
    <View
      key={index}
      style={[styles.interactionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
    >
      <Text style={[styles.interactionPair, { color: theme.text }]}>
        {tension.category_a} ↔ {tension.category_b}
      </Text>
      <Text style={[styles.interactionSummary, { color: theme.textSecondary }]}>
        {tension.summary}
      </Text>
      <Text style={[styles.interactionPrompt, { color: theme.accent }]}>
        {tension.reflection_prompt}
      </Text>
    </View>
  );

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
      {/* ================================================================== */}
      {/* SECTION 1: INTRO */}
      {/* ================================================================== */}
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
        <Text style={[styles.introDescription, { color: theme.textTertiary, fontStyle: 'italic' }]}>
          Some areas may feel quiet. Others may be more active.
        </Text>
      </View>

      {/* ================================================================== */}
      {/* SECTION 2: PATTERN DOMAINS (Primary) */}
      {/* ================================================================== */}
      <View style={styles.domainsSection}>
        {domains.map(domain => renderDomainCard(domain))}
      </View>

      {/* ================================================================== */}
      {/* SECTION 3: WHERE PATTERNS INTERACT */}
      {/* ================================================================== */}
      {tensions.length > 0 && (
        <View style={styles.interactionsSection}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
            WHERE PATTERNS INTERACT
          </Text>
          {tensions.map((tension, idx) => renderInteractionCard(tension, idx))}
        </View>
      )}

      {/* ================================================================== */}
      {/* SECTION 4: SIGNALS BEHIND THESE PATTERNS */}
      {/* ================================================================== */}
      {hasSignals && (
        <View style={styles.signalsSection}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
            SIGNALS BEHIND THESE PATTERNS
          </Text>
          <Text style={[styles.signalsDescription, { color: theme.textSecondary }]}>
            These signals may be contributing to the patterns appearing above.
          </Text>

          {/* Gene Keys */}
          {geneKeys.length > 0 && (
            <View style={[styles.signalGroup, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.signalGroupTitle, { color: theme.text }]}>
                Gene Keys
              </Text>
              {geneKeys.slice(0, 6).map((gk, idx) => (
                <View key={idx} style={styles.signalItem}>
                  <Text style={[styles.signalItemTitle, { color: theme.textSecondary }]}>
                    Gene Key {gk.keyNumber} — {gk.label}
                  </Text>
                  {gk.sphere && (
                    <Text style={[styles.signalItemSubtitle, { color: theme.textTertiary }]}>
                      Sphere: {gk.sphere}
                    </Text>
                  )}
                </View>
              ))}
            </View>
          )}

          {/* Human Design */}
          {humanDesign.length > 0 && (
            <View style={[styles.signalGroup, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.signalGroupTitle, { color: theme.text }]}>
                Human Design
              </Text>
              {humanDesign.slice(0, 6).map((hd, idx) => (
                <View key={idx} style={styles.signalItem}>
                  <Text style={[styles.signalItemTitle, { color: theme.textSecondary }]}>
                    {hd.label}
                  </Text>
                  {hd.detail && (
                    <Text style={[styles.signalItemSubtitle, { color: theme.textTertiary }]}>
                      {hd.detail}
                    </Text>
                  )}
                </View>
              ))}
            </View>
          )}

          {/* Journal & Reflections */}
          {journal.length > 0 && (
            <View style={[styles.signalGroup, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.signalGroupTitle, { color: theme.text }]}>
                Journal & Reflections
              </Text>
              <Text style={[styles.signalKeywords, { color: theme.textSecondary }]}>
                Recent keywords: {journal.slice(0, 8).join(', ')}
              </Text>
            </View>
          )}
        </View>
      )}
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

  // Section 1: Intro
  introSection: {
    marginBottom: 28,
  },
  introTitle: {
    fontSize: 26,
    fontWeight: '600',
    marginBottom: 12,
  },
  introDescription: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 8,
  },

  // Section 2: Pattern Domains
  domainsSection: {
    marginBottom: 32,
  },
  domainCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  domainHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  domainHeaderContent: {
    flex: 1,
  },
  domainName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  domainStrength: {
    fontSize: 12,
    fontWeight: '500',
  },
  expandIcon: {
    fontSize: 14,
    marginLeft: 8,
    marginTop: 2,
  },
  domainSynthesis: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 12,
  },
  domainPromptRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  domainPrompt: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  journalTrigger: {
    paddingLeft: 12,
    paddingTop: 2,
  },
  journalTriggerText: {
    fontSize: 12,
  },
  
  // Domain Expanded
  domainExpanded: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  expandedTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  expandedSignalRow: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  expandedSignalBullet: {
    fontSize: 12,
    marginRight: 8,
  },
  expandedSignalText: {
    fontSize: 13,
    lineHeight: 18,
    flex: 1,
  },

  // Section 3: Interactions
  interactionsSection: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 14,
  },
  interactionCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  interactionPair: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 10,
  },
  interactionSummary: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 10,
  },
  interactionPrompt: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },

  // Section 4: Signals
  signalsSection: {
    marginBottom: 16,
  },
  signalsDescription: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 16,
  },
  signalGroup: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  signalGroupTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
  },
  signalItem: {
    marginBottom: 10,
  },
  signalItemTitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  signalItemSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  signalKeywords: {
    fontSize: 13,
    lineHeight: 19,
  },
});
