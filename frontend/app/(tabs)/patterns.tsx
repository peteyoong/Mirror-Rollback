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

  const renderCategoryCard = (category: PatternCategory) => {
    const isExpanded = expandedCategory === category.category_id;
    const strengthColor = getStrengthColor(category.signal_strength);
    const hasSignals = category.matched_signals.length > 0;
    const trendColor = getTrendColor(category.trend);

    return (
      <View
        key={category.category_id}
        style={[styles.categoryCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        {/* Header - always visible */}
        <TouchableOpacity
          style={styles.categoryHeader}
          onPress={() => toggleCategory(category.category_id)}
          activeOpacity={0.7}
        >
          <View style={styles.categoryHeaderLeft}>
            <View style={[styles.strengthIndicator, { backgroundColor: strengthColor }]} />
            <View style={styles.categoryHeaderInfo}>
              <Text style={[styles.categoryName, { color: theme.text }]}>
                {category.category_name}
              </Text>
              <View style={styles.categoryMetaRow}>
                <Text style={[styles.categoryStrength, { color: strengthColor }]}>
                  {getStrengthLabel(category.signal_strength)}
                </Text>
                <Text style={[styles.categoryTrendSeparator, { color: theme.textTertiary }]}>
                  •
                </Text>
                <Text style={[styles.categoryTrend, { color: trendColor }]}>
                  {getTrendLabel(category.trend)}
                </Text>
              </View>
            </View>
          </View>
          {hasSignals && (
            <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
              {isExpanded ? '▾' : '▸'}
            </Text>
          )}
        </TouchableOpacity>

        {/* Summary - always visible */}
        <View style={[styles.summaryRow, { borderTopColor: theme.border }]}>
          <Text style={[styles.summaryText, { color: theme.textSecondary }]}>
            {category.summary}
          </Text>
        </View>

        {/* Expanded content */}
        {isExpanded && hasSignals && (
          <View style={[styles.expandedContent, { borderTopColor: theme.border }]}>
            {/* Pattern Reflection - LLM synthesis for recurring patterns */}
            {category.synthesis && (
              <View style={[styles.synthesisSection, { borderBottomColor: theme.border }]}>
                <Text style={[styles.synthesisLabel, { color: theme.textTertiary }]}>
                  PATTERN REFLECTION
                </Text>
                <Text style={[styles.synthesisText, { color: theme.textSecondary }]}>
                  {category.synthesis}
                </Text>
              </View>
            )}

            {/* Matched sources */}
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

            {/* Matched signals */}
            <View style={styles.signalsList}>
              <Text style={[styles.signalsLabel, { color: theme.textTertiary }]}>
                Matched Patterns
              </Text>
              {category.matched_signals.map((signal, idx) => (
                <View key={idx} style={styles.signalRow}>
                  <Text style={[styles.signalBullet, { color: theme.accent }]}>•</Text>
                  <View style={styles.signalContent}>
                    <Text style={[styles.signalLabel, { color: theme.text }]}>
                      {signal.label}
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

      {/* Summary stats */}
      {summary && !allQuiet && (
        <View style={[styles.statsRow, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.statItem}>
            <Text style={[styles.statNumber, { color: theme.accent }]}>
              {summary.active_categories}
            </Text>
            <Text style={[styles.statLabel, { color: theme.textTertiary }]}>
              Recurring
            </Text>
          </View>
          <View style={[styles.statDivider, { backgroundColor: theme.border }]} />
          <View style={styles.statItem}>
            <Text style={[styles.statNumber, { color: theme.textSecondary }]}>
              {summary.emerging_categories}
            </Text>
            <Text style={[styles.statLabel, { color: theme.textTertiary }]}>
              Present
            </Text>
          </View>
        </View>
      )}

      {/* Categories list */}
      <View style={styles.categoriesList}>
        {categories.map(category => renderCategoryCard(category))}
      </View>

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
