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
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';
import PatternArchetypeCard from '../../components/patterns/PatternArchetypeCard';

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
  
  // Timeline State (PRIMARY)
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(true);
  const [timelineRefreshing, setTimelineRefreshing] = useState(false);
  
  // Weekly State
  const [weeklySummary, setWeeklySummary] = useState<WeeklySummary | null>(null);
  const [weeklyLoading, setWeeklyLoading] = useState(true);
  
  // Expanded week tracking
  const [expandedWeek, setExpandedWeek] = useState<string | null>(null);

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

  // VARIATION GENERATOR - Unique behavioral summary for each week
  // All variations map to the same core pattern, but express it differently
  // NO REPEATED PHRASES allowed in the same timeline
  const getBehavioralSummary = (week: WeekEntry, weekIndex: number): string => {
    const domainId = week.top_domain_id;
    
    // VARIATION BANKS - 8+ unique phrases per domain, all expressing same core pattern
    const variationBanks: Record<string, string[]> = {
      'energy_vitality': [
        'You kept going even after your body said stop',
        'You pushed harder, hoping effort would fix the strain',
        'You stayed with it too long because stopping felt worse',
        'You overrode the fatigue and only noticed it later',
        'You treated depletion like something to push through',
        'You kept carrying it after the energy had already dropped',
        'You forced momentum when recovery was what was needed',
        'You only stopped once your system made the decision for you',
        'You ran on empty and called it discipline',
        'You mistook exhaustion for not trying hard enough',
      ],
      'emotional_landscape': [
        'You held it in until holding became its own weight',
        'You swallowed what needed to come out',
        'You kept composure while something cracked underneath',
        'You smiled through it and no one noticed',
        'You numbed the signal instead of hearing it',
        'You let it build because expressing felt unsafe',
        'You carried more than you showed anyone',
        'You felt it all but said nothing',
        'You kept functioning while something inside went quiet',
        'You performed calm while chaos lived beneath it',
      ],
      'identity_direction': [
        'You started over again, hoping this time it would stick',
        'You questioned the path even while walking it',
        'You changed direction before the last one settled',
        'You abandoned what was working because it did not feel like you',
        'You reinvented before anyone could pin you down',
        'You second-guessed the decision before it had a chance',
        'You wondered if this version of you was real either',
        'You searched for yourself in a new form',
        'You let go of something before knowing why',
        'You started fresh but brought the same doubts with you',
      ],
      'relationships_connection': [
        'You reached out then pulled back before they could respond',
        'You wanted closeness but created distance instead',
        'You tested them to see if they would stay',
        'You protected yourself by not asking for what you needed',
        'You felt alone in the room even with people around',
        'You kept them at arm length and felt the gap',
        'You showed up halfway and wondered why it felt hollow',
        'You gave more than you let yourself receive',
        'You stayed guarded and called it being careful',
        'You wanted to be seen but hid the parts that mattered',
      ],
      'work_purpose': [
        'You worked harder hoping it would finally feel like enough',
        'You produced more and felt less satisfied',
        'You delivered but the meaning did not land',
        'You stayed late and still felt behind',
        'You achieved the goal and immediately moved the bar',
        'You kept going because stopping felt like failing',
        'You tied your worth to output and came up short',
        'You performed well but felt like a fraud',
        'You finished it and felt nothing',
        'You did more and mattered less to yourself',
      ],
      'creativity_expression': [
        'You made something then convinced yourself it was nothing',
        'You created and immediately dismissed it',
        'You shared then wished you had not',
        'You held back the work that felt most true',
        'You edited the life out of what you made',
        'You compared it before it even had a chance',
        'You doubted it before anyone else could',
        'You created in private and kept it hidden',
        'You wanted to be seen but not judged',
        'You made art then called it waste',
      ],
      'health_body': [
        'You ignored what your body was telling you',
        'You pushed past the warning signs',
        'You treated symptoms instead of causes',
        'You powered through when rest was the answer',
        'You let it get worse before paying attention',
        'You dismissed the signal until it screamed',
        'You knew something was off but kept going anyway',
        'You waited too long to listen',
        'You prioritized everything except your own body',
        'You ran the system into the ground',
      ],
      'spirituality_meaning': [
        'You searched for answers then abandoned them before they landed',
        'You found something real then doubted it away',
        'You craved meaning but resisted stillness',
        'You touched depth then retreated to the surface',
        'You asked the big questions then distracted yourself',
        'You glimpsed something true then looked away',
        'You wanted to believe but could not let yourself',
        'You sought connection then ran from what you found',
        'You reached for transcendence then called it foolish',
        'You needed more and settled for less',
      ],
      'money_security': [
        'You built security then tore it down',
        'You saved then spent it all at once',
        'You planned carefully then sabotaged the plan',
        'You got close to stable then created chaos',
        'You accumulated then felt guilty for having',
        'You protected then punished yourself for it',
        'You earned more and felt less secure',
        'You restricted then released in the worst moment',
        'You hoarded then gave away what you needed',
        'You chased enough and never arrived',
      ],
      'family_roots': [
        'You carried them but would not let them carry you',
        'You protected everyone else and left yourself exposed',
        'You gave what you never got',
        'You stayed strong for them and fell apart alone',
        'You absorbed their weight and called it love',
        'You held the family together while you crumbled',
        'You kept the peace by losing yourself',
        'You showed up for them but never asked for the same',
        'You parented everyone including yourself',
        'You sacrificed without saying what it cost',
      ],
    };

    // Generic fallback variations (used if domain not in bank)
    const genericVariations = [
      'Something familiar showed up again',
      'The same thing returned in a different form',
      'You recognized this even before you named it',
      'It appeared again, wearing new clothes',
      'The pattern surfaced whether you wanted it to or not',
      'You saw it coming and still could not stop it',
      'It found you again like it always does',
      'The cycle continued even as you noticed it',
      'You caught yourself doing it again',
      'It returned like an old habit you thought you broke',
    ];

    // Get the variation bank for this domain, or use generic
    const variations = domainId && variationBanks[domainId] 
      ? variationBanks[domainId] 
      : genericVariations;

    // Use weekIndex to select a unique variation (modulo to handle overflow)
    const variationIndex = weekIndex % variations.length;
    
    return variations[variationIndex];
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
  // RENDER: TIMELINE SECTION (PRIMARY)
  // ============================================================================

  const renderWeekEntry = (week: WeekEntry, index: number) => {
    const isExpanded = expandedWeek === week.week_start;
    const weekLabel = formatDateRange(week.week_start, week.week_end);
    
    if (!week.top_domain) return null;
    
    // Use index to get unique behavioral variation for this week
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
            {isExpanded ? '−' : '+'}
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

  const renderTimelineSection = () => {
    if (timelineLoading) {
      return (
        <View style={styles.loadingSection}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Building your pattern timeline...
          </Text>
        </View>
      );
    }

    if (!timeline || !timeline.weeks || timeline.weeks.length === 0) {
      return (
        <View style={[styles.emptySection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.emptySectionIcon]}>◷</Text>
          <Text style={[styles.emptySectionTitle, { color: theme.text }]}>
            Your timeline is still forming
          </Text>
          <Text style={[styles.emptySectionText, { color: theme.textSecondary }]}>
            As patterns accumulate over time, you'll see when they've appeared before.
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
      <View style={styles.section}>
        {/* HERO: Human Pattern Phrase - First thing user sees */}
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

        {/* Week by Week instances */}
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
  // RENDER: ARCHETYPE SECTION (LAST - meaning after evidence)
  // ============================================================================

  const renderArchetypeSection = () => {
    return (
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
            YOUR PATTERN IDENTITY
          </Text>
        </View>
        
        {/* PatternArchetypeCard handles its own loading/data */}
        <PatternArchetypeCard />
        
        {/* Copy direction: NOT "You are this" but "This tends to show up when..." */}
        <View style={[styles.archetypeNote, { borderColor: theme.border }]}>
          <Text style={[styles.archetypeNoteText, { color: theme.textTertiary }]}>
            This identity emerges from the patterns you've shown over time — not a fixed label, but a recognition of what tends to return.
          </Text>
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
        style={styles.content}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={timelineRefreshing}
            onRefresh={handleRefresh}
            tintColor={theme.textTertiary}
          />
        }
      >
        {/* SECTION 1: TIMELINE (PRIMARY) - Proof of recurrence */}
        {renderTimelineSection()}
        
        {/* SECTION 2: THIS WEEK - What's active now */}
        {renderThisWeekSection()}
        
        {/* SECTION 3: ARCHETYPE (LAST) - Meaning after evidence */}
        {renderArchetypeSection()}
        
        {/* REFLECTION PROMPT */}
        {renderReflectionPrompt()}
        
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
