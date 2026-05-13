/**
 * AstrologyTimelineTab.tsx
 * 
 * "THE YEAR AS IT UNFOLDS"
 * Master Astrologer Timeline - Personalized yearly strategic view
 * 
 * UPGRADED: Chart-specific, house-aware, behavioral language
 */

import React, { useState, useMemo, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  LayoutAnimation,
  Platform,
  UIManager,
  ActivityIndicator,
} from 'react-native';
import Constants from 'expo-constants';
import { useTheme } from '../../contexts/ThemeContext';
import { Colors } from '../../constants/colors';
import { FullChartData } from '../../services/astrology/astrologyTypes';
import { getJournalEntriesByPhase, getJournalPatterns, JournalEntryResponseWithPhase, JournalPatternAnalysis } from '../../services/api';
import { useAppStore } from '../../store';
import { cleanText } from '../../utils/languageGuard';

// Backend URL resolution (same pattern AstrologyTodayV4 uses) — on web
// we rely on the relative /api proxy, on native we use the absolute
// EXPO_PUBLIC_BACKEND_URL so the fetch works under both runtimes.
const TIMELINE_BACKEND_BASE =
  (Constants.expoConfig?.extra as any)?.EXPO_PUBLIC_BACKEND_URL ||
  process.env.EXPO_PUBLIC_BACKEND_URL ||
  '';
const TIMELINE_APP_BASE = typeof window !== 'undefined' ? '' : TIMELINE_BACKEND_BASE;

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// ============================================
// TYPES
// ============================================

interface TimelinePhase {
  id: string;
  dateRange: string;
  phaseName: string;
  humanMeaning: string; // Plain-English explanation (Part 1)
  whatsHappening: string[];
  whatThisCreates: string[];
  wherePeopleGetItWrong: string[];
  whatItsAskingOfYou: string[];
  isPrimary?: boolean;
}

interface TurningPoint {
  id: string;
  date: string;
  lifeArea: string;
  whyThisMatters: string;
  whatBecomesClear: string;
  whatHappensIfAvoided: string;
}

interface DecisionWindow {
  id: string;
  dateRange: string;
  context: string;
  prompt: string;
  ifYouAct: string;
  ifYouWait: string;
}

interface TimelineData {
  yearTheme: string;
  primaryArc: string;
  phases: TimelinePhase[];
  turningPoints: TurningPoint[];
  decisionWindows: DecisionWindow[];
}

interface AstrologyTimelineTabProps {
  fullChartData: FullChartData | null;
  theme: any;
  onOpenChat: () => void;
  initialExpandPhase?: string; // Phase ID to auto-expand on mount (from URL param)
}

// ============================================
// HOUSE LIFE AREA MAPPING
// ============================================

const HOUSE_AREAS: { [key: number]: string } = {
  1: 'identity and how you show up',
  2: 'money, security, and self-worth',
  3: 'communication, decisions, and daily routines',
  4: 'home, family, and emotional foundation',
  5: 'creativity, joy, and what you pour yourself into',
  6: 'work, health, and daily habits',
  7: 'relationships and partnerships',
  8: 'intimacy, shared resources, and transformation',
  9: 'beliefs, meaning, and long-term direction',
  10: 'career, reputation, and public life',
  11: 'community, future vision, and friendships',
  12: 'rest, solitude, and what you hide from yourself',
};

const HOUSE_SHORT: { [key: number]: string } = {
  1: 'identity',
  2: 'security',
  3: 'communication',
  4: 'home',
  5: 'creativity',
  6: 'work',
  7: 'relationships',
  8: 'intimacy',
  9: 'direction',
  10: 'career',
  11: 'community',
  12: 'inner life',
};

// ============================================
// TENSION PATTERNS BY SIGN
// ============================================

interface PatternData {
  tension: string;
  yearTheme: string;
  arcDescription: string;
  costOfAction: string;
  costOfWaiting: string;
}

