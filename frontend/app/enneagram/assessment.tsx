import React, { useState, useCallback, useMemo, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Dimensions,
  Modal,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { Ionicons } from '@expo/vector-icons';
import { saveEnneagramResult } from '../../services/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ============================================
// STATE CALIBRATION NORMALIZATION
// ============================================

// Allowed enum values for state calibration
const ALLOWED_ENERGY_STATES = ['low', 'neutral', 'high'] as const;
const ALLOWED_LIFE_CONTEXTS = ['surviving', 'managing', 'expanding'] as const;
const ALLOWED_ANSWER_FRAMES = ['best_self', 'recent_self'] as const;

type NormalizedEnergyState = typeof ALLOWED_ENERGY_STATES[number];
type NormalizedLifeContext = typeof ALLOWED_LIFE_CONTEXTS[number];
type NormalizedAnswerFrame = typeof ALLOWED_ANSWER_FRAMES[number];

interface NormalizedStateCalibration {
  energy_state: NormalizedEnergyState;
  life_context: NormalizedLifeContext;
  answer_frame: NormalizedAnswerFrame;
}

/**
 * Normalizes state calibration values to allowed enums.
 * Used for validation logging and feedback submission to keep dataset clean.
 * 
 * Normalization rules:
 * - energy_state: invalid/missing → "neutral"
 * - life_context: invalid/missing → "managing"
 * - answer_frame: invalid/missing → "best_self"
 */
function normalizeStateCalibration(state: {
  energy_state?: string | null;
  life_context?: string | null;
  answer_frame?: string | null;
} | null | undefined): NormalizedStateCalibration {
  const rawEnergy = state?.energy_state;
  const rawLifeContext = state?.life_context;
  const rawAnswerFrame = state?.answer_frame;
  
  // Normalize energy_state
  const energy_state: NormalizedEnergyState = 
    rawEnergy && ALLOWED_ENERGY_STATES.includes(rawEnergy as NormalizedEnergyState)
      ? (rawEnergy as NormalizedEnergyState)
      : 'neutral';
  
  // Normalize life_context
  const life_context: NormalizedLifeContext = 
    rawLifeContext && ALLOWED_LIFE_CONTEXTS.includes(rawLifeContext as NormalizedLifeContext)
      ? (rawLifeContext as NormalizedLifeContext)
      : 'managing';
  
  // Normalize answer_frame
  const answer_frame: NormalizedAnswerFrame = 
    rawAnswerFrame && ALLOWED_ANSWER_FRAMES.includes(rawAnswerFrame as NormalizedAnswerFrame)
      ? (rawAnswerFrame as NormalizedAnswerFrame)
      : 'best_self';
  
  return { energy_state, life_context, answer_frame };
}

// ============================================
// VALIDATION ROW LOGGER (DEV ONLY)
// ============================================

interface ValidationRowData {
  participant_id: string;
  timestamp: string;
  pred_core: number;
  pred_wing: number | 'balanced';
  pred_confidence: number;
  pred_top2: string;
  pred_top3: string;
  close_flag: boolean;
  energy_state: string;
  life_context: string;
  answer_frame: string;
}

/**
 * Formats and logs a validation row for research purposes.
 * Only logs in development builds (__DEV__ === true).
 * Returns the formatted row for reference.
 */
function logEnneagramValidationRow(
  userId: string | undefined,
  scoring: {
    inferred_core: number;
    inferred_wing: number | 'balanced';
    confidence: number;
    is_close: boolean;
    top_candidates: { type: number; probability: number }[];
  },
  stateCalibration: {
    energy_state?: string | null;
    life_context?: string | null;
    answer_frame?: string | null;
  } | null | undefined
): ValidationRowData | null {
  // Only log in development
  if (!__DEV__) {
    return null;
  }
  
  const topTypes = scoring.top_candidates
    .sort((a, b) => b.probability - a.probability)
    .map(c => c.type);
  
  // Normalize state calibration values for clean dataset
  const normalizedState = normalizeStateCalibration(stateCalibration);
  
  const row: ValidationRowData = {
    participant_id: userId || 'unknown',
    timestamp: new Date().toISOString(),
    pred_core: scoring.inferred_core,
    pred_wing: scoring.inferred_wing,
    pred_confidence: scoring.confidence,
    pred_top2: topTypes.slice(0, 2).join(','),
    pred_top3: topTypes.slice(0, 3).join(','),
    close_flag: scoring.is_close,
    energy_state: normalizedState.energy_state,
    life_context: normalizedState.life_context,
    answer_frame: normalizedState.answer_frame,
  };
  
  // Log with exact prefix format
  console.log('ENNEAGRAM_VALIDATION_ROW:', JSON.stringify(row));
  
  return row;
}

// ============================================
// SECTION DEFINITIONS
// ============================================

interface SectionConfig {
  id: string;
  title: string;
  introCopy: string;
  questionFormat: 'likert' | 'forced_choice';
}

const SECTIONS: SectionConfig[] = [
  {
    id: 'core_motivation',
    title: 'Core Motivation',
    introCopy: 'These questions focus on your core motivation — the patterns that repeat across your life.\n\nAnswer based on what feels most fundamental to you, not just how you\'ve been feeling recently.',
    questionFormat: 'likert',
  },
  {
    id: 'disambiguation',
    title: 'Disambiguation',
    introCopy: 'These questions help distinguish between patterns that often look similar on the surface.\n\nChoose the option that feels closer underneath, even if neither feels perfect.',
    questionFormat: 'forced_choice',
  },
  {
    id: 'wing_resolution',
    title: 'Wing Resolution',
    introCopy: 'These final questions refine how your core type expresses itself.\n\nThey help determine which adjacent pattern you tend to draw from more.',
    questionFormat: 'likert', // Can be mixed, but we'll use likert as base
  },
];

// ============================================
// QUESTION TYPES
// ============================================

interface LikertQuestion {
  id: string;
  text: string;
  type: 'likert';
  typeMapping: number; // Enneagram type 1-9 for scoring
}

interface ForcedChoiceQuestion {
  id: string;
  prompt: string;
  optionA: string;
  optionB: string;
  optionAType: number; // Enneagram type 1-9 for scoring
  optionBType: number; // Enneagram type 1-9 for scoring
  type: 'forced_choice';
}

// Wing question types for Section 3
interface LikertWingQuestion {
  id: string;
  coreType: number; // Which core type this wing question belongs to (1-9)
  wingSide: 'left' | 'right'; // Left wing or right wing
  text: string;
  type: 'likert_wing';
}

interface ForcedChoiceWingQuestion {
  id: string;
  coreType: number; // Which core type this wing question belongs to (1-9)
  prompt: string;
  optionA: string;
  optionB: string;
  optionAMapsTo: 'left' | 'right';
  type: 'forced_choice_wing';
}

type WingQuestion = LikertWingQuestion | ForcedChoiceWingQuestion;
type Question = LikertQuestion | ForcedChoiceQuestion | WingQuestion;

// ============================================
// SECTION 1: CORE MOTIVATION QUESTIONS (27 total)
// ============================================

const CORE_MOTIVATION_QUESTIONS: LikertQuestion[] = [
  // TYPE 1 - The Perfectionist
  {
    id: 'Q01',
    text: 'I experience a persistent inner sense that things could and should be better than they are.',
    type: 'likert',
    typeMapping: 1,
  },
  {
    id: 'Q02',
    text: 'I feel uneasy when I compromise my standards, even in small ways.',
    type: 'likert',
    typeMapping: 1,
  },
  {
    id: 'Q03',
    text: 'There is an internal pressure to correct mistakes — especially my own.',
    type: 'likert',
    typeMapping: 1,
  },

  // TYPE 2 - The Helper
  {
    id: 'Q04',
    text: 'I naturally focus on what others need, often before noticing my own.',
    type: 'likert',
    typeMapping: 2,
  },
  {
    id: 'Q05',
    text: 'Feeling appreciated or valued by others strongly affects my sense of worth.',
    type: 'likert',
    typeMapping: 2,
  },
  {
    id: 'Q06',
    text: 'I find it difficult to disengage when someone depends on me.',
    type: 'likert',
    typeMapping: 2,
  },

  // TYPE 3 - The Achiever
  {
    id: 'Q07',
    text: 'I instinctively adapt myself to what will be valued or rewarded in a given environment.',
    type: 'likert',
    typeMapping: 3,
  },
  {
    id: 'Q08',
    text: 'Achievement and visible progress strongly influence how I evaluate myself.',
    type: 'likert',
    typeMapping: 3,
  },
  {
    id: 'Q09',
    text: 'I feel driven to be effective, capable, and ahead of expectations.',
    type: 'likert',
    typeMapping: 3,
  },

  // TYPE 4 - The Individualist
  // UPDATED: Specific behavioral tradeoffs, not generic introspection
  {
    id: 'Q10',
    text: 'I would rather feel deeply understood by a few than broadly liked by many.',
    type: 'likert',
    typeMapping: 4,
  },
  {
    id: 'Q11',
    text: 'I have withdrawn from opportunities because they felt ordinary or inauthentic.',
    type: 'likert',
    typeMapping: 4,
  },
  {
    id: 'Q12',
    text: 'I sometimes envy what others have while also feeling my experience is fundamentally different from theirs.',
    type: 'likert',
    typeMapping: 4,
  },

  // TYPE 5 - The Investigator
  // UPDATED: Specific behavioral tradeoffs, not generic wisdom
  {
    id: 'Q13',
    text: 'I routinely decline social invitations to protect time for thinking or projects.',
    type: 'likert',
    typeMapping: 5,
  },
  {
    id: 'Q14',
    text: 'I delay taking action until I have gathered enough information, even when others want me to move faster.',
    type: 'likert',
    typeMapping: 5,
  },
  {
    id: 'Q15',
    text: 'I feel drained after extended interaction and need significant alone time to recover.',
    type: 'likert',
    typeMapping: 5,
  },

  // TYPE 6 - The Loyalist
  {
    id: 'Q16',
    text: 'I naturally anticipate potential problems and think through what could go wrong.',
    type: 'likert',
    typeMapping: 6,
  },
  {
    id: 'Q17',
    text: 'I seek certainty or reassurance before fully committing to decisions.',
    type: 'likert',
    typeMapping: 6,
  },
  {
    id: 'Q18',
    text: 'Trust and reliability are central concerns in how I navigate relationships and systems.',
    type: 'likert',
    typeMapping: 6,
  },

  // TYPE 7 - The Enthusiast
  // UPDATED: Pursuit/expansion framing, no avoidance language
  {
    id: 'Q19',
    text: 'I am energised by new possibilities and quickly move toward the next interesting thing.',
    type: 'likert',
    typeMapping: 7,
  },
  {
    id: 'Q20',
    text: 'I prefer to keep multiple projects or plans active so I can switch between them freely.',
    type: 'likert',
    typeMapping: 7,
  },
  {
    id: 'Q21',
    text: 'I naturally focus on what could go right and find ways to make situations more enjoyable.',
    type: 'likert',
    typeMapping: 7,
  },

  // TYPE 8 - The Challenger
  {
    id: 'Q22',
    text: 'I feel a strong need to stay in control of my life and circumstances.',
    type: 'likert',
    typeMapping: 8,
  },
  {
    id: 'Q23',
    text: 'I resist being constrained, dominated, or told what to do.',
    type: 'likert',
    typeMapping: 8,
  },
  {
    id: 'Q24',
    text: 'I respect strength and directness more than sensitivity or hesitation.',
    type: 'likert',
    typeMapping: 8,
  },

  // TYPE 9 - The Peacemaker
  {
    id: 'Q25',
    text: 'I tend to minimise conflict and smooth things over to maintain harmony.',
    type: 'likert',
    typeMapping: 9,
  },
  {
    id: 'Q26',
    text: 'I can lose touch with my own priorities by accommodating others.',
    type: 'likert',
    typeMapping: 9,
  },
  {
    id: 'Q27',
    text: 'I feel most comfortable when there is stability and little emotional tension.',
    type: 'likert',
    typeMapping: 9,
  },
];

// ============================================
// SECTION 3: WING RESOLUTION QUESTIONS
// All wing questions for all 9 core types
// Each type has 4 Likert + 2 Forced-choice = 6 questions
// ============================================

const ALL_WING_QUESTIONS: WingQuestion[] = [
  // ============================================
  // Core Type 1 (wings 9-left and 2-right)
  // ============================================
  {
    id: 'W1_01',
    coreType: 1,
    wingSide: 'left',
    text: 'I try to improve things quietly and calmly, without drawing attention.',
    type: 'likert_wing',
  },
  {
    id: 'W1_02',
    coreType: 1,
    wingSide: 'left',
    text: 'I avoid open conflict even when I\'m dissatisfied.',
    type: 'likert_wing',
  },
  {
    id: 'W1_03',
    coreType: 1,
    wingSide: 'right',
    text: 'I feel responsible for helping others improve or do the right thing.',
    type: 'likert_wing',
  },
  {
    id: 'W1_04',
    coreType: 1,
    wingSide: 'right',
    text: 'I get frustrated when others ignore guidance or standards.',
    type: 'likert_wing',
  },
  {
    id: 'W1_FC01',
    coreType: 1,
    prompt: 'Which feels closer underneath?',
    optionA: 'I improve things by staying calm and steady.',
    optionB: 'I improve things by actively helping and correcting.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W1_FC02',
    coreType: 1,
    prompt: 'Which feels closer underneath?',
    optionA: 'Harmony matters more to me than being heard.',
    optionB: 'Helping others matters more to me than staying neutral.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },

  // ============================================
  // Core Type 2 (wings 1-left and 3-right)
  // ============================================
  {
    id: 'W2_01',
    coreType: 2,
    wingSide: 'left',
    text: 'I help others because it feels morally right, not just relational.',
    type: 'likert_wing',
  },
  {
    id: 'W2_02',
    coreType: 2,
    wingSide: 'left',
    text: 'I have clear opinions about how people should behave.',
    type: 'likert_wing',
  },
  {
    id: 'W2_03',
    coreType: 2,
    wingSide: 'right',
    text: 'I enjoy being recognised as capable and valuable.',
    type: 'likert_wing',
  },
  {
    id: 'W2_04',
    coreType: 2,
    wingSide: 'right',
    text: 'Being seen as successful matters to me more than I admit.',
    type: 'likert_wing',
  },
  {
    id: 'W2_FC01',
    coreType: 2,
    prompt: 'Which feels closer underneath?',
    optionA: 'I help because it\'s the right thing to do.',
    optionB: 'I help and want my contribution to be recognised.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W2_FC02',
    coreType: 2,
    prompt: 'Which feels closer underneath?',
    optionA: 'Principles guide my helping.',
    optionB: 'Impact and results guide my helping.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },

  // ============================================
  // Core Type 3 (wings 2-left and 4-right)
  // ============================================
  {
    id: 'W3_01',
    coreType: 3,
    wingSide: 'left',
    text: 'I gain energy from being liked and appreciated.',
    type: 'likert_wing',
  },
  {
    id: 'W3_02',
    coreType: 3,
    wingSide: 'left',
    text: 'Helping others succeed enhances my own sense of success.',
    type: 'likert_wing',
  },
  {
    id: 'W3_03',
    coreType: 3,
    wingSide: 'right',
    text: 'I care deeply about being authentic, not just impressive.',
    type: 'likert_wing',
  },
  {
    id: 'W3_04',
    coreType: 3,
    wingSide: 'right',
    text: 'I\'m sensitive to feeling different or misunderstood.',
    type: 'likert_wing',
  },
  {
    id: 'W3_FC01',
    coreType: 3,
    prompt: 'Which feels closer underneath?',
    optionA: 'People connection motivates me.',
    optionB: 'Authenticity motivates me.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W3_FC02',
    coreType: 3,
    prompt: 'Which feels closer underneath?',
    optionA: 'I win by being supportive.',
    optionB: 'I win by being uniquely myself.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },

  // ============================================
  // Core Type 4 (wings 3-left and 5-right)
  // ============================================
  {
    id: 'W4_01',
    coreType: 4,
    wingSide: 'left',
    text: 'I want my uniqueness to be seen and valued.',
    type: 'likert_wing',
  },
  {
    id: 'W4_02',
    coreType: 4,
    wingSide: 'left',
    text: 'Recognition and impact matter to me more than I admit.',
    type: 'likert_wing',
  },
  {
    id: 'W4_03',
    coreType: 4,
    wingSide: 'right',
    text: 'I prefer depth and privacy over visibility.',
    type: 'likert_wing',
  },
  {
    id: 'W4_04',
    coreType: 4,
    wingSide: 'right',
    text: 'I retreat inward to process meaning and emotion.',
    type: 'likert_wing',
  },
  {
    id: 'W4_FC01',
    coreType: 4,
    prompt: 'Which feels closer underneath?',
    optionA: 'I want my uniqueness to be recognised.',
    optionB: 'I want my uniqueness to be privately understood.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W4_FC02',
    coreType: 4,
    prompt: 'Which feels closer underneath?',
    optionA: 'Visibility matters.',
    optionB: 'Depth and solitude matter.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },

  // ============================================
  // Core Type 5 (wings 4-left and 6-right)
  // ============================================
  {
    id: 'W5_01',
    coreType: 5,
    wingSide: 'left',
    text: 'My inner world feels complex, nuanced, and emotionally rich.',
    type: 'likert_wing',
  },
  {
    id: 'W5_02',
    coreType: 5,
    wingSide: 'left',
    text: 'Originality and personal meaning are essential to me.',
    type: 'likert_wing',
  },
  {
    id: 'W5_03',
    coreType: 5,
    wingSide: 'right',
    text: 'Structure, systems, and reliability help me feel steady.',
    type: 'likert_wing',
  },
  {
    id: 'W5_04',
    coreType: 5,
    wingSide: 'right',
    text: 'Clear roles and expectations reduce my stress.',
    type: 'likert_wing',
  },
  {
    id: 'W5_FC01',
    coreType: 5,
    prompt: 'Which feels closer underneath?',
    optionA: 'Meaning and originality guide me.',
    optionB: 'Structure and reliability guide me.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W5_FC02',
    coreType: 5,
    prompt: 'Which feels closer underneath?',
    optionA: 'I withdraw to preserve inner depth.',
    optionB: 'I withdraw to preserve order and certainty.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },

  // ============================================
  // Core Type 6 (wings 5-left and 7-right)
  // ============================================
  {
    id: 'W6_01',
    coreType: 6,
    wingSide: 'left',
    text: 'Analysis and preparation help me feel secure.',
    type: 'likert_wing',
  },
  {
    id: 'W6_02',
    coreType: 6,
    wingSide: 'left',
    text: 'I prefer clarity and distance over enthusiasm.',
    type: 'likert_wing',
  },
  {
    id: 'W6_03',
    coreType: 6,
    wingSide: 'right',
    text: 'I manage anxiety by staying active and optimistic.',
    type: 'likert_wing',
  },
  {
    id: 'W6_04',
    coreType: 6,
    wingSide: 'right',
    text: 'Movement and engagement calm me more than reflection.',
    type: 'likert_wing',
  },
  {
    id: 'W6_FC01',
    coreType: 6,
    prompt: 'Which feels closer underneath?',
    optionA: 'I manage fear by analysing.',
    optionB: 'I manage fear by staying upbeat and active.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W6_FC02',
    coreType: 6,
    prompt: 'Which feels closer underneath?',
    optionA: 'Preparation calms me.',
    optionB: 'Possibility calms me.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },

  // ============================================
  // Core Type 7 (wings 6-left and 8-right)
  // ============================================
  {
    id: 'W7_01',
    coreType: 7,
    wingSide: 'left',
    text: 'I feel steadier when I have trusted allies or reassurance.',
    type: 'likert_wing',
  },
  {
    id: 'W7_02',
    coreType: 7,
    wingSide: 'left',
    text: 'Uncertainty pushes me to seek support or structure.',
    type: 'likert_wing',
  },
  {
    id: 'W7_03',
    coreType: 7,
    wingSide: 'right',
    text: 'I feel most alive when I assert myself against resistance.',
    type: 'likert_wing',
  },
  {
    id: 'W7_04',
    coreType: 7,
    wingSide: 'right',
    text: 'When blocked, my instinct is to push through rather than reconsider.',
    type: 'likert_wing',
  },
  {
    id: 'W7_FC01',
    coreType: 7,
    prompt: 'Which feels closer underneath?',
    optionA: 'I worry about losing support or security.',
    optionB: 'I worry about being controlled or limited.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W7_FC02',
    coreType: 7,
    prompt: 'Which feels closer underneath?',
    optionA: 'I stabilise by planning with others.',
    optionB: 'I stabilise by taking charge.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },

  // ============================================
  // Core Type 8 (wings 7-left and 9-right)
  // ============================================
  {
    id: 'W8_01',
    coreType: 8,
    wingSide: 'left',
    text: 'I combine intensity with action and momentum.',
    type: 'likert_wing',
  },
  {
    id: 'W8_02',
    coreType: 8,
    wingSide: 'left',
    text: 'I dislike stagnation and move quickly.',
    type: 'likert_wing',
  },
  {
    id: 'W8_03',
    coreType: 8,
    wingSide: 'right',
    text: 'I prefer steady control over constant confrontation.',
    type: 'likert_wing',
  },
  {
    id: 'W8_04',
    coreType: 8,
    wingSide: 'right',
    text: 'Calm authority matters more to me than force.',
    type: 'likert_wing',
  },
  {
    id: 'W8_FC01',
    coreType: 8,
    prompt: 'Which feels closer underneath?',
    optionA: 'Momentum matters most.',
    optionB: 'Stability matters most.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W8_FC02',
    coreType: 8,
    prompt: 'Which feels closer underneath?',
    optionA: 'I lead by pushing forward.',
    optionB: 'I lead by staying grounded.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },

  // ============================================
  // Core Type 9 (wings 8-left and 1-right)
  // ============================================
  {
    id: 'W9_01',
    coreType: 9,
    wingSide: 'left',
    text: 'When pushed, I can be stubborn and quietly firm.',
    type: 'likert_wing',
  },
  {
    id: 'W9_02',
    coreType: 9,
    wingSide: 'left',
    text: 'I protect my space more strongly than people realise.',
    type: 'likert_wing',
  },
  {
    id: 'W9_03',
    coreType: 9,
    wingSide: 'right',
    text: 'I feel tension when things are imperfect or unfair.',
    type: 'likert_wing',
  },
  {
    id: 'W9_04',
    coreType: 9,
    wingSide: 'right',
    text: 'I try to be calm and correct, even internally.',
    type: 'likert_wing',
  },
  {
    id: 'W9_FC01',
    coreType: 9,
    prompt: 'Which feels closer underneath?',
    optionA: 'I keep peace by holding my ground quietly.',
    optionB: 'I keep peace by staying principled and correct.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
  {
    id: 'W9_FC02',
    coreType: 9,
    prompt: 'Which feels closer underneath?',
    optionA: 'I resist pressure by becoming firm.',
    optionB: 'I resist pressure by becoming precise.',
    optionAMapsTo: 'left',
    type: 'forced_choice_wing',
  },
];

// Helper function to get wing questions for a specific core type
const getWingQuestionsForType = (coreType: number): WingQuestion[] => {
  return ALL_WING_QUESTIONS.filter(q => q.coreType === coreType);
};

// ============================================
// SECTION QUESTIONS
// ============================================

// Section 2: Disambiguation Questions (9 total - UPDATED v2)
// FC multiplier reduced from 1.5 to 1.0
// FC01-FC03 rewritten to use expansion framing for Type 7
// FC07-FC09 added for 7/8/3/6 cluster discrimination
const DISAMBIGUATION_QUESTIONS: ForcedChoiceQuestion[] = [
  // FC01-FC03: Type 7 disambiguation with EXPANSION framing (not avoidance)
  {
    id: 'FC01',
    prompt: 'Which feels closer underneath?',
    optionA: 'I pursue many experiences because the world is full of exciting possibilities.',
    optionB: 'I pursue goals strategically because success opens doors and earns respect.',
    optionAType: 7,
    optionBType: 3,
    type: 'forced_choice',
  },
  {
    id: 'FC02',
    prompt: 'Which feels closer underneath?',
    optionA: 'I generate enthusiasm and momentum to expand what is possible.',
    optionB: 'I think carefully and prepare so I am ready for whatever comes.',
    optionAType: 7,
    optionBType: 6,
    type: 'forced_choice',
  },
  {
    id: 'FC03',
    prompt: 'Which feels closer underneath?',
    optionA: 'I move quickly toward new opportunities and enjoy the variety.',
    optionB: 'I take charge directly and make things happen through force of will.',
    optionAType: 7,
    optionBType: 8,
    type: 'forced_choice',
  },
  // FC04-FC06: Original discrimination items (kept)
  {
    id: 'FC04',
    prompt: 'Which feels closer underneath?',
    optionA: 'I withdraw to preserve energy and understanding.',
    optionB: 'I tighten control to correct what feels wrong.',
    optionAType: 5,
    optionBType: 1,
    type: 'forced_choice',
  },
  {
    id: 'FC05',
    prompt: 'Which feels closer underneath?',
    optionA: 'I focus on winning approval through performance.',
    optionB: 'I focus on asserting power and independence.',
    optionAType: 3,
    optionBType: 8,
    type: 'forced_choice',
  },
  {
    id: 'FC06',
    prompt: 'Which feels closer underneath?',
    optionA: 'I stay connected by being useful and supportive.',
    optionB: 'I stay connected by maintaining harmony and avoiding friction.',
    optionAType: 2,
    optionBType: 9,
    type: 'forced_choice',
  },
  // FC07-FC09: NEW - 7/8/3/6 cluster discrimination
  {
    id: 'FC07',
    prompt: 'Which feels closer underneath?',
    optionA: 'I dislike being limited by rules and prefer to follow my own instincts.',
    optionB: 'I appreciate clear guidelines and feel uneasy when expectations are vague.',
    optionAType: 8,
    optionBType: 6,
    type: 'forced_choice',
  },
  {
    id: 'FC08',
    prompt: 'Which feels closer underneath?',
    optionA: 'I am more motivated by the excitement of starting things than finishing them.',
    optionB: 'I am more motivated by completing things and seeing measurable results.',
    optionAType: 7,
    optionBType: 3,
    type: 'forced_choice',
  },
  {
    id: 'FC09',
    prompt: 'Which feels closer underneath?',
    optionA: 'When challenged, I push back and assert my position directly.',
    optionB: 'When challenged, I consider multiple angles before responding.',
    optionAType: 8,
    optionBType: 6,
    type: 'forced_choice',
  },
];

const SECTION_QUESTIONS: { [key: string]: Question[] } = {
  core_motivation: CORE_MOTIVATION_QUESTIONS,
  disambiguation: DISAMBIGUATION_QUESTIONS,
  wing_resolution: [
    // Placeholder - will be replaced with actual questions
  ],
};

// ============================================
// LIKERT SCALE OPTIONS
// ============================================

const LIKERT_OPTIONS = [
  { value: 1, label: 'Strongly Disagree' },
  { value: 2, label: 'Disagree' },
  { value: 3, label: 'Neutral' },
  { value: 4, label: 'Agree' },
  { value: 5, label: 'Strongly Agree' },
];

// ============================================
// TYPES FOR RESPONSES
// ============================================

export interface LikertResponse {
  questionId: string;
  value: number; // 1-5
}

export interface ForcedChoiceResponse {
  questionId: string;
  choice: 'A' | 'B';
}

export interface StateCalibration {
  energy_state: 'low' | 'neutral' | 'high' | null;
  life_context: 'surviving' | 'managing' | 'expanding' | null;
  answer_frame: 'best_self' | 'recent_self' | null;
}

export interface AssessmentResponses {
  core_motivation: LikertResponse[];
  disambiguation: ForcedChoiceResponse[];
  wing_resolution: (LikertResponse | ForcedChoiceResponse)[];
}

// Scoring result types
export interface ScoringResult {
  inferred_core: number;
  inferred_wing: number | 'balanced';
  confidence: number;
  confidence_tier: 'high' | 'medium' | 'low';
  is_close: boolean;
  top_candidates: { type: number; probability: number }[];
  raw_scores: { [key: string]: number };
  z_scores: { [key: string]: number };
  wing_scores: { left: number; right: number; diff: number };
  // Extended debug data (v2)
  mean_likert: { [key: string]: number };
  forced_hits: { [key: string]: number };
  probabilities: { [key: string]: number };
  // Wing access flags (v2)
  wing_access: {
    left_type: number;
    right_type: number;
    left_accessible: boolean;
    right_accessible: boolean;
    dominant_wing: number | 'balanced' | 'none';
  };
}

// ============================================
// COMPONENT
// ============================================

export default function EnneagramAssessment() {
  const router = useRouter();
  const { user } = useAppStore();
  
  // Navigation state
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showSectionIntro, setShowSectionIntro] = useState(true);
  const [showInterpretingScreen, setShowInterpretingScreen] = useState(false);
  const [showStateCalibration, setShowStateCalibration] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Response storage
  const [responses, setResponses] = useState<AssessmentResponses>({
    core_motivation: [],
    disambiguation: [],
    wing_resolution: [],
  });
  
  // State calibration
  const [stateCalibration, setStateCalibration] = useState<StateCalibration>({
    energy_state: null,
    life_context: null,
    answer_frame: null,
  });
  
  // Guard to prevent duplicate validation row logs
  const hasLoggedValidationRowRef = useRef(false);
  
  // ============================================
  // SCORING ALGORITHM (v2 - Updated)
  // Changes:
  // - FC multiplier reduced from 1.5 → 1.0
  // - New confidence tier rules with gap thresholds
  // - Non-collapsing wing access logic
  // - Extended debug data output
  // ============================================
  
  // Compute full scoring (call after all sections complete)
  const computeFullScoring = useCallback((): ScoringResult => {
    // Step 1: Compute mean Likert scores per type (Section 1)
    const typeLikertScores: { [key: number]: number[] } = {
      1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [],
    };
    
    responses.core_motivation.forEach(response => {
      const question = CORE_MOTIVATION_QUESTIONS.find(q => q.id === response.questionId);
      if (question) {
        typeLikertScores[question.typeMapping].push(response.value);
      }
    });
    
    const meanLikert: { [key: number]: number } = {};
    const meanLikertOutput: { [key: string]: number } = {};
    for (let t = 1; t <= 9; t++) {
      const scores = typeLikertScores[t];
      meanLikert[t] = scores.length > 0 
        ? scores.reduce((sum, v) => sum + v, 0) / scores.length 
        : 0;
      meanLikertOutput[String(t)] = Math.round(meanLikert[t] * 100) / 100;
    }
    
    // Step 2: Count forced-choice hits (Section 2)
    const forcedHits: { [key: number]: number } = {
      1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0,
    };
    const forcedHitsOutput: { [key: string]: number } = {};
    
    responses.disambiguation.forEach(response => {
      const question = DISAMBIGUATION_QUESTIONS.find(q => q.id === response.questionId);
      if (question) {
        const selectedType = response.choice === 'A' ? question.optionAType : question.optionBType;
        forcedHits[selectedType]++;
      }
    });
    
    for (let t = 1; t <= 9; t++) {
      forcedHitsOutput[String(t)] = forcedHits[t];
    }
    
    // Step 3: Compute raw scores (UPDATED: multiplier 1.5 → 1.0)
    const FC_MULTIPLIER = 1.0; // Changed from 1.5
    const rawScores: { [key: string]: number } = {};
    for (let t = 1; t <= 9; t++) {
      rawScores[String(t)] = meanLikert[t] + (FC_MULTIPLIER * forcedHits[t]);
    }
    
    // Step 4: Z-score normalization
    const rawValues = Object.values(rawScores);
    const mean = rawValues.reduce((a, b) => a + b, 0) / rawValues.length;
    const variance = rawValues.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / rawValues.length;
    const stddev = Math.sqrt(variance) || 1;
    
    const zScores: { [key: string]: number } = {};
    for (let t = 1; t <= 9; t++) {
      zScores[String(t)] = Math.round(((rawScores[String(t)] - mean) / stddev) * 100) / 100;
    }
    
    // Step 5: Softmax to probabilities
    const expValues = Object.values(zScores).map(z => Math.exp(z));
    const sumExp = expValues.reduce((a, b) => a + b, 0);
    
    const probabilities: { type: number; probability: number }[] = [];
    const probabilitiesOutput: { [key: string]: number } = {};
    for (let t = 1; t <= 9; t++) {
      const prob = Math.exp(zScores[String(t)]) / sumExp;
      probabilities.push({ type: t, probability: prob });
      probabilitiesOutput[String(t)] = Math.round(prob * 10000) / 10000;
    }
    
    // Sort by probability descending
    probabilities.sort((a, b) => b.probability - a.probability);
    
    const inferred_core = probabilities[0].type;
    const topProb = probabilities[0].probability;
    const secondProb = probabilities.length >= 2 ? probabilities[1].probability : 0;
    const gap = topProb - secondProb;
    
    // UPDATED: New confidence tier rules with gap thresholds
    // High: top >= 0.45 AND gap >= 0.15
    // Medium: top >= 0.33 AND gap >= 0.08
    // Low: otherwise
    let confidence_tier: 'high' | 'medium' | 'low';
    if (topProb >= 0.45 && gap >= 0.15) {
      confidence_tier = 'high';
    } else if (topProb >= 0.33 && gap >= 0.08) {
      confidence_tier = 'medium';
    } else {
      confidence_tier = 'low';
    }
    
    const is_close = gap < 0.08;
    const top_candidates = probabilities.slice(0, 3);
    
    // Step 6: Wing scoring with NON-COLLAPSING access rules
    const leftWing = inferred_core === 1 ? 9 : inferred_core - 1;
    const rightWing = inferred_core === 9 ? 1 : inferred_core + 1;
    
    const wingQuestions = getWingQuestionsForType(inferred_core);
    
    let leftLikertSum = 0, leftLikertCount = 0;
    let rightLikertSum = 0, rightLikertCount = 0;
    let leftForcedHits = 0, rightForcedHits = 0;
    
    responses.wing_resolution.forEach(response => {
      const question = wingQuestions.find(q => q.id === response.questionId);
      if (!question) return;
      
      if (question.type === 'likert_wing') {
        const likertQ = question as LikertWingQuestion;
        const likertR = response as LikertResponse;
        if (likertQ.wingSide === 'left') {
          leftLikertSum += likertR.value;
          leftLikertCount++;
        } else {
          rightLikertSum += likertR.value;
          rightLikertCount++;
        }
      } else if (question.type === 'forced_choice_wing') {
        const fcQ = question as ForcedChoiceWingQuestion;
        const fcR = response as ForcedChoiceResponse;
        const selected = fcR.choice === 'A' ? fcQ.optionAMapsTo : (fcQ.optionAMapsTo === 'left' ? 'right' : 'left');
        if (selected === 'left') leftForcedHits++;
        else rightForcedHits++;
      }
    });
    
    const leftMean = leftLikertCount > 0 ? leftLikertSum / leftLikertCount : 0;
    const rightMean = rightLikertCount > 0 ? rightLikertSum / rightLikertCount : 0;
    
    // UPDATED: Wing FC multiplier also reduced to 1.0 (from 1.25)
    const WING_FC_MULTIPLIER = 1.0;
    const wing_left_score = leftMean + (WING_FC_MULTIPLIER * leftForcedHits);
    const wing_right_score = rightMean + (WING_FC_MULTIPLIER * rightForcedHits);
    const wing_diff = Math.abs(wing_left_score - wing_right_score);
    
    // UPDATED: Normalize wing scores to 0-1 range for access threshold calculation
    // Max possible: 5 (likert max) + 2 (max FC hits) = 7
    const maxWingScore = 7;
    const normalizedLeft = wing_left_score / maxWingScore;
    const normalizedRight = wing_right_score / maxWingScore;
    
    // Wing access rules:
    // - Accessible if normalized score >= 0.20
    // - Dominant if >= 0.25 AND difference >= 0.07
    const LEFT_ACCESSIBLE = normalizedLeft >= 0.20;
    const RIGHT_ACCESSIBLE = normalizedRight >= 0.20;
    
    let inferred_wing: number | 'balanced' | null;
    let dominant_wing: number | 'balanced' | 'none' | null;
    
    const normalizedDiff = Math.abs(normalizedLeft - normalizedRight);
    
    // ROBUSTNESS FIX: Check if we have valid wing data
    // If both scores are 0 or very close to 0, we don't have enough data
    const hasWingData = (wing_left_score > 0.1) || (wing_right_score > 0.1);
    
    if (!hasWingData) {
      // No wing data available - cannot determine wing
      inferred_wing = null;
      dominant_wing = null;
      console.log('[EnneagramScoring] Wing calculation: No wing data (scores too low), setting wing=null');
    } else if (normalizedDiff < 0.07) {
      // Both wings have data AND are balanced - this is a TRUE "balanced" result
      inferred_wing = 'balanced';
      dominant_wing = 'balanced';
      console.log('[EnneagramScoring] Wing calculation: Balanced (diff < 0.07 with valid data)');
    } else if (normalizedLeft >= 0.25 && normalizedLeft > normalizedRight) {
      inferred_wing = leftWing;
      dominant_wing = leftWing;
      console.log(`[EnneagramScoring] Wing calculation: Left wing ${leftWing} dominant`);
    } else if (normalizedRight >= 0.25 && normalizedRight > normalizedLeft) {
      inferred_wing = rightWing;
      dominant_wing = rightWing;
      console.log(`[EnneagramScoring] Wing calculation: Right wing ${rightWing} dominant`);
    } else {
      // Has data but neither wing is dominant enough
      inferred_wing = 'balanced';
      dominant_wing = 'none';
      console.log('[EnneagramScoring] Wing calculation: Neither dominant enough, balanced');
    }
    
    return {
      inferred_core,
      inferred_wing,
      confidence: topProb,
      confidence_tier: !hasWingData ? 'low' : confidence_tier, // Reduce confidence if no wing data
      is_close,
      top_candidates,
      raw_scores: rawScores,
      z_scores: zScores,
      wing_scores: {
        left: Math.round(wing_left_score * 100) / 100,
        right: Math.round(wing_right_score * 100) / 100,
        diff: Math.round(wing_diff * 100) / 100,
        // ENHANCED DEBUG: Explicit wing type mapping
        left_type: leftWing,
        right_type: rightWing,
        has_wing_data: hasWingData
      },
      // Extended debug data (v2)
      mean_likert: meanLikertOutput,
      forced_hits: forcedHitsOutput,
      probabilities: probabilitiesOutput,
      wing_access: {
        left_type: leftWing,
        right_type: rightWing,
        left_accessible: LEFT_ACCESSIBLE,
        right_accessible: RIGHT_ACCESSIBLE,
        dominant_wing: dominant_wing
      }
    };
  }, [responses]);
  
  // ============================================
  // COMPUTE INFERRED CORE TYPE FOR WING RESOLUTION
  // ============================================
  // Calculate average scores per type from Section 1 responses
  const computeInferredCoreType = useCallback((): number => {
    const typeScores: { [key: number]: number[] } = {
      1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [], 8: [], 9: [],
    };
    
    // Group responses by type
    responses.core_motivation.forEach(response => {
      const question = CORE_MOTIVATION_QUESTIONS.find(q => q.id === response.questionId);
      if (question) {
        typeScores[question.typeMapping].push(response.value);
      }
    });
    
    // Calculate averages and find highest
    let highestAvg = 0;
    let inferredType = 1;
    
    for (let type = 1; type <= 9; type++) {
      const scores = typeScores[type];
      if (scores.length > 0) {
        const avg = scores.reduce((sum, val) => sum + val, 0) / scores.length;
        if (avg > highestAvg) {
          highestAvg = avg;
          inferredType = type;
        }
      }
    }
    
    return inferredType;
  }, [responses.core_motivation]);
  
  // Get the inferred core type (computed when entering Section 3)
  const inferredCoreTypeForWing = computeInferredCoreType();
  
  // Get wing questions dynamically based on inferred core type
  const wingQuestionsForInferredType = getWingQuestionsForType(inferredCoreTypeForWing);
  
  // Get current section and questions (dynamic for wing_resolution)
  const currentSection = SECTIONS[currentSectionIndex];
  const currentSectionQuestions = currentSection.id === 'wing_resolution' 
    ? wingQuestionsForInferredType 
    : (SECTION_QUESTIONS[currentSection.id] || []);
  const currentQuestion = currentSectionQuestions[currentQuestionIndex];
  
  // Calculate overall progress (accounting for dynamic wing questions)
  const section1Count = SECTION_QUESTIONS.core_motivation.length;
  const section2Count = SECTION_QUESTIONS.disambiguation.length;
  const section3Count = wingQuestionsForInferredType.length;
  const totalQuestions = section1Count + section2Count + section3Count;
  
  const completedQuestions = 
    responses.core_motivation.length + 
    responses.disambiguation.length + 
    responses.wing_resolution.length;
  const overallProgress = totalQuestions > 0 
    ? (completedQuestions / totalQuestions) * 100 
    : 0;
  
  // Handle Likert response (for both regular and wing questions)
  const handleLikertResponse = useCallback((value: number) => {
    if (!currentQuestion || (currentQuestion.type !== 'likert' && currentQuestion.type !== 'likert_wing')) return;
    
    const newResponse: LikertResponse = {
      questionId: currentQuestion.id,
      value,
    };
    
    setResponses(prev => ({
      ...prev,
      [currentSection.id]: [...prev[currentSection.id as keyof AssessmentResponses], newResponse],
    }));
    
    advanceToNext();
  }, [currentQuestion, currentSection]);
  
  // Handle Forced Choice response (for both regular and wing questions)
  const handleForcedChoiceResponse = useCallback((choice: 'A' | 'B') => {
    if (!currentQuestion || (currentQuestion.type !== 'forced_choice' && currentQuestion.type !== 'forced_choice_wing')) return;
    
    const newResponse: ForcedChoiceResponse = {
      questionId: currentQuestion.id,
      choice,
    };
    
    setResponses(prev => ({
      ...prev,
      [currentSection.id]: [...prev[currentSection.id as keyof AssessmentResponses], newResponse],
    }));
    
    advanceToNext();
  }, [currentQuestion, currentSection]);
  
  // Advance to next question or section
  const advanceToNext = useCallback(() => {
    const nextQuestionIndex = currentQuestionIndex + 1;
    
    if (nextQuestionIndex < currentSectionQuestions.length) {
      // More questions in current section
      setCurrentQuestionIndex(nextQuestionIndex);
    } else {
      // Section complete
      const nextSectionIndex = currentSectionIndex + 1;
      
      if (nextSectionIndex < SECTIONS.length) {
        // Move to next section
        setCurrentSectionIndex(nextSectionIndex);
        setCurrentQuestionIndex(0);
        setShowSectionIntro(true);
      } else {
        // All questions complete - show state calibration before interpreting
        setShowStateCalibration(true);
      }
    }
  }, [currentQuestionIndex, currentSectionQuestions.length, currentSectionIndex]);
  
  // Handle state calibration completion
  const handleStateCalibrationComplete = useCallback(async () => {
    if (!stateCalibration.energy_state || !stateCalibration.life_context || !stateCalibration.answer_frame) {
      return; // All fields required
    }
    
    setShowStateCalibration(false);
    setShowInterpretingScreen(true);
    setIsSaving(true);
    
    try {
      // Compute final scoring
      const scoring = computeFullScoring();
      
      // Save to backend with extended debug data (v2)
      await saveEnneagramResult({
        user_id: user!.id,
        method: 'assessment_inference_v2', // Updated version
        version: 'v2',
        inferred_core: scoring.inferred_core,
        inferred_wing: scoring.inferred_wing,
        confidence: scoring.confidence,
        confidence_tier: scoring.confidence_tier,
        is_close: scoring.is_close,
        top_candidates: scoring.top_candidates,
        state_calibration: {
          energy_state: stateCalibration.energy_state,
          life_context: stateCalibration.life_context,
          answer_frame: stateCalibration.answer_frame
        },
        debug_scores: {
          raw_scores: scoring.raw_scores,
          z_scores: scoring.z_scores,
          wing_scores: scoring.wing_scores,
          // Extended debug data (v2)
          mean_likert: scoring.mean_likert,
          forced_hits: scoring.forced_hits,
          probabilities: scoring.probabilities,
          wing_access: scoring.wing_access
        }
      });
      
      // Log validation row for research (dev only, exactly once)
      if (!hasLoggedValidationRowRef.current) {
        hasLoggedValidationRowRef.current = true;
        logEnneagramValidationRow(
          user?.id,
          scoring,
          {
            energy_state: stateCalibration.energy_state,
            life_context: stateCalibration.life_context,
            answer_frame: stateCalibration.answer_frame
          }
        );
      }
      
      // Navigate to results after brief delay
      setTimeout(() => {
        router.replace('/enneagram/results');
      }, 2000);
    } catch (error) {
      console.error('Error saving Enneagram result:', error);
      // Still navigate to results even on error
      setTimeout(() => {
        router.replace('/enneagram/results');
      }, 2000);
    }
  }, [stateCalibration, computeFullScoring, user, router]);
  
  // Start section (from intro)
  const handleStartSection = useCallback(() => {
    setShowSectionIntro(false);
  }, []);
  
  // Go back
  const handleBack = useCallback(() => {
    if (showSectionIntro) {
      // If on section intro, go to previous section's last question
      if (currentSectionIndex > 0) {
        const prevSectionId = SECTIONS[currentSectionIndex - 1].id;
        const prevSectionQuestions = SECTION_QUESTIONS[prevSectionId] || [];
        setCurrentSectionIndex(currentSectionIndex - 1);
        setCurrentQuestionIndex(prevSectionQuestions.length - 1);
        setShowSectionIntro(false);
      } else {
        // Exit assessment
        router.back();
      }
    } else if (currentQuestionIndex > 0) {
      // Go to previous question in current section
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      // Remove last response
      setResponses(prev => {
        const sectionResponses = [...prev[currentSection.id as keyof AssessmentResponses]];
        sectionResponses.pop();
        return {
          ...prev,
          [currentSection.id]: sectionResponses,
        };
      });
    } else {
      // First question of section, show section intro
      setShowSectionIntro(true);
    }
  }, [showSectionIntro, currentSectionIndex, currentQuestionIndex, currentSection, router]);
  
  // Redirect if no user
  if (!user) {
    router.replace('/onboarding');
    return null;
  }
  
  // ============================================
  // RENDER: State Calibration Screen
  // ============================================
  if (showStateCalibration) {
    const isComplete = stateCalibration.energy_state && stateCalibration.life_context && stateCalibration.answer_frame;
    
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => setShowStateCalibration(false)} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>Final Step</Text>
          <View style={styles.headerSpacer} />
        </View>
        
        <ScrollView contentContainerStyle={styles.calibrationScrollContent}>
          <Text style={styles.calibrationTitle}>Before we interpret your results</Text>
          <Text style={styles.calibrationSubtitle}>
            These questions help us understand the context of your answers. They do not affect your score.
          </Text>
          
          {/* Energy State */}
          <View style={styles.calibrationSection}>
            <Text style={styles.calibrationLabel}>How would you describe your energy level right now?</Text>
            <View style={styles.calibrationOptions}>
              {(['low', 'neutral', 'high'] as const).map(option => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.calibrationOption,
                    stateCalibration.energy_state === option && styles.calibrationOptionSelected
                  ]}
                  onPress={() => setStateCalibration(prev => ({ ...prev, energy_state: option }))}
                >
                  <Text style={[
                    styles.calibrationOptionText,
                    stateCalibration.energy_state === option && styles.calibrationOptionTextSelected
                  ]}>
                    {option === 'low' ? 'Low' : option === 'neutral' ? 'Neutral' : 'High'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          
          {/* Life Context */}
          <View style={styles.calibrationSection}>
            <Text style={styles.calibrationLabel}>How would you describe your current life context?</Text>
            <View style={styles.calibrationOptions}>
              {(['surviving', 'managing', 'expanding'] as const).map(option => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.calibrationOption,
                    stateCalibration.life_context === option && styles.calibrationOptionSelected
                  ]}
                  onPress={() => setStateCalibration(prev => ({ ...prev, life_context: option }))}
                >
                  <Text style={[
                    styles.calibrationOptionText,
                    stateCalibration.life_context === option && styles.calibrationOptionTextSelected
                  ]}>
                    {option === 'surviving' ? 'Surviving' : option === 'managing' ? 'Managing' : 'Expanding'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          
          {/* Answer Frame */}
          <View style={styles.calibrationSection}>
            <Text style={styles.calibrationLabel}>How did you answer the questions?</Text>
            <View style={styles.calibrationOptions}>
              {(['best_self', 'recent_self'] as const).map(option => (
                <TouchableOpacity
                  key={option}
                  style={[
                    styles.calibrationOption,
                    stateCalibration.answer_frame === option && styles.calibrationOptionSelected
                  ]}
                  onPress={() => setStateCalibration(prev => ({ ...prev, answer_frame: option }))}
                >
                  <Text style={[
                    styles.calibrationOptionText,
                    stateCalibration.answer_frame === option && styles.calibrationOptionTextSelected
                  ]}>
                    {option === 'best_self' ? 'My best self' : 'How I\'ve been lately'}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
          
          <TouchableOpacity
            style={[styles.continueButton, !isComplete && styles.continueButtonDisabled]}
            onPress={handleStateCalibrationComplete}
            disabled={!isComplete}
          >
            <Text style={styles.continueButtonText}>See My Results</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Interpreting Screen
  // ============================================
  if (showInterpretingScreen) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.interpretingContainer}>
          <View style={styles.interpretingIconContainer}>
            {isSaving ? (
              <ActivityIndicator size="large" color={Colors.textSecondary} />
            ) : (
              <Ionicons name="analytics-outline" size={48} color={Colors.textSecondary} />
            )}
          </View>
          <Text style={styles.interpretingTitle}>Interpreting your responses…</Text>
          <Text style={styles.interpretingSubtext}>
            We&apos;re analyzing your patterns to identify your Enneagram type.
          </Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Section Intro
  // ============================================
  if (showSectionIntro) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <ScrollView contentContainerStyle={styles.introScrollContent}>
          <View style={styles.introContent}>
            <Text style={styles.sectionTitle}>{currentSection.title}</Text>
            <Text style={styles.introCopy}>{currentSection.introCopy}</Text>
            
            <TouchableOpacity 
              style={styles.continueButton}
              onPress={handleStartSection}
            >
              <Text style={styles.continueButtonText}>Continue</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: No Questions (placeholder state)
  // ============================================
  if (!currentQuestion) {
    // No questions defined yet - auto-advance or show placeholder
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <View style={styles.placeholderContent}>
          <Ionicons name="construct-outline" size={48} color={Colors.textTertiary} />
          <Text style={styles.placeholderTitle}>Questions Coming Soon</Text>
          <Text style={styles.placeholderText}>
            Questions for the {currentSection.title} section will be added here.
          </Text>
          
          <TouchableOpacity 
            style={styles.continueButton}
            onPress={advanceToNext}
          >
            <Text style={styles.continueButtonText}>
              {currentSectionIndex < SECTIONS.length - 1 ? 'Skip to Next Section' : 'Complete Assessment'}
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Likert Question
  // ============================================
  if (currentQuestion.type === 'likert') {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <ScrollView contentContainerStyle={styles.questionScrollContent}>
          {/* Question number */}
          <Text style={styles.questionNumber}>
            Question {currentQuestionIndex + 1} of {currentSectionQuestions.length}
          </Text>
          
          {/* Question text */}
          <Text style={styles.questionText}>
            {(currentQuestion as LikertQuestion).text}
          </Text>
          
          {/* Likert options */}
          <View style={styles.likertContainer}>
            {LIKERT_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.value}
                style={styles.likertOption}
                onPress={() => handleLikertResponse(option.value)}
                activeOpacity={0.7}
              >
                <View style={styles.likertCircle}>
                  <Text style={styles.likertValue}>{option.value}</Text>
                </View>
                <Text style={styles.likertLabel}>{option.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Forced Choice Question
  // ============================================
  if (currentQuestion.type === 'forced_choice') {
    const fcQuestion = currentQuestion as ForcedChoiceQuestion;
    
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <ScrollView contentContainerStyle={styles.questionScrollContent}>
          {/* Question number */}
          <Text style={styles.questionNumber}>
            Question {currentQuestionIndex + 1} of {currentSectionQuestions.length}
          </Text>
          
          {/* Prompt */}
          <Text style={styles.forcedChoicePrompt}>
            {fcQuestion.prompt}
          </Text>
          
          {/* Options */}
          <View style={styles.forcedChoiceContainer}>
            <TouchableOpacity
              style={styles.forcedChoiceOption}
              onPress={() => handleForcedChoiceResponse('A')}
              activeOpacity={0.7}
            >
              <View style={styles.forcedChoiceLabel}>
                <Text style={styles.forcedChoiceLetter}>A</Text>
              </View>
              <Text style={styles.forcedChoiceText}>{fcQuestion.optionA}</Text>
            </TouchableOpacity>
            
            <View style={styles.forcedChoiceDivider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.dividerLine} />
            </View>
            
            <TouchableOpacity
              style={styles.forcedChoiceOption}
              onPress={() => handleForcedChoiceResponse('B')}
              activeOpacity={0.7}
            >
              <View style={styles.forcedChoiceLabel}>
                <Text style={styles.forcedChoiceLetter}>B</Text>
              </View>
              <Text style={styles.forcedChoiceText}>{fcQuestion.optionB}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Likert Wing Question (Section 3)
  // ============================================
  if (currentQuestion.type === 'likert_wing') {
    const wingQuestion = currentQuestion as LikertWingQuestion;
    
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <ScrollView contentContainerStyle={styles.questionScrollContent}>
          {/* Question number */}
          <Text style={styles.questionNumber}>
            Question {currentQuestionIndex + 1} of {currentSectionQuestions.length}
          </Text>
          
          {/* Question text */}
          <Text style={styles.questionText}>
            {wingQuestion.text}
          </Text>
          
          {/* Likert options */}
          <View style={styles.likertContainer}>
            {LIKERT_OPTIONS.map((option) => (
              <TouchableOpacity
                key={option.value}
                style={styles.likertOption}
                onPress={() => handleLikertResponse(option.value)}
                activeOpacity={0.7}
              >
                <View style={styles.likertCircle}>
                  <Text style={styles.likertValue}>{option.value}</Text>
                </View>
                <Text style={styles.likertLabel}>{option.label}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // ============================================
  // RENDER: Forced Choice Wing Question (Section 3)
  // ============================================
  if (currentQuestion.type === 'forced_choice_wing') {
    const fcWingQuestion = currentQuestion as ForcedChoiceWingQuestion;
    
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="chevron-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.sectionIndicator}>
            Section {currentSectionIndex + 1} of {SECTIONS.length}
          </Text>
          <View style={styles.headerSpacer} />
        </View>
        
        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={[styles.progressBar, { width: `${overallProgress}%` }]} />
        </View>
        
        <ScrollView contentContainerStyle={styles.questionScrollContent}>
          {/* Question number */}
          <Text style={styles.questionNumber}>
            Question {currentQuestionIndex + 1} of {currentSectionQuestions.length}
          </Text>
          
          {/* Prompt */}
          <Text style={styles.forcedChoicePrompt}>
            {fcWingQuestion.prompt}
          </Text>
          
          {/* Options */}
          <View style={styles.forcedChoiceContainer}>
            <TouchableOpacity
              style={styles.forcedChoiceOption}
              onPress={() => handleForcedChoiceResponse('A')}
              activeOpacity={0.7}
            >
              <View style={styles.forcedChoiceLabel}>
                <Text style={styles.forcedChoiceLetter}>A</Text>
              </View>
              <Text style={styles.forcedChoiceText}>{fcWingQuestion.optionA}</Text>
            </TouchableOpacity>
            
            <View style={styles.forcedChoiceDivider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.dividerLine} />
            </View>
            
            <TouchableOpacity
              style={styles.forcedChoiceOption}
              onPress={() => handleForcedChoiceResponse('B')}
              activeOpacity={0.7}
            >
              <View style={styles.forcedChoiceLabel}>
                <Text style={styles.forcedChoiceLetter}>B</Text>
              </View>
              <Text style={styles.forcedChoiceText}>{fcWingQuestion.optionB}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // Fallback
  return null;
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    padding: 4,
    marginLeft: -4,
  },
  sectionIndicator: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  headerSpacer: {
    width: 32,
  },
  
  // Progress
  progressContainer: {
    height: 3,
    backgroundColor: Colors.border,
    marginHorizontal: 24,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: Colors.text,
    borderRadius: 2,
  },
  
  // Section Intro
  introScrollContent: {
    flexGrow: 1,
    padding: 24,
    justifyContent: 'center',
  },
  introContent: {
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 28,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 24,
    textAlign: 'center',
  },
  introCopy: {
    fontSize: 16,
    lineHeight: 26,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 40,
    paddingHorizontal: 8,
  },
  continueButton: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 48,
  },
  continueButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  
  // Question Common
  questionScrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  questionNumber: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 24,
    marginTop: 16,
  },
  questionText: {
    fontSize: 20,
    lineHeight: 30,
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 40,
    paddingHorizontal: 8,
  },
  
  // Likert Scale
  likertContainer: {
    gap: 12,
  },
  likertOption: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  likertCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  likertValue: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  likertLabel: {
    fontSize: 15,
    color: Colors.text,
    flex: 1,
  },
  
  // Forced Choice
  forcedChoicePrompt: {
    fontSize: 20,
    lineHeight: 28,
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 32,
    fontWeight: '500',
  },
  forcedChoiceContainer: {
    gap: 16,
  },
  forcedChoiceOption: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  forcedChoiceLabel: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  forcedChoiceLetter: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.text,
  },
  forcedChoiceText: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.text,
  },
  forcedChoiceDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    paddingVertical: 8,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.border,
  },
  dividerText: {
    fontSize: 13,
    color: Colors.textTertiary,
    fontWeight: '500',
  },
  
  // Placeholder State
  placeholderContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  placeholderTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  placeholderText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 32,
  },
  
  // Interpreting Screen
  interpretingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  interpretingIconContainer: {
    marginBottom: 24,
  },
  interpretingTitle: {
    fontSize: 24,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 16,
    textAlign: 'center',
  },
  interpretingSubtext: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  
  // State Calibration
  calibrationScrollContent: {
    flexGrow: 1,
    padding: 24,
  },
  calibrationTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
    marginTop: 16,
  },
  calibrationSubtitle: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 32,
  },
  calibrationSection: {
    marginBottom: 28,
  },
  calibrationLabel: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 12,
  },
  calibrationOptions: {
    flexDirection: 'row',
    gap: 10,
  },
  calibrationOption: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 8,
    borderRadius: 10,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
  },
  calibrationOptionSelected: {
    backgroundColor: Colors.text,
    borderColor: Colors.text,
  },
  calibrationOptionText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
  },
  calibrationOptionTextSelected: {
    color: Colors.background,
  },
  continueButtonDisabled: {
    backgroundColor: Colors.border,
    opacity: 0.6,
  },
});
