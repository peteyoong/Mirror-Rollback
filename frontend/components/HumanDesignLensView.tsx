import React, { useState, useEffect, useRef, useImperativeHandle, forwardRef, useMemo } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';
import { buildJournalPrefill, goToJournalWithPrefill, LENS_CONTINUATIONS } from '../utils/journalPrefill';
import TodayPanel from './TodayPanel';
import { hasKnownBirthTime, BIRTH_TIME_REQUIRED_MESSAGE } from '../utils/birthTimeUtils';

// Ref interface for imperative control
export interface LensViewRef {
  refetch: () => void;
}

interface HumanDesignSection {
  id: string;      // Stable identifier (e.g., "type", "strategy", "authority")
  label: string;   // Display label (can change without breaking expansion)
  body: string;
}

interface IncarnationCrossCanonical {
  canonical_key?: string;
  gates_key?: string;
  angle?: string;
  angle_full?: string;
  internal_name?: string;
  internal_label?: string;
  display_label?: string;
  vendor_labels?: {
    emergent?: string;
    genetic_matrix?: string;
    jovian_archive?: string;
  };
}

interface ActivationsCount {
  personality?: number;
  design?: number;
  total_unique_gates?: number;
}

interface HumanDesignData {
  title: string;
  sections: HumanDesignSection[];
  mirror_prompt: string;
  core_mechanics?: {
    type: string;
    strategy: string;
    authority: string;
    profile?: string;
    incarnation_cross?: string;
    incarnation_cross_gates?: string;
    incarnation_cross_canonical?: IncarnationCrossCanonical;
    activations_count?: ActivationsCount;
  };
  date?: string;
  // Debug fields from API
  debug_stamp?: {
    fallback_used?: boolean;
    source?: string;
    timestamp?: string;
    cached?: boolean;
  };
}

interface UserInfo {
  id: string;
  birth_time?: string | null;
  birth_time_known?: boolean | null;
}

interface Props {
  userId: string;
  user?: UserInfo;  // Optional user object for birth time checks
  onOpenChat: () => void;
}

type TabType = 'summary' | 'today' | 'deep_dive';