const SIGN_PATTERNS: { [key: string]: PatternData } = {
  'Aries': {
    tension: 'moving fast vs. moving right',
    yearTheme: 'This year keeps asking whether speed is actually getting you closer—or just keeping you from feeling stuck.',
    arcDescription: 'You\'ll notice the same friction between action and timing appearing in different contexts. The impulse to move shows up first; the question of whether it\'s time comes second. The year is teaching you that readiness isn\'t the same as restlessness.',
    costOfAction: 'the conversation gets uncomfortable fast, but the uncertainty stops running the show',
    costOfWaiting: 'you preserve momentum for now, but the question you\'re avoiding gets louder',
  },
  'Taurus': {
    tension: 'holding on vs. letting go',
    yearTheme: 'This year keeps showing you the difference between stability and stagnation—and which one you\'ve been calling the other.',
    arcDescription: 'Across the year, you\'ll feel the weight of things you\'ve been carrying longer than necessary. The pattern isn\'t about loss—it\'s about recognizing when holding on has become the obstacle, not the anchor.',
    costOfAction: 'the discomfort of releasing something familiar, but the relief of finally moving',
    costOfWaiting: 'the comfort of keeping things as they are, but the growing sense that comfort isn\'t the same as peace',
  },
  'Gemini': {
    tension: 'exploring options vs. choosing a path',
    yearTheme: 'This year keeps narrowing your options until you discover which one you actually want—not which one sounds interesting.',
    arcDescription: 'You\'ll notice the same tension between curiosity and commitment returning in different forms. The year isn\'t trying to limit you. It\'s showing you that depth requires staying somewhere long enough to see what\'s really there.',
    costOfAction: 'closing doors feels limiting, but the focus brings clarity you couldn\'t find while juggling',
    costOfWaiting: 'options remain open, but the energy stays scattered and nothing quite lands',
  },
  'Cancer': {
    tension: 'protecting vs. connecting',
    yearTheme: 'This year keeps asking whether your walls are keeping you safe—or keeping out what you actually need.',
    arcDescription: 'Across the year, you\'ll notice the same pattern: the instinct to protect, followed by the cost of isolation. The year is teaching you that vulnerability isn\'t the opposite of safety—sometimes it\'s the only path to it.',
    costOfAction: 'the exposure feels raw, but the connection becomes real instead of guarded',
    costOfWaiting: 'the distance feels safer, but the loneliness underneath keeps growing',
  },
  'Leo': {
    tension: 'being seen vs. being known',
    yearTheme: 'This year keeps showing you the difference between the version of you that performs and the version that\'s actually real.',
    arcDescription: 'You\'ll feel the gap between how you present and how you feel appearing in different contexts. The year isn\'t asking you to stop shining. It\'s asking whether the light is coming from somewhere authentic.',
    costOfAction: 'the mask drops, and not everyone will recognize you—but the right ones will',
    costOfWaiting: 'the performance continues smoothly, but the exhaustion of maintaining it grows',
  },
  'Virgo': {
    tension: 'fixing vs. accepting',
    yearTheme: 'This year keeps asking whether the problem is actually the thing you\'re trying to fix—or the fact that you can\'t stop fixing.',
    arcDescription: 'Across the year, you\'ll notice the same impulse: something isn\'t right, and you\'re the one who sees it. The pattern isn\'t about lowering your standards. It\'s about recognizing when improvement has become avoidance.',
    costOfAction: 'you let something be imperfect, and it doesn\'t collapse—the anxiety was the problem',
    costOfWaiting: 'you keep refining, but the thing you\'re avoiding keeps waiting underneath the tasks',
  },
  'Libra': {
    tension: 'pleasing vs. choosing',
    yearTheme: 'This year keeps putting you in positions where harmony requires honesty—and you can\'t have both by staying silent.',
    arcDescription: 'You\'ll feel the same tension between keeping the peace and stating your position appearing in different relationships. The year isn\'t asking you to become disagreeable. It\'s showing you that real connection requires knowing where you actually stand.',
    costOfAction: 'the conversation gets tense, but they finally know who they\'re dealing with',
    costOfWaiting: 'the relationship stays smooth on the surface, but you start disappearing from it',
  },
  'Scorpio': {
    tension: 'controlling vs. trusting',
    yearTheme: 'This year keeps asking you to loosen your grip—and discover what stays when you stop holding so tightly.',
    arcDescription: 'Across the year, you\'ll notice the same pattern: the impulse to control outcomes, followed by the cost of never knowing what would have happened naturally. The year is teaching you that trust isn\'t weakness—it\'s a different kind of power.',
    costOfAction: 'you let go, and it\'s terrifying—but you finally see what\'s real without your influence',
    costOfWaiting: 'you maintain control, but you never know if what you have would have chosen you back',
  },
  'Sagittarius': {
    tension: 'freedom vs. commitment',
    yearTheme: 'This year keeps showing you that some kinds of freedom are actually just avoidance wearing adventure as a costume.',
    arcDescription: 'You\'ll feel the pull between staying and going appearing in different contexts. The year isn\'t trying to cage you. It\'s asking whether the next horizon is actually calling—or just easier than being fully present here.',
    costOfAction: 'you commit, and some doors close—but you finally find out what\'s behind the one you chose',
    costOfWaiting: 'all options stay open, but you start noticing how shallow everything feels',
  },
  'Capricorn': {
    tension: 'achieving vs. arriving',
    yearTheme: 'This year keeps asking whether you\'re climbing toward something real—or just avoiding the emptiness that might be at the top.',
    arcDescription: 'Across the year, you\'ll notice the same pattern: the drive to accomplish, followed by the question of what it\'s actually for. The year isn\'t asking you to stop working. It\'s asking whether the work is building something that matters to you.',
    costOfAction: 'you pause the climb, and the identity question hits—but so does clarity about what\'s worth reaching',
    costOfWaiting: 'you keep achieving, but the satisfaction keeps requiring the next achievement to feel real',
  },
  'Aquarius': {
    tension: 'distance vs. belonging',
    yearTheme: 'This year keeps asking whether your independence is freedom—or just a sophisticated way of staying alone.',
    arcDescription: 'You\'ll feel the tension between standing apart and being part of something appearing in different contexts. The year isn\'t asking you to conform. It\'s asking whether the distance is protecting something valuable—or just preventing connection.',
    costOfAction: 'you move closer, and it feels vulnerable—but you finally know what belonging actually feels like',
    costOfWaiting: 'you maintain your position, but the loneliness you\'ve been calling freedom gets harder to ignore',
  },
  'Pisces': {
    tension: 'absorbing vs. protecting',
    yearTheme: 'This year keeps showing you the difference between compassion and losing yourself—and how often you\'ve confused them.',
    arcDescription: 'Across the year, you\'ll notice the same pattern: feeling everything around you, followed by the cost of not knowing which feelings are actually yours. The year is teaching you that boundaries aren\'t walls—they\'re the shape of who you are.',
    costOfAction: 'you draw a line, and it feels selfish—but you finally have energy that belongs to you',
    costOfWaiting: 'you keep absorbing, but you start forgetting what you wanted before you felt what everyone else needed',
  },
};

// ============================================
// TIMELINE DATA GENERATOR
// ============================================

