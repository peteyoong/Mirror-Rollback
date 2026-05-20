import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  Modal,
  Pressable,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import * as Clipboard from 'expo-clipboard';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { useForumContext } from '../../contexts/ForumContext';
import api, { 
  getForum, 
  getSharedReflections, 
  ForumReflection, 
  getForumExercise, 
  getForumMembers, 
  ForumMember,
  getForumPulse,
  ForumPulseResponse,
  ForumPulseMemberCard,
  getForumMemberLens,
  ForumMemberLensData,
  getPatternDiagnosis,
  PatternDiagnosisResponse,
  getForumLiveField,
  ForumLiveFieldResponse,
  getForumContributions,
  ForumContribution,
  getForumMemberSummary,
  ForumMemberSummary,
} from '../../services/api';
import ForumChatView from '../../components/ForumChatView';
import LiveFieldCard from '../../components/LiveFieldCard';
import StoryOfThisCircle from '../../components/StoryOfThisCircle';
import Constants from 'expo-constants';

// Visible build marker for live deployment verification.
import { BUILD_ID } from '../../constants/buildMarker';


// Types for modal states
interface MemberProfileModal {
  visible: boolean;
  member: ForumPulseMemberCard | null;
  lensData: ForumMemberLensData | null;
  loading: boolean;
}

interface DomainReflectionsModal {
  visible: boolean;
  domainId: string;
  domainName: string;
  reflections: ForumReflection[];
}

interface TypeMembersModal {
  visible: boolean;
  typeName: string;
  members: ForumPulseMemberCard[];
}

interface InsightModal {
  visible: boolean;
  insight: string;
}

// =============================================================================
// HUMAN UNDERSTANDING HELPER FUNCTIONS
// Transform lens data into FELT, RELATIONAL, ACTIONABLE descriptions
// =============================================================================

const getArchetypeLabel = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const enneaType = lensData.enneagram.core_type;
  
  // Generate archetype based on HD type + Enneagram
  const archetypes: Record<string, Record<number, string>> = {
    'Manifestor': { 1: 'The Principled Initiator', 2: 'The Generous Starter', 3: 'The Driven Pioneer', 4: 'The Creative Catalyst', 5: 'The Strategic Mover', 6: 'The Vigilant Leader', 7: 'The Visionary Igniter', 8: 'The Bold Activator', 9: 'The Peaceful Initiator' },
    'Generator': { 1: 'The Dedicated Builder', 2: 'The Nurturing Worker', 3: 'The Productive Achiever', 4: 'The Soulful Creator', 5: 'The Deep Investigator', 6: 'The Loyal Sustainer', 7: 'The Enthusiastic Doer', 8: 'The Powerful Producer', 9: 'The Steady Anchor' },
    'Manifesting Generator': { 1: 'The Efficient Perfectionist', 2: 'The Multi-talented Helper', 3: 'The Fast Achiever', 4: 'The Expressive Multi-tasker', 5: 'The Quick Learner', 6: 'The Adaptive Problem-solver', 7: 'The Energetic Explorer', 8: 'The Dynamic Force', 9: 'The Versatile Harmonizer' },
    'Projector': { 1: 'The Discerning Guide', 2: 'The Intuitive Counselor', 3: 'The Strategic Advisor', 4: 'The Deep Seer', 5: 'The Wise Observer', 6: 'The Trusted Mentor', 7: 'The Insightful Optimist', 8: 'The Powerful Guide', 9: 'The Gentle Director' },
    'Reflector': { 1: 'The Fair Mirror', 2: 'The Empathic Barometer', 3: 'The Adaptive Mirror', 4: 'The Sensitive Reflector', 5: 'The Observant Mirror', 6: 'The Community Sensor', 7: 'The Joyful Evaluator', 8: 'The Honest Mirror', 9: 'The Peaceful Assessor' },
  };
  
  if (hdType && enneaType && archetypes[hdType]?.[enneaType]) {
    return archetypes[hdType][enneaType];
  }
  
  if (hdType === 'Manifestor') return 'The Initiator';
  if (hdType === 'Generator') return 'The Builder';
  if (hdType === 'Manifesting Generator') return 'The Multi-tasker';
  if (hdType === 'Projector') return 'The Guide';
  if (hdType === 'Reflector') return 'The Mirror';
  return '';
};

// NEW: What it feels like to be WITH them (second person, experiential)
const getWhatItFeelsLike = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  let base = '';
  
  if (hdType === 'Manifestor') {
    base = "You may feel their urgency before you understand it. There's a sense that something wants to move—even if it's not fully clear yet.";
  } else if (hdType === 'Generator') {
    base = "You can feel their energy when they're lit up about something. When they're not, there's a heaviness that's hard to miss.";
  } else if (hdType === 'Manifesting Generator') {
    base = "You might feel like you're in a whirlwind. They move fast, shift gears quickly, and you may wonder how they keep track of it all.";
  } else if (hdType === 'Projector') {
    base = "You may feel seen in a way that's both comforting and exposing. They notice things others miss—including things about you.";
  } else if (hdType === 'Reflector') {
    base = "You may find yourself reflected back. The mood in the room often shows up in how they seem—they're taking in more than they let on.";
  }
  
  // Authority modifier
  if (authority?.includes('Emotional')) {
    base += " Their energy can shift—what feels true to them today may change tomorrow. This isn't inconsistency; it's their process.";
  }
  
  // Enneagram flavor
  if (enneaType === 7) {
    base += " There's often lightness around them, but sometimes you sense something underneath they're not slowing down to feel.";
  } else if (enneaType === 8) {
    base += " You may feel the weight of their presence—protective, intense, sometimes confronting.";
  } else if (enneaType === 4) {
    base += " You might sense depth under the surface, a longing for something real that not everyone sees.";
  } else if (enneaType === 2) {
    base += " You may feel cared for, but also wonder if they're taking care of themselves.";
  } else if (enneaType === 6) {
    base += " You might notice they're scanning for what could go wrong—not out of pessimism, but vigilance.";
  }
  
  return base;
};

// SHORTENED: How they show up (max 2 lines)
const getHowTheyShowUp = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const enneaType = lensData.enneagram.core_type;
  
  if (hdType === 'Manifestor') {
    return "Initiates and moves without waiting for consensus. Acts on internal timing, not external cues.";
  } else if (hdType === 'Generator') {
    return "Shows up with sustainable energy when engaged. Responds to what's in front of them rather than pushing forward.";
  } else if (hdType === 'Manifesting Generator') {
    return "Multi-tracks, moves fast, pivots often. Efficiency over linearity.";
  } else if (hdType === 'Projector') {
    return "Observes before engaging. Offers insight when invited, not before.";
  } else if (hdType === 'Reflector') {
    return "Takes in the group's energy. Reflects back what's really happening.";
  }
  
  return "Shows up authentically based on their inner rhythm.";
};

const getAtTheirBest = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const enneaType = lensData.enneagram.core_type;
  
  let base = '';
  
  if (hdType === 'Manifestor') {
    base = "Clear, decisive, and catalytic. Creates movement when things are stuck. Others feel permission to act.";
  } else if (hdType === 'Generator') {
    base = "Deeply satisfying output. Magnetic presence that draws the right opportunities. The work itself becomes the reward.";
  } else if (hdType === 'Manifesting Generator') {
    base = "Accomplishes what seems impossible. Creates shortcuts others can follow. Brings energy and momentum.";
  } else if (hdType === 'Projector') {
    base = "Sees what's really going on. Guides others to their own clarity. Wisdom that lands when received.";
  } else if (hdType === 'Reflector') {
    base = "Reads the room with uncanny accuracy. Offers perspective that cuts through noise. Reveals truth by reflection.";
  }
  
  return base;
};

// RENAMED: "When things get tense" (situational, not personality-based)
const getWhenThingsGetTense = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  let base = '';
  
  if (hdType === 'Manifestor') {
    base = "When decisions drag or feel unclear, they may push forward anyway—which can feel like pressure to others.";
  } else if (hdType === 'Generator') {
    base = "When forced to commit before feeling a clear response, they may say yes but disengage later. Or push through work that drains them.";
  } else if (hdType === 'Manifesting Generator') {
    base = "When things slow down or require too much waiting, they may skip ahead or abandon ship—leaving others scrambling.";
  } else if (hdType === 'Projector') {
    base = "When their input goes unacknowledged, they may either over-give or withdraw entirely. The bitterness can be quiet but real.";
  } else if (hdType === 'Reflector') {
    base = "When the group energy is off, they absorb it. They may seem checked out or overwhelmed—but they're processing everyone's stuff.";
  }
  
  if (authority?.includes('Emotional') && !base.includes('clarity')) {
    base += " If pushed for fast answers, they may commit to something they'll later need to undo.";
  }
  
  if (enneaType === 9) {
    base += " They may go along with decisions to keep the peace, then quietly resist later.";
  } else if (enneaType === 6) {
    base += " They may voice concerns that sound like resistance—but it's actually loyalty trying to protect the group.";
  }
  
  return base;
};

// NEW: Where misunderstandings happen (CRITICAL for forum)
const getWhereMisunderstandingsHappen = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  let base = '';
  
  if (hdType === 'Manifestor') {
    base = "They may think they've communicated clearly—others may feel left out of the process. Their 'informing' can feel like announcing.";
  } else if (hdType === 'Generator') {
    base = "Their 'yes' may sound enthusiastic even when it's not fully there. Others may assume commitment that wasn't actually given.";
  } else if (hdType === 'Manifesting Generator') {
    base = "They may skip steps that seem obvious to them—but others need those steps to follow along. Speed can feel like dismissal.";
  } else if (hdType === 'Projector') {
    base = "They may assume their insight is wanted. Others may feel analyzed or advised when they just wanted to be heard.";
  } else if (hdType === 'Reflector') {
    base = "Their shifting opinions may look like indecisiveness. Others may not realize they're reflecting the group's own uncertainty back.";
  }
  
  if (authority?.includes('Emotional')) {
    base += " What they said yesterday may change today—not because they were dishonest, but because clarity moves like a wave.";
  }
  
  if (enneaType === 5) {
    base += " Their silence may be read as disinterest—when they're actually processing deeply.";
  } else if (enneaType === 3) {
    base += " Their efficiency may feel cold. They're often moving toward results faster than others expect.";
  } else if (enneaType === 8) {
    base += " Their directness can land as aggression—even when they're trying to protect.";
  }
  
  return base;
};

// SHARPENED: How to work with them (direct + practical)
const getHowToWorkWith = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  let lines: string[] = [];
  
  if (hdType === 'Manifestor') {
    lines.push("Keep them informed early—not after decisions are made.");
    lines.push("Give them space to reach clarity instead of forcing answers.");
  } else if (hdType === 'Generator') {
    lines.push("Ask yes/no questions instead of open-ended ones.");
    lines.push("Watch their energy—it tells you more than their words.");
  } else if (hdType === 'Manifesting Generator') {
    lines.push("Let them pivot—it's how they find what works.");
    lines.push("Trust their process even when it looks chaotic.");
  } else if (hdType === 'Projector') {
    lines.push("Invite their perspective explicitly. Don't assume they'll offer it.");
    lines.push("Acknowledge their contributions—recognition matters more than you think.");
  } else if (hdType === 'Reflector') {
    lines.push("Give them time for big decisions—a month if possible.");
    lines.push("Ask 'what are you noticing?' to access their insight.");
  }
  
  if (authority?.includes('Emotional')) {
    lines.push("Don't press for immediate decisions. Let them sleep on it.");
  }
  
  if (enneaType === 2) lines.push("Ask what they need—they often forget to say.");
  else if (enneaType === 8) lines.push("Be direct. Don't soften or circle around issues.");
  else if (enneaType === 5) lines.push("Give them prep time. Surprises deplete them.");
  
  return lines.join('\n');
};

