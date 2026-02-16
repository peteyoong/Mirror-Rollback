import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { buildJournalPrefill, goToJournalWithPrefill } from '../utils/journalPrefill';
import { API_BASE_URL } from '../utils/apiBase';
import { 
  sendEnneagramChat, 
  getEnneagramTraits,
  askEnneagramQuestion,
  getEnneagramDeepDive,
  getEnneagramNarrative,
  EnneagramTraitCard,
  EnneagramComputedDetails,
  EnneagramDeepDiveSection,
  EnneagramDeepDiveResponse,
  EnneagramNarrativeResponse,
} from '../services/api';
import {
  BUILD_ID,
  BUILD_VERSION,
  getBackendHealth,
  BackendHealthInfo,
} from '../utils/buildInfo';

// ============================================
// DEBUG CONFIGURATION
// ============================================
// Server-side environment flag (must be 'true' to enable debug capability)
const DEBUG_MIRROR_ENV = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// Client-side URL param check (?debug=1)
const getUrlDebugParam = (): boolean => {
  if (typeof window === 'undefined') return false;
  return new URLSearchParams(window.location?.search || '').get('debug') === '1';
};

const APP_ENV = process.env.NODE_ENV || 'unknown';

// ============================================
// TYPE LABEL NORMALIZER (Task B - Fix "7wbalanced" bug)
// ============================================
// This function ensures wing labels are ALWAYS formatted correctly
// regardless of what the backend returns.
// Rules:
// - If wing is a number: "Type {core}w{wing}" (e.g., "Type 7w8")
// - If wing is "balanced": "Type {core} — balanced wings ({left} & {right})"
// - If wing is null/undefined: "Type {core}"
// - NEVER: "7wbalanced" or "Type 7wbalanced"
// ============================================
function normalizeTypeLabel(
  rawLabel: string | undefined,
  coreType: number,
  wing: number | 'balanced' | null | undefined
): string {
  const wings = WING_NUMBERS[coreType] || { left: coreType === 1 ? 9 : coreType - 1, right: coreType === 9 ? 1 : coreType + 1 };
  
  // DEFENSIVE: Check for malformed labels containing "wbalanced"
  if (rawLabel && rawLabel.toLowerCase().includes('wbalanced')) {
    console.warn('[WING_LABEL_BUG] Malformed label detected:', rawLabel);
    // Fix it by using local logic
    if (wing === 'balanced') {
      return `Type ${coreType} — balanced wings (${wings.left} & ${wings.right})`;
    }
    return `Type ${coreType}`;
  }
  
  // If rawLabel looks good, return it
  if (rawLabel && !rawLabel.includes('wbalanced')) {
    return rawLabel;
  }
  
  // Generate correct label from local data
  if (wing === null || wing === undefined) {
    return `Type ${coreType}`;
  }
  if (wing === 'balanced') {
    return `Type ${coreType} — balanced wings (${wings.left} & ${wings.right})`;
  }
  if (typeof wing === 'number') {
    return `Type ${coreType}w${wing}`;
  }
  
  return `Type ${coreType}`;
}

// ============================================
// DEBUG WING STATE OVERRIDE SYSTEM
// ============================================
// Purpose: Visual verification of P0 Wing UX Fix
// Active only when DEBUG_MIRROR_ENV === true
// UI-only, no backend, no persistence
// Zero impact on production logic
// ============================================

type DebugWingState = 'off' | 'dominant' | 'leaning' | 'balanced' | 'not_clear';

// Mock data generator for each wing state
const getDebugWingOverride = (
  coreType: number,
  selectedState: DebugWingState
): { mockWing: number | 'balanced' | null; mockConfidenceTier: string } | null => {
  if (selectedState === 'off') return null;
  
  // Use left wing as example for any core type
  const leftWing = coreType === 1 ? 9 : coreType - 1;
  
  switch (selectedState) {
    case 'dominant':
      return { mockWing: leftWing, mockConfidenceTier: 'high' };
    case 'leaning':
      return { mockWing: leftWing, mockConfidenceTier: 'medium' };
    case 'balanced':
      return { mockWing: 'balanced', mockConfidenceTier: 'low' };
    case 'not_clear':
      return { mockWing: null, mockConfidenceTier: 'low' };
    default:
      return null;
  }
};

// Debug state labels for UI
const DEBUG_WING_STATE_LABELS: Record<DebugWingState, string> = {
  off: 'OFF',
  dominant: 'Dominant',
  leaning: 'Leaning',
  balanced: 'Balanced',
  not_clear: 'Not Clear',
};

// ============================================
// TYPE DATA
// ============================================

const TYPE_NAMES: { [key: number]: string } = {
  1: 'The Perfectionist',
  2: 'The Helper',
  3: 'The Achiever',
  4: 'The Individualist',
  5: 'The Investigator',
  6: 'The Loyalist',
  7: 'The Enthusiast',
  8: 'The Challenger',
  9: 'The Peacemaker',
};

// Energetic Flow: Stress line descriptions (Mirror-safe)
const STRESS_DESCRIPTIONS: { [key: number]: { [key: number]: string } } = {
  1: { 4: "a pull toward feeling misunderstood, melancholic, or withdrawn." },
  2: { 8: "more assertive, confrontational, or demanding of recognition." },
  3: { 9: "checking out, numbing, or avoiding what feels overwhelming." },
  4: { 2: "over-giving, people-pleasing, or seeking validation through connection." },
  5: { 7: "scattered thinking, impulsive options, or escape into distraction." },
  6: { 3: "performing, image-managing, or proving worth through achievement." },
  7: { 1: "critical, perfectionistic, or rigidly focused on what's wrong." },
  8: { 5: "withdrawal, isolation, or guarding resources and energy." },
  9: { 6: "anxious, suspicious, or caught in worst-case thinking." },
};

// Energetic Flow: Growth line descriptions (Mirror-safe)
const GROWTH_DESCRIPTIONS: { [key: number]: { [key: number]: string } } = {
  1: { 7: "lightness, spontaneity, and permission to enjoy without judgment." },
  2: { 4: "self-awareness, emotional depth, and honoring your own needs." },
  3: { 6: "authenticity, loyalty, and connection beyond achievement." },
  4: { 1: "groundedness, discernment, and constructive action." },
  5: { 8: "embodiment, assertiveness, and direct engagement with the world." },
  6: { 9: "calm, trust, and acceptance of uncertainty." },
  7: { 5: "focus, depth, and comfort with stillness." },
  8: { 2: "tenderness, openness, and genuine care for others." },
  9: { 3: "purposeful action, self-assertion, and visible engagement." },
};

// Helper to get stress description text
const getStressDescription = (coreType: number, stressTo: number | string | undefined): string => {
  const stressNum = typeof stressTo === 'string' ? parseInt(stressTo, 10) : stressTo;
  if (!stressNum || !STRESS_DESCRIPTIONS[coreType]) return "patterns that may feel unfamiliar.";
  return STRESS_DESCRIPTIONS[coreType][stressNum] || "patterns that may feel unfamiliar.";
};

// Helper to get growth description text
const getGrowthDescription = (coreType: number, growthTo: number | string | undefined): string => {
  const growthNum = typeof growthTo === 'string' ? parseInt(growthTo, 10) : growthTo;
  if (!growthNum || !GROWTH_DESCRIPTIONS[coreType]) return "expanded capacity and resourcefulness.";
  return GROWTH_DESCRIPTIONS[coreType][growthNum] || "expanded capacity and resourcefulness.";
};

const CORE_MOTIVATIONS: { [key: number]: string } = {
  1: 'Driven by integrity and high standards — a desire to improve and do what is right.',
  2: 'Driven by connection through helping — a need to be needed and valued for giving.',
  3: 'Driven by value through achievement — a need to succeed and be seen as capable.',
  4: 'Driven by identity and meaning — a search for depth, authenticity, and significance.',
  5: 'Driven by competence and understanding — a need for knowledge, clarity, and inner resources.',
  6: 'Driven by security and trust — a need for certainty, support, and reliable foundations.',
  7: 'Driven by freedom and possibility — a need to stay stimulated, open, and unconfined.',
  8: 'Driven by autonomy and control — a need to be strong, independent, and uncontrolled.',
  9: 'Driven by peace and harmony — a desire for stability, comfort, and inner calm.',
};

// Wing numbers for each core type
const WING_NUMBERS: { [key: number]: { left: number; right: number } } = {
  1: { left: 9, right: 2 },
  2: { left: 1, right: 3 },
  3: { left: 2, right: 4 },
  4: { left: 3, right: 5 },
  5: { left: 4, right: 6 },
  6: { left: 5, right: 7 },
  7: { left: 6, right: 8 },
  8: { left: 7, right: 9 },
  9: { left: 8, right: 1 },
};

// Stress patterns per type
const STRESS_PATTERNS: { [key: number]: string } = {
  1: 'Under stress, you may become moody and emotionally volatile, feeling misunderstood (4-like behavior).',
  2: 'Under stress, you may become aggressive and controlling, demanding recognition (8-like behavior).',
  3: 'Under stress, you may disengage and become apathetic, avoiding failure (9-like behavior).',
  4: 'Under stress, you may become clingy and overly involved, seeking connection (2-like behavior).',
  5: 'Under stress, you may become scattered and impulsive, acting without thinking (7-like behavior).',
  6: 'Under stress, you may become competitive and arrogant, proving your worth (3-like behavior).',
  7: 'Under stress, you may become critical and perfectionistic, rigid and controlling (1-like behavior).',
  8: 'Under stress, you may become withdrawn and secretive, pulling away from connection (5-like behavior).',
  9: 'Under stress, you may become anxious and reactive, worrying about worst cases (6-like behavior).',
};

// Growth patterns per type
const GROWTH_PATTERNS: { [key: number]: string } = {
  1: 'When resourced, access spontaneity and joy (7-like): lightness, acceptance, playful engagement.',
  2: 'When resourced, access self-care and boundaries (4-like): honoring your own needs and feelings.',
  3: 'When resourced, access commitment and loyalty (6-like): depth over image, authentic connection.',
  4: 'When resourced, access objectivity and discipline (1-like): structure, principles, right action.',
  5: 'When resourced, access confident action (8-like): assertion, decisiveness, engaging the world.',
  6: 'When resourced, access inner peace and receptivity (9-like): trust, relaxation, groundedness.',
  7: 'When resourced, access focused depth (5-like): concentration, mastery, finishing what you start.',
  8: 'When resourced, access openheartedness (2-like): vulnerability, care, letting others in.',
  9: 'When resourced, access assertive energy (3-like): goals, action, making your mark.',
};

