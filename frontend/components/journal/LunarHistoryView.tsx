/**
 * Lunar History View - Task 51
 * 
 * Shows archived lunar considerations and their entries.
 * Allows Reflectors to browse past decision cycles.
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
  Modal,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface ArchivedCycle {
  id: string;
  topic: string;
  cycle_start: string;
  cycle_end: string;
  created_at: string;
  closed_at: string;
  final_reflection: string | null;
  entry_count: number;
  gates_touched: number[];
}

interface CycleDetail {
  id: string;
  topic: string;
  status: string;
  cycle_start: string;
  cycle_end: string;
  created_at: string;
  closed_at: string;
  final_reflection: string | null;
  entries: any[];
  entry_count: number;
  gates_touched: number[];
}

interface LunarHistoryViewProps {
  userId: string;
  onCycleSelect?: (cycle: ArchivedCycle) => void;
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

export default function LunarHistoryView({
  userId,
  onCycleSelect,
}: LunarHistoryViewProps) {
  const { theme } = useTheme();
  const [history, setHistory] = useState<ArchivedCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  // Detail modal state
  const [selectedCycle, setSelectedCycle] = useState<CycleDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  const fetchHistory = useCallback(async (showRefresh = false) => {
    if (!userId) return;
    
    if (showRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    
    try {
      const response = await api.get(`/lunar-journal/${userId}/history`);
      
      if (response.data?.success) {
        setHistory(response.data.history || []);
      }
    } catch (err) {
      console.error('[LunarHistory] Error:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const fetchCycleDetail = async (cycleId: string) => {
    setLoadingDetail(true);
    setDetailModalVisible(true);
    
    try {
      const response = await api.get(`/lunar-journal/${userId}/history/${cycleId}`);
      
      if (response.data?.success) {
        setSelectedCycle(response.data);
      }
    } catch (err) {
      console.error('[LunarHistory] Error fetching detail:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const formatDateRange = (start: string, end: string) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    
    const formatOpts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
    return `${startDate.toLocaleDateString('en-US', formatOpts)} – ${endDate.toLocaleDateString('en-US', formatOpts)}`;
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
          Loading history...
        </Text>
      </View>
    );
  }

  if (history.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyIcon}>📜</Text>
        <Text style={[styles.emptyTitle, { color: theme.text }]}>
          No completed cycles yet
        </Text>
        <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
          When you complete a lunar cycle observation, it will be archived here for future reference.
        </Text>
      </View>
    );
  }

  return (
    <>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchHistory(true)}
            tintColor={LUNAR_COLORS.moonlight}
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.headerTitle, { color: LUNAR_COLORS.moonlight }]}>
            LUNAR DECISION HISTORY
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            {history.length} completed {history.length === 1 ? 'cycle' : 'cycles'}
          </Text>
        </View>

        {/* Cycle List */}
        <View style={styles.cycleList}>
          {history.map((cycle) => (
            <TouchableOpacity
              key={cycle.id}
              style={[styles.cycleCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => fetchCycleDetail(cycle.id)}
              activeOpacity={0.7}
            >
              <View style={styles.cycleHeader}>
                <Text style={[styles.cycleTopic, { color: theme.text }]}>
                  "{truncateContent(cycle.topic, 50)}"
                </Text>
                <Text style={[styles.cycleDates, { color: theme.textTertiary }]}>
                  {cycle.cycle_start ? formatDateRange(cycle.cycle_start, cycle.cycle_end || cycle.closed_at) : ''}
                </Text>
              </View>

              <View style={styles.cycleStats}>
                <View style={styles.statBadge}>
                  <Text style={[styles.statBadgeText, { color: LUNAR_COLORS.silver }]}>
                    {cycle.entry_count} entries
                  </Text>
                </View>
                {cycle.gates_touched.length > 0 && (
                  <View style={styles.statBadge}>
                    <Text style={[styles.statBadgeText, { color: LUNAR_COLORS.silver }]}>
                      {cycle.gates_touched.length} gates
                    </Text>
                  </View>
                )}
              </View>

              {cycle.final_reflection && (
                <View style={[styles.finalReflection, { borderTopColor: theme.border }]}>
                  <Text style={[styles.finalReflectionLabel, { color: LUNAR_COLORS.silver }]}>
                    FINAL REFLECTION
                  </Text>
                  <Text style={[styles.finalReflectionText, { color: theme.textSecondary }]}>
                    {truncateContent(cycle.final_reflection, 100)}
                  </Text>
                </View>
              )}

              <Text style={[styles.viewMore, { color: LUNAR_COLORS.moonlight }]}>
                View full cycle →
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* Detail Modal */}
      <Modal
        visible={detailModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setDetailModalVisible(false)}
      >
        <View style={[styles.modalOverlay, { backgroundColor: 'rgba(0,0,0,0.7)' }]}>
          <View style={[styles.modalContent, { backgroundColor: theme.background }]}>
            {loadingDetail ? (
              <View style={styles.modalLoading}>
                <ActivityIndicator size="large" color={LUNAR_COLORS.moonlight} />
              </View>
            ) : selectedCycle ? (
              <ScrollView 
                style={styles.modalScroll}
                showsVerticalScrollIndicator={false}
              >
                {/* Modal Header */}
                <View style={styles.modalHeader}>
                  <TouchableOpacity
                    style={styles.closeButton}
                    onPress={() => setDetailModalVisible(false)}
                  >
                    <Text style={[styles.closeButtonText, { color: theme.textSecondary }]}>
                      ← Back
                    </Text>
                  </TouchableOpacity>
                  <Text style={[styles.modalTitle, { color: LUNAR_COLORS.moonlight }]}>
                    CYCLE DETAIL
                  </Text>
                </View>

                {/* Topic */}
                <View style={[styles.modalSection, { borderBottomColor: theme.border }]}>
                  <Text style={[styles.modalLabel, { color: LUNAR_COLORS.silver }]}>
                    CONSIDERATION
                  </Text>
                  <Text style={[styles.modalTopic, { color: theme.text }]}>
                    "{selectedCycle.topic}"
                  </Text>
                  {selectedCycle.cycle_start && (
                    <Text style={[styles.modalDates, { color: theme.textTertiary }]}>
                      {formatDateRange(selectedCycle.cycle_start, selectedCycle.cycle_end || selectedCycle.closed_at)}
                    </Text>
                  )}
                </View>

                {/* Stats */}
                <View style={[styles.modalStats, { borderBottomColor: theme.border }]}>
                  <View style={styles.modalStatItem}>
                    <Text style={[styles.modalStatValue, { color: theme.text }]}>
                      {selectedCycle.entry_count}
                    </Text>
                    <Text style={[styles.modalStatLabel, { color: theme.textTertiary }]}>
                      entries
                    </Text>
                  </View>
                  <View style={styles.modalStatItem}>
                    <Text style={[styles.modalStatValue, { color: theme.text }]}>
                      {selectedCycle.gates_touched.length}
                    </Text>
                    <Text style={[styles.modalStatLabel, { color: theme.textTertiary }]}>
                      gates touched
                    </Text>
                  </View>
                </View>

                {/* Final Reflection */}
                {selectedCycle.final_reflection && (
                  <View style={[styles.modalSection, { borderBottomColor: theme.border }]}>
                    <Text style={[styles.modalLabel, { color: LUNAR_COLORS.silver }]}>
                      FINAL REFLECTION
                    </Text>
                    <Text style={[styles.modalReflection, { color: theme.text }]}>
                      {selectedCycle.final_reflection}
                    </Text>
                  </View>
                )}

                {/* Entries */}
                <View style={styles.modalSection}>
                  <Text style={[styles.modalLabel, { color: LUNAR_COLORS.silver }]}>
                    ENTRIES ({selectedCycle.entries.length})
                  </Text>
                  {selectedCycle.entries.map((entry, index) => (
                    <View 
                      key={entry.id}
                      style={[
                        styles.entryCard,
                        { backgroundColor: theme.surface, borderColor: theme.border }
                      ]}
                    >
                      <View style={styles.entryHeader}>
                        <Text style={[styles.entryDay, { color: LUNAR_COLORS.moonlight }]}>
                          Day {Math.round(entry.lunar_day)}
                        </Text>
                        {entry.gate_title && (
                          <Text style={[styles.entryGate, { color: theme.textTertiary }]}>
                            Gate {entry.moon_gate} — {entry.gate_title}
                          </Text>
                        )}
                      </View>
                      <Text style={[styles.entryContent, { color: theme.text }]}>
                        {entry.content}
                      </Text>
                    </View>
                  ))}
                </View>
              </ScrollView>
            ) : null}
          </View>
        </View>
      </Modal>
    </>
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
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 21,
  },
  header: {
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 13,
  },
  cycleList: {
    gap: 12,
  },
  cycleCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  cycleHeader: {
    marginBottom: 10,
  },
  cycleTopic: {
    fontSize: 16,
    fontWeight: '500',
    fontStyle: 'italic',
    marginBottom: 4,
    lineHeight: 22,
  },
  cycleDates: {
    fontSize: 12,
  },
  cycleStats: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 10,
  },
  statBadge: {
    backgroundColor: 'rgba(192, 200, 212, 0.1)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statBadgeText: {
    fontSize: 11,
    fontWeight: '500',
  },
  finalReflection: {
    paddingTop: 10,
    marginTop: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  finalReflectionLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  finalReflectionText: {
    fontSize: 13,
    lineHeight: 19,
  },
  viewMore: {
    fontSize: 13,
    fontWeight: '500',
    marginTop: 10,
    textAlign: 'right',
  },
  // Modal Styles
  modalOverlay: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  modalContent: {
    maxHeight: '90%',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
  },
  modalLoading: {
    padding: 60,
    alignItems: 'center',
  },
  modalScroll: {
    padding: 20,
  },
  modalHeader: {
    marginBottom: 20,
  },
  closeButton: {
    paddingVertical: 8,
  },
  closeButtonText: {
    fontSize: 15,
  },
  modalTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    marginTop: 8,
  },
  modalSection: {
    paddingBottom: 16,
    marginBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  modalLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 8,
  },
  modalTopic: {
    fontSize: 22,
    fontWeight: '500',
    fontStyle: 'italic',
    lineHeight: 30,
    marginBottom: 4,
  },
  modalDates: {
    fontSize: 13,
  },
  modalStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 16,
    marginBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  modalStatItem: {
    alignItems: 'center',
  },
  modalStatValue: {
    fontSize: 24,
    fontWeight: '600',
  },
  modalStatLabel: {
    fontSize: 12,
    marginTop: 2,
  },
  modalReflection: {
    fontSize: 15,
    lineHeight: 23,
  },
  entryCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    marginTop: 10,
  },
  entryHeader: {
    marginBottom: 8,
  },
  entryDay: {
    fontSize: 13,
    fontWeight: '600',
  },
  entryGate: {
    fontSize: 11,
    marginTop: 2,
  },
  entryContent: {
    fontSize: 14,
    lineHeight: 21,
  },
});

export type { ArchivedCycle, CycleDetail };
