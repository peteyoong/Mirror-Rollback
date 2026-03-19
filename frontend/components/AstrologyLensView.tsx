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
import { InlineReflectButton } from './UniversalReflectButton';
// Removed Ionicons - using text alternatives for web compatibility
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';

interface AstrologySection {
  label: string;
  body: string;
}

// v6: Narrative-based response from /astrology/today-v2 (deprecated)
interface AstrologyNarrativeData {
  success: boolean;
  version: string;
  date: string;
  narrative: string;
  experience?: string;
  cause?: string;
  guidance?: string;
  internal_dynamics?: string;
  technical?: {
    placements?: string[];
    transits?: string[];
  };
  day_class?: string;
  transit_summary?: string;
  validation?: {
    valid: boolean;
    feels_like_thought?: boolean;
  };
}

// v_next: 3-altitude snapshot system
interface AltitudeNarrative {
  title: string;
  body: string;
  bridge: string | null;
  date?: string;
  date_range?: string;
  month?: string;
  technical?: {
    day_class?: string;
    week_class?: string;
    month_class?: string;
    transits?: string[];
    placements?: string[];
    interaction_theme?: string;
    intensity?: number;
  };
}

interface Snapshot3AltData {
  success: boolean;
  today: AltitudeNarrative;
  week: AltitudeNarrative;
  month: AltitudeNarrative;
  transit_stack: {
    classification?: string;
    intensity?: number;
    interaction_theme?: string;
    events?: string[];
  };
  version: string;
  generated_at: string;
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
  // v6: narrative data for Today tab
  narrative?: string;
  technical?: {
    placements?: string[];
    transits?: string[];
  };
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
  
  // v_next: 3-altitude snapshot state
  const [snapshotData, setSnapshotData] = useState<Snapshot3AltData | null>(null);
  const [activeAltitude, setActiveAltitude] = useState<'today' | 'week' | 'month'>('today');
  
