/**
 * Pattern Graph Card v0.1
 * 
 * Lightweight visualization of the Mirror Pattern Graph.
 * Displays:
 * - Active domains with signal strength
 * - Strongest current signals
 * - Repeated tags
 * - Recent signal stream
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import Constants from 'expo-constants';

// =============================================================================
// TYPES
// =============================================================================

interface DomainSummary {
  domain: string;
  domain_label: string;
  signal_count: number;
  dominant_signals: string[];
  dominant_tags: string[];
  average_intensity: number;
  polarity_breakdown: Record<string, number>;
}

interface SignalSummary {
  signal_type: string;
  domain: string;
  intensity: number;
  polarity: string;
  source_type: string;
  tags?: string[];
  preview?: string;
  gate?: number;
  timestamp?: string;
}

interface PatternGraphData {
  success: boolean;
  user_id: string;
  generated_at: string;
  total_signals: number;
  active_domains: DomainSummary[];
  strongest_signals: SignalSummary[];
  recent_signals: SignalSummary[];
  source_breakdown: Record<string, number>;
  repeated_tags: string[];
  overall_momentum: string;
  data_sufficiency: string;
  message?: string;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const PATTERN_COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  positive: '#81C784',
  negative: '#EF9A9A',
  mixed: '#FFB74D',
  neutral: '#90A4AE',
  cardBg: 'rgba(192, 200, 212, 0.06)',
};

const SIGNAL_ICONS: Record<string, string> = {
  excitement: '✨',
  hesitation: '🌀',
  clarity: '💡',
  confusion: '❓',
  desire: '💫',
  avoidance: '🚫',
  confidence: '💪',
  doubt: '🤔',
  expansion: '🌱',
  contraction: '🔒',
};

const MOMENTUM_LABELS: Record<string, { label: string; color: string }> = {
  positive: { label: 'Positive Momentum', color: PATTERN_COLORS.positive },
  resistant: { label: 'Resistant', color: PATTERN_COLORS.negative },
  mixed: { label: 'Mixed Signals', color: PATTERN_COLORS.mixed },
  unclear: { label: 'Emerging', color: PATTERN_COLORS.neutral },
};

// =============================================================================
// COMPONENT
// =============================================================================

interface PatternGraphCardProps {
  showDebug?: boolean;
}

export default function PatternGraphCard({ showDebug = false }: PatternGraphCardProps) {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const [data, setData] = useState<PatternGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  // Get backend URL
  const getBackendUrl = () => {
    const backendUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL 
      || process.env.EXPO_PUBLIC_BACKEND_URL 
      || '';
    return backendUrl;
  };

  // Fetch pattern graph data
  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id) return;

      try {
        setLoading(true);
        const baseUrl = getBackendUrl();
        const url = `${baseUrl}/api/pattern-engine/graph/${user.id}${showDebug ? '?include_debug=true' : ''}`;
        
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to fetch pattern graph: ${response.status}`);
        }
        
        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        console.error('[PatternGraphCard] Error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load pattern graph');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user?.id]);

  // ==========================================================================
  // RENDER HELPERS
  // ==========================================================================

  const renderDomainCard = (domain: DomainSummary) => {
    const strengthPercent = Math.min(domain.average_intensity * 100, 100);
    const positiveCount = domain.polarity_breakdown['positive'] || 0;
    const negativeCount = domain.polarity_breakdown['negative'] || 0;
    const totalCount = domain.signal_count;
    
    // Determine primary color based on polarity
    let barColor = PATTERN_COLORS.neutral;
    if (positiveCount > negativeCount) barColor = PATTERN_COLORS.positive;
    else if (negativeCount > positiveCount) barColor = PATTERN_COLORS.negative;
    else if (positiveCount > 0 && negativeCount > 0) barColor = PATTERN_COLORS.mixed;

    return (
      <View 
        key={domain.domain}
        style={[styles.domainCard, { backgroundColor: PATTERN_COLORS.cardBg, borderColor: theme.border }]}
      >
        <View style={styles.domainHeader}>
          <Text style={[styles.domainLabel, { color: theme.text }]}>
            {domain.domain_label}
          </Text>
          <Text style={[styles.domainCount, { color: theme.textTertiary }]}>
            {domain.signal_count} signals
          </Text>
        </View>
        
        {/* Strength Bar */}
        <View style={[styles.strengthBarBg, { backgroundColor: 'rgba(168, 178, 192, 0.2)' }]}>
          <View 
            style={[
              styles.strengthBarFill, 
              { 
                width: `${Math.max(strengthPercent, 5)}%`,
                backgroundColor: barColor,
              }
            ]} 
          />
        </View>
        
        {/* Dominant Signals */}
        {domain.dominant_signals.length > 0 && (
          <View style={styles.signalChips}>
            {domain.dominant_signals.slice(0, 2).map((signal, idx) => (
              <View key={idx} style={[styles.signalChip, { backgroundColor: 'rgba(192, 200, 212, 0.15)' }]}>
                <Text style={styles.signalChipIcon}>{SIGNAL_ICONS[signal] || '•'}</Text>
                <Text style={[styles.signalChipText, { color: theme.textSecondary }]}>
                  {signal}
                </Text>
              </View>
            ))}
          </View>
        )}
        
        {/* Dominant Tags */}
        {domain.dominant_tags.length > 0 && (
          <View style={styles.tagRow}>
            {domain.dominant_tags.slice(0, 3).map((tag, idx) => (
              <Text key={idx} style={[styles.tagText, { color: theme.textTertiary }]}>
                #{tag.replace(/_/g, ' ')}
              </Text>
            ))}
          </View>
        )}
      </View>
    );
  };

  const renderSignalItem = (signal: SignalSummary, index: number) => {
    const icon = SIGNAL_ICONS[signal.signal_type] || '•';
    const polarityColor = signal.polarity === 'positive' 
      ? PATTERN_COLORS.positive 
      : signal.polarity === 'negative' 
        ? PATTERN_COLORS.negative 
        : PATTERN_COLORS.neutral;

    return (
      <View 
        key={index}
        style={[styles.signalItem, { borderLeftColor: polarityColor }]}
      >
        <View style={styles.signalItemHeader}>
          <Text style={styles.signalItemIcon}>{icon}</Text>
          <Text style={[styles.signalItemType, { color: theme.text }]}>
            {signal.signal_type}
          </Text>
          {signal.gate && (
            <Text style={[styles.signalItemGate, { color: theme.textTertiary }]}>
              Gate {signal.gate}
            </Text>
          )}
        </View>
        {signal.preview && (
          <Text style={[styles.signalItemPreview, { color: theme.textSecondary }]} numberOfLines={2}>
            "{signal.preview}"
          </Text>
        )}
      </View>
    );
  };

  // ==========================================================================
  // MAIN RENDER
  // ==========================================================================

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <ActivityIndicator size="small" color={PATTERN_COLORS.moonlight} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
          Loading Pattern Graph...
        </Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.errorText, { color: theme.textTertiary }]}>
          {error || 'No pattern data available'}
        </Text>
      </View>
    );
  }

  if (data.total_signals === 0) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.headerLabel, { color: PATTERN_COLORS.silver }]}>
          PATTERN GRAPH
        </Text>
        <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
          {data.message || 'No pattern signals yet. Start by adding reflections to your Lunar Decision Journal.'}
        </Text>
      </View>
    );
  }

  const momentumInfo = MOMENTUM_LABELS[data.overall_momentum] || MOMENTUM_LABELS.unclear;

  // v0.15: Calculate source labels for display
  const sourceLabels: Record<string, string> = {
    lunar_reflection: 'Lunar',
    journal_entry: 'Journal',
    mirror_chat: 'Chat',
    human_design_gate: 'HD',
    enneagram: 'Enneagram',
    gene_keys: 'Gene Keys',
    transit: 'Transit',
  };

  const activeSourceCount = Object.values(data.source_breakdown).filter(v => v > 0).length;

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={[styles.headerLabel, { color: PATTERN_COLORS.silver }]}>
            PATTERN GRAPH
          </Text>
          <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]}>
            v0.15 • {data.total_signals} signals • {activeSourceCount} source{activeSourceCount !== 1 ? 's' : ''}
          </Text>
        </View>
        <View style={[styles.momentumBadge, { backgroundColor: momentumInfo.color + '20' }]}>
          <Text style={[styles.momentumText, { color: momentumInfo.color }]}>
            {momentumInfo.label}
          </Text>
        </View>
      </View>

      {/* v0.15: Source Breakdown Row */}
      <View style={styles.sourceRow}>
        {Object.entries(data.source_breakdown).map(([source, count]) => (
          count > 0 && (
            <View key={source} style={[styles.sourceChip, { backgroundColor: PATTERN_COLORS.cardBg }]}>
              <Text style={[styles.sourceChipText, { color: theme.textSecondary }]}>
                {sourceLabels[source] || source}: {count}
              </Text>
            </View>
          )
        ))}
        {/* Show stub sources with 0 count */}
        {Object.values(data.source_breakdown).every(v => v === 0 || data.source_breakdown['lunar_reflection'] === data.total_signals) && (
          <Text style={[styles.stubNote, { color: theme.textTertiary }]}>
            More sources coming soon
          </Text>
        )}
      </View>

      {/* Data Sufficiency Badge (v0.15) */}
      {data.data_sufficiency !== 'high' && (
        <View style={[styles.sufficiencyBadge, { 
          backgroundColor: data.data_sufficiency === 'insufficient' ? 'rgba(239, 154, 154, 0.15)' : 'rgba(255, 183, 77, 0.15)'
        }]}>
          <Text style={[styles.sufficiencyText, { 
            color: data.data_sufficiency === 'insufficient' ? '#EF9A9A' : '#FFB74D' 
          }]}>
            {data.data_sufficiency === 'insufficient' ? '⚠️ Limited data' : 
             data.data_sufficiency === 'low' ? '📊 Building pattern baseline' : 
             '📈 Good data foundation'}
          </Text>
        </View>
      )}

      {/* Active Domains Section */}
      <View style={styles.section}>
        <Text style={[styles.sectionLabel, { color: PATTERN_COLORS.silver }]}>
          ACTIVE DOMAINS
        </Text>
        {data.active_domains.slice(0, expanded ? undefined : 3).map(renderDomainCard)}
      </View>

      {/* Strongest Signals */}
      {data.strongest_signals.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: PATTERN_COLORS.silver }]}>
            STRONGEST SIGNALS
          </Text>
          {data.strongest_signals.slice(0, expanded ? 5 : 3).map(renderSignalItem)}
        </View>
      )}

      {/* Repeated Tags */}
      {data.repeated_tags.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: PATTERN_COLORS.silver }]}>
            REPEATED THEMES
          </Text>
          <View style={styles.tagsContainer}>
            {data.repeated_tags.slice(0, expanded ? undefined : 5).map((tag, idx) => (
              <View key={idx} style={[styles.tagBadge, { backgroundColor: PATTERN_COLORS.cardBg }]}>
                <Text style={[styles.tagBadgeText, { color: theme.textSecondary }]}>
                  {tag.replace(/_/g, ' ')}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Recent Signal Stream (expanded only) */}
      {expanded && data.recent_signals.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionLabel, { color: PATTERN_COLORS.silver }]}>
            RECENT SIGNALS
          </Text>
          {data.recent_signals.slice(0, 5).map((signal, idx) => (
            <View key={idx} style={styles.recentSignal}>
              <Text style={[styles.recentSignalIcon]}>
                {SIGNAL_ICONS[signal.signal_type] || '•'}
              </Text>
              <Text style={[styles.recentSignalText, { color: theme.textSecondary }]}>
                {signal.source_type.replace(/_/g, ' ')} • Gate {signal.gate || '—'} • {signal.signal_type}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Expand/Collapse Button */}
      {(data.active_domains.length > 3 || data.strongest_signals.length > 3) && (
        <TouchableOpacity
          style={styles.expandButton}
          onPress={() => setExpanded(!expanded)}
        >
          <Text style={[styles.expandButtonText, { color: PATTERN_COLORS.moonlight }]}>
            {expanded ? 'Show Less' : 'Show More'}
          </Text>
        </TouchableOpacity>
      )}

      {/* Data Sufficiency Indicator */}
      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: theme.textTertiary }]}>
          Data sufficiency: {data.data_sufficiency}
        </Text>
      </View>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginBottom: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
  },
  headerLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  headerSubtitle: {
    fontSize: 12,
    marginTop: 4,
  },
  momentumBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  momentumText: {
    fontSize: 11,
    fontWeight: '600',
  },
  section: {
    marginBottom: 20,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
  },
  // Domain Cards
  domainCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 10,
  },
  domainHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  domainLabel: {
    fontSize: 14,
    fontWeight: '600',
  },
  domainCount: {
    fontSize: 12,
  },
  strengthBarBg: {
    height: 6,
    borderRadius: 3,
    marginBottom: 10,
  },
  strengthBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  signalChips: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  signalChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 10,
    gap: 4,
  },
  signalChipIcon: {
    fontSize: 12,
  },
  signalChipText: {
    fontSize: 11,
    textTransform: 'capitalize',
  },
  tagRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tagText: {
    fontSize: 11,
  },
  // Signal Items
  signalItem: {
    borderLeftWidth: 3,
    paddingLeft: 12,
    paddingVertical: 8,
    marginBottom: 8,
  },
  signalItemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  signalItemIcon: {
    fontSize: 14,
  },
  signalItemType: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  signalItemGate: {
    fontSize: 11,
    marginLeft: 'auto',
  },
  signalItemPreview: {
    fontSize: 12,
    lineHeight: 18,
    marginTop: 4,
    fontStyle: 'italic',
  },
  // Tags
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tagBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  tagBadgeText: {
    fontSize: 12,
  },
  // Recent Signals
  recentSignal: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 6,
  },
  recentSignalIcon: {
    fontSize: 14,
  },
  recentSignalText: {
    fontSize: 12,
  },
  // Footer
  expandButton: {
    alignItems: 'center',
    paddingVertical: 10,
  },
  expandButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(168, 178, 192, 0.2)',
  },
  footerText: {
    fontSize: 11,
  },
  // Loading/Error
  loadingText: {
    textAlign: 'center',
    marginTop: 10,
    fontSize: 13,
  },
  errorText: {
    textAlign: 'center',
    fontSize: 13,
  },
  emptyText: {
    textAlign: 'center',
    fontSize: 13,
    marginTop: 10,
    lineHeight: 20,
  },
});

export type { PatternGraphData, DomainSummary, SignalSummary };
