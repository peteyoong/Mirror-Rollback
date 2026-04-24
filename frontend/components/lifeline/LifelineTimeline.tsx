/**
 * LifelineTimeline
 * 
 * Main Lifeline component that displays the full timeline.
 * Designed to be reusable in both Life Lens and Forum contexts.
 * 
 * Usage:
 * <LifelineTimeline userId="xxx" />
 * <LifelineTimeline userId="xxx" forumId="yyy" /> // Forum context
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { Colors } from '../../constants/colors';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';
import LifelineEventCard, { LifelineEvent } from './LifelineEventCard';
import LifelineEmptyState from './LifelineEmptyState';
import LifelineInlineOnboarding from './LifelineInlineOnboarding';
import LifelineEventEditor from './LifelineEventEditor';
import LifelinePatterns, { LifelinePatternsData } from './LifelinePatterns';
import LifelinePatternSynthesisCard from './LifelinePatternSynthesisCard';
import LifelineGapPrompt, { GapPromptData } from './LifelineGapPrompt';
import LifelineMemoryPrompt, { 
  MemoryPrompt, 
  generatePromptQueue,
  generateGapPrompt,
} from './LifelineMemoryPrompt';
import TimeDistanceTimeline from './TimeDistanceTimeline';
import { ChartResonance, ChartResonanceSection, PatternResonanceSummary } from './ChartResonance';
import LifelineAddMenu from './LifelineAddMenu';
import LifelineFramingCard from './LifelineFramingCard';
import LifelineMiniMap from './LifelineMiniMap';
import LifelineStarterPrompts from './LifelineStarterPrompts';

interface Props {
  userId: string;
  forumId?: string;  // For future Forum reuse
  isCompact?: boolean;
  maxEvents?: number;
  /**
   * When this prop changes (via bumped `key`), the LifelineTimeline opens
   * the Add Event editor with the provided prefill. Used by the Phase
   * Timeline "Add that moment" CTA.
   */
  externalAddRequest?: {
    key: number;
    suggestedCategory?: string | null;
    source?: string;
  } | null;
}

interface LifelineResponse {
  success: boolean;
  user_id: string;
  event_count: number;
  events: LifelineEvent[];
  statistics: {
    categories_used: string[];
    tone_distribution: Record<string, number>;
    year_range: { min: number; max: number } | null;
  };
}

interface ExtendedPatternsData extends LifelinePatternsData {
  missing_periods?: GapPromptData[];
}

interface LifelineSummaryResponse {
  success: boolean;
  user_id: string;
  has_lifeline: boolean;
  event_count: number;
  patterns: ExtendedPatternsData;
}