  // Debug: track raw API response length
  const [rawDataLength, setRawDataLength] = useState<number>(0);

  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab, userId]);

  const loadTabData = async (tab: TabType) => {
    setIsLoading(true);
    setError(null);

    try {
      // v_next: Use 3-altitude snapshot for Today tab
      if (tab === 'today') {
        const response = await api.get(`/astrology/snapshot/${userId}`);
        console.log('[ASTROLOGY_SNAPSHOT] 3-altitude data:', JSON.stringify(response.data, null, 2));
        
        if (response.data.success) {
          setSnapshotData(response.data as Snapshot3AltData);
          // Also set legacy data for fallback compatibility
          const todayNarrative = response.data.today;
          setData({
            title: todayNarrative.title,
            sections: [],
            mirror_prompt: '',
            date: todayNarrative.date,
            success: true,
            narrative: todayNarrative.body,
            technical: todayNarrative.technical,
          });
        } else {
          throw new Error('Failed to load snapshot');
        }
      } else {
        // Summary and Deep Dive use existing endpoints
        const endpoint = tab === 'deep_dive'
          ? `/astrology/deep-dive/${userId}`
          : `/astrology/summary/${userId}`;

        const response = await api.get(endpoint);
        setData(response.data);
        setSnapshotData(null); // Clear snapshot data for non-today tabs
      }
      
      // Debug: Calculate raw data length for comparison
      if (isDebugEnabled() && data?.sections) {
        const totalChars = data.sections.reduce(
          (sum: number, s: AstrologySection) => sum + (s.body?.length || 0), 
          0
        );
        setRawDataLength(totalChars);
        console.log(`[DEBUG_MIRROR] Astrology ${tab}: API returned ${totalChars} chars across ${data.sections.length} sections`);
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
            <Text style={{ fontSize: 14, color: theme.accent }}>☉</Text>
            <Text style={[styles.placementSign, { color: theme.text }]}>{formatPlacement(placements.sun)}</Text>
          </View>
          <View style={[styles.placementDivider, { backgroundColor: theme.border }]} />
          <View style={styles.placementItem}>
            <Text style={{ fontSize: 14, color: theme.accent }}>☽</Text>
            <Text style={[styles.placementSign, { color: theme.text }]}>{formatPlacement(placements.moon)}</Text>
          </View>
          <View style={[styles.placementDivider, { backgroundColor: theme.border }]} />
          <View style={styles.placementItem}>
            <Text style={{ fontSize: 14, color: theme.accent }}>↑</Text>
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
        <Text style={{ fontSize: 28, color: theme.textTertiary }}>⚠</Text>
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
              <Text style={{ fontSize: 16, color: theme.textInverse }}>↻</Text>
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
      <View key={index} style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => {
            if (activeTab === 'deep_dive') {
              setExpandedSection(expandedSection === section.label ? null : section.label);
            }
          }}
          activeOpacity={activeTab === 'deep_dive' ? 0.7 : 1}
        >
          <Text style={[styles.sectionLabel, { color: theme.text }]}>{section.label}</Text>
          {activeTab === 'deep_dive' && (
            <Text style={{ fontSize: 16, color: theme.textTertiary }}>
              {isExpanded ? '▲' : '▼'}
            </Text>
          )}
        </TouchableOpacity>
        {isExpanded && (
          <>
            <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>{section.body}</Text>
            {/* Debug: Show section-level metrics */}
            <SectionDebug label={section.label} body={section.body} index={index} />
            {/* Reflect Button */}
            <InlineReflectButton
              source={{
                lens: 'astrology',
                type: section.label.toLowerCase().replace(/\s+/g, '_'),
                name: section.label,
                id: `astrology_${section.label.toLowerCase().replace(/\s+/g, '_')}`,
              }}
              prompt={`Reflect on ${section.label}: ${section.body.slice(0, 100)}...`}
            />
          </>
        )}
      </View>
    );
  };

  const renderNatalChartReference = () => {
    if (activeTab !== 'deep_dive') return null;

    return (
      <View style={[styles.chartReferenceCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.chartReferenceHeader}>
          <Text style={{ fontSize: 18, color: theme.textSecondary }}>📄</Text>
          <Text style={[styles.chartReferenceTitle, { color: theme.text }]}>Natal Chart (Reference)</Text>
        </View>
        <Text style={[styles.chartReferenceDisclaimer, { color: theme.textTertiary }]}>
          This chart shows structure, not meaning on its own.
        </Text>
        <TouchableOpacity
          style={[styles.chartButton, { backgroundColor: theme.surfaceLight }]}
          onPress={() => setShowChartModal(true)}
        >
          <Text style={{ fontSize: 14, color: theme.accent }}>⤢</Text>
          <Text style={[styles.chartButtonText, { color: theme.accent }]}>Open Full Chart (PDF)</Text>
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
        <View style={[styles.modalContent, { backgroundColor: theme.surface }]}>
          <TouchableOpacity
            style={styles.modalClose}
            onPress={() => setShowChartModal(false)}
          >
            <Text style={{ fontSize: 22, color: theme.textSecondary }}>✕</Text>
          </TouchableOpacity>
          
          <Text style={[styles.modalTitle, { color: theme.text }]}>Natal Chart Reference</Text>
          
          <View style={[styles.chartPlaceholder, { backgroundColor: theme.background }]}>
            <Text style={{ fontSize: 42, color: theme.textTertiary }}>☿</Text>
            <Text style={[styles.chartPlaceholderText, { color: theme.textSecondary }]}>
              Full chart visualization coming soon
            </Text>
          </View>
          
          <Text style={[styles.modalDisclaimer, { color: theme.textTertiary }]}>
            This chart shows structure, not meaning on its own.
            {'\n\n'}
            Patterns suggest tendencies, not guarantees.
            What in this structure feels recognisable to you?
          </Text>
        </View>
      </View>
    </Modal>
  );

  // v_next: Render 3-altitude snapshot for Today tab
  const render3AltitudeSnapshot = () => {
    if (!snapshotData) return null;

    // Get current altitude data
    const currentAltitude = snapshotData[activeAltitude];
    if (!currentAltitude) return null;

    // Get date display for current altitude
    const getDateDisplay = () => {
      switch (activeAltitude) {
        case 'today':
          return currentAltitude.date;
        case 'week':
          return currentAltitude.date_range;
        case 'month':
          return currentAltitude.month;
        default:
          return '';
      }
    };

    return (
      <View style={styles.snapshotContainer}>
        {/* Altitude Selector */}
        <View style={[styles.altitudeSelector, { backgroundColor: theme.surfaceLight }]}>
          <TouchableOpacity
            style={[
              styles.altitudeTab,
              activeAltitude === 'today' && [styles.altitudeTabActive, { backgroundColor: theme.surface }]
            ]}
            onPress={() => setActiveAltitude('today')}
          >
            <Text style={[
              styles.altitudeTabText,
              { color: activeAltitude === 'today' ? theme.text : theme.textTertiary }
            ]}>
              Today
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.altitudeTab,
              activeAltitude === 'week' && [styles.altitudeTabActive, { backgroundColor: theme.surface }]
            ]}
            onPress={() => setActiveAltitude('week')}
          >
            <Text style={[
              styles.altitudeTabText,
              { color: activeAltitude === 'week' ? theme.text : theme.textTertiary }
            ]}>
              This Week
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.altitudeTab,
              activeAltitude === 'month' && [styles.altitudeTabActive, { backgroundColor: theme.surface }]
            ]}
            onPress={() => setActiveAltitude('month')}
          >
            <Text style={[
              styles.altitudeTabText,
              { color: activeAltitude === 'month' ? theme.text : theme.textTertiary }
            ]}>
              This Month
            </Text>
          </TouchableOpacity>
        </View>

        {/* Date Display */}
        <Text style={[styles.altitudeDate, { color: theme.textTertiary }]}>
          {getDateDisplay()}
        </Text>

        {/* Bridge - what this altitude represents */}
        {currentAltitude.bridge && (
          <Text style={[styles.altitudeBridge, { color: theme.textSecondary }]}>
            {currentAltitude.bridge}
          </Text>
        )}

        {/* Narrative Card */}
        <View style={[styles.narrativeCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.narrativeText, { color: theme.text }]}>
            {currentAltitude.body}
          </Text>
        </View>

        {/* Technical Details Toggle */}
        {currentAltitude.technical && (currentAltitude.technical.transits || currentAltitude.technical.placements) && (
          <TouchableOpacity
            style={styles.technicalToggle}
            onPress={() => setExpandedSection(expandedSection === 'technical' ? null : 'technical')}
          >
            <Text style={[styles.technicalToggleText, { color: theme.textTertiary }]}>
              {expandedSection === 'technical' ? 'Hide' : 'See'} what's driving this
            </Text>
            <Text style={{ fontSize: 12, color: theme.textTertiary }}>
              {expandedSection === 'technical' ? '▲' : '▼'}
            </Text>
          </TouchableOpacity>
        )}

        {/* Technical Details (expanded) */}
        {expandedSection === 'technical' && currentAltitude.technical && (
          <View style={[styles.technicalCard, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
            {currentAltitude.technical.transits && currentAltitude.technical.transits.length > 0 && (
              <View style={styles.technicalRow}>
                <Text style={[styles.technicalLabel, { color: theme.textTertiary }]}>TRANSITS</Text>
                <Text style={[styles.technicalValue, { color: theme.textSecondary }]}>
                  {currentAltitude.technical.transits.join(' • ')}
                </Text>
              </View>
            )}
            {currentAltitude.technical.placements && currentAltitude.technical.placements.length > 0 && (
              <View style={styles.technicalRow}>
                <Text style={[styles.technicalLabel, { color: theme.textTertiary }]}>PLACEMENTS</Text>
                <Text style={[styles.technicalValue, { color: theme.textSecondary }]}>
                  {currentAltitude.technical.placements.join(' • ')}
                </Text>
              </View>
            )}
            {currentAltitude.technical.interaction_theme && (
              <View style={styles.technicalRow}>
                <Text style={[styles.technicalLabel, { color: theme.textTertiary }]}>THEME</Text>
                <Text style={[styles.technicalValue, { color: theme.textSecondary }]}>
                  {currentAltitude.technical.interaction_theme.replace(/_/g, ' ')}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Reflect Button */}
        <InlineReflectButton
          source={{
            lens: 'astrology',
            type: `snapshot_${activeAltitude}`,
            name: currentAltitude.title,
            id: `astrology_snapshot_${activeAltitude}`,
          }}
          prompt={`Reflect on ${currentAltitude.title}: ${currentAltitude.body.slice(0, 150)}...`}
        />
      </View>
    );
  };

  // Legacy: Render old narrative for fallback (deprecated)
  const renderTodayNarrative = () => {
    if (!data?.narrative) return null;

    return (
      <View style={styles.narrativeContainer}>
        {/* Single narrative card - no headers inside */}
        <View style={[styles.narrativeCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.narrativeText, { color: theme.text }]}>
            {data.narrative}
          </Text>
        </View>

        {/* Collapsible "See what's driving this" */}
        {data.technical && (data.technical.placements || data.technical.transits) && (
          <TouchableOpacity
            style={styles.technicalToggle}
            onPress={() => setExpandedSection(expandedSection === 'technical' ? null : 'technical')}
          >
            <Text style={[styles.technicalToggleText, { color: theme.textTertiary }]}>
              {expandedSection === 'technical' ? 'Hide' : 'See'} what's driving this
            </Text>
            <Text style={{ fontSize: 12, color: theme.textTertiary }}>
              {expandedSection === 'technical' ? '▲' : '▼'}
            </Text>
          </TouchableOpacity>
        )}

        {/* Technical details (hidden by default) */}
        {expandedSection === 'technical' && data.technical && (
          <View style={[styles.technicalCard, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
            {data.technical.placements && data.technical.placements.length > 0 && (
              <View style={styles.technicalRow}>
                <Text style={[styles.technicalLabel, { color: theme.textTertiary }]}>PLACEMENTS</Text>
                <Text style={[styles.technicalValue, { color: theme.textSecondary }]}>
                  {data.technical.placements.join(' • ')}
                </Text>
              </View>
            )}
            {data.technical.transits && data.technical.transits.length > 0 && (
              <View style={styles.technicalRow}>
                <Text style={[styles.technicalLabel, { color: theme.textTertiary }]}>TRANSITS</Text>
                <Text style={[styles.technicalValue, { color: theme.textSecondary }]}>
                  {data.technical.transits.join(' • ')}
                </Text>
              </View>
            )}
          </View>
        )}

        {/* Reflect button */}
        <InlineReflectButton
          source={{
            lens: 'astrology',
            type: 'today_narrative',
            name: 'Today',
            id: 'astrology_today_narrative',
          }}
          prompt={`Reflect on today: ${data.narrative.slice(0, 150)}...`}
        />
      </View>
    );
  };

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
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              {activeTab === 'deep_dive' 
                ? 'Generating your personalized reading...\nThis may take 30-45 seconds'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Text style={{ fontSize: 28, color: theme.textTertiary }}>⚠</Text>
            <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryButton, { backgroundColor: theme.surface }]}
              onPress={() => loadTabData(activeTab)}
            >
              <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
            </TouchableOpacity>
            {/* Still show core card on Deep Dive even with error */}
            {activeTab === 'deep_dive' && renderCorePlacements()}
          </View>
        ) : data ? (
          <>
            {/* Title - only show for non-Today tabs */}
            {activeTab !== 'today' && (
              <Text style={[styles.title, { color: theme.text }]}>{data.title || (activeTab === 'deep_dive' ? 'Your Core Structure' : 'Astrology')}</Text>
            )}

            {/* v_next: TODAY TAB - 3-altitude snapshot system */}
            {activeTab === 'today' && (
              <>
                {snapshotData ? (
                  render3AltitudeSnapshot()
                ) : data?.narrative ? (
                  /* Legacy fallback */
                  renderTodayNarrative()
                ) : (
                  /* Fallback when no data */
                  <View style={[styles.narrativeCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                    <Text style={[styles.narrativeText, { color: theme.textSecondary, fontStyle: 'italic' }]}>
                      Still forming…
                    </Text>
                  </View>
                )}
              </>
            )}

            {/* Core Placements Card (Deep Dive only) - always show even if success=false */}
            {activeTab === 'deep_dive' && renderCorePlacements()}

            {/* ERROR CARD: Show when Deep Dive computation failed */}
            {activeTab === 'deep_dive' && data.success === false && renderComputeErrorCard()}

            {/* Only show content sections if success !== false AND not today tab (today uses narrative) */}
            {data.success !== false && activeTab !== 'today' && (
              <>
                {/* Expand Button (Deep Dive only) */}
                {activeTab === 'deep_dive' && (
                  <TouchableOpacity
                    style={styles.expandButton}
                    onPress={() => setExpandedSection(expandedSection ? null : 'all')}
                  >
                    <Text style={[styles.expandButtonText, { color: theme.accent }]}>
                      {expandedSection ? 'Collapse sections' : 'Explore your core structure'}
                    </Text>
                    <Text style={{ fontSize: 14, color: theme.accent }}>
                      {expandedSection ? '⤡' : '⤢'}
                    </Text>
                  </TouchableOpacity>
                )}

                {/* Sections */}
                {data.sections?.map((section, index) => renderSection(section, index))}

                {/* Mirror Prompt */}
                {data.mirror_prompt && (
                  <View style={[styles.mirrorPromptCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
                    <Text style={[styles.mirrorPromptLabel, { color: theme.textTertiary }]}>REFLECT</Text>
                    <Text style={[styles.mirrorPromptText, { color: theme.text }]}>{data.mirror_prompt}</Text>
                  </View>
                )}

                {/* Natal Chart Reference (Deep Dive only) */}
                {renderNatalChartReference()}

                {/* Ask Mirror Button */}
                <TouchableOpacity
                  style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
                  onPress={onOpenChat}
                >
                  <Text style={{ fontSize: 16, color: theme.background }}>💬</Text>
                  <Text style={[styles.askMirrorText, { color: theme.background }]}>Ask about this lens</Text>
                </TouchableOpacity>

                {/* Footer */}
                <Text style={[styles.footer, { color: theme.textTertiary }]}>
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
  // v6 Narrative styles for Today tab
  narrativeContainer: {
    marginBottom: 20,
  },
  narrativeCard: {
    backgroundColor: 'transparent',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'transparent',
  },
  narrativeText: {
    fontSize: 16,
    lineHeight: 26,
    color: 'inherit',
  },
  technicalToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    marginBottom: 12,
  },
  technicalToggleText: {
    fontSize: 13,
    color: 'inherit',
  },
  technicalCard: {
    backgroundColor: 'transparent',
    borderRadius: 10,
    padding: 14,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'transparent',
  },
  technicalRow: {
    marginBottom: 10,
  },
  technicalLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    color: 'inherit',
    marginBottom: 4,
  },
  technicalValue: {
    fontSize: 13,
    lineHeight: 20,
    color: 'inherit',
  },
  // v_next: 3-altitude snapshot styles
  snapshotContainer: {
    flex: 1,
  },
  altitudeSelector: {
    flexDirection: 'row',
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
  },
  altitudeTab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  altitudeTabActive: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  altitudeTabText: {
    fontSize: 13,
    fontWeight: '500',
  },
  altitudeDate: {
    fontSize: 13,
    textAlign: 'center',
    marginBottom: 8,
  },
  altitudeBridge: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
    marginBottom: 16,
  },
});