// Journal prompts per type
const JOURNAL_PROMPTS: { [key: number]: string } = {
  1: 'Where am I holding to a standard that serves my ego more than the situation?',
  2: 'What do I need right now that I\'m not asking for?',
  3: 'Where am I performing rather than being honest about what I feel?',
  4: 'What ordinary moment today could I receive as enough?',
  5: 'Where am I withholding time or energy out of a fear of being depleted?',
  6: 'What authority am I seeking outside myself that I already have within?',
  7: 'What am I running from by staying busy?',
  8: 'Where am I protecting myself by taking control instead of letting go?',
  9: 'What opinion or preference am I merging away to keep the peace?',
};

// Wing flavor descriptions - how each wing colors the core type
const WING_FLAVORS: { [key: string]: string } = {
  // Type 1 wings
  '1w9': 'The 9-wing brings a softer, more patient quality to the Reformer energy. You may notice a tendency to pick battles carefully, avoiding unnecessary conflict while still holding firm to principles. This combination often appears as quiet idealism rather than vocal criticism.',
  '1w2': 'The 2-wing adds warmth and interpersonal focus to the Reformer drive. You may experience your desire for improvement as care for others—wanting to help them do better. This can create a mentor-like quality, though the inner critic may extend to how well you serve.',
  
  // Type 2 wings
  '2w1': 'The 1-wing brings structure and principle to the Helper pattern. You may notice standards around how helping "should" be done—a sense of doing it right, not just doing it. This can create reliable, conscientious care but also self-criticism when your giving doesn\'t measure up.',
  '2w3': 'The 3-wing adds energy and social awareness to the Helper instinct. You may be drawn to visible roles where helping has impact—leadership, organizing, being the one who makes things happen. The risk is confusing being needed with being successful.',
  
  // Type 3 wings
  '3w2': 'The 2-wing brings warmth and relational focus to the Achiever drive. Your success orientation may express through people—motivating teams, building networks, being liked as well as respected. The shadow here is performing warmth rather than feeling it.',
  '3w4': 'The 4-wing adds depth and aesthetic sensitivity to the Achiever energy. You may pursue success in creative or distinctive ways—achievement with personal style. There\'s often an inner tension between image and authenticity.',
  
  // Type 4 wings
  '4w3': 'The 3-wing brings ambition and audience-awareness to the Individualist depth. You may channel emotional intensity into creative output or visible expression—art, performance, building something that reflects your inner world. The risk is the audience becoming the measure.',
  '4w5': 'The 5-wing adds intellectual focus and self-sufficiency to the Individualist search. You may process emotion through analysis, symbol, or private creative work. There\'s often a pull toward knowing yourself deeply, sometimes at the cost of connection.',
  
  // Type 5 wings
  '5w4': 'The 4-wing brings emotional depth and aesthetic sensitivity to the Investigator mind. Your analysis may be drawn to meaning, symbol, and subjective experience—understanding the inner world as much as the outer. There\'s often a creative or artistic dimension.',
  '5w6': 'The 6-wing adds practical concern and skepticism to the Investigator stance. You may focus on systems, preparation, and understanding how things work in order to feel secure. There\'s often a loyalty to ideas or small trusted circles.',
  
  // Type 6 wings
  '6w5': 'The 5-wing brings analytical depth to the Loyalist vigilance. You may seek security through knowledge—understanding threats, mastering systems, thinking through scenarios. There\'s often an independent streak beneath the team orientation.',
  '6w7': 'The 7-wing adds optimism and social energy to the Loyalist pattern. You may balance worst-case thinking with best-case possibilities—testing but also hoping. There\'s often warmth and humor alongside the vigilance.',
  
  // Type 7 wings
  '7w6': 'The 6-wing brings groundedness and relationship focus to the Enthusiast energy. You may balance adventure with loyalty—seeking fun with trusted people rather than alone. There\'s often more follow-through and anxiety than pure Sevens, and a stronger need to belong.',
  '7w8': 'The 8-wing adds intensity and directness to the Enthusiast pattern. You may pursue options with more force—assertive, decisive, willing to push past obstacles. There\'s often entrepreneurial energy and less patience for limits.',
  
  // Type 8 wings
  '8w7': 'The 7-wing adds energy and optimism to the Challenger force. You may approach challenges with enthusiasm—enjoying the game, the strategy, the possibilities. There\'s often a charismatic, larger-than-life quality.',
  '8w9': 'The 9-wing brings steadiness and patience to the Challenger strength. You may wield power more quietly—a calm presence rather than an obvious force. There\'s often more receptivity and less need to dominate.',
  
  // Type 9 wings
  '9w8': 'The 8-wing adds grounded strength to the Peacemaker ease. You may have more access to anger and assertion than typical Nines—a quiet force that emerges when boundaries are crossed. There\'s often stubbornness beneath the accommodation.',
  '9w1': 'The 1-wing brings principle and idealism to the Peacemaker pattern. You may have clearer opinions than typical Nines—a sense of right and wrong—though expressing them directly may still feel difficult.',
};

// Balanced wings explanation
const BALANCED_WINGS_EXPLANATION = 'Your assessment suggests relatively equal access to both wings. This means you may draw on either flavor depending on context—neither has become a dominant default. Many Enneagram teachers consider this a flexibility that allows conscious choice: you can lean into whichever wing serves the situation.';
const BALANCED_WINGS_GROWTH_NOTE = 'Over time, people often learn which wing supports them best in different moments.';

// Type patterns for Deep Dive
const TYPE_PATTERNS: { [key: number]: { strengths: string; blindSpot: string; defense: string; relational: string; work: string } } = {
  1: {
    strengths: 'Principled, responsible, improvement-oriented, ethical, organized',
    blindSpot: 'Your own anger and resentment; the gap between ideals and reality',
    defense: 'Reaction formation — converting unacceptable impulses into their opposites',
    relational: 'Teaching and correcting; can be critical; seeks shared standards',
    work: 'Detail-oriented, reliable, quality-focused; struggles with "good enough"',
  },
  2: {
    strengths: 'Generous, empathetic, supportive, interpersonally attuned, warm',
    blindSpot: 'Your own needs and pride in being needed; indirect manipulation',
    defense: 'Repression — pushing your own needs out of awareness',
    relational: 'Giving to receive; creates dependency; fears being unwanted',
    work: 'People-centered, helpful, collaborative; struggles with boundaries',
  },
  3: {
    strengths: 'Efficient, adaptable, goal-oriented, inspiring, pragmatic',
    blindSpot: 'Your own feelings and authentic self; image vs. substance gap',
    defense: 'Identification — becoming the role or image that wins approval',
    relational: 'Impressive and charming; can be superficial; fears being seen as failing',
    work: 'High-achieving, competitive, results-driven; struggles with depth',
  },
  4: {
    strengths: 'Creative, emotionally honest, aesthetic, deep, authentic',
    blindSpot: 'What\'s present and ordinary; romanticizing what\'s missing',
    defense: 'Introjection — internalizing criticism and making it part of identity',
    relational: 'Intense and meaningful; can be dramatic; fears being ordinary',
    work: 'Original, expressive, meaning-driven; struggles with routine tasks',
  },
  5: {
    strengths: 'Observant, insightful, objective, self-sufficient, analytical',
    blindSpot: 'Your emotional needs and impact on others; excessive detachment',
    defense: 'Isolation — separating feelings from thoughts and events',
    relational: 'Private and cerebral; needs space; fears intrusion and demands',
    work: 'Expert, thorough, innovative; struggles with collaboration and action',
  },
  6: {
    strengths: 'Loyal, responsible, vigilant, questioning, committed',
    blindSpot: 'Your own courage and authority; projecting threats onto others',
    defense: 'Projection — attributing your own doubts and fears to external sources',
    relational: 'Reliable and testing; questions loyalty; fears betrayal',
    work: 'Team-oriented, troubleshooting, thorough; struggles with confidence',
  },
  7: {
    strengths: 'Enthusiastic, optimistic, versatile, quick-minded, adventurous',
    blindSpot: 'Painful feelings and limits; using positive framing to avoid depth',
    defense: 'Rationalization — reframing pain as learning or opportunity',
    relational: 'Fun and engaging; avoids negativity; fears being trapped in pain',
    work: 'Innovative, energetic, multi-tasking; struggles with follow-through',
  },
  8: {
    strengths: 'Powerful, protective, direct, decisive, self-confident',
    blindSpot: 'Your own vulnerability and impact; excessive force or control',
    defense: 'Denial — blocking awareness of weakness or vulnerability',
    relational: 'Protective and confronting; dominates; fears being controlled',
    work: 'Leadership-oriented, decisive, entrepreneurial; struggles with delegation',
  },
  9: {
    strengths: 'Peaceful, accepting, patient, receptive, mediating',
    blindSpot: 'Your own preferences and anger; merging with others\' agendas',
    defense: 'Narcotization — numbing through routine, comfort, or distraction',
    relational: 'Harmonizing and accommodating; avoids conflict; fears disconnection',
    work: 'Steady, inclusive, diplomatic; struggles with priorities and assertion',
  },
};

// Self-mastery levels
const MASTERY_LEVELS: { [key: number]: { reactive: string; average: string; resourced: string } } = {
  1: {
    reactive: 'Critical, rigid, resentful — the inner critic runs the show.',
    average: 'Hardworking, principled, sometimes preachy — improvement-focused.',
    resourced: 'Wise, accepting, discerning — holds standards without attachment.',
  },
  2: {
    reactive: 'Manipulative, prideful, martyr — giving with strings attached.',
    average: 'Helpful, warm, people-pleasing — connection through service.',
    resourced: 'Unconditionally caring, self-aware — gives freely without agenda.',
  },
  3: {
    reactive: 'Deceitful, image-obsessed, empty — performing for approval.',
    average: 'Ambitious, efficient, competitive — achieving visible goals.',
    resourced: 'Authentic, inspiring, truthful — succeeds from genuine value.',
  },
  4: {
    reactive: 'Self-absorbed, dramatic, envious — lost in emotional storms.',
    average: 'Creative, melancholic, searching — seeking meaningful depth.',
    resourced: 'Equanimous, creative, present — transforms feeling into beauty.',
  },
  5: {
    reactive: 'Isolated, nihilistic, detached — retreating from all demands.',
    average: 'Analytical, private, accumulating — building inner resources.',
    resourced: 'Visionary, engaged, generous — shares knowledge and presence.',
  },
  6: {
    reactive: 'Paranoid, reactive, blaming — seeing threat everywhere.',
    average: 'Loyal, questioning, responsible — seeking security in structure.',
    resourced: 'Courageous, trusting, grounded — acts from inner authority.',
  },
  7: {
    reactive: 'Scattered, escapist, excessive — running from any discomfort.',
    average: 'Optimistic, busy, planning — staying stimulated and positive.',
    resourced: 'Focused, joyful, present — experiences depth without fear.',
  },
  8: {
    reactive: 'Dominating, vengeful, destructive — power without restraint.',
    average: 'Assertive, protective, direct — leading through strength.',
    resourced: 'Magnanimous, vulnerable, just — uses power to serve.',
  },
  9: {
    reactive: 'Stubborn, checked-out, passive-aggressive — resisting through inaction.',
    average: 'Pleasant, accommodating, routine — maintaining peace.',
    resourced: 'Engaged, self-assured, present — acts from clear priorities.',
  },
};

