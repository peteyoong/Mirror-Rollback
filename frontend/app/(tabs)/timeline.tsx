import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';

// Enable LayoutAnimation for Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// Types
interface WeekEntry {
  week_start: string;
  week_end: string;
  top_domain: string | null;
  top_domain_id: string | null;
  secondary_domains: string[];
  secondary_domain_ids: string[];
  trend_map: Record<string, string>;
  timing_amplified_domains: string[];
  narrative: string;
  reflection_prompt: string;
}

interface TimelineInsights {
  most_recurring_domain: string | null;
  strongest_recent_domain: string | null;
  volatile_domain: string | null;
  stable_domain: string | null;
  reemerging_domain: string | null;
}

interface TimelineData {
  range_label: string;
  weeks: WeekEntry[];
  insights: TimelineInsights;
  narrative_summary: string;
  reflection_prompt: string;
  is_partial: boolean;
  weeks_available: number;
}

export default function TimelineScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedWeek, setExpandedWeek] = useState<string | null>(null);
  
  const fetchTimeline = async (showRefresh = false) => {
    if (!user?.id) return;
    
    if (showRefresh) setIsRefreshing(true);
    else setIsLoading(true);
    
    try {
      const response = await api.get(`/pattern-timeline/${user.id}?weeks=8`);
      if (response.data?.success) {
        setTimeline(response.data.timeline);
        setError(null);
      } else {
        setError('Failed to load timeline');
      }
    } catch (err) {
      console.error('[Timeline] Error fetching:', err);
      setError('Unable to load pattern timeline');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };
  
  useEffect(() => {
    fetchTimeline();
  }, [user?.id]);
  
  const toggleWeekExpanded = (weekStart: string) => {
    if (Platform.OS !== 'web') {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    }
    setExpandedWeek(expandedWeek === weekStart ? null : weekStart);
  };
  
  const formatWeekLabel = (start: string, end: string): string => {
    const startDate = new Date(start + 'T00:00:00');
    const endDate = new Date(end + 'T00:00:00');
    
    const formatOptions: Intl.DateTimeFormatOptions = { 
      month: 'short', 
      day: 'numeric' 
    };
    
    const startStr = startDate.toLocaleDateString('en-US', formatOptions);
    const endStr = endDate.toLocaleDateString('en-US', formatOptions);
    
    return `${startStr}–${endStr}`;
  };
  
  // Map internal trend labels to softer UI language
  const getTrendChipLabel = (trend: string): string => {
    switch (trend) {
      case 'rising': return 'Growing';
      case 'steady': return 'Steady';
      case 'softening': return 'Easing';
      case 'emerging': return 'Emerging';
      default: return 'Present';
    }
  };
  
  const getTrendChipColor = (trend: string): { bg: string; text: string } => {
    switch (trend) {
      case 'rising':
        return { bg: 'rgba(125, 211, 160, 0.15)', text: '#7dd3a0' };
      case 'emerging':
        return { bg: 'rgba(160, 196, 232, 0.15)', text: '#a0c4e8' };
      case 'softening':
        return { bg: 'rgba(232, 196, 160, 0.15)', text: '#e8c4a0' };
      case 'steady':
      default:
        return { bg: 'rgba(255, 255, 255, 0.08)', text: theme.textTertiary };
    }
  };
  
  // Loading state
  if (isLoading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Building your pattern timeline...
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // Error or empty state
  if (error || !timeline || timeline.weeks.length === 0) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>◷</Text>
          <Text style={[styles.emptyTitle, { color: theme.text }]}>
            Your timeline is still taking shape
          </Text>
          <Text style={[styles.emptySubtext, { color: theme.textSecondary }]}>
            As more weekly patterns accumulate, a longer view of recurring themes will appear here.
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // Render insight card
  const renderInsightCard = (label: string, domain: string | null) => {
    if (!domain) return null;
    
    return (
      <View style={[styles.insightCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.insightLabel, { color: theme.textTertiary }]}>
          {label}
        </Text>
        <Text style={[styles.insightDomain, { color: theme.text }]}>
          {domain}
        </Text>
      </View>
    );
  };
  
  // Render week entry
  const renderWeekEntry = (week: WeekEntry, index: number) => {
    const isExpanded = expandedWeek === week.week_start;
    const weekLabel = formatWeekLabel(week.week_start, week.week_end);
    
    if (!week.top_domain) return null;
    
    // Get trends for display
    const trends = Object.entries(week.trend_map).slice(0, 3);
    
    return (
      <TouchableOpacity
        key={week.week_start}
        style={[styles.weekCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
        onPress={() => toggleWeekExpanded(week.week_start)}
        activeOpacity={0.8}
      >
        {/* Week Header */}
        <View style={styles.weekHeader}>
          <Text style={[styles.weekLabel, { color: theme.textTertiary }]}>
            {weekLabel}
          </Text>
          <Text style={[styles.expandIndicator, { color: theme.textTertiary }]}>
            {isExpanded ? '▲' : '▼'}
          </Text>
        </View>
        
        {/* Top Domain */}
        <Text style={[styles.topDomain, { color: theme.text }]}>
          {week.top_domain}
        </Text>
        
        {/* Secondary Domains */}
        {week.secondary_domains.length > 0 && (
          <Text style={[styles.secondaryDomains, { color: theme.textSecondary }]}>
            {week.secondary_domains.join(' • ')}
          </Text>
        )}
        
        {/* Trend Chips */}
        <View style={styles.trendChipsRow}>
          {trends.map(([domain, trend]) => {
            const colors = getTrendChipColor(trend);
            return (
              <View
                key={domain}
                style={[styles.trendChip, { backgroundColor: colors.bg }]}
              >
                <Text style={[styles.trendChipText, { color: colors.text }]}>
                  {getTrendChipLabel(trend)}
                </Text>
              </View>
            );
          })}
        </View>
        
        {/* Expanded Content */}
        {isExpanded && (
          <View style={[styles.expandedContent, { borderTopColor: theme.border }]}>
            {week.narrative && (
              <Text style={[styles.weekNarrative, { color: theme.textSecondary }]}>
                {week.narrative}
              </Text>
            )}
            {week.reflection_prompt && (
              <Text style={[styles.weekReflection, { color: theme.accent }]}>
                "{week.reflection_prompt}"
              </Text>
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => fetchTimeline(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Pattern Timeline
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            A longer view of what has repeated, shifted, or returned.
          </Text>
          <Text style={[styles.rangeLabel, { color: theme.textTertiary }]}>
            {timeline.range_label}
          </Text>
        </View>
        
        {/* Partial Data Note */}
        {timeline.is_partial && (
          <View style={[styles.partialNote, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.partialNoteText, { color: theme.textTertiary }]}>
              This view is based on the pattern history available so far.
            </Text>
          </View>
        )}
        
        {/* Narrative Summary Card */}
        <View style={[styles.narrativeCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.narrativeText, { color: theme.textSecondary }]}>
            {timeline.narrative_summary}
          </Text>
        </View>
        
        {/* Timeline Section */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Week by Week
          </Text>
          
          {timeline.weeks.map((week, index) => renderWeekEntry(week, index))}
        </View>
        
        {/* Insights Section */}
        {(timeline.insights.most_recurring_domain || 
          timeline.insights.strongest_recent_domain ||
          timeline.insights.volatile_domain ||
          timeline.insights.stable_domain ||
          timeline.insights.reemerging_domain) && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Pattern Insights
            </Text>
            
            <View style={styles.insightsGrid}>
              {renderInsightCard('Most recurring', timeline.insights.most_recurring_domain)}
              {renderInsightCard('Strongest recently', timeline.insights.strongest_recent_domain)}
              {renderInsightCard('Most variable', timeline.insights.volatile_domain)}
              {renderInsightCard('Most steady', timeline.insights.stable_domain)}
              {renderInsightCard('Re-emerging', timeline.insights.reemerging_domain)}
            </View>
          </View>
        )}
        
        {/* Reflection Prompt */}
        <View style={styles.section}>
          <View style={[styles.reflectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>
              A question to sit with
            </Text>
            <Text style={[styles.reflectionPrompt, { color: theme.accent }]}>
              "{timeline.reflection_prompt}"
            </Text>
          </View>
        </View>
        
        {/* Bottom spacer */}
        <View style={styles.bottomSpacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  
  // Loading/Empty states
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
    fontStyle: 'italic',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
    opacity: 0.5,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 12,
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
    fontStyle: 'italic',
  },
  
  // Header
  header: {
    paddingTop: 20,
    paddingBottom: 24,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: '600',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  rangeLabel: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  
  // Partial note
  partialNote: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
    marginBottom: 16,
  },
  partialNoteText: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Narrative card
  narrativeCard: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 18,
    marginBottom: 24,
  },
  narrativeText: {
    fontSize: 15,
    lineHeight: 24,
  },
  
  // Sections
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 14,
    letterSpacing: 0.3,
  },
  
  // Week cards
  weekCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  weekHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  weekLabel: {
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  expandIndicator: {
    fontSize: 10,
  },
  topDomain: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  secondaryDomains: {
    fontSize: 13,
    marginBottom: 12,
  },
  trendChipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  trendChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  trendChipText: {
    fontSize: 11,
    fontWeight: '500',
  },
  expandedContent: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  weekNarrative: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 12,
  },
  weekReflection: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  
  // Insights grid
  insightsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  insightCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    minWidth: '47%',
    flex: 1,
  },
  insightLabel: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  insightDomain: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Reflection
  reflectionCard: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    alignItems: 'center',
  },
  reflectionLabel: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  reflectionPrompt: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  
  bottomSpacer: {
    height: 40,
  },
});
