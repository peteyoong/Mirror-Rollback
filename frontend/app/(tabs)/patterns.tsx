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

  const getTrendLabel = (trend: string) => {
    switch (trend) {
      case 'rising':
        return '↑ Rising';
      case 'fading':
        return '↓ Fading';
      default:
        return '→ Steady';
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'rising':
        return theme.accent;
      case 'fading':
        return theme.textTertiary;
      default:
        return theme.textSecondary;
    }
  };

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

  // Render a "What's Most Present" card (story-focused)
  const renderMostPresentCard = (category: PatternCategory) => {
    const strengthColor = getStrengthColor(category.signal_strength);
    const trendColor = getTrendColor(category.trend);

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
            <Text style={[styles.presentCardTrendSep, { color: theme.textTertiary }]}>•</Text>
            <Text style={[styles.presentCardTrend, { color: trendColor }]}>
              {getTrendLabel(category.trend)}
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

  // Render an "Explore the Signals" card (evidence-focused, expandable)
  const renderSignalsCard = (category: PatternCategory) => {
    const isExpanded = expandedCategory === category.category_id;
    const strengthColor = getStrengthColor(category.signal_strength);
    const hasSignals = category.matched_signals.length > 0;
    const trendColor = getTrendColor(category.trend);

    // Skip quiet categories
    if (category.signal_strength === 'quiet') return null;

    return (
      <View
        key={category.category_id}
        style={[styles.signalsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        <TouchableOpacity
          style={styles.signalsCardHeader}
          onPress={() => toggleCategory(category.category_id)}
          activeOpacity={0.7}
        >
          <View style={styles.signalsCardLeft}>
            <View style={[styles.signalsIndicator, { backgroundColor: strengthColor }]} />
            <Text style={[styles.signalsCardName, { color: theme.text }]}>
              {category.category_name}
            </Text>
          </View>
          {hasSignals && (
            <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
              {isExpanded ? '▾' : '▸'}
            </Text>
          )}
        </TouchableOpacity>

        {/* Expanded content - the evidence */}
        {isExpanded && hasSignals && (
          <View style={[styles.signalsCardContent, { borderTopColor: theme.border }]}>
            {/* Sources */}
            {category.matched_sources.length > 0 && (
              <View style={styles.sourcesRow}>
                <Text style={[styles.sourcesLabel, { color: theme.textTertiary }]}>
                  Sources:
                </Text>
                {category.matched_sources.map((source, idx) => (
                  <View key={idx} style={[styles.sourceTag, { backgroundColor: 'rgba(255,255,255,0.05)' }]}>
                    <Text style={[styles.sourceTagText, { color: theme.textSecondary }]}>
                      {formatSource(source)}
                    </Text>
                  </View>
                ))}
              </View>
            )}

            {/* Signal list - renamed and cleaned */}
            <View style={styles.signalsList}>
              <Text style={[styles.signalsLabel, { color: theme.textTertiary }]}>
                What May Be Influencing This
              </Text>
              {category.matched_signals.map((signal, idx) => (
                <View key={idx} style={styles.signalRow}>
                  <Text style={[styles.signalBullet, { color: theme.accent }]}>•</Text>
                  <View style={styles.signalContent}>
                    <Text style={[styles.signalLabel, { color: theme.text }]}>
                      {formatSignalLabel(signal)}
                    </Text>
                    {signal.sphere_name && (
                      <Text style={[styles.signalDetail, { color: theme.textTertiary }]}>
                        {signal.sphere_name}
                      </Text>
                    )}
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}
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
          Patterns that may be showing up across what you've explored and reflected on.
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

      {/* SECTION 2: What's Most Present */}
      {topCategories.length > 0 && (
        <View style={styles.mostPresentSection}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
            WHAT'S MOST PRESENT
          </Text>
          <Text style={[styles.sectionSubtext, { color: theme.textSecondary }]}>
            The themes that seem to be surfacing most clearly right now.
          </Text>
          
          {topCategories.map(category => renderMostPresentCard(category))}
        </View>
      )}

      {/* SECTION 3: Explore the Signals */}
      {categories.filter(c => c.signal_strength !== 'quiet').length > 0 && (
        <View style={styles.exploreSection}>
          <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
            EXPLORE THE SIGNALS
          </Text>
          <Text style={[styles.sectionSubtext, { color: theme.textSecondary }]}>
            The underlying data behind your patterns.
          </Text>
          
          <View style={styles.signalsCardList}>
            {categories.map(category => renderSignalsCard(category))}
          </View>
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

      {/* Timeline Section */}
      {timeline.length > 0 && (
        <View style={styles.timelineSection}>
          <Text style={[styles.timelineSectionTitle, { color: theme.textTertiary }]}>
            PATTERN TIMELINE
          </Text>
          <Text style={[styles.timelineSectionSubtext, { color: theme.textSecondary }]}>
            How patterns have appeared over time.
          </Text>
          
          {timeline.map((bucket) => {
            // Only show categories that are not quiet
            const activeCategories = bucket.categories.filter(
              c => c.signal_strength !== 'quiet'
            );
            
            if (!bucket.has_activity) return null;
            
            return (
              <View 
                key={bucket.bucket_name} 
                style={[styles.timeBucket, { backgroundColor: theme.surface, borderColor: theme.border }]}
              >
                <Text style={[styles.bucketLabel, { color: theme.text }]}>
                  {bucket.bucket_label}
                </Text>
                
                <View style={styles.bucketCategories}>
                  {activeCategories.map((cat) => (
                    <View key={cat.category_id} style={styles.timelineCategoryRow}>
                      <View style={styles.timelineCategoryLeft}>
                        <View 
                          style={[
                            styles.timelineStrengthDot, 
                            { backgroundColor: cat.signal_strength === 'recurring' ? theme.accent : theme.textSecondary }
                          ]} 
                        />
                        <Text style={[styles.timelineCategoryName, { color: theme.text }]}>
                          {cat.category_name}
                        </Text>
                      </View>
                      <Text 
                        style={[
                          styles.timelineStrengthLabel, 
                          { color: cat.signal_strength === 'recurring' ? theme.accent : theme.textTertiary }
                        ]}
                      >
                        {cat.signal_strength === 'recurring' ? 'Recurring' : 'Present'}
                      </Text>
                    </View>
                  ))}
                </View>
                
                {activeCategories.length === 0 && (
                  <Text style={[styles.bucketEmpty, { color: theme.textTertiary }]}>
                    No strong patterns during this period.
                  </Text>
                )}
              </View>
            );
          })}
          
          {!timeline.some(b => b.has_activity) && (
            <View style={styles.timelineEmpty}>
              <Text style={[styles.timelineEmptyText, { color: theme.textTertiary }]}>
                Patterns become clearer over time as you reflect and return.
              </Text>
            </View>
          )}
        </View>
      )}

      {/* Footer note */}
      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: theme.textTertiary }]}>
          This is a reflection tool, not a diagnosis. Patterns suggest themes worth noticing, not certainties.
        </Text>
      </View>
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
    marginBottom: 24,
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
  
  // Stats row
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  statNumber: {
    fontSize: 24,
    fontWeight: '600',
  },
  statLabel: {
    fontSize: 12,
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    height: 32,
  },
  
  // Pattern Tensions section
  tensionsSection: {
    marginBottom: 24,
  },
  tensionsSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  tensionsSectionSubtext: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 16,
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
  
  // Categories list
  categoriesList: {
    gap: 12,
  },
  
  // Category card
  categoryCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  
  // Category header
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  categoryHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  strengthIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  categoryHeaderInfo: {
    flex: 1,
  },
  categoryName: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 2,
  },
  categoryMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryStrength: {
    fontSize: 12,
    fontWeight: '500',
  },
  categoryTrendSeparator: {
    fontSize: 12,
    marginHorizontal: 4,
  },
  categoryTrend: {
    fontSize: 12,
    fontWeight: '400',
  },
  expandIcon: {
    fontSize: 14,
    marginLeft: 8,
  },
  
  // Summary row
  summaryRow: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  summaryText: {
    fontSize: 13,
    lineHeight: 19,
  },
  
  // Expanded content
  expandedContent: {
    padding: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
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
  
  // Footer
  footer: {
    paddingTop: 24,
    paddingHorizontal: 8,
  },
  footerText: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  
  // Timeline section
  timelineSection: {
    marginTop: 32,
    marginBottom: 16,
  },
  timelineSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1.5,
    marginBottom: 6,
  },
  timelineSectionSubtext: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 16,
  },
  timeBucket: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  bucketLabel: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 12,
  },
  bucketCategories: {
    gap: 10,
  },
  timelineCategoryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timelineCategoryLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timelineStrengthDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 10,
  },
  timelineCategoryName: {
    fontSize: 14,
  },
  timelineStrengthLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  bucketEmpty: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  timelineEmpty: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  timelineEmptyText: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
  },
});
