/**
 * Lifeline Imported Sources Screen
 * 
 * Shows all import sources for the user's lifeline.
 * Displays file name, type, import date, and stats.
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
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import api from '../services/api';

interface ImportSource {
  id: string;
  source_type: string;
  file_name: string;
  uploaded_at: string;
  imported_at?: string;
  status: string;
  raw_event_count: number;
  candidate_event_count: number;
  canonical_match_count: number;
  duplicate_count: number;
}

interface IngestionStats {
  import_sources: number;
  imported_moments: {
    total: number;
    by_status: Record<string, number>;
  };
  canonical_events: number;
  events_with_source_tracking: number;
  potential_duplicate_groups: number;
  potential_duplicate_events: number;
}

const SOURCE_TYPE_CONFIG: Record<string, { icon: keyof typeof Ionicons.glyphMap; label: string; color: string }> = {
  spreadsheet: { icon: 'document-text', label: 'Spreadsheet', color: '#22C55E' },
  csv: { icon: 'document-text', label: 'CSV', color: '#22C55E' },
  pptx: { icon: 'easel', label: 'PowerPoint', color: '#F97316' },
  pdf: { icon: 'document', label: 'PDF', color: '#EF4444' },
  image: { icon: 'image', label: 'Image', color: '#8B5CF6' },
  manual: { icon: 'create', label: 'Manual', color: '#3B82F6' },
};

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  uploaded: { label: 'Uploaded', color: '#A3A3A3' },
  parsed: { label: 'Ready for review', color: '#F59E0B' },
  reviewed: { label: 'Reviewed', color: '#3B82F6' },
  merged: { label: 'Merged', color: '#22C55E' },
  failed: { label: 'Failed', color: '#EF4444' },
};

export default function LifelineImportedSourcesScreen() {
  const { user } = useAppStore();
  const { theme, isDark } = useTheme();
  const router = useRouter();
  
  const [sources, setSources] = useState<ImportSource[]>([]);
  const [stats, setStats] = useState<IngestionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async (isRefresh = false) => {
    if (!user?.id) return;
    
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const [sourcesResponse, statsResponse] = await Promise.all([
        api.get(`/lifeline/import-sources/${user.id}`),
        api.get(`/lifeline/ingestion-stats/${user.id}`),
      ]);

      if (sourcesResponse.data.success) {
        setSources(sourcesResponse.data.sources || []);
      }
      if (statsResponse.data.success) {
        setStats(statsResponse.data);
      }
    } catch (err: any) {
      console.error('[ImportedSources] Error loading data:', err);
      setError('Failed to load import sources');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getSourceConfig = (type: string) => {
    return SOURCE_TYPE_CONFIG[type] || SOURCE_TYPE_CONFIG.manual;
  };

  const getStatusConfig = (status: string) => {
    return STATUS_CONFIG[status] || STATUS_CONFIG.uploaded;
  };

  const renderSourceCard = (source: ImportSource) => {
    const sourceConfig = getSourceConfig(source.source_type);
    const statusConfig = getStatusConfig(source.status);

    return (
      <View
        key={source.id}
        style={[styles.sourceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        <View style={styles.sourceHeader}>
          <View style={[styles.sourceIcon, { backgroundColor: sourceConfig.color + '20' }]}>
            <Ionicons name={sourceConfig.icon} size={20} color={sourceConfig.color} />
          </View>
          <View style={styles.sourceInfo}>
            <Text style={[styles.fileName, { color: theme.text }]} numberOfLines={1}>
              {source.file_name}
            </Text>
            <Text style={[styles.sourceType, { color: theme.textSecondary }]}>
              {sourceConfig.label} • {formatDate(source.uploaded_at)}
            </Text>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: statusConfig.color + '20' }]}>
            <Text style={[styles.statusText, { color: statusConfig.color }]}>
              {statusConfig.label}
            </Text>
          </View>
        </View>

        <View style={[styles.sourceStats, { borderTopColor: theme.border }]}>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.text }]}>
              {source.candidate_event_count || source.raw_event_count}
            </Text>
            <Text style={[styles.statLabel, { color: theme.textTertiary }]}>parsed</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.text }]}>
              {source.canonical_match_count}
            </Text>
            <Text style={[styles.statLabel, { color: theme.textTertiary }]}>canonical</Text>
          </View>
          {source.duplicate_count > 0 && (
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: '#F59E0B' }]}>
                {source.duplicate_count}
              </Text>
              <Text style={[styles.statLabel, { color: theme.textTertiary }]}>overlaps</Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <View style={[styles.emptyIcon, { backgroundColor: theme.surface }]}>
        <Ionicons name="layers-outline" size={48} color={theme.textTertiary} />
      </View>
      <Text style={[styles.emptyTitle, { color: theme.text }]}>
        No imported sources yet
      </Text>
      <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
        Import spreadsheets or PowerPoint decks to build your Lifeline from multiple sources.
      </Text>
      <TouchableOpacity
        style={[styles.importButton, { backgroundColor: theme.accent }]}
        onPress={() => router.push('/lifeline-upload')}
      >
        <Ionicons name="add" size={18} color="#FFFFFF" />
        <Text style={styles.importButtonText}>Import Source</Text>
      </TouchableOpacity>
    </View>
  );

  const renderStats = () => {
    if (!stats) return null;

    return (
      <View style={[styles.statsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.statsTitle, { color: theme.text }]}>Overall Statistics</Text>
        <View style={styles.statsGrid}>
          <View style={styles.statsItem}>
            <Text style={[styles.statsValue, { color: theme.accent }]}>
              {stats.canonical_events}
            </Text>
            <Text style={[styles.statsLabel, { color: theme.textSecondary }]}>
              Timeline Events
            </Text>
          </View>
          <View style={styles.statsItem}>
            <Text style={[styles.statsValue, { color: theme.text }]}>
              {stats.import_sources}
            </Text>
            <Text style={[styles.statsLabel, { color: theme.textSecondary }]}>
              Sources
            </Text>
          </View>
          <View style={styles.statsItem}>
            <Text style={[styles.statsValue, { color: theme.text }]}>
              {stats.imported_moments.total}
            </Text>
            <Text style={[styles.statsLabel, { color: theme.textSecondary }]}>
              Imported
            </Text>
          </View>
          {stats.potential_duplicate_groups > 0 && (
            <View style={styles.statsItem}>
              <Text style={[styles.statsValue, { color: '#F59E0B' }]}>
                {stats.potential_duplicate_groups}
              </Text>
              <Text style={[styles.statsLabel, { color: theme.textSecondary }]}>
                To Review
              </Text>
            </View>
          )}
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading import sources...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
        >
          <Ionicons name="arrow-back" size={24} color={theme.text} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Imported Sources</Text>
          <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
            {sources.length} source{sources.length !== 1 ? 's' : ''}
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.addSourceButton, { backgroundColor: theme.accent }]}
          onPress={() => router.push('/lifeline-upload')}
        >
          <Ionicons name="add" size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => loadData(true)}
            tintColor={theme.textTertiary}
          />
        }
      >
        {error && (
          <View style={[styles.errorCard, { backgroundColor: '#FEE2E2', borderColor: '#FECACA' }]}>
            <Ionicons name="alert-circle" size={20} color="#DC2626" />
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {renderStats()}

        {sources.length === 0 ? (
          renderEmptyState()
        ) : (
          <View style={styles.sourcesSection}>
            <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
              Import History
            </Text>
            {sources.map(renderSourceCard)}
          </View>
        )}

        {/* Help text */}
        <View style={styles.helpSection}>
          <Ionicons name="information-circle-outline" size={16} color={theme.textTertiary} />
          <Text style={[styles.helpText, { color: theme.textTertiary }]}>
            Imported sources are merged into your Lifeline. Overlapping events are automatically detected and deduplicated.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: -8,
  },
  headerContent: {
    flex: 1,
    marginLeft: 4,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '600',
    letterSpacing: -0.3,
  },
  headerSubtitle: {
    fontSize: 13,
    marginTop: 2,
  },
  addSourceButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  errorCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 12,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 16,
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: '#DC2626',
  },
  statsCard: {
    padding: 16,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 20,
  },
  statsTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  statsItem: {
    flex: 1,
    minWidth: 70,
    alignItems: 'center',
  },
  statsValue: {
    fontSize: 24,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  statsLabel: {
    fontSize: 12,
    marginTop: 2,
  },
  sourcesSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  sourceCard: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
    overflow: 'hidden',
  },
  sourceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    gap: 12,
  },
  sourceIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sourceInfo: {
    flex: 1,
  },
  fileName: {
    fontSize: 15,
    fontWeight: '500',
  },
  sourceType: {
    fontSize: 13,
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
  },
  sourceStats: {
    flexDirection: 'row',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 20,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 4,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  statLabel: {
    fontSize: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
    paddingHorizontal: 20,
  },
  emptyIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  importButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
  },
  importButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  helpSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    padding: 12,
    marginTop: 8,
  },
  helpText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
});