// ============================================
// DAILY MICRO-LESSONS (10 per type)
// ============================================

const MICRO_LESSONS: { [key: number]: string[] } = {
  1: [
    "Notice where 'should' appears today. **Replace one 'should' with a choice.**",
    "Pick one small imperfection and let it stand. Practice staying calm with it.",
    "When you correct something, ask: 'Is this improvement… or control?'",
    "Trade criticism for precision: describe facts before judging.",
    "Try 'good enough' on one task. Finish, then stop.",
    "If you feel resentful, check if you're holding an unspoken standard.",
    "Choose one value you care about and do one tiny act that matches it.",
    "Before fixing others, ask permission—or offer options.",
    "Name your inner critic voice. Then answer it with a kinder truth.",
    "Today's integrity practice: align one action with what you believe.",
  ],
  2: [
    "Before helping, pause: **Do they want help or presence?**",
    "Ask for one thing you need, directly and simply.",
    "Notice if you're earning love. Try giving without tracking.",
    "If you feel unappreciated, check what expectation was unspoken.",
    "Practice saying 'not today' once, kindly.",
    "Let someone else support you without reciprocating immediately.",
    "Name your real feeling before you go into 'caretaker mode.'",
    "Today's boundary: help, but don't over-extend.",
    "Replace advice with a question. Stay curious.",
    "Choose one relationship and be honest about your needs.",
  ],
  3: [
    "Notice where you're performing. **Name the real fear underneath.**",
    "Do one thing slowly and well, even if no one sees it.",
    "Ask: 'What would success mean if nobody applauded?'",
    "Share one imperfect truth with someone safe.",
    "Choose one priority and drop one optional goal.",
    "Check if you're avoiding a feeling by staying productive.",
    "Practice being present without optimizing the moment.",
    "Today's integrity: don't exaggerate—be exact.",
    "Celebrate progress privately, not publicly.",
    "Ask for feedback that is not about results—about impact.",
  ],
  4: [
    "Notice longing today. **Name what you actually want.**",
    "Choose one ordinary moment and make it meaningful through attention.",
    "If you feel misunderstood, state your need plainly once.",
    "Practice 'enoughness': list 3 things that are already true and good.",
    "Create something small in 10 minutes. Finish it.",
    "Don't amplify emotion—witness it. Let it move through.",
    "Trade comparison for curiosity: 'What is this here to teach me?'",
    "Today: connect to beauty without needing intensity.",
    "Share a feeling without adding a story about it.",
    "Choose action over mood once today.",
  ],
  5: [
    "Notice where you're withholding. **Offer one small contribution.**",
    "Action can create clarity. Pick one tiny step before more research.",
    "If you feel drained, check if you're hoarding energy unnecessarily.",
    "Practice presence: engage for 5 minutes without retreating mentally.",
    "Say what you know in simple language—no over-explaining.",
    "Share one thought or feeling with someone you trust.",
    "Today: prioritize one deep focus block, then stop.",
    "Ask for what you need rather than disappearing.",
    "Let curiosity connect you to people, not just ideas.",
    "Your knowledge becomes wisdom when you apply it.",
  ],
  6: [
    "Notice the 'what if' loop. **Name the most likely outcome.**",
    "Choose one trusted person and ask for direct reassurance.",
    "Separate facts from fears: write 2 facts, 2 worries.",
    "Practice inner authority: make one small decision without polling others.",
    "If you feel tense, check if you're scanning for threats.",
    "Today: do one courageous action even with uncertainty.",
    "Replace worst-case planning with 'next right step.'",
    "Trust practice: delegate one small thing.",
    "Name your loyalty—what are you protecting? Is it still true?",
    "Ground in support: remember times you handled hard things.",
  ],
  7: [
    "Notice option-seeking. **Name the avoidance.**",
    "Choose one thing and go deeper, not wider.",
    "If you feel restless, ask: 'What feeling am I skipping?'",
    "Practice constraint: one plan, one commitment, one finish.",
    "Let a moment be simple—no upgrading needed.",
    "Today: complete a task even when it becomes boring.",
    "Replace reframing with truth: state the hard part plainly once.",
    "Joy practice: enjoy what's here without chasing the next.",
    "Ask someone: 'What are you not saying?' and listen fully.",
    "Freedom grows when you can stay with discomfort.",
  ],
  8: [
    "Notice control impulses. **Name what you're protecting.**",
    "Practice soft power: make one request without pushing.",
    "If you feel intensity rising, slow your body down first.",
    "Let someone else lead a small decision today.",
    "Say the vulnerable truth under the strong stance.",
    "Boundary practice: be clear without being forceful.",
    "Ask: 'Is this strength… or armor?'",
    "Choose one act of protection that is gentle, not aggressive.",
    "Repair quickly: if you overpowered, acknowledge it directly.",
    "True autonomy includes letting people choose.",
  ],
  9: [
    "Notice numbing. **Name what you want.**",
    "Choose one small priority and complete it before merging with others.",
    "Practice saying a clear 'no' once, kindly.",
    "If you're procrastinating, ask: 'What conflict am I avoiding?'",
    "Bring one honest preference into a conversation.",
    "Do one thing that creates momentum, even if imperfect.",
    "Body check: where are you tense but ignoring it?",
    "Choose presence over comfort: engage fully for 10 minutes.",
    "If you feel invisible, make yourself explicit—one sentence.",
    "Peace isn't avoidance. It's alignment.",
  ],
};

// Helper function to get today's micro-lesson index (Asia/Kuala_Lumpur timezone)
const getTodaysMicroLessonIndex = (coreType: number): number => {
  // Get current date in Asia/Kuala_Lumpur timezone
  const now = new Date();
  const klTime = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Kuala_Lumpur' }));
  
  // Calculate days since Unix epoch
  const daysSinceEpoch = Math.floor(klTime.getTime() / (1000 * 60 * 60 * 24));
  
  // Get lessons for this type
  const lessons = MICRO_LESSONS[coreType] || MICRO_LESSONS[1];
  
  // Return index using modulo
  return daysSinceEpoch % lessons.length;
};

// Helper function to render text with bold sections (marked with **)
const renderBoldText = (text: string, style: any, boldStyle: any) => {
  const parts = text.split(/\*\*(.*?)\*\*/g);
  return parts.map((part, index) => {
    // Odd indices are the bold parts
    if (index % 2 === 1) {
      return <Text key={index} style={[style, boldStyle]}>{part}</Text>;
    }
    return <Text key={index} style={style}>{part}</Text>;
  });
};

// ============================================
// TYPES
// ============================================

interface EnneagramResult {
  inferred_core: number;
  inferred_wing: number | 'balanced' | null;
  confidence: number;
  confidence_tier: string;
  is_close?: boolean;
  top_candidates: { type: number; probability: number }[];
  state_calibration?: {
    energy_state: string;
    life_context: string;
    answer_frame: string;
  };
  // PROVENANCE FIELDS (Task 1 - Debug Stamp)
  result_id?: string;
  user_id?: string;
  assessment_depth?: string;
  assessment_version?: string;
  created_at?: string;
  updated_at?: string;
  wing_left_score?: number;
  wing_right_score?: number;
  enneagram_computed_details?: any;
}

// ============================================
// WING DISPLAY SYSTEM
// ============================================
// Same logic as results.tsx - ensures consistency across all views
// ============================================

type WingDisplayState = 'dominant' | 'leaning' | 'balanced' | 'not_clear';

interface WingDisplayInfo {
  state: WingDisplayState;
  typeLabel: string;
  confidenceBadge: 'High' | 'Exploratory' | 'Low';
  helperText: string | null;
}

function getWingDisplayInfo(
  coreType: number,
  wing: number | 'balanced' | null,
  confidenceTier: string
): WingDisplayInfo {
  const wings = WING_NUMBERS[coreType];
  
  // Case D: Wing Not Yet Clear
  if (wing === null || wing === undefined) {
    return {
      state: 'not_clear',
      typeLabel: `Type ${coreType} — wing not yet clear`,
      confidenceBadge: 'Low',
      helperText: 'With more reflections or questions, a clearer wing may emerge.',
    };
  }
  
  // Case C: Balanced Wings
  if (wing === 'balanced') {
    return {
      state: 'balanced',
      typeLabel: `Type ${coreType} — balanced wings (${wings.left} & ${wings.right})`,
      confidenceBadge: 'Low',
      helperText: 'Both adjacent patterns appear active. This often clarifies over time.',
    };
  }
  
  // Wing is a number - show as dominant style (Type Xw#)
  // Per user request: Always show "Type 7w8" format for numeric wings
  // regardless of confidence tier
  const confidenceBadge = confidenceTier === 'high' ? 'High' 
    : (confidenceTier === 'medium' || confidenceTier === 'moderate') ? 'Exploratory' 
    : 'Exploratory';
  
  // For numeric wing, always use dominant display (Type XwY)
  return {
    state: 'dominant',
    typeLabel: `Type ${coreType}w${wing}`,
    confidenceBadge,
    helperText: confidenceTier !== 'high' 
      ? 'Your wing pattern is still emerging. This may refine with more reflections.'
      : null,
  };
}

interface Props {
  result: EnneagramResult;
  userId: string;
}

type TabType = 'summary' | 'snapshot' | 'today' | 'deep_dive';
type EnergyState = 'low' | 'neutral' | 'high';
type MasteryLevel = 'reactive' | 'average' | 'resourced';