function generateTimelineData(
  fullChartData: FullChartData | null
): TimelineData {
  const planets = fullChartData?.natal?.planets || {};
  const houses = fullChartData?.natal?.houses?.cusps || [];
  
  const sunSign = planets.Sun?.sign || 'Aries';
  const moonSign = planets.Moon?.sign || 'Cancer';
  const sunHouse = planets.Sun?.house || 5;
  const moonHouse = planets.Moon?.house || 4;
  const marsHouse = planets.Mars?.house || 1;
  const venusHouse = planets.Venus?.house || 7;
  const saturnHouse = planets.Saturn?.house || 10;
  
  const currentYear = new Date().getFullYear();
  
  // Get pattern data for this chart
  const patternData = SIGN_PATTERNS[sunSign] || SIGN_PATTERNS['Aries'];
  
  // Build house-specific life areas
  const sunArea = HOUSE_AREAS[sunHouse] || 'self-expression';
  const moonArea = HOUSE_AREAS[moonHouse] || 'emotional life';
  const marsArea = HOUSE_SHORT[marsHouse] || 'action';
  const venusArea = HOUSE_SHORT[venusHouse] || 'relationships';
  const saturnArea = HOUSE_SHORT[saturnHouse] || 'responsibility';
  
  const yearTheme = patternData.yearTheme;
  const primaryArc = patternData.arcDescription;

  const phases: TimelinePhase[] = [
    {
      id: 'q1',
      dateRange: `Jan – Mar ${currentYear}`,
      phaseName: 'Recognition',
      humanMeaning: 'Something is becoming clear',
      whatsHappening: [
        `The ${patternData.tension} tension starts showing up in ${sunArea}`,
        `Small moments in ${marsArea} and ${venusArea} that carry more weight than they look`,
      ],
      whatThisCreates: [
        'A nagging sense you\'ve been here before',
        'Situations that feel minor but keep replaying in your head',
      ],
      wherePeopleGetItWrong: [
        'Treating these moments as coincidence instead of signal',
        'Waiting for something bigger before paying attention',
      ],
      whatItsAskingOfYou: [
        `Notice what keeps echoing, especially around ${moonArea}`,
        'Start asking "why does this keep happening?" instead of "when will this stop?"',
      ],
      isPrimary: false,
    },
    {
      id: 'q2',
      dateRange: `Apr – Jun ${currentYear}`,
      phaseName: 'Confrontation',
      humanMeaning: 'Something can no longer be avoided',
      whatsHappening: [
        `What you\'ve been tolerating in ${venusArea} and ${saturnArea} stops feeling tolerable`,
        `The gap between how you present in ${sunArea} and how you feel in ${moonArea} gets harder to bridge`,
      ],
      whatThisCreates: [
        'Conversations you\'ve been putting off start demanding attention',
        'Choices that feel more permanent than before',
      ],
      wherePeopleGetItWrong: [
        'Blaming the situation instead of seeing what you brought to it',
        'Making a decision just to escape the pressure, then regretting the speed',
      ],
      whatItsAskingOfYou: [
        'Name what you\'ve been pretending not to see',
        `In ${saturnArea}, choose from clarity—not from wanting the discomfort to end`,
      ],
      isPrimary: true,
    },
    {
      id: 'q3',
      dateRange: `Jul – Sep ${currentYear}`,
      phaseName: 'The Crossroads',
      humanMeaning: 'A choice, split, or redirection is active',
      whatsHappening: [
        `In ${sunArea}, two versions of you become visible—the one you\'ve been and the one you could become`,
        `The tension in ${venusArea} crystallizes into a clear choice`,
      ],
      whatThisCreates: [
        'A sense that this period will be remembered as a before/after moment',
        'The strange calm of knowing what you need to do, even if you haven\'t done it yet',
      ],
      wherePeopleGetItWrong: [
        'Waiting for certainty that never comes—the information is already sufficient',
        'Choosing based on what\'s comfortable instead of what\'s aligned',
      ],
      whatItsAskingOfYou: [
        'Make the choice you\'ve been circling. The year has prepared you for this.',
        'Trust what you\'ve learned about yourself since January',
      ],
      isPrimary: true,
    },
    {
      id: 'q4',
      dateRange: `Oct – Dec ${currentYear}`,
      phaseName: 'Integration',
      humanMeaning: 'Something is settling into a new form',
      whatsHappening: [
        `The ripples from your Q3 choices start showing in ${saturnArea} and ${marsArea}`,
        `What you decided in ${venusArea} either settles or requires one more honest conversation`,
      ],
      whatThisCreates: [
        'Either: the relief of having finally moved, and the new ground beneath your feet',
        'Or: the recognition that you\'re not done yet—and clarity about what next year needs to address',
      ],
      wherePeopleGetItWrong: [
        'Forcing a sense of completion before it\'s earned',
        'Dismissing what the year taught because it was uncomfortable',
      ],
      whatItsAskingOfYou: [
        `Honest inventory: what actually changed in ${sunArea}?`,
        'Gratitude for the growth, acceptance for what remains',
      ],
      isPrimary: false,
    },
  ];

  const turningPoints: TurningPoint[] = [
    {
      id: 'tp1',
      date: `Late April ${currentYear}`,
      lifeArea: `${HOUSE_AREAS[moonHouse] || 'emotional life'}`,
      whyThisMatters: `Something happens in ${moonArea} that makes the ${patternData.tension} tension impossible to keep calling "manageable." The cost of continuing as you have been becomes clearer than the cost of changing.`,
      whatBecomesClear: `What you\'ve been tolerating. Why you\'ve been tolerating it. And what it\'s actually been costing you in ${venusArea}.`,
      whatHappensIfAvoided: 'The pattern doesn\'t go away—it goes underground. What could have been addressed as a conversation becomes a crisis by August.',
    },
    {
      id: 'tp2',
      date: `Mid-August ${currentYear}`,
      lifeArea: `${HOUSE_AREAS[sunHouse] || 'identity'}`,
      whyThisMatters: `This is the year\'s primary choice point in ${sunArea}. The options are clear. The information is sufficient. What remains is whether you\'ll choose from who you\'re becoming—or retreat to who you\'ve been.`,
      whatBecomesClear: 'Which direction matches the person you\'ve been growing into. The version of you that hesitates and the version that moves forward both become visible.',
      whatHappensIfAvoided: `The choice gets made for you by circumstances. In ${saturnArea}, you lose authorship of your own direction.`,
    },
    {
      id: 'tp3',
      date: `Early November ${currentYear}`,
      lifeArea: `${HOUSE_AREAS[saturnHouse] || 'responsibility'}`,
      whyThisMatters: `The year\'s arc reaches its natural conclusion in ${saturnArea}. What you started in Q1 is ready to be named: either as something that changed, or as something that needs another cycle.`,
      whatBecomesClear: 'Whether the year\'s lesson landed. Whether you\'re entering next year with new ground beneath you—or carrying forward what this year tried to resolve.',
      whatHappensIfAvoided: 'You enter next year still holding what this year asked you to put down. The same pattern returns, but with higher stakes.',
    },
  ];

  const decisionWindows: DecisionWindow[] = [
    {
      id: 'dw1',
      dateRange: `Mar 15-31, ${currentYear}`,
      context: `In ${HOUSE_SHORT[marsHouse] || 'action'}`,
      prompt: 'You can name it now. Or you can wait until it names itself.',
      ifYouAct: 'The conversation gets uncomfortable fast, but the uncertainty stops running the show. In two weeks, you\'ll be glad you didn\'t wait.',
      ifYouWait: 'You preserve the surface peace for now, but the thing you\'re avoiding keeps growing underneath it. By May, it\'s bigger.',
    },
    {
      id: 'dw2',
      dateRange: `Jun 1-15, ${currentYear}`,
      context: `In ${HOUSE_SHORT[venusHouse] || 'relationships'}`,
      prompt: 'You can say what\'s actually true. Or you can keep editing yourself for the room.',
      ifYouAct: `${patternData.costOfAction}. The relationship changes—but at least now it\'s based on something real.`,
      ifYouWait: `${patternData.costOfWaiting}. The connection stays familiar, but you start noticing how tired you are of managing it.`,
    },
    {
      id: 'dw3',
      dateRange: `Sep 1-20, ${currentYear}`,
      context: `In ${HOUSE_SHORT[saturnHouse] || 'career'}`,
      prompt: 'You can commit to the new direction. Or you can keep one foot in both worlds.',
      ifYouAct: 'Some doors close. The grief is real. But so is the focus—and the energy that comes from finally choosing.',
      ifYouWait: 'All options stay open, but your energy stays scattered. By November, you\'ll wish you\'d trusted yourself sooner.',
    },
  ];

  return {
    yearTheme,
    primaryArc,
    phases,
    turningPoints,
    decisionWindows,
  };
}