// NEW: Micro-trigger (1-liner pattern interrupt for real-time awareness)
const getMicroTrigger = (lensData: ForumMemberLensData): string => {
  const hdType = lensData.human_design.type;
  const authority = lensData.human_design.authority;
  const enneaType = lensData.enneagram.core_type;
  
  if (hdType === 'Manifestor') {
    if (enneaType === 7) return "When they suddenly go quiet after proposing something big.";
    if (enneaType === 8) return "When their energy shifts from driving to withdrawing mid-conversation.";
    return "When they stop initiating and start waiting for others to catch up.";
  } else if (hdType === 'Generator') {
    if (enneaType === 9) return "When they agree too easily—without that spark of real engagement.";
    return "When their energy drops mid-task, but they keep pushing anyway.";
  } else if (hdType === 'Manifesting Generator') {
    if (enneaType === 3) return "When they speed past a concern someone else raised—watch if it resurfaces.";
    return "When they suddenly pivot away from something they seemed committed to.";
  } else if (hdType === 'Projector') {
    if (enneaType === 4) return "When they offer insight and no one responds—the silence lands hard.";
    return "When they start over-explaining or advising without being asked.";
  } else if (hdType === 'Reflector') {
    return "When their mood shifts suddenly—something in the group just changed.";
  }
  
  if (authority?.includes('Emotional')) {
    return "When they commit quickly under pressure—check back in a day or two.";
  }
  
  return "When their pattern shifts—pause and ask what's happening.";
};