const HumanDesignLensView = forwardRef<LensViewRef, Props>(({ userId, onOpenChat }, ref) => {
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [data, setData] = useState<HumanDesignData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const [fetchStatus, setFetchStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [showSiderealInfo, setShowSiderealInfo] = useState(false);
  
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
        console.log(`[HD_LENS_DEBUG] refetch() called via ref - preserving UI state`);
      }
      loadTabData(activeTab);
    }
  }), [activeTab]);

  useEffect(() => {
    if (isDebug || __DEV__) {
      console.log(`[HD_LENS_DEBUG] Component mounted/updated - userId: ${userId}, activeTab: ${activeTab}`);
    }
    loadTabData(activeTab);
  }, [activeTab, userId]);

  const loadTabData = async (tab: TabType) => {
    // Increment request ID to track this specific request
    const requestId = ++requestIdRef.current;
    
    if (isDebug || __DEV__) {
      console.log(`[HD_LENS_DEBUG] Starting fetch for tab: ${tab} (requestId: ${requestId})`);
    }
    
    setIsLoading(true);
    setError(null);
    setFetchStatus('loading');

    try {
      const endpoint = tab === 'today' 
        ? `/human-design/today/${userId}`
        : tab === 'deep_dive'
        ? `/human-design/deep-dive/${userId}`
        : `/human-design/summary/${userId}`;

      console.log(`[HD_DEBUG] Loading tab: ${tab}, endpoint: ${endpoint}`);
      
      const response = await api.get(endpoint);
      
      // VERIFICATION LOGS - Task requirement
      console.log(`[HD_DEBUG] ========== DATA SOURCE VERIFICATION ==========`);
      console.log(`[HD_DEBUG] Active Tab: ${tab}`);
      console.log(`[HD_DEBUG] Endpoint Called: ${endpoint}`);
      console.log(`[HD_DEBUG] Full lens object keys:`, Object.keys(response.data || {}));
      console.log(`[HD_DEBUG] Has sections:`, !!response.data?.sections);
      console.log(`[HD_DEBUG] Sections count:`, response.data?.sections?.length || 0);
      
      if (response.data?.sections?.[0]) {
        const energySection = response.data.sections.find((s: any) => 
          s.label?.toLowerCase().includes('energy') || s.label?.toLowerCase().includes('pattern')
        );
        if (energySection) {
          console.log(`[HD_DEBUG] Energy pattern section length: ${energySection.body?.length || 0} chars`);
          console.log(`[HD_DEBUG] Energy pattern preview: ${energySection.body?.substring(0, 100)}...`);
        }
      }
      
      // Log total content length
      const totalChars = response.data?.sections?.reduce(
        (sum: number, s: HumanDesignSection) => sum + (s.body?.length || 0), 
        0
      ) || 0;
      console.log(`[HD_DEBUG] Total content chars: ${totalChars}`);
      console.log(`[HD_DEBUG] ================================================`);
      
      // STALE RESPONSE GUARD: Ignore if a newer request was made
      if (requestId !== requestIdRef.current) {
        if (isDebug || __DEV__) {
          console.log(`[HD_LENS_DEBUG] Ignoring stale response (requestId: ${requestId}, current: ${requestIdRef.current})`);
        }
        return;
      }
      
      setData(response.data);
      setFetchStatus('success');
      setLastUpdated(new Date().toISOString());
      
      if (isDebug || __DEV__) {
        console.log(`[HD_LENS_DEBUG] Fetch SUCCESS - sections: ${response.data?.sections?.length || 0}, chars: ${totalChars}`);
      }
      
      // Debug: Calculate raw data length for comparison
      if (isDebugEnabled() && response.data?.sections) {
        setRawDataLength(totalChars);
        console.log(`[DEBUG_MIRROR] HumanDesign ${tab}: API returned ${totalChars} chars across ${response.data.sections.length} sections`);
      }
    } catch (err: any) {
      // STALE RESPONSE GUARD: Ignore errors from stale requests
      if (requestId !== requestIdRef.current) {
        if (isDebug || __DEV__) {
          console.log(`[HD_LENS_DEBUG] Ignoring error from stale request (requestId: ${requestId})`);
        }
        return;
      }
      
      console.error(`Human Design ${tab} error:`, err);
      setError('Unable to load this view right now.');
      setFetchStatus('error');
      
      if (isDebug || __DEV__) {
        console.log(`[HD_LENS_DEBUG] Fetch ERROR: ${err?.message || 'Unknown error'}`);
      }
    } finally {
      // Only update loading state if this is still the current request
      if (requestId === requestIdRef.current) {
        setIsLoading(false);
      }
    }
  };
  
  // Debug panel (only with ?debug=1)
  const renderDebugPanel = () => {
    if (!isDebug) return null;
    
    return (
      <View style={styles.debugPanel}>
        <Text style={styles.debugTitle}>🔍 Human Design Lens Debug</Text>
        <Text style={styles.debugText}>userId: {userId}</Text>
        <Text style={styles.debugText}>activeTab: {activeTab}</Text>
        <Text style={styles.debugText}>fetchStatus: {fetchStatus}</Text>
        <Text style={styles.debugText}>isLoading: {isLoading ? 'Yes' : 'No'}</Text>
        <Text style={styles.debugText}>error: {error || 'None'}</Text>
        <Text style={styles.debugText}>data present: {data ? '✓' : '❌'}</Text>
        <Text style={styles.debugText}>sections: {data?.sections?.length || 0}</Text>
        <Text style={styles.debugText}>mechanics: {data?.core_mechanics ? '✓' : '❌'}</Text>
        <Text style={styles.debugText}>lastUpdated: {lastUpdated || 'Never'}</Text>
      </View>
    );
  };
  
  // Fallback UI when data is missing (not loading, not error, just no data)
  const renderEmptyFallback = () => {
    if (isDebug || __DEV__) {
      console.log(`[HD_LENS_DEBUG] Rendering empty fallback - data is null/undefined`);
    }
    
    return (
      <View style={styles.emptyFallbackContainer}>
        <Ionicons name="sync-outline" size={48} color={Colors.textTertiary} />
        <Text style={styles.emptyFallbackTitle}>Loading your Human Design...</Text>
        <Text style={styles.emptyFallbackText}>
          This lens is still loading — pull to refresh or tap retry.
        </Text>
        <TouchableOpacity
          style={styles.retryButton}
          onPress={() => loadTabData(activeTab)}
        >
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
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

  // Always render core mechanics for deep dive, even with fallback values
  const renderCoreMechanics = () => {
    // Default fallback if no data
    const mechanics = data?.core_mechanics || {
      type: 'Unknown',
      strategy: 'Unknown',
      authority: 'Unknown',
      profile: 'Unknown',
      incarnation_cross: 'Unknown',
      incarnation_cross_gates: null,
      incarnation_cross_canonical: null,
      activations_count: null
    };

    // Helper to format unknown gracefully
    const formatMechanic = (value: string | undefined | null) => {
      if (!value || value === 'Unknown') return '—';
      // For authority, take first part if it contains slash
      return value.split('/')[0];
    };

    // Format incarnation cross - include angle (LAX/RAX/JX) if available
    const formatCross = () => {
      const canonical = mechanics.incarnation_cross_canonical;
      
      // Priority 1: Use canonical with angle prepended
      if (canonical?.display_label) {
        // If angle exists, prepend it: "LAX Migration (37/40 - 5/35)"
        if (canonical.angle) {
          return `${canonical.angle} ${canonical.display_label}`;
        }
        return canonical.display_label;
      }
      
      // Priority 2: Use incarnation_cross field directly (already formatted by backend)
      if (mechanics.incarnation_cross && mechanics.incarnation_cross !== 'Unknown') {
        // Try to prepend angle if available
        if (canonical?.angle) {
          return `${canonical.angle} ${mechanics.incarnation_cross}`;
        }
        return mechanics.incarnation_cross;
      }
      
      return '—';
    };

    const getCrossGates = () => {
      // If we have canonical structure with gates_key, use it
      if (mechanics.incarnation_cross_canonical?.gates_key) {
        return mechanics.incarnation_cross_canonical.gates_key.replace('|', ' • ');
      }
      return mechanics.incarnation_cross_gates || '—';
    };

    // Check if cross display already includes gates (display_label format)
    const crossDisplay = formatCross();
    const showGatesSeparately = !crossDisplay.includes('(') && !crossDisplay.includes('•');

    return (
      <View style={styles.coreMechanicsCard}>
        <Text style={styles.coreMechanicsTitle}>CORE MECHANICS</Text>
        
        {/* Row 1: Type + Authority */}
        <View style={styles.mechanicsGrid}>
          <View style={styles.mechanicItem}>
            <Ionicons name="flash-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Type</Text>
            <Text style={styles.mechanicValue}>{formatMechanic(mechanics.type)}</Text>
          </View>
          <View style={styles.mechanicDivider} />
          <View style={styles.mechanicItem}>
            <Ionicons name="compass-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Authority</Text>
            <Text style={styles.mechanicValue}>{formatMechanic(mechanics.authority)}</Text>
          </View>
        </View>
        
        {/* Row 2: Profile + Incarnation Cross */}
        <View style={[styles.mechanicsGrid, { marginTop: 16 }]}>
          <View style={styles.mechanicItem}>
            <Ionicons name="person-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Profile</Text>
            <Text style={styles.mechanicValue}>{mechanics.profile || '—'}</Text>
          </View>
          <View style={styles.mechanicDivider} />
          <View style={styles.mechanicItem}>
            <Ionicons name="git-branch-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Incarnation Cross</Text>
            <Text style={[styles.mechanicValue, styles.mechanicValueSmall]}>{crossDisplay}</Text>
            {showGatesSeparately && (
              <Text style={styles.mechanicGates}>{getCrossGates()}</Text>
            )}
          </View>
        </View>
        
        {/* Debug Panel - only visible when DEBUG_MIRROR is enabled */}
        {isDebugEnabled() && mechanics.incarnation_cross_canonical && (
          <View style={styles.debugPanel}>
            <Text style={styles.debugPanelTitle}>🔧 HD DEBUG (Parity Verification)</Text>
            
            {/* Activation Counts */}
            {mechanics.activations_count && (
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>Activations:</Text>
                <Text style={styles.debugValue}>
                  P: {mechanics.activations_count.personality || 0}/13 | D: {mechanics.activations_count.design || 0}/13
                </Text>
              </View>
            )}
            
            {/* Canonical Key */}
            <View style={styles.debugRow}>
              <Text style={styles.debugLabel}>Canonical Key:</Text>
              <Text style={styles.debugValue}>{mechanics.incarnation_cross_canonical.canonical_key || '—'}</Text>
            </View>
            
            {/* Gates Key */}
            <View style={styles.debugRow}>
              <Text style={styles.debugLabel}>Gates Key:</Text>
              <Text style={styles.debugValue}>{mechanics.incarnation_cross_canonical.gates_key || '—'}</Text>
            </View>
            
            {/* Angle */}
            <View style={styles.debugRow}>
              <Text style={styles.debugLabel}>Angle:</Text>
              <Text style={styles.debugValue}>{mechanics.incarnation_cross_canonical.angle || '—'}</Text>
            </View>
            
            {/* Vendor Labels */}
            {mechanics.incarnation_cross_canonical.vendor_labels && (
              <>
                <Text style={[styles.debugLabel, { marginTop: 8 }]}>Vendor Labels:</Text>
                <View style={styles.debugRow}>
                  <Text style={styles.debugLabel}>  Emergent:</Text>
                  <Text style={styles.debugValue}>{mechanics.incarnation_cross_canonical.vendor_labels.emergent || '—'}</Text>
                </View>
                <View style={styles.debugRow}>
                  <Text style={styles.debugLabel}>  Genetic Matrix:</Text>
                  <Text style={styles.debugValue}>{mechanics.incarnation_cross_canonical.vendor_labels.genetic_matrix || '—'}</Text>
                </View>
              </>
            )}
          </View>
        )}
      </View>
    );
  };

  const renderSection = (section: HumanDesignSection, index: number) => {
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

  // Map API sections to TodayPanel props for Human Design
  // Mapping: "Today's Focus" → Tone, "A Small Experiment" → Small Experiment, "What to Notice" → What to Notice
  const mapSectionsToTodayPanel = useMemo(() => {
    if (!data?.sections || activeTab !== 'today') return null;
    
    let toneText: string | undefined;
    let experimentText: string | undefined;
    let noticeText: string | undefined;
    let noticeBullets: string[] | undefined;
    
    for (const section of data.sections) {
      const label = section.label?.toLowerCase() || '';
      
      // Map "Today's Focus" → Tone
      if (label.includes('focus') || label.includes('tone')) {
        toneText = section.body;
      }
      // Map "A Small Experiment" → Small Experiment  
      else if (label.includes('experiment')) {
        experimentText = section.body;
      }
      // Map "What to Notice" → What to Notice
      else if (label.includes('notice')) {
        const body = section.body || '';
        // Check if content looks like bullets
        if (body.includes('•') || body.includes('\n-') || body.includes('\n•')) {
          noticeBullets = body
            .split(/\n/)
            .map(line => line.replace(/^[•\-]\s*/, '').trim())
            .filter(line => line.length > 0);
        } else {
          noticeText = body;
        }
      }
    }
    
    return {
      toneText,
      experimentText,
      noticeText,
      noticeBullets,
      reflectQuestion: data.mirror_prompt,
    };
  }, [data, activeTab]);

  return (
    <View style={styles.container}>
      {/* Debug Panel (only with ?debug=1) */}
      {renderDebugPanel()}
      
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
          </View>
        ) : data ? (
          <>
            {/* Title */}
            <Text style={styles.title}>
              {data.title || 'Human Design'}
            </Text>

            {/* Sidereal Framework Qualifier (Overview tab only) */}
            {activeTab === 'summary' && (
              <View style={styles.siderealQualifier}>
                <Text style={styles.siderealText}>
                  Based on a True Sidereal astronomical reference frame.
                </Text>
                <TouchableOpacity
                  onPress={() => setShowSiderealInfo(!showSiderealInfo)}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                  <Ionicons
                    name={showSiderealInfo ? 'close-circle-outline' : 'information-circle-outline'}
                    size={14}
                    color={Colors.textTertiary}
                  />
                </TouchableOpacity>
              </View>
            )}
            
            {/* Sidereal Info Tooltip */}
            {activeTab === 'summary' && showSiderealInfo && (
              <View style={styles.siderealTooltip}>
                <Text style={styles.siderealTooltipText}>
                  Many systems use the Tropical zodiac, aligned to seasonal points of the year.{'\n\n'}Mirror calculates planetary positions relative to the observable constellations using a True Sidereal reference frame before deriving gates and activations.
                </Text>
              </View>
            )}

            {/* TODAY TAB: Use standardized TodayPanel */}
            {activeTab === 'today' && mapSectionsToTodayPanel && (
              <TodayPanel
                date={data.date}
                toneText={mapSectionsToTodayPanel.toneText}
                experimentText={mapSectionsToTodayPanel.experimentText}
                noticeText={mapSectionsToTodayPanel.noticeText}
                noticeBullets={mapSectionsToTodayPanel.noticeBullets}
                reflectQuestion={mapSectionsToTodayPanel.reflectQuestion}
                onSaveToJournal={() => {
                  const prefill = buildJournalPrefill(data.mirror_prompt || '', LENS_CONTINUATIONS.human_design);
                  goToJournalWithPrefill(router, prefill, 'human_design');
                }}
              />
            )}

            {/* Core Mechanics Card (Summary and Deep Dive only) */}
            {(activeTab === 'summary' || activeTab === 'deep_dive') && renderCoreMechanics()}

            {/* Expand Button (Deep Dive only) */}
            {activeTab === 'deep_dive' && (
              <TouchableOpacity
                style={styles.expandButton}
                onPress={() => setExpandedSection(expandedSection ? null : 'all')}
              >
                <Text style={styles.expandButtonText}>
                  {expandedSection ? 'Collapse sections' : 'Explore your mechanics'}
                </Text>
                <Ionicons
                  name={expandedSection ? 'contract-outline' : 'expand-outline'}
                  size={16}
                  color={Colors.accent}
                />
              </TouchableOpacity>
            )}

            {/* Sections (Overview and Deep Dive only) */}
            {activeTab !== 'today' && data.sections.map((section, index) => renderSection(section, index))}

            {/* Mirror Prompt (Overview and Deep Dive only) */}
            {activeTab !== 'today' && data.mirror_prompt && (
              <View style={styles.mirrorPromptCard}>
                <Text style={styles.mirrorPromptLabel}>EXPERIMENT</Text>
                <Text style={styles.mirrorPromptText}>{data.mirror_prompt}</Text>
                <TouchableOpacity
                  style={styles.journalCTA}
                  onPress={() => {
                    const prefill = buildJournalPrefill(data.mirror_prompt, LENS_CONTINUATIONS.human_design);
                    goToJournalWithPrefill(router, prefill, 'human_design');
                  }}
                >
                  <Ionicons name="create-outline" size={16} color={Colors.accent} />
                  <Text style={styles.journalCTAText}>Write in Journal</Text>
                </TouchableOpacity>
              </View>
            )}

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
              A lens for understanding energy patterns, not a definition of who you are.
            </Text>
            
            {/* Debug Footer - only shows when DEBUG_MIRROR is enabled */}
            {activeTab === 'deep_dive' && data.sections && (
              <DebugFooter 
                lens="Human Design"
                sections={data.sections}
                source={data.debug_stamp?.source}
                rawDataLength={rawDataLength}
                debugStamp={data.debug_stamp}
              />
            )}
          </>
        ) : (
          // FALLBACK: No data, not loading, no error - show retry UI
          renderEmptyFallback()
        )}
      </ScrollView>
    </View>
  );
});

