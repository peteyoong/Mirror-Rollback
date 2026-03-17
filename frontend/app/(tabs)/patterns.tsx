import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api, { getPatternInterpretation, PatternInterpretation } from '../../services/api';
import { useForumContext } from '../../contexts/ForumContext';
import { InlineReflectButton } from '../../components/UniversalReflectButton';
import { FullSynthesis, SynthesisData } from '../../components/CrossLensSynthesis';
import { ChartResonanceSection, PatternResonanceSummary } from '../../components/lifeline/ChartResonance';
import PatternGraphCard from '../../components/patterns/PatternGraphCard';

// Enable LayoutAnimation for Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// ============================================================================
// INTERFACES
// ============================================================================

interface TransitDetail {
  planet: string;
  aspect: string;
  target: string;
  sign: string;
}

interface MatchedSignal {
  source: string;
  label: string;
  sphere_name?: string;
  detail?: string;
  transit_data?: TransitDetail[];
}

interface PatternDomain {
  category_id: string;
  category_name: string;
  signal_strength: 'quiet' | 'present' | 'recurring';
  pattern_score: number;
  signal_count: number;
  trend: 'rising' | 'steady' | 'fading';
  matched_sources: string[];
  matched_signals: MatchedSignal[];
  summary: string;
  synthesis?: string;
}

interface PatternGraphResponse {
  success: boolean;
  categories: PatternDomain[];
  summary: {
    active_categories: number;
    emerging_categories: number;
    total_signals: number;
  };
  pattern_tensions: any[];
  updated_at: string;
}

// Weekly Types
interface TopDomain {
  domain: string;
  domain_id: string;
  trend: 'rising' | 'steady' | 'softening' | 'emerging';
  weekly_score: number;
  days_present: number;
  timing_amplified: boolean;
  evidence_summary: string[];
}

interface WeeklySummary {
  week_start: string;
  week_end: string;
  top_domains: TopDomain[];
  all_domains: any[];
  cross_week_shift: string | null;
  narrative: string;
  reflection_prompt: string;
  evidence_sources: string[];
  has_timing_influence: boolean;
}

// Timeline Types
interface WeekEntry {
  week_start: string;
  week_end: string;
  top_domain: string | null;
  top_domain_id: string | null;
  secondary_domains: string[];
  secondary_domain_ids: string[];
  trend_map: Record<string, string>;
  timing_amplified_domains: string[];
  narrative: string;
  reflection_prompt: string;
}

interface TimelineInsights {
  most_recurring_domain: string | null;
  strongest_recent_domain: string | null;
  volatile_domain: string | null;
  stable_domain: string | null;
  reemerging_domain: string | null;
}

interface TimelineData {
  range_label: string;
  weeks: WeekEntry[];
  insights: TimelineInsights;
  narrative_summary: string;
  reflection_prompt: string;
  is_partial: boolean;
  weeks_available: number;
}

// ============================================================================
// DOMAIN CONTENT - Deeper synthesis and reflection prompts
// ============================================================================

interface DomainContent {
  quietSynthesis: string;
  quietShowUp?: string;
  presentSynthesis: string;
  presentShowUp?: string;
  recurringSynthesis: string;
  recurringShowUp?: string;
  reflectionPrompt: string;
}

