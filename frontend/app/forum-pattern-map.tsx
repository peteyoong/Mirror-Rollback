/**
 * Forum Pattern Map Screen - Task 48
 * 
 * Visualizes shared life patterns across forum members.
 * Shows shared pattern types and timeline clusters.
 * 
 * Uses Mirror language principles - observational, hedged language.
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
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import api from '../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface SharedPattern {
  pattern_type: string;
  years: number[];
  start_year: number;
  end_year: number;
  member_count: number;
  members: string[];
  member_names: string[];
  summary: string;
}

interface TimelineCluster {
  start_year: number;
  end_year: number;
  event_count: number;
  member_count: number;
  members: string[];
  intensity: number;
  sample_events: string[];
}

interface PatternMapData {
  forum_id: string;
  member_count: number;
  events_total: number;
  shared_patterns: SharedPattern[];
  timeline_clusters: TimelineCluster[];
  has_data: boolean;
  empty_state_message: string | null;
  generated_at: string;
}

// Pattern type display names and icons
const PATTERN_TYPE_CONFIG: Record<string, { label: string; icon: string; color: string }> = {
  career_growth: { label: 'Career Growth', icon: '📈', color: '#10B981' },
  identity_shift: { label: 'Identity Shift', icon: '🔄', color: '#8B5CF6' },
  relationship_turning: { label: 'Relationship Turning', icon: '💫', color: '#EC4899' },
  momentum_pressure: { label: 'Momentum Pressure', icon: '⚡', color: '#F59E0B' },
  reinvention: { label: 'Reinvention', icon: '🌱', color: '#06B6D4' },
  expression_hesitation: { label: 'Expression & Hesitation', icon: '💭', color: '#6366F1' },
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function ForumPatternMapScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const params = useLocalSearchParams();
  const { user } = useAppStore();
  
  const forumId = params.forumId as string;
  
  // State
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<PatternMapData | null>(null);
  
  // Debug logging
  const debugLog = (message: string, logData?: any) => {
    console.log(`[ForumPatternMap] ${message}`, logData || '');
  };
  
  // Fetch pattern map data
  const fetchPatternMap = useCallback(async () => {
    if (!forumId || !user?.id) {
      setError('Missing forum or user information');
      setLoading(false);
      return;
    }
    
    debugLog('Fetching pattern map', { forumId, userId: user.id });
    
    try {
      const response = await api.get(`/forums/${forumId}/pattern-map`, {
        params: { user_id: user.id }
      });
      
      setData(response.data);
      debugLog(`members=${response.data.member_count} events=${response.data.events_total}`);
      debugLog(`shared_patterns=${response.data.shared_patterns?.length || 0}`);
      debugLog(`clusters=${response.data.timeline_clusters?.length || 0}`);
      
      setError(null);
    } catch (err: any) {
      console.error('[ForumPatternMap] Fetch error:', err);
      setError(err.response?.data?.detail || 'Failed to load pattern map');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [forumId, user?.id]);
  
  useEffect(() => {
    fetchPatternMap();
  }, [fetchPatternMap]);
  
  const onRefresh = () => {
    setRefreshing(true);
    fetchPatternMap();
  };
  
  // Get year range display
  const getYearRange = (startYear: number, endYear: number): string => {
    if (startYear === endYear) return String(startYear);
    return `${startYear} – ${endYear}`;
  };
  
  // Get pattern config
  const getPatternConfig = (patternType: string) => {
    return PATTERN_TYPE_CONFIG[patternType] || {
      label: patternType.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      icon: '◈',
      color: theme.accent,
    };
  };
  
  // =============================================================================
  // RENDER: LOADING
  // =============================================================================
  
  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Analyzing forum patterns...
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // =============================================================================
  // RENDER: ERROR
  // =============================================================================
  
  if (error) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={theme.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Forum Pattern Map</Text>
          <View style={styles.headerSpacer} />
        </View>
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: theme.error || '#EF4444' }]}>{error}</Text>
          <TouchableOpacity style={[styles.retryButton, { backgroundColor: theme.accent }]} onPress={fetchPatternMap}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  // =============================================================================
  // RENDER: EMPTY STATE
  // =============================================================================
  
  if (!data?.has_data) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={theme.text} />
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Forum Pattern Map</Text>
          <View style={styles.headerSpacer} />
        </View>
        <View style={styles.emptyContainer}>
          <View style={[styles.emptyIconCircle, { backgroundColor: `${theme.textTertiary}15` }]}>
            <Text style={styles.emptyIcon}>🗺️</Text>
          </View>
          <Text style={[styles.emptyTitle, { color: theme.text }]}>
            No shared patterns yet
          </Text>
          <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
            {data?.empty_state_message || 'Forum patterns will appear once members add more turning points to their timelines.'}
          </Text>
          {data && (
            <View style={[styles.statsRow, { borderColor: theme.border }]}>
              <View style={styles.statItem}>
                <Text style={[styles.statValue, { color: theme.accent }]}>{data.member_count}</Text>
                <Text style={[styles.statLabel, { color: theme.textTertiary }]}>members</Text>
              </View>
              <View style={[styles.statDivider, { backgroundColor: theme.border }]} />
              <View style={styles.statItem}>
                <Text style={[styles.statValue, { color: theme.accent }]}>{data.events_total}</Text>
                <Text style={[styles.statLabel, { color: theme.textTertiary }]}>turning points</Text>
              </View>
            </View>
          )}
        </View>
      </SafeAreaView>
    );
  }
  
  // =============================================================================
  // RENDER: MAIN CONTENT
  // =============================================================================
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="chevron-back" size={24} color={theme.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Forum Pattern Map</Text>
        <View style={styles.headerSpacer} />
      </View>
      
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.accent} />
        }
      >
        {/* Title Section */}
        <View style={styles.titleSection}>
          <Text style={[styles.screenLabel, { color: theme.textTertiary }]}>FORUM PATTERN MAP</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            Patterns emerging across your forum timelines.
          </Text>
        </View>
        
        {/* Stats Row */}
        <View style={[styles.statsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.accent }]}>{data.member_count}</Text>
            <Text style={[styles.statLabel, { color: theme.textTertiary }]}>members</Text>
          </View>
          <View style={[styles.statDivider, { backgroundColor: theme.border }]} />
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.accent }]}>{data.events_total}</Text>
            <Text style={[styles.statLabel, { color: theme.textTertiary }]}>turning points mapped</Text>
          </View>
        </View>
        
        {/* Shared Patterns Section */}
        {data.shared_patterns.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Shared Patterns</Text>
            <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>
              Moments where members' journeys seem to align
            </Text>
            
            {data.shared_patterns.map((pattern, index) => {
              const config = getPatternConfig(pattern.pattern_type);
              return (
                <View
                  key={`pattern-${index}`}
                  style={[styles.patternCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                >
                  <View style={styles.patternHeader}>
                    <View style={[styles.patternIconBadge, { backgroundColor: `${config.color}20` }]}>
                      <Text style={styles.patternIcon}>{config.icon}</Text>
                    </View>
                    <View style={styles.patternHeaderText}>
                      <Text style={[styles.patternLabel, { color: theme.textTertiary }]}>
                        {config.label.toUpperCase()}
                      </Text>
                      <Text style={[styles.patternYears, { color: theme.text }]}>
                        {getYearRange(pattern.start_year, pattern.end_year)}
                      </Text>
                    </View>
                    <View style={[styles.memberCountBadge, { backgroundColor: `${theme.accent}15` }]}>
                      <Text style={[styles.memberCountText, { color: theme.accent }]}>
                        {pattern.member_count} members
                      </Text>
                    </View>
                  </View>
                  
                  <Text style={[styles.patternSummary, { color: theme.textSecondary }]}>
                    {pattern.summary}
                  </Text>
                  
                  {/* Member avatars/names */}
                  <View style={styles.memberAvatars}>
                    {pattern.member_names.slice(0, 5).map((name, i) => (
                      <View key={i} style={[styles.memberAvatar, { backgroundColor: `${config.color}30`, borderColor: theme.background }]}>
                        <Text style={[styles.memberAvatarText, { color: config.color }]}>
                          {name.charAt(0).toUpperCase()}
                        </Text>
                      </View>
                    ))}
                    {pattern.member_names.length > 5 && (
                      <Text style={[styles.moreMembers, { color: theme.textTertiary }]}>
                        +{pattern.member_names.length - 5}
                      </Text>
                    )}
                  </View>
                </View>
              );
            })}
          </View>
        )}
        
        {/* Timeline Clusters Section */}
        {data.timeline_clusters.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Timeline Clusters</Text>
            <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>
              Periods of concentrated activity across members
            </Text>
            
            {/* Visual Timeline */}
            <View style={[styles.timelineContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              {data.timeline_clusters.map((cluster, index) => {
                // Calculate intensity for visual representation
                const intensityLevel = Math.min(cluster.intensity / 3, 1);
                const clusterColor = `rgba(139, 92, 246, ${0.3 + intensityLevel * 0.5})`; // Purple with varying opacity
                
                return (
                  <View key={`cluster-${index}`} style={styles.clusterItem}>
                    {/* Cluster marker */}
                    <View style={styles.clusterMarkerRow}>
                      <View style={[styles.clusterMarker, { backgroundColor: clusterColor }]}>
                        <Text style={styles.clusterMarkerText}>⚡</Text>
                      </View>
                      <View style={[styles.clusterLine, { backgroundColor: theme.border }]} />
                    </View>
                    
                    {/* Cluster info */}
                    <View style={styles.clusterInfo}>
                      <Text style={[styles.clusterYears, { color: theme.text }]}>
                        {getYearRange(cluster.start_year, cluster.end_year)}
                      </Text>
                      <View style={styles.clusterStats}>
                        <Text style={[styles.clusterStat, { color: theme.accent }]}>
                          {cluster.member_count} members
                        </Text>
                        <Text style={[styles.clusterStatDot, { color: theme.textTertiary }]}>•</Text>
                        <Text style={[styles.clusterStat, { color: theme.textSecondary }]}>
                          {cluster.event_count} turning points
                        </Text>
                      </View>
                      
                      {/* Sample events */}
                      {cluster.sample_events.length > 0 && (
                        <View style={styles.sampleEvents}>
                          {cluster.sample_events.slice(0, 2).map((event, i) => (
                            <Text key={i} style={[styles.sampleEvent, { color: theme.textTertiary }]} numberOfLines={1}>
                              "{event}"
                            </Text>
                          ))}
                        </View>
                      )}
                    </View>
                  </View>
                );
              })}
            </View>
          </View>
        )}
        
        {/* Footer note */}
        <View style={styles.footerNote}>
          <Text style={[styles.footerNoteText, { color: theme.textTertiary }]}>
            Patterns are observational and may not represent causal connections.
          </Text>
        </View>
        
        {/* Bottom spacing */}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  headerSpacer: {
    width: 32,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    gap: 16,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyIconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  emptyIcon: {
    fontSize: 36,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 16,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 17,
    lineHeight: 30,
    textAlign: 'center',
    marginBottom: 24,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
  },
  titleSection: {
    marginBottom: 20,
  },
  screenLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 14,
  },
  subtitle: {
    fontSize: 17,
    lineHeight: 30,
  },
  statsCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 28,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 20,
    marginTop: 8,
    borderTopWidth: 1,
  },
  statItem: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  statValue: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statDivider: {
    width: 1,
    height: 40,
  },
  section: {
    marginBottom: 28,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 16,
    marginBottom: 16,
  },
  patternCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
  },
  patternHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  patternIconBadge: {
    width: 40,
    height: 40,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  patternIcon: {
    fontSize: 24,
  },
  patternHeaderText: {
    flex: 1,
  },
  patternLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 2,
  },
  patternYears: {
    fontSize: 22,
    fontWeight: '600',
  },
  memberCountBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  memberCountText: {
    fontSize: 14,
    fontWeight: '600',
  },
  patternSummary: {
    fontSize: 16,
    lineHeight: 30,
    marginBottom: 16,
  },
  memberAvatars: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  memberAvatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: -8,
    borderWidth: 2,
  },
  memberAvatarText: {
    fontSize: 14,
    fontWeight: '600',
  },
  moreMembers: {
    fontSize: 14,
    marginLeft: 16,
  },
  timelineContainer: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
  },
  clusterItem: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  clusterMarkerRow: {
    alignItems: 'center',
    marginRight: 16,
  },
  clusterMarker: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clusterMarkerText: {
    fontSize: 16,
  },
  clusterLine: {
    width: 2,
    flex: 1,
    marginTop: 4,
  },
  clusterInfo: {
    flex: 1,
    paddingTop: 4,
  },
  clusterYears: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 4,
  },
  clusterStats: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  clusterStat: {
    fontSize: 16,
    fontWeight: '500',
  },
  clusterStatDot: {
    marginHorizontal: 6,
  },
  sampleEvents: {
    marginTop: 4,
  },
  sampleEvent: {
    fontSize: 14,
    fontStyle: 'italic',
    marginBottom: 2,
  },
  footerNote: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  footerNoteText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
  },
});
