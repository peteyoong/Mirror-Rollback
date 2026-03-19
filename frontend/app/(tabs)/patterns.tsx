/**
 * PATTERNS TAB - Recurrence/History View
 * 
 * ARCHITECTURE LOCK:
 * Primary Job: "What keeps showing up in my life?"
 * 
 * Structure (ORDER MATTERS):
 * 1. TIMELINE (PRIMARY) - When this pattern has appeared before → PROOF of recurrence
 * 2. THIS WEEK - What's active now → Connect past to present
 * 3. ARCHETYPE (LAST) - Pattern identity → Meaning AFTER evidence
 * 
 * DO NOT lead with identity. User must see:
 * - "This has happened before"
 * - "It's happening again"
 * THEN: "This is your pattern"
 * 
 * REMOVED: Domain accordions, Signals tab, Chart resonance, Analytics-heavy UI
 * 
 * SCROLL RESET: This screen must ALWAYS open at the top.
 * - useScrollToTop hook is disabled (empty scrollToTop function)
 * - useFocusEffect forces scroll to y=0 on every tab focus
 * - scrollsToTop={false} prevents iOS status bar tap scroll
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';

// ============================================================================
// INTERFACES
// ============================================================================

interface WeeklySummary {
  week_start: string;
  week_end: string;
  narrative: string;
  top_domains: {
    domain_id: string;
    domain: string;
    days_present: number;
    trend: 'rising' | 'steady' | 'fading';
    evidence_summary: string[];
    timing_amplified: boolean;
  }[];
  evidence_sources: string[];
  cross_week_shift: string | null;
  reflection_prompt: string;
}

interface WeekEntry {
  week_start: string;
  week_end: string;
  top_domain: string | null;
  top_domain_id?: string;
  secondary_domains?: string[];
  trend_map: Record<string, 'rising' | 'steady' | 'fading'>;
  timing_amplified_domains?: string[];
  narrative: string;
  reflection_prompt?: string;
}

interface TimelineData {
  weeks: WeekEntry[];
  range_label: string;
  narrative_summary: string;
  is_partial: boolean;
  insights: {
    most_recurring_domain: string | null;
    strongest_recent_domain: string | null;
    volatile_domain: string | null;
    stable_domain: string | null;
    reemerging_domain: string | null;
  };
  reflection_prompt: string;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function PatternsScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  
  // ============================================================================
  // SCROLL RESET - LAYOUT-BASED APPROACH
  // ============================================================================
  // 
  // ROOT CAUSE CONFIRMED:
  // User screenshots show the screen opening mid-page (at later timeline entries)
  // instead of at the HERO section at top. Native scroll restoration is
  // overriding our reset attempts.
  //
  // NEW APPROACH:
  // 1. Use onLayout callback to reset scroll AFTER layout completes
  // 2. Track layout completion with ref to avoid infinite loops
  // 3. Force scroll reset on EVERY layout cycle until we're focused
  //
  
  // Track if we should reset scroll on next layout
  const shouldResetScrollRef = useRef(true);
  
  // Track focus state
  const isFocusedRef = useRef(false);
  
  // Scroll ref for explicit scroll control
  const scrollViewRef = useRef<ScrollView>(null);
  
  // Timeline State (PRIMARY)
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(true);
  const [timelineRefreshing, setTimelineRefreshing] = useState(false);
  
  // Weekly State
  const [weeklySummary, setWeeklySummary] = useState<WeeklySummary | null>(null);
  const [weeklyLoading, setWeeklyLoading] = useState(true);
  
  // Expanded week tracking
  const [expandedWeek, setExpandedWeek] = useState<string | null>(null);

  // Master scroll reset function - resets to absolute top
  const resetScroll = useCallback(() => {
    if (scrollViewRef.current) {
      scrollViewRef.current.scrollTo({ x: 0, y: 0, animated: false });
    }
    
    // Also reset browser scroll on web
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      window.scrollTo(0, 0);
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    }
  }, []);

  // Disable browser scroll restoration (web only)
  useEffect(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
      }
    }
  }, []);

  // On focus: mark that we should reset scroll
  useFocusEffect(
    useCallback(() => {
      isFocusedRef.current = true;
      shouldResetScrollRef.current = true;
      setExpandedWeek(null);
      
      // Immediate reset attempt
      resetScroll();
      
      // Aggressive reset - keep trying for 500ms
      let attempts = 0;
      const intervalId = setInterval(() => {
        if (shouldResetScrollRef.current && attempts < 25) {
          resetScroll();
          attempts++;
        } else {
          clearInterval(intervalId);
        }
      }, 20);
      
      return () => {
        isFocusedRef.current = false;
        shouldResetScrollRef.current = false;
        clearInterval(intervalId);
      };
    }, [resetScroll])
  );

  // Handle layout changes - reset scroll when content renders
  const handleContentLayout = useCallback(() => {
    if (shouldResetScrollRef.current && isFocusedRef.current) {
      resetScroll();
    }
  }, [resetScroll]);

  // Reset scroll AFTER data loads
  useEffect(() => {
    if (!timelineLoading && !weeklyLoading && isFocusedRef.current) {
      // Data loaded - mark for reset and reset immediately
      shouldResetScrollRef.current = true;
      resetScroll();
      
      // Continue resetting for a short period
      let resetCount = 0;
      const intervalId = setInterval(() => {
        if (resetCount < 10) {
          resetScroll();
          resetCount++;
        } else {
          clearInterval(intervalId);
          shouldResetScrollRef.current = false;
        }
      }, 50);
      
      return () => clearInterval(intervalId);
    }
  }, [timelineLoading, weeklyLoading, resetScroll]);

  // ============================================================================
  // DATA LOADING
  // ============================================================================

  const fetchTimeline = useCallback(async (showRefresh = false) => {
    if (!user?.id) return;
    
    if (showRefresh) {
      setTimelineRefreshing(true);
    } else {
      setTimelineLoading(true);
    }
    
    try {
      const response = await api.get(`/pattern-timeline/${user.id}?weeks=8`);
      // API returns { success: true, timeline: { ... } }
      setTimeline(response.data?.timeline || null);
    } catch (error) {
      console.error('Failed to fetch timeline:', error);
    } finally {
      setTimelineLoading(false);
      setTimelineRefreshing(false);
    }
  }, [user?.id]);

  const fetchWeekly = useCallback(async () => {
    if (!user?.id) return;
    
    setWeeklyLoading(true);
    
    try {
      const response = await api.get(`/weekly-patterns/${user.id}`);
      // API returns { success: true, weekly_summary: { ... } }
      setWeeklySummary(response.data?.weekly_summary || null);
    } catch (error) {
      console.error('Failed to fetch weekly:', error);
    } finally {
      setWeeklyLoading(false);
    }
  }, [user?.id]);

  useEffect(() => {
    fetchTimeline();
    fetchWeekly();
  }, [fetchTimeline, fetchWeekly]);

  const handleRefresh = () => {
    fetchTimeline(true);
    fetchWeekly();
  };

  // ============================================================================
  // HELPERS
  // ============================================================================

  // PATTERN FINGERPRINT LANGUAGE - Confronting, specific, recognizable
  // Structure: [Action] - [Internal experience] - [Outcome or shift]
  // Test: "That is uncomfortable... but true"
  const DOMAIN_TO_HUMAN_PHRASE: Record<string, string> = {
    'energy_vitality': 'You push until you break - then wonder why you are exhausted',
    'emotional_landscape': 'You hold it together... until you cannot anymore',
    'identity_direction': 'You reinvent yourself - but the same doubts follow',
    'relationships_connection': 'You pull people close - then push them away before they see too much',
    'work_purpose': 'You throw yourself into work - hoping it will finally feel like enough',
    'creativity_expression': 'You create something - then convince yourself it does not matter',
    'health_body': 'You ignore what your body tells you - until it stops asking',
    'spirituality_meaning': 'You search for meaning - but abandon it before it settles',
    'money_security': 'You chase security - then sabotage it when you get close',
    'family_roots': 'You carry everyone else - but will not let anyone carry you',
  };

  // Get human phrase from domain ID, with fallback
  const getHumanPhrase = (domainId: string | null | undefined, domain: string | null | undefined): string => {
    if (domainId && DOMAIN_TO_HUMAN_PHRASE[domainId]) {
      return DOMAIN_TO_HUMAN_PHRASE[domainId];
    }
    // Fallback: still make it confronting
    if (domain) {
      return 'Something keeps pulling you back to ' + domain.toLowerCase() + ' - even when you try to move on';
    }
    return 'A pattern you recognize - even when you wish you did not';
  };

  // PHASE-BASED PROGRESSION - Each week shows a different stage of how the pattern unfolds
  // NOT random variations, but a STORY that progresses through time
  // Structure: Phase 1 (trigger) → Phase 2 (escalation) → ... → Phase 8 (aftermath)
  const getBehavioralSummary = (week: WeekEntry, weekIndex: number): string => {
    const domainId = week.top_domain_id;
    
    // PHASE SEQUENCES - Each pattern unfolds through these stages over time
    // Week 0 = earliest, Week 7 = most recent
    // The sequence tells the STORY of how this pattern plays out
    const phaseSequences: Record<string, string[]> = {
      'energy_vitality': [
        'You felt the pressure building and decided to push through',
        'You increased effort, thinking more would solve it',
        'Something started to feel off - but you ignored it',
        'You noticed the fatigue... but kept going anyway',
        'You were running on low, but did not slow down',
        'Your energy dropped - but you tried to maintain momentum',
        'Your system forced a stop',
        'You were left wondering why you felt so exhausted',
      ],
      'emotional_landscape': [
        'Something stirred that you did not want to feel',
        'You pushed it down and kept moving',
        'It started leaking through in small ways',
        'You held tighter, hoping it would pass',
        'The pressure built but you kept the lid on',
        'Cracks started to show',
        'It came out - not when you chose, but when it had to',
        'You were left processing what you had been carrying',
      ],
      'identity_direction': [
        'You felt the pull to become something new',
        'You started questioning what you thought you knew about yourself',
        'You made a change, hoping it would feel right',
        'The newness wore off and the old doubts returned',
        'You wondered if this version was any more real',
        'You started looking for the next thing to become',
        'You let go of what you were building',
        'You were left asking who you actually are',
      ],
      'relationships_connection': [
        'You wanted to feel close to someone',
        'You reached out, maybe more than usual',
        'You noticed yourself watching for signs of rejection',
        'You started to pull back before they could',
        'The distance grew even as you wanted connection',
        'You protected yourself by not asking for what you needed',
        'The gap became too wide to bridge easily',
        'You were left wondering why closeness feels so hard',
      ],
      'work_purpose': [
        'You felt driven to prove something through work',
        'You took on more, hoping it would feel meaningful',
        'You delivered, but the satisfaction did not land',
        'You pushed harder, thinking effort was the answer',
        'You started to feel trapped by what you built',
        'The work kept coming but the purpose faded',
        'You hit a wall you could not work through',
        'You were left questioning what any of it was for',
      ],
      'creativity_expression': [
        'You felt something wanting to come out',
        'You started creating with hope',
        'The inner critic showed up early',
        'You edited before you finished',
        'You compared it to others and found it lacking',
        'You considered abandoning it altogether',
        'You held back the part that felt most true',
        'You were left wondering why you cannot just create freely',
      ],
      'health_body': [
        'Your body sent a small signal',
        'You noticed it but decided it could wait',
        'The signal came again, a little louder',
        'You overrode it with willpower',
        'Other symptoms started to appear',
        'You kept functioning on borrowed time',
        'Your body made the decision you would not make',
        'You were left realizing you cannot outrun yourself',
      ],
      'spirituality_meaning': [
        'You felt a pull toward something deeper',
        'You started exploring with genuine curiosity',
        'Something meaningful started to form',
        'Doubt crept in and you questioned it',
        'You pulled back from what you found',
        'The search felt pointless for a while',
        'You abandoned what was starting to take root',
        'You were left wondering why you cannot let meaning settle',
      ],
      'money_security': [
        'You felt the urge to build security',
        'You started accumulating with purpose',
        'Things were coming together',
        'You started to feel uneasy with what you had',
        'You found reasons to undo the progress',
        'You spent or gave away what you built',
        'The stability you created collapsed',
        'You were left asking why you sabotage your own security',
      ],
      'family_roots': [
        'You felt responsible for holding something together',
        'You took on more than your share',
        'You noticed resentment building',
        'You pushed it down because others needed you',
        'You kept giving while running on empty',
        'You started to feel invisible despite all you carried',
        'You reached a point where you could not carry more',
        'You were left wondering when someone will carry you',
      ],
    };

    // Generic phase sequence for unknown domains
    const genericPhaseSequence = [
      'Something familiar started to stir',
      'You noticed the pattern beginning again',
      'You tried to handle it differently this time',
      'The same old pull returned',
      'You found yourself in familiar territory',
      'The pattern strengthened despite your awareness',
      'It played out the way it always does',
      'You were left recognizing what keeps returning',
    ];

    // Get the phase sequence for this domain, or use generic
    const phases = domainId && phaseSequences[domainId] 
      ? phaseSequences[domainId] 
      : genericPhaseSequence;

    // Map week index to phase (modulo handles overflow)
    // Week 0 = Phase 0 (earliest/trigger), Week 7 = Phase 7 (most recent/aftermath)
    const phaseIndex = weekIndex % phases.length;
    
    return phases[phaseIndex];
  };

  const formatDateRange = (start: string, end: string) => {
    const startDate = new Date(start);
    const endDate = new Date(end);
    const options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
    return `${startDate.toLocaleDateString('en-US', options)} – ${endDate.toLocaleDateString('en-US', options)}`;
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'rising': return '#4CAF50';
      case 'fading': return '#FF9800';
      default: return theme.textTertiary;
    }
  };

  const getTrendLabel = (trend: string) => {
    switch (trend) {
      case 'rising': return '↑ Intensifying';
      case 'fading': return '↓ Softening';
      default: return '• Steady';
    }
  };

  // ============================================================================
  // RENDER: WEEK ENTRY (used by repeating list)
  // ============================================================================

  const renderWeekEntry = (week: WeekEntry, index: number) => {
    const isExpanded = expandedWeek === week.week_start;
    const weekLabel = formatDateRange(week.week_start, week.week_end);
    
    if (!week.top_domain) return null;
    
    // Use index to get unique behavioral phase for this week
    const behavioralSummary = getBehavioralSummary(week, index);
    
    return (
      <TouchableOpacity
        key={week.week_start}
        style={[
          styles.weekCard,
          { 
            backgroundColor: theme.surface, 
            borderColor: isExpanded ? theme.accent : theme.border 
          }
        ]}
        onPress={() => setExpandedWeek(isExpanded ? null : week.week_start)}
        activeOpacity={0.7}
      >
        <View style={styles.weekHeader}>
          <View style={styles.weekLeft}>
            <Text style={[styles.weekLabel, { color: theme.textTertiary }]}>
              {weekLabel}
            </Text>
            <Text style={[styles.weekTopDomain, { color: theme.text }]}>
              {behavioralSummary}
            </Text>
          </View>
          <Text style={[styles.weekChevron, { color: theme.textTertiary }]}>
            {isExpanded ? '-' : '+'}
          </Text>
        </View>
        
        {isExpanded && week.narrative && (
          <View style={[styles.weekExpanded, { borderTopColor: theme.border }]}>
            <Text style={[styles.weekNarrative, { color: theme.textSecondary }]}>
              {week.narrative}
            </Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  // ============================================================================
  // RENDER: HERO SECTION (Pattern fingerprint)
  // ============================================================================

  const renderHeroSection = () => {
    if (timelineLoading) {
      return (
        <View style={styles.loadingSection}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading your patterns...
          </Text>
        </View>
      );
    }

    if (!timeline || !timeline.weeks || timeline.weeks.length === 0) {
      return (
        <View style={[styles.emptySection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.emptySectionIcon]}>◷</Text>
          <Text style={[styles.emptySectionTitle, { color: theme.text }]}>
            Your patterns are still forming
          </Text>
          <Text style={[styles.emptySectionText, { color: theme.textSecondary }]}>
            As patterns accumulate over time, you will see what keeps showing up.
          </Text>
        </View>
      );
    }

    // Calculate recurrence count for display
    const weeksWithPattern = timeline.weeks.filter(w => w.top_domain).length;
    
    // Get human phrase for HERO - NOT domain label
    const mostRecurringId = timeline.weeks.find(w => w.top_domain_id)?.top_domain_id;
    const mostRecurring = timeline.weeks.find(w => w.top_domain)?.top_domain;
    const humanPhrase = getHumanPhrase(mostRecurringId, mostRecurring);

    return (
      <View style={[styles.heroCard, { backgroundColor: theme.surface, borderColor: theme.accent }]}>
        <Text style={[styles.heroPattern, { color: theme.text }]}>
          {humanPhrase}
        </Text>
        <Text style={[styles.heroCount, { color: theme.accent }]}>
          Seen {weeksWithPattern} times in {timeline.weeks.length} weeks
        </Text>
        <Text style={[styles.heroSubtext, { color: theme.textSecondary }]}>
          This is real. It keeps happening.
        </Text>
      </View>
    );
  };

  // ============================================================================
  // RENDER: REPEATING PATTERNS LIST (Evidence/receipts)
  // ============================================================================

  const renderRepeatingList = () => {
    if (!timeline || !timeline.weeks || timeline.weeks.length === 0) {
      return null;
    }

    return (
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            WHEN IT APPEARED
          </Text>
        </View>
        
        <View style={styles.weeksContainer}>
          {timeline.weeks.map((week, index) => renderWeekEntry(week, index))}
        </View>
      </View>
    );
  };

  // ============================================================================
  // RENDER: THIS WEEK SECTION
  // ============================================================================

  const renderThisWeekSection = () => {
    if (weeklyLoading) {
      return (
        <View style={styles.loadingSection}>
          <ActivityIndicator size="small" color={theme.accent} />
        </View>
      );
    }

    if (!weeklySummary) {
      return null;
    }

    // Get human phrase for this week - NOT domain label
    const topDomainId = weeklySummary.top_domains?.[0]?.domain_id;
    const topDomain = weeklySummary.top_domains?.[0]?.domain;
    const humanPhrase = getHumanPhrase(topDomainId, topDomain);

    return (
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            THIS WEEK
          </Text>
          <Text style={[styles.sectionRange, { color: theme.textTertiary }]}>
            {formatDateRange(weeklySummary.week_start, weeklySummary.week_end)}
          </Text>
        </View>

        {/* Human phrase, not domain label */}
        <View style={[styles.narrativeCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.narrativeText, { color: theme.text }]}>
            This pattern is active again.
          </Text>
          <Text style={[styles.narrativeSubtext, { color: theme.textSecondary }]}>
            {humanPhrase}
          </Text>
        </View>

        {/* Link to current Keystone */}
        <TouchableOpacity
          style={[styles.keystoneLink, { borderColor: theme.border }]}
          onPress={() => router.push('/(tabs)')}
          activeOpacity={0.7}
        >
          <Text style={[styles.keystoneLinkLabel, { color: theme.accent }]}>
            See today's pattern →
          </Text>
        </TouchableOpacity>
      </View>
    );
  };

  // ============================================================================
  // RENDER: ARCHETYPE SECTION (CONCLUSION - meaning after evidence)
  // ============================================================================

  const [archetypeData, setArchetypeData] = useState<any>(null);
  const [archetypeLoading, setArchetypeLoading] = useState(true);
  const [archetypeExpanded, setArchetypeExpanded] = useState(false);

  // Fetch archetype data
  useEffect(() => {
    const fetchArchetype = async () => {
      if (!user?.id) return;
      try {
        setArchetypeLoading(true);
        const response = await api.get(`/pattern-archetype/${user.id}`);
        setArchetypeData(response.data);
      } catch (error) {
        console.error('Failed to fetch archetype:', error);
      } finally {
        setArchetypeLoading(false);
      }
    };
    fetchArchetype();
  }, [user?.id]);

  const renderArchetypeSection = () => {
    if (archetypeLoading) {
      return null; // Don't show loading - let it appear when ready
    }

    if (!archetypeData?.primary_archetype) {
      return null;
    }

    const archetype = archetypeData.primary_archetype;
    const narrative = archetype.narrative;
    
    // Extract just the archetype name without "A" or "Pattern"
    // e.g., "The Reinventor" not "A The Reinventor Pattern"
    const archetypeName = archetype.name;

    // Create a tight opening line based on archetype
    const tightOpeningLines: Record<string, string> = {
      'The Reinventor': 'You do not stay who you were - you outgrow it.',
      'The Carrier': 'You hold what others cannot hold for themselves.',
      'The Seeker': 'You chase what keeps moving just out of reach.',
      'The Protector': 'You build walls so others do not have to.',
      'The Striver': 'You measure yourself by what you have not yet done.',
      'The Feeler': 'You carry the room before anyone speaks.',
      'Emergence Keeper': 'You hold space for what has not yet arrived.',
      'The Observer': 'You see patterns others miss.',
    };

    const tightOpening = tightOpeningLines[archetypeName] || narrative.short_description;

    return (
      <View style={styles.conclusionSection}>
        {/* Transition text - bridges timeline to meaning */}
        <Text style={[styles.conclusionTransition, { color: theme.textTertiary }]}>
          When this keeps happening, it usually points to this:
        </Text>

        {/* Archetype as conclusion - softer, continuation feel */}
        <View style={[styles.conclusionCard, { borderColor: theme.border }]}>
          <View style={styles.conclusionHeader}>
            <Text style={styles.conclusionIcon}>{archetype.icon}</Text>
            <Text style={[styles.conclusionName, { color: theme.text }]}>
              {archetypeName}
            </Text>
          </View>
          
          {/* Tight opening line */}
          <Text style={[styles.conclusionOpening, { color: theme.textSecondary }]}>
            {tightOpening}
          </Text>

          {/* Expand for details */}
          <TouchableOpacity
            style={styles.conclusionExpand}
            onPress={() => setArchetypeExpanded(!archetypeExpanded)}
            activeOpacity={0.7}
          >
            <Text style={[styles.conclusionExpandText, { color: theme.accent }]}>
              {archetypeExpanded ? 'Less' : 'More about this pattern'}
            </Text>
          </TouchableOpacity>

          {archetypeExpanded && (
            <View style={[styles.conclusionDetails, { borderTopColor: theme.border }]}>
              <Text style={[styles.conclusionSummary, { color: theme.textSecondary }]}>
                {narrative.summary}
              </Text>
              {narrative.how_this_shows_up && narrative.how_this_shows_up.length > 0 && (
                <View style={styles.conclusionShowsUp}>
                  {narrative.how_this_shows_up.slice(0, 3).map((item: string, index: number) => (
                    <Text key={index} style={[styles.conclusionShowsUpItem, { color: theme.textTertiary }]}>
                      {item}
                    </Text>
                  ))}
                </View>
              )}
            </View>
          )}
        </View>
      </View>
    );
  };

  // ============================================================================
  // RENDER: REFLECTION PROMPT
  // ============================================================================

  const renderReflectionPrompt = () => {
    const prompt = timeline?.reflection_prompt || weeklySummary?.reflection_prompt;
    if (!prompt) return null;

    return (
      <View style={[styles.reflectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>
          A question to sit with
        </Text>
        <Text style={[styles.reflectionPrompt, { color: theme.accent }]}>
          "{prompt}"
        </Text>
      </View>
    );
  };

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Patterns</Text>
        <Text style={[styles.headerSubtitle, { color: theme.textSecondary }]}>
          What keeps showing up
        </Text>
      </View>
      
      <ScrollView
        ref={scrollViewRef}
        style={styles.content}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        scrollsToTop={false}
        onLayout={handleContentLayout}
        refreshControl={
          <RefreshControl
            refreshing={timelineRefreshing}
            onRefresh={handleRefresh}
            tintColor={theme.textTertiary}
          />
        }
      >
        {/* 1. HERO - Pattern fingerprint */}
        {renderHeroSection()}
        
        {/* 2. WHEN IT APPEARED - Evidence/receipts */}
        <View style={styles.timelineSection}>
          {renderRepeatingList()}
        </View>
        
        {/* 3. THIS WEEK - Current activation */}
        <View style={styles.thisWeekSection}>
          <View style={[styles.sectionDivider, { backgroundColor: theme.border }]} />
          {renderThisWeekSection()}
        </View>
        
        {/* 4. ARCHETYPE - Conclusion */}
        <View style={styles.archetypeSection}>
          {renderArchetypeSection()}
        </View>
        
        {/* 5. REFLECTION PROMPT */}
        <View style={styles.reflectionSection}>
          {renderReflectionPrompt()}
        </View>
        
        {/* Bottom padding for tab bar */}
        <View style={{ height: 100 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

// ============================================================================
// STYLES
// ============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 16,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
  },
  headerSubtitle: {
    fontSize: 14,
    marginTop: 4,
    fontStyle: 'italic',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  
  // Loading
  loadingSection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24,
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  
  // Empty State
  emptySection: {
    padding: 24,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    marginBottom: 24,
  },
  emptySectionIcon: {
    fontSize: 32,
    opacity: 0.5,
    marginBottom: 12,
  },
  emptySectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySectionText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  
  // Sections
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
  },
  sectionRange: {
    fontSize: 12,
  },
  
  // HARD SECTION BOUNDARIES
  timelineSection: {
    marginTop: 28,
  },
  thisWeekSection: {
    marginTop: 32,
    paddingTop: 24,
  },
  archetypeSection: {
    marginTop: 36,
  },
  reflectionSection: {
    marginTop: 24,
    paddingBottom: 16,
  },
  sectionDivider: {
    height: 1,
    marginBottom: 24,
  },
  
  // Narrative Card
  narrativeCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  narrativeText: {
    fontSize: 15,
    lineHeight: 24,
  },
  narrativeSubtext: {
    fontSize: 13,
    marginTop: 8,
    fontStyle: 'italic',
  },
  
  // Hero Card (Timeline HERO)
  heroCard: {
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 24,
    alignItems: 'center',
  },
  heroCount: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  heroPattern: {
    fontSize: 22,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  heroSubtext: {
    fontSize: 14,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  
  // Week Cards (Timeline)
  weeksContainer: {
    gap: 8,
  },
  weekCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  weekHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
  },
  weekLeft: {
    flex: 1,
  },
  weekLabel: {
    fontSize: 11,
    fontWeight: '500',
    marginBottom: 4,
  },
  weekTopDomain: {
    fontSize: 15,
    fontWeight: '500',
  },
  weekChevron: {
    fontSize: 16,
    fontWeight: '300',
  },
  weekExpanded: {
    padding: 14,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  weekNarrative: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  trendsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  trendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendDomain: {
    fontSize: 12,
  },
  trendIndicator: {
    fontSize: 12,
    fontWeight: '600',
  },
  
  // Insight Card
  insightCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    marginTop: 16,
  },
  insightLabel: {
    fontSize: 11,
    fontWeight: '500',
    marginBottom: 4,
  },
  insightValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  insightNote: {
    fontSize: 13,
    marginTop: 6,
    fontStyle: 'italic',
  },
  
  // This Week - Domain Chips
  domainsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  domainChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  domainChipName: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  domainChipTrend: {
    fontSize: 11,
  },
  
  // Keystone Link
  keystoneLink: {
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  keystoneLinkLabel: {
    fontSize: 13,
  },
  
  // Archetype Note
  archetypeNote: {
    paddingTop: 12,
    marginTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  archetypeNoteText: {
    fontSize: 12,
    lineHeight: 18,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Conclusion Section (Archetype as conclusion, not separate card)
  conclusionSection: {
    marginTop: 8,
    marginBottom: 24,
  },
  conclusionTransition: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 12,
    textAlign: 'center',
  },
  conclusionCard: {
    padding: 16,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderLeftWidth: 2,
  },
  conclusionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  conclusionIcon: {
    fontSize: 20,
    marginRight: 10,
  },
  conclusionName: {
    fontSize: 18,
    fontWeight: '600',
  },
  conclusionOpening: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
  },
  conclusionExpand: {
    paddingVertical: 8,
  },
  conclusionExpandText: {
    fontSize: 13,
  },
  conclusionDetails: {
    paddingTop: 12,
    marginTop: 8,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  conclusionSummary: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  conclusionShowsUp: {
    gap: 6,
  },
  conclusionShowsUpItem: {
    fontSize: 13,
    lineHeight: 18,
  },
  
  // Reflection
  reflectionCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 24,
  },
  reflectionLabel: {
    fontSize: 11,
    fontWeight: '500',
    marginBottom: 8,
  },
  reflectionPrompt: {
    fontSize: 15,
    fontStyle: 'italic',
    lineHeight: 22,
  },
});