export default function LifelineTimeline({ userId, forumId, isCompact = false, maxEvents, externalAddRequest }: Props) {
  const { theme } = useTheme();
  const router = useRouter();
  const scrollViewRef = useRef<ScrollView>(null);
  
  // Data state
  const [events, setEvents] = useState<LifelineEvent[]>([]);
  const [statistics, setStatistics] = useState<LifelineResponse['statistics'] | null>(null);
  const [patterns, setPatterns] = useState<ExtendedPatternsData | null>(null);
  const [missingPeriods, setMissingPeriods] = useState<GapPromptData[]>([]);
  const [dismissedGaps, setDismissedGaps] = useState<Set<string>>(new Set());
  const [birthYear, setBirthYear] = useState<number | null>(null);
  
  // Year-based scroll positions for mini-map navigation
  const [yearPositions, setYearPositions] = useState<Record<number, number>>({});
  const [headerHeight, setHeaderHeight] = useState(0);
  
  // Highlighted year for visual feedback after jump
  const [highlightedYear, setHighlightedYear] = useState<number | null>(null);
  
  // Memory prompt state
  const [memoryPromptQueue, setMemoryPromptQueue] = useState<MemoryPrompt[]>([]);
  const [dismissedPrompts, setDismissedPrompts] = useState<Set<string>>(new Set());
  const [currentPromptIndex, setCurrentPromptIndex] = useState(0);
  
  // Chart resonance state
  const [resonanceMap, setResonanceMap] = useState<Record<string, ChartResonance[]>>({});
  const [resonanceSummary, setResonanceSummary] = useState<PatternResonanceSummary[]>([]);
  
  // UI state
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Add menu state
  const [showAddMenu, setShowAddMenu] = useState(false);
  const [importSourceCount, setImportSourceCount] = useState(0);
  
  // Editor state
  const [showEditor, setShowEditor] = useState(false);
  const [editingEvent, setEditingEvent] = useState<LifelineEvent | null>(null);
  const [prefillYear, setPrefillYear] = useState<number | null>(null);
  const [prefillDescription, setPrefillDescription] = useState<string | null>(null);
  const [prefillCategory, setPrefillCategory] = useState<string | null>(null);

  // Toast state for progression feedback
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastOpacity] = useState(new Animated.Value(0));

  // Show toast with auto-hide
  const showToast = (message: string) => {
    setToastMessage(message);
    Animated.sequence([
      Animated.timing(toastOpacity, { toValue: 1, duration: 300, useNativeDriver: true }),
      Animated.delay(3000),
      Animated.timing(toastOpacity, { toValue: 0, duration: 300, useNativeDriver: true }),
    ]).start(() => setToastMessage(null));
  };
  
  // Scroll to a specific year in the timeline
  const scrollToYear = useCallback((year: number) => {
    console.log('==== SCROLL TO YEAR DEBUG ====');
    console.log('[Lifeline] scrollToYear called with year:', year, 'type:', typeof year);
    console.log('[Lifeline] yearPositions keys:', Object.keys(yearPositions));
    console.log('[Lifeline] yearPositions full:', JSON.stringify(yearPositions));
    console.log('[Lifeline] headerHeight:', headerHeight);
    
    // Find exact year or closest year with events
    let targetYear = year;
    let usedFallback = false;
    
    if (yearPositions[year] === undefined) {
      console.log('[Lifeline] Exact year', year, 'not found in positions');
      const years = Object.keys(yearPositions).map(Number).sort((a, b) => a - b);
      console.log('[Lifeline] Available years (sorted):', years);
      
      if (years.length === 0) {
        console.log('[Lifeline] ERROR: No year positions available yet');
        showToast(`Looking for ${year}...`);
        return;
      }
      
      targetYear = years.reduce((prev, curr) => 
        Math.abs(curr - year) < Math.abs(prev - year) ? curr : prev
      );
      usedFallback = true;
      console.log('[Lifeline] FALLBACK: Using closest year:', targetYear, 'instead of', year);
    }
    
    const targetY = yearPositions[targetYear];
    console.log('[Lifeline] Target year:', targetYear, 'has Y position:', targetY);
    
    if (targetY !== undefined) {
      // Calculate scroll position: event Y position + header offset - some margin from top
      const scrollOffset = targetY + headerHeight - 150;
      console.log('[Lifeline] Final scroll calculation:');
      console.log('  - Event Y:', targetY);
      console.log('  - Header height:', headerHeight);
      console.log('  - Offset (-150):', -150);
      console.log('  - Final scrollTo Y:', Math.max(0, scrollOffset));
      
      scrollViewRef.current?.scrollTo({ 
        y: Math.max(0, scrollOffset),
        animated: true 
      });
      
      // Highlight the target year for visual feedback
      setHighlightedYear(targetYear);
      showToast(`Jumped to ${targetYear}${usedFallback ? ' (nearest)' : ''}`);
      setTimeout(() => setHighlightedYear(null), 2500);
    } else {
      console.log('[Lifeline] ERROR: No position found for target year:', targetYear);
    }
    console.log('==== END SCROLL DEBUG ====');
  }, [yearPositions, headerHeight]);
  
  // Handle gap press from mini-map
  const handleGapPressFromMap = useCallback((gap: GapPromptData) => {
    console.log('[Lifeline] Gap pressed:', gap.start_year, '-', gap.end_year);
    scrollToYear(gap.start_year);
  }, [scrollToYear]);
  
  // Track event card positions for scroll navigation
  // The Y position from onLayout is relative to the parent, we need cumulative position
  const handleEventLayout = useCallback((year: number, y: number) => {
    console.log('[Lifeline] handleEventLayout called - year:', year, 'y:', y);
    setYearPositions(prev => {
      // Only store the first event of each year (lowest position)
      // This ensures we scroll to the top of a year's events
      if (prev[year] === undefined || y < prev[year]) {
        console.log('[Lifeline] Storing position for year:', year, 'Y:', y, prev[year] ? '(replacing)' : '(new)');
        return { ...prev, [year]: y };
      }
      console.log('[Lifeline] Skipping position for year:', year, 'Y:', y, '(existing:', prev[year], ')');
      return prev;
    });
  }, []);
  
  // Track header height for accurate scroll calculation
  const handleHeaderLayout = useCallback((e: any) => {
    const height = e.nativeEvent.layout.height;
    if (Math.abs(height - headerHeight) > 10) {
      console.log('[Lifeline] Header height updated:', height);
      setHeaderHeight(height);
    }
  }, [headerHeight]);

  // Load timeline data and patterns
  const loadTimeline = useCallback(async (refresh = false) => {
    if (refresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    console.log('[Lifeline] ======= DEBUG: Loading timeline =======');
    console.log('[Lifeline] Loading all data for user:', userId, 'refresh:', refresh);
    console.log('[Lifeline] userId type:', typeof userId, 'length:', userId?.length);

    try {
      // Fetch events, summary (with patterns), resonances, import stats, and user profile in parallel
      const [eventsRes, summaryRes, resonancesRes, importStatsRes, userRes] = await Promise.all([
        api.get<LifelineResponse>(`/lifeline/${userId}`),
        api.get<LifelineSummaryResponse>(`/lifeline/${userId}/summary`),
        api.get<{
          success: boolean;
          resonance_map: Record<string, ChartResonance[]>;
          pattern_summary: PatternResonanceSummary[];
        }>(`/lifeline/${userId}/resonances`).catch(() => ({ data: { success: false, resonance_map: {}, pattern_summary: [] } })),
        api.get(`/lifeline/ingestion-stats/${userId}`).catch(() => ({ data: { import_sources: 0 } })),
        api.get(`/users/${userId}`).catch(() => ({ data: null })),
      ]);
      
      console.log('[Lifeline] API response - events count:', eventsRes.data?.events?.length || 0);
      console.log('[Lifeline] API response - success:', eventsRes.data?.success);
      
      if (eventsRes.data.success) {
        let loadedEvents = eventsRes.data.events || [];
        if (maxEvents) {
          loadedEvents = loadedEvents.slice(0, maxEvents);
        }
        setEvents(loadedEvents);
        setStatistics(eventsRes.data.statistics);
        console.log('[Lifeline] Loaded', loadedEvents.length, 'canonical events');
      }
      
      // Extract birth year from user profile
      if (userRes.data?.birth_date) {
        const birthYearFromProfile = parseInt(userRes.data.birth_date.substring(0, 4), 10);
        if (!isNaN(birthYearFromProfile)) {
          setBirthYear(birthYearFromProfile);
          console.log('[Lifeline] Birth year:', birthYearFromProfile);
        }
      }
      
      if (summaryRes.data.success && summaryRes.data.patterns) {
        setPatterns(summaryRes.data.patterns);
        // Store missing periods for gap prompts
        if (summaryRes.data.patterns.missing_periods) {
          setMissingPeriods(summaryRes.data.patterns.missing_periods);
        }
        console.log('[Lifeline] Loaded patterns with', summaryRes.data.patterns.intense_periods?.length || 0, 'intense periods');
      }
      
      // Store resonance data - important: this must refresh after deletes/edits
      if (resonancesRes.data.success) {
        const resonanceMapData = resonancesRes.data.resonance_map || {};
        const patternSummaryData = resonancesRes.data.pattern_summary || [];
        setResonanceMap(resonanceMapData);
        setResonanceSummary(patternSummaryData);
        console.log('[Lifeline] Loaded resonances:', Object.keys(resonanceMapData).length, 'event mappings,', patternSummaryData.length, 'pattern summaries');
      }
      
      // Store import source count
      if (importStatsRes.data) {
        setImportSourceCount(importStatsRes.data.import_sources || 0);
      }
    } catch (err: any) {
      console.error('[Lifeline] Load error:', err);
      setError('Unable to load your lifeline right now.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [userId, maxEvents]);

  useEffect(() => {
    loadTimeline();
  }, [loadTimeline]);

  // Track if this is the first focus to avoid double loading
  const isFirstFocus = useRef(true);

  // Refresh all data when screen comes into focus (but not on initial mount)
  // This ensures resonances, patterns, and timeline update after imports/navigation
  useFocusEffect(
    useCallback(() => {
      if (isFirstFocus.current) {
        isFirstFocus.current = false;
        console.log('[Lifeline] Initial focus - skipping redundant refresh');
        return;
      }
      console.log('[Lifeline] Screen refocused - refreshing all data');
      loadTimeline(true); // Force refresh on subsequent focus
    }, [loadTimeline])
  );

  // Save event (create or update)
  const handleSaveEvent = async (eventData: Partial<LifelineEvent>) => {
    const isNewEvent = !eventData.id;
    if (eventData.id) {
      // Update existing
      await api.put(`/lifeline/event/${eventData.id}`, eventData);
    } else {
      // Create new
      await api.post('/lifeline/event', {
        ...eventData,
        user_id: userId,
      });
    }
    await loadTimeline();
    
    // Show progression feedback toast for new events
    if (isNewEvent) {
      showToast("Added. Over time, patterns will start to emerge.");
    }
  };

  // Delete event with proper cleanup and refresh
  const handleDeleteEvent = async (eventId: string) => {
    console.log('[Lifeline] Deleting event:', eventId);
    try {
      const response = await api.delete(`/lifeline/event/${eventId}`);
      console.log('[Lifeline] Delete response:', response.data);
      
      if (response.data.success) {
        // Close the editor modal first
        setShowEditor(false);
        setEditingEvent(null);
        
        // Refresh all lifeline data (events, patterns, resonances, stats)
        console.log('[Lifeline] Delete successful, refreshing all data...');
        await loadTimeline(true);
      } else {
        throw new Error(response.data.message || 'Delete failed');
      }
    } catch (err: any) {
      console.error('[Lifeline] Delete error:', err);
      throw err; // Re-throw so the editor can show error
    }
  };

  // Open editor for new event
  const handleAddEvent = () => {
    setEditingEvent(null);
    setPrefillYear(null);
    setShowEditor(true);
  };

  // External trigger — Phase Timeline "Add that moment" CTA.
  // Opens the editor with a suggested category prefilled.
  useEffect(() => {
    if (!externalAddRequest || !externalAddRequest.key) return;
    setEditingEvent(null);
    setPrefillYear(null);
    setPrefillDescription(null);
    setPrefillCategory(externalAddRequest.suggestedCategory || null);
    setShowEditor(true);
  }, [externalAddRequest?.key]); // eslint-disable-line react-hooks/exhaustive-deps

  // Open editor with prefilled year (for gap prompts)
  const handleAddFromGap = (startYear: number, endYear: number) => {
    setEditingEvent(null);
    // Use the middle year of the gap range as prefill
    const middleYear = Math.round((startYear + endYear) / 2);
    setPrefillYear(middleYear);
    setShowEditor(true);
  };

  // Dismiss a gap prompt
  const handleDismissGap = (gap: GapPromptData) => {
    const gapKey = `${gap.start_year}-${gap.end_year}`;
    setDismissedGaps(prev => new Set([...prev, gapKey]));
  };

  // Get non-dismissed gaps
  const visibleGaps = missingPeriods.filter(gap => {
    const gapKey = `${gap.start_year}-${gap.end_year}`;
    return !dismissedGaps.has(gapKey);
  });

  // Generate memory prompts when we have events
  useEffect(() => {
    if (events.length >= 2 && patterns) {
      const prompts = generatePromptQueue(events, patterns);
      setMemoryPromptQueue(prompts);
    }
  }, [events, patterns]);

  // Get the current visible memory prompt
  const currentMemoryPrompt = memoryPromptQueue.find(
    (p, idx) => !dismissedPrompts.has(p.id) && idx >= currentPromptIndex
  );

  // Handle "Add this moment" from memory prompt
  const handleAddFromMemoryPrompt = (prompt: MemoryPrompt) => {
    setEditingEvent(null);
    setPrefillYear(prompt.prefillData?.year ?? null);
    setPrefillDescription(prompt.prefillData?.description ?? null);
    setPrefillCategory(prompt.prefillData?.category ?? null);
    setShowEditor(true);
    // Dismiss this prompt after acting on it
    setDismissedPrompts(prev => new Set([...prev, prompt.id]));
  };

  // Dismiss a memory prompt
  const handleDismissMemoryPrompt = (promptId: string) => {
    setDismissedPrompts(prev => new Set([...prev, promptId]));
    setCurrentPromptIndex(prev => prev + 1);
  };

  // Open editor for existing event
  const handleEditEvent = (event: LifelineEvent) => {
    setEditingEvent(event);
    setPrefillYear(null);
    setShowEditor(true);
  };

  // Handle starter prompt selection
  const handleStarterPromptSelect = (prefillTitle: string, category?: string) => {
    setEditingEvent(null);
    setPrefillYear(null);
    setPrefillDescription(prefillTitle);
    setPrefillCategory(category || null);
    setShowEditor(true);
  };

  // Render header with statistics and patterns
  const renderHeader = () => (
    <View style={styles.header} onLayout={handleHeaderLayout}>
      {/* 1. Framing Card - Smart collapsible for all users */}
      <LifelineFramingCard 
        onAddMoment={handleAddEvent}
        eventCount={events.length}
        birthYear={birthYear || undefined}
      />
      
      {/* 2. Mini Map - Life arc visualization (only if we have birth year) */}
      {birthYear && (
        <LifelineMiniMap
          events={events}
          birthYear={birthYear}
          gaps={missingPeriods}
          onYearPress={scrollToYear}
          onGapPress={handleGapPressFromMap}
        />
      )}
      
      {/* 3. Starter Prompts - for users with < 5 moments */}
      <LifelineStarterPrompts
        eventCount={events.length}
        onSelectPrompt={handleStarterPromptSelect}
      />
      
      {/* 4. Title + Add button */}
      <View style={styles.headerTop}>
        <View>
          <Text style={[styles.title, { color: theme.text }]}>Lifeline</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            A place to map the moments that shaped you — and see the patterns behind them.
          </Text>
        </View>
        <TouchableOpacity
          style={[styles.addButton, { backgroundColor: theme.accent }]}
          onPress={() => setShowAddMenu(true)}
        >
          <Ionicons name="add" size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* 5. Statistics summary */}
      {statistics && events.length > 0 && (
        <View style={[styles.statsRow, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.text }]}>{events.length}</Text>
            <Text style={[styles.statLabel, { color: theme.textTertiary }]}>moments</Text>
          </View>
          {statistics.year_range && (
            <View style={styles.statItem}>
              <Text style={[styles.statValue, { color: theme.text }]}>
                {statistics.year_range.min}–{statistics.year_range.max}
              </Text>
              <Text style={[styles.statLabel, { color: theme.textTertiary }]}>years</Text>
            </View>
          )}
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: theme.text }]}>
              {statistics.categories_used.length}
            </Text>
            <Text style={[styles.statLabel, { color: theme.textTertiary }]}>categories</Text>
          </View>
        </View>
      )}

      {/* 6. Pattern Insights - appears above timeline */}
      <LifelinePatterns patterns={patterns} eventCount={events.length} />
      
      {/* 7. Pattern Synthesis Card - LLM-generated insights for 5+ events */}
      <LifelinePatternSynthesisCard userId={userId} eventCount={events.length} />

      {/* Memory Expansion Prompt - gentle prompt based on patterns/gaps */}
      {currentMemoryPrompt && (
        <View style={styles.memoryPromptContainer}>
          <LifelineMemoryPrompt
            prompt={currentMemoryPrompt}
            onAddMoment={handleAddFromMemoryPrompt}
            onDismiss={handleDismissMemoryPrompt}
          />
        </View>
      )}

      {/* Gap Prompts - gentle prompts for missing periods (only if no memory prompt shown) */}
      {!currentMemoryPrompt && visibleGaps.length > 0 && (
        <View style={styles.gapPromptsContainer}>
          {visibleGaps.slice(0, 2).map((gap, index) => (
            <LifelineGapPrompt
              key={`gap-${gap.start_year}-${gap.end_year}`}
              gap={gap}
              onAddMoment={handleAddFromGap}
              onDismiss={handleDismissGap}
            />
          ))}
        </View>
      )}
    </View>
  );

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        {renderHeader()}
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.textTertiary} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>Loading your lifeline...</Text>
        </View>
      </View>
    );
  }

  // Error state
  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        {renderHeader()}
        <View style={styles.errorContainer}>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
          <TouchableOpacity
            style={[styles.retryButton, { borderColor: theme.border }]}
            onPress={() => loadTimeline()}
          >
            <Text style={[styles.retryText, { color: theme.text }]}>Try again</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Empty state - use inline onboarding with full buttons
  if (events.length === 0) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <LifelineInlineOnboarding 
          onStartLifeline={handleAddEvent}
          tabContext="lifeline"
        />
        <LifelineEventEditor
          visible={showEditor}
          event={editingEvent}
          onClose={() => setShowEditor(false)}
          onSave={handleSaveEvent}
          onDelete={handleDeleteEvent}
        />
      </View>
    );
  }

  // Timeline with events - using time-distance visualization
  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView
        ref={scrollViewRef}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => loadTimeline(true)}
            tintColor={theme.textTertiary}
          />
        }
      >
        {renderHeader()}
        
        {/* Time-Distance Timeline */}
        <TimeDistanceTimeline
          events={events}
          onEditEvent={handleEditEvent}
          onDeleteEvent={handleDeleteEvent}
          isCompact={isCompact}
          isFirstReveal={false}
          showEarlyMessages={events.length <= 3}
          resonanceMap={resonanceMap}
          onEventLayout={handleEventLayout}
          highlightedYear={highlightedYear}
          birthYear={birthYear || undefined}
        />
        
        {/* Chart Resonance Section for Pattern Lens */}
        {resonanceSummary.length > 0 && (
          <ChartResonanceSection resonances={resonanceSummary} />
        )}
        
        <View style={styles.footer}>
          <Text style={[styles.footerText, { color: theme.textTertiary }]}>
            Your story is still being written.
          </Text>
        </View>
      </ScrollView>

      {/* Add to Lifeline Menu */}
      <LifelineAddMenu
        visible={showAddMenu}
        onClose={() => setShowAddMenu(false)}
        onAddManually={handleAddEvent}
        onViewSources={() => router.push('/lifeline-imported-sources')}
        hasImportedSources={importSourceCount > 0}
        importedSourceCount={importSourceCount}
      />

      {/* Event Editor Modal */}
      <LifelineEventEditor
        visible={showEditor}
        event={editingEvent}
        prefillYear={prefillYear}
        prefillDescription={prefillDescription}
        prefillCategory={prefillCategory}
        onClose={() => {
          setShowEditor(false);
          setPrefillDescription(null);
          setPrefillCategory(null);
        }}
        onSave={handleSaveEvent}
        onDelete={handleDeleteEvent}
      />
      
      {/* Toast notification */}
      {toastMessage && (
        <Animated.View style={[styles.toast, { opacity: toastOpacity, backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.toastText, { color: theme.text }]}>{toastMessage}</Text>
        </Animated.View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    marginBottom: 20,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '600',
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    lineHeight: 20,
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 11,
  },
  listContent: {
    padding: 20,
    paddingBottom: 120, // Extra padding for PWA banner overlay
  },
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    padding: 40,
    alignItems: 'center',
    gap: 16,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  footer: {
    paddingTop: 20,
    paddingBottom: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  gapPromptsContainer: {
    marginTop: 4,
  },
  memoryPromptContainer: {
    marginTop: 16,
  },
  toast: {
    position: 'absolute',
    bottom: 100,
    left: 20,
    right: 20,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  toastText: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
  },
});
