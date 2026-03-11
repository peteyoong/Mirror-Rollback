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

interface MatchedSignal {
  source: string;
  label: string;
  sphere_name?: string;
  detail?: string;
}

interface PatternCategory {
  category_id: string;
  category_name: string;
  signal_strength: 'quiet' | 'present' | 'recurring';
  pattern_score: number;
  signal_count: number;
  trend: 'rising' | 'steady' | 'fading';
  matched_sources: string[];
  matched_signals: MatchedSignal[];
  summary: string;
  synthesis?: string;  // LLM-generated reflective paragraph for recurring patterns
}

interface PatternGraphResponse {
  success: boolean;
  categories: PatternCategory[];
  summary: {
    active_categories: number;
    emerging_categories: number;
    total_signals: number;
  };
  pattern_tensions: PatternTension[];
  updated_at: string;
}

interface PatternTension {
  category_a: string;
  category_b: string;
  combined_score: number;
  summary: string;
  reflection_prompt: string;
}

// Timeline types
interface TimelineCategory {
  category_id: string;
  category_name: string;
  signal_strength: 'quiet' | 'present' | 'recurring';
  total_signals: number;
  matched_sources: string[];
  summary: string;
}

interface TimeBucket {
  bucket_name: string;
  bucket_label: string;
  start_date: string;
  end_date: string;
  categories: TimelineCategory[];
  has_activity: boolean;
}

interface TimelineResponse {
  success: boolean;
  buckets: TimeBucket[];
  has_any_activity: boolean;
  generated_at: string;
}

