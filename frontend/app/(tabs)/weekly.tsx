import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';

// Types
interface TopDomain {
  domain: string;
  domain_id: string;
  trend: 'rising' | 'steady' | 'softening' | 'emerging';
  weekly_score: number;
  days_present: number;
  timing_amplified: boolean;
  evidence_summary: string[];
}

interface WeeklySummary {
  week_start: string;
  week_end: string;
  top_domains: TopDomain[];
  all_domains: {
    domain: string;
    domain_id: string;
    trend: string;
    weekly_score: number;
    days_present: number;
  }[];
  cross_week_shift: string | null;
  narrative: string;
  reflection_prompt: string;
  evidence_sources: string[];
  has_timing_influence: boolean;
}

export default function WeeklyScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  
  const [summary, setSummary] = useState<WeeklySummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchWeeklySummary = async (showRefresh = false) => {
    if (!user?.id) return;
    
    if (showRefresh) setIsRefreshing(true);
    else setIsLoading(true);
    
    try {
      const response = await api.get(`/weekly-patterns/${user.id}`);
      if (response.data?.success) {
        setSummary(response.data.weekly_summary);
        setError(null);
      } else {
        setError('Failed to load weekly patterns');
      }
    } catch (err) {
      console.error('[Weekly] Error fetching summary:', err);
      setError('Unable to load weekly summary');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };
  
  useEffect(() => {
    fetchWeeklySummary();
  }, [user?.id]);
  
  const formatDateRange = (start: string, end: string): string => {
    const startDate = new Date(start + 'T00:00:00');
    const endDate = new Date(end + 'T00:00:00');
    
    const formatOptions: Intl.DateTimeFormatOptions = { 
      month: 'short', 
      day: 'numeric' 
    };
    
    const startStr = startDate.toLocaleDateString('en-US', formatOptions);
    const endStr = endDate.toLocaleDateString('en-US', formatOptions);
    
    return `${startStr} – ${endStr}`;
  };
  
  const getTrendLabel = (trend: string): string => {
    switch (trend) {
      case 'rising': return 'Rising this week';
      case 'softening': return 'Softening this week';
      case 'emerging': return 'Emerging this week';
      case 'steady': return 'Steady this week';
      default: return 'Present this week';
    }
  };
  
  const getTrendColor = (trend: string): string => {
    switch (trend) {
      case 'rising': return '#7dd3a0';     // Soft green
      case 'emerging': return '#a0c4e8';   // Soft blue
      case 'softening': return '#e8c4a0';  // Soft amber
      case 'steady': return theme.textSecondary;
      default: return theme.textSecondary;
    }
  };
  
  // Loading state
  if (isLoading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Synthesizing your week...
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // Error state
  if (error || !summary) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.errorContainer}>
          <Text style={[styles.errorIcon]}>☽</Text>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {error || 'Unable to load weekly patterns'}
          </Text>
          <Text style={[styles.errorSubtext, { color: theme.textTertiary }]}>
            Continue reflecting to see patterns emerge
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => fetchWeeklySummary(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            Your Week in Patterns
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            A gentle synthesis of what seemed to repeat, intensify, or shift.
          </Text>
          <Text style={[styles.dateRange, { color: theme.textTertiary }]}>
            Week of {formatDateRange(summary.week_start, summary.week_end)}
          </Text>
        </View>
        
        {/* Weekly Summary Card */}
        <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.narrative, { color: theme.textSecondary }]}>
            {summary.narrative}
          </Text>
        </View>
        
        {/* Top Recurring Themes */}
        {summary.top_domains.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Top Recurring Themes
            </Text>
            
            {summary.top_domains.map((domain, index) => (
              <View 
                key={domain.domain_id}
                style={[styles.domainCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              >
                <View style={styles.domainHeader}>
                  <Text style={[styles.domainName, { color: theme.text }]}>
                    {domain.domain}
                  </Text>
                  <Text style={[styles.domainTrend, { color: getTrendColor(domain.trend) }]}>
                    {getTrendLabel(domain.trend)}
                  </Text>
                </View>
                
                <Text style={[styles.domainEvidence, { color: theme.textTertiary }]}>
                  {domain.evidence_summary.length > 0 
                    ? `Appeared through ${domain.evidence_summary.join(' and ').toLowerCase()}.`
                    : `Present across ${domain.days_present} days this week.`
                  }
                </Text>
                
                {domain.timing_amplified && (
                  <Text style={[styles.timingNote, { color: theme.textTertiary }]}>
                    ✦ Timing emphasis active
                  </Text>
                )}
              </View>
            ))}
          </View>
        )}
        
        {/* What Shaped This Week */}
        {summary.evidence_sources.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              What May Have Shaped This Pattern
            </Text>
            
            <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              {summary.evidence_sources.map((source, index) => (
                <View key={index} style={styles.evidenceItem}>
                  <Text style={[styles.evidenceBullet, { color: theme.textTertiary }]}>•</Text>
                  <Text style={[styles.evidenceText, { color: theme.textSecondary }]}>
                    {source}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}
        
        {/* Cross-Week Shift */}
        {summary.cross_week_shift && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Shift Across the Week
            </Text>
            
            <View style={[styles.shiftCard, { backgroundColor: theme.surface, borderColor: theme.accent }]}>
              <Text style={[styles.shiftText, { color: theme.textSecondary }]}>
                {summary.cross_week_shift}
              </Text>
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
              "{summary.reflection_prompt}"
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
  
  // Loading/Error states
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorIcon: {
    fontSize: 48,
    marginBottom: 16,
    opacity: 0.5,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 8,
  },
  errorSubtext: {
    fontSize: 14,
    textAlign: 'center',
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
  dateRange: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  
  // Cards
  card: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 18,
    marginBottom: 16,
  },
  
  // Narrative
  narrative: {
    fontSize: 15,
    lineHeight: 24,
  },
  
  // Sections
  section: {
    marginTop: 8,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  
  // Domain cards
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
    marginBottom: 8,
  },
  domainName: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  domainTrend: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 8,
  },
  domainEvidence: {
    fontSize: 13,
    lineHeight: 20,
  },
  timingNote: {
    fontSize: 11,
    marginTop: 8,
    fontStyle: 'italic',
  },
  
  // Evidence
  evidenceItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  evidenceBullet: {
    fontSize: 14,
    marginRight: 10,
    marginTop: 2,
  },
  evidenceText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  
  // Shift card
  shiftCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    borderLeftWidth: 3,
  },
  shiftText: {
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic',
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
