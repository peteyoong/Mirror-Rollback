import React, { useState, useEffect, forwardRef, useImperativeHandle, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';
import { LensViewRef } from './HumanDesignLensView';
import { buildJournalPrefill, goToJournalWithPrefill, LENS_CONTINUATIONS } from '../utils/journalPrefill';

interface AstrologySection {
  id: string;      // Stable identifier (e.g., "sun", "moon", "ascendant")
  label: string;   // Display label (can change without breaking expansion)
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

const AstrologyLensView = forwardRef<LensViewRef, Props>(({ userId, onOpenChat }, ref) => {
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [data, setData] = useState<AstrologyData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [showChartModal, setShowChartModal] = useState(false);
  const [isRecomputing, setIsRecomputing] = useState(false);
  
  // Router for navigation
  const router = useRouter();
  
  // Debug: track raw API response length
  const [rawDataLength, setRawDataLength] = useState<number>(0);
  
  // Debug flag
  const isDebug = typeof window !== 'undefined' && window.location?.search?.includes('debug=1');
  
  // Stale response guard: prevent race conditions when switching tabs quickly
  const requestIdRef = useRef(0);

  // Expose refetch method via ref (preserves accordion/scroll state)
  useImperativeHandle(ref, () => ({
    refetch: () => {
      if (isDebug || __DEV__) {
        console.log(`[ASTRO_LENS_DEBUG] refetch() called via ref - preserving UI state`);
      }
      loadTabData(activeTab);
    }
  }), [activeTab]);

  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab, userId]);

  const loadTabData = async (tab: TabType) => {
    // Increment request ID to track this specific request
    const requestId = ++requestIdRef.current;
    
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = tab === 'today' 
        ? `/astrology/today/${userId}`
        : tab === 'deep_dive'
        ? `/astrology/deep-dive/${userId}`
        : `/astrology/summary/${userId}`;

      const response = await api.get(endpoint);
      
      // STALE RESPONSE GUARD: Ignore if a newer request was made
      if (requestId !== requestIdRef.current) {
        if (isDebug || __DEV__) {
          console.log(`[ASTRO_LENS_DEBUG] Ignoring stale response (requestId: ${requestId})`);
        }
        return;
      }
      
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
      // STALE RESPONSE GUARD: Ignore errors from stale requests
      if (requestId !== requestIdRef.current) {
        return;
      }
      console.error(`Astrology ${tab} error:`, err);
      setError('Unable to load this view right now.');
    } finally {
      // Only update loading state if this is still the current request
      if (requestId === requestIdRef.current) {
        setIsLoading(false);
      }
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
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, activeTab === 'summary' && styles.activeTabText]}>
          Overview
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'today' && styles.activeTab]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, activeTab === 'today' && styles.activeTabText]}>
          Today
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, activeTab === 'deep_dive' && styles.activeTabText]}>
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
      <View style={styles.corePlacementsCard}>
        <Text style={styles.corePlacementsTitle}>SUN • MOON • ASCENDANT</Text>
        <View style={styles.corePlacementsRow}>
          <View style={styles.placementItem}>
            <Ionicons name="sunny-outline" size={16} color={Colors.accent} />
            <Text style={styles.placementSign}>{formatPlacement(placements.sun)}</Text>
          </View>
          <View style={styles.placementDivider} />
          <View style={styles.placementItem}>
            <Ionicons name="moon-outline" size={16} color={Colors.accent} />
            <Text style={styles.placementSign}>{formatPlacement(placements.moon)}</Text>
          </View>
          <View style={styles.placementDivider} />
          <View style={styles.placementItem}>
            <Ionicons name="arrow-up-outline" size={16} color={Colors.accent} />
            <Text style={styles.placementSign}>{formatPlacement(placements.ascendant)}</Text>
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
        <Ionicons name="alert-circle-outline" size={32} color={Colors.textTertiary} />
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
            <ActivityIndicator size="small" color={Colors.surface} />
          ) : (
            <>
              <Ionicons name="refresh-outline" size={18} color={Colors.surface} />
              <Text style={styles.recomputeButtonText}>Recompute chart</Text>
            </>
          )}
        </TouchableOpacity>
      </View>
    );
  };

  const renderSection = (section: AstrologySection, index: number) => {
    // Use stable section.id for expansion state (not display label)
    // For non-deep_dive tabs, always show expanded
    // For deep_dive: expand if 'all' selected, or if this specific section is selected by id
    const isExpanded = 
      activeTab !== 'deep_dive' || 
      expandedSection === 'all' || 
      expandedSection === section.id;

    return (
      <View key={section.id || index} style={styles.sectionCard}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => {
            if (activeTab === 'deep_dive') {
              // Toggle by section.id for stability
              setExpandedSection(expandedSection === section.id ? null : section.id);
            }
          }}
          activeOpacity={activeTab === 'deep_dive' ? 0.7 : 1}
        >
          <Text style={styles.sectionLabel}>{section.label}</Text>
          {activeTab === 'deep_dive' && (
            <Ionicons
              name={isExpanded ? 'chevron-up' : 'chevron-down'}
              size={18}
              color={Colors.textTertiary}
            />
          )}
        </TouchableOpacity>
        {isExpanded && (
          <View style={styles.sectionBodyContainer}>
            <Text style={styles.sectionBody}>{section.body}</Text>
            {/* Debug: Show section-level metrics */}
            <SectionDebug label={section.label} body={section.body} index={index} />
          </View>
        )}
      </View>
    );
  };

  const renderNatalChartReference = () => {
    if (activeTab !== 'deep_dive') return null;

    return (
      <View style={styles.chartReferenceCard}>
        <View style={styles.chartReferenceHeader}>
          <Ionicons name="document-outline" size={20} color={Colors.textSecondary} />
          <Text style={styles.chartReferenceTitle}>Natal Chart (Reference)</Text>
        </View>
        <Text style={styles.chartReferenceDisclaimer}>
          This chart shows structure, not meaning on its own.
        </Text>
        <TouchableOpacity
          style={styles.chartButton}
          onPress={() => setShowChartModal(true)}
        >
          <Ionicons name="expand-outline" size={16} color={Colors.accent} />
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
            <Ionicons name="close" size={24} color={Colors.textSecondary} />
          </TouchableOpacity>
          
          <Text style={styles.modalTitle}>Natal Chart Reference</Text>
          
          <View style={styles.chartPlaceholder}>
            <Ionicons name="planet-outline" size={48} color={Colors.textTertiary} />
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
    <View style={styles.container}>
      {renderTabs()}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.textTertiary} />
            <Text style={styles.loadingText}>
              {activeTab === 'deep_dive' 
                ? 'Generating your personalized reading...\nThis may take 30-45 seconds'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={32} color={Colors.textTertiary} />
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
            <Text style={styles.title}>
              {data.title || (activeTab === 'deep_dive' ? 'Your Core Structure' : 'Astrology')}
            </Text>

            {/* Date for Today tab */}
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
                      color={Colors.accent}
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
                    <TouchableOpacity
                      style={styles.journalCTA}
                      onPress={() => {
                        const prefill = buildJournalPrefill(data.mirror_prompt, LENS_CONTINUATIONS.astrology);
                        goToJournalWithPrefill(router, prefill, 'astrology');
                      }}
                    >
                      <Ionicons name="create-outline" size={16} color={Colors.accent} />
                      <Text style={styles.journalCTAText}>Write in Journal</Text>
                    </TouchableOpacity>
                  </View>
                )}

                {/* Natal Chart Reference (Deep Dive only) */}
                {renderNatalChartReference()}

                {/* Ask Mirror Button */}
                <TouchableOpacity
                  style={styles.askMirrorButton}
                  onPress={onOpenChat}
                >
                  <Ionicons name="chatbubble-outline" size={18} color={Colors.surface} />
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
});