export default function PatternGraphScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const [categories, setCategories] = useState<PatternCategory[]>([]);
  const [summary, setSummary] = useState<{ active_categories: number; emerging_categories: number } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  
  // Pattern tensions state
  const [patternTensions, setPatternTensions] = useState<PatternTension[]>([]);
  
  // Timeline state
  const [timeline, setTimeline] = useState<TimeBucket[]>([]);
  const [timelineLoading, setTimelineLoading] = useState(false);

  useEffect(() => {
    if (user?.id) {
      loadPatternGraph();
      loadTimeline();
    }
  }, [user?.id]);

  const loadPatternGraph = async (refresh = false) => {
    if (refresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    
    try {
      const response = await api.get<PatternGraphResponse>(`/pattern-graph/${user?.id}`);
      if (response.data.success) {
        setCategories(response.data.categories);
        setSummary(response.data.summary || null);
        setPatternTensions(response.data.pattern_tensions || []);
      } else {
        setError('Unable to load pattern graph.');
      }
    } catch (err: any) {
      console.error('Pattern graph load error:', err);
      setError('Unable to load patterns right now.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const loadTimeline = async () => {
    setTimelineLoading(true);
    try {
      const response = await api.get<TimelineResponse>(`/pattern-graph/timeline/${user?.id}`);
      if (response.data.success) {
        setTimeline(response.data.buckets);
      }
    } catch (err: any) {
      console.error('Timeline load error:', err);
    } finally {
      setTimelineLoading(false);
    }
  };

  const toggleCategory = (categoryId: string) => {
    setExpandedCategory(expandedCategory === categoryId ? null : categoryId);
  };

  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'recurring':
        return theme.accent;
      case 'present':
        return theme.textSecondary;
      default:
        return theme.textTertiary;
    }
  };

  const getStrengthLabel = (strength: string) => {
    switch (strength) {
      case 'recurring':
        return 'Recurring';
      case 'present':
        return 'Present';
      default:
        return 'Quiet';
    }
  };

  const formatSource = (source: string) => {
    switch (source) {
      case 'gene_keys':
        return 'Gene Keys';
      case 'human_design':
        return 'Human Design';
      case 'journal':
        return 'Journal';
      case 'chat':
        return 'Mirror Chat';
      default:
        return source;
    }
  };

  // Trend labels removed - no longer showing arrows
  // Signal strength is now the primary indicator

  // getTrendColor function removed - no longer needed

  // Get top categories by pattern_score (non-quiet only)
  const topCategories = [...categories]
    .filter(c => c.signal_strength !== 'quiet')
    .sort((a, b) => b.pattern_score - a.pattern_score)
    .slice(0, 3);

  // Format signal label for cleaner display
  const formatSignalLabel = (signal: MatchedSignal) => {
    // Clean up repetitive phrasing like "Weakness (weak)" -> "Weakness"
    let label = signal.label;
    
    // If it's a Gene Key pattern like "Shadow → Gift", format nicely
    if (signal.detail && signal.detail.includes('Gene Key')) {
      const keyMatch = signal.detail.match(/Gene Key (\d+)/);
      if (keyMatch) {
        return `Gene Key ${keyMatch[1]} — ${label}`;
      }
    }
    
    return label;
  };

  // Reflection prompts for categories (deterministic)
  const getCategoryReflectionPrompt = (categoryId: string) => {
    const prompts: Record<string, string> = {
      'energy_vitality': 'What does your energy want you to notice right now?',
      'emotional_landscape': 'What emotion might be asking for your attention?',
      'identity_direction': 'What part of yourself is seeking expression?',
      'mind_meaning': 'What is your mind trying to understand?',
      'expression_action': 'What wants to be expressed or created through you?',
      'relationships_boundaries': 'Where might your connections be asking for care?',
      'growth_transformation': 'What change might be ready to happen?'
    };
    return prompts[categoryId] || 'What might this pattern be showing you?';
  };

  // Extract and group all signals by source (for Section 3)
  const getSignalsBySource = () => {
    const geneKeysSignals: { keyNumber: string; label: string; sphere?: string }[] = [];
    const humanDesignSignals: { label: string; detail?: string }[] = [];
    const journalSignals: string[] = [];
    
    // Track seen Gene Key numbers to show one entry per key
    const seenGeneKeyNumbers = new Set<string>();
    const seenHumanDesign = new Set<string>();
    
    // Collect all signals from all categories
    categories.forEach(cat => {
      cat.matched_signals.forEach(signal => {
        if (signal.source === 'gene_keys') {
          // Extract Gene Key number from detail
          const keyMatch = signal.detail?.match(/Gene Key (\d+)/);
          if (keyMatch) {
            const keyNumber = keyMatch[1];
            // Only add one entry per Gene Key number
            if (!seenGeneKeyNumbers.has(keyNumber)) {
              seenGeneKeyNumbers.add(keyNumber);
              // Prefer the "Shadow → Gift" format if available
              const isTransformation = signal.label.includes('→');
              geneKeysSignals.push({
                keyNumber,
                label: signal.label,
                sphere: signal.sphere_name
              });
            } else {
              // If we already have this key, prefer the transformation label
              const existingIdx = geneKeysSignals.findIndex(s => s.keyNumber === keyNumber);
              if (existingIdx >= 0 && signal.label.includes('→') && !geneKeysSignals[existingIdx].label.includes('→')) {
                geneKeysSignals[existingIdx].label = signal.label;
              }
            }
          }
        } else if (signal.source === 'human_design' || signal.source === 'human_design_centers' || signal.source === 'human_design_gates') {
          if (!seenHumanDesign.has(signal.label)) {
            seenHumanDesign.add(signal.label);
            humanDesignSignals.push({
              label: signal.label,
              detail: signal.detail
            });
          }
        } else if (signal.source === 'journal' || signal.source === 'mirror_chat') {
          if (!journalSignals.includes(signal.label)) {
            journalSignals.push(signal.label);
          }
        }
      });
    });
    
    return { geneKeysSignals, humanDesignSignals, journalSignals };
  };

  // Format Gene Key signal for clean display (one entry per key)
  const formatGeneKeySignal = (signal: { keyNumber: string; label: string; sphere?: string }) => {
    return {
      title: `Gene Key ${signal.keyNumber} — ${signal.label}`,
      subtitle: signal.sphere ? `Sphere: ${signal.sphere}` : undefined
    };
  };

  // Get timeline data organized by period for compact display
  const getTimelineByPeriod = () => {
    const result: { period: string; recurring: string[] }[] = [];
    
    timeline.forEach(bucket => {
      const recurring = bucket.categories
        .filter(cat => cat.signal_strength === 'recurring')
        .map(cat => cat.category_name);
      
      if (recurring.length > 0) {
        result.push({
          period: bucket.bucket_label,
          recurring
        });
      }
    });
    
    return result;
  };

  // Get recurring themes from timeline for summary (legacy)
  const getTimelineSummary = () => {
    const recurringThemes: string[] = [];
    timeline.forEach(bucket => {
      bucket.categories.forEach(cat => {
        if (cat.signal_strength === 'recurring' && !recurringThemes.includes(cat.category_name)) {
          recurringThemes.push(cat.category_name);
        }
      });
    });
    return recurringThemes;
  };

  const { geneKeysSignals, humanDesignSignals, journalSignals } = getSignalsBySource();
  const timelineRecurring = getTimelineSummary();
  const timelineByPeriod = getTimelineByPeriod();
  const hasAnySignals = geneKeysSignals.length > 0 || humanDesignSignals.length > 0 || journalSignals.length > 0;

  // Render a "Current Themes" card (story-focused)
  const renderMostPresentCard = (category: PatternCategory) => {
    const strengthColor = getStrengthColor(category.signal_strength);

    return (
      <View
        key={category.category_id}
        style={[styles.presentCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        <View style={styles.presentCardHeader}>
          <Text style={[styles.presentCardName, { color: theme.text }]}>
            {category.category_name}
          </Text>
          <View style={styles.presentCardMeta}>
            <Text style={[styles.presentCardStrength, { color: strengthColor }]}>
              {getStrengthLabel(category.signal_strength)}
            </Text>
          </View>
        </View>
        
        {/* Synthesis or summary - the story */}
        <Text style={[styles.presentCardStory, { color: theme.textSecondary }]}>
          {category.synthesis || category.summary}
        </Text>
        
        {/* Reflection prompt */}
        <Text style={[styles.presentCardPrompt, { color: theme.accent }]}>
          {getCategoryReflectionPrompt(category.category_id)}
        </Text>
      </View>
    );
  };

  // Check if all categories are quiet
  const allQuiet = categories.every(c => c.signal_strength === 'quiet');

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading patterns...
          </Text>
        </View>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
          <TouchableOpacity
            style={[styles.retryButton, { borderColor: theme.border }]}
            onPress={() => loadPatternGraph()}
          >
            <Text style={[styles.retryText, { color: theme.accent }]}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isRefreshing}
          onRefresh={() => loadPatternGraph(true)}
          tintColor={theme.textTertiary}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.pageTitle, { color: theme.text }]}>
          Pattern Graph
        </Text>
        <Text style={[styles.pageSubtext, { color: theme.textTertiary }]}>
          Patterns that may be surfacing across what you've been exploring.
        </Text>
      </View>

      {/* Subtle theme indicator (replaces dashboard stats) */}
      {!allQuiet && (
        <Text style={[styles.themesIndicator, { color: theme.textTertiary }]}>
          Some themes may be more active than others right now.
        </Text>
      )}

      {/* SECTION 1: Pattern Tensions */}
      {patternTensions.length > 0 && (
        <View style={styles.tensionsSection}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
            PATTERN TENSIONS
          </Text>
          <Text style={[styles.sectionSubtext, { color: theme.textSecondary }]}>
            Sometimes two themes may be active at once, creating friction, growth, or choice.
          </Text>
          
          {patternTensions.map((tension, index) => (
            <View 
              key={index}
              style={[styles.tensionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
            >
              <Text style={[styles.tensionCategories, { color: theme.text }]}>
                {tension.category_a} ↔ {tension.category_b}
              </Text>
              <Text style={[styles.tensionSummary, { color: theme.textSecondary }]}>
                {tension.summary}
              </Text>
              <Text style={[styles.tensionPrompt, { color: theme.accent }]}>
                {tension.reflection_prompt}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* SECTION 2: Current Themes */}
      {topCategories.length > 0 && (
        <View style={styles.mostPresentSection}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
            CURRENT THEMES
          </Text>
          <Text style={[styles.sectionSubtext, { color: theme.textSecondary }]}>
            The themes that seem to be surfacing most clearly right now.
          </Text>
          
          {topCategories.map(category => renderMostPresentCard(category))}
        </View>
      )}

      {/* SECTION 3: Signals Behind These Patterns (grouped by source) */}
      {hasAnySignals && (
        <View style={styles.exploreSection}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
            SIGNALS BEHIND THESE PATTERNS
          </Text>
          <Text style={[styles.sectionSubtext, { color: theme.textSecondary }]}>
            The underlying sources that may be contributing to your patterns.
          </Text>
          
          {/* Gene Keys Signals */}
          {geneKeysSignals.length > 0 && (
            <View style={[styles.sourceSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.sourceTitle, { color: theme.text }]}>
                Gene Keys
              </Text>
              {geneKeysSignals.slice(0, 6).map((signal, idx) => {
                const formatted = formatGeneKeySignal(signal);
                return (
                  <View key={idx} style={styles.sourceSignalRow}>
                    <Text style={[styles.sourceSignalTitle, { color: theme.textSecondary }]}>
                      {formatted.title}
                    </Text>
                    {formatted.subtitle && (
                      <Text style={[styles.sourceSignalSubtitle, { color: theme.textTertiary }]}>
                        {formatted.subtitle}
                      </Text>
                    )}
                  </View>
                );
              })}
            </View>
          )}
          
          {/* Human Design Signals */}
          {humanDesignSignals.length > 0 && (
            <View style={[styles.sourceSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.sourceTitle, { color: theme.text }]}>
                Human Design
              </Text>
              {humanDesignSignals.slice(0, 6).map((signal, idx) => (
                <View key={idx} style={styles.sourceSignalRow}>
                  <Text style={[styles.sourceSignalTitle, { color: theme.textSecondary }]}>
                    {signal.label}
                  </Text>
                  {signal.detail && (
                    <Text style={[styles.sourceSignalSubtitle, { color: theme.textTertiary }]}>
                      {signal.detail}
                    </Text>
                  )}
                </View>
              ))}
            </View>
          )}
          
          {/* Journal / Reflection Signals */}
          {journalSignals.length > 0 && (
            <View style={[styles.sourceSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.sourceTitle, { color: theme.text }]}>
                Journal & Reflections
              </Text>
              <Text style={[styles.sourceKeywords, { color: theme.textSecondary }]}>
                Recent reflection keywords: {journalSignals.slice(0, 8).join(', ')}
              </Text>
            </View>
          )}
        </View>
      )}

      {/* Empty state message */}
      {allQuiet && (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
            Patterns may become clearer as you reflect, journal, and explore your lenses.
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
    gap: 16,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Header
  header: {
    marginBottom: 20,
  },
  pageTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 8,
  },
  pageSubtext: {
    fontSize: 14,
    lineHeight: 20,
  },
  
  // Themes indicator (replaces stats row)
  themesIndicator: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 24,
    fontStyle: 'italic',
  },
  
  // Section styles (shared)
  sectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  sectionSubtext: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 16,
  },
  
  // Pattern Tensions section
  tensionsSection: {
    marginBottom: 32,
  },
  tensionCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  tensionCategories: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 10,
  },
  tensionSummary: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 12,
  },
  tensionPrompt: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  
  // What's Most Present section
  mostPresentSection: {
    marginBottom: 32,
  },
  presentCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  presentCardHeader: {
    marginBottom: 12,
  },
  presentCardName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  presentCardMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  presentCardStrength: {
    fontSize: 12,
    fontWeight: '500',
  },
  presentCardTrendSep: {
    fontSize: 12,
    marginHorizontal: 6,
  },
  presentCardTrend: {
    fontSize: 12,
  },
  presentCardStory: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 12,
  },
  presentCardPrompt: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  
  // Explore the Signals section (now source-grouped)
  exploreSection: {
    marginBottom: 24,
  },
  sourceSection: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  sourceTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
  },
  sourceSignalRow: {
    marginBottom: 10,
  },
  sourceSignalTitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  sourceSignalSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  sourceKeywords: {
    fontSize: 13,
    lineHeight: 19,
  },
  
  // Expand icon
  expandIcon: {
    fontSize: 14,
    marginLeft: 8,
  },
  
  // Sources
  sourcesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    marginBottom: 16,
    gap: 8,
  },
  sourcesLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  sourceTag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  sourceTagText: {
    fontSize: 11,
  },
  
  // Synthesis section
  synthesisSection: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  synthesisLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  synthesisText: {
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  
  // Signals list
  signalsList: {
    gap: 10,
  },
  signalsLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  signalRow: {
    flexDirection: 'row',
  },
  signalBullet: {
    fontSize: 14,
    marginRight: 8,
    marginTop: 1,
  },
  signalContent: {
    flex: 1,
  },
  signalLabel: {
    fontSize: 14,
    lineHeight: 20,
  },
  signalDetail: {
    fontSize: 12,
    marginTop: 2,
  },
  
  // Empty state
  emptyState: {
    paddingVertical: 32,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 14,
    lineHeight: 21,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