export default function ForumHomeScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const forumId = id as string;
  const { setForumContext, clearForumContext } = useForumContext();
  
  const [forum, setForum] = useState<any | null>(null);
  const [reflections, setReflections] = useState<ForumReflection[]>([]);
  const [members, setMembers] = useState<ForumMember[]>([]);
  const [pulse, setPulse] = useState<ForumPulseResponse | null>(null);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [expandedReflection, setExpandedReflection] = useState<string | null>(null);
  
  // Forum Chat state
  const [showForumChat, setShowForumChat] = useState(false);
  const [forumChatInitialMode, setForumChatInitialMode] = useState<'self' | 'member' | 'forum'>('self');
  const [forumChatInitialMember, setForumChatInitialMember] = useState<ForumPulseMemberCard | null>(null);
  
  // Modal states for interactive Forum Pulse
  const [memberModal, setMemberModal] = useState<MemberProfileModal>({ visible: false, member: null, lensData: null, loading: false });
  const [domainModal, setDomainModal] = useState<DomainReflectionsModal>({ visible: false, domainId: '', domainName: '', reflections: [] });
  const [typeModal, setTypeModal] = useState<TypeMembersModal>({ visible: false, typeName: '', members: [] });
  const [insightModal, setInsightModal] = useState<InsightModal>({ visible: false, insight: '' });
  
  // FIX 4: Forum Pattern State
  const [forumPattern, setForumPattern] = useState<PatternDiagnosisResponse | null>(null);
  const [forumPatternLoading, setForumPatternLoading] = useState(false);
  // Story Hero expansion (new forum UX)
  const [storyExpansionOpen, setStoryExpansionOpen] = useState(false);
  const [storyBullets, setStoryBullets] = useState<string[]>([]);
  const [analyticsExpanded, setAnalyticsExpanded] = useState(false);

  // Lazy-load the expansion bullets when the user taps "See how this plays out"
  useEffect(() => {
    if (!storyExpansionOpen || storyBullets.length > 0 || !forumId || !user?.id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await api.get(`/forums/${forumId}/story?user_id=${user.id}`);
        const story: string = res.data?.story || '';
        // Extract bullets from the [SECTION:How This Plays Out] block
        const m = story.match(/\[SECTION:How This Plays Out\]\s*([\s\S]*?)(?=\[SECTION:|$)/i);
        const block = m ? m[1] : '';
        const bullets = block
          .split(/\n/)
          .map((l) => l.trim())
          .filter((l) => l.startsWith('-'))
          .map((l) => l.replace(/^[-•]\s*/, ''))
          .filter(Boolean)
          .slice(0, 5);
        if (!cancelled) setStoryBullets(bullets);
      } catch (e) {
        if (!cancelled) setStoryBullets(['How this plays out is still coming into focus.']);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [storyExpansionOpen, forumId, user?.id, storyBullets.length]);
  const [showForumPattern, setShowForumPattern] = useState(false);
  
  // Live Field State - Real-time field dynamics
  const [liveField, setLiveField] = useState<ForumLiveFieldResponse | null>(null);
  const [liveFieldLoading, setLiveFieldLoading] = useState(false);

  // What Each Person Brings — compact contribution cards
  const [contributions, setContributions] = useState<ForumContribution[] | null>(null);

  // Interactive member summary card — shown inline below the members row
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(null);
  const [memberSummaries, setMemberSummaries] = useState<Record<string, ForumMemberSummary>>({});
  const [memberSummaryLoading, setMemberSummaryLoading] = useState<string | null>(null);
  
  // Member profile state
  const [showPatternSignals, setShowPatternSignals] = useState(false);

  // Forum loading instrumentation — surfaces in the recovery UI when
  // a Safari/PWA load gets stuck. Updated as each API call completes
  // so we always know exactly where we are in the load sequence.
  const [loadStep, setLoadStep] = useState<string>('idle');
  const [lastApiUrl, setLastApiUrl] = useState<string>('');
  const [lastErrorMsg, setLastErrorMsg] = useState<string>('');

  // ===========================================================================
  // P1 Forum Runtime Stability Refs (May 2026 hotfix)
  // ---------------------------------------------------------------------------
  // The previous version of this screen had a subtle infinite re-fetch loop
  // on Safari because `fetchData` was wrapped in useCallback with `forum` as
  // a dependency. Every successful `setForum(...)` changed the callback
  // identity, which re-fired the [fetchData] useEffect, which set
  // loading=true again — producing the exact flicker / spinner-flash /
  // partial-render symptoms reported in production.
  //
  // The fix:
  //   1. `forumRef` lets fetchData check "do we already have a forum doc?"
  //      without needing `forum` in the dep array.
  //   2. `inFlightRef` dedupes overlapping fetches (Safari sometimes fires
  //      the effect twice during StrictMode / focus events).
  //   3. `fetchCountRef`, `renderCountRef` instrument the lifecycle so we
  //      can verify in the console that the forum loads ONCE.
  // ===========================================================================
  const forumRef = useRef<any | null>(null);
  const inFlightRef = useRef<boolean>(false);
  const fetchCountRef = useRef<number>(0);
  const renderCountRef = useRef<number>(0);
  const hasLoadedOnceRef = useRef<boolean>(false);
  renderCountRef.current += 1;

  // Per-call timeout helper. We were getting Safari hangs where a
  // SINGLE slow API call (Forum Pulse, Live Field) blocked the whole
  // Promise.all for 30s+ before the parent safety timeout fired. By
  // racing each call against an 8s AbortController/timer and using
  // Promise.allSettled, the page now renders with whatever loaded —
  // and surfaces which call actually hung in the debug strip.
  const withTimeout = <T,>(
    p: Promise<T>,
    ms: number,
    label: string,
    fallback: T,
  ): Promise<T> => {
    return new Promise<T>((resolve) => {
      let done = false;
      const finish = (v: T) => { if (!done) { done = true; resolve(v); } };
      const timer = setTimeout(() => {
        console.warn(`[Forum] ${label} timed out after ${ms}ms`);
        setLastErrorMsg((prev) => prev || `${label} timed out`);
        finish(fallback);
      }, ms);
      p.then(
        (v) => { clearTimeout(timer); finish(v); },
        (e) => {
          clearTimeout(timer);
          console.warn(`[Forum] ${label} rejected:`, e?.message ?? e);
          setLastErrorMsg((prev) => prev || `${label}: ${e?.message ?? e}`);
          finish(fallback);
        },
      );
    });
  };

  const fetchData = useCallback(async (showRefresh = false) => {
    // ===========================================================================
    // P1 Forum Runtime Stability (May 2026 hotfix)
    // ---------------------------------------------------------------------------
    // 1. Dedupe: if a fetch is already in flight, drop the duplicate. Safari
    //    sometimes fires the parent effect twice in quick succession during
    //    auth-context resolution / focus events — without this guard you get
    //    overlapping Promise.allSettled batches racing each other and the
    //    later one overwriting the earlier one mid-render → flicker.
    if (inFlightRef.current) {
      console.log('[Forum/Stability] fetchData call dropped — fetch already in flight');
      return;
    }
    inFlightRef.current = true;
    fetchCountRef.current += 1;
    const thisFetch = fetchCountRef.current;

    // Forensic console logging for Safari debugging — these messages
    // are the FIRST things to look for in console when the user
    // reports "stuck on Loading forum..." on Safari.
    try {
      console.log(`[Forum/Stability] -------- fetchData #${thisFetch} fired (renders=${renderCountRef.current}) --------`);
      console.log('[Forum/Safari-debug] pathname:',
        typeof window !== 'undefined' ? window.location.pathname : '(non-web)');
      console.log('[Forum/Safari-debug] forumId param:', forumId);
      console.log('[Forum/Safari-debug] user.id present:', !!user?.id, 'user.email:', user?.email);
      console.log('[Forum/Safari-debug] hasLoadedOnce:', hasLoadedOnceRef.current);
    } catch {/* logging is best effort */}

    // P0 Safari hotfix (May 2026): if auth context hasn't resolved
    // OR forumId is missing, we used to set a soft error and let the
    // user sit on a recovery screen. On Safari iOS that path was
    // occasionally never reached because the auth hook itself was
    // hanging. New behavior: redirect to the Welcome / Forums landing
    // immediately instead of waiting forever.
    if (!user?.id || !forumId) {
      console.warn('[Forum/Safari-debug] missing user.id or forumId → redirecting');
      setLoading(false);
      setRefreshing(false);
      inFlightRef.current = false;
      if (!forumId) {
        setError('Forum not found');
        setLoadStep('missing_forum_id');
        // Send back to forums list — friendlier than a dead screen.
        setTimeout(() => router.replace('/forums'), 50);
      } else if (!user?.id) {
        setError('Please sign in to view this forum');
        setLoadStep('missing_user_id');
        // No auth → route to welcome / login. Replace prevents the
        // forum URL from staying in history and re-firing this state.
        setTimeout(() => router.replace('/welcome'), 50);
      }
      return;
    }

    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    setLastErrorMsg('');
    setLoadStep('fetching_in_parallel');

    try {
      // Per-API timeout = 7s. Granular fallbacks so a single slow call
      // can't cause the whole forum to spin. Each call also updates
      // lastApiUrl when it starts so the debug strip can pinpoint
      // exactly which one is in flight.
      const trackedGet = <T,>(label: string, url: string, p: Promise<T>, fb: T) => {
        setLastApiUrl(url);
        return withTimeout(p, 7000, label, fb);
      };

      const t0 = Date.now();
      const results = await Promise.allSettled([
        trackedGet('getForum',               `/forums/${forumId}`,                  getForum(forumId, user.id),                null as any),
        trackedGet('getSharedReflections',   `/forums/${forumId}/reflections`,      getSharedReflections(forumId, user.id),    { reflections: [] as ForumReflection[] } as any),
        trackedGet('getForumExercise',       `/forums/${forumId}/exercise`,         getForumExercise(forumId, user.id),        { has_submitted: false } as any),
        trackedGet('getForumMembers',        `/forums/${forumId}/members`,          getForumMembers(forumId, user.id),         { members: [] as ForumMember[] } as any),
        trackedGet('getForumPulse',          `/forums/${forumId}/pulse`,            getForumPulse(forumId, user.id),           null as any),
        trackedGet('getForumLiveField',      `/forums/${forumId}/live-field-v1`,    getForumLiveField(forumId, user.id),       null as any),
        trackedGet('getForumContributions',  `/forums/${forumId}/contributions`,    getForumContributions(forumId, user.id),   { contributions: [] as ForumContribution[] } as any),
      ]);
      const elapsed = Date.now() - t0;
      console.log(`[Forum/Stability] fetch #${thisFetch} settled in ${elapsed}ms`);

      setLoadStep('applying_results');
      const [forumR, reflR, exR, memR, pulseR, lfR, contR] = results;
      const val = <T,>(r: PromiseSettledResult<T>): T | null =>
        r.status === 'fulfilled' ? r.value : null;

      // Forensic: log which payload sections came back empty/null so we
      // can pinpoint which card silently disappeared.
      const payloadReport = {
        forum: val(forumR) ? 'ok' : 'MISSING',
        reflections: (val(reflR) as any)?.reflections?.length ?? 'MISSING',
        exercise: val(exR) ? 'ok' : 'MISSING',
        members: (val(memR) as any)?.members?.length ?? 'MISSING',
        pulse: val(pulseR) ? 'ok' : 'MISSING',
        liveField: val(lfR) ? 'ok' : 'MISSING',
        contributions: (val(contR) as any)?.contributions?.length ?? 'MISSING',
      };
      console.log(`[Forum/Stability] payload #${thisFetch}:`, payloadReport);

      const forumData = val(forumR);
      if (forumData) {
        setForum(forumData);
        forumRef.current = forumData;
      } else if (!forumRef.current) {
        // Forum is the ONE call we can't degrade past — if we have no
        // forum object after a fresh load and have no prior cached one,
        // surface a hard error rather than render an empty shell.
        throw new Error('Forum data unavailable');
      }
      const reflData  = val(reflR) || { reflections: [] };
      const exData    = val(exR)   || { has_submitted: false };
      const memData   = val(memR)  || { members: [] };
      const contData  = val(contR);

      setReflections((reflData as any).reflections || []);
      setHasSubmitted(!!(exData as any).has_submitted);
      setMembers((memData as any).members || []);
      setPulse(val(pulseR));
      setLiveField(val(lfR));
      // Defensive: only OVERWRITE contributions if we got a non-null
      // payload back. Keeps any prior render intact when the API
      // briefly fails — prevents the "What Each Person Brings" card
      // from disappearing mid-session.
      if (contData) {
        setContributions((contData as any).contributions || []);
      }
      setError(null);
      setLoadStep('done');
      hasLoadedOnceRef.current = true;
    } catch (err: any) {
      console.error('[Forum] Error fetching data:', err);
      setLastErrorMsg(err?.message || String(err));
      if (err?.response?.status === 403) {
        setError('You are not a member of this forum');
        setLoadStep('error_403');
      } else {
        setError('Unable to load forum');
        setLoadStep('error_generic');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      inFlightRef.current = false;
    }
    // CRITICAL: Do NOT include `forum` (or any state set inside this
    // callback) in the deps array. That created an infinite re-fetch
    // loop in production because every setForum() changed the callback
    // identity → the parent useEffect re-fired → loading flicker.
    // We use forumRef.current to read the latest forum value safely.
  }, [user?.id, forumId, router]);

  useEffect(() => {
    // Load ONCE per (user, forum) pair. fetchData internally dedupes
    // overlapping calls; this effect is intentionally simple so the
    // forum shell never thrashes.
    fetchData();
  }, [fetchData]);

  // Safety net (May 2026, hotfix v2): if the loading state hasn't
  // resolved in 5s for any reason (Safari iOS service-worker hang,
  // stale bundle, flaky network on a deployed PWA, etc.) surface the
  // recovery UI with Retry / Clear-Cache / Back instead of letting
  // the user sit on an infinite "Loading forum..." spinner.
  // Tightened from 8s → 5s after Safari reports. Cleared on unmount
  // and when `loading` transitions to false.
  useEffect(() => {
    if (!loading) return;
    const t = setTimeout(() => {
      console.warn('[Forum/Safari-debug] safety_timeout_5s fired — forcing recovery UI');
      setError((prev) => prev || "This is taking longer than expected — please retry.");
      setLoadStep((prev) => prev === 'fetching_in_parallel' ? 'safety_timeout_5s' : prev);
      setLoading(false);
    }, 5000);
    return () => clearTimeout(t);
  }, [loading]);

  // Clear the most likely sources of Safari/PWA cache corruption and
  // hard-reload the app, skipping the HTTP cache. Used by the
  // recovery UI's "Clear local cache & reload" button.
  const handleClearCacheAndReload = useCallback(() => {
    try {
      if (typeof window !== 'undefined') {
        // Wipe forum-scoped storage so a stale member-cache doesn't
        // resurrect after reload, but keep user/session so the user
        // doesn't have to log back in.
        try {
          const keys: string[] = [];
          for (let i = 0; i < window.localStorage.length; i++) {
            const k = window.localStorage.key(i);
            if (!k) continue;
            if (k.startsWith('forum_') || k.startsWith('mirror_forum_') || k.includes('ForumContext')) {
              keys.push(k);
            }
          }
          keys.forEach((k) => window.localStorage.removeItem(k));
        } catch {}
        try { window.sessionStorage.clear(); } catch {}
        // Force-reload bypassing the HTTP cache (Safari honors this).
        window.location.reload();
      }
    } catch (e) {
      console.warn('[Forum] cache clear failed:', e);
    }
  }, []);

  const handleBack = () => {
    clearForumContext();
    router.push('/forums');
  };

  // Interactive Member Summary — tap a member to view a compact multi-lens
  // summary card inline, right below the members row. Summaries are cached
  // client-side so repeat taps are instant.
  const handleSelectMember = useCallback(async (memberId: string) => {
    if (!user?.id || !forumId) return;
    // Toggle off when re-tapping the same member
    if (selectedMemberId === memberId) {
      setSelectedMemberId(null);
      return;
    }
    setSelectedMemberId(memberId);
    if (memberSummaries[memberId]) return; // already cached
    setMemberSummaryLoading(memberId);
    try {
      const resp = await getForumMemberSummary(forumId, memberId, user.id);
      if (resp?.success && resp.summary) {
        setMemberSummaries((prev) => ({ ...prev, [memberId]: resp.summary! }));
      }
    } catch (err) {
      console.error('[Forum] member summary error:', err);
    } finally {
      setMemberSummaryLoading((curr) => (curr === memberId ? null : curr));
    }
  }, [user?.id, forumId, selectedMemberId, memberSummaries]);

  const handleBeginReflection = () => {
    // Navigate to the Forum Updates page with forum context
    // This is the new structured update experience
    router.push(`/forums/updates?forumId=${forumId}&forumName=${encodeURIComponent(forum?.name || 'Forum')}`);
  };

  const handleMyMirrorProfile = () => {
    // Set forum context before navigating to Mirror
    if (forum) {
      setForumContext({
        forumId: forumId,
        forumName: forum.name,
        exerciseId: forum.active_exercise?.id || null,
        exerciseTitle: forum.active_exercise?.title || null,
      });
    }
    // Navigate to the Lenses tab where user can browse their insights
    router.push('/(tabs)/lenses');
  };

  const handleCopyInvite = async () => {
    if (!forum?.invite_token) return;
    const baseUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL || '';
    const link = `${baseUrl}/forums/join/${forum.invite_token}`;
    await Clipboard.setStringAsync(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDeleteForum = async () => {
    if (!forum || !user?.id) return;
    if (forum.created_by !== user.id) {
      if (Platform.OS === 'web') {
        // eslint-disable-next-line no-alert
        window.alert('Only the forum creator can delete this forum.');
      } else {
        Alert.alert('Not Allowed', 'Only the forum creator can delete this forum.');
      }
      return;
    }
    
    const performDelete = async () => {
      try {
        await api.post(`/forums/${id}/delete?user_id=${user.id}`);
        router.replace('/(tabs)');
      } catch (err: any) {
        const msg = err?.response?.data?.detail || 'Failed to delete forum';
        if (Platform.OS === 'web') {
          // eslint-disable-next-line no-alert
          window.alert(`Error: ${msg}`);
        } else {
          Alert.alert('Error', msg);
        }
      }
    };
    
    if (Platform.OS === 'web') {
      // Alert.alert destructive callback doesn't fire on React Native Web;
      // use window.confirm instead so the Delete action actually runs.
      // eslint-disable-next-line no-alert
      const ok = typeof window !== 'undefined' && window.confirm(`Are you sure you want to delete "${forum.name}"? This cannot be undone.`);
      if (ok) {
        await performDelete();
      }
      return;
    }
    
    Alert.alert(
      'Delete Forum',
      `Are you sure you want to delete "${forum.name}"? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: performDelete,
        },
      ]
    );
  };

  const toggleReflection = (id: string) => {
    setExpandedReflection(expandedReflection === id ? null : id);
  };

  const getPreviewText = (text: string, maxLength: number = 120) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
  };

  // Get first name for display
  const getFirstName = (fullName: string) => {
    return fullName.split(' ')[0];
  };

  // =============================================
  // Modal Handlers for Interactive Forum Pulse
  // =============================================
  
  // Open member profile modal and fetch full lens data
  const handleMemberPress = async (member: ForumPulseMemberCard) => {
    if (!user?.id) return;
    
    // Show modal immediately with basic data while loading full lens data
    setMemberModal({ visible: true, member, lensData: null, loading: true });
    
    try {
      const response = await getForumMemberLens(forumId, member.user_id, user.id);
      setMemberModal(prev => ({ 
        ...prev, 
        lensData: response.lens_data, 
        loading: false 
      }));
    } catch (error) {
      console.error('[Forum] Error fetching member lens data:', error);
      setMemberModal(prev => ({ ...prev, loading: false }));
    }
  };
  
  // Open domain reflections modal
  const handleThemePress = (domainId: string, domainName: string) => {
    const domainReflections = reflections.filter(r => r.selected_domain === domainId);
    setDomainModal({ 
      visible: true, 
      domainId, 
      domainName, 
      reflections: domainReflections 
    });
  };
  
  // Open type members modal
  const handleTypePress = (typeName: string) => {
    if (!pulse) return;
    const typeMembers = pulse.member_cards.filter(m => m.hd_type === typeName);
    setTypeModal({ visible: true, typeName, members: typeMembers });
  };
  
  // Open lens insight explanation modal
  const handleInsightPress = () => {
    if (!pulse?.lens_insight) return;
    setInsightModal({ visible: true, insight: pulse.lens_insight });
  };
  
  // Close all modals
  const closeAllModals = () => {
    setMemberModal({ visible: false, member: null, lensData: null, loading: false });
    setDomainModal({ visible: false, domainId: '', domainName: '', reflections: [] });
    setTypeModal({ visible: false, typeName: '', members: [] });
    setInsightModal({ visible: false, insight: '' });
  };

  // Open Forum Chat in member mode with a specific member selected
  const openForumChatWithMember = (member: ForumPulseMemberCard) => {
    closeAllModals();
    setForumChatInitialMode('member');
    setForumChatInitialMember(member);
    setShowForumChat(true);
  };

  // Open Forum Chat in default mode (self)
  const openForumChat = () => {
    setForumChatInitialMode('self');
    setForumChatInitialMember(null);
    setShowForumChat(true);
  };

  // Close Forum Chat and reset initial state
  const closeForumChat = () => {
    setShowForumChat(false);
    setForumChatInitialMode('self');
    setForumChatInitialMember(null);
  };
  
  // FIX 4: Handle forum pattern reveal
  const handleRevealGroupPattern = async () => {
    if (!user?.id) return;
    setForumPatternLoading(true);
    try {
      const response = await getPatternDiagnosis(user.id);
      setForumPattern(response);
      setShowForumPattern(true);
    } catch (err) {
      console.error('[Forum] Pattern load error:', err);
    } finally {
      setForumPatternLoading(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        {/* Escape button — always available so users are never stuck     */}
        {/* on the loading screen, even if the API hangs or auth context  */}
        {/* hasn't resolved yet on a deployed PWA / fresh tab.            */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => router.replace('/')}
            style={styles.backButton}
          >
            <Text style={[styles.backText, { color: theme.accent }]}>← Home</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Forum</Text>
          <View style={styles.backButton} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading forum...
          </Text>
          {/* Dev / preview only: show what step we're on while the
              spinner is still up. Production users do not see this. */}
          {__DEV__ && (
            <View style={styles.debugStrip}>
              <Text style={[styles.debugStripText, { color: theme.textTertiary }]}>
                [dev] step={loadStep}  forumId={forumId || '∅'}
              </Text>
              {lastApiUrl ? (
                <Text style={[styles.debugStripText, { color: theme.textTertiary }]}>
                  last={lastApiUrl}
                </Text>
              ) : null}
            </View>
          )}
          {/* Always-visible build marker — used to confirm a given
              client is running the latest bundle. Visible in production
              so we can ask users "do you see this?" in support. */}
          <Text style={[styles.forumBuildMarker, { color: theme.textTertiary }]}>
            build · {BUILD_ID}
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => router.replace('/')}
            style={styles.backButton}
          >
            <Text style={[styles.backText, { color: theme.accent }]}>← Home</Text>
          </TouchableOpacity>
          <Text style={[styles.headerTitle, { color: theme.text }]}>Forum</Text>
          <View style={styles.backButton} />
        </View>
        <View style={styles.errorContainer}>
          <Text style={[styles.errorTitle, { color: theme.text }]}>
            Forum is taking longer than expected.
          </Text>
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {error}
          </Text>

          {/* Primary recovery action: retry the load. */}
          <TouchableOpacity
            onPress={() => { setError(null); fetchData(); }}
            style={[styles.recoveryBtnPrimary, { borderColor: theme.accent }]}
            accessibilityLabel="Retry loading the forum"
          >
            <Text style={[styles.recoveryBtnPrimaryText, { color: theme.accent }]}>
              Retry
            </Text>
          </TouchableOpacity>

          {/* Web-only: explicit Safari/PWA cache nuke + reload. On
              native this is a no-op so we hide it. */}
          {Platform.OS === 'web' && (
            <TouchableOpacity
              onPress={handleClearCacheAndReload}
              style={styles.recoveryBtnSecondary}
              accessibilityLabel="Clear local cache and reload"
            >
              <Text style={[styles.recoveryBtnSecondaryText, { color: theme.textSecondary }]}>
                Clear local cache & reload
              </Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity
            onPress={() => router.replace('/forums')}
            style={styles.recoveryBtnSecondary}
            accessibilityLabel="Back to forums"
          >
            <Text style={[styles.recoveryBtnSecondaryText, { color: theme.textSecondary }]}>
              Back to Forums
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => router.replace('/')}
            style={styles.recoveryBtnSecondary}
            accessibilityLabel="Back to home"
          >
            <Text style={[styles.recoveryBtnSecondaryText, { color: theme.textSecondary }]}>
              Back to Home
            </Text>
          </TouchableOpacity>

          {/* Dev / preview only: rich diagnostic strip showing where
              we got stuck. Hidden in production builds. */}
          {__DEV__ && (
            <View style={styles.debugStrip}>
              <Text style={[styles.debugStripText, { color: theme.textTertiary }]}>
                [dev] step={loadStep}
              </Text>
              <Text style={[styles.debugStripText, { color: theme.textTertiary }]}>
                forumId={forumId || '∅'}  user={user?.email || user?.id || '∅'}
              </Text>
              {lastApiUrl ? (
                <Text style={[styles.debugStripText, { color: theme.textTertiary }]}>
                  last_api={lastApiUrl}
                </Text>
              ) : null}
              {lastErrorMsg ? (
                <Text style={[styles.debugStripText, { color: theme.textTertiary }]}>
                  last_err={lastErrorMsg}
                </Text>
              ) : null}
            </View>
          )}
          {/* Always-visible build marker on error screen too. */}
          <Text style={[styles.forumBuildMarker, { color: theme.textTertiary }]}>
            build · {BUILD_ID}
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Forums</Text>
        </TouchableOpacity>
        <View style={styles.headerRight}>
          <TouchableOpacity onPress={handleCopyInvite} style={styles.inviteButton}>
            <Text style={[styles.inviteButtonText, { color: theme.accent }]}>
              {copied ? '✓ Copied' : 'Invite'}
            </Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => router.replace('/(tabs)')} style={styles.homeButton} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Ionicons name="home-outline" size={22} color={theme.text} />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchData(true)}
            tintColor={theme.textSecondary}
          />
        }
      >
        {/* Story of This Circle — forum-topology-and-timing-v1 hero.
            Quiet, recognitional read of the room. Calls
            GET /api/forums/{id}/story-of-circle. */}
        {id && <StoryOfThisCircle forumId={String(id)} reloadKey={refreshing} />}

        {/* Talk to the room → forum-conversational-field-v1 CTA.
            Field-observer chat surface. Per-user history. */}
        {id && (
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={() => router.push(`/forums/${String(id)}/chat` as any)}
            style={[
              styles.talkToRoomCta,
              { backgroundColor: theme.surface, borderColor: theme.border },
            ]}
            accessibilityRole="button"
            accessibilityLabel="Talk to the room"
          >
            <View style={{ flex: 1 }}>
              <Text style={[styles.talkToRoomKicker, { color: theme.textTertiary }]}>
                With the room
              </Text>
              <Text style={[styles.talkToRoomLabel, { color: theme.text }]}>
                Talk to the room →
              </Text>
              <Text style={[styles.talkToRoomSub, { color: theme.textSecondary }]}>
                Field-level reflection. No diagnosis. No naming.
              </Text>
            </View>
          </TouchableOpacity>
        )}

        {/* Map your role → topology-editor-v2 CTA.
            Lets the member declare directional edges with other members. */}
        {id && (
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={() => router.push(`/forums/${String(id)}/topology` as any)}
            style={[
              styles.talkToRoomCta,
              { backgroundColor: theme.surface, borderColor: theme.border, marginTop: 8 },
            ]}
            accessibilityRole="button"
            accessibilityLabel="Map your role"
          >
            <View style={{ flex: 1 }}>
              <Text style={[styles.talkToRoomKicker, { color: theme.textTertiary }]}>
                Topology
              </Text>
              <Text style={[styles.talkToRoomLabel, { color: theme.text }]}>
                Map your role →
              </Text>
              <Text style={[styles.talkToRoomSub, { color: theme.textSecondary }]}>
                Quietly declare how you see your role with each person.
              </Text>
            </View>
          </TouchableOpacity>
        )}

        {/* Forum Info */}
        <View style={styles.forumInfo}>
          <Text style={[styles.forumName, { color: theme.text }]}>{forum?.name}</Text>
          {forum?.description && (
            <Text style={[styles.forumDescription, { color: theme.textSecondary }]}>
              {forum.description}
            </Text>
          )}
        </View>

        {/* Members Quick List */}
        <View style={[styles.membersSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.membersTitle, { color: theme.textTertiary }]}>
            {members.length} {members.length === 1 ? 'MEMBER' : 'MEMBERS'}
          </Text>
          <View style={styles.membersList}>
            {members.slice(0, 8).map((member) => {
              const isSelected = selectedMemberId === member.user_id;
              return (
                <TouchableOpacity
                  key={member.user_id}
                  onPress={() => handleSelectMember(member.user_id)}
                  activeOpacity={0.7}
                  style={[
                    styles.memberItem,
                    styles.memberItemTappable,
                    isSelected && {
                      backgroundColor: theme.accent + '15',
                      borderColor: theme.accent,
                    },
                    !isSelected && { borderColor: theme.border },
                  ]}
                >
                  <View style={[styles.memberAvatar, { backgroundColor: theme.accent + '20' }]}>
                    <Text style={[styles.memberInitial, { color: theme.accent }]}>
                      {member.user_name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <Text style={[styles.memberName, { color: theme.text }]}>
                    {getFirstName(member.user_name)}
                    {member.role === 'owner' && (
                      <Text style={[styles.memberRole, { color: theme.textTertiary }]}> • host</Text>
                    )}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Interactive Member Summary Card — inline, below the row */}
          {selectedMemberId ? (
            <View style={[styles.summaryCard, { borderColor: theme.border, backgroundColor: theme.background }]}>
              {memberSummaryLoading === selectedMemberId && !memberSummaries[selectedMemberId] ? (
                <View style={styles.summaryLoading}>
                  <ActivityIndicator size="small" color={theme.textTertiary} />
                  <Text style={[styles.summaryLoadingText, { color: theme.textTertiary }]}>
                    Loading summary…
                  </Text>
                </View>
              ) : memberSummaries[selectedMemberId] ? (
                (() => {
                  const s = memberSummaries[selectedMemberId];
                  const Row = ({ label, value }: { label: string; value: string | null }) =>
                    value ? (
                      <View style={styles.summaryRow}>
                        <Text style={[styles.summaryRowLabel, { color: theme.textTertiary }]}>{label}</Text>
                        <Text style={[styles.summaryRowValue, { color: theme.text }]}>{value}</Text>
                      </View>
                    ) : null;
                  return (
                    <View>
                      <View style={styles.summaryHeaderRow}>
                        <Text style={[styles.summaryName, { color: theme.text }]}>
                          {s.name}{s.is_host ? <Text style={[styles.memberRole, { color: theme.textTertiary }]}>  •  host</Text> : null}
                        </Text>
                        <TouchableOpacity
                          onPress={() => setSelectedMemberId(null)}
                          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                        >
                          <Ionicons name="close" size={18} color={theme.textTertiary} />
                        </TouchableOpacity>
                      </View>
                      <Row label="Astrology"    value={s.astrology} />
                      <Row label="Human Design" value={s.human_design} />
                      <Row label="BaZi"         value={s.bazi} />
                      <Row label="Enneagram"    value={s.enneagram} />
                      <Row label="Numerology"   value={s.numerology} />
                      {s.how_they_read ? (
                        <View style={[styles.summaryHowBlock, { borderTopColor: theme.border }]}>
                          <Text style={[styles.summaryHowLabel, { color: theme.textTertiary }]}>
                            How they read in the room
                          </Text>
                          <Text style={[styles.summaryHowText, { color: theme.text }]}>
                            {s.how_they_read}
                          </Text>
                        </View>
                      ) : null}
                    </View>
                  );
                })()
              ) : (
                <Text style={[styles.summaryLoadingText, { color: theme.textTertiary }]}>
                  No summary available for this member yet.
                </Text>
              )}
            </View>
          ) : null}
        </View>

        {/* ============================================
        {/* ============================================
            LIVE FIELD V1 (Feb 2026 brief) — clean field-state card.
            Reads only from member V5 sky-state; never names individuals.
            Renders nothing when forum has <3 active members.
            Mounted ABOVE the legacy "Story of This Circle" so users
            see the new V1 read first.
            ============================================ */}
        {forumId && user?.id ? (
          <View style={{ marginBottom: 16 }}>
            <LiveFieldCard
              forumId={forumId}
              userId={user.id}
              theme={theme}
            />
          </View>
        ) : null}

        {/* ============================================
            FORUM STORY HERO — "The Story of This Circle"
            The room's lived truth in 3-5 lines. No labels, no system talk.
            Tap to reveal the behavioural expansion bullets.
            ============================================ */}
        {liveField && (
          <View style={[styles.heroCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.heroTitle, { color: theme.text }]}>
              The Story of This Circle
            </Text>
            <Text style={[styles.heroBody, { color: theme.text }]}>
              {liveField.field_reading}
            </Text>
            {liveField.what_hasnt_landed ? (
              <Text style={[styles.heroBody, { color: theme.text, marginTop: 8 }]}>
                {liveField.what_hasnt_landed}
              </Text>
            ) : null}

            <TouchableOpacity
              style={styles.heroExpansionToggle}
              onPress={() => setStoryExpansionOpen((v) => !v)}
              activeOpacity={0.7}
            >
              <Text style={[styles.heroExpansionText, { color: theme.accent }]}>
                {storyExpansionOpen ? 'Hide' : 'See how this plays out →'}
              </Text>
            </TouchableOpacity>

            {storyExpansionOpen ? (
              <View style={styles.heroExpansionBody}>
                <Text style={[styles.heroExpansionHeader, { color: theme.textTertiary }]}>
                  How this tends to play out:
                </Text>
                {storyBullets.length === 0 ? (
                  <ActivityIndicator size="small" color={theme.textTertiary} />
                ) : (
                  storyBullets.map((b, i) => (
                    <View key={i} style={styles.heroBulletRow}>
                      <Text style={[styles.heroBullet, { color: theme.textTertiary }]}>•</Text>
                      <Text style={[styles.heroBulletText, { color: theme.textSecondary }]}>{b}</Text>
                    </View>
                  ))
                )}
              </View>
            ) : null}
          </View>
        )}

        {/* ============================================
            YOUR POSITION — personal recognition, 2-3 lines
            ============================================ */}
        {liveField?.your_position ? (
          <View style={[styles.positionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.positionLabel, { color: theme.textTertiary }]}>
              Where you are in this
            </Text>
            <Text style={[styles.positionBody, { color: theme.text }]}>
              {liveField.your_position}
            </Text>
          </View>
        ) : null}

        {/* ============================================
            WHAT EACH PERSON BRINGS — compact per-member contribution cards
            Scannable: name + 2-3 uppercase chips + one-line primary label.
            Renders inline, NOT behind a "View" button.

            STABLE RENDER CONTRACT (May 2026 hotfix):
            This card MUST always render once we have any forum data. If
            contributions are still loading or temporarily empty, fall
            back to a member-based placeholder so the section never
            silently disappears between renders (the bug users reported
            on Safari).
            ============================================ */}
        {contributions && contributions.length > 0 ? (
          <View style={[styles.contributionsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.contributionsTitle, { color: theme.text }]}>
              What Each Person Brings
            </Text>
            <Text style={[styles.contributionsSubtitle, { color: theme.textSecondary }]}>
              The strengths and forces each person naturally brings into this room.
            </Text>

            {contributions.map((c, idx) => {
              const superpower = c.superpower || (c.items?.[0]?.title ?? '');
              const lines =
                c.lines && c.lines.length > 0
                  ? c.lines
                  : c.items && c.items.length > 0
                    ? c.items.map((it) => it.description)
                    : c.primary_label
                      ? [c.primary_label]
                      : [];

              return (
                <View
                  key={c.member_id}
                  style={[
                    styles.contributionRow,
                    idx === contributions.length - 1 ? styles.contributionRowLast : null,
                    { borderBottomColor: theme.border },
                  ]}
                >
                  {/* Single-row heading: "Name — Superpower   host" */}
                  <View style={styles.contributionHeader}>
                    <Text style={[styles.contributionHeadline, { color: theme.text }]}>
                      <Text style={styles.contributionName}>{c.name}</Text>
                      {superpower ? (
                        <Text style={{ color: theme.textSecondary }}> — </Text>
                      ) : null}
                      {superpower ? (
                        <Text style={styles.contributionSuper}>{superpower}</Text>
                      ) : null}
                    </Text>
                    {c.is_host ? (
                      <Text style={[styles.contributionHostBadge, { color: theme.textTertiary }]}>
                        host
                      </Text>
                    ) : null}
                  </View>

                  {lines.map((line, i) => (
                    <Text
                      key={`${c.member_id}-line-${i}`}
                      style={[
                        i === 0 ? styles.superpowerLinePrimary : styles.superpowerLineSupport,
                        { color: i === 0 ? theme.text : theme.textSecondary },
                      ]}
                    >
                      {line}
                    </Text>
                  ))}
                </View>
              );
            })}
          </View>
        ) : members && members.length > 0 ? (
          // Graceful placeholder: contributions enrichment is still
          // streaming in. Show the member roster as a stable shell so
          // the "What Each Person Brings" card never disappears between
          // renders — even if the contributions API briefly errors.
          <View style={[styles.contributionsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.contributionsTitle, { color: theme.text }]}>
              What Each Person Brings
            </Text>
            <Text style={[styles.contributionsSubtitle, { color: theme.textSecondary }]}>
              {contributions === null
                ? 'Reading what each person brings into this room…'
                : 'Each person\'s strengths will appear here once they\'re ready.'}
            </Text>
            {members.map((m: any, idx: number) => (
              <View
                key={m.user_id || m.id || `member-placeholder-${idx}`}
                style={[
                  styles.contributionRow,
                  idx === members.length - 1 ? styles.contributionRowLast : null,
                  { borderBottomColor: theme.border },
                ]}
              >
                <View style={styles.contributionHeader}>
                  <Text style={[styles.contributionHeadline, { color: theme.text }]}>
                    <Text style={styles.contributionName}>{m.name || m.display_name || 'Member'}</Text>
                  </Text>
                </View>
                <Text
                  style={[
                    styles.superpowerLineSupport,
                    { color: theme.textTertiary, fontStyle: 'italic' },
                  ]}
                >
                  {contributions === null ? 'Loading…' : 'Insights coming soon'}
                </Text>
              </View>
            ))}
          </View>
        ) : null}

        {/* ============================================
            SHARE FORUM UPDATE — primary CTA (Pattern Running Me V2)
            ============================================ */}
        <TouchableOpacity
          style={[styles.shareUpdateBtn, { backgroundColor: theme.accent }]}
          onPress={() =>
            router.push({
              pathname: '/forums/updates',
              params: { forumId, forumName: forum?.name },
            })
          }
          activeOpacity={0.85}
        >
          <Text style={styles.shareUpdateBtnText}>Share Forum Update</Text>
        </TouchableOpacity>

        {/* ============================================
            ASK MIRROR — secondary CTA
            ============================================ */}
        <TouchableOpacity
          style={[styles.askMirrorSection, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}
          onPress={openForumChat}
          activeOpacity={0.7}
        >
          <View style={styles.askMirrorContent}>
            <View style={[styles.askMirrorIcon, { backgroundColor: theme.accent + '20' }]}>
              <Text style={{ fontSize: 20 }}>✨</Text>
            </View>
            <View style={styles.askMirrorTextContainer}>
              <Text style={[styles.askMirrorTitle, { color: theme.text }]}>Ask Mirror</Text>
              <Text style={[styles.askMirrorSubtitle, { color: theme.textSecondary }]}>
                Explore yourself, members, or forum dynamics
              </Text>
            </View>
          </View>
          <Text style={[styles.askMirrorArrow, { color: theme.accent }]}>→</Text>
        </TouchableOpacity>

        {/* ============================================
            HOW THEY MAP TO ME — kept as primary exploration CTA
            ============================================ */}
        <TouchableOpacity
          style={[styles.forumDynamicsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={() => router.push({ pathname: '/forums/mappings', params: { forumId, forumName: forum?.name } })}
          activeOpacity={0.7}
        >
          <View style={styles.forumDynamicsContent}>
            <View style={[styles.forumDynamicsIcon, { backgroundColor: theme.accent + '15' }]}>
              <Text style={{ fontSize: 20 }}>🔗</Text>
            </View>
            <View style={styles.forumDynamicsTextContainer}>
              <Text style={[styles.forumDynamicsTitle, { color: theme.text }]}>How they map to me</Text>
              <Text style={[styles.forumDynamicsSubtitle, { color: theme.textSecondary }]}>
                See how each member energetically connects with you
              </Text>
            </View>
          </View>
          <TouchableOpacity
            style={[styles.forumDynamicsButton, { backgroundColor: theme.accent + '15' }]}
            onPress={() => router.push({ pathname: '/forums/mappings', params: { forumId, forumName: forum?.name } })}
          >
            <Text style={[styles.forumDynamicsButtonText, { color: theme.accent }]}>View</Text>
          </TouchableOpacity>
        </TouchableOpacity>

        {/* ============================================
            ANALYTICS — collapsed by default, below everything
            ============================================ */}
        <TouchableOpacity
          style={[styles.analyticsToggle, { backgroundColor: theme.surface, borderWidth: 1, borderColor: theme.border }]}
          onPress={() => setAnalyticsExpanded((v) => !v)}
          activeOpacity={0.7}
        >
          <Text style={[styles.analyticsToggleText, { color: theme.textSecondary }]}>
            {analyticsExpanded ? 'HIDE FORUM ANALYTICS ▴' : 'VIEW FORUM ANALYTICS ▾'}
          </Text>
        </TouchableOpacity>

        {analyticsExpanded ? (
          <>
            {/* Forum Dynamics shortcut */}
            <TouchableOpacity
              style={[styles.forumDynamicsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              onPress={() => router.push({ pathname: '/forums/dynamics', params: { forumId } })}
              activeOpacity={0.7}
            >
              <View style={styles.forumDynamicsContent}>
                <View style={[styles.forumDynamicsIcon, { backgroundColor: theme.accent + '15' }]}>
                  <Text style={{ fontSize: 20 }}>🔮</Text>
                </View>
                <View style={styles.forumDynamicsTextContainer}>
                  <Text style={[styles.forumDynamicsTitle, { color: theme.text }]}>Forum Dynamics</Text>
                  <Text style={[styles.forumDynamicsSubtitle, { color: theme.textSecondary }]}>
                    Energy mix, authority, enneagram diversity, element balance
                  </Text>
                </View>
              </View>
              <TouchableOpacity
                style={[styles.forumDynamicsButton, { backgroundColor: theme.accent + '15' }]}
                onPress={() => router.push({ pathname: '/forums/dynamics', params: { forumId } })}
              >
                <Text style={[styles.forumDynamicsButtonText, { color: theme.accent }]}>Explore</Text>
              </TouchableOpacity>
            </TouchableOpacity>

        {/* ============================================
            FORUM PULSE - Collective Patterns & Lens Dynamics
            ============================================ */}
        {pulse && (
          <View style={[styles.pulseSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.pulseSectionTitle, { color: theme.text }]}>Forum Pulse</Text>
            
            {/* Exploring Themes */}
            {pulse.exploring_themes.length > 0 && (
              <View style={styles.pulseBlock}>
                <Text style={[styles.pulseBlockLabel, { color: theme.textTertiary }]}>EXPLORING THEMES</Text>
                <View style={styles.themeTags}>
                  {pulse.exploring_themes.map((theme_item, index) => (
                    <TouchableOpacity 
                      key={theme_item.domain_id} 
                      style={[styles.themeTag, { backgroundColor: theme.accent + '15', borderColor: theme.accent + '30' }]}
                      onPress={() => handleThemePress(theme_item.domain_id, theme_item.domain_name)}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.themeTagText, { color: theme.accent }]}>
                        {theme_item.domain_name}
                      </Text>
                      <Text style={[styles.themeTagCount, { color: theme.textTertiary }]}>
                        {theme_item.count}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}
            
            {/* Activity Summary */}
            <View style={styles.pulseBlock}>
              <Text style={[styles.pulseBlockLabel, { color: theme.textTertiary }]}>ACTIVITY (7 DAYS)</Text>
              <View style={styles.activityStats}>
                <View style={styles.statItem}>
                  <Text style={[styles.statNumber, { color: theme.text }]}>
                    {pulse.activity_summary.reflections_7d}
                  </Text>
                  <Text style={[styles.statLabel, { color: theme.textTertiary }]}>reflections</Text>
                </View>
                <View style={[styles.statDivider, { backgroundColor: theme.border }]} />
                <View style={styles.statItem}>
                  <Text style={[styles.statNumber, { color: theme.text }]}>
                    {pulse.activity_summary.active_members_7d}
                  </Text>
                  <Text style={[styles.statLabel, { color: theme.textTertiary }]}>active</Text>
                </View>
                {pulse.activity_summary.most_active_domain && (
                  <>
                    <View style={[styles.statDivider, { backgroundColor: theme.border }]} />
                    <View style={[styles.statItem, { flex: 2 }]}>
                      <Text style={[styles.statNumber, { color: theme.accent, fontSize: 13 }]} numberOfLines={1}>
                        {pulse.activity_summary.most_active_domain}
                      </Text>
                      <Text style={[styles.statLabel, { color: theme.textTertiary }]}>most active</Text>
                    </View>
                  </>
                )}
              </View>
            </View>
            
            {/* Group Energy (HD Types) */}
            {Object.keys(pulse.group_energy).length > 0 && (
              <View style={styles.pulseBlock}>
                <Text style={[styles.pulseBlockLabel, { color: theme.textTertiary }]}>GROUP ENERGY</Text>
                <View style={styles.hdTypesGrid}>
                  {Object.entries(pulse.group_energy).map(([type, count]) => (
                    <TouchableOpacity 
                      key={type} 
                      style={styles.hdTypeItem}
                      onPress={() => handleTypePress(type)}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.hdTypeName, { color: theme.textSecondary }]}>{type}</Text>
                      <Text style={[styles.hdTypeCount, { color: theme.text }]}>{count}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            )}
            
            {/* Lens Insight */}
            {pulse.lens_insight && (
              <TouchableOpacity 
                style={[styles.lensInsightBlock, { backgroundColor: theme.accent + '08', borderLeftColor: theme.accent }]}
                onPress={handleInsightPress}
                activeOpacity={0.8}
              >
                <Text style={[styles.lensInsightText, { color: theme.textSecondary }]}>
                  {pulse.lens_insight}
                </Text>
                <Text style={[styles.lensInsightHint, { color: theme.textTertiary }]}>Tap to learn more</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Member Lens Cards */}
        {pulse && pulse.member_cards.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>Members</Text>
            <View style={styles.memberCardsGrid}>
              {pulse.member_cards.map((member) => (
                <TouchableOpacity 
                  key={member.user_id}
                  style={[styles.memberLensCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                  onPress={() => handleMemberPress(member)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.memberLensName, { color: theme.text }]}>{member.name}</Text>
                  <View style={styles.memberLensDetails}>
                    {/* HD Type • Profile */}
                    {member.hd_type && (
                      <Text style={[styles.memberLensType, { color: theme.textSecondary }]}>
                        {member.hd_type}
                        {member.hd_profile && ` • ${member.hd_profile}`}
                      </Text>
                    )}
                    {/* Authority */}
                    {member.hd_authority && (
                      <Text style={[styles.memberLensAuthority, { color: theme.textTertiary }]}>
                        {member.hd_authority} Authority
                      </Text>
                    )}
                    {/* Enneagram core */}
                    {member.enneagram_type && (
                      <Text style={[styles.memberLensEnneagram, { color: theme.textTertiary }]}>
                        Enneagram {member.enneagram_type}
                      </Text>
                    )}
                    {/* Active Pattern Domain */}
                    {member.active_pattern && (
                      <Text style={[styles.memberLensActive, { color: theme.accent }]}>
                        Active: {member.active_pattern}
                      </Text>
                    )}
                    {!member.hd_type && !member.enneagram_type && (
                      <Text style={[styles.memberLensEmpty, { color: theme.textTertiary }]}>
                        Profile not set up yet
                      </Text>
                    )}
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}
        {/* END analytics collapsed block */}
          </>
        ) : null}

        {/* My Mirror Profile Card */}
        <TouchableOpacity
          style={[styles.mirrorProfileCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
          onPress={handleMyMirrorProfile}
          activeOpacity={0.7}
        >
          <View style={styles.mirrorProfileContent}>
            <Text style={[styles.mirrorProfileIcon, { color: theme.accent }]}>◎</Text>
            <View style={styles.mirrorProfileText}>
              <Text style={[styles.mirrorProfileTitle, { color: theme.text }]}>My Mirror Profile</Text>
              <Text style={[styles.mirrorProfileSubtitle, { color: theme.textTertiary }]}>
                Access your lenses and insights
              </Text>
            </View>
          </View>
          <Text style={[styles.mirrorProfileChevron, { color: theme.textTertiary }]}>›</Text>
        </TouchableOpacity>

        {/* Current Exercise Card */}
        {forum?.active_exercise && (
          <View style={[styles.exerciseCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <View style={styles.exerciseHeader}>
              <Text style={[styles.exerciseLabel, { color: theme.textTertiary }]}>CURRENT EXERCISE</Text>
            </View>
            <Text style={[styles.exerciseTitle, { color: theme.text }]}>
              {forum.active_exercise.title}
            </Text>
            <Text style={[styles.exerciseDescription, { color: theme.textSecondary }]}>
              {forum.active_exercise.description}
            </Text>
            
            <TouchableOpacity
              style={[styles.beginButton, { backgroundColor: theme.buttonPrimaryBg }]}
              onPress={handleBeginReflection}
            >
              <Text style={[styles.beginButtonText, { color: theme.buttonPrimaryText }]}>
                {hasSubmitted ? 'Edit Update' : 'Share Forum Update'}
              </Text>
            </TouchableOpacity>
            
            {hasSubmitted && (
              <Text style={[styles.submittedNote, { color: theme.success }]}>
                ✓ You&apos;ve shared an update
              </Text>
            )}
          </View>
        )}

        {/* Shared Reflections */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Shared Reflections</Text>
          
          {reflections.length === 0 ? (
            <View style={[styles.emptyReflections, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={styles.emptyIcon}>✎</Text>
              <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
                No reflections shared yet.
              </Text>
              <Text style={[styles.emptySubtext, { color: theme.textTertiary }]}>
                Be the first to share your reflection with the group.
              </Text>
            </View>
          ) : (
            <View style={styles.reflectionsList}>
              {reflections.map((reflection) => {
                const isExpanded = expandedReflection === reflection.id;
                return (
                  <TouchableOpacity
                    key={reflection.id}
                    style={[styles.reflectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                    onPress={() => toggleReflection(reflection.id)}
                    activeOpacity={0.8}
                  >
                    <View style={styles.reflectionHeader}>
                      <Text style={[styles.reflectionAuthor, { color: theme.text }]}>
                        {getFirstName(reflection.user_name)}
                      </Text>
                      <Text style={[styles.reflectionDomain, { color: theme.accent }]}>
                        {reflection.domain_name}
                      </Text>
                    </View>
                    <Text style={[styles.reflectionText, { color: theme.textSecondary }]}>
                      {isExpanded ? reflection.reflection_text : getPreviewText(reflection.reflection_text)}
                    </Text>
                    {reflection.reflection_text.length > 120 && (
                      <Text style={[styles.expandHint, { color: theme.textTertiary }]}>
                        {isExpanded ? 'Tap to collapse' : 'Tap to read more'}
                      </Text>
                    )}
                  </TouchableOpacity>
                );
              })}
            </View>
          )}
        </View>

        {/* Delete Forum — only visible to creator */}
        {forum && user?.id && forum.created_by === user.id && (
          <TouchableOpacity 
            onPress={handleDeleteForum} 
            style={[styles.deleteForumButton, { borderColor: '#CF6679' }]}
            activeOpacity={0.7}
          >
            <Ionicons name="trash-outline" size={16} color="#CF6679" />
            <Text style={styles.deleteForumText}>Delete Forum</Text>
          </TouchableOpacity>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>

      {/* ============================================
          MODALS - Interactive Forum Pulse Components
          ============================================ */}
      
      {/* Member Lens Profile Modal - REDESIGNED for human understanding */}
      <Modal
        visible={memberModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, styles.modalLarge, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}></Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            {memberModal.member && (
              <ScrollView style={styles.modalScrollContent} showsVerticalScrollIndicator={false}>
                {/* 1. HEADER - Name + Archetype */}
                <View style={styles.humanProfileHeader}>
                  <View style={[styles.humanProfileAvatar, { backgroundColor: theme.accent + '15' }]}>
                    <Text style={[styles.humanProfileInitial, { color: theme.accent }]}>
                      {memberModal.member.name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <Text style={[styles.humanProfileName, { color: theme.text }]}>
                    {memberModal.member.name}
                  </Text>
                  {memberModal.lensData && (
                    <Text style={[styles.humanProfileArchetype, { color: theme.textSecondary }]}>
                      {getArchetypeLabel(memberModal.lensData)}
                    </Text>
                  )}
                </View>
                
                {memberModal.loading ? (
                  <View style={styles.lensLoadingContainer}>
                    <ActivityIndicator size="small" color={theme.accent} />
                    <Text style={[styles.lensLoadingText, { color: theme.textTertiary }]}>Understanding this person...</Text>
                  </View>
                ) : memberModal.lensData ? (
                  <View style={styles.humanProfileContent}>
                    
                    {/* 2. WHAT IT FEELS LIKE TO BE WITH THEM - NEW TOP PRIORITY */}
                    <View style={[styles.humanSectionFelt, { backgroundColor: theme.accent + '06', borderColor: theme.accent + '20' }]}>
                      <Text style={[styles.humanSectionTitleFelt, { color: theme.accent }]}>What it feels like to be with them</Text>
                      <Text style={[styles.humanSectionTextFelt, { color: theme.text }]}>
                        {getWhatItFeelsLike(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 3. HOW THEY SHOW UP - Shortened */}
                    <View style={[styles.humanSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
                      <Text style={[styles.humanSectionTitle, { color: theme.text }]}>How they show up</Text>
                      <Text style={[styles.humanSectionText, { color: theme.textSecondary }]}>
                        {getHowTheyShowUp(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 4. WHEN THEY'RE AT THEIR BEST */}
                    <View style={[styles.humanSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
                      <Text style={[styles.humanSectionTitle, { color: theme.text }]}>When they're at their best</Text>
                      <Text style={[styles.humanSectionText, { color: theme.textSecondary }]}>
                        {getAtTheirBest(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 5. WHEN THINGS GET TENSE - Renamed, situational */}
                    <View style={[styles.humanSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
                      <Text style={[styles.humanSectionTitle, { color: theme.text }]}>When things get tense</Text>
                      <Text style={[styles.humanSectionText, { color: theme.textSecondary }]}>
                        {getWhenThingsGetTense(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 6. WHERE MISUNDERSTANDINGS HAPPEN - NEW CRITICAL */}
                    <View style={[styles.humanSectionWarning, { backgroundColor: '#FF572208', borderColor: '#FF572225' }]}>
                      <Text style={[styles.humanSectionTitleWarning, { color: '#FF5722' }]}>⚠️ Where misunderstandings happen</Text>
                      <Text style={[styles.humanSectionText, { color: theme.text }]}>
                        {getWhereMisunderstandingsHappen(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 7. HOW TO WORK WITH THEM - Sharpened */}
                    <View style={[styles.humanSectionHighlight, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '25' }]}>
                      <Text style={[styles.humanSectionTitleHighlight, { color: theme.accent }]}>How to work with them</Text>
                      <Text style={[styles.humanSectionTextLines, { color: theme.text }]}>
                        {getHowToWorkWith(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 8. MICRO-TRIGGER - NEW Real-time awareness */}
                    <View style={[styles.microTriggerBox, { backgroundColor: theme.surface, borderColor: theme.border }]}>
                      <Text style={[styles.microTriggerLabel, { color: theme.textTertiary }]}>👁 Watch for this moment:</Text>
                      <Text style={[styles.microTriggerText, { color: theme.text }]}>
                        {getMicroTrigger(memberModal.lensData)}
                      </Text>
                    </View>
                    
                    {/* 9. PATTERN SIGNALS - Collapsible */}
                    <TouchableOpacity 
                      style={[styles.patternSignalsToggle, { borderColor: theme.border }]}
                      onPress={() => setShowPatternSignals(!showPatternSignals)}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.patternSignalsToggleText, { color: theme.textTertiary }]}>
                        Underlying patterns (optional)
                      </Text>
                      <Text style={[styles.patternSignalsChevron, { color: theme.textTertiary }]}>
                        {showPatternSignals ? '▼' : '▶'}
                      </Text>
                    </TouchableOpacity>
                    
                    {showPatternSignals && (
                      <View style={[styles.patternSignalsContent, { backgroundColor: theme.background }]}>
                        <View style={styles.patternSignalsTags}>
                          {memberModal.lensData.human_design.type && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                {memberModal.lensData.human_design.type}
                              </Text>
                            </View>
                          )}
                          {memberModal.lensData.human_design.authority && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                {memberModal.lensData.human_design.authority} Authority
                              </Text>
                            </View>
                          )}
                          {memberModal.lensData.enneagram.core_type && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                Type {memberModal.lensData.enneagram.core_type}
                                {memberModal.lensData.enneagram.wing ? `w${memberModal.lensData.enneagram.wing}` : ''}
                              </Text>
                            </View>
                          )}
                          {memberModal.lensData.astrology.dominant_element && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                {memberModal.lensData.astrology.dominant_element} dominant
                              </Text>
                            </View>
                          )}
                          {memberModal.lensData.human_design.profile && (
                            <View style={[styles.patternTag, { backgroundColor: theme.border }]}>
                              <Text style={[styles.patternTagText, { color: theme.textSecondary }]}>
                                {memberModal.lensData.human_design.profile} Profile
                              </Text>
                            </View>
                          )}
                        </View>
                      </View>
                    )}
                    
                    {/* Ask Mirror Button */}
                    <TouchableOpacity
                      style={[styles.askMirrorButton, { backgroundColor: theme.accent + '15', borderColor: theme.accent + '40' }]}
                      activeOpacity={0.7}
                      onPress={() => {
                        if (memberModal.member) {
                          openForumChatWithMember(memberModal.member);
                        }
                      }}
                    >
                      <Text style={[styles.askMirrorButtonText, { color: theme.accent }]}>
                        Ask Mirror About {memberModal.member.name}
                      </Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  // Fallback when no lens data
                  <View style={styles.humanProfileContent}>
                    <View style={[styles.humanSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
                      <Text style={[styles.humanSectionText, { color: theme.textSecondary }]}>
                        Lens data not available for this member yet.
                      </Text>
                    </View>
                  </View>
                )}
              </ScrollView>
            )}
          </Pressable>
        </Pressable>
      </Modal>

      {/* Domain Reflections Modal */}
      <Modal
        visible={domainModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, styles.modalLarge, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>{domainModal.domainName}</Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            <Text style={[styles.modalSubtitle, { color: theme.textTertiary }]}>
              {domainModal.reflections.length} reflection{domainModal.reflections.length !== 1 ? 's' : ''} shared
            </Text>
            
            <ScrollView style={styles.modalScrollContent} showsVerticalScrollIndicator={false}>
              {domainModal.reflections.length === 0 ? (
                <Text style={[styles.emptyText, { color: theme.textTertiary }]}>
                  No reflections shared in this domain yet.
                </Text>
              ) : (
                domainModal.reflections.map((reflection) => (
                  <View key={reflection.id} style={[styles.modalReflectionCard, { borderBottomColor: theme.border }]}>
                    <Text style={[styles.modalReflectionAuthor, { color: theme.text }]}>
                      {reflection.user_name}
                    </Text>
                    <Text style={[styles.modalReflectionText, { color: theme.textSecondary }]}>
                      {reflection.reflection_text}
                    </Text>
                  </View>
                ))
              )}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Type Members Modal */}
      <Modal
        visible={typeModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>{typeModal.typeName}s</Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            <Text style={[styles.modalSubtitle, { color: theme.textTertiary }]}>
              {typeModal.members.length} member{typeModal.members.length !== 1 ? 's' : ''} with this type
            </Text>
            
            <View style={styles.typeMembersList}>
              {typeModal.members.map((member) => (
                <View key={member.user_id} style={[styles.typeMemberItem, { borderBottomColor: theme.border }]}>
                  <View style={[styles.typeMemberAvatar, { backgroundColor: theme.accent + '20' }]}>
                    <Text style={[styles.typeMemberInitial, { color: theme.accent }]}>
                      {member.name.charAt(0).toUpperCase()}
                    </Text>
                  </View>
                  <View style={styles.typeMemberInfo}>
                    <Text style={[styles.typeMemberName, { color: theme.text }]}>{member.name}</Text>
                    {member.hd_profile && (
                      <Text style={[styles.typeMemberProfile, { color: theme.textTertiary }]}>
                        Profile {member.hd_profile}
                      </Text>
                    )}
                  </View>
                </View>
              ))}
            </View>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Lens Insight Modal */}
      <Modal
        visible={insightModal.visible}
        transparent
        animationType="fade"
        onRequestClose={closeAllModals}
      >
        <Pressable style={styles.modalOverlay} onPress={closeAllModals}>
          <Pressable style={[styles.modalContent, { backgroundColor: theme.surface }]} onPress={() => {}}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>Lens Insight</Text>
              <TouchableOpacity onPress={closeAllModals} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
                <Text style={[styles.modalClose, { color: theme.textTertiary }]}>✕</Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.insightContent}>
              <Text style={[styles.insightMainText, { color: theme.text }]}>
                {insightModal.insight}
              </Text>
              
              <View style={[styles.insightNote, { backgroundColor: theme.accent + '08' }]}>
                <Text style={[styles.insightNoteText, { color: theme.textSecondary }]}>
                  This insight is generated based on the lens data shared by forum members. 
                  It reflects tendencies that may be present in the group, not predictions or prescriptions.
                </Text>
              </View>
              
              <Text style={[styles.insightDisclaimer, { color: theme.textTertiary }]}>
                Human Design describes energy patterns. How these show up in practice varies for each person.
              </Text>
            </View>
          </Pressable>
        </Pressable>
      </Modal>

      {/* Forum Chat Full Screen Modal */}
      <Modal
        visible={showForumChat}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={closeForumChat}
      >
        <SafeAreaView style={{ flex: 1, backgroundColor: theme.background }} edges={['top']}>
          <ForumChatView
            forumId={forumId}
            members={pulse?.member_cards || []}
            onClose={closeForumChat}
            initialMode={forumChatInitialMode}
            initialMember={forumChatInitialMember}
          />
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  // ---- Talk to the room CTA (forum-conversational-field-v1) ----
  talkToRoomCta: {
    marginHorizontal: 16,
    marginTop: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 4,
  },
  talkToRoomKicker: {
    fontSize: 10,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    fontWeight: '600',
  },
  talkToRoomLabel: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: -0.1,
    marginTop: 2,
  },
  talkToRoomSub: {
    fontSize: 12.5,
    lineHeight: 18,
    marginTop: 2,
  },

  // ---- Forum V2 Hero + Position ----
  heroCard: {
    marginTop: 12,
    marginBottom: 12,
    padding: 16,
    borderRadius: 14,
    borderWidth: 1,
  },
  heroTitle: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 10,
    letterSpacing: 0.2,
  },
  heroBody: {
    fontSize: 15,
    lineHeight: 22,
  },
  heroExpansionToggle: {
    marginTop: 12,
    alignSelf: 'flex-start',
  },
  heroExpansionText: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  heroExpansionBody: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#00000022',
  },
  heroExpansionHeader: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.7,
    marginBottom: 6,
  },
  heroBulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginTop: 4,
    gap: 6,
  },
  heroBullet: {
    fontSize: 14,
    lineHeight: 20,
  },
  heroBulletText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  positionCard: {
    marginBottom: 12,
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
  },
  positionLabel: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    marginBottom: 6,
  },
  positionBody: {
    fontSize: 15,
    lineHeight: 22,
  },
  shareUpdateBtn: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 10,
  },
  shareUpdateBtnText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  analyticsToggle: {
    marginTop: 6,
    marginBottom: 6,
    padding: 10,
    borderRadius: 10,
    alignItems: 'center',
  },
  analyticsToggleText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  container: {
    flex: 1,
  },
  
  // FIX 4: Forum Pattern Entry Card styles
  forumPatternCard: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 16,
  },
  forumPatternTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
  },
  forumPatternSub: {
    fontSize: 16,
    marginBottom: 14,
  },
  forumPatternButton: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  forumPatternButtonText: {
    fontSize: 17,
    fontWeight: '600',
  },
  forumPatternResult: {
    gap: 10,
  },
  forumPatternResultTitle: {
    fontSize: 22,
    fontWeight: '600',
  },
  forumPatternResultText: {
    fontSize: 16,
    lineHeight: 30,
  },
  forumPatternResultWisdom: {
    fontSize: 16,
    fontStyle: 'italic',
    lineHeight: 32,
  },
  forumPatternRefreshBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignSelf: 'flex-start',
    marginTop: 8,
  },
  forumPatternRefreshText: {
    fontSize: 16,
    fontWeight: '500',
  },
  
  // FIX 6: Real Life Meaning styles
  realLifeMeaningBox: {
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    marginBottom: 16,
  },
  realLifeMeaningTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  realLifeMeaningContent: {
    gap: 6,
  },
  realLifeMeaningText: {
    fontSize: 16,
    lineHeight: 32,
  },
  
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  backButton: {
    minWidth: 80,
  },
  backText: {
    fontSize: 16,
    fontWeight: '500',
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '600',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  homeButton: {
    padding: 8,
  },
  deleteForumButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    marginHorizontal: 20,
    marginTop: 24,
    borderRadius: 10,
    borderWidth: 1,
  },
  deleteForumText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#CF6679',
  },
  inviteButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  inviteButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    opacity: 0.8,
  },
  retryText: {
    fontSize: 16,
    fontWeight: '500',
  },
  recoveryBtnPrimary: {
    paddingHorizontal: 28,
    paddingVertical: 12,
    borderRadius: 24,
    borderWidth: 1.5,
    marginBottom: 12,
    minWidth: 180,
    alignItems: 'center',
  },
  recoveryBtnPrimaryText: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  recoveryBtnSecondary: {
    paddingHorizontal: 18,
    paddingVertical: 10,
    marginTop: 4,
  },
  recoveryBtnSecondaryText: {
    fontSize: 14,
    fontWeight: '400',
    letterSpacing: 0.2,
  },
  debugStrip: {
    marginTop: 24,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    backgroundColor: 'rgba(127,127,127,0.06)',
    alignItems: 'center',
  },
  debugStripText: {
    fontSize: 10,
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
    lineHeight: 14,
  },
  forumBuildMarker: {
    fontSize: 10,
    letterSpacing: 0.4,
    opacity: 0.4,
    marginTop: 32,
    fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }),
    textAlign: 'center',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  forumInfo: {
    marginBottom: 16,
  },
  forumName: {
    fontSize: 26,
    fontWeight: '700',
    marginBottom: 4,
  },
  forumDescription: {
    fontSize: 17,
    lineHeight: 30,
  },
  // Members Quick List
  membersSection: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  membersTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 16,
  },
  membersList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  memberItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  memberItemTappable: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  memberAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  memberInitial: {
    fontSize: 16,
    fontWeight: '600',
  },
  memberName: {
    fontSize: 16,
    fontWeight: '500',
  },
  memberRole: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  // Interactive Member Summary Card — inline, below the members row
  summaryCard: {
    marginTop: 16,
    padding: 14,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  summaryLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  summaryLoadingText: {
    fontSize: 13,
  },
  summaryHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  summaryName: {
    fontSize: 16,
    fontWeight: '600',
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 4,
    gap: 10,
  },
  summaryRowLabel: {
    width: 104,
    fontSize: 11,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    fontWeight: '600',
    paddingTop: 2,
  },
  summaryRowValue: {
    flex: 1,
    fontSize: 14,
    lineHeight: 20,
  },
  summaryHowBlock: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  summaryHowLabel: {
    fontSize: 11,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    fontWeight: '600',
    marginBottom: 4,
  },
  summaryHowText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  // Ask Mirror Button
  askMirrorSection: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 20,
  },
  askMirrorContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  askMirrorIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  askMirrorTextContainer: {
    flex: 1,
  },
  askMirrorTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  askMirrorSubtitle: {
    fontSize: 16,
  },
  askMirrorArrow: {
    fontSize: 22,
    fontWeight: '600',
    paddingLeft: 8,
  },
  // ============================================
  // NARRATIVE FLOW STYLES - Continuous experience
  // ============================================
  narrativeFlow: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  narrativeSection: {
    paddingVertical: 16,
  },
  narrativeFieldHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  narrativeFieldEmoji: {
    fontSize: 24,
    marginRight: 10,
  },
  narrativeFieldTemp: {
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  narrativeFieldText: {
    fontSize: 17,
    lineHeight: 30,
    fontWeight: '400',
  },
  narrativeSubtext: {
    fontSize: 17,
    lineHeight: 30,
    marginTop: 12,
    fontStyle: 'italic',
  },
  narrativeDivider: {
    height: 1,
    marginVertical: 4,
  },
  narrativeSectionHint: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'lowercase',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  narrativePositionText: {
    fontSize: 16,
    lineHeight: 32,
    fontWeight: '400',
  },
  narrativeTrajectoryText: {
    fontSize: 17,
    lineHeight: 31,
    fontStyle: 'italic',
  },
  narrativeStoryText: {
    fontSize: 17,
    lineHeight: 31,
  },
  narrativeStoryLink: {
    fontSize: 16,
    fontWeight: '500',
    marginTop: 10,
  },
  narrativeMoveDivider: {
    height: 2,
    marginVertical: 8,
    borderRadius: 1,
  },
  narrativeMoveSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 14,
  },
  narrativeMoveHint: {
    fontSize: 16,
    marginRight: 10,
    marginTop: 2,
  },
  narrativeMoveText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 32,
    fontStyle: 'italic',
  },
  narrativeIdentityNote: {
    fontSize: 16,
    lineHeight: 32,
    marginTop: 12,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  // Live Field Card Styles - FIELD-FIRST design (legacy, keeping for backwards compat)
  liveFieldCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 16,
  },
  liveFieldHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  liveFieldTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  liveFieldTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  liveFieldBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  liveFieldBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  liveFieldReading: {
    fontSize: 17,
    lineHeight: 30,
    marginBottom: 16,
  },
  liveFieldSection: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 14,
  },
  liveFieldSectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  liveFieldSectionText: {
    fontSize: 16,
    lineHeight: 32,
  },
  liveFieldYourShift: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginTop: 4,
  },
  liveFieldYourShiftLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
  },
  liveFieldYourShiftText: {
    fontSize: 16,
    lineHeight: 32,
    fontStyle: 'italic',
  },
  liveFieldIdentityNote: {
    fontSize: 14,
    lineHeight: 31,
    marginTop: 10,
    fontStyle: 'italic',
  },
  // YOUR POSITION IN THE FIELD styles
  liveFieldPositionCard: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 14,
  },
  liveFieldPositionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  liveFieldPositionLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  liveFieldPositionText: {
    fontSize: 16,
    lineHeight: 32,
  },
  // TRAJECTORY (IF NOTHING CHANGES) styles
  liveFieldTrajectoryCard: {
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    marginBottom: 14,
  },
  liveFieldTrajectoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  liveFieldTrajectoryLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  liveFieldTrajectoryText: {
    fontSize: 16,
    lineHeight: 32,
    fontStyle: 'italic',
  },
  // THE MOVE - Subtle action opening styles
  liveFieldTheMoveCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderStyle: 'dashed',
    marginTop: 8,
    marginBottom: 4,
  },
  liveFieldTheMoveHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  liveFieldTheMoveLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  liveFieldTheMoveText: {
    fontSize: 17,
    lineHeight: 30,
    fontStyle: 'italic',
  },
  // Forum Story Card
  forumStoryCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  forumStoryContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 16,
  },
  forumStoryIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  forumStoryTextContainer: {
    flex: 1,
  },
  forumStoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  forumStorySubtitle: {
    fontSize: 16,
    lineHeight: 31,
  },
  forumStoryButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  forumStoryButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  // Forum Dynamics Card Styles
  forumDynamicsCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  forumDynamicsContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 16,
  },
  forumDynamicsIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  forumDynamicsTextContainer: {
    flex: 1,
  },
  forumDynamicsTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  forumDynamicsSubtitle: {
    fontSize: 16,
    lineHeight: 31,
  },
  forumDynamicsButton: {
    alignSelf: 'flex-start',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  forumDynamicsButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  // Forum Pulse Styles
  pulseSection: {
    padding: 20,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 20,
  },
  pulseSectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 16,
  },
  pulseBlock: {
    marginBottom: 16,
  },
  pulseBlockLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 14,
  },
  themeTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  themeTag: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    gap: 6,
  },
  themeTagText: {
    fontSize: 16,
    fontWeight: '500',
  },
  themeTagCount: {
    fontSize: 14,
    fontWeight: '600',
  },
  activityStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  statDivider: {
    width: 1,
    height: 32,
  },
  hdTypesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  hdTypeItem: {
    alignItems: 'center',
    minWidth: 60,
  },
  hdTypeName: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 2,
  },
  hdTypeCount: {
    fontSize: 16,
    fontWeight: '700',
  },
  lensInsightBlock: {
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    marginTop: 4,
  },
  lensInsightText: {
    fontSize: 16,
    lineHeight: 32,
    fontStyle: 'italic',
  },
  // Member Lens Cards
  memberCardsGrid: {
    gap: 12,
  },
  memberLensCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  memberLensName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 14,
  },
  memberLensDetails: {
    gap: 4,
  },
  memberLensType: {
    fontSize: 16,
    fontWeight: '500',
  },
  memberLensEnneagram: {
    fontSize: 16,
  },
  memberLensActive: {
    fontSize: 16,
    fontWeight: '500',
  },
  memberLensEmpty: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  memberLensAuthority: {
    fontSize: 14,
  },
  // Lens Data Loading
  lensLoadingContainer: {
    alignItems: 'center',
    paddingVertical: 32,
    gap: 12,
  },
  lensLoadingText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  // Lens Data Container
  lensDataContainer: {
    paddingTop: 8,
  },
  lensSection: {
    paddingVertical: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 8,
  },
  lensSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  lensRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingVertical: 6,
  },
  lensRowVertical: {
    paddingVertical: 8,
  },
  lensLabel: {
    fontSize: 16,
    flex: 1,
  },
  lensValue: {
    fontSize: 16,
    fontWeight: '500',
    flex: 1.5,
    textAlign: 'right',
  },
  lensValueSmall: {
    fontSize: 14,
    lineHeight: 31,
    marginTop: 4,
  },
  patternTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 8,
  },
  patternTag: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  patternTagText: {
    fontSize: 14,
    fontWeight: '500',
  },
  askMirrorButton: {
    marginTop: 20,
    marginBottom: 14,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  askMirrorButtonText: {
    fontSize: 17,
    fontWeight: '600',
  },
  askMirrorHint: {
    fontSize: 14,
    marginTop: 4,
    fontStyle: 'italic',
  },
  
  // =============================================================================
  // HUMAN UNDERSTANDING MEMBER PROFILE STYLES
  // =============================================================================
  humanProfileHeader: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  humanProfileAvatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  humanProfileInitial: {
    fontSize: 28,
    fontWeight: '600',
  },
  humanProfileName: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 4,
  },
  humanProfileArchetype: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  humanProfileContent: {
    paddingTop: 8,
  },
  
  // NEW: "What it feels like" - Top priority felt section
  humanSectionFelt: {
    borderRadius: 14,
    padding: 18,
    marginBottom: 14,
    borderWidth: 1,
  },
  humanSectionTitleFelt: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  humanSectionTextFelt: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
  },
  
  humanSection: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
  },
  humanSectionHighlight: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
  },
  humanSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 14,
    letterSpacing: 0.3,
  },
  humanSectionTitleHighlight: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 14,
    letterSpacing: 0.3,
  },
  humanSectionText: {
    fontSize: 17,
    lineHeight: 31,
  },
  patternSignalsToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
    marginTop: 8,
  },
  patternSignalsToggleText: {
    fontSize: 16,
  },
  patternSignalsChevron: {
    fontSize: 14,
  },
  patternSignalsContent: {
    paddingVertical: 12,
    paddingHorizontal: 4,
  },
  patternSignalsTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  
  // NEW: Warning section (Where misunderstandings happen)
  humanSectionWarning: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
  },
  humanSectionTitleWarning: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 14,
    letterSpacing: 0.3,
  },
  
  // NEW: Text with line breaks for "How to work with them"
  humanSectionTextLines: {
    fontSize: 17,
    lineHeight: 32,
  },
  
  // NEW: Micro-trigger box
  microTriggerBox: {
    borderRadius: 10,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderStyle: 'dashed',
  },
  microTriggerLabel: {
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 6,
  },
  microTriggerText: {
    fontSize: 16,
    lineHeight: 30,
    fontStyle: 'italic',
  },
  
  // My Mirror Profile Card
  mirrorProfileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
  },
  mirrorProfileContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  mirrorProfileIcon: {
    fontSize: 28,
    marginRight: 14,
  },
  mirrorProfileText: {
    flex: 1,
  },
  mirrorProfileTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  mirrorProfileSubtitle: {
    fontSize: 16,
  },
  mirrorProfileChevron: {
    fontSize: 24,
    marginLeft: 8,
  },
  // Exercise Card
  exerciseCard: {
    padding: 20,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 24,
  },
  exerciseHeader: {
    marginBottom: 16,
  },
  exerciseLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1,
  },
  exerciseTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 14,
  },
  exerciseDescription: {
    fontSize: 16,
    lineHeight: 30,
    marginBottom: 20,
  },
  beginButton: {
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  beginButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  submittedNote: {
    fontSize: 16,
    textAlign: 'center',
    marginTop: 12,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 16,
  },
  emptyReflections: {
    padding: 32,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: 16,
    opacity: 0.5,
  },
  emptyText: {
    fontSize: 17,
    textAlign: 'center',
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 16,
    textAlign: 'center',
  },
  reflectionsList: {
    gap: 12,
  },
  reflectionCard: {
    padding: 16,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
  },
  reflectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  reflectionAuthor: {
    fontSize: 17,
    fontWeight: '600',
  },
  reflectionDomain: {
    fontSize: 14,
    fontWeight: '500',
  },
  reflectionText: {
    fontSize: 16,
    lineHeight: 30,
  },
  expandHint: {
    fontSize: 14,
    marginTop: 8,
    fontStyle: 'italic',
  },
  
  // ============================================
  // Modal Styles
  // ============================================
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    maxWidth: 360,
    borderRadius: 20,
    padding: 20,
    maxHeight: '70%',
  },
  modalLarge: {
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '600',
  },
  modalClose: {
    fontSize: 24,
    fontWeight: '300',
    padding: 4,
  },
  modalSubtitle: {
    fontSize: 16,
    marginBottom: 16,
  },
  modalScrollContent: {
    maxHeight: 400,
  },
  
  // Member Profile Modal
  memberProfileContent: {
    alignItems: 'center',
    paddingTop: 8,
  },
  memberProfileAvatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  memberProfileInitial: {
    fontSize: 26,
    fontWeight: '600',
  },
  memberProfileName: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 20,
    textAlign: 'center',
  },
  memberProfileDetails: {
    width: '100%',
    gap: 12,
  },
  profileRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  profileLabel: {
    fontSize: 16,
  },
  profileValue: {
    fontSize: 17,
    fontWeight: '500',
  },
  profileEmpty: {
    fontSize: 16,
    textAlign: 'center',
    marginTop: 16,
    fontStyle: 'italic',
  },
  
  // Domain Reflections Modal
  modalReflectionCard: {
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  modalReflectionAuthor: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 6,
  },
  modalReflectionText: {
    fontSize: 16,
    lineHeight: 32,
  },
  
  // Type Members Modal
  typeMembersList: {
    gap: 4,
  },
  typeMemberItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  typeMemberAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  typeMemberInitial: {
    fontSize: 16,
    fontWeight: '600',
  },
  typeMemberInfo: {
    flex: 1,
  },
  typeMemberName: {
    fontSize: 17,
    fontWeight: '500',
  },
  typeMemberProfile: {
    fontSize: 16,
    marginTop: 2,
  },
  
  // Lens Insight Modal
  insightContent: {
    gap: 16,
  },
  insightMainText: {
    fontSize: 16,
    lineHeight: 32,
  },
  insightNote: {
    padding: 14,
    borderRadius: 12,
  },
  insightNoteText: {
    fontSize: 16,
    lineHeight: 32,
  },
  insightDisclaimer: {
    fontSize: 14,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // Lens Insight Hint
  lensInsightHint: {
    fontSize: 14,
    marginTop: 6,
    fontStyle: 'italic',
  },

  // ---------- What Each Person Brings ----------
  contributionsCard: {
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 16,
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 6,
    marginHorizontal: 16,
    marginTop: 12,
    marginBottom: 16,
  },
  contributionsTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 4,
  },
  contributionsSubtitle: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 14,
  },
  contributionRow: {
    paddingVertical: 18,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  contributionRowLast: {
    borderBottomWidth: 0,
    paddingBottom: 8,
  },
  contributionHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: 8,
    marginBottom: 10,
  },
  contributionName: {
    fontSize: 17,
    fontWeight: '600',
  },
  contributionHostBadge: {
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  contributionItem: {
    marginBottom: 12,
  },
  contributionItemTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 3,
  },
  contributionItemDesc: {
    fontSize: 14,
    lineHeight: 20,
  },
  // Legacy superpower styles (pre v3.1; kept for backward compat if any
  // older render path references them):
  superpowerTitle: {
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 6,
    letterSpacing: 0.2,
  },
  superpowerLine: {
    fontSize: 14,
    lineHeight: 21,
    marginBottom: 4,
  },
  // v3.1 compact single-row heading styles
  contributionHeadline: {
    fontSize: 16,
    fontWeight: '500',
    flexShrink: 1,
    flex: 1,
  },
  contributionSuper: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  superpowerLinePrimary: {
    fontSize: 14,
    lineHeight: 21,
    marginTop: 2,
  },
  superpowerLineSupport: {
    fontSize: 13,
    lineHeight: 19,
    marginTop: 3,
  },
  // Legacy (kept for any older consumer paths, no longer used by the main
  // forum page):
  contributionChips: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.4,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  contributionLabel: {
    fontSize: 14,
    lineHeight: 20,
  },
});