// ============================================
// SERVER PAYLOAD → LOCAL SHAPE ADAPTER
// ============================================
// Maps the rich payload from GET /api/astrology/timeline/{user_id}
// (engine_version "timeline_v1.1") into the existing local
// `TimelineData` shape so the UI renders without any visual change.
// Server is treated as the source of truth — this adapter only
// renames fields. If the server payload is malformed, returns null
// so the caller can fall back to the client-side generator.

interface ServerPhase {
  id: string;
  name: string;
  period: string;
  human_meaning: string;
  description?: string;
  whats_happening?: string[];
  what_this_creates?: string[];
  where_people_get_it_wrong?: string[];
  what_its_asking_of_you?: string[];
  is_primary?: boolean;
  is_current?: boolean;
}

interface ServerTurningPoint {
  timing: string;
  type?: string;
  life_area: string;
  what_activates: string;
  what_becomes_clear: string;
  if_avoided: string;
}

interface ServerDecisionWindow {
  period: string;
  context: string;
  prompt: string;
  if_act: string;
  if_wait: string;
}

interface ServerTimelinePayload {
  year_theme?: string;
  year_question?: string;
  arc?: string;
  phases?: ServerPhase[];
  turning_points?: ServerTurningPoint[];
  decision_windows?: ServerDecisionWindow[];
  _cache_meta?: {
    source?: 'cache' | 'generated';
    year?: number;
    engine_version?: string;
    birth_data_hash?: string;
    generated_at?: string;
    age_seconds?: number;
    refresh_reason?: string | null;
    cache_key?: string;
  };
}

function adaptServerTimeline(server: ServerTimelinePayload | null): TimelineData | null {
  if (!server || !Array.isArray(server.phases) || server.phases.length === 0) {
    return null;
  }

  const phases: TimelinePhase[] = server.phases.map((p, idx) => ({
    id:           p.id ?? `q${idx + 1}`,
    dateRange:    p.period ?? '',
    phaseName:    p.name ?? '',
    humanMeaning: p.human_meaning ?? '',
    whatsHappening:        p.whats_happening ?? (p.description ? [p.description] : []),
    whatThisCreates:       p.what_this_creates ?? [],
    wherePeopleGetItWrong: p.where_people_get_it_wrong ?? [],
    whatItsAskingOfYou:    p.what_its_asking_of_you ?? [],
    isPrimary:    !!p.is_primary,
  }));

  const turningPoints: TurningPoint[] = (server.turning_points ?? []).map((t, idx) => ({
    id:                   `tp${idx + 1}`,
    date:                 t.timing ?? '',
    lifeArea:             t.life_area ?? '',
    whyThisMatters:       t.what_activates ?? '',
    whatBecomesClear:     t.what_becomes_clear ?? '',
    whatHappensIfAvoided: t.if_avoided ?? '',
  }));

  const decisionWindows: DecisionWindow[] = (server.decision_windows ?? []).map((d, idx) => ({
    id:        `dw${idx + 1}`,
    dateRange: d.period ?? '',
    context:   d.context ?? '',
    prompt:    d.prompt ?? '',
    ifYouAct:  d.if_act ?? '',
    ifYouWait: d.if_wait ?? '',
  }));

  return {
    yearTheme:    server.year_question ?? server.year_theme ?? '',
    primaryArc:   server.arc ?? '',
    phases,
    turningPoints,
    decisionWindows,
  };
}