const DOMAIN_CONTENT: Record<string, DomainContent> = {
  'energy_vitality': {
    quietSynthesis: "Your energy may be in a quieter phase right now. This doesn't mean something is wrong—sometimes the body and spirit need rest before the next movement becomes clear.",
    presentSynthesis: "Something around energy, vitality, or the pace of your life may be surfacing. This domain can become active when the body is asking for attention—whether through fatigue, restlessness, or a subtle sense that something needs to shift.",
    presentShowUp: "One way this pattern can appear is through the tension between what you want to do and what your energy actually allows.",
    recurringSynthesis: "A recurring theme around energy and vitality seems to be present across your reflections. This may point to a deeper question about how you sustain yourself—not just physically, but emotionally and spiritually.",
    recurringShowUp: "This pattern can sometimes show up as cycles of depletion and recovery, or as a growing awareness that something in how you're living may need to change.",
    reflectionPrompt: "What is your energy asking you to notice right now?"
  },
  'emotional_landscape': {
    quietSynthesis: "The emotional landscape may feel quieter at the moment. This can be a time of integration, or simply a pause between waves of feeling.",
    presentSynthesis: "Emotional themes may be moving through your inner world right now. This domain often becomes active when feelings are asking for acknowledgment.",
    presentShowUp: "One way this can show up is through mood shifts that feel disconnected from external events, or through recurring feelings that don't quite resolve.",
    recurringSynthesis: "Emotional patterns seem to be surfacing repeatedly in your reflections. This may suggest that something in your inner life is asking for deeper attention.",
    recurringShowUp: "Sometimes this pattern shows up as a particular emotion that keeps returning, or as a sense that your emotional life has its own rhythm.",
    reflectionPrompt: "What emotion might be asking for your attention?"
  },
  'identity_direction': {
    quietSynthesis: "Questions of identity and direction may be resting for now. This can be a period of simply being, without the pressure of becoming.",
    presentSynthesis: "A quieter question may be surfacing around self-trust, worth, or permission to move forward.",
    presentShowUp: "One way this pattern can appear is through hesitation that feels deeper than practical uncertainty.",
    recurringSynthesis: "Themes around identity and direction seem to be recurring in your inner world. This may point to a deeper process of self-definition.",
    recurringShowUp: "This pattern can sometimes show up as a persistent question about what you really want, or as a tension between external expectations and internal truth.",
    reflectionPrompt: "What part of yourself is seeking expression or acknowledgment?"
  },
  'mind_meaning': {
    quietSynthesis: "The mind may be in a quieter phase right now—less focused on making sense of things, more present to experience itself.",
    presentSynthesis: "Something around thinking, understanding, or meaning-making may be active.",
    presentShowUp: "One way this can show up is through mental restlessness, overthinking, or a sense that understanding something will bring relief.",
    recurringSynthesis: "Patterns around mind and meaning seem to be recurring in your reflections.",
    recurringShowUp: "Sometimes this pattern shows up as a persistent question that doesn't have a clear answer.",
    reflectionPrompt: "What is your mind trying to understand or make sense of?"
  },
  'expression_action': {
    quietSynthesis: "Expression and action may be in a quieter phase. This can be a time of gathering, preparing, or simply being.",
    presentSynthesis: "Something around expression, creativity, or taking action may be surfacing.",
    presentShowUp: "One way this can show up is through creative restlessness, or a feeling that something wants to be said.",
    recurringSynthesis: "Themes around expression and action seem to be recurring in your reflections.",
    recurringShowUp: "Sometimes this pattern shows up as a persistent question about voice, visibility, or impact.",
    reflectionPrompt: "What wants to be expressed or created through you?"
  },
  'relationships_boundaries': {
    quietSynthesis: "Relational themes may be quieter right now. This can be a time of being present with yourself.",
    presentSynthesis: "Something around relationships, boundaries, or connection may be surfacing.",
    presentShowUp: "One way this can show up is through a sense of being pulled between your own needs and others' expectations.",
    recurringSynthesis: "Patterns around relationships and boundaries seem to be recurring in your reflections.",
    recurringShowUp: "Sometimes this pattern shows up as a persistent question about where you end and others begin.",
    reflectionPrompt: "Where might your connections be asking for care or attention?"
  },
  'growth_transformation': {
    quietSynthesis: "Growth and transformation may be in a quieter phase. Sometimes the most profound changes happen invisibly.",
    presentSynthesis: "Something around change, growth, or transformation may be surfacing.",
    presentShowUp: "One way this can show up is through a sense of being between identities, or through the discomfort that comes before a shift.",
    recurringSynthesis: "Themes around growth and transformation seem to be recurring in your reflections.",
    recurringShowUp: "Sometimes this pattern shows up as a feeling of being on the edge of something new.",
    reflectionPrompt: "What change might be ready to happen in you?"
  }
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

type TabType = 'patterns' | 'weekly' | 'timeline' | 'signals';

// Expanded section tracking for accordion sections within a domain
type ExpandedSection = 'story' | 'pattern' | 'challenge' | 'genius' | 'experiments' | null;

export default function PatternsScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { isInForumContext, forumId, forumName } = useForumContext();
  
  // Tab State
  const [activeTab, setActiveTab] = useState<TabType>('patterns');
  
  // Patterns State
  const [domains, setDomains] = useState<PatternDomain[]>([]);
  const [patternsLoading, setPatternsLoading] = useState(true);
  const [patternsRefreshing, setPatternsRefreshing] = useState(false);
  const [patternsError, setPatternsError] = useState<string | null>(null);
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null);
  
  // New: Pattern interpretation cache
  const [interpretations, setInterpretations] = useState<Record<string, PatternInterpretation>>({});
  const [loadingInterpretation, setLoadingInterpretation] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, Set<string>>>({});
  
  // New: Track which inner tab is active for each domain (interpretation vs signals)
  const [domainInnerTab, setDomainInnerTab] = useState<Record<string, 'interpretation' | 'signals'>>({});
  
  // Weekly State
  const [weeklySummary, setWeeklySummary] = useState<WeeklySummary | null>(null);
  const [weeklyLoading, setWeeklyLoading] = useState(true);
  const [weeklyRefreshing, setWeeklyRefreshing] = useState(false);
  const [weeklyError, setWeeklyError] = useState<string | null>(null);
  
  // Timeline State
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(true);
  const [timelineRefreshing, setTimelineRefreshing] = useState(false);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [expandedWeek, setExpandedWeek] = useState<string | null>(null);
  
  // Cross-Lens Synthesis State
  const [synthesis, setSynthesis] = useState<SynthesisData | null>(null);
  const [synthesisLoading, setSynthesisLoading] = useState(true);
  
  // Chart Resonance State (for Pattern Lens section)
  const [chartResonances, setChartResonances] = useState<PatternResonanceSummary[]>([]);
  
  // Lunar Cycle State (for Reflectors - Task 49 & 50)
  const [lunarCycle, setLunarCycle] = useState<{
    is_reflector: boolean;
    moon_phase: string;
    moon_icon: string;
    lunar_day: number;
    phase_energy: string;
    pattern_lens_message?: string;
    reflection_message?: string;
    reflective_question?: string;
    days_until_new_moon: number;
    cycle_progress: number;
    // Task 50: Lunar Gate data
    current_moon_gate?: number;
    gate_line?: number;
    gate_formatted?: string;
    gate_title?: string;
    gate_theme?: string;
    center?: string;
    gate_reflection_message?: string;
    gate_reflective_question?: string;
  } | null>(null);

  // ============================================================================
  // DATA LOADING
  // ============================================================================

  const fetchPatterns = async (showRefresh = false) => {
    if (!user?.id) return;
    
    if (showRefresh) setPatternsRefreshing(true);
    else setPatternsLoading(true);
    
    try {
      // Fetch patterns and resonances in parallel
      const [patternsRes, resonancesRes] = await Promise.all([
        api.get<PatternGraphResponse>(`/pattern-graph/${user.id}`),
        api.get<{
          success: boolean;
          pattern_summary: PatternResonanceSummary[];
        }>(`/lifeline/${user.id}/resonances`).catch(() => ({ data: { success: false, pattern_summary: [] } })),
      ]);
      
      if (patternsRes.data?.success) {
        setDomains(patternsRes.data.categories || []);
        setPatternsError(null);
      } else {
        setPatternsError('Failed to load patterns');
      }
      
      // Store chart resonance summary for Pattern Lens section
      if (resonancesRes.data?.success && resonancesRes.data.pattern_summary) {
        setChartResonances(resonancesRes.data.pattern_summary);
      }
      
      // Fetch lunar cycle data for Reflectors (Task 49)
      try {
        const lunarRes = await api.get(`/lunar-cycle/${user.id}`);
        if (lunarRes.data) {
          setLunarCycle(lunarRes.data);
          console.log('[Patterns] Lunar cycle:', lunarRes.data.is_reflector ? 'Reflector user' : 'Non-Reflector');
        }
      } catch (lunarErr) {
        console.log('[Patterns] Lunar cycle fetch failed:', lunarErr);
      }
    } catch (err) {
      console.error('[Patterns] Error:', err);
      setPatternsError('Unable to load patterns');
    } finally {
      setPatternsLoading(false);
      setPatternsRefreshing(false);
    }
  };

  const fetchWeekly = async (showRefresh = false) => {
    if (!user?.id) return;
    
    if (showRefresh) setWeeklyRefreshing(true);
    else setWeeklyLoading(true);
    
    try {
      const response = await api.get(`/weekly-patterns/${user.id}`);
      if (response.data?.success) {
        setWeeklySummary(response.data.weekly_summary);
        setWeeklyError(null);
      } else {
        setWeeklyError('Failed to load weekly patterns');
      }
    } catch (err) {
      console.error('[Weekly] Error:', err);
      setWeeklyError('Unable to load weekly summary');
    } finally {
      setWeeklyLoading(false);
      setWeeklyRefreshing(false);
    }
  };

  const fetchTimeline = async (showRefresh = false) => {
    if (!user?.id) return;
    
    if (showRefresh) setTimelineRefreshing(true);
    else setTimelineLoading(true);
    
    try {
      const response = await api.get(`/pattern-timeline/${user.id}?weeks=8`);
      if (response.data?.success) {
        setTimeline(response.data.timeline);
        setTimelineError(null);
      } else {
        setTimelineError('Failed to load timeline');
      }
    } catch (err) {
      console.error('[Timeline] Error:', err);
      setTimelineError('Unable to load pattern timeline');
    } finally {
      setTimelineLoading(false);
      setTimelineRefreshing(false);
    }
  };

  const fetchSynthesis = async () => {
    if (!user?.id) return;
    setSynthesisLoading(true);
    
    try {
      const response = await api.get(`/synthesis/${user.id}`);
      if (response.data) {
        setSynthesis(response.data);
      }
    } catch (err) {
      console.log('[Synthesis] Failed to load:', err);
      setSynthesis(null);
    } finally {
      setSynthesisLoading(false);
    }
  };

  useEffect(() => {
    fetchPatterns();
    fetchWeekly();
    fetchTimeline();
    fetchSynthesis();
  }, [user?.id]);

  // ============================================================================
  // HELPER FUNCTIONS
  // ============================================================================

  const getStrengthLabel = (strength: string): string => {
    switch (strength) {
      case 'recurring': return 'Strong Signal';
      case 'present': return 'Present';
      case 'emerging': return 'Early Signal';
      case 'stable': return 'Consistent';
      case 'quiet': return 'Quiet';
      case 'context': return 'Lens-based';
      default: return strength;
    }
  };

  const getStrengthColor = (strength: string): string => {
    switch (strength) {
      case 'recurring': return '#7dd3a0';  // Green - active/frequent
      case 'emerging': return '#f5b942';   // Amber/Gold - new/rising
      case 'present': return '#a0c4e8';    // Blue - occasional
      case 'stable': return '#9b8ac4';     // Purple - consistent/long-term
      case 'context': return '#c9a07d';    // Bronze/Brown - lens-activated
      case 'quiet': return theme.textTertiary;
      default: return theme.textTertiary;
    }
  };

  const getDomainContent = (domainId: string, strength: string) => {
    const content = DOMAIN_CONTENT[domainId];
    if (!content) {
      return {
        synthesis: "This domain is being observed.",
        prompt: "What do you notice here?"
      };
    }
    
    // Map new status types to existing content
    switch (strength) {
      case 'recurring':
        return {
          synthesis: content.recurringSynthesis,
          prompt: content.reflectionPrompt
        };
      case 'stable':
        // Stable uses recurring content but feels more established
        return {
          synthesis: content.recurringSynthesis,
          prompt: content.reflectionPrompt
        };
      case 'emerging':
        // Emerging uses present content with emphasis on newness
        return {
          synthesis: content.presentSynthesis,
          prompt: content.reflectionPrompt
        };
      case 'present':
        return {
          synthesis: content.presentSynthesis,
          prompt: content.reflectionPrompt
        };
      case 'context':
        // Context is lens-activated, use present synthesis
        return {
          synthesis: content.presentSynthesis,
          prompt: content.reflectionPrompt
        };
      case 'quiet':
      default:
        return {
          synthesis: content.quietSynthesis,
          prompt: content.reflectionPrompt
        };
    }
  };

  const getSourceDisplayName = (source: string): string => {
    const sourceNames: Record<string, string> = {
      'gene_keys': 'Gene Keys',
      'human_design': 'Human Design',
      'journal': 'Journal & Reflections',
      'mirror_chat': 'Mirror Chat',
    };
    return sourceNames[source] || source;
  };

  const formatSignalLabel = (signal: MatchedSignal): string => {
    if (signal.source === 'gene_keys' && signal.detail?.includes('Gene Key')) {
      const match = signal.detail.match(/Gene Key (\d+)/);
      if (match) return `Gene Key ${match[1]} — ${signal.label}`;
    }
    if (signal.sphere_name) return `${signal.label} · ${signal.sphere_name}`;
    return signal.label;
  };

  const countSignalsBySource = (signals: MatchedSignal[]): Record<string, number> => {
    const counts: Record<string, number> = {};
    signals.forEach(s => {
      counts[s.source] = (counts[s.source] || 0) + 1;
    });
    return counts;
  };

  // Fetch interpretation when expanding a domain
  const fetchInterpretation = useCallback(async (domainId: string) => {
    if (!user?.id || interpretations[domainId]) return;
    
    setLoadingInterpretation(domainId);
    try {
      const response = await getPatternInterpretation(user.id, domainId);
      if (response.success && response.interpretation) {
        setInterpretations(prev => ({
          ...prev,
          [domainId]: response.interpretation
        }));
      } else {
        // Handle case where API returns success=false or no interpretation
        console.warn('[Patterns] No interpretation in response for', domainId);
        setInterpretations(prev => ({
          ...prev,
          [domainId]: {
            story: 'This pattern insight is currently unavailable. Please try again later.',
            pattern: '',
            challenge: '',
            genius: '',
            experiments: []
          }
        }));
      }
    } catch (err) {
      console.error('[Patterns] Error fetching interpretation:', err);
      // Set a fallback interpretation on error so it doesn't stay stuck on loading
      setInterpretations(prev => ({
        ...prev,
        [domainId]: {
          story: 'Unable to load this insight right now. Please check your connection and try again.',
          pattern: '',
          challenge: '',
          genius: '',
          experiments: []
        }
      }));
    } finally {
      setLoadingInterpretation(null);
    }
  }, [user?.id, interpretations]);

  const toggleExpanded = (domainId: string, domainName: string) => {
    const newExpanded = expandedDomain === domainId ? null : domainId;
    if (Platform.OS !== 'web') {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    }
    setExpandedDomain(newExpanded);
    
    // Fetch interpretation when expanding
    if (newExpanded) {
      fetchInterpretation(domainId);
    }
  };

  // Toggle section within a domain card
  const toggleSection = (domainId: string, section: string) => {
    if (Platform.OS !== 'web') {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    }
    setExpandedSections(prev => {
      const domainSections = prev[domainId] || new Set();
      const newSet = new Set(domainSections);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return { ...prev, [domainId]: newSet };
    });
  };

  // Toggle inner tab for domain card (interpretation vs signals)
  const toggleDomainInnerTab = (domainId: string, tab: 'interpretation' | 'signals') => {
    if (Platform.OS !== 'web') {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    }
    setDomainInnerTab(prev => ({ ...prev, [domainId]: tab }));
  };

  // Get the current inner tab for a domain (default: interpretation)
  const getDomainInnerTab = (domainId: string): 'interpretation' | 'signals' => {
    return domainInnerTab[domainId] || 'interpretation';
  };

  // ============================================================================
  // SIGNAL FORMATTING HELPERS - Human-readable signal descriptions
  // ============================================================================

  // Astrological symbol mappings
  const PLANET_SYMBOLS: Record<string, string> = {
    'Sun': '☉',
    'Moon': '☽',
    'Mercury': '☿',
    'Venus': '♀',
    'Mars': '♂',
    'Jupiter': '♃',
    'Saturn': '♄',
    'Uranus': '♅',
    'Neptune': '♆',
    'Pluto': '♇',
    'North Node': '☊',
    'South Node': '☋',
  };

  const ASPECT_SYMBOLS: Record<string, string> = {
    'conjunction': '☌',
    'opposition': '☍',
    'square': '□',
    'trine': '△',
    'sextile': '⚹',
  };

  const SIGN_SYMBOLS: Record<string, string> = {
    'Aries': '♈',
    'Taurus': '♉',
    'Gemini': '♊',
    'Cancer': '♋',
    'Leo': '♌',
    'Virgo': '♍',
    'Libra': '♎',
    'Scorpio': '♏',
    'Sagittarius': '♐',
    'Capricorn': '♑',
    'Aquarius': '♒',
    'Pisces': '♓',
  };

  // Format transit data into readable symbol string
  const formatTransitSymbol = (transit: any): string => {
    const planet = PLANET_SYMBOLS[transit.planet] || transit.planet;
    const aspect = transit.aspect ? ASPECT_SYMBOLS[transit.aspect] : null;
    const target = transit.target ? PLANET_SYMBOLS[transit.target] || transit.target : null;
    const sign = transit.sign ? SIGN_SYMBOLS[transit.sign] : null;

    if (aspect && target) {
      // Transit to natal: ☉ ☌ ♄ (Sun conjunct natal Saturn)
      return `${planet} ${aspect} ${target}`;
    } else if (sign) {
      // Planet in sign: ☽ in ♋ (Moon in Cancer)
      return `${planet} in ${sign}`;
    } else {
      // Just the planet
      return planet;
    }
  };

  // Get human-readable transit description
  const getTransitDescription = (transit: any): string => {
    const planet = transit.planet;
    const aspect = transit.aspect;
    const target = transit.target;
    const sign = transit.sign;

    if (aspect && target) {
      const aspectWords: Record<string, string> = {
        'conjunction': 'meeting',
        'opposition': 'facing',
        'square': 'challenging',
        'trine': 'flowing with',
        'sextile': 'supporting',
      };
      return `${planet} ${aspectWords[aspect] || aspect} natal ${target}`;
    } else if (sign) {
      return `${planet} moving through ${sign}`;
    } else {
      return `${planet} influence`;
    }
  };

  // Format a single signal into human-readable text
  const formatSignalDescription = (signal: MatchedSignal): { title: string; description: string } => {
    const source = signal.source;
    const label = signal.label || '';
    const detail = signal.detail || '';
    const sphere = signal.sphere_name;

    switch (source) {
      case 'journal':
        return {
          title: 'Journal',
          description: `Recent reflections suggest themes around ${label.replace('Journal reflection (', '').replace(')', '').replace(/, /g, ' and ')}.`
        };
      
      case 'mirror_chat':
        return {
          title: 'Mirror',
          description: `Reflections point to processing around ${detail || 'this theme'}.`
        };
      
      case 'gene_keys':
        if (sphere) {
          return {
            title: 'Lens Context',
            description: `${label}${sphere ? ` (${sphere})` : ''} — a quality in your design that may resonate with this pattern.`
          };
        }
        return {
          title: 'Lens Context',
          description: `${label} appears in your chart, suggesting a natural sensitivity to this area.`
        };
      
      case 'human_design':
        const hdDetail = detail || label;
        return {
          title: 'Lens Context',
          description: `${hdDetail} in your Human Design connects to themes in this domain.`
        };
      
      case 'astrology_transit':
        return {
          title: 'Enhanced Energy',
          description: `A current timing influence may be amplifying ${detail || 'this pattern'}. This is temporary and part of natural cycles.`
        };
      
      case 'pattern_memory':
        return {
          title: 'Pattern Memory',
          description: `This domain has recurred over recent weeks, suggesting an ongoing process.`
        };
      
      case 'enneagram':
        return {
          title: 'Lens Context',
          description: `Your Enneagram type shows a natural relationship with ${detail || 'this area'}.`
        };
      
      default:
        return {
          title: 'Signal',
          description: label || detail || 'A signal was detected in this area.'
        };
    }
  };

  // Group signals by type for cleaner presentation
  const groupSignalsByType = (signals: MatchedSignal[]): Record<string, MatchedSignal[]> => {
    const groups: Record<string, MatchedSignal[]> = {};
    
    signals.forEach(signal => {
      let groupKey = 'Other';
      
      switch (signal.source) {
        case 'journal':
          groupKey = 'Journal';
          break;
        case 'mirror_chat':
          groupKey = 'Mirror';
          break;
        case 'gene_keys':
        case 'human_design':
        case 'enneagram':
          groupKey = 'Lens Context';
          break;
        case 'astrology_transit':
          groupKey = 'Enhanced Energy';
          break;
        case 'pattern_memory':
          groupKey = 'Pattern Memory';
          break;
      }
      
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(signal);
    });
    
    return groups;
  };

  // Get signal group icon
  const getSignalGroupIcon = (groupKey: string): string => {
    switch (groupKey) {
      case 'Journal': return '📝';
      case 'Mirror': return '💭';
      case 'Lens Context': return '🔮';
      case 'Enhanced Energy': return '✨';
      case 'Pattern Memory': return '🔄';
      default: return '•';
    }
  };

  const handleJournalTrigger = (domainName: string, prompt: string) => {
    router.push({
      pathname: '/(tabs)/journal',
      params: {
        prefillPrompt: prompt,
        journalSource: 'pattern_domain',
        category: domainName,
      }
    });
  };

  // Weekly helpers
  const formatDateRange = (start: string, end: string): string => {
    const startDate = new Date(start + 'T00:00:00');
    const endDate = new Date(end + 'T00:00:00');
    const formatOptions: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
    return `${startDate.toLocaleDateString('en-US', formatOptions)} – ${endDate.toLocaleDateString('en-US', formatOptions)}`;
  };

  const getTrendLabel = (trend: string): string => {
    switch (trend) {
      case 'rising': return 'Rising this week';
      case 'softening': return 'Softening this week';
      case 'emerging': return 'Emerging this week';
      case 'steady': return 'Steady this week';
      default: return 'Present this week';
    }
  };

  const getTrendColor = (trend: string): string => {
    switch (trend) {
      case 'rising': return '#7dd3a0';
      case 'emerging': return '#a0c4e8';
      case 'softening': return '#e8c4a0';
      case 'steady': return theme.textSecondary;
      default: return theme.textSecondary;
    }
  };

  // Timeline helpers
  const getTrendChipLabel = (trend: string): string => {
    switch (trend) {
      case 'rising': return 'Growing';
      case 'steady': return 'Steady';
      case 'softening': return 'Easing';
      case 'emerging': return 'Emerging';
      default: return 'Present';
    }
  };

  const getTrendChipColor = (trend: string): { bg: string; text: string } => {
    switch (trend) {
      case 'rising': return { bg: 'rgba(125, 211, 160, 0.15)', text: '#7dd3a0' };
      case 'emerging': return { bg: 'rgba(160, 196, 232, 0.15)', text: '#a0c4e8' };
      case 'softening': return { bg: 'rgba(232, 196, 160, 0.15)', text: '#e8c4a0' };
      default: return { bg: 'rgba(255, 255, 255, 0.08)', text: theme.textTertiary };
    }
  };

  const toggleWeekExpanded = (weekStart: string) => {
    if (Platform.OS !== 'web') {
      LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    }
    setExpandedWeek(expandedWeek === weekStart ? null : weekStart);
  };

  // ============================================================================
  // SEGMENTED CONTROL
  // ============================================================================

  const renderSegmentedControl = () => (
    <View style={[styles.segmentedControl, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {(['patterns', 'weekly', 'timeline', 'signals'] as TabType[]).map((tab) => (
        <TouchableOpacity
          key={tab}
          style={[
            styles.segmentButton,
            activeTab === tab && { backgroundColor: theme.accent + '20' }
          ]}
          onPress={() => setActiveTab(tab)}
          activeOpacity={0.7}
        >
          <Text style={[
            styles.segmentText,
            { color: activeTab === tab ? theme.accent : theme.textSecondary }
          ]}>
            {tab === 'patterns' ? 'Patterns' : tab === 'weekly' ? 'Weekly' : tab === 'timeline' ? 'Timeline' : 'Signals'}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  // ============================================================================
  // RENDER: PATTERNS TAB - New 5-Section Accordion Structure
  // ============================================================================

  // Helper to render a collapsible section
  const renderCollapsibleSection = (
    domainId: string,
    sectionKey: string,
    title: string,
    content: string | string[] | undefined,
    isLoading: boolean
  ) => {
    const domainSections = expandedSections[domainId] || new Set();
    const isOpen = domainSections.has(sectionKey);
    
    // Handle array content (experiments)
    const isArray = Array.isArray(content);
    const hasContent = content && (isArray ? content.length > 0 : content.trim() !== '');
    
    return (
      <TouchableOpacity
        key={sectionKey}
        style={[styles.sectionAccordion, { borderBottomColor: theme.border }]}
        onPress={() => toggleSection(domainId, sectionKey)}
        activeOpacity={0.7}
      >
        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>{title}</Text>
          <Text style={[styles.sectionChevron, { color: theme.textTertiary }]}>
            {isOpen ? '−' : '+'}
          </Text>
        </View>
        
        {isOpen && (
          <View style={styles.sectionContent}>
            {isLoading ? (
              <ActivityIndicator size="small" color={theme.textTertiary} />
            ) : isArray && hasContent ? (
              <View style={styles.experimentsList}>
                {(content as string[]).map((experiment, idx) => (
                  <View key={idx} style={styles.experimentItem}>
                    <Text style={[styles.experimentBullet, { color: theme.accent }]}>•</Text>
                    <Text style={[styles.experimentText, { color: theme.textSecondary }]}>
                      {experiment}
                    </Text>
                  </View>
                ))}
              </View>
            ) : hasContent ? (
              <Text style={[styles.sectionText, { color: theme.textSecondary }]}>
                {content as string}
              </Text>
            ) : (
              <Text style={[styles.sectionText, { color: theme.textTertiary, fontStyle: 'italic' }]}>
                Not available for this pattern.
              </Text>
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderDomainCard = (domain: PatternDomain) => {
    const strengthColor = getStrengthColor(domain.signal_strength);
    const isExpanded = expandedDomain === domain.category_id;
    const interpretation = interpretations[domain.category_id];
    const isLoadingThis = loadingInterpretation === domain.category_id;
    const currentInnerTab = getDomainInnerTab(domain.category_id);
    
    // Group signals for the Signals tab
    const signalGroups = groupSignalsByType(domain.matched_signals || []);
    const hasTransitEmphasis = domain.matched_signals?.some(s => s.source === 'astrology_transit');
    
    return (
      <View
        key={domain.category_id}
        style={[
          styles.accordionCard, 
          { 
            backgroundColor: theme.surface, 
            borderColor: isExpanded ? theme.accent + '40' : theme.border 
          }
        ]}
      >
        {/* Domain Header - Click to expand */}
        <TouchableOpacity
          style={styles.accordionHeader}
          onPress={() => toggleExpanded(domain.category_id, domain.category_name)}
          activeOpacity={0.7}
        >
          <View style={styles.accordionLeft}>
            <Text style={[styles.accordionTitle, { color: theme.text }]}>
              {domain.category_name}
            </Text>
          </View>
          <View style={styles.accordionRight}>
            <View style={[styles.statusBadge, { backgroundColor: strengthColor + '18' }]}>
              <Text style={[styles.statusText, { color: strengthColor }]}>
                {getStrengthLabel(domain.signal_strength)}
              </Text>
            </View>
            <Text style={[styles.accordionChevron, { color: theme.textTertiary }]}>
              {isExpanded ? '▲' : '▼'}
            </Text>
          </View>
        </TouchableOpacity>

        {/* Expanded Content */}
        {isExpanded && (
          <View style={[styles.accordionBody, { borderTopColor: theme.border }]}>
            
            {/* Inner Tab Control: Interpretation | Signals */}
            <View style={[styles.innerTabControl, { borderBottomColor: theme.border }]}>
              <TouchableOpacity
                style={[
                  styles.innerTab,
                  currentInnerTab === 'interpretation' && styles.innerTabActive,
                  currentInnerTab === 'interpretation' && { borderBottomColor: theme.accent }
                ]}
                onPress={() => toggleDomainInnerTab(domain.category_id, 'interpretation')}
              >
                <Text style={[
                  styles.innerTabText,
                  { color: currentInnerTab === 'interpretation' ? theme.accent : theme.textTertiary }
                ]}>
                  Interpretation
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.innerTab,
                  currentInnerTab === 'signals' && styles.innerTabActive,
                  currentInnerTab === 'signals' && { borderBottomColor: theme.accent }
                ]}
                onPress={() => toggleDomainInnerTab(domain.category_id, 'signals')}
              >
                <Text style={[
                  styles.innerTabText,
                  { color: currentInnerTab === 'signals' ? theme.accent : theme.textTertiary }
                ]}>
                  Signals
                </Text>
                {(domain.matched_signals?.length || 0) > 0 && (
                  <View style={[styles.signalBadge, { backgroundColor: theme.accent + '20' }]}>
                    <Text style={[styles.signalBadgeText, { color: theme.accent }]}>
                      {domain.matched_signals?.length || 0}
                    </Text>
                  </View>
                )}
              </TouchableOpacity>
            </View>

            {/* INTERPRETATION TAB CONTENT */}
            {currentInnerTab === 'interpretation' && (
              <View style={styles.innerTabContent}>
                {/* Loading indicator when fetching interpretation */}
                {isLoadingThis && !interpretation && (
                  <View style={styles.loadingInterpretation}>
                    <ActivityIndicator size="small" color={theme.accent} />
                    <Text style={[styles.loadingInterpretationText, { color: theme.textTertiary }]}>
                      Loading pattern insight...
                    </Text>
                  </View>
                )}
                
                {/* Section 1: Story */}
                {renderCollapsibleSection(
                  domain.category_id,
                  'story',
                  'Story',
                  interpretation?.story,
                  isLoadingThis && !interpretation
                )}
                
                {/* Section 2: Pattern */}
                {renderCollapsibleSection(
                  domain.category_id,
                  'pattern',
                  'Pattern',
                  interpretation?.pattern,
                  isLoadingThis && !interpretation
                )}
                
                {/* Section 3: Challenge */}
                {renderCollapsibleSection(
                  domain.category_id,
                  'challenge',
                  'Challenge',
                  interpretation?.challenge,
                  isLoadingThis && !interpretation
                )}
                
                {/* Section 4: Genius */}
                {renderCollapsibleSection(
                  domain.category_id,
                  'genius',
                  'Genius',
                  interpretation?.genius,
                  isLoadingThis && !interpretation
                )}
                
                {/* Section 5: Practical Experiments */}
                {renderCollapsibleSection(
                  domain.category_id,
                  'experiments',
                  'Practical Experiments',
                  interpretation?.experiments,
                  isLoadingThis && !interpretation
                )}
              </View>
            )}

            {/* SIGNALS TAB CONTENT */}
            {currentInnerTab === 'signals' && (
              <View style={styles.innerTabContent}>
                {/* Why This Pattern Section */}
                <Text style={[styles.signalsIntro, { color: theme.textSecondary }]}>
                  Here's what may be contributing to this pattern surfacing:
                </Text>

                {/* Signal Groups */}
                {Object.keys(signalGroups).length === 0 ? (
                  <Text style={[styles.noSignalsText, { color: theme.textTertiary }]}>
                    No specific signals detected yet. This domain may become active as you journal and reflect.
                  </Text>
                ) : (
                  <View style={styles.signalGroupsContainer}>
                    {Object.entries(signalGroups).map(([groupKey, signals]) => (
                      <View key={groupKey} style={styles.signalGroup}>
                        <View style={styles.signalGroupHeader}>
                          <Text style={styles.signalGroupIcon}>{getSignalGroupIcon(groupKey)}</Text>
                          <Text style={[styles.signalGroupTitle, { color: theme.text }]}>
                            {groupKey}
                          </Text>
                        </View>
                        <View style={styles.signalGroupItems}>
                          {signals.map((signal, idx) => {
                            const formatted = formatSignalDescription(signal);
                            return (
                              <View key={idx} style={[styles.signalItem, { borderLeftColor: theme.accent + '40' }]}>
                                <Text style={[styles.signalItemText, { color: theme.textSecondary }]}>
                                  {formatted.description}
                                </Text>
                              </View>
                            );
                          })}
                        </View>
                      </View>
                    ))}
                  </View>
                )}

                {/* Enhanced Energy Note with Transit Symbols */}
                {hasTransitEmphasis && (() => {
                  // Get the transit signal with its transit_data
                  const transitSignal = domain.matched_signals?.find(s => s.source === 'astrology_transit');
                  const transits = transitSignal?.transit_data || [];
                  const topTransits = transits.slice(0, 3); // Show top 2-3 transits
                  
                  return (
                    <View style={[styles.enhancedEnergyNote, { backgroundColor: theme.accent + '08', borderLeftColor: theme.accent }]}>
                      <Text style={[styles.enhancedEnergyTitle, { color: theme.accent }]}>
                        ✨ Timing Influence Active
                      </Text>
                      
                      {/* Transit Symbols Display */}
                      {topTransits.length > 0 && (
                        <View style={styles.transitSymbolsContainer}>
                          {topTransits.map((transit, idx) => (
                            <View key={idx} style={styles.transitSymbolRow}>
                              <Text style={[styles.transitSymbolText, { color: theme.text }]}>
                                {formatTransitSymbol(transit)}
                              </Text>
                              <Text style={[styles.transitDescText, { color: theme.textTertiary }]}>
                                {getTransitDescription(transit)}
                              </Text>
                            </View>
                          ))}
                        </View>
                      )}
                      
                      <Text style={[styles.enhancedEnergyText, { color: theme.textSecondary }]}>
                        These transits may be temporarily amplifying this pattern. This is natural and part of ongoing cycles.
                      </Text>
                    </View>
                  );
                })()}

                {/* Signal Sources Summary */}
                {domain.matched_sources && domain.matched_sources.length > 0 && (
                  <View style={[styles.sourcesSummary, { borderTopColor: theme.border }]}>
                    <Text style={[styles.sourcesSummaryLabel, { color: theme.textTertiary }]}>
                      Sources: {domain.matched_sources.map(s => 
                        s === 'journal' ? 'Journal' :
                        s === 'mirror_chat' ? 'Mirror' :
                        s === 'gene_keys' ? 'Gene Keys' :
                        s === 'human_design' ? 'Human Design' :
                        s === 'astrology_transit' ? 'Transits' :
                        s === 'enneagram' ? 'Enneagram' :
                        s
                      ).join(' • ')}
                    </Text>
                  </View>
                )}
              </View>
            )}
            
            {/* Reflect Button at Bottom - Always visible */}
            <View style={styles.reflectButtonContainer}>
              <InlineReflectButton
                source={{
                  lens: 'patterns',
                  type: 'domain',
                  name: domain.category_name,
                  id: domain.category_id,
                  value: getStrengthLabel(domain.signal_strength),
                }}
                prompt={interpretation?.story}
              />
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderPatternsTab = () => {
    if (patternsLoading) {
      return (
        <View style={[styles.centeredContent]}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading patterns...
          </Text>
        </View>
      );
    }

    if (patternsError || domains.length === 0) {
      return (
        <View style={[styles.centeredContent]}>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {patternsError || 'No patterns found'}
          </Text>
          <TouchableOpacity
            style={[styles.retryButton, { borderColor: theme.border }]}
            onPress={() => fetchPatterns()}
          >
            <Text style={[styles.retryText, { color: theme.accent }]}>Try Again</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <ScrollView
        style={styles.tabContent}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={patternsRefreshing}
            onRefresh={() => {
              fetchPatterns(true);
              fetchSynthesis();
            }}
            tintColor={theme.textSecondary}
          />
        }
      >
        {/* Cross-Lens Synthesis - Shown at top when available */}
        {(synthesis || synthesisLoading) && (
          <FullSynthesis synthesis={synthesis} isLoading={synthesisLoading} />
        )}

        <View style={styles.introSection}>
          <Text style={[styles.introDescription, { color: theme.textSecondary }]}>
            Patterns can emerge across different parts of life. This view gathers signals from your reflections and interpretive lenses.
          </Text>
        </View>

        <View style={styles.domainsSection}>
          {domains.map(domain => renderDomainCard(domain))}
        </View>
        
        {/* Chart Resonance Section */}
        {chartResonances.length > 0 && (
          <View style={[styles.resonanceSection, { paddingHorizontal: 16 }]}>
            <ChartResonanceSection resonances={chartResonances} />
          </View>
        )}
        
        {/* Lunar Reflection Cycle Section - Task 49 & 50 (Reflectors Only) */}
        {lunarCycle?.is_reflector && (
          <View style={[styles.lunarCycleSection, { paddingHorizontal: 16 }]}>
            <View style={[styles.lunarCycleCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              {/* Header */}
              <View style={styles.lunarCycleHeader}>
                <Text style={styles.lunarMoonIcon}>{lunarCycle.moon_icon}</Text>
                <Text style={[styles.lunarCycleTitle, { color: '#C0C8D4' }]}>
                  LUNAR REFLECTION CYCLE
                </Text>
              </View>
              
              {/* Phase Badge */}
              <View style={[styles.lunarPhaseBadge, { backgroundColor: 'rgba(192, 200, 212, 0.15)' }]}>
                <Text style={[styles.lunarPhaseBadgeText, { color: '#C0C8D4' }]}>
                  {lunarCycle.moon_phase} • Day {Math.round(lunarCycle.lunar_day)}
                </Text>
              </View>
              
              {/* Cycle Progress */}
              <View style={styles.lunarProgressContainer}>
                <View style={[styles.lunarProgressTrack, { backgroundColor: 'rgba(192, 200, 212, 0.2)' }]}>
                  <View 
                    style={[
                      styles.lunarProgressFill, 
                      { width: `${lunarCycle.cycle_progress * 100}%`, backgroundColor: '#C0C8D4' }
                    ]} 
                  />
                </View>
                <View style={styles.lunarProgressLabels}>
                  <Text style={[styles.lunarProgressLabel, { color: theme.textTertiary }]}>New</Text>
                  <Text style={[styles.lunarProgressLabel, { color: theme.textTertiary }]}>Full</Text>
                  <Text style={[styles.lunarProgressLabel, { color: theme.textTertiary }]}>New</Text>
                </View>
              </View>
              
              {/* Task 50: Current Lunar Gate Section */}
              {lunarCycle.current_moon_gate && (
                <View style={[styles.lunarGateSection, { borderTopColor: theme.border }]}>
                  <Text style={[styles.lunarGateSectionTitle, { color: '#A8B2C0' }]}>
                    CURRENT LUNAR GATE
                  </Text>
                  <View style={styles.lunarGateHeader}>
                    <Text style={[styles.lunarGateNumber, { color: '#C0C8D4' }]}>
                      Gate {lunarCycle.gate_formatted}
                    </Text>
                    <Text style={[styles.lunarGateTitle, { color: theme.text }]}>
                      {lunarCycle.gate_title}
                    </Text>
                  </View>
                  {lunarCycle.gate_theme && (
                    <Text style={[styles.lunarGateTheme, { color: theme.textTertiary }]}>
                      {lunarCycle.gate_theme}
                    </Text>
                  )}
                  {lunarCycle.center && (
                    <Text style={[styles.lunarGateCenter, { color: theme.textTertiary }]}>
                      {lunarCycle.center}
                    </Text>
                  )}
                </View>
              )}
              
              {/* Pattern Lens Message */}
              {lunarCycle.pattern_lens_message && (
                <Text style={[styles.lunarPatternMessage, { color: theme.textSecondary }]}>
                  {lunarCycle.pattern_lens_message}
                </Text>
              )}
              
              {/* Timing Info */}
              <View style={[styles.lunarTimingRow, { borderTopColor: theme.border }]}>
                <View style={styles.lunarTimingItem}>
                  <Text style={[styles.lunarTimingValue, { color: '#C0C8D4' }]}>
                    {Math.round(lunarCycle.days_until_new_moon)}d
                  </Text>
                  <Text style={[styles.lunarTimingLabel, { color: theme.textTertiary }]}>
                    to New Moon
                  </Text>
                </View>
              </View>
              
              {/* Reflective Question - now gate-based when available */}
              {(lunarCycle.gate_reflective_question || lunarCycle.reflective_question) && (
                <View style={[styles.lunarQuestionBlock, { borderTopColor: theme.border }]}>
                  <Text style={[styles.lunarQuestionLabel, { color: '#A8B2C0' }]}>
                    TO NOTICE
                  </Text>
                  <Text style={[styles.lunarQuestionText, { color: theme.textSecondary }]}>
                    {lunarCycle.gate_reflective_question || lunarCycle.reflective_question}
                  </Text>
                </View>
              )}
            </View>
          </View>
        )}
      </ScrollView>
    );
  };

  // ============================================================================
  // RENDER: WEEKLY TAB
  // ============================================================================

  const renderWeeklyTab = () => {
    if (weeklyLoading) {
      return (
        <View style={[styles.centeredContent]}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Synthesizing your week...
          </Text>
        </View>
      );
    }

    if (weeklyError || !weeklySummary) {
      return (
        <View style={[styles.centeredContent]}>
          <Text style={styles.emptyIcon}>☽</Text>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {weeklyError || 'Unable to load weekly patterns'}
          </Text>
          <Text style={[styles.emptySubtext, { color: theme.textTertiary }]}>
            Continue reflecting to see patterns emerge
          </Text>
        </View>
      );
    }

    return (
      <ScrollView
        style={styles.tabContent}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={weeklyRefreshing}
            onRefresh={() => fetchWeekly(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        <View style={styles.weeklyHeader}>
          <Text style={[styles.weeklySubtitle, { color: theme.textSecondary }]}>
            A gentle synthesis of what seemed to repeat, intensify, or shift.
          </Text>
          <Text style={[styles.dateRange, { color: theme.textTertiary }]}>
            Week of {formatDateRange(weeklySummary.week_start, weeklySummary.week_end)}
          </Text>
        </View>

        <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.narrative, { color: theme.textSecondary }]}>
            {weeklySummary.narrative}
          </Text>
        </View>

        {weeklySummary.top_domains.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Top Recurring Themes
            </Text>
            
            {weeklySummary.top_domains.map((domain, index) => (
              <View 
                key={domain.domain_id}
                style={[styles.weeklyDomainCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              >
                <View style={styles.weeklyDomainHeader}>
                  <Text style={[styles.weeklyDomainName, { color: theme.text }]}>
                    {domain.domain}
                  </Text>
                  <Text style={[styles.weeklyDomainTrend, { color: getTrendColor(domain.trend) }]}>
                    {getTrendLabel(domain.trend)}
                  </Text>
                </View>
                
                <Text style={[styles.weeklyDomainEvidence, { color: theme.textTertiary }]}>
                  {domain.evidence_summary.length > 0 
                    ? `Appeared through ${domain.evidence_summary.join(' and ').toLowerCase()}.`
                    : `Present across ${domain.days_present} days this week.`
                  }
                </Text>
                
                {domain.timing_amplified && (
                  <Text style={[styles.timingNote, { color: theme.textTertiary }]}>
                    ✦ Timing emphasis active
                  </Text>
                )}
              </View>
            ))}
          </View>
        )}

        {weeklySummary.evidence_sources.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              What May Have Shaped This Pattern
            </Text>
            
            <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              {weeklySummary.evidence_sources.map((source, index) => (
                <View key={index} style={styles.evidenceItem}>
                  <Text style={[styles.evidenceBullet, { color: theme.textTertiary }]}>•</Text>
                  <Text style={[styles.evidenceText, { color: theme.textSecondary }]}>
                    {source}
                  </Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {weeklySummary.cross_week_shift && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Shift Across the Week
            </Text>
            
            <View style={[styles.shiftCard, { backgroundColor: theme.surface, borderColor: theme.accent }]}>
              <Text style={[styles.shiftText, { color: theme.textSecondary }]}>
                {weeklySummary.cross_week_shift}
              </Text>
            </View>
          </View>
        )}

        <View style={styles.section}>
          <View style={[styles.reflectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>
              A question to sit with
            </Text>
            <Text style={[styles.reflectionPrompt, { color: theme.accent }]}>
              "{weeklySummary.reflection_prompt}"
            </Text>
          </View>
        </View>
      </ScrollView>
    );
  };

  // ============================================================================
  // RENDER: TIMELINE TAB
  // ============================================================================

  const renderWeekEntry = (week: WeekEntry) => {
    const isExpanded = expandedWeek === week.week_start;
    const weekLabel = formatDateRange(week.week_start, week.week_end);
    
    if (!week.top_domain) return null;
    
    const trends = Object.entries(week.trend_map).slice(0, 3);
    
    return (
      <TouchableOpacity
        key={week.week_start}
        style={[styles.weekCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
        onPress={() => toggleWeekExpanded(week.week_start)}
        activeOpacity={0.8}
      >
        <View style={styles.weekHeader}>
          <Text style={[styles.weekLabel, { color: theme.textTertiary }]}>
            {weekLabel}
          </Text>
          <Text style={[styles.expandIndicator, { color: theme.textTertiary }]}>
            {isExpanded ? '▲' : '▼'}
          </Text>
        </View>
        
        <Text style={[styles.topDomain, { color: theme.text }]}>
          {week.top_domain}
        </Text>
        
        {week.secondary_domains.length > 0 && (
          <Text style={[styles.secondaryDomains, { color: theme.textSecondary }]}>
            {week.secondary_domains.join(' • ')}
          </Text>
        )}
        
        <View style={styles.trendChipsRow}>
          {trends.map(([domain, trend]) => {
            const colors = getTrendChipColor(trend);
            return (
              <View key={domain} style={[styles.trendChip, { backgroundColor: colors.bg }]}>
                <Text style={[styles.trendChipText, { color: colors.text }]}>
                  {getTrendChipLabel(trend)}
                </Text>
              </View>
            );
          })}
        </View>
        
        {isExpanded && (
          <View style={[styles.expandedContent, { borderTopColor: theme.border }]}>
            {week.narrative && (
              <Text style={[styles.weekNarrative, { color: theme.textSecondary }]}>
                {week.narrative}
              </Text>
            )}
            {week.reflection_prompt && (
              <Text style={[styles.weekReflectionText, { color: theme.accent }]}>
                "{week.reflection_prompt}"
              </Text>
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderInsightCard = (label: string, domain: string | null) => {
    if (!domain) return null;
    
    return (
      <View style={[styles.insightCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.insightLabel, { color: theme.textTertiary }]}>
          {label}
        </Text>
        <Text style={[styles.insightDomain, { color: theme.text }]}>
          {domain}
        </Text>
      </View>
    );
  };

  const renderTimelineTab = () => {
    if (timelineLoading) {
      return (
        <View style={[styles.centeredContent]}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Building your pattern timeline...
          </Text>
        </View>
      );
    }

    if (timelineError || !timeline || timeline.weeks.length === 0) {
      return (
        <View style={[styles.centeredContent]}>
          <Text style={styles.emptyIcon}>◷</Text>
          <Text style={[styles.emptyTitle, { color: theme.text }]}>
            Your timeline is still taking shape
          </Text>
          <Text style={[styles.emptySubtext, { color: theme.textSecondary }]}>
            As more weekly patterns accumulate, a longer view of recurring themes will appear here.
          </Text>
        </View>
      );
    }

    return (
      <ScrollView
        style={styles.tabContent}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={timelineRefreshing}
            onRefresh={() => fetchTimeline(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        <View style={styles.timelineHeader}>
          <Text style={[styles.timelineSubtitle, { color: theme.textSecondary }]}>
            A longer view of what has repeated, shifted, or returned.
          </Text>
          <Text style={[styles.rangeLabel, { color: theme.textTertiary }]}>
            {timeline.range_label}
          </Text>
        </View>

        {timeline.is_partial && (
          <View style={[styles.partialNote, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.partialNoteText, { color: theme.textTertiary }]}>
              This view is based on the pattern history available so far.
            </Text>
          </View>
        )}

        <View style={[styles.narrativeCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.narrativeText, { color: theme.textSecondary }]}>
            {timeline.narrative_summary}
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Week by Week
          </Text>
          {timeline.weeks.map(week => renderWeekEntry(week))}
        </View>

        {(timeline.insights.most_recurring_domain || timeline.insights.strongest_recent_domain) && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              Pattern Insights
            </Text>
            
            <View style={styles.insightsGrid}>
              {renderInsightCard('Most recurring', timeline.insights.most_recurring_domain)}
              {renderInsightCard('Strongest recently', timeline.insights.strongest_recent_domain)}
              {renderInsightCard('Most variable', timeline.insights.volatile_domain)}
              {renderInsightCard('Most steady', timeline.insights.stable_domain)}
              {renderInsightCard('Re-emerging', timeline.insights.reemerging_domain)}
            </View>
          </View>
        )}

        <View style={styles.section}>
          <View style={[styles.reflectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>
              A question to sit with
            </Text>
            <Text style={[styles.reflectionPrompt, { color: theme.accent }]}>
              "{timeline.reflection_prompt}"
            </Text>
          </View>
        </View>
      </ScrollView>
    );
  };

  // ============================================================================
  // RENDER: SIGNALS TAB
  // ============================================================================
  // SIGNALS TAB - Summary-First Design (v0.15)
  // All detail sections are collapsed by default via PatternGraphCard accordions
  // ============================================================================

  const renderSignalsTab = () => {
    return (
      <ScrollView
        style={styles.tabContent}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={patternsRefreshing}
            onRefresh={() => fetchPatterns(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        {/* Short intro copy */}
        <View style={styles.signalsIntroContainer}>
          <Text style={[styles.signalsIntroText, { color: theme.textSecondary }]}>
            A live view of the signals shaping your patterns.
          </Text>
        </View>

        {/* Pattern Graph Summary Card - handles all data, loading, errors internally */}
        {/* All detail sections (domains, signals, themes, sources) are collapsed by default */}
        <PatternGraphCard />
      </ScrollView>
    );
  };

  // ============================================================================
  // MAIN RENDER
  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Patterns</Text>
      </View>
      
      {renderSegmentedControl()}
      
      <View style={styles.tabContentContainer}>
        {activeTab === 'patterns' && renderPatternsTab()}
        {activeTab === 'weekly' && renderWeeklyTab()}
        {activeTab === 'timeline' && renderTimelineTab()}
        {activeTab === 'signals' && renderSignalsTab()}
      </View>
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
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
  },
  
  // Segmented Control
  segmentedControl: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginBottom: 16,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  segmentButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
  },
  segmentText: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Tab Content
  tabContentContainer: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 120, // Extra padding for PWA banner overlay
  },
  
  // Centered Content
  centeredContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 14,
    fontStyle: 'italic',
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 16,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 16,
    opacity: 0.5,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 12,
  },
  emptySubtext: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
    fontStyle: 'italic',
  },
  retryButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Intro Section (Patterns)
  introSection: {
    marginBottom: 20,
  },
  introDescription: {
    fontSize: 14,
    lineHeight: 22,
  },
  
  // Domain Cards (Patterns)
  domainsSection: {
    marginBottom: 20,
  },
  resonanceSection: {
    marginBottom: 32,
    marginTop: 8,
  },
  
  // Lunar Cycle Section Styles - Task 49
  lunarCycleSection: {
    marginBottom: 32,
    marginTop: 8,
  },
  lunarCycleCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 18,
  },
  lunarCycleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 14,
  },
  lunarMoonIcon: {
    fontSize: 22,
  },
  lunarCycleTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1.5,
  },
  lunarPhaseBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    marginBottom: 16,
  },
  lunarPhaseBadgeText: {
    fontSize: 14,
    fontWeight: '600',
  },
  lunarProgressContainer: {
    marginBottom: 18,
  },
  lunarProgressTrack: {
    height: 6,
    borderRadius: 3,
    marginBottom: 8,
  },
  lunarProgressFill: {
    height: '100%',
    borderRadius: 3,
  },
  lunarProgressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  lunarProgressLabel: {
    fontSize: 10,
    fontWeight: '500',
  },
  lunarPatternMessage: {
    fontSize: 15,
    lineHeight: 24,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  lunarTimingRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingTop: 14,
    marginTop: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  lunarTimingItem: {
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  lunarTimingValue: {
    fontSize: 20,
    fontWeight: '600',
  },
  lunarTimingLabel: {
    fontSize: 11,
    marginTop: 2,
  },
  lunarQuestionBlock: {
    paddingTop: 16,
    marginTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  lunarQuestionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 6,
  },
  lunarQuestionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  // Task 50: Lunar Gate Styles
  lunarGateSection: {
    paddingTop: 14,
    marginTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  lunarGateSectionTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 10,
  },
  lunarGateHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 10,
    marginBottom: 6,
  },
  lunarGateNumber: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  lunarGateTitle: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
  },
  lunarGateTheme: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  lunarGateCenter: {
    fontSize: 12,
    marginBottom: 8,
  },
  
  // New Accordion Card Styles
  accordionCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 10,
    overflow: 'hidden',
  },
  accordionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  accordionLeft: {
    flex: 1,
  },
  accordionTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  accordionRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  accordionChevron: {
    fontSize: 10,
  },
  accordionBody: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  
  // New Section Accordion Styles (for Story, Pattern, Challenge, Genius, Experiments)
  loadingInterpretation: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  loadingInterpretationText: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  sectionAccordion: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    marginBottom: 0,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  sectionChevron: {
    fontSize: 16,
    fontWeight: '600',
    width: 24,
    textAlign: 'center',
  },
  sectionContent: {
    paddingBottom: 14,
    paddingRight: 8,
  },
  sectionText: {
    fontSize: 14,
    lineHeight: 22,
  },
  experimentsList: {
    gap: 10,
  },
  experimentItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  experimentBullet: {
    fontSize: 16,
    marginRight: 10,
    marginTop: -1,
  },
  experimentText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  reflectButtonContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
  },
  
  // ============================================
  // Inner Tab Control (Interpretation | Signals)
  // ============================================
  innerTabControl: {
    flexDirection: 'row',
    borderBottomWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  innerTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
    gap: 6,
  },
  innerTabActive: {
    // Border color applied inline
  },
  innerTabText: {
    fontSize: 13,
    fontWeight: '500',
  },
  signalBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
  },
  signalBadgeText: {
    fontSize: 10,
    fontWeight: '600',
  },
  innerTabContent: {
    // Container for tab content
  },
  
  // ============================================
  // Signals Tab Styles
  // ============================================
  signalsIntroContainer: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 12,
  },
  signalsIntroText: {
    fontSize: 13,
    lineHeight: 18,
  },
  signalsIntro: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 16,
    fontStyle: 'italic',
  },
  noSignalsText: {
    fontSize: 14,
    lineHeight: 20,
    textAlign: 'center',
    paddingVertical: 20,
  },
  signalGroupsContainer: {
    gap: 16,
  },
  signalGroup: {
    gap: 8,
  },
  signalGroupHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  signalGroupIcon: {
    fontSize: 14,
  },
  signalGroupTitle: {
    fontSize: 13,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  signalGroupItems: {
    gap: 8,
    paddingLeft: 22,
  },
  signalItem: {
    borderLeftWidth: 2,
    paddingLeft: 12,
    paddingVertical: 4,
  },
  signalItemText: {
    fontSize: 14,
    lineHeight: 20,
  },
  enhancedEnergyNote: {
    marginTop: 16,
    borderRadius: 10,
    padding: 14,
    borderLeftWidth: 3,
  },
  enhancedEnergyTitle: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 6,
  },
  transitSymbolsContainer: {
    marginVertical: 10,
    gap: 8,
  },
  transitSymbolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  transitSymbolText: {
    fontSize: 18,
    fontWeight: '500',
    minWidth: 70,
  },
  transitDescText: {
    fontSize: 12,
    flex: 1,
  },
  enhancedEnergyText: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 8,
  },
  sourcesSummary: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  sourcesSummaryLabel: {
    fontSize: 11,
    textAlign: 'center',
  },
  
  // Legacy styles below
  accordionNarrative: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 14,
  },
  signalsCompact: {
    marginBottom: 14,
  },
  signalsCompactLabel: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  signalsCompactList: {
    gap: 4,
  },
  signalChip: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  signalChipDot: {
    fontSize: 10,
    marginRight: 8,
  },
  signalChipText: {
    fontSize: 13,
  },
  accordionPromptSection: {
    borderRadius: 10,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  accordionPromptText: {
    fontSize: 13,
    fontStyle: 'italic',
    lineHeight: 20,
    flex: 1,
  },
  reflectButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  reflectButtonText: {
    fontSize: 12,
    fontWeight: '500',
  },
  
  // Legacy Domain Card Styles (kept for reference)
  domainCard: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 18,
    marginBottom: 16,
    overflow: 'visible',
  },
  domainHeaderTouchable: {
    marginBottom: 14,
  },
  domainHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  domainName: {
    fontSize: 17,
    fontWeight: '600',
    marginBottom: 4,
    flex: 1,
  },
  domainStrength: {
    fontSize: 12,
    fontWeight: '500',
  },
  expandChevron: {
    fontSize: 10,
    marginLeft: 6,
  },
  domainSynthesis: {
    fontSize: 14,
    lineHeight: 23,
    marginBottom: 12,
  },
  domainShowUp: {
    fontSize: 14,
    lineHeight: 23,
    marginBottom: 14,
    opacity: 0.9,
  },
  domainPromptRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.08)',
  },
  domainPrompt: {
    fontSize: 13,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  journalTrigger: {
    paddingLeft: 12,
    paddingTop: 2,
  },
  journalTriggerText: {
    fontSize: 12,
  },
  
  // Weekly Tab Styles
  weeklyHeader: {
    marginBottom: 20,
  },
  weeklySubtitle: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  dateRange: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  card: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 18,
    marginBottom: 16,
  },
  narrative: {
    fontSize: 15,
    lineHeight: 24,
  },
  section: {
    marginTop: 8,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    marginBottom: 12,
    letterSpacing: 0.3,
  },
  weeklyDomainCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  weeklyDomainHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  weeklyDomainName: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  weeklyDomainTrend: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 8,
  },
  weeklyDomainEvidence: {
    fontSize: 13,
    lineHeight: 20,
  },
  timingNote: {
    fontSize: 11,
    marginTop: 8,
    fontStyle: 'italic',
  },
  evidenceItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  evidenceBullet: {
    fontSize: 14,
    marginRight: 10,
    marginTop: 2,
  },
  evidenceText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
  shiftCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    borderLeftWidth: 3,
  },
  shiftText: {
    fontSize: 14,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  reflectionCard: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    alignItems: 'center',
  },
  reflectionLabel: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  reflectionPrompt: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  
  // Timeline Tab Styles
  timelineHeader: {
    marginBottom: 20,
  },
  timelineSubtitle: {
    fontSize: 15,
    lineHeight: 22,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  rangeLabel: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  partialNote: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
    marginBottom: 16,
  },
  partialNoteText: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  narrativeCard: {
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 18,
    marginBottom: 24,
  },
  narrativeText: {
    fontSize: 15,
    lineHeight: 24,
  },
  weekCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  weekHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  weekLabel: {
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 0.5,
  },
  expandIndicator: {
    fontSize: 10,
  },
  topDomain: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  secondaryDomains: {
    fontSize: 13,
    marginBottom: 12,
  },
  trendChipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  trendChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  trendChipText: {
    fontSize: 11,
    fontWeight: '500',
  },
  expandedContent: {
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  weekNarrative: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 12,
  },
  weekReflectionText: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  insightsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  insightCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    minWidth: '47%',
    flex: 1,
  },
  insightLabel: {
    fontSize: 11,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  insightDomain: {
    fontSize: 14,
    fontWeight: '500',
  },
  
  // Signals Tab Styles
  signalsSection: {
    gap: 16,
  },
  signalSourceCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 12,
  },
  signalSourceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  signalSourceIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  signalSourceTitle: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  signalCountBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  signalCountText: {
    fontSize: 12,
    fontWeight: '600',
  },
  signalSourceItems: {
    gap: 12,
  },
  signalSourceItem: {
    borderLeftWidth: 3,
    paddingLeft: 12,
    paddingVertical: 8,
  },
  signalItemHeader: {
    marginBottom: 6,
  },
  signalDomainTag: {
    fontSize: 11,
    fontWeight: '500',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    alignSelf: 'flex-start',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  signalItemDescription: {
    fontSize: 13,
    lineHeight: 18,
  },
  transitDetails: {
    marginTop: 8,
    gap: 4,
  },
  transitDetailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  transitSymbol: {
    fontSize: 14,
    fontWeight: '600',
    minWidth: 60,
  },
  transitDescription: {
    fontSize: 12,
    flex: 1,
  },
});
