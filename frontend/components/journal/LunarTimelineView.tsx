/**
 * Lunar Timeline View - Task 51
 * 
 * Shows lunar journal entries across the cycle, grouped by lunar day.
 * Helps Reflectors see how their perception shifts across the cycle.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface LunarEntry {
  id: string;
  content: string;
  created_at: string;
  lunar_day: number;
  moon_phase: string;
  moon_gate: number | null;
  gate_line: number | null;
  gate_title: string | null;
  gate_theme: string | null;
  center: string | null;
  consideration_id: string | null;
}

interface TimelineDay {
  lunar_day: number;
  entries: LunarEntry[];
  entry_count: number;
  gates: number[];
}

interface CycleTimeline {
  success: boolean;
  current_lunar_day: number;
  moon_phase: string;
  cycle_start: string;
  cycle_end: string;
  is_near_new_moon: boolean;
  days_until_new_moon: number;
  timeline: TimelineDay[];
  total_entries: number;
}

interface LunarTimelineViewProps {
  userId: string;
  considerationId?: string | null;
  considerationTopic?: string;
  onEntryPress?: (entry: LunarEntry) => void;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const LUNAR_COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  glow: 'rgba(192, 200, 212, 0.12)',
};

// =============================================================================
// COMPONENT
// =============================================================================

export default function LunarTimelineView({
  userId,
  considerationId,
  considerationTopic,
  onEntryPress,
}: LunarTimelineViewProps) {
  const { theme } = useTheme();
  const [timeline, setTimeline] = useState<CycleTimeline | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set());

  const fetchTimeline = useCallback(async (showRefresh = false) => {
    if (!userId) return;
    
    if (showRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    
    try {
      const url = considerationId 
        ? `/lunar-journal/${userId}/timeline?consideration_id=${considerationId}`
        : `/lunar-journal/${userId}/timeline`;
      
      const response = await api.get(url);
      
      if (response.data?.success) {
        setTimeline(response.data);
      }
    } catch (err) {
      console.error('[LunarTimeline] Error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [userId, considerationId]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  const toggleDay = (day: number) => {
    setExpandedDays(prev => {
      const next = new Set(prev);
      if (next.has(day)) {
        next.delete(day);
      } else {
        next.add(day);
      }
      return next;
    });
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const truncateContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength).trim() + '...';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={LUNAR_COLORS.moonlight} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading lunar timeline...
        </Text>
      </View>
    );
  }

  if (!timeline || timeline.total_entries === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>🌙</Text>
        <Text style={[styles.emptyTitle, { color: theme.text }]}>
          No entries yet this cycle
        </Text>
        <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
          Journal entries you write will appear here, organized by lunar day and gate.
        </Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={() => fetchTimeline(true)}
          tintColor={LUNAR_COLORS.moonlight}
        />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: LUNAR_COLORS.moonlight }]}>
          LUNAR CYCLE TIMELINE
        </Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          {timeline.cycle_start} → {timeline.cycle_end}
        </Text>
      </View>

      {/* Consideration Topic */}
      {considerationTopic && (
        <View style={[styles.topicSection, { borderColor: theme.border }]}>
          <Text style={[styles.topicLabel, { color: LUNAR_COLORS.silver }]}>
            OBSERVING
          </Text>
          <Text style={[styles.topicText, { color: theme.text }]}>
            "{considerationTopic}"
          </Text>
        </View>
      )}

      {/* Current Position Indicator */}
      <View style={[styles.currentPosition, { backgroundColor: LUNAR_COLORS.glow }]}>
        <Text style={[styles.currentPositionText, { color: LUNAR_COLORS.moonlight }]}>
          Currently Day {Math.round(timeline.current_lunar_day)} • {timeline.moon_phase}
        </Text>
        {timeline.is_near_new_moon && (
          <Text style={[styles.newMoonNote, { color: LUNAR_COLORS.silver }]}>
            {timeline.days_until_new_moon < 1 
              ? "Cycle completing"
              : `${Math.round(timeline.days_until_new_moon)} days to new moon`
            }
          </Text>
        )}
      </View>

      {/* Summary Stats */}
      <View style={[styles.stats, { borderColor: theme.border }]}>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: theme.text }]}>
            {timeline.total_entries}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textTertiary }]}>
            entries
          </Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: theme.text }]}>
            {timeline.timeline.length}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textTertiary }]}>
            days active
          </Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: theme.text }]}>
            {new Set(timeline.timeline.flatMap(d => d.gates)).size}
          </Text>
          <Text style={[styles.statLabel, { color: theme.textTertiary }]}>
            gates touched
          </Text>
        </View>
      </View>

      {/* Timeline Entries */}
      <View style={styles.timeline}>
        {timeline.timeline.map((day, index) => {
          const isExpanded = expandedDays.has(day.lunar_day);
          const isCurrentDay = Math.round(timeline.current_lunar_day) === day.lunar_day;
          
          return (
            <View key={day.lunar_day} style={styles.dayContainer}>
              {/* Timeline Line */}
              <View style={styles.timelineLineContainer}>
                <View 
                  style={[
                    styles.timelineDot,
                    { backgroundColor: isCurrentDay ? LUNAR_COLORS.moonlight : theme.textTertiary }
                  ]} 
                />
                {index < timeline.timeline.length - 1 && (
                  <View style={[styles.timelineLine, { backgroundColor: theme.border }]} />
                )}
              </View>

              {/* Day Card */}
              <TouchableOpacity
                style={[
                  styles.dayCard,
                  { 
                    backgroundColor: theme.surface, 
                    borderColor: isCurrentDay ? LUNAR_COLORS.moonlight + '40' : theme.border 
                  }
                ]}
                onPress={() => toggleDay(day.lunar_day)}
                activeOpacity={0.7}
              >
                <View style={styles.dayHeader}>
                  <View style={styles.dayInfo}>
                    <Text style={[styles.dayNumber, { color: LUNAR_COLORS.moonlight }]}>
                      Day {day.lunar_day}
                    </Text>
                    {day.gates.length > 0 && (
                      <Text style={[styles.dayGates, { color: theme.textSecondary }]}>
                        Gate {day.gates.join(', ')}
                      </Text>
                    )}
                  </View>
                  <View style={styles.dayMeta}>
                    <Text style={[styles.entryCount, { color: theme.textTertiary }]}>
                      {day.entry_count} {day.entry_count === 1 ? 'entry' : 'entries'}
                    </Text>
                    <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
                      {isExpanded ? '▲' : '▼'}
                    </Text>
                  </View>
                </View>

                {/* Expanded Entry List */}
                {isExpanded && (
                  <View style={[styles.entriesList, { borderTopColor: theme.border }]}>
                    {day.entries.map((entry) => (
                      <TouchableOpacity
                        key={entry.id}
                        style={[styles.entryItem, { borderBottomColor: theme.border }]}
                        onPress={() => onEntryPress?.(entry)}
                        activeOpacity={0.7}
                      >
                        <View style={styles.entryHeader}>
                          {entry.gate_title && (
                            <Text style={[styles.entryGate, { color: LUNAR_COLORS.silver }]}>
                              Gate {entry.moon_gate} — {entry.gate_title}
                            </Text>
                          )}
                          <Text style={[styles.entryTime, { color: theme.textTertiary }]}>
                            {formatDate(entry.created_at)}
                          </Text>
                        </View>
                        <Text style={[styles.entryContent, { color: theme.text }]}>
                          {truncateContent(entry.content, 150)}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}
              </TouchableOpacity>
            </View>
          );
        })}
      </View>

      {/* Near Cycle End Message */}
      {timeline.is_near_new_moon && (
        <View style={[styles.cycleEndSection, { backgroundColor: LUNAR_COLORS.glow, borderColor: LUNAR_COLORS.moonlight + '40' }]}>
          <Text style={[styles.cycleEndTitle, { color: LUNAR_COLORS.moonlight }]}>
            Cycle Completing
          </Text>
          <Text style={[styles.cycleEndText, { color: theme.textSecondary }]}>
            This lunar cycle appears to be completing. Take a moment to notice what has shifted in your perspective over these {timeline.timeline.length} days of observation.
          </Text>
        </View>
      )}
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
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 60,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '500',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 21,
  },
  header: {
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 13,
  },
  topicSection: {
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  topicLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1,
    marginBottom: 4,
  },
  topicText: {
    fontSize: 15,
    fontStyle: 'italic',
    lineHeight: 22,
  },
  currentPosition: {
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    alignItems: 'center',
  },
  currentPositionText: {
    fontSize: 14,
    fontWeight: '500',
  },
  newMoonNote: {
    fontSize: 12,
    marginTop: 4,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 8,
    padding: 12,
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '500',
  },
  statLabel: {
    fontSize: 11,
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    backgroundColor: 'rgba(192, 200, 212, 0.2)',
  },
  timeline: {
    gap: 0,
  },
  dayContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  timelineLineContainer: {
    width: 20,
    alignItems: 'center',
  },
  timelineDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginTop: 16,
  },
  timelineLine: {
    width: 2,
    flex: 1,
    marginVertical: 4,
  },
  dayCard: {
    flex: 1,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
    overflow: 'hidden',
  },
  dayHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
  },
  dayInfo: {
    gap: 4,
  },
  dayNumber: {
    fontSize: 15,
    fontWeight: '500',
  },
  dayGates: {
    fontSize: 12,
  },
  dayMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  entryCount: {
    fontSize: 12,
  },
  expandIcon: {
    fontSize: 10,
  },
  entriesList: {
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  entryItem: {
    padding: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  entryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  entryGate: {
    fontSize: 11,
    fontWeight: '500',
  },
  entryTime: {
    fontSize: 11,
  },
  entryContent: {
    fontSize: 14,
    lineHeight: 20,
  },
  cycleEndSection: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginTop: 20,
  },
  cycleEndTitle: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 8,
  },
  cycleEndText: {
    fontSize: 14,
    lineHeight: 21,
  },
});

export type { LunarEntry, CycleTimeline };