// Network helper. Returns parsed payload on 2xx, throws otherwise so
// the caller can fall back. `forceRefresh` flips the query param.
async function fetchServerTimeline(
  userId: string,
  forceRefresh: boolean = false,
): Promise<ServerTimelinePayload> {
  const qs = forceRefresh ? '?force_refresh=true' : '';
  const url = `${TIMELINE_APP_BASE}/api/astrology/timeline/${userId}${qs}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`timeline endpoint returned HTTP ${res.status}`);
  }
  return res.json();
}

// ============================================
// COMPONENT
// ============================================

export default function AstrologyTimelineTab({
  fullChartData,
  theme,
  onOpenChat,
  initialExpandPhase,
}: AstrologyTimelineTabProps) {
  const { isDark } = useTheme();
  const [expandedPhaseId, setExpandedPhaseId] = useState<string | null>(null);
  const [highlightedPhaseId, setHighlightedPhaseId] = useState<string | null>(null);
  
  // Journal evidence state (Journal ↔ Timeline connection)
  const [phaseEvidence, setPhaseEvidence] = useState<Record<string, JournalEntryResponseWithPhase[]>>({});
  const [evidenceLoading, setEvidenceLoading] = useState<Record<string, boolean>>({});
  const [patternData, setPatternData] = useState<JournalPatternAnalysis | null>(null);
  const user = useAppStore(state => state.user);

  // Server-side timeline payload (source of truth).
  // - Loaded once on mount via GET /api/astrology/timeline/{user_id}.
  // - Cache lives in db.astrology_timeline_cache with weekly TTL, so
  //   the SAME yearly arc is returned to UI and to Ask About My Life.
  // - Falls back to client-side generateTimelineData() ONLY when the
  //   network request fails (offline / 5xx / chart-missing).
  const [serverTimeline, setServerTimeline] = useState<TimelineData | null>(null);
  const [serverMeta, setServerMeta] = useState<ServerTimelinePayload['_cache_meta'] | null>(null);
  const [timelineError, setTimelineError] = useState<string | null>(null);
  const [timelineLoading, setTimelineLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  const loadServerTimeline = async (forceRefresh: boolean = false) => {
    if (!user?.id) {
      setTimelineLoading(false);
      return;
    }
    try {
      if (forceRefresh) setRefreshing(true); else setTimelineLoading(true);
      setTimelineError(null);
      const raw = await fetchServerTimeline(user.id, forceRefresh);
      const adapted = adaptServerTimeline(raw);
      if (!adapted) throw new Error('timeline payload could not be adapted');
      setServerTimeline(adapted);
      setServerMeta(raw._cache_meta ?? null);
    } catch (err: any) {
      console.warn('[Timeline] Server fetch failed; falling back to client generator:', err?.message ?? err);
      setTimelineError(String(err?.message ?? err));
      setServerTimeline(null);
      setServerMeta(null);
    } finally {
      setTimelineLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadServerTimeline(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  // Build the rendered TimelineData. Preference order:
  //   1. Server payload (adapted)
  //   2. Client-side generator from fullChartData (fallback only)
  const timelineData = useMemo<TimelineData>(() => {
    if (serverTimeline) return serverTimeline;
    return generateTimelineData(fullChartData);
  }, [serverTimeline, fullChartData]);

  const usingServerSource = serverTimeline !== null;

  // Fetch pattern data (for compressed pattern lines)
  useEffect(() => {
    if (user?.id && !patternData) {
      getJournalPatterns(user.id)
        .then(data => setPatternData(data))
        .catch(err => console.error('[Timeline] Failed to fetch patterns:', err));
    }
  }, [user?.id]);

  // Auto-expand phase if passed via URL param (Part 6)
  useEffect(() => {
    if (initialExpandPhase && !expandedPhaseId) {
      setExpandedPhaseId(initialExpandPhase);
      setHighlightedPhaseId(initialExpandPhase);
      fetchPhaseEvidence(initialExpandPhase);
      
      // Clear highlight after 2 seconds
      setTimeout(() => {
        setHighlightedPhaseId(null);
      }, 2000);
    }
  }, [initialExpandPhase]);

  // Fetch journal entries for a phase when expanded
  const fetchPhaseEvidence = async (phaseId: string) => {
    if (!user?.id || phaseEvidence[phaseId]) return; // Already loaded or no user
    
    setEvidenceLoading(prev => ({ ...prev, [phaseId]: true }));
    try {
      const entries = await getJournalEntriesByPhase(user.id, phaseId, 3);
      setPhaseEvidence(prev => ({ ...prev, [phaseId]: entries }));
    } catch (err) {
      console.error('[Timeline] Failed to fetch phase evidence:', err);
    } finally {
      setEvidenceLoading(prev => ({ ...prev, [phaseId]: false }));
    }
  };

  const togglePhase = (phaseId: string) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    const newExpanded = expandedPhaseId === phaseId ? null : phaseId;
    setExpandedPhaseId(newExpanded);
    
    // Fetch evidence when expanding a phase
    if (newExpanded) {
      fetchPhaseEvidence(newExpanded);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerContainer}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>
          The Year As It Unfolds
        </Text>
        <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]}>
          Where things build, break, and shift
        </Text>
        {/* Manual refresh — minimal affordance, top-right of header.
            Calls /api/astrology/timeline/{user_id}?force_refresh=true
            and re-adapts the payload. */}
        {user?.id && (
          <TouchableOpacity
            onPress={() => loadServerTimeline(true)}
            disabled={refreshing || timelineLoading}
            style={styles.refreshButton}
            accessibilityLabel="Refresh timeline"
          >
            {refreshing ? (
              <ActivityIndicator size="small" color={theme.textTertiary} />
            ) : (
              <Text style={[styles.refreshButtonText, { color: theme.textTertiary }]}>
                ↻ Refresh
              </Text>
            )}
          </TouchableOpacity>
        )}
        {/* Dev-only cache meta strip. Never visible in production builds. */}
        {__DEV__ && serverMeta && (
          <Text style={[styles.debugMeta, { color: theme.textTertiary }]}>
            [dev] {serverMeta.source} · {serverMeta.engine_version} · y{serverMeta.year}
            {serverMeta.age_seconds != null
              ? ` · age=${Math.round(serverMeta.age_seconds)}s`
              : ''}
            {serverMeta.refresh_reason ? ` · reason=${serverMeta.refresh_reason}` : ''}
          </Text>
        )}
        {__DEV__ && !usingServerSource && (
          <Text style={[styles.debugMeta, { color: '#c0392b' }]}>
            [dev] using client-side fallback{timelineError ? ` (${timelineError})` : ''}
          </Text>
        )}
      </View>

      {/* Year Theme */}
      <View style={[styles.yearThemeCard, { backgroundColor: isDark ? 'rgba(139, 92, 246, 0.08)' : 'rgba(139, 92, 246, 0.05)', borderColor: Colors.accent + '30' }]}>
        <Text style={[styles.yearThemeLabel, { color: Colors.accent }]}>THIS YEAR'S QUESTION</Text>
        <Text style={[styles.yearThemeText, { color: theme.text }]}>
          {timelineData.yearTheme}
        </Text>
      </View>

      {/* Primary Arc */}
      <View style={styles.primaryArcContainer}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>THE ARC</Text>
        <Text style={[styles.primaryArcText, { color: theme.textSecondary }]}>
          {timelineData.primaryArc}
        </Text>
      </View>

      {/* Key Phases */}
      <View style={styles.phasesContainer}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>HOW IT UNFOLDS</Text>
        
        {timelineData.phases.map((phase) => (
          <TouchableOpacity
            key={phase.id}
            style={[
              styles.phaseCard,
              { 
                backgroundColor: theme.surface, 
                borderColor: phase.isPrimary ? Colors.accent + '40' : theme.border,
                borderWidth: phase.isPrimary ? 1.5 : 1,
              }
            ]}
            onPress={() => togglePhase(phase.id)}
            activeOpacity={0.8}
          >
            <View style={styles.phaseHeader}>
              <View style={styles.phaseHeaderLeft}>
                {phase.isPrimary && (
                  <Text style={[styles.primaryBadge, { color: Colors.accent }]}>⭐</Text>
                )}
                <View style={{ flex: 1 }}>
                  <Text style={[styles.phaseDateRange, { color: theme.textTertiary }]}>
                    {phase.dateRange}
                  </Text>
                  <Text style={[styles.phaseName, { color: theme.text }]}>
                    {phase.phaseName}
                  </Text>
                  <Text style={[styles.phaseHumanMeaning, { color: theme.textSecondary }]}>
                    {phase.humanMeaning}
                  </Text>
                </View>
              </View>
              <Text style={[styles.phaseExpandIcon, { color: theme.textSecondary }]}>
                {expandedPhaseId === phase.id ? '−' : '+'}
              </Text>
            </View>

            {expandedPhaseId === phase.id && (
              <View style={styles.phaseDetails}>
                <View style={styles.phaseSection}>
                  <Text style={[styles.phaseSectionTitle, { color: theme.textSecondary }]}>
                    What's happening
                  </Text>
                  {phase.whatsHappening.map((item, i) => (
                    <Text key={i} style={[styles.phaseBullet, { color: theme.text }]}>• {item}</Text>
                  ))}
                </View>

                <View style={styles.phaseSection}>
                  <Text style={[styles.phaseSectionTitle, { color: theme.textSecondary }]}>
                    What this creates
                  </Text>
                  {phase.whatThisCreates.map((item, i) => (
                    <Text key={i} style={[styles.phaseBullet, { color: theme.text }]}>• {item}</Text>
                  ))}
                </View>

                <View style={styles.phaseSection}>
                  <Text style={[styles.phaseSectionTitle, { color: '#E57373' }]}>
                    Where people get it wrong
                  </Text>
                  {phase.wherePeopleGetItWrong.map((item, i) => (
                    <Text key={i} style={[styles.phaseBullet, { color: theme.textSecondary }]}>• {item}</Text>
                  ))}
                </View>

                <View style={styles.phaseSection}>
                  <Text style={[styles.phaseSectionTitle, { color: Colors.accent }]}>
                    What it's asking of you
                  </Text>
                  {phase.whatItsAskingOfYou.map((item, i) => (
                    <Text key={i} style={[styles.phaseBullet, { color: theme.text }]}>• {item}</Text>
                  ))}
                </View>

                {/* Journal Evidence Section - V2.6: INSIGHT FIRST, PROOF SECOND */}
                {user?.id && (
                  <View style={styles.phaseSection}>
                    <Text style={[styles.evidenceSectionTitle, { color: Colors.accent }]}>
                      YOUR WORDS FROM THIS PHASE
                    </Text>
                    {evidenceLoading[phase.id] ? (
                      <ActivityIndicator size="small" color={theme.textTertiary} style={{ marginTop: 8 }} />
                    ) : phaseEvidence[phase.id] && phaseEvidence[phase.id].length > 0 ? (
                      <View style={styles.evidenceContainer}>
                        
                        {/* V2.6 STEP 1: Compressed Pattern Line (FIRST - INSIGHT) */}
                        {patternData?.compressed_pattern_lines?.[phase.id] && (
                          <View style={styles.timelineCompressedSection}>
                            <Text style={[styles.timelineCompressedLeadIn, { color: theme.textTertiary }]}>
                              This might be what's underneath:
                            </Text>
                            <View style={[styles.timelineCompressedContainer, { borderColor: Colors.accent + '40' }]}>
                              <Text style={[styles.timelineCompressedLine, { color: theme.text }]}>
                                {cleanText(patternData.compressed_pattern_lines[phase.id])}
                              </Text>
                            </View>
                          </View>
                        )}
                        
                        {/* V2.6 STEP 2: Identity Echo (when threshold met) */}
                        {patternData?.identity_echo && patternData?.identity_threshold_met && (
                          <View style={[styles.timelineIdentityEcho, { 
                            backgroundColor: Colors.accent + '08', 
                            borderColor: Colors.accent + '20' 
                          }]}>
                            <Text style={[styles.timelineIdentityEchoLabel, { color: Colors.accent }]}>
                              A pattern in how you move:
                            </Text>
                            <Text style={[styles.timelineIdentityEchoText, { color: theme.text }]}>
                              {cleanText(patternData.identity_echo)}
                            </Text>
                          </View>
                        )}
                        
                        {/* V2.7: Angle Line - Transit-based amplifier */}
                        {patternData?.angle_line && patternData?.compressed_pattern_lines?.[phase.id] && (
                          <View style={styles.timelineAngleSection}>
                            <Text style={[styles.timelineAngleLabel, { color: theme.textTertiary }]}>
                              Why this may feel stronger right now:
                            </Text>
                            <Text style={[styles.timelineAngleText, { color: theme.textSecondary }]}>
                              {cleanText(patternData.angle_line)}
                            </Text>
                          </View>
                        )}
                        
                        {/* V3: Facet Line - Where the pattern is most active */}
                        {patternData?.facet_line && patternData?.compressed_pattern_lines?.[phase.id] && (
                          <View style={styles.timelineFacetSection}>
                            <Text style={[styles.timelineFacetLabel, { color: theme.textTertiary }]}>
                              Where this may be landing:
                            </Text>
                            <Text style={[styles.timelineFacetText, { color: theme.textSecondary }]}>
                              {cleanText(patternData.facet_line)}
                            </Text>
                          </View>
                        )}
                        
                        {/* V3.1: Facet Memory Line - Pattern over time */}
                        {patternData?.facet_memory_line && patternData?.compressed_pattern_lines?.[phase.id] && (
                          <View style={styles.timelineFacetMemorySection}>
                            <Text style={[styles.timelineFacetMemoryText, { color: theme.textTertiary }]}>
                              {cleanText(patternData.facet_memory_line)}
                            </Text>
                          </View>
                        )}
                        
                        {/* V3.2: Facet Progression Line - Movement over time */}
                        {patternData?.facet_progression_line && patternData?.compressed_pattern_lines?.[phase.id] && (
                          <View style={styles.timelineFacetProgressionSection}>
                            <Text style={[styles.timelineFacetProgressionText, { color: theme.textTertiary }]}>
                              {cleanText(patternData.facet_progression_line)}
                            </Text>
                          </View>
                        )}
                        
                        {/* V2.6 STEP 3: Evidence Entries (SECOND - PROOF) */}
                        <Text style={[styles.evidenceIntro, { color: theme.textTertiary }]}>
                          This is how this phase has been showing up in your life:
                        </Text>
                        {phaseEvidence[phase.id].map((entry) => (
                          <View 
                            key={entry.id} 
                            style={[styles.evidenceCard, { 
                              backgroundColor: isDark ? 'rgba(139, 92, 246, 0.08)' : 'rgba(139, 92, 246, 0.05)',
                              borderColor: isDark ? 'rgba(139, 92, 246, 0.2)' : 'rgba(139, 92, 246, 0.15)',
                            }]}
                          >
                            <Text style={[styles.evidenceSnippet, { color: theme.text }]} numberOfLines={2}>
                              "{entry.content.substring(0, 100)}{entry.content.length > 100 ? '...' : ''}"
                            </Text>
                            <Text style={[styles.evidenceDate, { color: theme.textTertiary }]}>
                              {new Date(entry.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                            </Text>
                          </View>
                        ))}
                        
                      </View>
                    ) : (
                      <Text style={[styles.noEvidenceText, { color: theme.textTertiary }]}>
                        No journal entries from this phase yet. What you write during this time will appear here.
                      </Text>
                    )}
                  </View>
                )}
              </View>
            )}
          </TouchableOpacity>
        ))}
      </View>

      {/* Primary Turning Points */}
      <View style={styles.turningPointsContainer}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
          TURNING POINTS
        </Text>
        <Text style={[styles.sectionHelper, { color: theme.textTertiary }]}>
          After these moments, pretending not to know stops working.
        </Text>
        
        {timelineData.turningPoints.map((tp) => (
          <View
            key={tp.id}
            style={[styles.turningPointCard, { backgroundColor: isDark ? 'rgba(255, 193, 7, 0.06)' : 'rgba(255, 193, 7, 0.04)', borderColor: isDark ? 'rgba(255, 193, 7, 0.25)' : 'rgba(255, 193, 7, 0.2)' }]}
          >
            <View style={styles.turningPointHeader}>
              <Text style={[styles.turningPointDate, { color: isDark ? '#FFD54F' : '#F9A825' }]}>
                ⭐ {tp.date}
              </Text>
              <Text style={[styles.turningPointArea, { color: theme.textTertiary }]}>
                {tp.lifeArea}
              </Text>
            </View>
            
            <View style={styles.turningPointSection}>
              <Text style={[styles.turningPointSectionTitle, { color: theme.textSecondary }]}>
                Why this matters
              </Text>
              <Text style={[styles.turningPointText, { color: theme.text }]}>
                {tp.whyThisMatters}
              </Text>
            </View>

            <View style={styles.turningPointSection}>
              <Text style={[styles.turningPointSectionTitle, { color: theme.textSecondary }]}>
                What becomes clear
              </Text>
              <Text style={[styles.turningPointText, { color: theme.text }]}>
                {tp.whatBecomesClear}
              </Text>
            </View>

            <View style={styles.turningPointSection}>
              <Text style={[styles.turningPointSectionTitle, { color: '#E57373' }]}>
                What happens if avoided
              </Text>
              <Text style={[styles.turningPointText, { color: theme.textSecondary }]}>
                {tp.whatHappensIfAvoided}
              </Text>
            </View>
          </View>
        ))}
      </View>

      {/* Decision Windows */}
      <View style={styles.decisionWindowsContainer}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
          CHOICE POINTS
        </Text>
        <Text style={[styles.sectionHelper, { color: theme.textTertiary }]}>
          Windows where acting and waiting both carry distinct costs.
        </Text>
        
        {timelineData.decisionWindows.map((dw) => (
          <View
            key={dw.id}
            style={[styles.decisionWindowCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          >
            <View style={styles.decisionWindowHeader}>
              <Text style={[styles.decisionWindowDateRange, { color: theme.textTertiary }]}>
                {dw.dateRange}
              </Text>
              <Text style={[styles.decisionWindowContext, { color: Colors.accent }]}>
                {dw.context}
              </Text>
            </View>
            
            <Text style={[styles.decisionWindowPrompt, { color: theme.text }]}>
              "{dw.prompt}"
            </Text>

            <View style={styles.decisionOutcomes}>
              <View style={[styles.decisionOutcome, { backgroundColor: isDark ? 'rgba(76, 175, 80, 0.08)' : 'rgba(76, 175, 80, 0.05)' }]}>
                <Text style={[styles.decisionOutcomeLabel, { color: '#66BB6A' }]}>If you act →</Text>
                <Text style={[styles.decisionOutcomeText, { color: theme.textSecondary }]}>{dw.ifYouAct}</Text>
              </View>
              <View style={[styles.decisionOutcome, { backgroundColor: isDark ? 'rgba(255, 167, 38, 0.08)' : 'rgba(255, 167, 38, 0.05)' }]}>
                <Text style={[styles.decisionOutcomeLabel, { color: '#FFA726' }]}>If you wait →</Text>
                <Text style={[styles.decisionOutcomeText, { color: theme.textSecondary }]}>{dw.ifYouWait}</Text>
              </View>
            </View>
          </View>
        ))}
      </View>

      {/* Ask Mirror Button */}
      <TouchableOpacity
        style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
        onPress={onOpenChat}
      >
        <Text style={{ fontSize: 16, color: theme.background }}>💬</Text>
        <Text style={[styles.askMirrorText, { color: theme.background }]}>Ask about this year</Text>
      </TouchableOpacity>
    </View>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  headerContainer: {
    marginBottom: 16,
    position: 'relative',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '600',
    letterSpacing: 0.3,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 13,
    fontStyle: 'italic',
  },
  refreshButton: {
    position: 'absolute',
    top: 0,
    right: 0,
    paddingHorizontal: 10,
    paddingVertical: 6,
    minWidth: 80,
    minHeight: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  refreshButtonText: {
    fontSize: 12,
    letterSpacing: 0.4,
  },
  debugMeta: {
    fontSize: 10,
    marginTop: 6,
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 8,
  },
  sectionHelper: {
    fontSize: 12,
    fontStyle: 'italic',
    marginBottom: 12,
    marginTop: -4,
  },
  
  // Year Theme
  yearThemeCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 20,
  },
  yearThemeLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 10,
  },
  yearThemeText: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '500',
    fontStyle: 'italic',
  },

  // Primary Arc
  primaryArcContainer: {
    marginBottom: 24,
  },
  primaryArcText: {
    fontSize: 14,
    lineHeight: 22,
  },

  // Phases
  phasesContainer: {
    marginBottom: 24,
  },
  phaseCard: {
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 10,
    overflow: 'hidden',
  },
  phaseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
  },
  phaseHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  primaryBadge: {
    fontSize: 12,
    marginRight: 8,
  },
  phaseDateRange: {
    fontSize: 11,
    fontWeight: '500',
  },
  phaseName: {
    fontSize: 14,
    fontWeight: '600',
    marginTop: 1,
  },
  phaseHumanMeaning: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 2,
    opacity: 0.8,
  },
  phaseExpandIcon: {
    fontSize: 22,
    fontWeight: '300',
    marginLeft: 8,
  },
  phaseDetails: {
    paddingHorizontal: 12,
    paddingBottom: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128,128,128,0.2)',
    paddingTop: 12,
  },
  phaseSection: {
    marginBottom: 12,
  },
  phaseSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 5,
  },
  phaseBullet: {
    fontSize: 13,
    lineHeight: 19,
    marginLeft: 2,
    marginBottom: 2,
  },

  // Turning Points
  turningPointsContainer: {
    marginBottom: 24,
  },
  turningPointCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 10,
  },
  turningPointHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  turningPointDate: {
    fontSize: 13,
    fontWeight: '700',
  },
  turningPointArea: {
    fontSize: 11,
    fontStyle: 'italic',
  },
  turningPointSection: {
    marginBottom: 10,
  },
  turningPointSectionTitle: {
    fontSize: 10,
    fontWeight: '600',
    marginBottom: 3,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  turningPointText: {
    fontSize: 13,
    lineHeight: 19,
  },

  // Decision Windows
  decisionWindowsContainer: {
    marginBottom: 24,
  },
  decisionWindowCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 10,
  },
  decisionWindowHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  decisionWindowDateRange: {
    fontSize: 11,
    fontWeight: '500',
  },
  decisionWindowContext: {
    fontSize: 10,
    fontWeight: '600',
  },
  decisionWindowPrompt: {
    fontSize: 14,
    fontStyle: 'italic',
    fontWeight: '500',
    marginBottom: 12,
    lineHeight: 20,
  },
  decisionOutcomes: {
    gap: 8,
  },
  decisionOutcome: {
    padding: 10,
    borderRadius: 8,
  },
  decisionOutcomeLabel: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 3,
  },
  decisionOutcomeText: {
    fontSize: 12,
    lineHeight: 17,
  },

  // Ask Mirror Button
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    marginTop: 8,
    marginBottom: 40,
  },
  askMirrorText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Journal Evidence styles (Journal ↔ Timeline connection)
  evidenceContainer: {
    marginTop: 8,
    gap: 8,
  },
  evidenceSectionTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  evidenceIntro: {
    fontSize: 12,
    fontStyle: 'italic',
    marginBottom: 10,
  },
  evidenceCard: {
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  evidenceSnippet: {
    fontSize: 12,
    lineHeight: 17,
    fontStyle: 'italic',
  },
  evidenceDate: {
    fontSize: 10,
    marginTop: 6,
    textAlign: 'right',
  },
  evidenceContextLine: {
    fontSize: 11,
    fontStyle: 'italic',
    marginTop: 10,
    textAlign: 'center',
  },
  noEvidenceText: {
    fontSize: 12,
    fontStyle: 'italic',
    marginTop: 6,
  },
  // V2.6: Compressed Pattern Line (INSIGHT FIRST)
  timelineCompressedSection: {
    marginBottom: 14,
  },
  timelineCompressedLeadIn: {
    fontSize: 11,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  timelineCompressedContainer: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderLeftWidth: 3,
  },
  timelineCompressedLine: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  // V2.6: Identity Echo (when threshold met)
  timelineIdentityEcho: {
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 12,
  },
  timelineIdentityEchoLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  timelineIdentityEchoText: {
    fontSize: 12,
    lineHeight: 18,
  },
  // V2.7: Angle Line - Transit-based amplifier
  timelineAngleSection: {
    marginBottom: 12,
    paddingLeft: 8,
  },
  timelineAngleLabel: {
    fontSize: 10,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  timelineAngleText: {
    fontSize: 11,
    lineHeight: 17,
    fontStyle: 'italic',
  },
  // V3: Facet Line
  timelineFacetSection: {
    marginBottom: 12,
    paddingLeft: 8,
  },
  timelineFacetLabel: {
    fontSize: 10,
    fontStyle: 'italic',
    marginBottom: 4,
  },
  timelineFacetText: {
    fontSize: 11,
    lineHeight: 17,
  },
  // V3.1: Facet Memory Line - Pattern over time
  timelineFacetMemorySection: {
    marginBottom: 12,
    paddingLeft: 8,
  },
  timelineFacetMemoryText: {
    fontSize: 10,
    lineHeight: 16,
    fontStyle: 'italic',
  },
  // V3.2: Facet Progression Line - Movement over time
  timelineFacetProgressionSection: {
    marginBottom: 12,
    paddingLeft: 8,
  },
  timelineFacetProgressionText: {
    fontSize: 10,
    lineHeight: 16,
    fontStyle: 'italic',
  },
});