// ============================================
// COMPONENT
// ============================================

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function EnneagramLensView({ result, userId }: Props) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [energyState, setEnergyState] = useState<EnergyState | null>(
    (result.state_calibration?.energy_state as EnergyState) || null
  );
  const [selectedMasteryLevel, setSelectedMasteryLevel] = useState<MasteryLevel>('average');
  const [showRetakeModal, setShowRetakeModal] = useState(false);
  
  // ============================================
  // DEBUG WING STATE OVERRIDE
  // ============================================
  // For visual verification of P0 Wing UX Fix
  // Only active when DEBUG_MIRROR_ENV === true
  const [debugWingState, setDebugWingState] = useState<DebugWingState>('off');
  
  // Chat state
  const [chatExpanded, setChatExpanded] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [activeCardContext, setActiveCardContext] = useState<string>('today_general');
  
  // Trait cards and computed details state
  const [traitCards, setTraitCards] = useState<EnneagramTraitCard[]>([]);
  const [computedDetails, setComputedDetails] = useState<EnneagramComputedDetails | null>(null);
  const [traitsLoading, setTraitsLoading] = useState(false);
  const [traitsSource, setTraitsSource] = useState<'book' | 'static' | 'none'>('none');
  
  // Deep Dive state (legacy API-driven content - fallback only)
  const [deepDiveData, setDeepDiveData] = useState<EnneagramDeepDiveResponse | null>(null);
  const [deepDiveLoading, setDeepDiveLoading] = useState(false);
  
  // Narrative Engine state (new layered narrative content - PRIMARY)
  const [narrativeData, setNarrativeData] = useState<EnneagramNarrativeResponse | null>(null);
  const [narrativeStatus, setNarrativeStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  
  // Collapsible state for Deeper Patterns section
  const [deeperPatternsExpanded, setDeeperPatternsExpanded] = useState(false);
  
  // Collapsible state for other sections
  const [otherWingExpanded, setOtherWingExpanded] = useState(false);
  const [energeticFlowExpanded, setEnergeticFlowExpanded] = useState(false);
  
  // Q&A Modal state (hidden initially per user request)
  const [showQAModal, setShowQAModal] = useState(false);
  const [qaQuestion, setQaQuestion] = useState('');
  const [qaAnswer, setQaAnswer] = useState<string | null>(null);
  const [qaLoading, setQaLoading] = useState(false);
  
  // ============================================
  // DEBUG WATERMARK STATE (for verifying live deployment)
  // ============================================
  const [backendHealth, setBackendHealth] = useState<BackendHealthInfo | null>(null);
  const [rawDeepDiveTypeLabel, setRawDeepDiveTypeLabel] = useState<string | null>(null);
  const isDebugMode = getUrlDebugParam();
  
  // Fetch backend health once per session (debug mode only)
  useEffect(() => {
    if (isDebugMode) {
      getBackendHealth().then(setBackendHealth);
    }
  }, [isDebugMode]);

  const core = result.inferred_core;
  const wing = result.inferred_wing;
  const wings = WING_NUMBERS[core];
  const otherWing = wing === wings.left ? wings.right : (wing === wings.right ? wings.left : wings.left);
  
  // ============================================
  // COMPUTE WING INFO (with debug override support)
  // ============================================
  // If debug override is active, use mock data
  // Otherwise use real result data
  const debugOverride = DEBUG_MIRROR_ENV ? getDebugWingOverride(core, debugWingState) : null;
  
  // Get comprehensive wing display info
  const wingInfo = debugOverride 
    ? getWingDisplayInfo(core, debugOverride.mockWing, debugOverride.mockConfidenceTier)
    : getWingDisplayInfo(core, wing, result.confidence_tier);
  
  // Send chat message
  const handleSendChat = useCallback(async () => {
    if (!chatInput.trim() || chatLoading) return;
    
    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);
    
    try {
      const response = await sendEnneagramChat({
        user_id: userId,
        message: userMessage,
        context: {
          inferred_core: result.inferred_core,
          inferred_wing: result.inferred_wing,
          confidence_tier: result.confidence_tier,
          is_close: result.is_close || false,
          top_candidates: result.top_candidates.slice(0, 2),
          energy_state: energyState || 'unknown',
          active_card_context: activeTab === 'deep_dive' ? 'deep_dive' : activeCardContext,
        },
      });
      
      setChatMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
    } catch (error) {
      console.error('Enneagram chat error:', error);
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'I couldn\'t process that right now. Try again in a moment.' 
      }]);
    } finally {
      setChatLoading(false);
    }
  }, [chatInput, chatLoading, userId, result, energyState, activeTab, activeCardContext]);

  // Save energy state locally for session
  const handleEnergySelect = async (state: EnergyState) => {
    setEnergyState(state);
    try {
      await AsyncStorage.setItem(`enneagram_energy_${userId}`, state);
    } catch (e) {
      console.error('Failed to save energy state:', e);
    }
  };

  // Load saved energy state
  useEffect(() => {
    const loadEnergyState = async () => {
      try {
        const saved = await AsyncStorage.getItem(`enneagram_energy_${userId}`);
        if (saved && !energyState) {
          setEnergyState(saved as EnergyState);
        }
      } catch (e) {
        console.error('Failed to load energy state:', e);
      }
    };
    loadEnergyState();
  }, [userId]);

  // Load trait cards and computed details (once on mount)
  useEffect(() => {
    const loadTraitCards = async () => {
      if (!userId) return;
      
      setTraitsLoading(true);
      try {
        const response = await getEnneagramTraits(userId);
        setTraitCards(response.cards || []);
        setComputedDetails(response.computed_details || null);
        setTraitsSource(response.source || 'none');
      } catch (error) {
        console.error('Failed to load trait cards:', error);
      } finally {
        setTraitsLoading(false);
      }
    };
    loadTraitCards();
  }, [userId]);

  // Load Narrative Engine content FIRST when deep dive tab is selected
  // This is the PRIMARY content source - legacy deepDiveData is fallback only
  useEffect(() => {
    const loadNarrative = async () => {
      console.log('[EnneagramLens] loadNarrative called, userId:', userId, 'activeTab:', activeTab, 'narrativeStatus:', narrativeStatus);
      if (!userId || activeTab !== 'deep_dive') return;
      // Skip if already loaded or loading
      if (narrativeStatus === 'loading' || narrativeStatus === 'ready') return;
      
      console.log('[EnneagramLens] Starting narrative fetch...');
      setNarrativeStatus('loading');
      try {
        const response = await getEnneagramNarrative(userId);
        console.log('[EnneagramLens] Narrative response:', response.success, response.sections?.length);
        
        // DEBUG: Capture raw type_label for debug watermark
        if (response.type_label) {
          setRawDeepDiveTypeLabel(response.type_label);
          console.log(`[DEBUG_WATERMARK] Raw type_label from API: "${response.type_label}"`);
          if (response.type_label.includes('wbalanced')) {
            console.warn(`[DEBUG_WATERMARK] ⚠️ BUG DETECTED: type_label contains "wbalanced"!`);
          }
        }
        
        if (response.success && response.sections.length > 0) {
          setNarrativeData(response);
          setNarrativeStatus('ready');
          console.log('[EnneagramLens] Narrative ready!');
        } else {
          setNarrativeStatus('error');
          console.log('[EnneagramLens] Narrative failed - no sections');
        }
      } catch (error) {
        console.error('[EnneagramLens] Failed to load narrative:', error);
        setNarrativeStatus('error');
      }
    };
    loadNarrative();
  }, [userId, activeTab, narrativeStatus]);

  // Load Deep Dive data ONLY as fallback when narrative fails
  useEffect(() => {
    const loadDeepDive = async () => {
      // Only load legacy deepDiveData if narrative failed and we don't have it yet
      if (!userId || activeTab !== 'deep_dive') return;
      if (narrativeStatus !== 'error') return; // Wait for narrative to fail first
      if (deepDiveData || deepDiveLoading) return;
      
      setDeepDiveLoading(true);
      try {
        const response = await getEnneagramDeepDive(userId);
        setDeepDiveData(response);
      } catch (error) {
        console.error('Failed to load deep dive fallback:', error);
      } finally {
        setDeepDiveLoading(false);
      }
    };
    loadDeepDive();
  }, [userId, activeTab, narrativeStatus, deepDiveData, deepDiveLoading]);

  // Handle Q&A question submission
  const handleAskQuestion = useCallback(async (question?: string) => {
    const questionToAsk = question || qaQuestion;
    if (!questionToAsk.trim() || qaLoading) return;
    
    setQaLoading(true);
    setQaAnswer(null);
    
    try {
      const response = await askEnneagramQuestion(userId, questionToAsk);
      setQaAnswer(response.answer);
    } catch (error) {
      console.error('Q&A error:', error);
      setQaAnswer('Unable to process your question right now. Please try again.');
    } finally {
      setQaLoading(false);
    }
  }, [qaQuestion, qaLoading, userId]);

  // Open Q&A modal with a suggested question from a trait card
  const handleOpenQA = (suggestedQuestion?: string) => {
    setQaQuestion(suggestedQuestion || '');
    setQaAnswer(null);
    setShowQAModal(true);
  };

  const handleRetakeConfirm = () => {
    setShowRetakeModal(false);
    router.push('/enneagram/assessment');
  };

  // ============================================
  // RENDER HELPERS
  // ============================================

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, activeTab === 'summary' && styles.activeTabText]}>
          Summary
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'snapshot' && styles.activeTab]}
        onPress={() => setActiveTab('snapshot')}
      >
        <Text style={[styles.tabText, activeTab === 'snapshot' && styles.activeTabText]}>
          Snapshot
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

  const renderConfidenceBadge = () => {
    const tier = result.confidence_tier;
    return (
      <View style={[
        styles.confidenceBadge,
        tier === 'high' && styles.confidenceHigh,
        tier === 'medium' && styles.confidenceMedium,
        tier === 'low' && styles.confidenceLow,
      ]}>
        <Text style={styles.confidenceText}>
          {tier === 'high' ? 'High' : tier === 'medium' ? 'Medium' : 'Low'} Confidence
        </Text>
      </View>
    );
  };
  
  // ============================================
  // CHAT BOX COMPONENT
  // ============================================
  
  const renderChatBox = () => (
    <View style={styles.chatContainer}>
      <TouchableOpacity 
        style={styles.chatHeader}
        onPress={() => setChatExpanded(!chatExpanded)}
      >
        <View style={styles.chatHeaderLeft}>
          <Ionicons 
            name="chatbubble-outline" 
            size={18} 
            color={Colors.textSecondary} 
          />
          <Text style={styles.chatHeaderText}>Ask about this</Text>
        </View>
        <Ionicons 
          name={chatExpanded ? 'chevron-down' : 'chevron-up'} 
          size={18} 
          color={Colors.textTertiary} 
        />
      </TouchableOpacity>
      
      {chatExpanded && (
        <View style={styles.chatBody}>
          {/* Chat Messages */}
          {chatMessages.length > 0 && (
            <View style={styles.chatMessages}>
              {chatMessages.map((msg, index) => (
                <View 
                  key={index} 
                  style={[
                    styles.chatMessage,
                    msg.role === 'user' ? styles.chatMessageUser : styles.chatMessageAssistant
                  ]}
                >
                  <Text style={[
                    styles.chatMessageText,
                    msg.role === 'user' && styles.chatMessageTextUser
                  ]}>
                    {msg.content}
                  </Text>
                </View>
              ))}
              {chatLoading && (
                <View style={styles.chatMessageAssistant}>
                  <ActivityIndicator size="small" color={Colors.textSecondary} />
                </View>
              )}
            </View>
          )}
          
          {/* Chat Input */}
          <View style={styles.chatInputContainer}>
            <TextInput
              style={styles.chatInput}
              value={chatInput}
              onChangeText={setChatInput}
              placeholder="Ask about today's pattern, your wing, stress loops, or how to practice."
              placeholderTextColor={Colors.textTertiary}
              multiline
              maxLength={500}
              editable={!chatLoading}
            />
            <TouchableOpacity 
              style={[
                styles.chatSendButton,
                (!chatInput.trim() || chatLoading) && styles.chatSendButtonDisabled
              ]}
              onPress={handleSendChat}
              disabled={!chatInput.trim() || chatLoading}
            >
              <Ionicons 
                name="send" 
                size={18} 
                color={(!chatInput.trim() || chatLoading) ? Colors.textTertiary : Colors.background} 
              />
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );

  // ============================================
  // SUMMARY TAB
  // ============================================

  // ============================================
  // DEBUG STAMP DATA (shared between Summary and Deep Dive)
  // ============================================
  const showDebugStamp = DEBUG_MIRROR_ENV || getUrlDebugParam();
  const debugStampData = {
    // CLIENT INFO
    build_id: BUILD_ID,
    build_version: BUILD_VERSION,
    app_env: APP_ENV,
    platform: Platform.OS,
    api_base_url: API_BASE_URL,
    // SERVER RESPONSE PROVENANCE (from API)
    user_id: result.user_id || userId,
    result_id: result.result_id || 'unknown',
    assessment_depth: result.assessment_depth || 'unknown',
    assessment_version: result.assessment_version || 'unknown',
    core_type: core,
    wing_raw: String(wing),
    wing_left_score: result.wing_left_score ?? 'n/a',
    wing_right_score: result.wing_right_score ?? 'n/a',
    confidence_tier: result.confidence_tier,
    updated_at: result.updated_at || result.created_at || 'unknown',
    // LABEL DIAGNOSTICS
    wing_balance_label: computedDetails?.wing_balance_label || 'n/a',
  };
  
  // LOG PROVENANCE (Task 4 - automatic diagnostic log)
  useEffect(() => {
    if (showDebugStamp) {
      console.log(`[PROVENANCE] platform=${debugStampData.platform}, api=${debugStampData.api_base_url}, user=${debugStampData.user_id}, result_id=${debugStampData.result_id}, wing=${debugStampData.wing_raw}, updated_at=${debugStampData.updated_at}`);
    }
  }, [showDebugStamp, debugStampData.result_id]);

  // Reusable Debug Stamp Component
  const renderDebugStamp = () => {
    if (!showDebugStamp) return null;
    return (
      <View style={styles.debugStamp}>
        <Text style={styles.debugStampTitle}>🔧 PROVENANCE DEBUG</Text>
        <Text style={styles.debugStampSection}>Client:</Text>
        <Text style={styles.debugStampText}>BUILD: {debugStampData.build_version} ({debugStampData.build_id})</Text>
        <Text style={styles.debugStampText}>Platform: {debugStampData.platform} | API: {debugStampData.api_base_url}</Text>
        <Text style={styles.debugStampSection}>Server Response:</Text>
        <Text style={styles.debugStampText}>user_id: {debugStampData.user_id}</Text>
        <Text style={styles.debugStampText}>result_id: {debugStampData.result_id}</Text>
        <Text style={styles.debugStampText}>depth: {debugStampData.assessment_depth} | version: {debugStampData.assessment_version}</Text>
        <Text style={styles.debugStampText}>updated_at: {debugStampData.updated_at}</Text>
        <Text style={styles.debugStampSection}>Enneagram:</Text>
        <Text style={styles.debugStampText}>core: {debugStampData.core_type} | wing: {debugStampData.wing_raw} | tier: {debugStampData.confidence_tier}</Text>
        <Text style={styles.debugStampText}>wing_L: {debugStampData.wing_left_score} | wing_R: {debugStampData.wing_right_score}</Text>
      </View>
    );
  };

  const renderSummaryTab = () => (
    <>
      {/* DEBUG STAMP - visible with ?debug=1 */}
      {renderDebugStamp()}
      
      {/* Hero Card */}
      <View style={styles.heroCard}>
        <View style={styles.heroBadge}>
          <Text style={styles.heroBadgeText}>{core}</Text>
        </View>
        <Text style={styles.heroTitle}>{wingInfo.typeLabel}</Text>
        <Text style={styles.heroSubtitle}>
          {TYPE_NAMES[core]}
        </Text>
        {/* Confidence Badge with new system */}
        <View style={[
          styles.confidenceBadge,
          wingInfo.confidenceBadge === 'High' && styles.confidenceHigh,
          wingInfo.confidenceBadge === 'Exploratory' && styles.confidenceMedium,
          wingInfo.confidenceBadge === 'Low' && styles.confidenceLow,
        ]}>
          <Text style={styles.confidenceText}>
            {wingInfo.confidenceBadge}
          </Text>
        </View>
        {/* Helper text for non-dominant wing states */}
        {wingInfo.helperText && (
          <Text style={styles.heroHelperText}>
            {wingInfo.helperText}
          </Text>
        )}
        <Text style={styles.heroDisclaimer}>
          This lens reflects motivation, not mood.
        </Text>
      </View>

      {/* Core Motivation Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Core Motivation</Text>
        <Text style={styles.cardBody}>
          {CORE_MOTIVATIONS[core]}
        </Text>
      </View>

      {/* Wing Access Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Your Wing Access</Text>
        {wingInfo.state === 'dominant' || wingInfo.state === 'leaning' ? (
          <>
            <Text style={styles.cardBody}>
              Wings are access paths — capacities you can develop. The quieter wing often holds untapped potential.
            </Text>
            <View style={styles.wingRow}>
              <View style={styles.wingItem}>
                <Text style={styles.wingLabel}>
                  {wingInfo.state === 'dominant' ? 'Dominant' : 'Leaning'}
                </Text>
                <Text style={styles.wingValue}>Wing {wing}</Text>
              </View>
              <View style={styles.wingDivider} />
              <View style={styles.wingItem}>
                <Text style={styles.wingLabel}>Growth access</Text>
                <Text style={styles.wingValue}>Wing {otherWing}</Text>
              </View>
            </View>
          </>
        ) : wingInfo.state === 'balanced' ? (
          <Text style={styles.cardBody}>
            You show access to both wings ({wings.left} & {wings.right}). Balance comes from choosing consciously based on the situation, not defaulting to one pattern.
          </Text>
        ) : (
          <Text style={styles.cardBody}>
            Your wing pattern is still emerging. Both adjacent types ({wings.left} & {wings.right}) are available to you, and clarity often develops through more reflection and experience.
          </Text>
        )}
      </View>

      {/* Top Alternatives Card */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Top Alternatives</Text>
        <Text style={styles.cardSubtitle}>
          Common mistypes included for self-verification
        </Text>
        {result.top_candidates.slice(0, 3).map((candidate, index) => (
          <View key={candidate.type} style={styles.candidateRow}>
            <Text style={styles.candidateRank}>{index + 1}</Text>
            <Text style={styles.candidateType}>
              Type {candidate.type} — {TYPE_NAMES[candidate.type]}
            </Text>
            <Text style={styles.candidatePercent}>
              {Math.round(candidate.probability * 100)}%
            </Text>
          </View>
        ))}
      </View>

      {/* CTA Row */}
      <View style={styles.ctaRow}>
        <TouchableOpacity
          style={styles.ctaButtonPrimary}
          onPress={() => router.push('/enneagram/results')}
        >
          <Text style={styles.ctaButtonPrimaryText}>View Full Results</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={styles.ctaButtonSecondary}
          onPress={() => setShowRetakeModal(true)}
        >
          <Text style={styles.ctaButtonSecondaryText}>Retake Assessment</Text>
        </TouchableOpacity>
      </View>
    </>
  );

  // ============================================
  // TODAY TAB
  // ============================================

  const renderTodayTab = () => {
    // Generate practice based on energy state
    const getPractice = (): string => {
      if (!energyState || energyState === 'low') {
        return 'Ground yourself: feet on floor, three deep breaths. Then choose one small task you can complete in 10 minutes. Do only that.';
      } else if (energyState === 'neutral') {
        return 'Name one honest feeling without justifying it. Then pick your single most important priority for the next 2 hours. Focus only on that.';
      } else {
        return 'Use this energy for one courageous action: a difficult conversation, a focused sprint on deep work, or a decision you\'ve been avoiding.';
      }
    };
    
    // Get today's micro-lesson
    const lessonIndex = getTodaysMicroLessonIndex(core);
    const todaysLesson = MICRO_LESSONS[core]?.[lessonIndex] || MICRO_LESSONS[1][0];

    return (
      <>
        {/* Today Check-in Card */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Today Check-in</Text>
          <Text style={styles.cardBody}>What&apos;s your energy right now?</Text>
          <View style={styles.energyButtons}>
            {(['low', 'neutral', 'high'] as EnergyState[]).map((state) => (
              <TouchableOpacity
                key={state}
                style={[
                  styles.energyButton,
                  energyState === state && styles.energyButtonSelected
                ]}
                onPress={() => handleEnergySelect(state)}
              >
                <Ionicons
                  name={state === 'low' ? 'battery-dead-outline' : state === 'neutral' ? 'battery-half-outline' : 'battery-full-outline'}
                  size={18}
                  color={energyState === state ? Colors.background : Colors.text}
                />
                <Text style={[
                  styles.energyButtonText,
                  energyState === state && styles.energyButtonTextSelected
                ]}>
                  {state.charAt(0).toUpperCase() + state.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        
        {/* Daily Micro-Lesson Card */}
        <View style={styles.microLessonCard}>
          <View style={styles.microLessonHeader}>
            <View>
              <Text style={styles.microLessonTitle}>Daily Micro-Lesson</Text>
              <Text style={styles.microLessonSubtitle}>Type {core} practice</Text>
            </View>
            <Ionicons name="bulb-outline" size={22} color={Colors.text} />
          </View>
          <Text style={styles.microLessonBody}>
            {renderBoldText(todaysLesson, styles.microLessonBodyText, styles.microLessonBoldText)}
          </Text>
          <View style={styles.microLessonFooter}>
            <View style={styles.microLessonRotates}>
              <Ionicons name="refresh-outline" size={12} color={Colors.textTertiary} />
              <Text style={styles.microLessonRotatesText}>Rotates daily</Text>
            </View>
            <TouchableOpacity 
              style={styles.microLessonAskButton}
              onPress={() => {
                setChatExpanded(true);
                setActiveCardContext('practice');
              }}
            >
              <Text style={styles.microLessonAskText}>Ask about this</Text>
              <Ionicons name="chatbubble-outline" size={12} color={Colors.text} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Stress Pattern Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="warning-outline" size={18} color={Colors.textSecondary} />
            <Text style={styles.cardTitle}>Watch For (Stress)</Text>
          </View>
          <Text style={styles.cardBody}>
            {STRESS_PATTERNS[core]}
          </Text>
        </View>

        {/* Growth Pattern Card */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="trending-up-outline" size={18} color={Colors.textSecondary} />
            <Text style={styles.cardTitle}>Access (Growth)</Text>
          </View>
          <Text style={styles.cardBody}>
            {GROWTH_PATTERNS[core]}
          </Text>
        </View>

        {/* 2-Minute Practice Card */}
        <View style={styles.practiceCard}>
          <Text style={styles.practiceLabel}>2-MINUTE PRACTICE</Text>
          <Text style={styles.practiceBody}>
            {getPractice()}
          </Text>
        </View>

        {/* Journal Prompt Card */}
        <View style={styles.promptCard}>
          <Text style={styles.promptLabel}>JOURNAL PROMPT</Text>
          <Text style={styles.promptBody}>
            {JOURNAL_PROMPTS[core]}
          </Text>
          <TouchableOpacity
            style={styles.journalCTA}
            onPress={() => {
              // Use shared helper for navigation
              const prefill = buildJournalPrefill(JOURNAL_PROMPTS[core]);
              goToJournalWithPrefill(router, prefill, 'enneagram');
            }}
          >
            <Ionicons name="create-outline" size={16} color={Colors.accent} />
            <Text style={styles.journalCTAText}>Write in Journal</Text>
          </TouchableOpacity>
        </View>
        
        {/* Chat Box */}
        {renderChatBox()}
      </>
    );
  };

  // ============================================
  // DEEP DIVE TAB
  // ============================================

  // Helper to format group labels nicely
  const formatGroupLabel = (group: string | undefined): string => {
    if (!group) return '—';
    return group.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  // Determine if wings are balanced
  const isBalancedWings = wing === 'balanced' || computedDetails?.wing_balance_label === 'balanced';
  
  // Get wing stance display string - NOW USING wingInfo
  const getWingStanceLabel = (): string => {
    return wingInfo.typeLabel;
  };

  // Get wing flavor key for lookup
  const getWingFlavorKey = (): string => {
    if (typeof wing === 'number') return `${core}w${wing}`;
    return '';
  };

  // Get confidence label from wing info - replaces old logic
  const getConfidenceLabel = (): { text: string; tier: 'high' | 'medium' | 'low' } => {
    if (wingInfo.confidenceBadge === 'High') return { text: 'High', tier: 'high' };
    if (wingInfo.confidenceBadge === 'Exploratory') return { text: 'Exploratory', tier: 'medium' };
    return { text: 'Low', tier: 'low' };
  };

  const renderDeepDiveTab = () => {
    console.log('[EnneagramLens] renderDeepDiveTab called! narrativeStatus:', narrativeStatus, 'useNarrative:', narrativeStatus === 'ready' && narrativeData?.sections?.length);
    
    // =====================================================================
    // LOADING STATE - Show while narrative is loading (prevents flicker)
    // Never show legacy content while narrative is loading
    // =====================================================================
    if (narrativeStatus === 'loading' || narrativeStatus === 'idle') {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.textSecondary} />
          <Text style={styles.loadingText}>Generating your narrative...</Text>
        </View>
      );
    }
    
    // =====================================================================
    // FALLBACK: Legacy deep dive loading (only when narrative failed)
    // =====================================================================
    if (narrativeStatus === 'error' && deepDiveLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.textSecondary} />
          <Text style={styles.loadingText}>Loading your Deep Dive...</Text>
        </View>
      );
    }

    // =====================================================================
    // CONTENT RENDERING - Mutually exclusive: narrative OR legacy
    // =====================================================================
    const useNarrative = narrativeStatus === 'ready' && narrativeData?.sections && narrativeData.sections.length > 0;
    
    // CRITICAL: Always use LOCAL wingInfo.typeLabel for header display
    // Never trust backend type_label - it may contain bugs like "7wbalanced"
    // This ensures Summary and Deep Dive render identically
    const typeLabel = wingInfo.typeLabel;
    const typeName = TYPE_NAMES[core];
    
    // LAYOUT VERSION MARKER (PART B requirement)
    const ENNEAGRAM_LAYOUT_VERSION = 'v2';

    return (
      <>
        {/* DEBUG STAMP - visible with ?debug=1 */}
        {renderDebugStamp()}
        
        {/* ENNEAGRAM_LAYOUT DEBUG MARKER (PART B - ?debug=1 only) */}
        {isDebugMode && (
          <View style={styles.layoutVersionBadge}>
            <Text style={styles.layoutVersionText}>ENNEAGRAM_LAYOUT={ENNEAGRAM_LAYOUT_VERSION}</Text>
            <Text style={styles.layoutVersionSubtext}>
              renderer={useNarrative ? 'narrative_v2' : 'legacy_fallback'}
            </Text>
          </View>
        )}
        
        {/* ===== HEADER (consistent, no flicker) ===== */}
        <View style={styles.deepDiveHeader}>
          <View style={styles.deepDiveHeaderTop}>
            <Text style={styles.deepDiveType}>{typeLabel}</Text>
            <View style={[
              styles.confidenceBadge,
              wingInfo.confidenceBadge === 'High' && styles.confidenceHigh,
              wingInfo.confidenceBadge === 'Exploratory' && styles.confidenceMedium,
              wingInfo.confidenceBadge === 'Low' && styles.confidenceLow,
            ]}>
              <Text style={styles.confidenceBadgeText}>
                {wingInfo.confidenceBadge}
              </Text>
            </View>
          </View>
          <Text style={styles.deepDiveWingStance}>{typeName}</Text>
          {wingInfo.helperText && (
            <Text style={styles.deepDiveHelperText}>
              {wingInfo.helperText}
            </Text>
          )}
          <Text style={styles.deepDiveNote}>This lens reflects strategy, not identity.</Text>
        </View>

        {/* ===== NARRATIVE SECTIONS (Story-only when available) ===== */}
        {useNarrative && narrativeData.sections.map((section, index) => {
          // Identify section types for collapsible behavior
          const sectionId = section.id || '';
          const labelLower = (section.label || '').toLowerCase();
          
          const isCoreStory = sectionId === 'core_story' || labelLower.includes('core story');
          const isWingStory = sectionId === 'wing_story' || labelLower.includes('your wing');
          const isOtherWing = sectionId === 'other_wing' || labelLower.includes('other wing');
          const isDeeperPatterns = sectionId === 'deeper_patterns' || labelLower.includes('deeper pattern');
          const isClosing = !section.label;
          
          // Core Story - always expanded (no collapsible)
          if (isCoreStory) {
            return (
              <View key={`narrative-${index}`} style={styles.deepDiveSection}>
                <Text style={styles.deepDiveSectionTitle}>{section.label}</Text>
                <Text style={styles.deepDiveSectionBody}>{section.body}</Text>
              </View>
            );
          }
          
          // Core + Wing - always expanded (no collapsible)
          if (isWingStory) {
            return (
              <View key={`narrative-${index}`} style={styles.deepDiveSection}>
                <Text style={styles.deepDiveSectionTitle}>{section.label}</Text>
                <Text style={styles.deepDiveSectionBody}>{section.body}</Text>
              </View>
            );
          }
          
          // The Other Wing - collapsible, collapsed by default
          if (isOtherWing) {
            return (
              <View key={`narrative-${index}`} style={styles.deepDiveSection}>
                <TouchableOpacity 
                  style={styles.collapsibleHeader}
                  onPress={() => setOtherWingExpanded(!otherWingExpanded)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.deepDiveSectionTitle}>{section.label}</Text>
                  <Ionicons 
                    name={otherWingExpanded ? "chevron-up" : "chevron-down"} 
                    size={20} 
                    color={Colors.textSecondary} 
                  />
                </TouchableOpacity>
                {otherWingExpanded && (
                  <Text style={styles.deepDiveSectionBody}>{section.body}</Text>
                )}
              </View>
            );
          }
          
          // Deeper Patterns - collapsible, collapsed by default
          if (isDeeperPatterns) {
            return (
              <View key={`narrative-${index}`} style={styles.deepDiveSection}>
                <TouchableOpacity 
                  style={styles.collapsibleHeader}
                  onPress={() => setDeeperPatternsExpanded(!deeperPatternsExpanded)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.deepDiveSectionTitle}>{section.label}</Text>
                  <Ionicons 
                    name={deeperPatternsExpanded ? "chevron-up" : "chevron-down"} 
                    size={20} 
                    color={Colors.textSecondary} 
                  />
                </TouchableOpacity>
                {deeperPatternsExpanded && (
                  <Text style={styles.deepDiveSectionBody}>{section.body}</Text>
                )}
              </View>
            );
          }
          
          // Closing reflection - always visible, special styling
          if (isClosing) {
            return (
              <View key={`narrative-${index}`} style={styles.deepDiveSection}>
                <Text style={styles.closingReflection}>{section.body}</Text>
              </View>
            );
          }
          
          // Default: regular section
          return (
            <View key={`narrative-${index}`} style={styles.deepDiveSection}>
              {section.label && (
                <Text style={styles.deepDiveSectionTitle}>{section.label}</Text>
              )}
              <Text style={styles.deepDiveSectionBody}>{section.body}</Text>
            </View>
          );
        })}
        
        {/* ===== ENERGETIC FLOW SECTION (Stress/Growth Movement) ===== */}
        {useNarrative && computedDetails && (
          <View style={styles.deepDiveSection}>
            <TouchableOpacity 
              style={styles.collapsibleHeader}
              onPress={() => setEnergeticFlowExpanded(!energeticFlowExpanded)}
              activeOpacity={0.7}
            >
              <Text style={styles.deepDiveSectionTitle}>Energetic Flow</Text>
              <Ionicons 
                name={energeticFlowExpanded ? "chevron-up" : "chevron-down"} 
                size={20} 
                color={Colors.textSecondary} 
              />
            </TouchableOpacity>
            {energeticFlowExpanded && (
              <View style={styles.energeticFlowContent}>
                <Text style={styles.deepDiveSectionBody}>
                  {`Under pressure, attention may shift toward Type ${computedDetails.stress_line_to || '?'} patterns — ${getStressDescription(core, computedDetails.stress_line_to)}`}
                </Text>
                <Text style={[styles.deepDiveSectionBody, { marginTop: 12 }]}>
                  {`When resourced, there's often access to Type ${computedDetails.growth_line_to || '?'} qualities — ${getGrowthDescription(core, computedDetails.growth_line_to)}`}
                </Text>
                <Text style={styles.energeticFlowNote}>
                  These aren't destinations — just movements you may notice.
                </Text>
              </View>
            )}
          </View>
        )}

        {/* ===== FALLBACK: Legacy Deep Dive (only when narrative unavailable) ===== */}
        {!useNarrative && narrativeStatus === 'error' && deepDiveData?.sections && (
          <>
            {deepDiveData.sections.map((section, index) => (
              <View key={index} style={styles.deepDiveSection}>
                <Text style={styles.deepDiveSectionTitle}>{section.label}</Text>
                <Text style={styles.deepDiveSectionBody}>{section.body}</Text>
              </View>
            ))}
            
            {/* Enneagram Structure grid - ONLY in legacy fallback mode */}
            {(deepDiveData?.computed_details || computedDetails) && (
              <View style={styles.structureCard}>
                <Text style={styles.structureTitle}>ENNEAGRAM STRUCTURE</Text>
                
                <View style={styles.structureGrid}>
                  <View style={styles.structureItem}>
                    <Ionicons name="radio-button-on-outline" size={14} color={Colors.textSecondary} />
                    <Text style={styles.structureLabel}>Center</Text>
                    <Text style={styles.structureValue}>{formatGroupLabel((deepDiveData?.computed_details || computedDetails)?.center)}</Text>
                  </View>
                  <View style={styles.structureDivider} />
                  <View style={styles.structureItem}>
                    <Ionicons name="people-outline" size={14} color={Colors.textSecondary} />
                    <Text style={styles.structureLabel}>Social Style</Text>
                    <Text style={styles.structureValue}>{formatGroupLabel((deepDiveData?.computed_details || computedDetails)?.hornevian_group)}</Text>
                  </View>
                </View>
                
                <View style={[styles.structureGrid, { marginTop: 12 }]}>
                  <View style={styles.structureItem}>
                    <Ionicons name="arrow-down-outline" size={14} color={Colors.textSecondary} />
                    <Text style={styles.structureLabel}>Stress → Type</Text>
                    <Text style={styles.structureValue}>{(deepDiveData?.computed_details || computedDetails)?.stress_line_to || '—'}</Text>
                  </View>
                  <View style={styles.structureDivider} />
                  <View style={styles.structureItem}>
                    <Ionicons name="arrow-up-outline" size={14} color={Colors.textSecondary} />
                    <Text style={styles.structureLabel}>Growth → Type</Text>
                    <Text style={styles.structureValue}>{(deepDiveData?.computed_details || computedDetails)?.growth_line_to || '—'}</Text>
                  </View>
                </View>
              </View>
            )}
          </>
        )}

        {/* ===== RETAKE LINK ===== */}
        <TouchableOpacity
          style={styles.retakeLink}
          onPress={() => setShowRetakeModal(true)}
        >
          <Ionicons name="refresh-outline" size={16} color={Colors.textSecondary} />
          <Text style={styles.retakeLinkText}>Retake Assessment</Text>
        </TouchableOpacity>
        
        {/* Chat Box - kept outside story flow */}
        {renderChatBox()}
      </>
    );
  };

  // ============================================
  // RETAKE MODAL
  // ============================================

  const renderRetakeModal = () => (
    <Modal
      visible={showRetakeModal}
      transparent
      animationType="fade"
      onRequestClose={() => setShowRetakeModal(false)}
    >
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <Text style={styles.modalTitle}>Retake Assessment?</Text>
          <Text style={styles.modalText}>
            This will replace your current results. The assessment takes about 10-12 minutes.
          </Text>
          <View style={styles.modalActions}>
            <TouchableOpacity
              style={styles.modalCancelButton}
              onPress={() => setShowRetakeModal(false)}
            >
              <Text style={styles.modalCancelText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.modalConfirmButton}
              onPress={handleRetakeConfirm}
            >
              <Text style={styles.modalConfirmText}>Retake</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );

  // ============================================
  // Q&A MODAL (hidden initially, opened from trait cards)
  // ============================================

  const renderQAModal = () => (
    <Modal
      visible={showQAModal}
      transparent
      animationType="slide"
      onRequestClose={() => setShowQAModal(false)}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.qaModalOverlay}
      >
        <View style={styles.qaModalContent}>
          {/* Header */}
          <View style={styles.qaModalHeader}>
            <Text style={styles.qaModalTitle}>Ask About Enneagram</Text>
            <TouchableOpacity onPress={() => setShowQAModal(false)}>
              <Ionicons name="close" size={24} color={Colors.textSecondary} />
            </TouchableOpacity>
          </View>
          
          {/* Answer Area */}
          {qaAnswer && (
            <View style={styles.qaAnswerContainer}>
              <ScrollView style={styles.qaAnswerScroll} showsVerticalScrollIndicator={false}>
                <Text style={styles.qaAnswerText}>{qaAnswer}</Text>
              </ScrollView>
            </View>
          )}
          
          {qaLoading && (
            <View style={styles.qaLoadingContainer}>
              <ActivityIndicator size="small" color={Colors.textSecondary} />
              <Text style={styles.qaLoadingText}>Searching book knowledge...</Text>
            </View>
          )}
          
          {/* Input Area */}
          <View style={styles.qaInputContainer}>
            <TextInput
              style={styles.qaInput}
              value={qaQuestion}
              onChangeText={setQaQuestion}
              placeholder="Ask about your type, patterns, or the Enneagram..."
              placeholderTextColor={Colors.textTertiary}
              multiline
              maxLength={500}
              editable={!qaLoading}
            />
            <TouchableOpacity 
              style={[
                styles.qaSendButton,
                (!qaQuestion.trim() || qaLoading) && styles.qaSendButtonDisabled
              ]}
              onPress={() => handleAskQuestion()}
              disabled={!qaQuestion.trim() || qaLoading}
            >
              <Ionicons 
                name="send" 
                size={18} 
                color={(!qaQuestion.trim() || qaLoading) ? Colors.textTertiary : Colors.background} 
              />
            </TouchableOpacity>
          </View>
          
          <Text style={styles.qaDisclaimer}>
            Answers are drawn from Enneagram literature. Use as reflection, not prescription.
          </Text>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );

  // ============================================
  // DEBUG WING STATE OVERRIDE PANEL
  // ============================================
  // Renders ONLY when DEBUG_MIRROR_ENV === true
  // Allows visual verification of all 4 wing display states
  // ============================================
  const renderDebugWingOverridePanel = () => {
    if (!DEBUG_MIRROR_ENV) return null;
    
    const debugWingStates: DebugWingState[] = ['off', 'dominant', 'leaning', 'balanced', 'not_clear'];
    
    return (
      <View style={styles.debugWingPanel}>
        {/* DEBUG BADGE */}
        <View style={styles.debugBadgeRow}>
          <Ionicons name="bug-outline" size={14} color="#FF6B6B" />
          <Text style={styles.debugBadgeLabel}>DEBUG — Wing State Override</Text>
        </View>
        
        {/* Toggle Buttons */}
        <View style={styles.debugToggleRow}>
          {debugWingStates.map((state) => (
            <TouchableOpacity
              key={state}
              style={[
                styles.debugToggleBtn,
                debugWingState === state && styles.debugToggleBtnActive,
              ]}
              onPress={() => setDebugWingState(state)}
            >
              <Text style={[
                styles.debugToggleBtnText,
                debugWingState === state && styles.debugToggleBtnTextActive,
              ]}>
                {DEBUG_WING_STATE_LABELS[state]}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
        
        {/* Mock indicator */}
        {debugWingState !== 'off' && (
          <View style={styles.debugMockAlert}>
            <Ionicons name="information-circle" size={14} color="#FFB800" />
            <Text style={styles.debugMockAlertText}>
              Showing MOCK: {DEBUG_WING_STATE_LABELS[debugWingState]}
            </Text>
          </View>
        )}
      </View>
    );
  };

  // ============================================
  // DEBUG WATERMARK (visible only with ?debug=1)
  // ============================================
  const renderDebugWatermark = () => {
    if (!isDebugMode) return null;
    
    const deepDiveEndpoint = `${API_BASE_URL}/api/enneagram/deep-dive/${userId}`;
    
    return (
      <View style={styles.debugWatermark}>
        <Text style={styles.debugWatermarkTitle}>🔍 ENNEAGRAM DEBUG WATERMARK</Text>
        
        <Text style={styles.debugWatermarkLabel}>FRONTEND_BUILD_ID:</Text>
        <Text style={styles.debugWatermarkValue}>{BUILD_ID}</Text>
        
        <Text style={styles.debugWatermarkLabel}>BUILD_VERSION:</Text>
        <Text style={styles.debugWatermarkValue}>{BUILD_VERSION}</Text>
        
        <Text style={styles.debugWatermarkLabel}>API_BASE_URL:</Text>
        <Text style={styles.debugWatermarkValue}>{API_BASE_URL}</Text>
        
        <Text style={styles.debugWatermarkLabel}>ENNEAGRAM_DEEP_DIVE_ENDPOINT:</Text>
        <Text style={styles.debugWatermarkValue}>{deepDiveEndpoint}</Text>
        
        <Text style={styles.debugWatermarkLabel}>BACKEND_HEALTH:</Text>
        {backendHealth ? (
          <>
            <Text style={styles.debugWatermarkValue}>build: {backendHealth.build}</Text>
            <Text style={styles.debugWatermarkValue}>env: {backendHealth.env}</Text>
            <Text style={styles.debugWatermarkValue}>git_sha: {backendHealth.git_sha}</Text>
            <Text style={styles.debugWatermarkValue}>db_name: {backendHealth.db_name}</Text>
          </>
        ) : (
          <Text style={styles.debugWatermarkValue}>Loading...</Text>
        )}
        
        {rawDeepDiveTypeLabel && (
          <>
            <Text style={styles.debugWatermarkLabel}>RAW_TYPE_LABEL (from API):</Text>
            <Text style={[
              styles.debugWatermarkValue,
              rawDeepDiveTypeLabel.includes('wbalanced') && styles.debugWatermarkError
            ]}>
              {rawDeepDiveTypeLabel}
              {rawDeepDiveTypeLabel.includes('wbalanced') && ' ⚠️ BUG!'}
            </Text>
            
            <Text style={styles.debugWatermarkLabel}>NORMALIZED_LABEL (UI):</Text>
            <Text style={styles.debugWatermarkValue}>{wingInfo.typeLabel}</Text>
          </>
        )}
      </View>
    );
  };

  // ============================================
  // MAIN RENDER
  // ============================================

  return (
    <View style={styles.container}>
      {renderTabs()}
      
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Debug Watermark - only shows with ?debug=1 */}
        {renderDebugWatermark()}
        
        {/* Debug Wing Override Panel - only shows when DEBUG_MIRROR_ENV=true */}
        {renderDebugWingOverridePanel()}
        
        {activeTab === 'summary' && renderSummaryTab()}
        {activeTab === 'today' && renderTodayTab()}
        {activeTab === 'deep_dive' && renderDeepDiveTab()}
        
        <View style={styles.bottomSpacer} />
      </ScrollView>
      
      {renderRetakeModal()}
      {renderQAModal()}
    </View>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
  },
  bottomSpacer: {
    height: 40,
  },

  // ============================================
  // DEBUG ENV STAMP STYLES (Task A diagnostic)
  // ============================================
  debugStamp: {
    backgroundColor: '#0a0a14',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#00FF00',
  },
  debugStampTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#00FF00',
    marginBottom: 8,
  },
  debugStampSection: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#00FFFF',
    marginTop: 6,
    marginBottom: 2,
  },
  debugStampText: {
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#00FF00',
    marginBottom: 1,
  },
  
  // ============================================
  // LAYOUT VERSION BADGE (PART B - debug only)
  // ============================================
  layoutVersionBadge: {
    backgroundColor: '#4ade80',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 12,
    alignSelf: 'flex-start',
  },
  layoutVersionText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#000',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  layoutVersionSubtext: {
    fontSize: 10,
    color: '#166534',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginTop: 2,
  },

  // ============================================
  // DEBUG WING OVERRIDE PANEL STYLES
  // ============================================
  debugWingPanel: {
    backgroundColor: '#1a1a2e',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#FF6B6B',
    borderStyle: 'dashed',
  },
  debugBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginBottom: 12,
  },
  debugBadgeLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FF6B6B',
    letterSpacing: 0.5,
  },
  debugToggleRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    justifyContent: 'center',
  },
  debugToggleBtn: {
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 6,
    backgroundColor: '#2d2d44',
    borderWidth: 1,
    borderColor: '#3d3d5c',
  },
  debugToggleBtnActive: {
    backgroundColor: '#4CAF50',
    borderColor: '#4CAF50',
  },
  debugToggleBtnText: {
    fontSize: 11,
    fontWeight: '500',
    color: '#aaaacc',
  },
  debugToggleBtnTextActive: {
    color: '#ffffff',
    fontWeight: '600',
  },
  debugMockAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 10,
    padding: 8,
    backgroundColor: 'rgba(255, 184, 0, 0.15)',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 184, 0, 0.3)',
  },
  debugMockAlertText: {
    fontSize: 11,
    color: '#FFB800',
  },

  // Tabs
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  tab: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: Colors.text,
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textTertiary,
  },
  activeTabText: {
    color: Colors.text,
  },

  // Hero Card
  heroCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  heroBadge: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  heroBadgeText: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.background,
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
  },
  heroSubtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginBottom: 12,
  },
  heroHelperText: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 8,
    marginBottom: 4,
    paddingHorizontal: 12,
  },
  heroDisclaimer: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 8,
    fontStyle: 'italic',
  },

  // Cards
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  cardSubtitle: {
    fontSize: 13,
    color: Colors.textTertiary,
    marginBottom: 12,
  },
  cardBody: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  cardNote: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textTertiary,
    marginTop: 12,
    fontStyle: 'italic',
  },

  // Wing Row
  wingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  wingItem: {
    flex: 1,
    alignItems: 'center',
  },
  wingDivider: {
    width: 1,
    height: 32,
    backgroundColor: Colors.border,
  },
  wingLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 4,
  },
  wingValue: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },

  // Candidates
  candidateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  candidateRank: {
    width: 24,
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
  },
  candidateType: {
    flex: 1,
    fontSize: 14,
    color: Colors.text,
  },
  candidatePercent: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },

  // CTA Row
  ctaRow: {
    gap: 12,
    marginTop: 8,
  },
  ctaButtonPrimary: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  ctaButtonPrimaryText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.background,
  },
  ctaButtonSecondary: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  ctaButtonSecondaryText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },

  // Energy Buttons (Today tab)
  energyButtons: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
  },
  energyButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  energyButtonSelected: {
    backgroundColor: Colors.text,
    borderColor: Colors.text,
  },
  energyButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
  },
  energyButtonTextSelected: {
    color: Colors.background,
  },

  // Practice Card
  practiceCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 20,
    marginBottom: 12,
  },
  practiceLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  practiceBody: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
  },

  // Prompt Card
  promptCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    borderLeftWidth: 3,
    borderLeftColor: Colors.text,
  },
  promptLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  promptBody: {
    fontSize: 16,
    lineHeight: 24,
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

  // Pattern Rows (Deep Dive)
  patternRow: {
    marginBottom: 14,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  patternLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textTertiary,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  patternValue: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.text,
  },

  // Wing Flight Row
  wingFlightRow: {
    flexDirection: 'row',
    marginTop: 16,
    gap: 12,
  },
  wingFlightItem: {
    flex: 1,
    backgroundColor: Colors.background,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  wingFlightLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 4,
  },
  wingFlightValue: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.text,
  },

  // Mastery Toggle
  masteryToggle: {
    flexDirection: 'row',
    backgroundColor: Colors.background,
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  masteryButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  masteryButtonSelected: {
    backgroundColor: Colors.text,
  },
  masteryButtonText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  masteryButtonTextSelected: {
    color: Colors.background,
  },
  masteryDescription: {
    backgroundColor: Colors.background,
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  masteryDescriptionText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.text,
    textAlign: 'center',
  },

  // Verification
  verificationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  verificationType: {
    fontSize: 14,
    color: Colors.text,
  },
  verificationPercent: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  retakeLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 16,
    paddingVertical: 8,
  },
  retakeLinkText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },

  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: Colors.background,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  modalText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 24,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalCancelButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  modalCancelText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },
  modalConfirmButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: Colors.text,
    borderRadius: 10,
  },
  modalConfirmText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.background,
  },
  
  // Chat Box
  chatContainer: {
    marginTop: 16,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  chatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
    backgroundColor: Colors.surfaceLight,
  },
  chatHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  chatHeaderText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  chatBody: {
    padding: 14,
    paddingTop: 8,
  },
  chatMessages: {
    marginBottom: 12,
    maxHeight: 300,
  },
  chatMessage: {
    marginBottom: 10,
    padding: 12,
    borderRadius: 10,
    maxWidth: '90%',
  },
  chatMessageUser: {
    alignSelf: 'flex-end',
    backgroundColor: Colors.text,
  },
  chatMessageAssistant: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chatMessageText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.text,
  },
  chatMessageTextUser: {
    color: Colors.background,
  },
  chatInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
  },
  chatInput: {
    flex: 1,
    backgroundColor: Colors.background,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    fontSize: 14,
    maxHeight: 100,
    color: Colors.text,
  },
  chatSendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chatSendButtonDisabled: {
    backgroundColor: Colors.border,
  },
  
  // Daily Micro-Lesson Card
  microLessonCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 12,
  },
  microLessonHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  microLessonTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 2,
  },
  microLessonSubtitle: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  microLessonBody: {
    marginBottom: 14,
  },
  microLessonBodyText: {
    fontSize: 15,
    lineHeight: 23,
    color: Colors.textSecondary,
  },
  microLessonBoldText: {
    fontWeight: '600',
    color: Colors.text,
  },
  microLessonFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  microLessonRotates: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  microLessonRotatesText: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
  microLessonAskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: Colors.surfaceLight,
  },
  microLessonAskText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.text,
  },

  // Enneagram Structure Card (Deep Dive)
  structureCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  structureTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.2,
    textAlign: 'center',
    marginBottom: 12,
  },
  structureGrid: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  structureItem: {
    alignItems: 'center',
    paddingHorizontal: 14,
    gap: 3,
  },
  structureLabel: {
    fontSize: 10,
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  structureValue: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
  },
  structureDivider: {
    width: 1,
    height: 32,
    backgroundColor: Colors.border,
  },

  // Trait Cards Section (Deep Dive)
  traitCardsSection: {
    marginBottom: 12,
  },
  traitCardsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  traitCardsTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },
  traitCardsSourceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 10,
  },
  traitCardsSourceText: {
    fontSize: 10,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  traitCardsLoading: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  traitCard: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  traitCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 6,
  },
  traitCardBody: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textSecondary,
  },
  traitCardCitation: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 8,
    fontStyle: 'italic',
  },
  traitCardAsk: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: 4,
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  traitCardAskText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.text,
  },

  // Section Divider (before Pattern Insights)
  sectionDivider: {
    height: 1,
    backgroundColor: Colors.border,
    marginBottom: 16,
    marginTop: 4,
    opacity: 0.5,
  },

  // Q&A Modal
  qaModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  qaModalContent: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    paddingBottom: 32,
    maxHeight: '80%',
  },
  qaModalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  qaModalTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  qaAnswerContainer: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    maxHeight: 220,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  qaAnswerScroll: {
    flex: 1,
  },
  qaAnswerText: {
    fontSize: 15,
    lineHeight: 23,
    color: Colors.text,
  },
  qaLoadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 20,
  },
  qaLoadingText: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  qaInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
  },
  qaInput: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    fontSize: 14,
    maxHeight: 100,
    color: Colors.text,
  },
  qaSendButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
  },
  qaSendButtonDisabled: {
    backgroundColor: Colors.border,
  },
  qaDisclaimer: {
    fontSize: 11,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 12,
    fontStyle: 'italic',
  },

  // Deep Dive Header (Anchor)
  deepDiveHeader: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  deepDiveHeaderTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 4,
  },
  deepDiveType: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
  },
  deepDiveWingStance: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.textSecondary,
    marginBottom: 8,
  },
  deepDiveHelperText: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  deepDiveNote: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },

  // Deep Dive Sections (new template)
  loadingContainer: {
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: Colors.textTertiary,
  },
  deepDiveSection: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  deepDiveSectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 10,
  },
  deepDiveSectionBody: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.textSecondary,
  },
  closingReflection: {
    fontStyle: 'italic',
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textTertiary,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    marginTop: 8,
  },
  // Collapsible section header
  collapsibleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 4,
  },
  // Energetic Flow section styles
  energeticFlowContent: {
    marginTop: 8,
  },
  energeticFlowNote: {
    marginTop: 16,
    fontSize: 14,
    fontStyle: 'italic',
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  mirrorPromptCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 3,
    borderLeftColor: Colors.textTertiary,
  },
  mirrorPromptHeader: {
    marginBottom: 8,
  },
  mirrorPromptLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 0.5,
  },
  mirrorPromptText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
    fontStyle: 'italic',
  },

  confidenceBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: Colors.surfaceLight,
  },
  confidenceBadgeText: {
    fontSize: 11,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  confidenceText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
  },
  confidenceHigh: {
    backgroundColor: 'rgba(76, 175, 80, 0.15)',
  },
  confidenceMedium: {
    backgroundColor: 'rgba(255, 193, 7, 0.15)',
  },
  confidenceLow: {
    backgroundColor: 'rgba(158, 158, 158, 0.15)',
  },

  // Wing Section
  wingSection: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  wingSectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 10,
  },
  wingSectionBody: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textSecondary,
  },
  wingGrowthNoteText: {
    fontSize: 13,
    lineHeight: 20,
    color: Colors.textTertiary,
    marginTop: 10,
    fontStyle: 'italic',
  },
  wingAccessHint: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  wingAccessHintText: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  wingGrowthHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  wingGrowthHintText: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  
  // ============================================
  // DEBUG WATERMARK STYLES (visible with ?debug=1)
  // ============================================
  debugWatermark: {
    backgroundColor: '#1a1a2e',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#00FF00',
  },
  debugWatermarkTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#00FF00',
    marginBottom: 12,
    textAlign: 'center',
  },
  debugWatermarkLabel: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#00FFFF',
    marginTop: 8,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  debugWatermarkValue: {
    fontSize: 10,
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginLeft: 8,
  },
  debugWatermarkError: {
    color: '#FF4444',
    fontWeight: 'bold',
  },
});
