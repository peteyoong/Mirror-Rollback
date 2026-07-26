/**
 * Pattern Graph Card v0.15
 * 
 * Summary-first visualization with progressive disclosure.
 * Shows compact overview by default, details on expand.
 * 
 * Design principles:
 * - Summary first, evidence second, debug third
 * - Collapsed sections by default
 * - Insight over raw data
 * - Product feel, not analytics dump
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import Constants from 'expo-constants';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

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
  debug?: any;
}

type AccordionSection = 'domains' | 'signals' | 'themes' | 'sources' | null;

// =============================================================================
// CONSTANTS
// =============================================================================

const COLORS = {
  moonlight: '#C0C8D4',
  silver: '#A8B2C0',
  positive: '#81C784',
  negative: '#EF9A9A',
  mixed: '#FFB74D',
  neutral: '#90A4AE',
  cardBg: 'rgba(192, 200, 212, 0.06)',
  border: 'rgba(168, 178, 192, 0.15)',
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

const MOMENTUM_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  positive: { label: 'Positive', color: COLORS.positive, icon: '↗' },
  strong_positive: { label: 'Strong Positive', color: COLORS.positive, icon: '⬆' },
  resistant: { label: 'Resistant', color: COLORS.negative, icon: '↘' },
  mixed: { label: 'Mixed', color: COLORS.mixed, icon: '↔' },
  unclear: { label: 'Emerging', color: COLORS.neutral, icon: '○' },
};

const SOURCE_LABELS: Record<string, string> = {
  lunar_reflection: 'Lunar',
  journal_entry: 'Journal',
  mirror_chat: 'Chat',
  human_design_gate: 'HD',
  enneagram: 'Enneagram',
  gene_keys: 'Gene Keys',
  transit: 'Transit',
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
  const [expandedSection, setExpandedSection] = useState<AccordionSection>(null);
  const [showMoreSignals, setShowMoreSignals] = useState(false);

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id) return;
      try {
        setLoading(true);
        const baseUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL 
          || process.env.EXPO_PUBLIC_BACKEND_URL || '';
        const url = `${baseUrl}/api/pattern-engine/graph/${user.id}${showDebug ? '?include_debug=true' : ''}`;
        
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Failed to fetch: ${response.status}`);
        
        const result = await response.json();
        setData(result);
        setError(null);
      } catch (err) {
        console.error('[PatternGraphCard] Error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [user?.id, showDebug]);

  // Toggle accordion section (only one open at a time)
  const toggleSection = (section: AccordionSection) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedSection(expandedSection === section ? null : section);
  };

  // ==========================================================================
  // RENDER: LOADING / ERROR / EMPTY STATES
  // ==========================================================================

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <ActivityIndicator size="small" color={COLORS.moonlight} />
        <Text style={[styles.loadingText, { color: theme.textTertiary }]}>Gathering your patterns...</Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.emptyText, { color: theme.textTertiary }]}>{error || 'Unable to load patterns'}</Text>
      </View>
    );
  }

  if (data.total_signals === 0) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.emptyTitle, { color: theme.text }]}>Your Patterns Dashboard</Text>
        
        <View style={styles.emptyStateContent}>
          <Text style={[styles.emptyDescription, { color: theme.textSecondary }]}>
            Pattern signals begin to appear when you add moments, reflections, or decision observations. Mirror looks for repeated themes across your life and journal.
          </Text>
          
          <View style={styles.emptyStateActions}>
            <Text style={[styles.emptyActionsTitle, { color: theme.textTertiary }]}>
              To see patterns emerge:
            </Text>
            <View style={styles.emptyActionsList}>
              <Text style={[styles.emptyActionItem, { color: theme.textSecondary }]}>
                • Add a moment to your Lifeline
              </Text>
              <Text style={[styles.emptyActionItem, { color: theme.textSecondary }]}>
                • Write a journal reflection
              </Text>
              <Text style={[styles.emptyActionItem, { color: theme.textSecondary }]}>
                • Continue a lunar decision cycle
              </Text>
            </View>
          </View>
        </View>
      </View>
    );
  }

  // ==========================================================================
  // COMPUTED VALUES
  // ==========================================================================

  const momentum = MOMENTUM_CONFIG[data.overall_momentum] || MOMENTUM_CONFIG.unclear;
  const topDomains = data.active_domains.slice(0, 3);
  const topThemes = data.repeated_tags.slice(0, 3);
  
  // Source breakdown - only count sources with signals > 0
  const activeSources = Object.entries(data.source_breakdown || {}).filter(([_, count]) => count > 0);
  const activeSourceCount = activeSources.length;
  
  // Future sources that aren't active yet
  const futureSourceLabels = ['Journal', 'Chat', 'HD', 'Enneagram'];

  // ==========================================================================
  // RENDER: ACCORDION HEADER
  // ==========================================================================

  const renderAccordionHeader = (
    section: AccordionSection,
    title: string,
    count?: number
  ) => {
    const isOpen = expandedSection === section;
    return (
      <TouchableOpacity
        style={[styles.accordionHeader, { borderBottomColor: COLORS.border }]}
        onPress={() => toggleSection(section)}
        activeOpacity={0.7}
      >
        <View style={styles.accordionTitleRow}>
          <Text style={[styles.accordionTitle, { color: theme.text }]}>{title}</Text>
          {count !== undefined && (
            <Text style={[styles.accordionCount, { color: theme.textTertiary }]}>{count}</Text>
          )}
        </View>
        <Text style={[styles.chevron, { color: theme.textTertiary }]}>
          {isOpen ? '▼' : '▶'}
        </Text>
      </TouchableOpacity>
    );
  };

  // ==========================================================================
  // RENDER: DOMAIN CARD (COMPACT)
  // ==========================================================================

  const renderDomainCard = (domain: DomainSummary, index: number) => {
    const strengthPercent = Math.min(domain.average_intensity * 100, 100);
    return (
      <View key={domain.domain} style={styles.domainCard}>
        <View style={styles.domainHeader}>
          <Text style={[styles.domainName, { color: theme.text }]}>{domain.domain_label}</Text>
          <Text style={[styles.domainSignalCount, { color: theme.textTertiary }]}>
            {domain.signal_count}
          </Text>
        </View>
        <View style={[styles.strengthBar, { backgroundColor: 'rgba(168, 178, 192, 0.15)' }]}>
          <View style={[styles.strengthFill, { width: `${Math.max(strengthPercent, 8)}%`, backgroundColor: COLORS.moonlight }]} />
        </View>
        <View style={styles.domainMeta}>
          {domain.dominant_signals.slice(0, 2).map((sig, i) => (
            <Text key={i} style={[styles.domainTag, { color: theme.textSecondary }]}>
              {SIGNAL_ICONS[sig] || '•'} {sig}
            </Text>
          ))}
        </View>
      </View>
    );
  };

  // ==========================================================================
  // RENDER: SIGNAL ITEM (COMPACT)
  // ==========================================================================

  const renderSignalItem = (signal: SignalSummary, index: number) => {
    const icon = SIGNAL_ICONS[signal.signal_type] || '•';
    return (
      <View key={index} style={styles.signalItem}>
        <Text style={styles.signalIcon}>{icon}</Text>
        <View style={styles.signalContent}>
          <Text style={[styles.signalType, { color: theme.text }]}>{signal.signal_type}</Text>
          {signal.preview && (
            <Text style={[styles.signalPreview, { color: theme.textTertiary }]} numberOfLines={1}>
              "{signal.preview}"
            </Text>
          )}
        </View>
        {signal.gate && (
          <Text style={[styles.signalGate, { color: theme.textTertiary }]}>G{signal.gate}</Text>
        )}
      </View>
    );
  };

  // ==========================================================================
  // MAIN RENDER
  // ==========================================================================

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      
      {/* ════════════════════════════════════════════════════════════════════
          SUMMARY SECTION (Always Visible)
          ════════════════════════════════════════════════════════════════════ */}
      <View style={styles.summarySection}>
        {/* Header Row */}
        <View style={styles.headerRow}>
          <Text style={[styles.title, { color: theme.text }]}>Pattern Signals</Text>
          <View style={[styles.momentumBadge, { backgroundColor: momentum.color + '20' }]}>
            <Text style={[styles.momentumText, { color: momentum.color }]}>
              {momentum.icon} {momentum.label}
            </Text>
          </View>
        </View>

        {/* Stats Row - More human-readable */}
        <Text style={[styles.statsText, { color: theme.textTertiary }]}>
          {data.total_signals} signal{data.total_signals !== 1 ? 's' : ''} from {activeSourceCount} source{activeSourceCount !== 1 ? 's' : ''}{data.data_sufficiency === 'limited' ? ' · Still building' : data.data_sufficiency === 'medium' ? ' · Growing' : ' · Rich data'}
        </Text>

        {/* Most Active Domains */}
        {topDomains.length > 0 && (
          <View style={styles.summaryGroup}>
            <Text style={[styles.summaryLabel, { color: COLORS.silver }]}>Active Life Areas</Text>
            <View style={styles.summaryList}>
              {topDomains.map((d, i) => (
                <Text key={i} style={[styles.summaryItem, { color: theme.textSecondary }]}>
                  • {d.domain_label}
                </Text>
              ))}
            </View>
          </View>
        )}

        {/* Top Themes */}
        {topThemes.length > 0 && (
          <View style={styles.summaryGroup}>
            <Text style={[styles.summaryLabel, { color: COLORS.silver }]}>Recurring Themes</Text>
            <View style={styles.themePills}>
              {topThemes.map((tag, i) => (
                <View key={i} style={[styles.themePill, { backgroundColor: COLORS.cardBg }]}>
                  <Text style={[styles.themePillText, { color: theme.textSecondary }]}>
                    {tag.replace(/_/g, ' ')}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </View>

      {/* ════════════════════════════════════════════════════════════════════
          ACCORDION SECTIONS (Collapsed by Default)
          ════════════════════════════════════════════════════════════════════ */}
      <View style={[styles.accordionContainer, { borderTopColor: COLORS.border }]}>
        
        {/* Active Domains Accordion */}
        {renderAccordionHeader('domains', 'Active Domains', data.active_domains.length)}
        {expandedSection === 'domains' && (
          <View style={styles.accordionContent}>
            {data.active_domains.map(renderDomainCard)}
          </View>
        )}

        {/* Strongest Signals Accordion */}
        {renderAccordionHeader('signals', 'Strongest Signals', data.strongest_signals.length)}
        {expandedSection === 'signals' && (
          <View style={styles.accordionContent}>
            {data.strongest_signals.slice(0, showMoreSignals ? undefined : 3).map(renderSignalItem)}
            {data.strongest_signals.length > 3 && !showMoreSignals && (
              <TouchableOpacity onPress={() => setShowMoreSignals(true)}>
                <Text style={[styles.showMoreText, { color: COLORS.moonlight }]}>
                  Show {data.strongest_signals.length - 3} more
                </Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Themes Accordion */}
        {renderAccordionHeader('themes', 'All Themes', data.repeated_tags.length)}
        {expandedSection === 'themes' && (
          <View style={styles.accordionContent}>
            <View style={styles.themePillsExpanded}>
              {data.repeated_tags.map((tag, i) => (
                <View key={i} style={[styles.themePill, { backgroundColor: COLORS.cardBg }]}>
                  <Text style={[styles.themePillText, { color: theme.textSecondary }]}>
                    {tag.replace(/_/g, ' ')}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Sources Accordion */}
        {renderAccordionHeader('sources', 'Source Breakdown', activeSourceCount)}
        {expandedSection === 'sources' && (
          <View style={styles.accordionContent}>
            {activeSources.length > 0 ? (
              <View style={styles.sourcePills}>
                {activeSources.map(([source, count]) => (
                  <View key={source} style={[styles.sourcePill, { backgroundColor: COLORS.cardBg }]}>
                    <Text style={[styles.sourcePillText, { color: theme.textSecondary }]}>
                      {SOURCE_LABELS[source] || source} — {count}
                    </Text>
                  </View>
                ))}
              </View>
            ) : (
              <Text style={[styles.noSourcesText, { color: theme.textTertiary }]}>
                No active sources yet
              </Text>
            )}
            <Text style={[styles.stubNote, { color: theme.textTertiary }]}>
              More sources coming soon: {futureSourceLabels.join(', ')}
            </Text>
          </View>
        )}
      </View>

      {/* ════════════════════════════════════════════════════════════════════
          DEBUG SECTION (Only if showDebug is true)
          ════════════════════════════════════════════════════════════════════ */}
      {showDebug && data.debug && (
        <View style={[styles.debugSection, { backgroundColor: 'rgba(255, 165, 0, 0.1)', borderColor: '#FFA500' }]}>
          <Text style={[styles.debugTitle, { color: '#FFA500' }]}>🐛 Debug Info</Text>
          <Text style={[styles.debugText, { color: theme.textSecondary }]}>
            Total excitement: {data.debug.total_excitement?.toFixed(2)}{'\n'}
            Total hesitation: {data.debug.total_hesitation?.toFixed(2)}{'\n'}
            Raw signal count: {data.debug.raw_signal_count}{'\n'}
            Domains: {data.debug.all_domains?.join(', ')}
          </Text>
        </View>
      )}
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
    overflow: 'hidden',
    marginBottom: 16,
  },
  
  // Loading/Error/Empty
  loadingText: {
    textAlign: 'center',
    padding: 20,
    fontSize: 13,
  },
  emptyText: {
    textAlign: 'center',
    padding: 20,
    fontSize: 13,
    lineHeight: 20,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '500',
    marginBottom: 12,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  emptyStateContent: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  emptyDescription: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 20,
  },
  emptyStateActions: {
    backgroundColor: 'rgba(168, 178, 192, 0.08)',
    borderRadius: 12,
    padding: 16,
  },
  emptyActionsTitle: {
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  emptyActionsList: {
    gap: 8,
  },
  emptyActionItem: {
    fontSize: 14,
    lineHeight: 20,
  },

  // Summary Section
  summarySection: {
    padding: 20,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: '500',
  },
  momentumBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  momentumText: {
    fontSize: 12,
    fontWeight: '500',
  },
  statsText: {
    fontSize: 12,
    marginBottom: 16,
  },
  summaryGroup: {
    marginTop: 12,
  },
  summaryLabel: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  summaryList: {
    gap: 2,
  },
  summaryItem: {
    fontSize: 13,
    lineHeight: 20,
  },
  themePills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  themePill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  themePillText: {
    fontSize: 12,
  },

  // Accordion
  accordionContainer: {
    borderTopWidth: 1,
  },
  accordionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
  },
  accordionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  accordionTitle: {
    fontSize: 14,
    fontWeight: '500',
  },
  accordionCount: {
    fontSize: 12,
  },
  chevron: {
    fontSize: 10,
  },
  accordionContent: {
    paddingHorizontal: 20,
    paddingVertical: 12,
  },

  // Domain Cards
  domainCard: {
    marginBottom: 12,
  },
  domainHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  domainName: {
    fontSize: 13,
    fontWeight: '500',
  },
  domainSignalCount: {
    fontSize: 11,
  },
  strengthBar: {
    height: 4,
    borderRadius: 2,
    marginBottom: 6,
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  domainMeta: {
    flexDirection: 'row',
    gap: 12,
  },
  domainTag: {
    fontSize: 11,
    textTransform: 'capitalize',
  },

  // Signal Items
  signalItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    gap: 10,
  },
  signalIcon: {
    fontSize: 16,
    width: 24,
  },
  signalContent: {
    flex: 1,
  },
  signalType: {
    fontSize: 13,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  signalPreview: {
    fontSize: 11,
    marginTop: 2,
  },
  signalGate: {
    fontSize: 10,
    fontWeight: '500',
  },
  showMoreText: {
    fontSize: 12,
    fontWeight: '500',
    textAlign: 'center',
    paddingVertical: 8,
  },

  // Themes Expanded
  themePillsExpanded: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },

  // Sources
  sourcePills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 8,
  },
  sourcePill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  sourcePillText: {
    fontSize: 13,
    fontWeight: '500',
  },
  noSourcesText: {
    fontSize: 12,
    marginBottom: 8,
  },
  stubNote: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 8,
  },

  // Debug
  debugSection: {
    margin: 16,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  debugTitle: {
    fontSize: 12,
    fontWeight: '500',
    marginBottom: 6,
  },
  debugText: {
    fontSize: 10,
    fontFamily: 'monospace',
    lineHeight: 16,
  },
});

export type { PatternGraphData, DomainSummary, SignalSummary };