// Set display name for debugging
AstrologyLensView.displayName = 'AstrologyLensView';

export default AstrologyLensView;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
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
    backgroundColor: Colors.surface,
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: Colors.text,
  },
  tabText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  activeTabText: {
    color: Colors.surface,
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
    color: Colors.textTertiary,
  },
  errorContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: Colors.surface,
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  dateLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 20,
  },
  corePlacementsCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  corePlacementsTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
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
    color: Colors.text,
  },
  placementDivider: {
    width: 1,
    height: 20,
    backgroundColor: Colors.border,
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
    color: Colors.accent,
    fontWeight: '500',
  },
  sectionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
    letterSpacing: 0.3,
    flex: 1,
  },
  sectionBodyContainer: {
    // Ensure expanded content has natural height, no clipping
    flexShrink: 0,
  },
  sectionBody: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.text,
    marginTop: 12,
    // Ensure text is never truncated
    flexWrap: 'wrap',
  },
  mirrorPromptCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 20,
    marginTop: 8,
    marginBottom: 20,
    borderLeftWidth: 3,
    borderLeftColor: Colors.accent,
  },
  mirrorPromptLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  mirrorPromptText: {
    fontSize: 16,
    lineHeight: 26,
    color: Colors.text,
    fontStyle: 'italic',
  },
  journalCTA: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  journalCTAText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.accent,
  },
  chartReferenceCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
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
    color: Colors.text,
  },
  chartReferenceDisclaimer: {
    fontSize: 13,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    marginBottom: 12,
  },
  chartButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    backgroundColor: Colors.background,
    borderRadius: 8,
  },
  chartButtonText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    backgroundColor: Colors.text,
    borderRadius: 12,
    marginBottom: 20,
  },
  askMirrorText: {
    fontSize: 15,
    color: Colors.surface,
    fontWeight: '500',
  },
  footer: {
    fontSize: 12,
    color: Colors.textTertiary,
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
    backgroundColor: Colors.background,
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
    color: Colors.text,
    marginBottom: 20,
  },
  chartPlaceholder: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 40,
    alignItems: 'center',
    marginBottom: 20,
  },
  chartPlaceholderText: {
    fontSize: 14,
    color: Colors.textTertiary,
    marginTop: 12,
    textAlign: 'center',
  },
  modalDisclaimer: {
    fontSize: 13,
    lineHeight: 20,
    color: Colors.textSecondary,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  // Compute Error Card styles
  computeErrorCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 24,
    marginVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  computeErrorTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 8,
  },
  computeErrorMessage: {
    fontSize: 14,
    color: Colors.textSecondary,
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
    backgroundColor: Colors.text,
    borderRadius: 8,
  },
  recomputeButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.surface,
  },
  disabledButton: {
    opacity: 0.6,
  },
});