// Set display name for debugging
HumanDesignLensView.displayName = 'HumanDesignLensView';

export default HumanDesignLensView;

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
  siderealQualifier: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 16,
  },
  siderealText: {
    fontSize: 11,
    color: Colors.textTertiary,
    opacity: 0.8,
    letterSpacing: 0.2,
  },
  siderealTooltip: {
    backgroundColor: Colors.surface,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  siderealTooltipText: {
    fontSize: 12,
    lineHeight: 18,
    color: Colors.textSecondary,
  },
  dateLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 20,
  },
  coreMechanicsCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  coreMechanicsTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 16,
  },
  mechanicsGrid: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mechanicItem: {
    alignItems: 'center',
    paddingHorizontal: 16,
    gap: 4,
  },
  mechanicLabel: {
    fontSize: 10,
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  mechanicValue: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
  },
  mechanicValueSmall: {
    fontSize: 12,
    lineHeight: 16,
  },
  mechanicGates: {
    fontSize: 11,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: 2,
  },
  mechanicDivider: {
    width: 1,
    height: 40,
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
  // Debug Panel Styles (HD Parity Verification)
  debugPanel: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 8,
    padding: 12,
    marginHorizontal: -4,
  },
  debugPanelTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  debugRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 2,
  },
  debugLabel: {
    fontSize: 10,
    color: '#6B5A28',
    fontFamily: 'monospace',
  },
  debugValue: {
    fontSize: 10,
    color: '#4A4A4A',
    fontFamily: 'monospace',
    fontWeight: '500',
  },
  // Debug Panel for Lens Diagnostics
  debugTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#8B6914',
    marginBottom: 8,
  },
  debugText: {
    fontSize: 11,
    color: '#6B5A28',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  // Empty Fallback UI
  emptyFallbackContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 24,
  },
  emptyFallbackTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptyFallbackText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 20,
  },
});
