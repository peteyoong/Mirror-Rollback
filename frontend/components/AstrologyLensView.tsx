import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';

interface AstrologySection {
  label: string;
  body: string;
}

interface AstrologyData {
  title: string;
  sections: AstrologySection[];
  mirror_prompt: string;
  core_placements?: {
    sun: string;
    moon: string;
    ascendant: string | null;
  };
  date?: string;
  success?: boolean;
  error?: string;
  message?: string;
  // Debug fields from API
  debug_stamp?: {
    fallback_used?: boolean;
    source?: string;
    timestamp?: string;
    cached?: boolean;
  };
}

interface Props {
  userId: string;
  onOpenChat: () => void;
}

type TabType = 'summary' | 'today' | 'deep_dive';

export default function AstrologyLensView({ userId, onOpenChat }: Props) {
  // Theme support
  const { theme, isDark } = useTheme();
  
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [data, setData] = useState<AstrologyData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [showChartModal, setShowChartModal] = useState(false);
  const [isRecomputing, setIsRecomputing] = useState(false);
  
  // Debug: track raw API response length
  const [rawDataLength, setRawDataLength] = useState<number>(0);

  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab, userId]);

  const loadTabData = async (tab: TabType) => {
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = tab === 'today' 
        ? `/astrology/today/${userId}`
        : tab === 'deep_dive'
        ? `/astrology/deep-dive/${userId}`
        : `/astrology/summary/${userId}`;

      const response = await api.get(endpoint);
      setData(response.data);
      
      // Debug: Calculate raw data length for comparison
      if (isDebugEnabled() && response.data?.sections) {
        const totalChars = response.data.sections.reduce(
          (sum: number, s: AstrologySection) => sum + (s.body?.length || 0), 
          0
        );
        setRawDataLength(totalChars);
        console.log(`[DEBUG_MIRROR] Astrology ${tab}: API returned ${totalChars} chars across ${response.data.sections.length} sections`);
      }
    } catch (err: any) {
      console.error(`Astrology ${tab} error:`, err);
      setError('Unable to load this view right now.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecomputeChart = async () => {
    setIsRecomputing(true);
    try {
      await api.post(`/charts/calculate`, { user_id: userId });
      // Reload data after recompute
      await loadTabData(activeTab);
    } catch (err: any) {
      console.error('Recompute error:', err);
      setError('Failed to recompute chart. Please try again.');
    } finally {
      setIsRecomputing(false);
    }
  };

  const renderTabs = () => (
    <View style={[styles.tabContainer, { borderBottomColor: theme.border }]}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'summary' && { color: theme.text }]}>
          Summary
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'today' && styles.activeTab]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'today' && { color: theme.text }]}>
          Today's Snapshot
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text }]}>
          Deep Dive
        </Text>
      </TouchableOpacity>
    </View>
  );

  // Always render core placements for deep dive, even with fallback values
  const renderCorePlacements = () => {
    // Default fallback if no data
    const placements = data?.core_placements || {
      sun: 'Unknown',
      moon: 'Unknown',
      ascendant: 'Unknown'
    };

    // Helper to format unknown gracefully
    const formatPlacement = (value: string | null) => {
      if (!value || value === 'Unknown') return '—';
      return value;
    };

    return (
      <View style={[styles.corePlacementsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.corePlacementsTitle, { color: theme.textTertiary }]}>SUN • MOON • ASCENDANT</Text>
        <View style={styles.corePlacementsRow}>
          <View style={styles.placementItem}>
            <Ionicons name="sunny-outline" size={16} color={theme.accent} />
            <Text style={[styles.placementSign, { color: theme.text }]}>{formatPlacement(placements.sun)}</Text>
          </View>
          <View style={[styles.placementDivider, { backgroundColor: theme.border }]} />
          <View style={styles.placementItem}>
            <Ionicons name="moon-outline" size={16} color={theme.accent} />
            <Text style={[styles.placementSign, { color: theme.text }]}>{formatPlacement(placements.moon)}</Text>
          </View>
          <View style={[styles.placementDivider, { backgroundColor: theme.border }]} />
          <View style={styles.placementItem}>
            <Ionicons name="arrow-up-outline" size={16} color={theme.accent} />
            <Text style={[styles.placementSign, { color: theme.text }]}>{formatPlacement(placements.ascendant)}</Text>
          </View>
        </View>
      </View>
    );
  };

  // Render error card when ascendant computation failed
  const renderComputeErrorCard = () => {
    if (data?.success !== false) return null;
    
    return (
      <View style={styles.computeErrorCard}>
        <Ionicons name="alert-circle-outline" size={32} color={theme.textTertiary} />
        <Text style={styles.computeErrorTitle}>
          We couldn't compute your Ascendant right now.
        </Text>
        <Text style={styles.computeErrorMessage}>
          {data?.message || 'Your chart may need to be recalculated.'}
        </Text>
        <TouchableOpacity
          style={[styles.recomputeButton, isRecomputing && styles.disabledButton]}
          onPress={handleRecomputeChart}
          disabled={isRecomputing}
        >
          {isRecomputing ? (
            <ActivityIndicator size="small" color={theme.textInverse} />
          ) : (
            <>
              <Ionicons name="refresh-outline" size={18} color={theme.textInverse} />
              <Text style={styles.recomputeButtonText}>Recompute chart</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    );
  };

  const renderSection = (section: AstrologySection, index: number) => {
    const isExpanded = expandedSection === section.label || activeTab !== 'deep_dive';

    return (
      <View key={index} style={styles.sectionCard}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => {
            if (activeTab === 'deep_dive') {
              setExpandedSection(expandedSection === section.label ? null : section.label);
            }
          }}
          activeOpacity={activeTab === 'deep_dive' ? 0.7 : 1}
        >
          <Text style={styles.sectionLabel}>{section.label}</Text>
          {activeTab === 'deep_dive' && (
            <Ionicons
              name={isExpanded ? 'chevron-up' : 'chevron-down'}
              size={18}
              color={theme.textTertiary}
            />
          )}
        </TouchableOpacity>
        {isExpanded && (
          <>
            <Text style={styles.sectionBody}>{section.body}</Text>
            {/* Debug: Show section-level metrics */}
            <SectionDebug label={section.label} body={section.body} index={index} />
          </>
        )}
      </View>
    );
  };

  const renderNatalChartReference = () => {
    if (activeTab !== 'deep_dive') return null;

    return (
      <View style={styles.chartReferenceCard}>
        <View style={styles.chartReferenceHeader}>
          <Ionicons name="document-outline" size={20} color={theme.textSecondary} />
          <Text style={styles.chartReferenceTitle}>Natal Chart (Reference)</Text>
        </View>
        <Text style={styles.chartReferenceDisclaimer}>
          This chart shows structure, not meaning on its own.
        </Text>
        <TouchableOpacity
          style={styles.chartButton}
          onPress={() => setShowChartModal(true)}
        >
          <Ionicons name="expand-outline" size={16} color={theme.accent} />
          <Text style={styles.chartButtonText}>Open Full Chart (PDF)</Text>
        </TouchableOpacity>
      </View>
    );
  };

  const renderChartModal = () => (
    <Modal
      visible={showChartModal}
      transparent
      animationType="fade"
      onRequestClose={() => setShowChartModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <TouchableOpacity
            style={styles.modalClose}
            onPress={() => setShowChartModal(false)}
          >
            <Ionicons name="close" size={24} color={theme.textSecondary} />
          </TouchableOpacity>
          
          <Text style={styles.modalTitle}>Natal Chart Reference</Text>
          
          <View style={styles.chartPlaceholder}>
            <Ionicons name="planet-outline" size={48} color={theme.textTertiary} />
            <Text style={styles.chartPlaceholderText}>
              Full chart visualization coming soon
            </Text>
          </View>
          
          <Text style={styles.modalDisclaimer}>
            This chart shows structure, not meaning on its own.
            {'\n\n'}
            Patterns suggest tendencies, not guarantees.
            What in this structure feels recognisable to you?
          </Text>
        </View>
      </View>
    </Modal>
  );

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {renderTabs()}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.textTertiary} />
            <Text style={styles.loadingText}>
              {activeTab === 'deep_dive' 
                ? 'Generating your personalized reading...\nThis may take 30-45 seconds'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={32} color={theme.textTertiary} />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => loadTabData(activeTab)}
            >
              <Text style={styles.retryText}>Try Again</Text>
            </TouchableOpacity>
            {/* Still show core card on Deep Dive even with error */}
            {activeTab === 'deep_dive' && renderCorePlacements()}
          </View>
        ) : data ? (
          <>
            {/* Title */}
            <Text style={styles.title}>{data.title || (activeTab === 'deep_dive' ? 'Your Core Structure' : 'Astrology')}</Text>

            {/* Date for Today's Snapshot tab only */}
            {activeTab === 'today' && data.date && (
              <Text style={styles.dateLabel}>{data.date}</Text>
            )}

            {/* Core Placements Card (Deep Dive only) - always show even if success=false */}
            {activeTab === 'deep_dive' && renderCorePlacements()}

            {/* ERROR CARD: Show when Deep Dive computation failed */}
            {activeTab === 'deep_dive' && data.success === false && renderComputeErrorCard()}

            {/* Only show content sections if success !== false */}
            {data.success !== false && (
              <>
                {/* Expand Button (Deep Dive only) */}
                {activeTab === 'deep_dive' && (
                  <TouchableOpacity
                    style={styles.expandButton}
                    onPress={() => setExpandedSection(expandedSection ? null : 'all')}
                  >
                    <Text style={styles.expandButtonText}>
                      {expandedSection ? 'Collapse sections' : 'Explore your core structure'}
                    </Text>
                    <Ionicons
                      name={expandedSection ? 'contract-outline' : 'expand-outline'}
                      size={16}
                      color={theme.accent}
                    />
                  </TouchableOpacity>
                )}

                {/* Sections */}
                {data.sections?.map((section, index) => renderSection(section, index))}

                {/* Mirror Prompt */}
                {data.mirror_prompt && (
                  <View style={styles.mirrorPromptCard}>
                    <Text style={styles.mirrorPromptLabel}>REFLECT</Text>
                    <Text style={styles.mirrorPromptText}>{data.mirror_prompt}</Text>
                  </View>
                )}

                {/* Natal Chart Reference (Deep Dive only) */}
                {renderNatalChartReference()}

                {/* Ask Mirror Button */}
                <TouchableOpacity
                  style={styles.askMirrorButton}
                  onPress={onOpenChat}
                >
                  <Ionicons name="chatbubble-outline" size={18} color={theme.textInverse} />
                  <Text style={styles.askMirrorText}>Ask about this lens</Text>
                </TouchableOpacity>

                {/* Footer */}
                <Text style={styles.footer}>
                  A lens for understanding patterns, not a definition of identity.
                </Text>
                
                {/* Debug Footer - only shows when DEBUG_MIRROR is enabled */}
                {activeTab === 'deep_dive' && data.sections && (
                  <DebugFooter 
                    lens="Astrology"
                    sections={data.sections}
                    source={data.debug_stamp?.source}
                    rawDataLength={rawDataLength}
                    debugStamp={data.debug_stamp}
                  />
                )}
              </>
            )}
          </>
        ) : null}
      </ScrollView>

      {renderChartModal()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "transparent",
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: "transparent",
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: "transparent",
  },
  tabText: {
    fontSize: 13,
    fontWeight: '500',
    color: "inherit",
  },
  activeTabText: {
    color: "inherit",
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: "inherit",
  },
  errorContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    color: "inherit",
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: "transparent",
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    color: "inherit",
    fontWeight: '500',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 8,
  },
  dateLabel: {
    fontSize: 12,
    color: "inherit",
    marginBottom: 20,
  },
  corePlacementsCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  corePlacementsTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 12,
  },
  corePlacementsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  placementItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
  },
  placementSign: {
    fontSize: 15,
    fontWeight: '500',
    color: "inherit",
  },
  placementDivider: {
    width: 1,
    height: 20,
    backgroundColor: "transparent",
  },
  expandButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    marginBottom: 16,
  },
  expandButtonText: {
    fontSize: 14,
    color: "inherit",
    fontWeight: '500',
  },
  sectionCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 0.3,
    flex: 1,
  },
  sectionBody: {
    fontSize: 15,
    lineHeight: 24,
    color: "inherit",
    marginTop: 12,
  },
  mirrorPromptCard: {
    backgroundColor: '#FDFCFA',
    borderRadius: 12,
    padding: 20,
    marginTop: 8,
    marginBottom: 20,
    borderLeftWidth: 3,
    borderLeftColor: "transparent",
  },
  mirrorPromptLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  mirrorPromptText: {
    fontSize: 16,
    lineHeight: 26,
    color: "inherit",
    fontStyle: 'italic',
  },
  chartReferenceCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  chartReferenceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  chartReferenceTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: "inherit",
  },
  chartReferenceDisclaimer: {
    fontSize: 13,
    color: "inherit",
    fontStyle: 'italic',
    marginBottom: 12,
  },
  chartButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    backgroundColor: "transparent",
    borderRadius: 8,
  },
  chartButtonText: {
    fontSize: 14,
    color: "inherit",
    fontWeight: '500',
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    backgroundColor: "transparent",
    borderRadius: 12,
    marginBottom: 20,
  },
  askMirrorText: {
    fontSize: 15,
    color: "inherit",
    fontWeight: '500',
  },
  footer: {
    fontSize: 12,
    color: "inherit",
    textAlign: 'center',
    fontStyle: 'italic',
    opacity: 0.7,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: "transparent",
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 360,
  },
  modalClose: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 1,
    padding: 4,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 20,
  },
  chartPlaceholder: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
    marginBottom: 20,
  },
  chartPlaceholderText: {
    fontSize: 14,
    color: "inherit",
    marginTop: 12,
    textAlign: 'center',
  },
  modalDisclaimer: {
    fontSize: 13,
    lineHeight: 20,
    color: "inherit",
    textAlign: 'center',
    fontStyle: 'italic',
  },
  // Compute Error Card styles
  computeErrorCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 24,
    marginVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: "transparent",
  },
  computeErrorTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: "inherit",
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 8,
  },
  computeErrorMessage: {
    fontSize: 14,
    color: "inherit",
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 20,
  },
  recomputeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: "transparent",
    borderRadius: 8,
  },
  recomputeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: "inherit",
  },
  disabledButton: {
    opacity: 0.6,
  },
});
