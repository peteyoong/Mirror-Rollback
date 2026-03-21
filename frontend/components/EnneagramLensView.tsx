import React, { useState, useEffect, useCallback } from 'react';
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
import { useTheme, ThemeColors } from '../contexts/ThemeContext';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { InlineReflectButton } from './UniversalReflectButton';
import KeystoneReferenceLink from './KeystoneReferenceLink';
import EnneagramWheel, { ENNEAGRAM_SCHEMA } from './EnneagramWheel';
import { 
  sendEnneagramChat, 
  getEnneagramTraits,
  askEnneagramQuestion,
  getEnneagramDeepDive,
  getPatternDrift,
  getEnneagramResult,
  EnneagramTraitCard,
  EnneagramComputedDetails,
  EnneagramDeepDiveSection,
  EnneagramDeepDiveResponse,
  PatternDriftResponse
} from '../services/api';

// Build info for debugging
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'unknown';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';

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

// Stress/Growth directions (Enneagram movement arrows)
const STRESS_DIRECTIONS: { [key: number]: number } = {
  1: 4, 2: 8, 3: 9, 4: 2, 5: 7, 6: 3, 7: 1, 8: 5, 9: 6,
};

const GROWTH_DIRECTIONS: { [key: number]: number } = {
  1: 7, 2: 4, 3: 6, 4: 1, 5: 8, 6: 9, 7: 5, 8: 2, 9: 3,
};

// Core needs (short labels for wheel)
const CORE_NEEDS: { [key: number]: string } = {
  1: 'Integrity',
  2: 'Connection',
  3: 'Achievement',
  4: 'Authenticity',
  5: 'Knowledge',
  6: 'Security',
  7: 'Freedom',
  8: 'Autonomy',
  9: 'Peace',
};

// Concise Core Pattern descriptions for Summary (NOT essays)
const CORE_PATTERN_CONCISE: { [key: number]: string } = {
  1: 'You move toward what feels correct, aligned, and improvable.\n\nWhen something feels wrong or out of order, your instinct is to fix it — to make it better, more right, more complete.',
  2: 'You move toward connection through giving and being needed.\n\nWhen someone seems to need support, your instinct is to offer it — anticipating, helping, making yourself valuable.',
  3: 'You move toward achievement, recognition, and presenting your best self.\n\nWhen success feels possible, your instinct is to pursue it — adapting, optimizing, showing what you can do.',
  4: 'You move toward what feels authentic, meaningful, and emotionally true.\n\nWhen life feels ordinary or flat, your instinct is to seek depth — to find what\'s missing, what\'s real, what matters.',
  5: 'You move toward understanding, clarity, and preserving your inner resources.\n\nWhen the world feels demanding, your instinct is to observe — to gather knowledge, maintain boundaries, protect your energy.',
  6: 'You move toward security, preparation, and reliable foundations.\n\nWhen uncertainty arises, your instinct is to question it — to test, plan, and find ground you can trust.',
  7: 'You move toward what feels open, interesting, and full of possibility.\n\nWhen something feels limiting or heavy, your instinct is to shift — to reframe, redirect, or find another path forward.',
  8: 'You move toward strength, directness, and protecting your autonomy.\n\nWhen control feels threatened, your instinct is to take charge — to push back, set boundaries, assert your position.',
  9: 'You move toward harmony, comfort, and maintaining inner peace.\n\nWhen conflict arises, your instinct is to smooth it over — to merge, accommodate, and keep things steady.',
};

// Hero summary sentences for each type + wing combo
const HERO_SUMMARY_SENTENCES: { [key: string]: string } = {
  '1w9': 'You move toward correctness and improvement — with added patience and steadiness from your 9 wing.',
  '1w2': 'You move toward correctness and improvement — with added warmth and care from your 2 wing.',
  '2w1': 'You move toward connection through helping — with added structure and standards from your 1 wing.',
  '2w3': 'You move toward connection through helping — with added drive and visibility from your 3 wing.',
  '3w2': 'You move toward achievement and recognition — with added warmth and people-focus from your 2 wing.',
  '3w4': 'You move toward achievement and recognition — with added depth and personal style from your 4 wing.',
  '4w3': 'You move toward authenticity and meaning — with added drive and outward expression from your 3 wing.',
  '4w5': 'You move toward authenticity and meaning — with added intellectual depth and privacy from your 5 wing.',
  '5w4': 'You move toward understanding and clarity — with added emotional sensitivity from your 4 wing.',
  '5w6': 'You move toward understanding and clarity — with added vigilance and practical application from your 6 wing.',
  '6w5': 'You move toward security and preparation — with added analytical depth from your 5 wing.',
  '6w7': 'You move toward security and preparation — with added optimism and forward energy from your 7 wing.',
  '7w6': 'You move toward possibility and stimulation — with added loyalty and groundedness from your 6 wing.',
  '7w8': 'You move toward possibility, stimulation, and freedom — with added decisiveness from your 8 wing.',
  '8w7': 'You move toward strength and autonomy — with added energy and expansiveness from your 7 wing.',
  '8w9': 'You move toward strength and autonomy — with added patience and steadiness from your 9 wing.',
  '9w8': 'You move toward harmony and peace — with added directness and backbone from your 8 wing.',
  '9w1': 'You move toward harmony and peace — with added principles and purpose from your 1 wing.',
};

// Expanded Core Story content for Summary page
const CORE_STORY_CONTENT: { [key: number]: { what: string; drives: string; tradeoff: string; helps: string } } = {
  1: {
    what: 'Type 1 is the pattern of improvement, integrity, and holding things to a higher standard. Your attention naturally moves toward what could be better, more aligned, more correct.',
    drives: 'A deep sense that things should be done right — and that you have a responsibility to make them so. This isn\'t about perfectionism for its own sake; it\'s about a genuine desire for goodness and order.',
    tradeoff: 'The inner critic that drives improvement can become relentless. The pursuit of "right" can crowd out acceptance of what already is. Resentment builds when others don\'t share your standards.',
    helps: 'Your conscientiousness creates trust. Your commitment to improvement raises the bar for everyone. Your integrity is a quiet anchor in chaotic environments.',
  },
  2: {
    what: 'Type 2 is the pattern of connection through giving, anticipating needs, and being valued for helping. Your attention naturally moves toward what others need — often before they ask.',
    drives: 'A deep sense that love is earned through giving, and that being needed is the surest path to belonging. This isn\'t manipulation; it\'s a genuine desire to matter to people.',
    tradeoff: 'Your own needs can disappear beneath the focus on others. Resentment builds when giving doesn\'t generate the recognition you expected. The help can come with invisible strings.',
    helps: 'Your attentiveness creates genuine warmth. Your ability to anticipate needs makes others feel seen. Your generosity builds bridges others can\'t.',
  },
  3: {
    what: 'Type 3 is the pattern of achievement, efficiency, and presenting yourself in the best possible light. Your attention naturally moves toward goals, outcomes, and how you\'re perceived.',
    drives: 'A deep sense that you are what you accomplish — and that being seen as successful is essential to being valued. This isn\'t vanity; it\'s a genuine drive to create and achieve.',
    tradeoff: 'The drive to succeed can disconnect you from what you actually feel. Image management can replace authenticity. The fear of failure can make slowing down feel dangerous.',
    helps: 'Your ability to get things done is real. Your adaptability helps you navigate complex environments. Your energy inspires others to raise their game.',
  },
  4: {
    what: 'Type 4 is the pattern of authenticity, depth, and finding meaning in emotional experience. Your attention naturally moves toward what feels significant, unique, or missing.',
    drives: 'A deep sense that authentic self-expression is essential — and that something meaningful is always just out of reach. This isn\'t drama; it\'s a genuine search for what\'s real.',
    tradeoff: 'The search for depth can become an attachment to melancholy. Comparing your inner life to others\' surfaces creates unnecessary pain. The extraordinary can eclipse the ordinary.',
    helps: 'Your emotional honesty creates permission for others to feel. Your aesthetic sense adds beauty to environments. Your depth reaches places others can\'t access.',
  },
  5: {
    what: 'Type 5 is the pattern of observation, understanding, and preserving inner resources. Your attention naturally moves toward knowledge, clarity, and maintaining boundaries.',
    drives: 'A deep sense that your resources — time, energy, knowledge — are limited and must be protected. This isn\'t coldness; it\'s a genuine need to understand before engaging.',
    tradeoff: 'The pull toward observation can become avoidance of participation. The pursuit of certainty can delay action indefinitely. Knowledge can substitute for connection.',
    helps: 'Your ability to see clearly without emotional distortion is rare. Your depth of understanding creates real expertise. Your independence allows you to think freely.',
  },
  6: {
    what: 'Type 6 is the pattern of vigilance, preparation, and seeking reliable ground. Your attention naturally moves toward potential risks, loyalties, and what can be trusted.',
    drives: 'A deep sense that the world requires alertness — and that security must be actively maintained. This isn\'t anxiety; it\'s a genuine desire for trustworthy foundations.',
    tradeoff: 'The scanning for threats can create the very anxiety you\'re trying to prevent. Worst-case thinking can crowd out possibility. Testing loyalty can strain the relationships you value.',
    helps: 'Your ability to anticipate problems prevents real disasters. Your loyalty creates deep, durable bonds. Your questioning mind catches what others miss.',
  },
  7: {
    what: 'Type 7 is the pattern of possibility, exploration, and staying open to positive options. Your attention naturally moves toward what could be interesting, stimulating, or enjoyable.',
    drives: 'A deep sense that freedom and possibility are essential — and that being trapped in limitation or pain must be avoided. This isn\'t escapism; it\'s a genuine appetite for life.',
    tradeoff: 'The draw toward options can prevent the satisfaction of completion. Reframing everything positively can bypass pain that needs attention. Depth requires staying when moving feels easier.',
    helps: 'Your enthusiasm is genuinely contagious. Your ability to reframe creates resilience. Your vision for possibility opens doors others don\'t see.',
  },
  8: {
    what: 'Type 8 is the pattern of strength, directness, and protecting autonomy. Your attention naturally moves toward power dynamics, control, and who can be trusted with vulnerability.',
    drives: 'A deep sense that strength is necessary for survival — and that vulnerability invites harm. This isn\'t aggression; it\'s a genuine desire to protect what matters.',
    tradeoff: 'The protection of strength can block the intimacy you actually want. Control can become domination. The denial of vulnerability can leave you isolated at the top.',
    helps: 'Your ability to take charge creates safety for others. Your directness cuts through confusion. Your strength protects those who can\'t protect themselves.',
  },
  9: {
    what: 'Type 9 is the pattern of harmony, acceptance, and maintaining inner and outer peace. Your attention naturally moves toward what creates connection and avoids disruption.',
    drives: 'A deep sense that peace must be preserved — and that your own needs can wait to maintain harmony. This isn\'t passivity; it\'s a genuine desire for calm and connection.',
    tradeoff: 'The maintenance of peace can mean the loss of yourself. Avoiding conflict can create passive resistance. Merging with others\' agendas can make your own voice disappear.',
    helps: 'Your ability to see all sides creates real mediation. Your acceptance creates space where others can be themselves. Your steadiness is an anchor in turbulent times.',
  },
};

// Wing influence descriptions (concise)
const WING_INFLUENCE_CONCISE: { [key: string]: string } = {
  '1w9': 'Your 9 wing adds patience and a preference for harmony.\n\nInstead of confronting directly, you pick battles carefully — holding principles without forcing them.',
  '1w2': 'Your 2 wing adds warmth and care for others.\n\nYour desire for improvement often shows up as wanting to help people grow and do better.',
  '2w1': 'Your 1 wing adds structure and standards.\n\nYou don\'t just help — you want to help the right way, with integrity and conscientiousness.',
  '2w3': 'Your 3 wing adds energy and visibility.\n\nYou\'re drawn to roles where care has impact — leading, organizing, being the one who makes things happen.',
  '3w2': 'Your 2 wing adds warmth and people-focus.\n\nSuccess isn\'t just about results — it\'s about being liked, building networks, bringing others along.',
  '3w4': 'Your 4 wing adds depth and personal style.\n\nYou pursue success in distinctive ways — achievement with authenticity, work that reflects something real.',
  '4w3': 'Your 3 wing adds drive and outward expression.\n\nYou want your uniqueness to be seen and valued — creativity that connects, not just internal depth.',
  '4w5': 'Your 5 wing adds intellectual depth and privacy.\n\nYour emotional world is rich but guarded — depth explored through ideas, not just feelings.',
  '5w4': 'Your 4 wing adds emotional sensitivity and aesthetic sense.\n\nKnowledge isn\'t just analytical — it carries feeling, meaning, personal significance.',
  '5w6': 'Your 6 wing adds vigilance and practical application.\n\nYou seek knowledge that\'s reliable, tested — understanding that provides security.',
  '6w5': 'Your 5 wing adds intellectual depth and independence.\n\nYou question through analysis — seeking certainty through understanding, not just loyalty.',
  '6w7': 'Your 7 wing adds optimism and forward energy.\n\nYou balance caution with possibility — preparing for risks while staying open to opportunity.',
  '7w6': 'Your 6 wing adds loyalty and conscientiousness.\n\nYou\'re enthusiastic but grounded — pursuing possibilities while maintaining trusted connections.',
  '7w8': 'Your 8 wing adds intensity and decisiveness.\n\nInstead of just exploring options, you\'re willing to act, push, and take control to make things happen.',
  '8w7': 'Your 7 wing adds energy and expansiveness.\n\nYou combine strength with enthusiasm — taking charge while keeping things moving and alive.',
  '8w9': 'Your 9 wing adds patience and steadiness.\n\nYour strength is quieter, more grounded — power that doesn\'t need to constantly assert itself.',
  '9w8': 'Your 8 wing adds directness and backbone.\n\nYou can assert yourself when needed — peace-seeking, but not a pushover.',
  '9w1': 'Your 1 wing adds principles and purpose.\n\nYour calm has direction — harmony pursued through values, not just avoidance.',
};

// Stress patterns per type
// Stress patterns per type - structured format
const STRESS_PATTERNS: { [key: number]: { pattern: string; tradeoff: string; strength: string; experiment: string } } = {
  1: {
    pattern: 'Under pressure, you may notice yourself becoming moody, withdrawn, and emotionally volatile—losing your usual composure and feeling misunderstood.',
    tradeoff: 'The inner critic that usually drives improvement can turn inward destructively. Self-judgment may intensify rather than motivate.',
    strength: 'This movement also opens access to emotional depth and authenticity. The feelings that surface may carry important information.',
    experiment: 'When you notice yourself withdrawing, pause. What feeling is asking for attention beneath the surface?'
  },
  2: {
    pattern: 'Under pressure, you may notice yourself becoming aggressive and demanding—insisting on recognition and pushing harder when feeling unappreciated.',
    tradeoff: 'The energy that usually flows toward others may redirect into self-assertion. Generosity can flip into entitlement.',
    strength: 'This movement also offers access to your own needs and boundaries. The force you feel may be legitimate self-advocacy emerging.',
    experiment: 'When you notice yourself demanding recognition, pause. What need of your own have you been neglecting?'
  },
  3: {
    pattern: 'Under pressure, you may notice yourself disengaging—going through the motions, avoiding situations where failure feels possible.',
    tradeoff: 'The drive that usually propels achievement can flatline. Success may start feeling meaningless or unattainable.',
    strength: 'This movement also offers permission to rest and simply be. The pause may reveal what matters beyond accomplishment.',
    experiment: 'When you notice yourself going through the motions, pause. What would feel meaningful even without recognition?'
  },
  4: {
    pattern: 'Under pressure, you may notice yourself becoming clingy and overinvolved—seeking external connection to fill an internal void.',
    tradeoff: 'The independence you usually value can give way to neediness. Connection may be sought to avoid rather than enrich.',
    strength: 'This movement also opens access to genuine interdependence. The reaching out may reflect real need for support.',
    experiment: 'When you notice yourself seeking excessive connection, pause. What are you hoping someone else will provide?'
  },
  5: {
    pattern: 'Under pressure, you may notice yourself becoming scattered and impulsive—acting without your usual thoughtfulness, jumping from thing to thing.',
    tradeoff: 'The careful analysis you usually rely on may fragment. Action may outpace understanding.',
    strength: 'This movement also offers access to spontaneity and engagement. The energy you feel may want expression, not just containment.',
    experiment: 'When you notice scattered energy, pause. What are you avoiding by staying in motion?'
  },
  6: {
    pattern: 'Under pressure, you may notice yourself becoming competitive and image-conscious—trying to prove your worth through visible achievement.',
    tradeoff: 'The vigilance that usually protects may redirect into performance anxiety. Security may be sought through success.',
    strength: 'This movement also offers access to confidence and capability. The drive you feel may reflect genuine ambition.',
    experiment: 'When you notice yourself performing, pause. What would feel secure even without proving yourself?'
  },
  7: {
    pattern: 'Under pressure, you may notice yourself becoming critical and rigid—fixating on what\'s wrong rather than what\'s possible.',
    tradeoff: 'The optimism that usually flows freely may harden into judgment. Possibility may feel blocked.',
    strength: 'This movement also offers access to discernment and standards. The criticism may carry legitimate insight.',
    experiment: 'When you notice yourself becoming critical, pause. What standard are you holding, and is it serving you?'
  },
  8: {
    pattern: 'Under pressure, you may notice yourself withdrawing and becoming secretive—pulling away from connection to protect vulnerability.',
    tradeoff: 'The direct engagement you usually offer may retreat into isolation. Strength may feel like it requires distance.',
    strength: 'This movement also offers access to reflection and conservation. The withdrawal may be genuine self-protection.',
    experiment: 'When you notice yourself pulling away, pause. What vulnerability are you protecting, and does it need protection right now?'
  },
  9: {
    pattern: 'Under pressure, you may notice yourself becoming anxious and reactive—scanning for threats, worrying about worst-case scenarios.',
    tradeoff: 'The peace you usually maintain may fragment into vigilance. Calm may give way to contingency planning.',
    strength: 'This movement also offers access to alertness and engagement. The anxiety may carry important information about what matters.',
    experiment: 'When you notice anxiety rising, pause. What are you sensing that your usual calm might overlook?'
  }
};

// Growth patterns per type - structured format
const GROWTH_PATTERNS: { [key: number]: { pattern: string; tradeoff: string; strength: string; experiment: string } } = {
  1: {
    pattern: 'When resourced, you may notice access to spontaneity and joy—a loosening of the grip on standards, permission to play.',
    tradeoff: 'Lightness may initially feel irresponsible. You might resist accepting imperfection even when it serves you.',
    strength: 'This movement offers the gift of acceptance—the capacity to enjoy what is without needing to fix it.',
    experiment: 'Do something "imperfectly" on purpose today. What happens when good enough is actually good enough?'
  },
  2: {
    pattern: 'When resourced, you may notice access to self-care and emotional honesty—honoring your own needs without guilt.',
    tradeoff: 'Attending to yourself may initially feel selfish. You might resist receiving what you freely give others.',
    strength: 'This movement offers the gift of authenticity—the capacity to know and express what you actually need.',
    experiment: 'Let someone help you with something this week. Notice what arises when you receive without immediately reciprocating.'
  },
  3: {
    pattern: 'When resourced, you may notice access to commitment and loyalty—valuing depth over image, authentic connection over impression.',
    tradeoff: 'Slowing down may initially feel like falling behind. You might resist intimacy that can\'t be optimized.',
    strength: 'This movement offers the gift of belonging—the capacity to be valued for who you are, not what you achieve.',
    experiment: 'Stay in a conversation past the point of productivity. What opens up when you\'re not moving toward an outcome?'
  },
  4: {
    pattern: 'When resourced, you may notice access to objectivity and discipline—using structure to channel emotion into action.',
    tradeoff: 'Structure may initially feel constraining. You might resist routines that seem to flatten emotional experience.',
    strength: 'This movement offers the gift of groundedness—the capacity to act from principle, not just feeling.',
    experiment: 'Follow a simple routine this week without questioning it. What happens when you trust the container?'
  },
  5: {
    pattern: 'When resourced, you may notice access to confident engagement—moving from observation to participation, sharing knowledge generously.',
    tradeoff: 'Engagement may initially feel exposing. You might resist action before you feel fully prepared.',
    strength: 'This movement offers the gift of impact—the capacity to shape the world, not just understand it.',
    experiment: 'Share your perspective before someone asks for it. What happens when you offer rather than wait?'
  },
  6: {
    pattern: 'When resourced, you may notice access to inner peace and trust—relaxing vigilance, acting from groundedness rather than anticipation.',
    tradeoff: 'Trust may initially feel naive. You might resist letting go of the watchfulness that feels protective.',
    strength: 'This movement offers the gift of presence—the capacity to rest in what is rather than brace for what might be.',
    experiment: 'Let something unfold without contingency planning. What happens when you trust the situation to work out?'
  },
  7: {
    pattern: 'When resourced, you may notice access to focused depth—staying with one thing, finding richness in completion rather than variety.',
    tradeoff: 'Focus may initially feel limiting. You might resist depth that requires giving up other options.',
    strength: 'This movement offers the gift of mastery—the capacity to go deep enough to find what breadth cannot reach.',
    experiment: 'Finish something before starting something new. What satisfaction lives on the other side of completion?'
  },
  8: {
    pattern: 'When resourced, you may notice access to openheartedness and vulnerability—letting others in, using strength to protect rather than dominate.',
    tradeoff: 'Vulnerability may initially feel like weakness. You might resist softening that seems to compromise your position.',
    strength: 'This movement offers the gift of intimacy—the capacity to be seen and known, not just respected.',
    experiment: 'Share something tender with someone you trust. What happens when strength includes softness?'
  },
  9: {
    pattern: 'When resourced, you may notice access to assertive energy and clear priorities—making your mark, letting your preferences be known.',
    tradeoff: 'Assertion may initially feel aggressive. You might resist differentiation that seems to threaten harmony.',
    strength: 'This movement offers the gift of presence—the capacity to matter, to take up space, to be fully here.',
    experiment: 'State a clear preference today without hedging. What happens when you simply say what you want?'
  }
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

// ============================================
// OVERVIEW DATA (Reflective Summary)
// ============================================

// Core Pattern descriptions - the first "mirror"
const CORE_PATTERNS: { [key: number]: string } = {
  1: 'A tendency toward improvement, correctness, and holding yourself to high standards. Your attention naturally moves to what could be better, more aligned, more right.',
  2: 'A tendency toward connection through giving, anticipating what others need, and finding value in being helpful. Your attention naturally moves toward relationships and how you can support.',
  3: 'A tendency toward achievement, efficiency, and presenting yourself in the best possible light. Your attention naturally moves to goals, outcomes, and how you\'re perceived.',
  4: 'A tendency toward depth, authenticity, and finding meaning in emotional experience. Your attention naturally moves to what feels significant, unique, or missing.',
  5: 'A tendency toward observation, understanding, and maintaining inner resources. Your attention naturally moves to knowledge, boundaries, and preserving your energy.',
  6: 'A tendency toward preparation, questioning, and seeking reliable ground. Your attention naturally moves to potential risks, loyalties, and what you can trust.',
  7: 'A tendency toward possibility, exploration, and maintaining access to positive options. Your attention naturally moves to what could be interesting, stimulating, or enjoyable.',
  8: 'A tendency toward strength, directness, and protecting your autonomy. Your attention naturally moves to power dynamics, control, and who can be trusted.',
  9: 'A tendency toward harmony, comfort, and maintaining inner and outer peace. Your attention naturally moves to what creates connection and avoids disruption.',
};

// What drives this pattern - internal motivation
const PATTERN_DRIVERS: { [key: number]: string } = {
  1: 'Avoiding error and criticism. A deep sense that things should be done correctly, and that you are responsible for making them so.',
  2: 'Avoiding being unwanted or unnecessary. A deep sense that love is earned through giving, and that your value comes from being needed.',
  3: 'Avoiding failure and worthlessness. A deep sense that you must achieve to be valuable, and that image matters as much as substance.',
  4: 'Avoiding ordinariness and emotional flatness. A deep sense that authentic self-expression is essential, and that something meaningful is always just out of reach.',
  5: 'Avoiding depletion and intrusion. A deep sense that your resources are limited, and that understanding the world provides safety.',
  6: 'Avoiding danger and betrayal. A deep sense that the world requires vigilance, and that security must be actively maintained.',
  7: 'Avoiding pain and limitation. A deep sense that freedom and possibility are essential, and that being trapped in negativity must be prevented.',
  8: 'Avoiding vulnerability and being controlled. A deep sense that strength is necessary for survival, and that weakness invites harm.',
  9: 'Avoiding conflict and disconnection. A deep sense that peace must be preserved, and that your own needs can wait to maintain harmony.',
};

// Where this shows up - bullet points for each type
const PATTERN_MANIFESTATIONS: { [key: number]: { decisions: string; work: string; relationships: string; stress: string } } = {
  1: {
    decisions: 'Weighing options against internal standards; difficulty with "good enough"',
    work: 'High quality output paired with self-criticism when results fall short',
    relationships: 'Teaching and improving others; sometimes perceived as critical',
    stress: 'Tightening standards, increased frustration with imperfection',
  },
  2: {
    decisions: 'Considering how choices affect others before yourself',
    work: 'People-focused, collaborative, may struggle with boundaries',
    relationships: 'Giving generously; sometimes expecting recognition in return',
    stress: 'Over-helping, feeling unappreciated, difficulty asking for support',
  },
  3: {
    decisions: 'Evaluating which option leads to the best outcome or impression',
    work: 'Goal-driven, efficient, adapts presentation to context',
    relationships: 'Charming and engaging; may struggle with deeper vulnerability',
    stress: 'Working harder, image-consciousness, avoiding feelings of failure',
  },
  4: {
    decisions: 'Seeking the option that feels most authentic or meaningful',
    work: 'Creative, expressive, may struggle with routine tasks',
    relationships: 'Deep connection valued; can feel misunderstood or different',
    stress: 'Intensifying emotions, withdrawing, romanticizing what\'s missing',
  },
  5: {
    decisions: 'Gathering information before committing; preferring certainty',
    work: 'Deep expertise, independent, may hesitate to engage or share',
    relationships: 'Private, selective, needs space to recharge',
    stress: 'Withdrawing further, detaching from emotions, hoarding resources',
  },
  6: {
    decisions: 'Scanning for risks, seeking input, testing trustworthiness',
    work: 'Reliable, thorough, may second-guess or seek reassurance',
    relationships: 'Loyal and committed; can be suspicious or test loyalty',
    stress: 'Increased anxiety, worst-case thinking, seeking authority or rebelling',
  },
  7: {
    decisions: 'Keeping options open, favoring exciting possibilities',
    work: 'Innovative, multi-tasking, may struggle with follow-through',
    relationships: 'Fun and engaging; may avoid difficult emotional territory',
    stress: 'Scattering attention, over-planning, avoiding uncomfortable feelings',
  },
  8: {
    decisions: 'Acting decisively, trusting gut instinct, taking charge',
    work: 'Leading, protecting territory, direct communication',
    relationships: 'Intense loyalty; may dominate or test boundaries',
    stress: 'Increasing force, controlling more, difficulty showing vulnerability',
  },
  9: {
    decisions: 'Considering what maintains harmony; may defer or delay',
    work: 'Steady, accommodating, may struggle with priorities',
    relationships: 'Easy-going, merging with others\' preferences',
    stress: 'Numbing out, passive resistance, losing sense of own wants',
  },
};

// Reflection prompts for Overview (different from journal prompts)
const OVERVIEW_REFLECTIONS: { [key: number]: string } = {
  1: 'Where in your life is the standard you\'re holding serving growth—and where might it be creating unnecessary pressure?',
  2: 'Where are you giving freely—and where might giving be a way to avoid asking for what you need?',
  3: 'Where is your drive to achieve aligned with your values—and where might it be a substitute for being seen as you are?',
  4: 'Where is your depth serving you—and where might intensity be a way to avoid the ordinary richness already present?',
  5: 'Where is your understanding serving wisdom—and where might knowing be a way to avoid engaging?',
  6: 'Where is your vigilance keeping you safe—and where might it be preventing trust that wants to grow?',
  7: 'Where are you expanding possibility—and where might depth be asking for attention?',
  8: 'Where is your strength protecting what matters—and where might vulnerability be waiting to connect?',
  9: 'Where is your peace genuine presence—and where might it be a way to avoid the clarity of your own voice?',
};

// ============================================
// PATTERN LAYERS DATA (Deeper Enneagram Layers)
// Translated from: Passion, Fixation, Avoidance, Anti-Self, Virtue, Holy Idea
// into natural, human, reflective language (NO JARGON)
// ============================================

interface PatternLayersType {
  // How the user tends to move/behave
  howYouMove: string;
  // What they subtly avoid or move away from
  whatYouAvoid: string;
  // What sits underneath the pattern
  whatSitsUnderneath: string;
  
  // Collapsible: What's driving this
  emotionalTendency: string;  // From Passion
  thinkingTendency: string;   // From Fixation
  
  // Collapsible: What this protects you from
  avoidancePattern: string;   // From Avoidance
  antiSelfPattern: string;    // From Anti-Self (inner voice that reinforces the pattern)
  
  // Collapsible: When this opens
  growthDirection: string;    // From Virtue + Holy Idea
}

const PATTERN_LAYERS: { [key: number]: PatternLayersType } = {
  1: {
    howYouMove: 'You tend to notice what could be better, more aligned, more correct. There\'s a natural pull toward improvement—in yourself, in situations, in how things are done.',
    whatYouAvoid: 'You often move away from anything that feels sloppy, careless, or ethically questionable. There\'s a subtle vigilance against being seen as wrong or irresponsible.',
    whatSitsUnderneath: 'Beneath the drive for correctness is a quiet tension: a sense that the world requires your constant attention to keep it from falling into disorder—and that letting up might mean becoming part of the problem.',
    
    emotionalTendency: 'A simmering frustration when things don\'t meet your internal standards. Not explosive, but always there—like a background hum of "this could be better."',
    thinkingTendency: 'Comparing reality to how it should be. Your mind naturally evaluates, critiques, and imagines the improved version.',
    
    avoidancePattern: 'Making mistakes. Being criticized. Losing control of your own integrity.',
    antiSelfPattern: 'A voice that says: "If you relax your standards, everything will fall apart. You can\'t trust yourself to be good without constant vigilance."',
    
    growthDirection: 'When this pattern softens, you access genuine acceptance—the ability to see that perfection isn\'t the point, and that what\'s already present is enough. Joy becomes possible without needing everything to be fixed first.',
  },
  2: {
    howYouMove: 'You tend to notice what others need, often before they do. There\'s a natural pull toward connection, care, and being the one who helps.',
    whatYouAvoid: 'You often move away from your own needs, from being the one who receives, from situations where you might be seen as selfish or unhelpful.',
    whatSitsUnderneath: 'Beneath the giving is a quiet question: Am I loved for who I am, or only for what I provide? There\'s a fear that without usefulness, connection might disappear.',
    
    emotionalTendency: 'Pride in being needed, though it may not feel like pride. More like a warm glow when you\'ve made someone\'s life easier.',
    thinkingTendency: 'Reading others—anticipating what they want, what they need, what would make them happy. Your attention flows outward.',
    
    avoidancePattern: 'Acknowledging your own needs. Asking directly for help. Being perceived as selfish.',
    antiSelfPattern: 'A voice that says: "Your needs don\'t matter as much. If you stop giving, they\'ll forget about you."',
    
    growthDirection: 'When this pattern softens, you access genuine humility—the recognition that receiving is as valuable as giving. You discover that love doesn\'t depend on earning it.',
  },
  3: {
    howYouMove: 'You tend to notice what leads to success, recognition, or progress. There\'s a natural pull toward achieving, presenting well, and making things happen.',
    whatYouAvoid: 'You often move away from failure, from being seen as ineffective, from situations where you can\'t shine or succeed.',
    whatSitsUnderneath: 'Beneath the achievement is a quiet uncertainty: Am I valuable for who I am, or only for what I accomplish? There\'s a fear that without success, you might disappear.',
    
    emotionalTendency: 'A subtle deceit—not lying to others, but adjusting who you appear to be. Becoming the version that\'s most likely to succeed in each context.',
    thinkingTendency: 'Strategizing. Your mind naturally calculates the shortest path to the goal, the best presentation, the most effective approach.',
    
    avoidancePattern: 'Failure. Being ordinary. Stopping long enough to feel what\'s underneath the drive.',
    antiSelfPattern: 'A voice that says: "You are what you achieve. Without accomplishment, you\'re nothing special."',
    
    growthDirection: 'When this pattern softens, you access genuine authenticity—the freedom to be seen as you actually are, not just as your achievements. You discover that being is enough, even without doing.',
  },
  4: {
    howYouMove: 'You tend to notice what\'s missing, what\'s unique, what carries emotional depth. There\'s a natural pull toward authenticity, meaning, and the fullness of experience.',
    whatYouAvoid: 'You often move away from ordinariness, from emotional flatness, from being like everyone else or settling for the mundane.',
    whatSitsUnderneath: 'Beneath the search for meaning is a quiet longing: a sense that something essential is missing, and that finding it would finally make you feel complete.',
    
    emotionalTendency: 'A melancholic longing—not always sad, but always aware of what isn\'t here. The gap between the ideal and the real is vivid.',
    thinkingTendency: 'Comparing yourself to others, often unfavorably. Romanticizing what\'s distant or lost while devaluing what\'s present.',
    
    avoidancePattern: 'Being ordinary. Losing your unique identity. Having your depth go unseen.',
    antiSelfPattern: 'A voice that says: "No one truly understands you. What\'s wrong with you is too fundamental to fix."',
    
    growthDirection: 'When this pattern softens, you access genuine equanimity—the ability to see that nothing is actually missing. What you\'re searching for has been here all along, just overlooked.',
  },
  5: {
    howYouMove: 'You tend to notice what you understand, what you can observe, what you can contain and preserve. There\'s a natural pull toward knowledge, privacy, and maintaining your inner resources.',
    whatYouAvoid: 'You often move away from demands on your energy, from situations that deplete you, from engagement that feels overwhelming or intrusive.',
    whatSitsUnderneath: 'Beneath the withdrawal is a quiet fear: a sense that the world takes more than it gives, and that your inner reserves must be carefully protected to survive.',
    
    emotionalTendency: 'A retracted quality—holding back, observing before engaging, minimizing your needs so you don\'t have to ask for much.',
    thinkingTendency: 'Analyzing from a distance. Your mind naturally creates frameworks, categories, and understanding that doesn\'t require direct participation.',
    
    avoidancePattern: 'Being overwhelmed. Having your boundaries invaded. Not knowing enough.',
    antiSelfPattern: 'A voice that says: "You don\'t have enough to offer. It\'s safer to watch than to participate."',
    
    growthDirection: 'When this pattern softens, you access genuine engagement—the trust that your resources are abundant and that giving doesn\'t mean losing. Participation becomes nourishing rather than depleting.',
  },
  6: {
    howYouMove: 'You tend to notice what could go wrong, what needs to be prepared for, who can be trusted. There\'s a natural pull toward security, loyalty, and reliable foundations.',
    whatYouAvoid: 'You often move away from uncertainty, from situations where you can\'t predict the outcome, from authority you haven\'t tested.',
    whatSitsUnderneath: 'Beneath the vigilance is a quiet doubt: a sense that you can\'t fully trust your own judgment, and that external guidance or confirmation is needed to feel safe.',
    
    emotionalTendency: 'Anxiety that scans for danger—not always dramatic, but always slightly alert. Worry as a form of preparation.',
    thinkingTendency: 'Questioning, testing, imagining worst-case scenarios. Your mind naturally plays devil\'s advocate, even with yourself.',
    
    avoidancePattern: 'Uncertainty. Being without support. Making decisions alone.',
    antiSelfPattern: 'A voice that says: "You can\'t handle this alone. Something bad is probably coming that you haven\'t prepared for."',
    
    growthDirection: 'When this pattern softens, you access genuine inner courage—the discovery that you can trust yourself, that you already have the guidance you\'ve been seeking outside.',
  },
  7: {
    howYouMove: 'You tend to notice what\'s possible, what\'s interesting, what opens up new horizons. There\'s a natural pull toward stimulation, options, and keeping the future bright.',
    whatYouAvoid: 'You often move away from pain, limitation, boredom, and anything that might trap you in negativity or close down your options.',
    whatSitsUnderneath: 'Beneath the enthusiasm is a quiet escape: a sense that if you slow down or face the difficult thing directly, you\'ll be stuck in discomfort with no way out.',
    
    emotionalTendency: 'A gluttony for experience—not always excess, but a constant reaching toward the next interesting thing. Avoiding satiation because that might mean stopping.',
    thinkingTendency: 'Reframing, planning, ideating. Your mind naturally finds the silver lining, the escape route, the more exciting possibility.',
    
    avoidancePattern: 'Pain. Limitation. Being trapped in negative emotions or boring circumstances.',
    antiSelfPattern: 'A voice that says: "If you stop and feel this, you\'ll get stuck. Keep moving, keep planning, keep the options open."',
    
    growthDirection: 'When this pattern softens, you access genuine presence—the discovery that this moment, even if painful, is sufficient. Depth becomes possible when you stop running toward the next thing.',
  },
  8: {
    howYouMove: 'You tend to notice who has power, who can be trusted, who needs protection. There\'s a natural pull toward strength, directness, and taking charge of your own destiny.',
    whatYouAvoid: 'You often move away from vulnerability, from being controlled, from situations where you might appear weak or dependent.',
    whatSitsUnderneath: 'Beneath the strength is a quiet guardedness: a sense that the world is harsh, that weakness invites harm, and that only through power can you be safe.',
    
    emotionalTendency: 'A lustiness for intensity—not just physical, but a desire for aliveness, impact, and full engagement. Holding back feels like dying.',
    thinkingTendency: 'Assessing power dynamics. Your mind naturally reads situations for who\'s in charge, who\'s trustworthy, and where the real power lies.',
    
    avoidancePattern: 'Vulnerability. Being controlled. Appearing weak.',
    antiSelfPattern: 'A voice that says: "If you show your soft side, people will take advantage. Strength is survival."',
    
    growthDirection: 'When this pattern softens, you access genuine innocence—the ability to be open and tender without fear. Vulnerability becomes strength rather than weakness.',
  },
  9: {
    howYouMove: 'You tend to notice what creates harmony, what avoids disruption, what keeps things comfortable and connected. There\'s a natural pull toward peace, stability, and merging with the flow.',
    whatYouAvoid: 'You often move away from conflict, from asserting yourself in ways that might create tension, from anything that disrupts your inner calm.',
    whatSitsUnderneath: 'Beneath the peacefulness is a quiet self-forgetting: a sense that your own presence might disturb things, and that it\'s easier to go along than to risk disconnection.',
    
    emotionalTendency: 'A comfortable numbness—not depression, but a gentle blurring of your own needs and desires in favor of maintaining equilibrium.',
    thinkingTendency: 'Seeing all sides. Your mind naturally finds where everyone is right, making it hard to know where you actually stand.',
    
    avoidancePattern: 'Conflict. Being seen as difficult. Losing your sense of inner peace.',
    antiSelfPattern: 'A voice that says: "Your needs aren\'t that important. It\'s not worth the disruption. Just go along."',
    
    growthDirection: 'When this pattern softens, you access genuine right action—the ability to know what you want and move toward it without losing connection. Your presence becomes a gift rather than a disturbance.',
  },
};

// ============================================
// MIRROR PATTERN CARDS DATA (Deep Dive Refactor)
// 6 standardized cards with interactive structure
// ============================================

interface MirrorPatternCardData {
  whatThisIs: string;
  whatYouMightNotice: string;
  theTension: string;
  whenItWorks: string;
  tryThis: string;
  reflectionPrompts: string[];
  journalPrompt: string;
  mirrorPrompt: string;
}

interface TypeMirrorPatternCards {
  corePattern: MirrorPatternCardData;
  howThisShowsUp: MirrorPatternCardData;
  underPressure: MirrorPatternCardData;
  whenResourced: MirrorPatternCardData;
  yourEdges: MirrorPatternCardData;
  growthPath: MirrorPatternCardData;
}

const MIRROR_PATTERN_CARDS: { [key: number]: TypeMirrorPatternCards } = {
  1: {
    corePattern: {
      whatThisIs: 'A drive toward improvement—making things right, correct, aligned with ideals.',
      whatYouMightNotice: 'You may notice an inner critic that\'s always on. A constant awareness of gaps between how things are and how they should be.',
      theTension: 'The very thing that makes you conscientious can also make you rigid. Wanting things to be right can crowd out accepting what is.',
      whenItWorks: 'When channeled well, this becomes discernment, integrity, and the ability to improve things that genuinely need improving.',
      tryThis: 'Notice one moment today where "good enough" actually is. What happens when you let that be okay?',
      reflectionPrompts: ['What standard am I holding right now? Is it serving me?', 'Where might acceptance do more good than correction?'],
      journalPrompt: 'When I notice the impulse to fix or improve something, what feeling is underneath that?',
      mirrorPrompt: 'Help me explore how my drive for improvement is showing up in my life right now',
    },
    howThisShowsUp: {
      whatThisIs: 'The daily expressions of this pattern—how it moves through your life.',
      whatYouMightNotice: 'You may notice yourself mentally correcting things, holding back criticism, or feeling responsible for maintaining standards others overlook.',
      theTension: 'What feels like helping often comes across as criticism. What feels like integrity can become inflexibility.',
      whenItWorks: 'You bring order, reliability, and genuine improvement to everything you touch. People trust your judgment.',
      tryThis: 'Before correcting something today, pause and ask: Is this mine to fix? Does it actually need fixing?',
      reflectionPrompts: ['What did I feel compelled to improve today?', 'Where did I hold back criticism?'],
      journalPrompt: 'I notice myself wanting to fix or improve things when...',
      mirrorPrompt: 'Help me see how my pattern of improvement shows up in daily interactions',
    },
    underPressure: {
      whatThisIs: 'When stressed, you may move toward Type 4 qualities—becoming more moody, withdrawn, or feeling uniquely flawed.',
      whatYouMightNotice: 'You may notice self-pity, melancholy, or a sense that your imperfections are worse than everyone else\'s.',
      theTension: 'The usual self-control relaxes into emotional intensity. You may feel exempt from rules you normally uphold.',
      whenItWorks: 'This movement can actually help—giving you access to deeper feelings and creative self-expression.',
      tryThis: 'When you feel the mood shift, name it: "I\'m stressed and moving toward withdrawal." Then choose consciously.',
      reflectionPrompts: ['What triggered this emotional shift?', 'What do I actually need right now?'],
      journalPrompt: 'When I\'m really stressed, I notice myself becoming...',
      mirrorPrompt: 'I\'m feeling stressed and want to explore what\'s underneath it',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 7 qualities—becoming more spontaneous, joyful, and accepting.',
      whatYouMightNotice: 'You may notice yourself lightening up, being playful, accepting imperfection with good humor.',
      theTension: 'This can feel like abandoning standards, but it\'s actually liberation from unnecessary rigidity.',
      whenItWorks: 'You become inspiring—someone who holds standards AND enjoys life. This is your natural potential.',
      tryThis: 'Do something today purely for enjoyment, with no productive justification needed.',
      reflectionPrompts: ['What would feel spontaneously joyful today?', 'Where could I accept "good enough"?'],
      journalPrompt: 'When I let myself lighten up, I feel...',
      mirrorPrompt: 'Help me explore what happens when I let myself be spontaneous',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—what drives this, what you avoid, and the voice that keeps it going.',
      whatYouMightNotice: 'A simmering frustration beneath the surface. An inner voice saying you can\'t trust yourself to be good without vigilance.',
      theTension: 'The fear of being corrupt or wrong drives constant self-monitoring that\'s exhausting but feels necessary.',
      whenItWorks: 'When you see this clearly, you can choose. The pattern becomes a tool, not a prison.',
      tryThis: 'Notice the inner critic\'s voice today. What is it afraid will happen if it stops?',
      reflectionPrompts: ['What would happen if I relaxed my standards?', 'What is my inner critic protecting me from?'],
      journalPrompt: 'The voice in my head that pushes for perfection is afraid that...',
      mirrorPrompt: 'Help me understand what drives my need for things to be right',
    },
    growthPath: {
      whatThisIs: 'The direction of genuine growth—toward serenity, acceptance, and recognizing inherent goodness.',
      whatYouMightNotice: 'Moments of accepting what is. Recognizing that perfection isn\'t required for things to be good.',
      theTension: 'Growth feels like letting go of something important. It\'s actually letting go of a burden.',
      whenItWorks: 'You access genuine serenity—not resignation, but deep acceptance that includes the motivation to improve.',
      tryThis: 'Find one thing today that\'s already good enough exactly as it is. Let yourself feel that.',
      reflectionPrompts: ['What would serenity feel like for me?', 'What can I accept today without needing to change it?'],
      journalPrompt: 'If I could fully accept myself as I am, I would feel...',
      mirrorPrompt: 'Guide me in exploring what acceptance might look like for me',
    },
  },
  // Types 2-9 follow similar structure with type-specific content
  2: {
    corePattern: {
      whatThisIs: 'A drive toward connection—meeting needs, helping, making yourself essential to others.',
      whatYouMightNotice: 'You may notice yourself scanning for what others need, anticipating requests, feeling warm when appreciated.',
      theTension: 'The very giving that creates connection can obscure your own needs. Helpfulness can become a way to earn love.',
      whenItWorks: 'When balanced, this becomes genuine empathy, emotional intelligence, and the gift of making others feel truly seen.',
      tryThis: 'Notice one need of your own today. What happens when you acknowledge it?',
      reflectionPrompts: ['What did I give today? What did I need?', 'Where am I giving to earn rather than to share?'],
      journalPrompt: 'When I think about asking for what I need, I feel...',
      mirrorPrompt: 'Help me explore the relationship between my giving and my own needs',
    },
    howThisShowsUp: {
      whatThisIs: 'How this pattern expresses daily—through care, attention to others, and relational awareness.',
      whatYouMightNotice: 'You may notice yourself adapting to different people, knowing what they need before they ask, feeling hurt when help is rejected.',
      theTension: 'What feels like generosity can come with strings attached. The help can carry unspoken expectations.',
      whenItWorks: 'You\'re the emotional heart of groups. People feel genuinely cared for in your presence.',
      tryThis: 'Give something today with zero expectation of recognition or return.',
      reflectionPrompts: ['Whose needs am I prioritizing over my own?', 'What would change if no one noticed my giving?'],
      journalPrompt: 'I find myself most focused on others\' needs when...',
      mirrorPrompt: 'Help me see how my helping patterns show up in my relationships',
    },
    underPressure: {
      whatThisIs: 'Under stress, you may move toward Type 8—becoming more aggressive, demanding, or confrontational.',
      whatYouMightNotice: 'You may notice yourself insisting on recognition, feeling entitled to appreciation, becoming pushy about your contributions.',
      theTension: 'The usual indirect approach turns direct. Suppressed needs burst out as demands.',
      whenItWorks: 'This can actually help you claim space and voice needs directly—if channeled consciously.',
      tryThis: 'When you feel the push rising, pause. What do you actually need? Can you ask for it without demanding?',
      reflectionPrompts: ['What am I really needing right now?', 'How can I ask directly instead of demanding?'],
      journalPrompt: 'When I feel underappreciated, I notice myself...',
      mirrorPrompt: 'I\'m feeling unappreciated and want to explore what\'s underneath',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 4 qualities—becoming more authentic, aware of your own feelings and needs.',
      whatYouMightNotice: 'You may notice yourself getting clearer on what YOU feel, valuing your own experience, expressing needs directly.',
      theTension: 'This can feel selfish, but it\'s actually the foundation of genuine giving.',
      whenItWorks: 'You become someone who gives from overflow rather than from need. Your care is unconditional.',
      tryThis: 'Do something today purely for yourself. Notice how that feels.',
      reflectionPrompts: ['What do I genuinely want right now?', 'What would self-care look like today?'],
      journalPrompt: 'When I attend to my own needs, I discover...',
      mirrorPrompt: 'Help me explore what I genuinely need and want',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—the pride in being needed, the fear of being unloved without usefulness.',
      whatYouMightNotice: 'A subtle pride in how much you do for others. A fear that your own needs are too much or unworthy.',
      theTension: 'The belief that love must be earned through service keeps you from receiving it freely.',
      whenItWorks: 'When seen clearly, you can choose to give freely while also receiving. The pattern loses its grip.',
      tryThis: 'Notice where you feel proud of your helpfulness. What would happen if no one needed you?',
      reflectionPrompts: ['What would I be without my helpfulness?', 'How would I feel if I couldn\'t give?'],
      journalPrompt: 'The voice that says my needs don\'t matter sounds like...',
      mirrorPrompt: 'Help me understand why asking for help feels so hard',
    },
    growthPath: {
      whatThisIs: 'The direction of growth—toward genuine humility and the recognition that receiving is as valuable as giving.',
      whatYouMightNotice: 'Moments where you receive without needing to reciprocate immediately. Recognizing your own worth apart from usefulness.',
      theTension: 'Growth feels like becoming selfish. It\'s actually becoming whole.',
      whenItWorks: 'You access genuine love—given freely, received openly. You no longer need to earn what\'s already yours.',
      tryThis: 'Let someone help you today without immediately trying to return the favor.',
      reflectionPrompts: ['What would it feel like to be loved for who I am, not what I do?', 'How can I practice receiving?'],
      journalPrompt: 'If I truly believed I was lovable without doing anything, I would...',
      mirrorPrompt: 'Guide me in exploring what unconditional self-worth might feel like',
    },
  },
  3: {
    corePattern: {
      whatThisIs: 'A drive toward achievement—succeeding, presenting well, making things happen efficiently.',
      whatYouMightNotice: 'You may notice yourself measuring situations by what can be accomplished, adapting your presentation to your audience.',
      theTension: 'The achievement that earns admiration can disconnect you from what you actually feel. Success can become identity.',
      whenItWorks: 'When balanced, this becomes genuine competence, inspiration, and the ability to manifest goals into reality.',
      tryThis: 'Notice one moment today where you\'re performing rather than being. What would authentic look like?',
      reflectionPrompts: ['What am I trying to prove right now?', 'Who am I when I\'m not achieving?'],
      journalPrompt: 'When I stop achieving, I\'m afraid people will see...',
      mirrorPrompt: 'Help me explore my relationship with success and achievement',
    },
    howThisShowsUp: {
      whatThisIs: 'How this pattern expresses daily—through productivity, image awareness, and goal orientation.',
      whatYouMightNotice: 'You may notice yourself keeping score, adjusting how you present in different contexts, feeling restless when not productive.',
      theTension: 'What looks like effectiveness can be image management. The presentation may not match the inner experience.',
      whenItWorks: 'You get things done. You inspire others. You make success look achievable.',
      tryThis: 'Do something today that serves no productive purpose. Notice the discomfort.',
      reflectionPrompts: ['Where am I performing today?', 'What would happen if I did less?'],
      journalPrompt: 'I notice myself adjusting my image when...',
      mirrorPrompt: 'Help me see how my achievement patterns show up daily',
    },
    underPressure: {
      whatThisIs: 'Under stress, you may move toward Type 9—becoming more disengaged, numb, or checked out.',
      whatYouMightNotice: 'You may notice yourself procrastinating, checking out, losing your usual drive.',
      theTension: 'The usual forward momentum stalls. You may distract yourself with trivial activities.',
      whenItWorks: 'This slowdown can actually be restorative—if you use it to reconnect with what you actually want.',
      tryThis: 'When you notice the withdrawal, ask: What am I avoiding feeling?',
      reflectionPrompts: ['What am I trying not to feel right now?', 'What would rest actually look like?'],
      journalPrompt: 'When my drive stalls, I notice myself...',
      mirrorPrompt: 'I\'m feeling unmotivated and want to understand what\'s happening',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 6 qualities—becoming more loyal, collaborative, and authentic.',
      whatYouMightNotice: 'You may notice yourself valuing team success over personal glory, being more honest about struggles.',
      theTension: 'This can feel like losing your edge, but it\'s actually gaining depth.',
      whenItWorks: 'You become a leader who brings others along, not just a star who outshines them.',
      tryThis: 'Share a genuine struggle with someone today. Notice what happens.',
      reflectionPrompts: ['What would I share if I weren\'t managing my image?', 'How might vulnerability serve me?'],
      journalPrompt: 'When I let myself be seen as imperfect, I feel...',
      mirrorPrompt: 'Help me explore what authenticity might look like for me',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—the deceit of image, the fear of being worthless without achievement.',
      whatYouMightNotice: 'A subtle shape-shifting—becoming what each situation requires. A fear that stopping means disappearing.',
      theTension: 'The belief that you are what you achieve keeps you performing. Failure feels existential.',
      whenItWorks: 'When seen clearly, you can achieve from choice rather than compulsion. Success becomes a tool, not a identity.',
      tryThis: 'Notice where you\'re performing today. What would change if you stopped?',
      reflectionPrompts: ['Who am I when I\'m not succeeding?', 'What do I fear people will see if I fail?'],
      journalPrompt: 'If I couldn\'t achieve anything, I would be...',
      mirrorPrompt: 'Help me understand my fear of being seen as ordinary',
    },
    growthPath: {
      whatThisIs: 'The direction of growth—toward authenticity and the recognition that being is enough.',
      whatYouMightNotice: 'Moments of simply being without needing to produce. Valuing yourself apart from accomplishments.',
      theTension: 'Growth feels like giving up your superpower. It\'s actually freeing you to use it consciously.',
      whenItWorks: 'You access genuine authenticity—achieving because you choose to, not because you have to.',
      tryThis: 'Spend time today with no agenda. Notice what arises.',
      reflectionPrompts: ['What would I do if I didn\'t need to prove anything?', 'How might being enough change my life?'],
      journalPrompt: 'If I truly believed I was valuable just as I am...',
      mirrorPrompt: 'Guide me in exploring what it means to be valuable without achieving',
    },
  },
  4: {
    corePattern: {
      whatThisIs: 'A drive toward depth—finding meaning, expressing uniqueness, experiencing the fullness of emotion.',
      whatYouMightNotice: 'You may notice yourself drawn to what\'s missing, feeling different from others, seeking experiences with emotional weight.',
      theTension: 'The search for meaning can obscure what\'s already here. The depth you seek can become a way to avoid ordinary presence.',
      whenItWorks: 'When balanced, this becomes creativity, emotional intelligence, and the gift of seeing beauty in what others miss.',
      tryThis: 'Notice one ordinary thing today that\'s actually beautiful. Let it be enough.',
      reflectionPrompts: ['What am I searching for that might already be here?', 'Where is depth showing up in the ordinary?'],
      journalPrompt: 'When I feel something is missing, I\'m actually longing for...',
      mirrorPrompt: 'Help me explore my relationship with longing and meaning',
    },
    howThisShowsUp: {
      whatThisIs: 'How this pattern expresses daily—through emotional awareness, aesthetic sensitivity, and identity focus.',
      whatYouMightNotice: 'You may notice yourself comparing to others, feeling misunderstood, drawn to melancholy, valuing authenticity intensely.',
      theTension: 'What feels like depth can become self-absorption. Emotional honesty can turn into emotional indulgence.',
      whenItWorks: 'You bring meaning to experience. You create beauty. You see what others overlook.',
      tryThis: 'Notice when you\'re romanticizing distance over appreciating what\'s present.',
      reflectionPrompts: ['What am I making special that\'s actually ordinary?', 'Where am I indulging emotion instead of feeling it?'],
      journalPrompt: 'I feel most like myself when...',
      mirrorPrompt: 'Help me see how my search for meaning shows up daily',
    },
    underPressure: {
      whatThisIs: 'Under stress, you may move toward Type 2—becoming more clingy, needy, or people-pleasing.',
      whatYouMightNotice: 'You may notice yourself seeking reassurance, becoming attached, needing others to affirm your worth.',
      theTension: 'The usual self-focus turns outward into dependency. You may lose yourself in others\' approval.',
      whenItWorks: 'This movement toward connection can help—if you let it bring genuine intimacy rather than neediness.',
      tryThis: 'When you feel the pull toward seeking reassurance, ask: What am I really needing?',
      reflectionPrompts: ['What do I need that I\'m seeking from others?', 'How can I give this to myself?'],
      journalPrompt: 'When I\'m stressed, I find myself reaching out to others for...',
      mirrorPrompt: 'I\'m feeling needy and want to understand what\'s underneath',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 1 qualities—becoming more disciplined, principled, and action-oriented.',
      whatYouMightNotice: 'You may notice yourself following through, valuing consistency, taking action instead of just feeling.',
      theTension: 'This can feel like losing your depth, but it\'s actually grounding it in reality.',
      whenItWorks: 'You become someone who creates meaning through action, not just through feeling.',
      tryThis: 'Commit to one practical action today regardless of how you feel.',
      reflectionPrompts: ['What would discipline serve in my life?', 'How might action complement my depth?'],
      journalPrompt: 'When I take action despite my mood, I discover...',
      mirrorPrompt: 'Help me explore how to ground my feelings in action',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—the envy of others\' completeness, the belief that something essential is missing.',
      whatYouMightNotice: 'A melancholic longing, comparing yourself to others who seem to have what you lack.',
      theTension: 'The belief that you\'re fundamentally flawed keeps you searching for what\'s already here.',
      whenItWorks: 'When seen clearly, the longing relaxes. You discover that what you seek has been present all along.',
      tryThis: 'Notice envy today without acting on it. What is it pointing toward?',
      reflectionPrompts: ['What do I believe is missing in me?', 'What if nothing was actually missing?'],
      journalPrompt: 'The voice that says something\'s wrong with me sounds like...',
      mirrorPrompt: 'Help me understand my sense that something is missing',
    },
    growthPath: {
      whatThisIs: 'The direction of growth—toward equanimity and recognizing that nothing is actually missing.',
      whatYouMightNotice: 'Moments of contentment with what is. Seeing ordinary beauty without needing it to be special.',
      theTension: 'Growth feels like losing your depth. It\'s actually finding true depth—here, now, as is.',
      whenItWorks: 'You access genuine equanimity—creative, present, at home in ordinary life.',
      tryThis: 'Find something completely ordinary and let yourself be fully satisfied by it.',
      reflectionPrompts: ['What would contentment feel like?', 'Where is completeness already present?'],
      journalPrompt: 'If I truly believed nothing was missing, I would...',
      mirrorPrompt: 'Guide me in exploring what presence and contentment might feel like',
    },
  },
  5: {
    corePattern: {
      whatThisIs: 'A drive toward understanding—gathering knowledge, preserving resources, maintaining privacy and boundaries.',
      whatYouMightNotice: 'You may notice yourself conserving energy, preferring observation to participation, valuing expertise.',
      theTension: 'The understanding that protects you can also isolate you. Knowledge can become a substitute for experience.',
      whenItWorks: 'When balanced, this becomes genuine wisdom, insight, and the ability to see clearly what others miss.',
      tryThis: 'Notice one moment today where participation might serve you more than observation.',
      reflectionPrompts: ['What am I protecting by withdrawing?', 'Where might engagement be nourishing?'],
      journalPrompt: 'When I choose to observe rather than participate, I\'m feeling...',
      mirrorPrompt: 'Help me explore my relationship with engagement and withdrawal',
    },
    howThisShowsUp: {
      whatThisIs: 'How this pattern expresses daily—through research, privacy, minimizing needs, and careful boundaries.',
      whatYouMightNotice: 'You may notice yourself needing time alone to recharge, preferring depth over breadth, feeling drained by demands.',
      theTension: 'What feels like self-protection can become isolation. Minimizing needs can mean not getting them met.',
      whenItWorks: 'You bring depth of understanding. You see what others overlook. Your insights are valuable.',
      tryThis: 'Share one piece of knowledge with someone today. Notice what happens.',
      reflectionPrompts: ['Where am I withdrawing when connection would serve me?', 'What needs am I minimizing?'],
      journalPrompt: 'I protect my energy by...',
      mirrorPrompt: 'Help me see how my withdrawal patterns show up in relationships',
    },
    underPressure: {
      whatThisIs: 'Under stress, you may move toward Type 7—becoming scattered, distracted, or overstimulated.',
      whatYouMightNotice: 'You may notice yourself jumping between interests, seeking stimulation, feeling overwhelmed by options.',
      theTension: 'The usual focus scatters. Depth gives way to breadth as you try to escape anxiety.',
      whenItWorks: 'This movement can lighten you up—if you let it bring genuine engagement rather than distraction.',
      tryThis: 'When you feel scattered, pause. What are you avoiding by staying busy?',
      reflectionPrompts: ['What am I distracting myself from?', 'What would it feel like to settle?'],
      journalPrompt: 'When I\'m overwhelmed, I cope by...',
      mirrorPrompt: 'I\'m feeling scattered and want to understand what\'s underneath',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 8 qualities—becoming more embodied, assertive, and engaged.',
      whatYouMightNotice: 'You may notice yourself taking action, claiming space, engaging physically with the world.',
      theTension: 'This can feel overwhelming, but it\'s actually completing the circuit between thought and action.',
      whenItWorks: 'You become powerful—someone who not only understands but acts on that understanding.',
      tryThis: 'Take one physical action today based on something you know.',
      reflectionPrompts: ['What would acting on my knowledge look like?', 'How might assertiveness serve me?'],
      journalPrompt: 'When I act on what I know, I feel...',
      mirrorPrompt: 'Help me explore what it would mean to be more engaged in life',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—the fear of being overwhelmed, the belief that resources are scarce.',
      whatYouMightNotice: 'A retracted quality—minimizing yourself to reduce demands. A fear that you don\'t have enough to give.',
      theTension: 'The belief that engagement depletes you keeps you watching life from the sidelines.',
      whenItWorks: 'When seen clearly, you discover that your resources are more abundant than you thought. Giving becomes receiving.',
      tryThis: 'Give something today—time, attention, knowledge—and notice if you feel depleted or enriched.',
      reflectionPrompts: ['What do I fear will happen if I give too much?', 'What if resources were abundant?'],
      journalPrompt: 'The voice that says I don\'t have enough sounds like...',
      mirrorPrompt: 'Help me understand my fear of being depleted',
    },
    growthPath: {
      whatThisIs: 'The direction of growth—toward engagement and recognizing that participation nourishes rather than depletes.',
      whatYouMightNotice: 'Moments of genuine engagement where you feel energized rather than drained.',
      theTension: 'Growth feels like being overwhelmed. It\'s actually discovering that engagement is sustainable.',
      whenItWorks: 'You access genuine presence—knowing AND being in the world fully.',
      tryThis: 'Engage with something fully today. Notice if it drains or fills you.',
      reflectionPrompts: ['What would full engagement look like?', 'Where might giving actually fill me up?'],
      journalPrompt: 'If I believed engagement could nourish me, I would...',
      mirrorPrompt: 'Guide me in exploring what sustainable engagement might look like',
    },
  },
  6: {
    corePattern: {
      whatThisIs: 'A drive toward security—anticipating problems, building alliances, testing what can be trusted.',
      whatYouMightNotice: 'You may notice yourself scanning for danger, questioning authority, valuing loyalty and reliability.',
      theTension: 'The vigilance that keeps you safe can also create the very anxiety it\'s trying to prevent.',
      whenItWorks: 'When balanced, this becomes discernment, loyalty, and the ability to prepare for real challenges.',
      tryThis: 'Notice one moment today where trust might serve you more than vigilance.',
      reflectionPrompts: ['What am I preparing for that might not happen?', 'Where is trust already warranted?'],
      journalPrompt: 'When I scan for danger, I\'m trying to protect myself from...',
      mirrorPrompt: 'Help me explore my relationship with trust and security',
    },
    howThisShowsUp: {
      whatThisIs: 'How this pattern expresses daily—through preparation, questioning, loyalty, and contingency thinking.',
      whatYouMightNotice: 'You may notice yourself playing devil\'s advocate, testing people\'s trustworthiness, preparing for worst cases.',
      theTension: 'What feels like prudent preparation can become chronic worry. Loyalty can become dependence.',
      whenItWorks: 'You\'re the one who sees problems before they happen. Your loyalty is deep and genuine.',
      tryThis: 'Trust one thing today without testing it first. Notice what happens.',
      reflectionPrompts: ['Where am I over-preparing?', 'Whose loyalty have I tested unnecessarily?'],
      journalPrompt: 'I test trustworthiness by...',
      mirrorPrompt: 'Help me see how my vigilance shows up in daily life',
    },
    underPressure: {
      whatThisIs: 'Under stress, you may move toward Type 3—becoming more competitive, image-focused, or workaholic.',
      whatYouMightNotice: 'You may notice yourself seeking validation through achievement, becoming more aggressive, proving yourself.',
      theTension: 'The usual caution gives way to action—sometimes reckless, sometimes productive.',
      whenItWorks: 'This movement can help you take action instead of just worrying—if channeled consciously.',
      tryThis: 'When you feel the push to prove yourself, pause. What do you actually need?',
      reflectionPrompts: ['What am I trying to prove?', 'What would be enough?'],
      journalPrompt: 'When I\'m anxious, I cope by...',
      mirrorPrompt: 'I\'m feeling the need to prove myself and want to explore it',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 9 qualities—becoming more peaceful, trusting, and able to relax.',
      whatYouMightNotice: 'You may notice yourself relaxing vigilance, trusting more easily, finding peace in uncertainty.',
      theTension: 'This can feel dangerous, but it\'s actually the calm you\'ve been seeking.',
      whenItWorks: 'You become a reassuring presence—someone who can be calm in crisis because you\'ve made peace with uncertainty.',
      tryThis: 'Let something remain uncertain today without trying to resolve it.',
      reflectionPrompts: ['What would peace with uncertainty feel like?', 'Where could I trust more?'],
      journalPrompt: 'When I relax my vigilance, I feel...',
      mirrorPrompt: 'Help me explore what peace and trust might look like',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—the anxiety that scans for danger, the fear of being without support.',
      whatYouMightNotice: 'Doubt that questions everything—including yourself. A fear that you can\'t handle things alone.',
      theTension: 'The belief that the world is dangerous keeps you in protective mode. The guidance you seek is already within.',
      whenItWorks: 'When seen clearly, you discover your own inner authority. Courage becomes available.',
      tryThis: 'Make one decision today without seeking external validation. Notice what happens.',
      reflectionPrompts: ['What do I already know that I\'m not trusting?', 'What if I could handle whatever comes?'],
      journalPrompt: 'The voice that says I can\'t handle this alone sounds like...',
      mirrorPrompt: 'Help me understand my difficulty trusting my own judgment',
    },
    growthPath: {
      whatThisIs: 'The direction of growth—toward inner courage and the discovery that you can trust yourself.',
      whatYouMightNotice: 'Moments of genuine inner knowing. Acting from your own authority rather than seeking permission.',
      theTension: 'Growth feels like jumping without a net. It\'s actually discovering you\'ve had wings all along.',
      whenItWorks: 'You access genuine courage—not fearlessness, but the ability to act despite fear.',
      tryThis: 'Trust your gut on one thing today. Don\'t second-guess it.',
      reflectionPrompts: ['What does my own authority feel like?', 'Where am I already trustworthy?'],
      journalPrompt: 'If I fully trusted myself, I would...',
      mirrorPrompt: 'Guide me in exploring what trusting myself might look like',
    },
  },
  7: {
    corePattern: {
      whatThisIs: 'A drive toward possibility—seeking stimulation, keeping options open, moving toward what\'s interesting.',
      whatYouMightNotice: 'You may notice yourself planning future adventures, reframing negatives, feeling trapped by limitation.',
      theTension: 'The pursuit of options can prevent the satisfaction of completion. Avoiding pain can mean avoiding depth.',
      whenItWorks: 'When balanced, this becomes genuine joy, creativity, and the gift of bringing lightness to heavy situations.',
      tryThis: 'Stay with one thing today until it\'s complete, even if something more interesting appears.',
      reflectionPrompts: ['What am I avoiding by staying in motion?', 'Where might depth serve me more than breadth?'],
      journalPrompt: 'When I feel the pull toward the next thing, I\'m moving away from...',
      mirrorPrompt: 'Help me explore my relationship with possibility and limitation',
    },
    howThisShowsUp: {
      whatThisIs: 'How this pattern expresses daily—through enthusiasm, planning, positive reframing, and novelty-seeking.',
      whatYouMightNotice: 'You may notice yourself making exciting plans, finding silver linings, feeling restless when contained.',
      theTension: 'What feels like optimism can be avoidance. The next adventure can be an escape from this moment.',
      whenItWorks: 'You bring joy and possibility. You see options others miss. You make things lighter.',
      tryThis: 'Notice when "excitement" is actually escape. What would staying feel like?',
      reflectionPrompts: ['What is this planning protecting me from?', 'What would satisfaction feel like right now?'],
      journalPrompt: 'I feel most restless when...',
      mirrorPrompt: 'Help me see how my pursuit of possibility shows up daily',
    },
    underPressure: {
      whatThisIs: 'Under stress, you may move toward Type 1—becoming more critical, perfectionist, and rigid.',
      whatYouMightNotice: 'You may notice yourself becoming judgmental, finding fault, getting stuck in how things should be.',
      theTension: 'The usual flexibility turns rigid. You may become the critic you normally avoid.',
      whenItWorks: 'This movement can help you focus and discern—if you don\'t get lost in criticism.',
      tryThis: 'When you notice criticism arising, ask: What am I actually anxious about?',
      reflectionPrompts: ['What standards am I suddenly applying?', 'What\'s underneath the criticism?'],
      journalPrompt: 'When I\'m stressed, I become critical about...',
      mirrorPrompt: 'I\'m feeling critical and want to understand what\'s happening',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 5 qualities—becoming more focused, thoughtful, and present.',
      whatYouMightNotice: 'You may notice yourself slowing down, going deeper, being satisfied with less stimulation.',
      theTension: 'This can feel boring, but it\'s actually the depth you\'ve been skimming over.',
      whenItWorks: 'You become someone who can both envision possibility AND be present to this moment.',
      tryThis: 'Go deep with one thing today instead of wide with many.',
      reflectionPrompts: ['What would depth serve in my life?', 'What is here when I stop moving?'],
      journalPrompt: 'When I slow down and go deep, I discover...',
      mirrorPrompt: 'Help me explore what presence and depth might feel like',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—the gluttony for experience, the fear of pain and limitation.',
      whatYouMightNotice: 'A constant reaching toward the next thing. A voice saying "don\'t stop, don\'t feel this, keep moving."',
      theTension: 'The belief that stopping means suffering keeps you in perpetual motion. What you\'re running from follows.',
      whenItWorks: 'When seen clearly, you can choose motion consciously. Staying becomes as viable as going.',
      tryThis: 'Feel something uncomfortable today without reframing or escaping. What happens?',
      reflectionPrompts: ['What am I afraid I\'ll feel if I stop?', 'What if pain was survivable?'],
      journalPrompt: 'The voice that says "keep moving" is protecting me from...',
      mirrorPrompt: 'Help me understand my resistance to staying with difficult feelings',
    },
    growthPath: {
      whatThisIs: 'The direction of growth—toward sobriety and the discovery that this moment is sufficient.',
      whatYouMightNotice: 'Moments of genuine contentment with what is. Satisfaction that doesn\'t require more.',
      theTension: 'Growth feels like giving up joy. It\'s actually finding joy that doesn\'t depend on novelty.',
      whenItWorks: 'You access genuine presence—joyful, satisfied, complete in this moment.',
      tryThis: 'Find sufficiency in something ordinary today. Let nothing need to be added.',
      reflectionPrompts: ['What would enough feel like?', 'Where is satisfaction already present?'],
      journalPrompt: 'If I believed this moment was sufficient, I would...',
      mirrorPrompt: 'Guide me in exploring what satisfaction and sufficiency might feel like',
    },
  },
  8: {
    corePattern: {
      whatThisIs: 'A drive toward strength—taking charge, protecting territory, living with intensity.',
      whatYouMightNotice: 'You may notice yourself reading power dynamics, confronting what seems unjust, taking up space unapologetically.',
      theTension: 'The strength that protects can also isolate. The power that creates safety can push away intimacy.',
      whenItWorks: 'When balanced, this becomes leadership, protection of the vulnerable, and the ability to take decisive action.',
      tryThis: 'Notice one moment today where softness might serve you more than strength.',
      reflectionPrompts: ['What am I protecting by staying strong?', 'Where might vulnerability create connection?'],
      journalPrompt: 'When I show strength, I\'m protecting...',
      mirrorPrompt: 'Help me explore my relationship with power and vulnerability',
    },
    howThisShowsUp: {
      whatThisIs: 'How this pattern expresses daily—through directness, intensity, protection, and boundary-setting.',
      whatYouMightNotice: 'You may notice yourself taking charge automatically, feeling discomfort with weakness, expressing forcefully.',
      theTension: 'What feels like authenticity can come across as aggression. Protection can become control.',
      whenItWorks: 'You create safety for others. You speak truth. You make things happen through sheer will.',
      tryThis: 'Let someone else take charge of something today. Notice what arises.',
      reflectionPrompts: ['Where am I controlling when I could be trusting?', 'What would it feel like to be protected?'],
      journalPrompt: 'I take charge because...',
      mirrorPrompt: 'Help me see how my need for control shows up in relationships',
    },
    underPressure: {
      whatThisIs: 'Under stress, you may move toward Type 5—becoming more withdrawn, secretive, or disengaged.',
      whatYouMightNotice: 'You may notice yourself pulling back, becoming isolated, hiding rather than confronting.',
      theTension: 'The usual expansiveness contracts. You may retreat instead of engaging.',
      whenItWorks: 'This movement can help you pause and think before acting—if you don\'t get lost in withdrawal.',
      tryThis: 'When you feel the pull to retreat, ask: What am I protecting?',
      reflectionPrompts: ['What makes me want to withdraw?', 'What would staying engaged require?'],
      journalPrompt: 'When I retreat, I\'m trying to protect...',
      mirrorPrompt: 'I\'m feeling withdrawn and want to understand what\'s happening',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 2 qualities—becoming more nurturing, considerate, and emotionally available.',
      whatYouMightNotice: 'You may notice yourself caring openly, considering others\' feelings, leading through support rather than force.',
      theTension: 'This can feel like weakness, but it\'s actually your power maturing into wisdom.',
      whenItWorks: 'You become a leader who creates not just safety but warmth. Your strength includes tenderness.',
      tryThis: 'Express care directly to someone today without any edge.',
      reflectionPrompts: ['What would it feel like to lead through care?', 'Where might softness be my strength?'],
      journalPrompt: 'When I lead with care rather than force, I feel...',
      mirrorPrompt: 'Help me explore what it means to be both strong and tender',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—the lust for intensity, the fear of being vulnerable or controlled.',
      whatYouMightNotice: 'An excess that goes all the way—in pleasure, confrontation, defense. A fear that softness means defeat.',
      theTension: 'The belief that vulnerability invites harm keeps your walls high. The intimacy you want stays out.',
      whenItWorks: 'When seen clearly, you discover that true strength includes tenderness. Vulnerability becomes power.',
      tryThis: 'Show one soft truth to someone you trust today. Notice what happens.',
      reflectionPrompts: ['What do I believe will happen if I\'m vulnerable?', 'What if softness was safe?'],
      journalPrompt: 'The part of me that stays guarded is afraid that...',
      mirrorPrompt: 'Help me understand my resistance to vulnerability',
    },
    growthPath: {
      whatThisIs: 'The direction of growth—toward innocence and the ability to be open without needing armor.',
      whatYouMightNotice: 'Moments of genuine tenderness. Openness that doesn\'t feel like weakness.',
      theTension: 'Growth feels like disarming. It\'s actually discovering that your heart is stronger than your armor.',
      whenItWorks: 'You access genuine innocence—powerful, present, able to receive as well as give.',
      tryThis: 'Let someone take care of you today. Receive without returning immediately.',
      reflectionPrompts: ['What would it feel like to not need armor?', 'Where is tenderness already present?'],
      journalPrompt: 'If I could be fully open without fear, I would...',
      mirrorPrompt: 'Guide me in exploring what it would mean to drop my guard',
    },
  },
  9: {
    corePattern: {
      whatThisIs: 'A drive toward harmony—keeping peace, avoiding conflict, merging with comfortable flow.',
      whatYouMightNotice: 'You may notice yourself going along to get along, seeing all sides, losing track of your own preferences.',
      theTension: 'The peace that maintains connection can come at the cost of your own voice. Harmony can mean self-erasure.',
      whenItWorks: 'When balanced, this becomes genuine peacemaking, the ability to see multiple perspectives, and creating true harmony.',
      tryThis: 'Notice one preference you have today and honor it, even if it creates minor friction.',
      reflectionPrompts: ['What do I actually want right now?', 'Where am I going along when I could speak up?'],
      journalPrompt: 'When I choose harmony over my own preferences, I\'m avoiding...',
      mirrorPrompt: 'Help me explore my relationship with conflict and my own voice',
    },
    howThisShowsUp: {
      whatThisIs: 'How this pattern expresses daily—through agreeableness, merging, comfortable routines, and conflict avoidance.',
      whatYouMightNotice: 'You may notice yourself adapting to others, losing track of time in comfortable activities, feeling invisible.',
      theTension: 'What feels like flexibility can be self-abandonment. Peace can come at the cost of presence.',
      whenItWorks: 'You create genuine calm. You help others feel heard. You see the bigger picture.',
      tryThis: 'State one opinion today without adding "but" or qualifying it.',
      reflectionPrompts: ['Where did I merge with someone else\'s preference today?', 'What is my own position?'],
      journalPrompt: 'I find it easiest to go along with others when...',
      mirrorPrompt: 'Help me see how my peacemaking shows up in relationships',
    },
    underPressure: {
      whatThisIs: 'Under stress, you may move toward Type 6—becoming more anxious, worried, and suspicious.',
      whatYouMightNotice: 'You may notice yourself worrying, seeking reassurance, becoming defensive or stubborn.',
      theTension: 'The usual calm gives way to anxiety. You may become unexpectedly rigid.',
      whenItWorks: 'This movement can wake you up—if you use the anxiety to finally take action on what matters.',
      tryThis: 'When worry arises, ask: What action have I been avoiding?',
      reflectionPrompts: ['What am I anxious about that I haven\'t addressed?', 'What action might relieve this?'],
      journalPrompt: 'When I\'m stressed, I notice myself worrying about...',
      mirrorPrompt: 'I\'m feeling anxious and want to understand what\'s underneath',
    },
    whenResourced: {
      whatThisIs: 'When healthy, you access Type 3 qualities—becoming more focused, energized, and effective.',
      whatYouMightNotice: 'You may notice yourself taking initiative, caring about your own goals, showing up with energy.',
      theTension: 'This can feel like losing your peace, but it\'s actually finding your power.',
      whenItWorks: 'You become a peaceful presence AND an effective force—someone who can be calm AND take action.',
      tryThis: 'Identify one of your own goals today and take a step toward it.',
      reflectionPrompts: ['What do I actually want to accomplish?', 'What would showing up fully look like?'],
      journalPrompt: 'When I pursue my own goals, I feel...',
      mirrorPrompt: 'Help me explore what it would mean to take action on what I want',
    },
    yourEdges: {
      whatThisIs: 'The deeper patterns—the sloth toward your own agenda, the fear of conflict and disconnection.',
      whatYouMightNotice: 'A numbing that blurs your own desires. A voice that says "it\'s not worth the disruption."',
      theTension: 'The belief that your presence might disturb keeps you invisible. The peace you seek requires you.',
      whenItWorks: 'When seen clearly, you discover that your presence is a gift, not a burden. Speaking up creates connection.',
      tryThis: 'Disagree with something today—kindly but clearly. Notice what happens.',
      reflectionPrompts: ['What would change if I let myself matter?', 'What if my presence was welcome?'],
      journalPrompt: 'The part of me that stays quiet believes...',
      mirrorPrompt: 'Help me understand why taking up space feels so hard',
    },
    growthPath: {
      whatThisIs: 'The direction of growth—toward right action and the recognition that your presence matters.',
      whatYouMightNotice: 'Moments of knowing what you want and moving toward it. Speaking your truth without losing connection.',
      theTension: 'Growth feels like creating conflict. It\'s actually creating wholeness.',
      whenItWorks: 'You access genuine engagement—present, expressed, maintaining peace that includes you.',
      tryThis: 'Name one thing you want today and take one step toward it.',
      reflectionPrompts: ['What is my right action here?', 'How might my voice serve the whole?'],
      journalPrompt: 'If I believed my presence and preferences truly mattered...',
      mirrorPrompt: 'Guide me in exploring what claiming my own voice might look like',
    },
  },
};

// Wing flavor descriptions - structured format for Deep Dive
// Format: Core Pattern | The Tradeoff | Potential Strength | Try This
const WING_FLAVORS: { [key: string]: { pattern: string; tradeoff: string; strength: string; experiment: string } } = {
  // Type 1 wings
  '1w9': {
    pattern: 'The 9-wing often softens Reformer energy with patience and a preference for harmony. You may notice a tendency to pick battles carefully—holding principles without forcing them, expressing idealism quietly rather than vocally.',
    tradeoff: 'The pull toward peace can sometimes delay necessary confrontation. Standards may simmer beneath the surface rather than being addressed directly.',
    strength: 'When integrated, this combination offers principled steadiness—the capacity to hold firm without rigidity, to improve without demanding.',
    experiment: 'Notice when you\'re choosing peace over clarity. What would it feel like to express one opinion today without softening it?'
  },
  '1w2': {
    pattern: 'The 2-wing often adds warmth to the Reformer drive—improvement expressed as care for others. You may notice your desire for things to be better showing up as wanting to help people do better.',
    tradeoff: 'The inner critic may extend to how well you serve others. Helping can become another arena for self-judgment.',
    strength: 'When integrated, this combination offers grounded mentorship—the ability to guide others toward growth while maintaining genuine warmth.',
    experiment: 'When helping feels like obligation, pause. What happens if you offer support without attachment to whether it\'s received "correctly"?'
  },
  
  // Type 2 wings
  '2w1': {
    pattern: 'The 1-wing often brings structure to the Helper pattern—a sense of doing it right, not just doing it. You may notice standards around how care "should" be given.',
    tradeoff: 'Self-criticism can arise when giving doesn\'t meet your own internal standards. The gift may feel tainted if it\'s not perfect.',
    strength: 'When integrated, this combination offers reliable, conscientious care—support others can count on, delivered with integrity.',
    experiment: 'Try giving something imperfectly and letting it be enough. Notice what arises when you release the need for your generosity to meet a standard.'
  },
  '2w3': {
    pattern: 'The 3-wing often adds energy and visibility to the Helper instinct. You may find yourself drawn to roles where care has impact—leading, organizing, being the one who makes things happen.',
    tradeoff: 'Being needed and being successful can become entangled. The applause for helping may start mattering more than the help itself.',
    strength: 'When integrated, this combination offers effective compassion—the ability to mobilize care at scale, to make helping happen.',
    experiment: 'Help someone invisibly this week. What do you notice about how it feels when no one sees your contribution?'
  },
  
  // Type 3 wings
  '3w2': {
    pattern: 'The 2-wing often brings warmth to the Achiever drive—success expressed through people, networks, being liked as well as respected.',
    tradeoff: 'Warmth can become performance. The charm that wins people over may disconnect from what you actually feel.',
    strength: 'When integrated, this combination offers inspiring presence—the capacity to achieve while bringing others along, to succeed without isolation.',
    experiment: 'Notice when warmth feels strategic versus spontaneous. What happens if you let someone see you uncertain or unprepared?'
  },
  '3w4': {
    pattern: 'The 4-wing often adds depth and aesthetic sensitivity to the Achiever energy. You may pursue success in distinctive ways—achievement with personal style, work that reflects something real.',
    tradeoff: 'Image and authenticity can pull in different directions. The desire to be both successful and genuine may create internal tension.',
    strength: 'When integrated, this combination offers meaningful achievement—success that carries personal signature, accomplishment that feels true.',
    experiment: 'Share work before it\'s polished. Notice the space between "good enough to show" and "perfectly crafted."'
  },
  
  // Type 4 wings
  '4w3': {
    pattern: 'The 3-wing often channels emotional depth into visible expression—creative output, performance, building something that reflects inner experience for others to witness.',
    tradeoff: 'The audience can become the measure of authenticity. External validation may start shaping what feels true inside.',
    strength: 'When integrated, this combination offers expressive power—the ability to make inner worlds visible, to create from depth in ways that reach others.',
    experiment: 'Make something you never show anyone. What does it feel like to create without an audience in mind?'
  },
  '4w5': {
    pattern: 'The 5-wing often adds intellectual depth to emotional exploration—processing feeling through analysis, symbol, or private creative work. You may find yourself drawn to understanding your inner world as much as feeling it.',
    tradeoff: 'The pull toward knowing can become withdrawal from connecting. Understanding may substitute for being understood.',
    strength: 'When integrated, this combination offers profound insight—the capacity to map emotional territory with precision, to name what others feel but cannot articulate.',
    experiment: 'Share a feeling before you\'ve fully figured it out. What happens when understanding isn\'t a prerequisite for connection?'
  },
  
  // Type 5 wings
  '5w4': {
    pattern: 'The 4-wing often brings emotional depth to the Investigator mind—analysis drawn to meaning, symbol, subjective experience. There may be a creative or artistic dimension to how you think.',
    tradeoff: 'The pull toward inner worlds can become isolation. Rich internal experience may substitute for external connection.',
    strength: 'When integrated, this combination offers creative insight—the ability to see patterns others miss, to think with both precision and feeling.',
    experiment: 'Share an idea before it\'s complete. Notice what it\'s like to think out loud rather than presenting finished thoughts.'
  },
  '5w6': {
    pattern: 'The 6-wing often adds practical concern to the Investigator stance—focus on systems, preparation, understanding how things work in order to navigate safely.',
    tradeoff: 'Thorough analysis can become anxious preparation. The pursuit of enough information may never feel complete.',
    strength: 'When integrated, this combination offers grounded expertise—knowledge that serves action, understanding that builds real security.',
    experiment: 'Act on 80% certainty. What happens when you trust what you already know is enough?'
  },
  
  // Type 6 wings
  '6w5': {
    pattern: 'The 5-wing often brings analytical depth to Loyalist vigilance—seeking security through knowledge, mastering systems, thinking through scenarios before they arrive.',
    tradeoff: 'Analysis can become another form of vigilance. The mind may generate threats faster than it resolves them.',
    strength: 'When integrated, this combination offers strategic wisdom—the ability to anticipate and prepare without being paralyzed by possibility.',
    experiment: 'Trust your first instinct on something small today. Notice what happens when you skip the analysis.'
  },
  '6w7': {
    pattern: 'The 7-wing often adds optimism to the Loyalist pattern—balancing worst-case with best-case, testing but also hoping. There may be warmth and humor alongside the vigilance.',
    tradeoff: 'Positivity can become another avoidance strategy. Hope may be used to bypass legitimate concerns rather than address them.',
    strength: 'When integrated, this combination offers resilient optimism—the ability to face reality clearly while maintaining access to lightness.',
    experiment: 'Sit with one worry without resolving or reframing it. What happens when you let a concern simply be present?'
  },
  
  // Type 7 wings
  '7w6': {
    pattern: 'The 6-wing often brings groundedness to Enthusiast energy—adventure with trusted people, more follow-through, loyalty alongside the love of options.',
    tradeoff: 'Anxiety may fuel the escape into possibilities. The pursuit of positive experience can be driven by what you\'re avoiding as much as what you\'re seeking.',
    strength: 'When integrated, this combination offers committed exploration—the ability to go deep with people and projects while maintaining joy.',
    experiment: 'Stay with one thing past the point of initial interest. What opens up when you resist the pull toward something new?'
  },
  '7w8': {
    pattern: 'The 8-wing often adds intensity to the Enthusiast pattern—assertive pursuit of experience, entrepreneurial energy, less patience for limits.',
    tradeoff: 'Force can override sensitivity. The drive toward more may bulldoze past discomfort that deserves attention.',
    strength: 'When integrated, this combination offers bold vision—the ability to pursue possibility with conviction, to make things happen.',
    experiment: 'Let something be difficult without fixing or leaving it. What happens when you stay present with discomfort?'
  },
  
  // Type 8 wings
  '8w7': {
    pattern: 'The 7-wing often adds energy and optimism to Challenger force—enjoying the game, the strategy, the possibilities. There may be a charismatic, expansive quality to how you move through the world.',
    tradeoff: 'Enthusiasm can mask vulnerability. The larger-than-life presence may keep others from seeing what\'s underneath.',
    strength: 'When integrated, this combination offers magnetic leadership—the ability to mobilize energy and inspire action while staying connected to joy.',
    experiment: 'Let someone see you at less than full strength. What happens when you don\'t need to be the biggest presence in the room?'
  },
  '8w9': {
    pattern: 'The 9-wing often brings steadiness to Challenger strength—quiet power, calm presence, force that doesn\'t need to announce itself.',
    tradeoff: 'Patience can become stubbornness. The unwillingness to push may be avoidance of conflict disguised as equanimity.',
    strength: 'When integrated, this combination offers grounded power—the ability to hold space, to protect without dominating, to lead through presence.',
    experiment: 'Express preference before you\'re certain it will be received well. Notice what it\'s like to want something openly.'
  },
  
  // Type 9 wings
  '9w8': {
    pattern: 'The 8-wing often gives the Peacemaker access to assertion—a quiet force that emerges when boundaries are crossed, stubbornness beneath the accommodation.',
    tradeoff: 'Anger may erupt rather than flow. Long periods of accommodation can end in intensity that surprises everyone, including you.',
    strength: 'When integrated, this combination offers peaceful strength—the ability to maintain harmony while honoring your own presence and needs.',
    experiment: 'Express disagreement before it becomes urgent. What happens when you voice friction early rather than late?'
  },
  '9w1': {
    pattern: 'The 1-wing often brings principle to the Peacemaker pattern—clearer opinions, a sense of right and wrong, even if expressing them directly still feels difficult.',
    tradeoff: 'Judgment may simmer beneath the agreeable surface. Internal criticism of self and others may coexist with external harmony.',
    strength: 'When integrated, this combination offers principled peace—the ability to hold values clearly while remaining genuinely open to others.',
    experiment: 'Voice one opinion today without apologizing for it. Notice what it feels like to take a clear position.'
  }
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
  inferred_wing: number | 'balanced';
  confidence: number;
  confidence_tier: string;
  is_close?: boolean;
  top_candidates: { type: number; probability: number }[];
  state_calibration?: {
    energy_state: string;
    life_context: string;
    answer_frame: string;
  };
  source?: 'assessment' | 'self_declared';
  method?: string;
}

interface Props {
  result?: EnneagramResult;  // Make optional - will fetch internally if not provided
  userId: string;
  onOpenChat?: () => void;
}

type TabType = 'summary' | 'at_a_glance' | 'today' | 'deep_dive';
type EnergyState = 'low' | 'neutral' | 'high';
type MasteryLevel = 'reactive' | 'average' | 'resourced';

// ============================================
// COMPONENT
// ============================================

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function EnneagramLensView({ result: propResult, userId, onOpenChat }: Props) {
  const router = useRouter();
  
  // Theme support - use the useTheme hook
  const { theme, isDark } = useTheme();
  
  // Internal result state (fetch if not provided as prop)
  const [internalResult, setInternalResult] = useState<EnneagramResult | null>(propResult || null);
  const [resultLoading, setResultLoading] = useState(!propResult);
  
  // Use prop result if provided, otherwise use internal fetched result
  const result = propResult || internalResult;
  
  // Derived values with null safety
  const core = result?.inferred_core || 0;
  const wing = result?.inferred_wing || 0;
  const wings = WING_NUMBERS[core] || { left: 0, right: 0 };
  const otherWing = wing === wings?.left ? wings?.right : wings?.left;
  
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [energyState, setEnergyState] = useState<EnergyState | null>(
    (result?.state_calibration?.energy_state as EnergyState) || null
  );
  const [selectedMasteryLevel, setSelectedMasteryLevel] = useState<MasteryLevel>('average');
  const [showRetakeModal, setShowRetakeModal] = useState(false);
  
  // Deep Dive accordion state
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['core_story']));
  
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
  
  // Deep Dive state (new API-driven content)
  const [deepDiveData, setDeepDiveData] = useState<EnneagramDeepDiveResponse | null>(null);
  const [deepDiveLoading, setDeepDiveLoading] = useState(false);
  
  // Pattern Drift state
  const [patternDrift, setPatternDrift] = useState<PatternDriftResponse | null>(null);
  const [patternDriftLoading, setPatternDriftLoading] = useState(false);
  
  // Debug logging on mount
  useEffect(() => {
    console.log('[EnneagramLensView] MOUNTED');
    console.log('[EnneagramLensView] Build:', BUILD_VERSION, BUILD_ID);
    console.log('[EnneagramLensView] userId:', userId);
    console.log('[EnneagramLensView] renderTabs will be called:', typeof renderTabs);
  }, []);

  // Fetch enneagram result if not provided as prop
  useEffect(() => {
    const fetchResult = async () => {
      if (propResult || !userId) return;
      
      console.log('[EnneagramLensView] Fetching enneagram result for user:', userId);
      setResultLoading(true);
      try {
        const data = await getEnneagramResult(userId);
        // API returns { has_result: boolean, result: EnneagramResult }
        const resultData = data?.result || data;
        console.log('[EnneagramLensView] Fetched result:', resultData?.inferred_core, resultData?.inferred_wing);
        setInternalResult(resultData);
      } catch (error) {
        console.error('[EnneagramLensView] Failed to fetch result:', error);
        setInternalResult(null);
      } finally {
        setResultLoading(false);
      }
    };
    fetchResult();
  }, [userId, propResult]);

  // Debug logging on tab change
  useEffect(() => {
    console.log('[EnneagramLensView] activeTab changed to:', activeTab);
  }, [activeTab]);

  // Q&A Modal state (hidden initially per user request)
  const [showQAModal, setShowQAModal] = useState(false);
  const [qaQuestion, setQaQuestion] = useState('');
  const [qaAnswer, setQaAnswer] = useState<string | null>(null);
  const [qaLoading, setQaLoading] = useState(false);
  
  // At a Glance collapsible section states
  const [drivingExpanded, setDrivingExpanded] = useState(false);
  const [protectsExpanded, setProtectsExpanded] = useState(false);
  const [opensExpanded, setOpensExpanded] = useState(false);
  
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
          confidence_tier: result?.confidence_tier || 'low',
          is_close: result.is_close || false,
          top_candidates: (result?.top_candidates || []).slice(0, 2),
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

  // Load Deep Dive data when tab is selected
  useEffect(() => {
    const loadDeepDive = async () => {
      if (!userId || activeTab !== 'deep_dive') return;
      
      // Always reload to get fresh keystone data
      setDeepDiveLoading(true);
      try {
        const response = await getEnneagramDeepDive(userId);
        setDeepDiveData(response);
        console.log('[EnneagramLensView] Deep dive data loaded, has keystone:', !!response?.keystone_explanation);
      } catch (error) {
        console.error('Failed to load deep dive:', error);
      } finally {
        setDeepDiveLoading(false);
      }
    };
    loadDeepDive();
  }, [userId, activeTab]);

  // Load Pattern Drift data (lazy load on Overview tab)
  useEffect(() => {
    const loadPatternDrift = async () => {
      if (!userId || activeTab !== 'summary' || patternDrift) return;
      
      setPatternDriftLoading(true);
      try {
        const response = await getPatternDrift(userId);
        setPatternDrift(response);
      } catch (error) {
        console.error('Failed to load pattern drift:', error);
      } finally {
        setPatternDriftLoading(false);
      }
    };
    loadPatternDrift();
  }, [userId, activeTab, patternDrift]);

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

  const handleEditType = () => {
    // Navigate to the self-declare screen to manually edit type
    router.push('/enneagram/self-declare');
  };

  // ============================================
  // RENDER HELPERS
  // ============================================

  const renderTabs = () => (
    <View style={[styles.tabContainer, { backgroundColor: theme.surface, borderBottomColor: theme.border }]}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'summary' && styles.activeTab, activeTab === 'summary' && { borderBottomColor: theme.text }]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'summary' && { color: theme.text }]}>
          Overview
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'at_a_glance' && styles.activeTab, activeTab === 'at_a_glance' && { borderBottomColor: theme.text }]}
        onPress={() => setActiveTab('at_a_glance')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'at_a_glance' && { color: theme.text }]}>
          At a Glance
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'today' && styles.activeTab, activeTab === 'today' && { borderBottomColor: theme.text }]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'today' && { color: theme.text }]}>
          Today
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab, activeTab === 'deep_dive' && { borderBottomColor: theme.text }]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text }]}>
          Deep Dive
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderConfidenceBadge = () => {
    const tier = result?.confidence_tier;
    const isSelfDeclared = result?.source === 'self_declared' || result?.method === 'self_declared';
    
    // Self-declared results show "Self-declared" instead of confidence
    if (isSelfDeclared) {
      return (
        <View style={styles.sourceBadge}>
          <Text style={[styles.sourceBadgeText, { color: theme.textSecondary }]}>Self-declared</Text>
        </View>
      );
    }
    
    // Assessment results show confidence tier with improved contrast
    return (
      <View style={[
        styles.confidenceBadge,
        tier === 'high' && styles.confidenceHigh,
        tier === 'medium' && styles.confidenceMedium,
        tier === 'low' && styles.confidenceLow,
      ]}>
        <Text style={[
          styles.confidenceText,
          tier === 'high' && styles.confidenceHighText,
          tier === 'medium' && styles.confidenceMediumText,
          tier === 'low' && styles.confidenceLowText,
        ]}>
          {tier === 'high' ? 'High' : tier === 'medium' ? 'Medium' : 'Low'} Confidence
        </Text>
      </View>
    );
  };
  
  // ============================================
  // CHAT BOX COMPONENT
  // ============================================
  
  const renderAskLensButton = () => (
    <View style={styles.askLensContainer}>
      <TouchableOpacity
        style={[styles.askLensButton, { backgroundColor: theme.text }]}
        onPress={() => setShowQAModal(true)}
      >
        <Text style={[styles.askLensText, { color: theme.background }]}>Ask about this lens</Text>
      </TouchableOpacity>
      <Text style={[styles.askLensDisclaimer, { color: theme.textTertiary }]}>
        A lens for understanding patterns, not a definition of identity.
      </Text>
    </View>
  );

  // ============================================
  // SUMMARY TAB
  // ============================================

  const renderSummaryTab = () => {
    // Guard against no data
    if (!core || core === 0) {
      return (
        <View style={[styles.structureCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <Text style={[styles.structureType, { color: theme.text }]}>
            No Enneagram Result Yet
          </Text>
          <Text style={[styles.structureBridge, { color: theme.textSecondary }]}>
            Complete the assessment to see your pattern analysis.
          </Text>
        </View>
      );
    }
    
    const wingNum = typeof wing === 'number' ? wing : (wing === 'balanced' ? null : parseInt(wing));
    const wingKey = wingNum && wingNum !== 0 ? `${core}w${wingNum}` : null;
    const stressType = STRESS_DIRECTIONS[core];
    const growthType = GROWTH_DIRECTIONS[core];
    const confidenceTier = result?.confidence_tier || 'medium';
    const isSelfDeclared = result?.source === 'self_declared' || result?.method === 'self_declared';
    
    // Get hero summary sentence
    const getHeroSummary = () => {
      if (wingKey && HERO_SUMMARY_SENTENCES[wingKey]) {
        return HERO_SUMMARY_SENTENCES[wingKey];
      }
      return CORE_MOTIVATIONS[core] || '';
    };

    // Get Core Story content
    const coreStory = CORE_STORY_CONTENT[core];
    
    // Compute normalized top 3 signals for display
    // If we only have raw probabilities, normalize them to show relative strength
    const getTopSignals = () => {
      const candidates = result?.top_candidates || [];
      if (candidates.length === 0) {
        // Fallback: create mock signals from core/wing
        return [
          { type: core, probability: 0.75 },
          { type: wingNum || (core === 9 ? 1 : core + 1), probability: 0.35 },
          { type: growthType, probability: 0.22 },
        ];
      }
      
      // Take top 3 and normalize if needed
      const top3 = candidates.slice(0, 3);
      const maxProb = Math.max(...top3.map(c => c.probability));
      
      // If max is 1.0 or very close, normalize to show relative differences
      if (maxProb >= 0.95) {
        // Distribute scores more meaningfully
        return top3.map((c, i) => ({
          type: c.type,
          // Scale down from max to show variation
          probability: Math.max(0.20, c.probability * (i === 0 ? 0.85 : i === 1 ? 0.45 : 0.30))
        }));
      }
      
      return top3;
    };
    
    const topSignals = getTopSignals();
    
    return (
      <>
        {/* ============================================ */}
        {/* SECTION 1: HERO RESULT CARD (TOP OF PAGE) */}
        {/* "This is my result." */}
        {/* ============================================ */}
        <View style={[styles.heroResultCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          {/* Large Result Label */}
          <Text style={[styles.heroResultLabel, { color: theme.text }]}>
            {wingNum ? `${core}w${wingNum}` : `Type ${core}`}
          </Text>
          
          {/* Type Name Subtitle */}
          <Text style={[styles.heroResultName, { color: theme.textSecondary }]}>
            {TYPE_NAMES[core]}
          </Text>
          
          {/* Confidence Badge */}
          <View style={styles.heroConfidenceRow}>
            {isSelfDeclared ? (
              <View style={[styles.heroConfidenceBadge, { backgroundColor: theme.surfaceLight }]}>
                <Text style={[styles.heroConfidenceText, { color: theme.textSecondary }]}>Self-declared</Text>
              </View>
            ) : (
              <View style={[
                styles.heroConfidenceBadge,
                { 
                  backgroundColor: confidenceTier === 'high' 
                    ? '#2E7D3220' 
                    : confidenceTier === 'medium'
                      ? '#F5A62320'
                      : '#C6282820',
                }
              ]}>
                <Text style={[
                  styles.heroConfidenceText,
                  { 
                    color: confidenceTier === 'high' 
                      ? '#2E7D32' 
                      : confidenceTier === 'medium'
                        ? '#F5A623'
                        : '#C62828',
                  }
                ]}>
                  {confidenceTier === 'high' ? 'High' : confidenceTier === 'medium' ? 'Medium' : 'Low'} Confidence
                </Text>
              </View>
            )}
          </View>
          
          {/* Summary Sentence */}
          <Text style={[styles.heroSummaryText, { color: theme.text }]}>
            {getHeroSummary()}
          </Text>
          
          {/* Small Note */}
          <Text style={[styles.heroNote, { color: theme.textTertiary }]}>
            This lens reflects strategy, not identity.
          </Text>
        </View>

        {/* ============================================ */}
        {/* SECTION 2: CORE STORY — TYPE X */}
        {/* "This is what Type X means." */}
        {/* ============================================ */}
        <View style={[styles.coreStoryCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <Text style={[styles.coreStoryTitle, { color: theme.textTertiary }]}>
            CORE STORY — TYPE {core}
          </Text>
          
          {/* Core Pattern */}
          <View style={styles.coreStorySection}>
            <Text style={[styles.coreStorySectionTitle, { color: theme.text }]}>Core Pattern</Text>
            <Text style={[styles.coreStoryBody, { color: theme.textSecondary }]}>
              {coreStory?.what || CORE_PATTERNS[core]}
            </Text>
          </View>
          
          {/* What Drives This */}
          <View style={styles.coreStorySection}>
            <Text style={[styles.coreStorySectionTitle, { color: theme.text }]}>What Drives This</Text>
            <Text style={[styles.coreStoryBody, { color: theme.textSecondary }]}>
              {coreStory?.drives || PATTERN_DRIVERS[core]}
            </Text>
          </View>
          
          {/* Tradeoff to Watch */}
          <View style={styles.coreStorySection}>
            <Text style={[styles.coreStorySectionTitle, { color: theme.text }]}>Tradeoff to Watch</Text>
            <Text style={[styles.coreStoryBody, { color: theme.textSecondary }]}>
              {coreStory?.tradeoff || ''}
            </Text>
          </View>
          
          {/* Where This Helps */}
          <View style={styles.coreStorySection}>
            <Text style={[styles.coreStorySectionTitle, { color: theme.text }]}>Where This Often Helps</Text>
            <Text style={[styles.coreStoryBody, { color: theme.textSecondary }]}>
              {coreStory?.helps || ''}
            </Text>
          </View>
        </View>

        {/* ============================================ */}
        {/* SECTION 3: HOW WING SHAPES THIS */}
        {/* "This is how the wing changes it." */}
        {/* ============================================ */}
        {wingKey && WING_INFLUENCE_CONCISE[wingKey] && (
          <View style={[styles.wingInfluenceCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
            <Text style={[styles.wingInfluenceTitle, { color: theme.textTertiary }]}>
              HOW {wingNum} SHAPES THIS
            </Text>
            <Text style={[styles.wingInfluenceBody, { color: theme.text }]}>
              {WING_INFLUENCE_CONCISE[wingKey]}
            </Text>
          </View>
        )}

        {/* ============================================ */}
        {/* SECTION 4: OTHER IMPORTANT SUMMARY DATA */}
        {/* Growth/Stress directions and key context */}
        {/* ============================================ */}
        <View style={[styles.summaryDataCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <Text style={[styles.summaryDataTitle, { color: theme.textTertiary }]}>
            MOVEMENT PATTERNS
          </Text>
          
          {/* Growth Direction */}
          <View style={styles.movementRow}>
            <View style={[styles.movementIcon, { backgroundColor: '#2E7D3220' }]}>
              <Text style={styles.movementIconText}>↗</Text>
            </View>
            <View style={styles.movementContent}>
              <Text style={[styles.movementLabel, { color: '#2E7D32' }]}>
                Growth → Type {growthType}
              </Text>
              <Text style={[styles.movementDesc, { color: theme.textSecondary }]}>
                When resourced, you access {TYPE_NAMES[growthType]} qualities
              </Text>
            </View>
          </View>
          
          {/* Stress Direction */}
          <View style={styles.movementRow}>
            <View style={[styles.movementIcon, { backgroundColor: '#C6282820' }]}>
              <Text style={styles.movementIconText}>↘</Text>
            </View>
            <View style={styles.movementContent}>
              <Text style={[styles.movementLabel, { color: '#C62828' }]}>
                Stress → Type {stressType}
              </Text>
              <Text style={[styles.movementDesc, { color: theme.textSecondary }]}>
                Under pressure, you may show {TYPE_NAMES[stressType]} patterns
              </Text>
            </View>
          </View>
        </View>

        {/* ============================================ */}
        {/* SECTION 5: TOP 3 HIGHEST INDICATORS CHART */}
        {/* "Here are my top comparative type strengths." */}
        {/* ============================================ */}
        <View style={[styles.signalsCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <Text style={[styles.signalsTitle, { color: theme.textTertiary }]}>
            TOP SIGNALS
          </Text>
          <Text style={[styles.signalsSubtitle, { color: theme.textTertiary }]}>
            Relative strength of type indicators
          </Text>
          
          {topSignals.map((candidate, index) => {
            const percentage = Math.round(candidate.probability * 100);
            // Scale bar width relative to highest score
            const maxPercent = Math.round(topSignals[0].probability * 100);
            const barWidth = `${Math.round((percentage / maxPercent) * 100)}%`;
            const isTop = index === 0;
            
            return (
              <View key={candidate.type} style={styles.signalRow}>
                <View style={styles.signalTypeContainer}>
                  <Text style={[styles.signalType, { color: theme.text }]}>
                    Type {candidate.type}
                  </Text>
                </View>
                <View style={[styles.signalBarContainer, { backgroundColor: theme.surfaceLight }]}>
                  <View 
                    style={[
                      styles.signalBar, 
                      { 
                        width: barWidth as any,
                        backgroundColor: isTop ? theme.accent : `${theme.accent}60`,
                      }
                    ]} 
                  />
                </View>
                <Text style={[styles.signalPercent, { color: theme.textSecondary }]}>
                  {percentage}%
                </Text>
              </View>
            );
          })}
        </View>

        {/* ============================================ */}
        {/* SECTION 6: ENNEAGRAM WHEEL (SUPPORTING STRUCTURE) */}
        {/* "Here is the structural diagram underneath it." */}
        {/* Wheel is LOWER on the page - supporting, not dominant */}
        {/* ============================================ */}
        <View style={[styles.wheelSupportCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <Text style={[styles.wheelSupportTitle, { color: theme.textTertiary }]}>
            How your pattern moves
          </Text>
          
          {/* Classic Enneagram Wheel with inner geometry */}
          <EnneagramWheel
            coreType={core}
            wing={wingNum}
            size={260}
            showLabels={true}
            compact={false}
          />
        </View>

        {/* ============================================ */}
        {/* SECTION 7: ASK ABOUT THIS LENS CTA */}
        {/* "Now I can ask about this lens." */}
        {/* ============================================ */}
        {renderAskLensButton()}
      </>
    );
  };

  // ============================================
  // AT A GLANCE TAB
  // ============================================

  const renderAtAGlanceTab = () => {
    const details = computedDetails || deepDiveData?.computed_details;
    
    // Wing stance display
    const getWingStanceDisplay = () => {
      if (!details) return 'Loading...';
      if (details.wing_balance_label === 'balanced') {
        return 'Wing access still developing';
      }
      return details.wing_openness_hint || `${wing !== 'balanced' ? `${core}w${wing}` : 'balanced'}`;
    };

    // Social style tags
    const socialStyleTags = details?.social_style_tags || [];
    
    // Basic fear and desire based on type (with updated labels)
    const TYPE_BASIC_FEARS: { [key: number]: string } = {
      1: 'Being corrupt, evil, or defective',
      2: 'Being unwanted or unloved',
      3: 'Being worthless or without value',
      4: 'Having no identity or significance',
      5: 'Being useless, incompetent, or incapable',
      6: 'Being without support or guidance',
      7: 'Being deprived or trapped in pain',
      8: 'Being controlled or harmed by others',
      9: 'Loss of connection or fragmentation',
    };
    
    const TYPE_BASIC_DESIRES: { [key: number]: string } = {
      1: 'To be good, balanced, and have integrity',
      2: 'To be loved and appreciated',
      3: 'To be valuable and worthwhile',
      4: 'To find themselves and their significance',
      5: 'To be capable and competent',
      6: 'To have security and support',
      7: 'To be satisfied and content',
      8: 'To protect themselves and control their destiny',
      9: 'To have inner peace and stability',
    };
    
    // Get pattern layers for this type
    const patternLayers = PATTERN_LAYERS[core];

    return (
      <>
        {/* Loading state */}
        {traitsLoading && !details && (
          <View style={[styles.loadingContainer, { backgroundColor: theme.cardBg }]}>
            <ActivityIndicator size="small" color={theme.textSecondary} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>Loading profile...</Text>
          </View>
        )}

        {/* ============================================ */}
        {/* PATTERN SUMMARY CARD - NEW TOP SECTION */}
        {/* ============================================ */}
        {details && patternLayers && (
          <View style={[styles.patternSummaryCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
            <Text style={[styles.patternSummaryTitle, { color: theme.text }]}>Your Pattern</Text>
            
            {/* Paragraph 1: How you tend to move */}
            <Text style={[styles.patternSummaryBody, { color: theme.textSecondary }]}>
              {patternLayers.howYouMove}
            </Text>
            
            {/* Paragraph 2: What you subtly avoid */}
            <Text style={[styles.patternSummaryBody, { color: theme.textSecondary }]}>
              {patternLayers.whatYouAvoid}
            </Text>
            
            {/* Paragraph 3: What sits underneath */}
            <Text style={[styles.patternSummaryBody, styles.patternSummaryEmphasized, { color: theme.textTertiary }]}>
              {patternLayers.whatSitsUnderneath}
            </Text>
          </View>
        )}

        {/* ============================================ */}
        {/* COLLAPSIBLE SUB-SECTIONS */}
        {/* ============================================ */}
        {details && patternLayers && (
          <>
            {/* Section A: What's driving this */}
            <TouchableOpacity 
              style={[styles.collapsibleSection, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}
              onPress={() => setDrivingExpanded(!drivingExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.collapsibleHeader}>
                <Text style={[styles.collapsibleTitle, { color: theme.text }]}>What's driving this</Text>
                <Text style={[styles.collapsibleChevron, { color: theme.textTertiary }]}>
                  {drivingExpanded ? '▲' : '▼'}
                </Text>
              </View>
              {drivingExpanded && (
                <View style={styles.collapsibleContent}>
                  <View style={styles.collapsibleItem}>
                    <Text style={[styles.collapsibleItemLabel, { color: theme.textTertiary }]}>Emotional tendency</Text>
                    <Text style={[styles.collapsibleItemText, { color: theme.textSecondary }]}>
                      {patternLayers.emotionalTendency}
                    </Text>
                  </View>
                  <View style={styles.collapsibleItem}>
                    <Text style={[styles.collapsibleItemLabel, { color: theme.textTertiary }]}>Thinking tendency</Text>
                    <Text style={[styles.collapsibleItemText, { color: theme.textSecondary }]}>
                      {patternLayers.thinkingTendency}
                    </Text>
                  </View>
                </View>
              )}
            </TouchableOpacity>

            {/* Section B: What this protects you from */}
            <TouchableOpacity 
              style={[styles.collapsibleSection, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}
              onPress={() => setProtectsExpanded(!protectsExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.collapsibleHeader}>
                <Text style={[styles.collapsibleTitle, { color: theme.text }]}>What this protects you from</Text>
                <Text style={[styles.collapsibleChevron, { color: theme.textTertiary }]}>
                  {protectsExpanded ? '▲' : '▼'}
                </Text>
              </View>
              {protectsExpanded && (
                <View style={styles.collapsibleContent}>
                  <View style={styles.collapsibleItem}>
                    <Text style={[styles.collapsibleItemLabel, { color: theme.textTertiary }]}>What you avoid</Text>
                    <Text style={[styles.collapsibleItemText, { color: theme.textSecondary }]}>
                      {patternLayers.avoidancePattern}
                    </Text>
                  </View>
                  <View style={styles.collapsibleItem}>
                    <Text style={[styles.collapsibleItemLabel, { color: theme.textTertiary }]}>The inner voice</Text>
                    <Text style={[styles.collapsibleItemText, styles.collapsibleItemQuote, { color: theme.textSecondary }]}>
                      {patternLayers.antiSelfPattern}
                    </Text>
                  </View>
                </View>
              )}
            </TouchableOpacity>

            {/* Section C: When this opens */}
            <TouchableOpacity 
              style={[styles.collapsibleSection, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}
              onPress={() => setOpensExpanded(!opensExpanded)}
              activeOpacity={0.7}
            >
              <View style={styles.collapsibleHeader}>
                <Text style={[styles.collapsibleTitle, { color: theme.text }]}>When this opens</Text>
                <Text style={[styles.collapsibleChevron, { color: theme.textTertiary }]}>
                  {opensExpanded ? '▲' : '▼'}
                </Text>
              </View>
              {opensExpanded && (
                <View style={styles.collapsibleContent}>
                  <Text style={[styles.collapsibleItemText, { color: theme.textSecondary }]}>
                    {patternLayers.growthDirection}
                  </Text>
                </View>
              )}
            </TouchableOpacity>
          </>
        )}

        {/* ============================================ */}
        {/* STRUCTURE BEHIND YOUR PATTERN (Existing table) */}
        {/* ============================================ */}
        {details && (
          <>
            <View style={[styles.structureSectionHeader, { borderTopColor: theme.border }]}>
              <Text style={[styles.structureSectionTitle, { color: theme.textTertiary }]}>
                STRUCTURE BEHIND YOUR PATTERN
              </Text>
            </View>
            
            {/* Profile Card */}
            <View style={[styles.glanceCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
              {/* Wing Stance Row */}
              <View style={styles.glanceRow}>
                <View style={styles.glanceContent}>
                  <Text style={[styles.glanceLabel, { color: theme.textTertiary }]}>Wing Stance</Text>
                  <Text style={[styles.glanceValue, { color: theme.text }]}>{getWingStanceDisplay()}</Text>
                </View>
              </View>
              
              {/* Center Row */}
              <View style={styles.glanceRow}>
                <View style={styles.glanceContent}>
                  <Text style={[styles.glanceLabel, { color: theme.textTertiary }]}>Center</Text>
                  <Text style={[styles.glanceValue, { color: theme.text }]}>{formatGroupLabel(details.center)}</Text>
                </View>
              </View>
              
              {/* Hornevian Group Row */}
              <View style={styles.glanceRow}>
                <View style={styles.glanceContent}>
                  <Text style={[styles.glanceLabel, { color: theme.textTertiary }]}>Hornevian Group</Text>
                  <Text style={[styles.glanceValue, { color: theme.text }]}>{formatGroupLabel(details.hornevian_group)}</Text>
                </View>
              </View>
              
              {/* Harmonic Group Row */}
              <View style={styles.glanceRow}>
                <View style={styles.glanceContent}>
                  <Text style={[styles.glanceLabel, { color: theme.textTertiary }]}>Harmonic Group</Text>
                  <Text style={[styles.glanceValue, { color: theme.text }]}>{formatGroupLabel(details.harmonic_group)}</Text>
                </View>
              </View>
              
              {/* Growth Direction Row */}
              <View style={styles.glanceRow}>
                <View style={styles.glanceContent}>
                  <Text style={[styles.glanceLabel, { color: theme.textTertiary }]}>Growth Direction</Text>
                  <Text style={[styles.glanceValue, { color: theme.text }]}>Toward Type {details.growth_line_to}</Text>
                </View>
              </View>
              
              {/* Stress Direction Row */}
              <View style={styles.glanceRow}>
                <View style={styles.glanceContent}>
                  <Text style={[styles.glanceLabel, { color: theme.textTertiary }]}>Stress Direction</Text>
                  <Text style={[styles.glanceValue, { color: theme.text }]}>Toward Type {details.stress_line_to}</Text>
                </View>
              </View>
            </View>

            {/* Social Style Card - Updated label */}
            {socialStyleTags.length > 0 && (
              <View style={[styles.glanceCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
                <Text style={[styles.glanceSectionTitle, { color: theme.textTertiary }]}>HOW YOU TEND TO SHOW UP</Text>
                <View style={styles.glanceTagsContainer}>
                  {socialStyleTags.map((tag, index) => (
                    <View key={index} style={[styles.glanceTag, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
                      <Text style={[styles.glanceTagText, { color: theme.text }]}>{tag}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Quick Reference Card - Updated labels */}
            <View style={[styles.glanceCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
              <Text style={[styles.glanceSectionTitle, { color: theme.textTertiary }]}>QUICK REFERENCE</Text>
              <View style={styles.glanceRefGrid}>
                <View style={styles.glanceRefItem}>
                  <Text style={[styles.glanceRefLabel, { color: theme.textTertiary }]}>What this pattern is trying to avoid</Text>
                  <Text style={[styles.glanceRefValue, { color: theme.text }]}>{TYPE_BASIC_FEARS[core]}</Text>
                </View>
                <View style={styles.glanceRefItem}>
                  <Text style={[styles.glanceRefLabel, { color: theme.textTertiary }]}>What this pattern is seeking</Text>
                  <Text style={[styles.glanceRefValue, { color: theme.text }]}>{TYPE_BASIC_DESIRES[core]}</Text>
                </View>
              </View>
            </View>

            {/* Confidence Badge */}
            <View style={styles.glanceFooter}>
              <Text style={[styles.glanceFooterText, { color: theme.textTertiary }]}>
                {result?.confidence_tier === 'high' ? 'High' : result?.confidence_tier === 'medium' ? 'Moderate' : 'Low'} confidence
              </Text>
              <Text style={[styles.glanceFooterText, { color: theme.textTertiary }]}>
                {' '}·{' '}Based on assessment results
              </Text>
            </View>

            {/* Chat Box */}
            {renderAskLensButton()}
          </>
        )}
      </>
    );
  };

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
        <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>Today Check-in</Text>
          <Text style={[styles.cardBody, { color: theme.textSecondary }]}>What&apos;s your energy right now?</Text>
          <View style={styles.energyButtons}>
            {(['low', 'neutral', 'high'] as EnergyState[]).map((state) => (
              <TouchableOpacity
                key={state}
                style={[
                  styles.energyButton,
                  { borderColor: theme.border },
                  energyState === state && [styles.energyButtonSelected, { backgroundColor: theme.text }]
                ]}
                onPress={() => handleEnergySelect(state)}
              >
                <Text style={[
                  styles.energyButtonText,
                  { color: theme.text },
                  energyState === state && { color: theme.background }
                ]}>
                  {state.charAt(0).toUpperCase() + state.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
        
        {/* Daily Micro-Lesson Card */}
        <View style={[styles.microLessonCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.microLessonHeader}>
            <View>
              <Text style={[styles.microLessonTitle, { color: theme.text }]}>Daily Micro-Lesson</Text>
              <Text style={[styles.microLessonSubtitle, { color: theme.textTertiary }]}>Type {core} practice</Text>
            </View>
          </View>
          <Text style={[styles.microLessonBody, { color: theme.textSecondary }]}>
            {renderBoldText(todaysLesson, styles.microLessonBodyText, styles.microLessonBoldText)}
          </Text>
          <View style={styles.microLessonFooter}>
            <View style={styles.microLessonRotates}>
              <Text style={[styles.microLessonRotatesText, { color: theme.textTertiary }]}>Rotates daily</Text>
            </View>
            <TouchableOpacity 
              style={styles.microLessonAskButton}
              onPress={() => {
                setChatExpanded(true);
                setActiveCardContext('practice');
              }}
            >
              <Text style={[styles.microLessonAskText, { color: theme.accent }]}>Ask about this</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Stress Pattern Card */}
        <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.cardHeader}>
            <Text style={[styles.cardTitle, { color: theme.text }]}>Watch For (Stress)</Text>
          </View>
          <Text style={[styles.cardBody, { color: theme.textSecondary }]}>
            {STRESS_PATTERNS[core]?.pattern || 'Under stress, your patterns may shift.'}
          </Text>
        </View>

        {/* Growth Pattern Card */}
        <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.cardHeader}>
            <Text style={[styles.cardTitle, { color: theme.text }]}>Access (Growth)</Text>
          </View>
          <Text style={[styles.cardBody, { color: theme.textSecondary }]}>
            {GROWTH_PATTERNS[core]?.pattern || 'Growth invites new perspectives and behaviors.'}
          </Text>
        </View>

        {/* 2-Minute Practice Card */}
        <View style={[styles.practiceCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
          <Text style={[styles.practiceLabel, { color: theme.textTertiary }]}>2-MINUTE PRACTICE</Text>
          <Text style={[styles.practiceBody, { color: theme.text }]}>
            {getPractice()}
          </Text>
        </View>

        {/* Journal Prompt Card */}
        <View style={[styles.promptCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
          <Text style={[styles.promptLabel, { color: theme.textTertiary }]}>JOURNAL PROMPT</Text>
          <Text style={[styles.promptBody, { color: theme.text }]}>
            {JOURNAL_PROMPTS[core]}
          </Text>
        </View>
        
        {/* Chat Box */}
        {renderAskLensButton()}
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
  
  // Get wing stance display string
  const getWingStanceLabel = (): string => {
    if (isBalancedWings) return 'Balanced wings';
    if (typeof wing === 'number') return `${core}w${wing}`;
    return `Type ${core}`;
  };

  // Get wing flavor key for lookup
  const getWingFlavorKey = (): string => {
    if (typeof wing === 'number') return `${core}w${wing}`;
    return '';
  };

  // Get confidence label from top candidate
  const getConfidenceLabel = (): { text: string; tier: 'high' | 'medium' | 'low' } => {
    const topProb = result?.top_candidates?.[0]?.probability || 0;
    if (topProb >= 0.7) return { text: 'High confidence', tier: 'high' };
    if (topProb >= 0.5) return { text: 'Moderate confidence', tier: 'medium' };
    return { text: 'Exploratory', tier: 'low' };
  };

  // ARCHITECTURE LOCK: Lenses explain the Keystone, they don't display it.
  // This renders ONLY the lens-specific explanation (WHY THIS KEEPS REPEATING)
  // The full Keystone card lives on Home. KeystoneReferenceLink handles navigation.
  const renderKeystoneExplanation = () => {
    console.log('[EnneagramLensView] renderKeystoneExplanation - deepDiveData:', !!deepDiveData, 'keystone_explanation:', !!deepDiveData?.keystone_explanation);
    if (!deepDiveData?.keystone_explanation) return null;
    
    const { 
      lens_explanation_title, 
      lens_explanation_body 
    } = deepDiveData.keystone_explanation;

    return (
      <View style={[styles.keystoneExplanationCard, { backgroundColor: theme.surface, borderColor: theme.accent }]}>
        {/* Enneagram Repetition Explanation ONLY - No Keystone anchor/sequence */}
        <View style={styles.keystoneExplanation}>
          <Text style={[styles.keystoneRoleLabel, { color: theme.accent }]}>
            WHY THIS KEEPS REPEATING
          </Text>
          <Text style={[styles.keystoneExplanationTitle, { color: theme.text }]}>
            {lens_explanation_title}
          </Text>
          <Text style={[styles.keystoneExplanationBody, { color: theme.textSecondary }]}>
            {lens_explanation_body}
          </Text>
        </View>
      </View>
    );
  };

  const renderDeepDiveTab = () => {
    // Show loading state
    if (deepDiveLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.textSecondary} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>Loading your Deep Dive...</Text>
        </View>
      );
    }

    // Use API data if available, fallback to local data
    const data = deepDiveData;
    const confidence = data?.confidence_tier || result?.confidence_tier || 'low';
    const typeLabel = data?.type_label || (wing !== 'balanced' ? `${core}w${wing}` : `Type ${core}`);
    const typeName = data?.type_name || TYPE_NAMES[core];
    
    const toggleSection = (sectionId: string) => {
      setExpandedSections(prev => {
        const newSet = new Set(prev);
        if (newSet.has(sectionId)) {
          newSet.delete(sectionId);
        } else {
          newSet.add(sectionId);
        }
        return newSet;
      });
    };

    // Accordion Section Component
    const AccordionSection = ({ 
      id, 
      title, 
      subtitle, 
      children 
    }: { 
      id: string; 
      title: string; 
      subtitle: string; 
      children: React.ReactNode;
    }) => {
      const isExpanded = expandedSections.has(id);
      return (
        <View style={[styles.accordionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <TouchableOpacity 
            style={styles.accordionHeader} 
            onPress={() => toggleSection(id)}
            activeOpacity={0.7}
          >
            <View style={styles.accordionHeaderText}>
              <Text style={[styles.accordionTitle, { color: theme.text }]}>{title}</Text>
              <Text style={[styles.accordionSubtitle, { color: theme.textTertiary }]}>{subtitle}</Text>
            </View>
            <Text style={[styles.accordionChevron, { color: theme.textSecondary }]}>
              {isExpanded ? '▼' : '▶'}
            </Text>
          </TouchableOpacity>
          {isExpanded && (
            <View style={styles.accordionContent}>
              {children}
            </View>
          )}
        </View>
      );
    };

    // Section Divider Component
    const SectionDivider = ({ title }: { title: string }) => (
      <View style={styles.sectionDivider}>
        <Text style={[styles.sectionDividerText, { color: theme.textTertiary }]}>{title}</Text>
      </View>
    );

    // Check if self-declared
    const isSelfDeclared = result?.source === 'self_declared' || result?.method === 'self_declared';

    return (
      <>
        {/* ═══════════════════════════════════════════════════════════════
            SECTION 1 — IDENTITY BLOCK
            Identity card + Core Story (expanded by default)
        ═══════════════════════════════════════════════════════════════ */}
        
        {/* Identity Card */}
        <View style={[styles.deepDiveHeader, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.deepDiveHeaderTop}>
            <View style={styles.identityTitleRow}>
              <Text style={[styles.deepDiveType, { color: theme.text }]}>{typeLabel}</Text>
            </View>
            {isSelfDeclared ? (
              <View style={[styles.sourceBadge, { backgroundColor: theme.surfaceLight }]}>
                <Text style={[styles.sourceBadgeText, { color: theme.textSecondary }]}>Self-declared</Text>
              </View>
            ) : (
              <View style={[
                styles.confidenceBadge,
                confidence === 'high' && styles.confidenceHigh,
                confidence === 'medium' && styles.confidenceMedium,
                confidence === 'low' && styles.confidenceLow,
              ]}>
                <Text style={[styles.confidenceBadgeText, { color: theme.background }]}>
                  {confidence === 'high' ? 'High Confidence' : confidence === 'medium' ? 'Moderate Confidence' : 'Exploratory'}
                </Text>
              </View>
            )}
          </View>
          <Text style={[styles.deepDiveWingStance, { color: theme.textSecondary }]}>{typeName}</Text>
          <Text style={[styles.deepDiveNote, { color: theme.textTertiary }]}>This lens reflects strategy, not identity.</Text>
        </View>

        {/* Core Story - expanded by default */}
        <AccordionSection
          id="core_story"
          title="Core Story"
          subtitle="Your primary pattern and motivation"
        >
          {data?.sections && data.sections.map((section, index) => (
            <View key={index} style={styles.accordionBodySection}>
              {section?.label && section.label !== 'Core Story' && (
                <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>{section.label}</Text>
              )}
              <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{section?.body || ''}</Text>
            </View>
          ))}
        </AccordionSection>

        {/* ═══════════════════════════════════════════════════════════════
            SECTION 2 — STRUCTURE BLOCK
            Understanding your type structure
        ═══════════════════════════════════════════════════════════════ */}

        {/* Your Core Strategy */}
        <AccordionSection
          id="core_strategy"
          title="Your Core Strategy"
          subtitle="How you naturally approach the world"
        >
          <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
            Type {core} moves through the world by {core === 7 
              ? 'seeking variety, possibilities, and new experiences. Your mind naturally scans for what could be interesting, stimulating, or enjoyable next.'
              : core === 1 ? 'striving to improve and perfect. Your attention naturally goes to what could be better, more correct, or more aligned with ideals.'
              : core === 2 ? 'connecting with others and meeting their needs. Your attention naturally goes to what others want or require.'
              : core === 3 ? 'achieving goals and earning recognition. Your attention naturally goes to what will create success and admiration.'
              : core === 4 ? 'expressing individuality and seeking depth. Your attention naturally goes to what feels authentic and meaningful.'
              : core === 5 ? 'observing and understanding. Your attention naturally goes to gathering knowledge and maintaining boundaries.'
              : core === 6 ? 'anticipating problems and seeking security. Your attention naturally goes to potential risks and what could go wrong.'
              : core === 8 ? 'taking charge and protecting territory. Your attention naturally goes to power dynamics and who is in control.'
              : 'finding peace and avoiding conflict. Your attention naturally goes to maintaining harmony and inner calm.'}
          </Text>
          {(data?.computed_details || computedDetails) && (
            <View style={styles.structureGridCompact}>
              <View style={styles.structureGridRow}>
                <View style={styles.structureGridItem}>
                  <Text style={[styles.structureGridLabel, { color: theme.textTertiary }]}>Center</Text>
                  <Text style={[styles.structureGridValue, { color: theme.text }]}>{formatGroupLabel((data?.computed_details || computedDetails)?.center)}</Text>
                </View>
                <View style={styles.structureGridItem}>
                  <Text style={[styles.structureGridLabel, { color: theme.textTertiary }]}>Social Style</Text>
                  <Text style={[styles.structureGridValue, { color: theme.text }]}>{formatGroupLabel((data?.computed_details || computedDetails)?.hornevian_group)}</Text>
                </View>
              </View>
            </View>
          )}
        </AccordionSection>

        {/* Your Wing */}
        <AccordionSection
          id="your_wing"
          title={wing !== 'balanced' ? `Your Wing (${wing})` : `Your Wing Access`}
          subtitle="How your dominant wing colors your expression"
        >
          {wing !== 'balanced' ? (
            <>
              <View style={styles.wingCard}>
                <View style={styles.wingCardHeader}>
                  <Text style={[styles.wingCardTitle, { color: theme.text }]}>Wing {wing} · {TYPE_NAMES[wing as number]}</Text>
                </View>
              </View>
              
              {/* Core Pattern */}
              <View style={styles.accordionBodySection}>
                <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>Core Pattern</Text>
                <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
                  {WING_FLAVORS[`${core}w${wing}`]?.pattern || `Your ${wing}-wing adds the qualities of ${TYPE_NAMES[wing as number]} to your core pattern.`}
                </Text>
              </View>
              
              {/* The Tradeoff */}
              <View style={styles.accordionBodySection}>
                <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>The Tradeoff</Text>
                <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
                  {WING_FLAVORS[`${core}w${wing}`]?.tradeoff || ''}
                </Text>
              </View>
              
              {/* Potential Strength */}
              <View style={styles.accordionBodySection}>
                <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>Potential Strength</Text>
                <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
                  {WING_FLAVORS[`${core}w${wing}`]?.strength || ''}
                </Text>
              </View>
              
              {/* Experiment */}
              <View style={styles.experimentCard}>
                <View style={styles.experimentHeader}>
                  <Text style={[styles.experimentLabel, { color: theme.accent }]}>Try This</Text>
                </View>
                <Text style={[styles.experimentText, { color: theme.textSecondary }]}>
                  {WING_FLAVORS[`${core}w${wing}`]?.experiment || ''}
                </Text>
              </View>
            </>
          ) : (
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
              You show access to both wings. This flexibility lets you choose consciously based on context rather than defaulting to one pattern.
            </Text>
          )}
        </AccordionSection>

        {/* The Other Wing */}
        <AccordionSection
          id="other_wing"
          title={`Other Wing (${otherWing})`}
          subtitle="Untapped capacity for balance"
        >
          <View style={styles.wingCard}>
            <View style={styles.wingCardHeader}>
              <Text style={[styles.wingCardTitle, { color: theme.text }]}>Wing {otherWing} · {TYPE_NAMES[otherWing]}</Text>
            </View>
          </View>
          
          {/* Core Pattern */}
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>Core Pattern</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
              {WING_FLAVORS[`${core}w${otherWing}`]?.pattern || `The ${otherWing}-wing offers access to ${TYPE_NAMES[otherWing]} qualities.`}
            </Text>
          </View>
          
          {/* Strength */}
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>Potential Strength</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
              {WING_FLAVORS[`${core}w${otherWing}`]?.strength || ''}
            </Text>
          </View>
          
          {/* Experiment */}
          <View style={styles.experimentCard}>
            <View style={styles.experimentHeader}>
              <Text style={[styles.experimentLabel, { color: theme.accent }]}>Try This</Text>
            </View>
            <Text style={[styles.experimentText, { color: theme.textSecondary }]}>
              {WING_FLAVORS[`${core}w${otherWing}`]?.experiment || ''}
            </Text>
          </View>
        </AccordionSection>

        {/* ═══════════════════════════════════════════════════════════════
            SECTION 3 — PATTERN BLOCK
            Deeper patterns and tendencies to notice
        ═══════════════════════════════════════════════════════════════ */}
        
        <SectionDivider title="Patterns to Notice" />

        {/* Deeper Patterns */}
        <AccordionSection
          id="deeper_patterns"
          title="Deeper Patterns"
          subtitle="Tradeoffs and tendencies to notice"
        >
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>The Core Tradeoff</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
              {core === 1 ? 'Integrity vs. flexibility. The drive toward correctness can crowd out acceptance of what is.' :
               core === 2 ? 'Giving vs. receiving. The focus on others\' needs can obscure your own.' :
               core === 3 ? 'Achievement vs. authenticity. The drive to succeed can disconnect you from what you actually feel.' :
               core === 4 ? 'Depth vs. presence. The search for meaning can obscure the ordinary beauty already here.' :
               core === 5 ? 'Understanding vs. participating. The pull toward observation can become avoidance of engagement.' :
               core === 6 ? 'Preparation vs. trust. Vigilance against threat can become the threat itself.' :
               core === 7 ? 'Possibility vs. depth. The draw toward options can prevent the satisfaction of completion.' :
               core === 8 ? 'Strength vs. vulnerability. The protection of power can block the intimacy you actually want.' :
               'Harmony vs. assertion. The maintenance of peace can mean the loss of yourself.'}
            </Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>Daily Reflection</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{JOURNAL_PROMPTS[core]}</Text>
          </View>
        </AccordionSection>

        {/* Energetic Flow */}
        <AccordionSection
          id="energetic_flow"
          title="Energetic Flow"
          subtitle="Movement under stress and when resourced"
        >
          <View style={styles.flowRow}>
            <View style={styles.flowItem}>
              <View style={styles.flowIconContainer}>
                <Text style={[styles.flowIconText, { color: '#C62828' }]}>↓</Text>
              </View>
              <Text style={[styles.flowLabel, { color: theme.textSecondary }]}>Under Stress → Type {(data?.computed_details || computedDetails)?.stress_line_to || '—'}</Text>
            </View>
            <View style={styles.flowItem}>
              <View style={styles.flowIconContainer}>
                <Text style={[styles.flowIconText, { color: '#2E7D32' }]}>↑</Text>
              </View>
              <Text style={[styles.flowLabel, { color: theme.textSecondary }]}>When Resourced → Type {(data?.computed_details || computedDetails)?.growth_line_to || '—'}</Text>
            </View>
          </View>
          
          {/* Stress Section */}
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>Under Stress</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{STRESS_PATTERNS[core]?.pattern}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>The Tradeoff</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{STRESS_PATTERNS[core]?.tradeoff}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>Potential Strength</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{STRESS_PATTERNS[core]?.strength}</Text>
          </View>
          <View style={styles.experimentCard}>
            <View style={styles.experimentHeader}>
              <Text style={[styles.experimentLabel, { color: theme.accent }]}>Try This</Text>
            </View>
            <Text style={[styles.experimentText, { color: theme.textSecondary }]}>{STRESS_PATTERNS[core]?.experiment}</Text>
          </View>
          
          {/* Growth Section */}
          <View style={[styles.accordionBodySection, { marginTop: 24 }]}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>When Resourced</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{GROWTH_PATTERNS[core]?.pattern}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>The Tradeoff</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{GROWTH_PATTERNS[core]?.tradeoff}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>Potential Strength</Text>
            <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{GROWTH_PATTERNS[core]?.strength}</Text>
          </View>
          <View style={styles.experimentCard}>
            <View style={styles.experimentHeader}>
              <Text style={[styles.experimentLabel, { color: theme.accent }]}>Try This</Text>
            </View>
            <Text style={[styles.experimentText, { color: theme.textSecondary }]}>{GROWTH_PATTERNS[core]?.experiment}</Text>
          </View>
        </AccordionSection>

        {/* Top Alternatives */}
        <AccordionSection
          id="top_alternatives"
          title="Top Alternatives"
          subtitle="Other patterns worth exploring"
        >
          <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>
            Your responses showed resonance with these types. Worth exploring if your primary type doesn't fully land.
          </Text>
          {(result?.top_candidates || []).slice(0, 3).map((candidate, index) => (
            <View key={candidate.type} style={[styles.alternativeRow, { borderBottomColor: theme.border }]}>
              <Text style={[styles.alternativeRank, { color: theme.textSecondary }]}>{index + 1}</Text>
              <View style={styles.alternativeInfo}>
                <Text style={[styles.alternativeType, { color: theme.text }]}>Type {candidate.type}</Text>
                <Text style={[styles.alternativeName, { color: theme.textTertiary }]}>{TYPE_NAMES[candidate.type]}</Text>
              </View>
              <Text style={[styles.alternativePercent, { color: theme.text }]}>
                {Math.round(candidate.probability * 100)}%
              </Text>
            </View>
          ))}
        </AccordionSection>

        {/* ═══════════════════════════════════════════════════════════════
            WHY THIS KEEPS REPEATING — Moved to bottom of Deep Dive
            Role: REPETITION_LOOP (after user sees structure, pattern, behavior)
        ═══════════════════════════════════════════════════════════════ */}
        {renderKeystoneExplanation()}

        {/* ═══════════════════════════════════════════════════════════════
            FOOTER
        ═══════════════════════════════════════════════════════════════ */}

        {/* Disclaimer */}
        <View style={[styles.disclaimerCard, { backgroundColor: theme.surfaceAlt || theme.surface }]}>
          <Text style={[styles.disclaimerText, { color: theme.textTertiary }]}>
            This isn't a rule—just a Type {core} pattern you might notice; you're free to take what resonates, 
            leave the rest, and only engage it if it feels useful.
          </Text>
        </View>
        
        {/* Chat Box */}
        {renderAskLensButton()}
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
        <View style={[styles.modalContent, { backgroundColor: theme.surface }]}>
          <Text style={[styles.modalTitle, { color: theme.text }]}>Retake Assessment?</Text>
          <Text style={[styles.modalText, { color: theme.textSecondary }]}>
            This will replace your current results. The assessment takes about 10-12 minutes.
          </Text>
          <View style={styles.modalActions}>
            <TouchableOpacity
              style={[styles.modalCancelButton, { backgroundColor: theme.surfaceAlt || theme.border }]}
              onPress={() => setShowRetakeModal(false)}
            >
              <Text style={[styles.modalCancelText, { color: theme.text }]}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.modalConfirmButton, { backgroundColor: theme.accent }]}
              onPress={handleRetakeConfirm}
            >
              <Text style={[styles.modalConfirmText, { color: theme.textInverse || '#FFFFFF' }]}>Retake</Text>
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
        <View style={[styles.qaModalContent, { backgroundColor: theme.surface }]}>
          {/* Header */}
          <View style={styles.qaModalHeader}>
            <Text style={[styles.qaModalTitle, { color: theme.text }]}>Ask About Enneagram</Text>
            <TouchableOpacity onPress={() => setShowQAModal(false)}>
              <Text style={[styles.closeButtonText, { color: theme.textSecondary }]}>✕</Text>
            </TouchableOpacity>
          </View>
          
          {/* Answer Area */}
          {qaAnswer && (
            <View style={styles.qaAnswerContainer}>
              <ScrollView style={styles.qaAnswerScroll} showsVerticalScrollIndicator={false}>
                <Text style={[styles.qaAnswerText, { color: theme.text }]}>{qaAnswer}</Text>
              </ScrollView>
            </View>
          )}
          
          {qaLoading && (
            <View style={styles.qaLoadingContainer}>
              <ActivityIndicator size="small" color={theme.textSecondary} />
              <Text style={[styles.qaLoadingText, { color: theme.textSecondary }]}>Searching book knowledge...</Text>
            </View>
          )}
          
          {/* Input Area */}
          <View style={[styles.qaInputContainer, { backgroundColor: theme.surfaceAlt || theme.background, borderColor: theme.border }]}>
            <TextInput
              style={[styles.qaInput, { color: theme.text }]}
              value={qaQuestion}
              onChangeText={setQaQuestion}
              placeholder="Ask about your type, patterns, or the Enneagram..."
              placeholderTextColor={theme.textTertiary}
              multiline
              maxLength={500}
              editable={!qaLoading}
            />
            <TouchableOpacity 
              style={[
                styles.qaSendButton,
                { backgroundColor: theme.accent },
                (!qaQuestion.trim() || qaLoading) && styles.qaSendButtonDisabled
              ]}
              onPress={() => handleAskQuestion()}
              disabled={!qaQuestion.trim() || qaLoading}
            >
              <Text style={[
                styles.sendButtonText,
                { color: (!qaQuestion.trim() || qaLoading) ? theme.textTertiary : theme.textInverse || '#FFFFFF' }
              ]}>
                ➤
              </Text>
            </TouchableOpacity>
          </View>
          
          <Text style={[styles.qaDisclaimer, { color: theme.textTertiary }]}>
            Answers are drawn from Enneagram literature. Use as reflection, not prescription.
          </Text>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );

  // ============================================
  // MAIN RENDER
  // ============================================

  const isSelfDeclared = result?.source === 'self_declared' || result?.method === 'self_declared';

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {renderTabs()}
      
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* ARCHITECTURE LOCK: Keystone Reference Link at top of all tabs */}
        {/* Navigates to Home where the full Keystone card lives */}
        <KeystoneReferenceLink patternLabel={deepDiveData?.keystone_explanation?.keystone_label} />
        
        {activeTab === 'summary' && renderSummaryTab()}
        {activeTab === 'at_a_glance' && renderAtAGlanceTab()}
        {activeTab === 'today' && renderTodayTab()}
        {activeTab === 'deep_dive' && renderDeepDiveTab()}
        
        {/* Shared Footer - visible on all tabs */}
        <View style={[styles.sharedFooter, { borderTopColor: theme.border }]}>
          <View style={[styles.footerDivider, { backgroundColor: theme.border }]} />
          <View style={styles.footerActions}>
            <TouchableOpacity
              style={styles.footerAction}
              onPress={() => setShowRetakeModal(true)}
            >
              <Text style={[styles.footerActionText, { color: theme.textSecondary }]}>Retake Assessment</Text>
            </TouchableOpacity>
            
            <View style={[styles.footerDot, { backgroundColor: theme.border }]} />
            
            <TouchableOpacity
              style={styles.footerAction}
              onPress={handleEditType}
            >
              <Text style={[styles.footerActionText, { color: theme.textSecondary }]}>Edit Type</Text>
            </TouchableOpacity>
          </View>
        </View>
        
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
    backgroundColor: "transparent",
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

  // Tabs
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: "transparent",
    borderBottomWidth: 1,
    borderBottomColor: "transparent",
  },
  tab: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: "transparent",
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: "#FFFFFF",
  },
  activeTabText: {
    color: "#FFFFFF",
  },

  // Deep Dive Sub-Tabs
  deepDiveSubTabContainer: {
    flexDirection: 'row',
    backgroundColor: "transparent",
    borderRadius: 8,
    padding: 4,
    marginBottom: 16,
  },
  deepDiveSubTab: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 4,
    alignItems: 'center',
    borderRadius: 6,
  },
  deepDiveSubTabActive: {
    backgroundColor: "transparent",
  },
  deepDiveSubTabText: {
    fontSize: 12,
    fontWeight: '500',
    color: "#FFFFFF",
  },
  deepDiveSubTabTextActive: {
    color: "#FFFFFF",
  },

  // Verification Badge
  verificationBadge: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 12,
    marginBottom: 12,
  },
  verificationBadgeText: {
    fontSize: 12,
    fontWeight: '500',
  },

  // Accordion Styles
  accordionCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    marginBottom: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    overflow: 'hidden',
  },
  accordionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 14,
  },
  accordionHeaderText: {
    flex: 1,
    marginRight: 10,
  },
  accordionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 1,
  },
  accordionSubtitle: {
    fontSize: 12,
    color: "#FFFFFF",
    lineHeight: 16,
  },
  accordionChevron: {
    fontSize: 14,
    color: "#FFFFFF",
  },
  accordionContent: {
    paddingHorizontal: 14,
    paddingBottom: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "transparent",
    paddingTop: 14,
  },
  accordionBodySection: {
    marginBottom: 14,
  },
  accordionBodySectionLast: {
    marginBottom: 0,
  },
  accordionBodyTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 4,
    letterSpacing: 0.1,
  },
  accordionBodyText: {
    fontSize: 14,
    lineHeight: 21,
    color: "#FFFFFF",
  },

  // Wing Card (inside accordion)
  wingCard: {
    backgroundColor: "transparent",
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
  },
  wingCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginBottom: 2,
  },
  wingCardTitle: {
    fontSize: 13,
    fontWeight: '500',
    color: "#FFFFFF",
  },
  wingCardName: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
  },

  // Structure Grid Compact
  structureGridCompact: {
    backgroundColor: "transparent",
    borderRadius: 8,
    padding: 10,
    marginTop: 12,
  },
  structureGridRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  structureGridItem: {
    alignItems: 'center',
  },
  structureGridLabel: {
    fontSize: 11,
    color: "#FFFFFF",
    marginBottom: 2,
  },
  structureGridValue: {
    fontSize: 13,
    fontWeight: '500',
    color: "#FFFFFF",
  },

  // Flow Row (stress/growth)
  flowRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: "transparent",
    borderRadius: 8,
    padding: 10,
    marginBottom: 12,
  },
  flowItem: {
    alignItems: 'center',
  },
  flowIconContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "transparent",
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  flowLabel: {
    fontSize: 12,
    color: "#FFFFFF",
  },

  // Alternative Rows
  alternativeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "transparent",
  },
  alternativeRank: {
    width: 22,
    fontSize: 13,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  alternativeInfo: {
    flex: 1,
  },
  alternativeType: {
    fontSize: 13,
    fontWeight: '500',
    color: "#FFFFFF",
  },
  alternativeName: {
    fontSize: 11,
    color: "#FFFFFF",
  },
  alternativePercent: {
    fontSize: 13,
    fontWeight: '500',
    color: "#FFFFFF",
  },

  // Disclaimer Card
  disclaimerCard: {
    backgroundColor: "transparent",
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  disclaimerText: {
    fontSize: 12,
    lineHeight: 18,
    color: "#FFFFFF",
    fontStyle: 'italic',
    textAlign: 'center',
  },

  // Hero Card
  heroCard: {
    backgroundColor: "transparent",
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: "transparent",
    marginBottom: 16,
  },
  heroBadge: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "transparent",
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  heroBadgeText: {
    fontSize: 28,
    fontWeight: '700',
    color: "#FFFFFF",
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 4,
  },
  heroSubtitle: {
    fontSize: 16,
    color: "#FFFFFF",
    marginBottom: 12,
  },
  heroDisclaimer: {
    fontSize: 12,
    color: "#FFFFFF",
    marginTop: 8,
    fontStyle: 'italic',
  },

  // ============================================
  // OVERVIEW TAB STYLES (Redesigned)
  // ============================================

  // Identity Card (new compact design)
  identityCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    marginBottom: 10,
  },
  identityMain: {
    alignItems: 'center',
    marginBottom: 8,
  },
  identityType: {
    fontSize: 22,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 2,
  },
  identityName: {
    fontSize: 14,
    color: "#FFFFFF",
  },
  identityNote: {
    fontSize: 11,
    color: "#FFFFFF",
    marginTop: 6,
    fontStyle: 'italic',
  },

  // Overview Cards
  overviewCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    marginBottom: 10,
  },
  overviewCardTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 8,
  },
  overviewCardBody: {
    fontSize: 14,
    lineHeight: 21,
    color: "#FFFFFF",
  },

  // Manifestation List (Where This Shows Up)
  manifestationList: {
    gap: 10,
  },
  manifestationItem: {
    paddingBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "transparent",
  },
  manifestationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 3,
  },
  manifestationText: {
    fontSize: 13,
    lineHeight: 19,
    color: "#FFFFFF",
  },

  // Reflection Card
  reflectionCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 2,
    borderLeftColor: "transparent",
  },
  reflectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: "#FFFFFF",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 22,
    color: "#FFFFFF",
    fontStyle: 'italic',
  },

  // Subtle Link (Explore Deep Dive)
  subtleLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 12,
  },
  subtleLinkText: {
    fontSize: 13,
    color: "#FFFFFF",
  },

  // Cards
  card: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "transparent",
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
    color: "#FFFFFF",
    marginBottom: 8,
  },
  cardSubtitle: {
    fontSize: 13,
    color: "#FFFFFF",
    marginBottom: 12,
  },
  cardBody: {
    fontSize: 15,
    lineHeight: 22,
    color: "#FFFFFF",
  },
  cardNote: {
    fontSize: 13,
    lineHeight: 19,
    color: "#FFFFFF",
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
    borderTopColor: "transparent",
  },
  wingItem: {
    flex: 1,
    alignItems: 'center',
  },
  wingDivider: {
    width: 1,
    height: 32,
    backgroundColor: "transparent",
  },
  wingLabel: {
    fontSize: 12,
    color: "#FFFFFF",
    marginBottom: 4,
  },
  wingValue: {
    fontSize: 16,
    fontWeight: '600',
    color: "#FFFFFF",
  },

  // Candidates
  candidateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "transparent",
  },
  candidateRank: {
    width: 24,
    fontSize: 14,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  candidateType: {
    flex: 1,
    fontSize: 14,
    color: "#FFFFFF",
  },
  candidatePercent: {
    fontSize: 14,
    fontWeight: '600',
    color: "#FFFFFF",
  },

  // CTA Row
  ctaRow: {
    gap: 12,
    marginTop: 8,
  },
  ctaButtonPrimary: {
    backgroundColor: "transparent",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  ctaButtonPrimaryText: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  ctaButtonSecondary: {
    backgroundColor: "transparent",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: "transparent",
  },
  ctaButtonSecondaryText: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
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
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: "transparent",
  },
  energyButtonSelected: {
    backgroundColor: "transparent",
    borderColor: "transparent",
  },
  energyButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: "#FFFFFF",
  },
  energyButtonTextSelected: {
    color: "#FFFFFF",
  },

  // Practice Card
  practiceCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 20,
    marginBottom: 12,
  },
  practiceLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: "#FFFFFF",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  practiceBody: {
    fontSize: 15,
    lineHeight: 22,
    color: "#FFFFFF",
  },

  // Prompt Card
  promptCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: "transparent",
    borderLeftWidth: 3,
    borderLeftColor: "transparent",
  },
  promptLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: "#FFFFFF",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  promptBody: {
    fontSize: 16,
    lineHeight: 24,
    color: "#FFFFFF",
    fontStyle: 'italic',
  },

  // Pattern Rows (Deep Dive)
  patternRow: {
    marginBottom: 14,
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: "transparent",
  },
  patternLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  patternValue: {
    fontSize: 14,
    lineHeight: 20,
    color: "#FFFFFF",
  },

  // Wing Flight Row
  wingFlightRow: {
    flexDirection: 'row',
    marginTop: 16,
    gap: 12,
  },
  wingFlightItem: {
    flex: 1,
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: "transparent",
  },
  wingFlightLabel: {
    fontSize: 12,
    color: "#FFFFFF",
    marginBottom: 4,
  },
  wingFlightValue: {
    fontSize: 20,
    fontWeight: '700',
    color: "#FFFFFF",
  },

  // Mastery Toggle
  masteryToggle: {
    flexDirection: 'row',
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "transparent",
  },
  masteryButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  masteryButtonSelected: {
    backgroundColor: "transparent",
  },
  masteryButtonText: {
    fontSize: 13,
    fontWeight: '500',
    color: "#FFFFFF",
  },
  masteryButtonTextSelected: {
    color: "#FFFFFF",
  },
  masteryDescription: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    borderColor: "transparent",
  },
  masteryDescriptionText: {
    fontSize: 14,
    lineHeight: 20,
    color: "#FFFFFF",
    textAlign: 'center',
  },
  
  // Experiment Card (Try This)
  experimentCard: {
    backgroundColor: 'rgba(255, 215, 0, 0.05)',
    borderRadius: 12,
    padding: 14,
    marginTop: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 215, 0, 0.2)',
  },
  experimentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  experimentLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: "#FFFFFF",
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  experimentText: {
    fontSize: 14,
    lineHeight: 21,
    color: "#FFFFFF",
    fontStyle: 'italic',
  },

  // Verification
  verificationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "transparent",
  },
  verificationType: {
    fontSize: 14,
    color: "#FFFFFF",
  },
  verificationPercent: {
    fontSize: 14,
    fontWeight: '600',
    color: "#FFFFFF",
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
    color: "#FFFFFF",
  },
  editTypeLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 4,
    paddingVertical: 8,
  },
  
  // Source badge (for self-declared)
  sourceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: "transparent",
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  sourceBadgeText: {
    fontSize: 12,
    fontWeight: '500',
    color: "#FFFFFF",
  },
  
  // Identity card edit button
  identityTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  editTypeInline: {
    padding: 6,
    borderRadius: 12,
    backgroundColor: "transparent",
  },
  
  // Pattern Movement Card
  patternMovementCard: {
    backgroundColor: "transparent",
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "transparent",
  },
  patternMovementHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  patternMovementTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: "#FFFFFF",
    flex: 1,
  },
  patternMovementTitleMuted: {
    color: "#FFFFFF",
  },
  patternMovementContent: {
    gap: 10,
  },
  
  // Visual Movement Indicator
  movementIndicatorContainer: {
    alignItems: 'center',
    marginBottom: 16,
    paddingVertical: 8,
  },
  movementIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  typeCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "transparent",
    borderWidth: 2,
    borderColor: "transparent",
    alignItems: 'center',
    justifyContent: 'center',
  },
  typeCircleMuted: {
    borderColor: "transparent",
    backgroundColor: "transparent",
  },
  typeCircleDrift: {
    borderStyle: 'dashed',
  },
  typeCircleStress: {
    borderColor: '#C62828',
    backgroundColor: '#FFEBEE',
  },
  typeCircleGrowth: {
    borderColor: '#2E7D32',
    backgroundColor: '#E8F5E9',
  },
  typeCircleNumber: {
    fontSize: 18,
    fontWeight: '700',
    color: "#FFFFFF",
  },
  typeCircleNumberMuted: {
    color: "#FFFFFF",
  },
  typeCircleNumberStress: {
    color: '#C62828',
  },
  typeCircleNumberGrowth: {
    color: '#2E7D32',
  },
  movementArrowLine: {
    width: 24,
    height: 2,
    backgroundColor: "transparent",
    marginLeft: -2,
  },
  movementArrowStress: {
    backgroundColor: '#C62828',
  },
  movementArrowGrowth: {
    backgroundColor: '#2E7D32',
  },
  movementArrowIcon: {
    marginRight: -2,
  },
  movementDirectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: "#FFFFFF",
    textTransform: 'lowercase',
    letterSpacing: 0.5,
    marginTop: 10,
  },
  movementDirectionStress: {
    color: '#C62828',
  },
  movementDirectionGrowth: {
    color: '#2E7D32',
  },
  movementBaselineLabel: {
    fontSize: 12,
    color: "#FFFFFF",
    marginTop: 8,
  },
  
  // Drift content styles (keywords secondary, summary tertiary)
  driftRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  driftLabel: {
    fontSize: 12,
    color: "#FFFFFF",
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  driftValue: {
    fontSize: 14,
    color: "#FFFFFF",
  },
  driftSignalValue: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  driftStress: {
    color: '#E57373',
  },
  driftGrowth: {
    color: '#81C784',
  },
  driftKeywords: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    justifyContent: 'center',
  },
  driftKeywordBadge: {
    backgroundColor: "transparent",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  driftKeywordText: {
    fontSize: 11,
    color: "#FFFFFF",
  },
  driftSummary: {
    fontSize: 13,
    lineHeight: 19,
    color: "#FFFFFF",
    fontStyle: 'italic',
    marginTop: 8,
    textAlign: 'center',
  },
  driftSummaryNeutral: {
    fontSize: 13,
    lineHeight: 19,
    color: "#FFFFFF",
    marginTop: 4,
    textAlign: 'center',
  },
  driftDisclaimer: {
    fontSize: 11,
    color: "#FFFFFF",
    marginTop: 12,
    textAlign: 'center',
    opacity: 0.7,
  },
  driftConfidenceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    backgroundColor: "transparent",
  },
  driftConfidenceModerate: {
    backgroundColor: 'rgba(129, 199, 132, 0.15)',
  },
  driftConfidenceEmerging: {
    backgroundColor: 'rgba(255, 215, 0, 0.15)',
  },
  driftConfidenceText: {
    fontSize: 10,
    fontWeight: '500',
    color: "#FFFFFF",
    textTransform: 'capitalize',
  },
  
  // Shared footer (across all tabs)
  sharedFooter: {
    marginTop: 24,
    paddingTop: 16,
  },
  footerDivider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: "transparent",
    marginBottom: 16,
  },
  footerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  footerAction: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  footerActionText: {
    fontSize: 14,
    color: "#FFFFFF",
  },
  footerDot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: "transparent",
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
    backgroundColor: "transparent",
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 12,
  },
  modalText: {
    fontSize: 15,
    lineHeight: 22,
    color: "#FFFFFF",
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
    backgroundColor: "transparent",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "transparent",
  },
  modalCancelText: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  modalConfirmButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: "transparent",
    borderRadius: 10,
  },
  modalConfirmText: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  
  // Chat Box
  chatContainer: {
    marginTop: 16,
    backgroundColor: "transparent",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "transparent",
    overflow: 'hidden',
  },
  
  // Ask Lens Button Styles
  askLensContainer: {
    marginTop: 24,
    marginBottom: 20,
    alignItems: 'center',
  },
  askLensButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 24,
    backgroundColor: "transparent",
    borderRadius: 12,
    marginBottom: 16,
    width: '100%',
  },
  askLensText: {
    fontSize: 15,
    color: "#FFFFFF",
    fontWeight: '500',
  },
  askLensDisclaimer: {
    fontSize: 12,
    color: "#FFFFFF",
    textAlign: 'center',
    fontStyle: 'italic',
    opacity: 0.7,
  },
  
  chatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
    backgroundColor: "transparent",
  },
  chatHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  chatHeaderText: {
    fontSize: 14,
    fontWeight: '500',
    color: "#FFFFFF",
  },
  chatExpandText: {
    fontSize: 12,
    color: "#FFFFFF",
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
    backgroundColor: "transparent",
  },
  chatMessageAssistant: {
    alignSelf: 'flex-start',
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: "transparent",
  },
  chatMessageText: {
    fontSize: 14,
    lineHeight: 20,
    color: "#FFFFFF",
  },
  chatMessageTextUser: {
    color: "#FFFFFF",
  },
  chatInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
  },
  chatInput: {
    flex: 1,
    backgroundColor: "transparent",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: "transparent",
    fontSize: 14,
    maxHeight: 100,
    color: "#FFFFFF",
  },
  chatSendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "transparent",
    alignItems: 'center',
    justifyContent: 'center',
  },
  chatSendButtonDisabled: {
    backgroundColor: "transparent",
  },
  sendButtonText: {
    fontSize: 18,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  closeButtonText: {
    fontSize: 24,
    fontWeight: '400',
    color: "#FFFFFF",
  },
  flowIconText: {
    fontSize: 16,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  movementArrowText: {
    fontSize: 18,
    fontWeight: '600',
    color: "#FFFFFF",
    marginHorizontal: 4,
  },
  
  // Daily Micro-Lesson Card
  microLessonCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "transparent",
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
    color: "#FFFFFF",
    marginBottom: 2,
  },
  microLessonSubtitle: {
    fontSize: 11,
    fontWeight: '600',
    color: "#FFFFFF",
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  microLessonBody: {
    marginBottom: 14,
  },
  microLessonBodyText: {
    fontSize: 15,
    lineHeight: 23,
    color: "#FFFFFF",
  },
  microLessonBoldText: {
    fontWeight: '600',
    color: "#FFFFFF",
  },
  microLessonFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "transparent",
  },
  microLessonRotates: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  microLessonRotatesText: {
    fontSize: 12,
    color: "#FFFFFF",
  },
  microLessonAskButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: "transparent",
  },
  microLessonAskText: {
    fontSize: 12,
    fontWeight: '500',
    color: "#FFFFFF",
  },

  // Enneagram Structure Card (Deep Dive)
  structureCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  structureTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: "#FFFFFF",
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
    color: "#FFFFFF",
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  structureValue: {
    fontSize: 13,
    fontWeight: '500',
    color: "#FFFFFF",
    textAlign: 'center',
  },
  structureSubValue: {
    fontSize: 11,
    color: "#FFFFFF",
    textAlign: 'center',
    marginTop: 2,
  },
  structureDivider: {
    width: 1,
    height: 32,
    backgroundColor: "transparent",
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
    color: "#FFFFFF",
  },
  traitCardsSourceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    backgroundColor: "transparent",
    borderRadius: 10,
  },
  traitCardsSourceText: {
    fontSize: 10,
    color: "#FFFFFF",
    fontWeight: '500',
  },
  traitCardsLoading: {
    paddingVertical: 24,
    alignItems: 'center',
  },
  traitCard: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  traitCardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 6,
  },
  traitCardBody: {
    fontSize: 14,
    lineHeight: 21,
    color: "#FFFFFF",
  },
  traitCardCitation: {
    fontSize: 11,
    color: "#FFFFFF",
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
    borderTopColor: "transparent",
  },
  traitCardAskText: {
    fontSize: 12,
    fontWeight: '500',
    color: "#FFFFFF",
  },

  // Section Divider (text-based)
  sectionDivider: {
    marginTop: 12,
    marginBottom: 6,
    paddingVertical: 4,
  },
  sectionDividerText: {
    fontSize: 11,
    fontWeight: '600',
    color: "#FFFFFF",
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    textAlign: 'center',
  },

  // Q&A Modal
  qaModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  qaModalContent: {
    backgroundColor: "transparent",
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
    color: "#FFFFFF",
  },
  qaAnswerContainer: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    maxHeight: 220,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  qaAnswerScroll: {
    flex: 1,
  },
  qaAnswerText: {
    fontSize: 15,
    lineHeight: 23,
    color: "#FFFFFF",
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
    color: "#FFFFFF",
  },
  qaInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 10,
  },
  qaInput: {
    flex: 1,
    backgroundColor: "transparent",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: "transparent",
    fontSize: 14,
    maxHeight: 100,
    color: "#FFFFFF",
  },
  qaSendButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: "transparent",
    alignItems: 'center',
    justifyContent: 'center',
  },
  qaSendButtonDisabled: {
    backgroundColor: "transparent",
  },
  qaDisclaimer: {
    fontSize: 11,
    color: "#FFFFFF",
    textAlign: 'center',
    marginTop: 12,
    fontStyle: 'italic',
  },

  // Deep Dive Header (Anchor)
  deepDiveHeader: {
    backgroundColor: "transparent",
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    alignItems: 'center',
  },
  deepDiveHeaderTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginBottom: 2,
  },
  deepDiveType: {
    fontSize: 22,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  deepDiveWingStance: {
    fontSize: 15,
    fontWeight: '500',
    color: "#FFFFFF",
    marginBottom: 4,
  },
  deepDiveNote: {
    fontSize: 11,
    color: "#FFFFFF",
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
    color: "#FFFFFF",
  },
  deepDiveSection: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  deepDiveSectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 10,
  },
  deepDiveSectionBody: {
    fontSize: 15,
    lineHeight: 24,
    color: "#FFFFFF",
  },
  mirrorPromptCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderLeftWidth: 3,
    borderLeftColor: "transparent",
  },
  mirrorPromptHeader: {
    marginBottom: 8,
  },
  mirrorPromptLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: "#FFFFFF",
    letterSpacing: 0.5,
  },
  mirrorPromptText: {
    fontSize: 15,
    lineHeight: 22,
    color: "#FFFFFF",
    fontStyle: 'italic',
  },

  confidenceBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: "transparent",
  },
  confidenceBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  confidenceText: {
    fontSize: 13,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  confidenceHigh: {
    backgroundColor: '#E8F5E9',
  },
  confidenceHighText: {
    color: '#2E7D32',
  },
  confidenceMedium: {
    backgroundColor: '#FFF8E1',
  },
  confidenceMediumText: {
    color: '#E65100',
  },
  confidenceLow: {
    backgroundColor: '#F5F5F5',
  },
  confidenceLowText: {
    color: '#616161',
  },

  // Wing Section
  wingSection: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
  },
  wingSectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 10,
  },
  wingSectionBody: {
    fontSize: 14,
    lineHeight: 21,
    color: "#FFFFFF",
  },
  wingGrowthNoteText: {
    fontSize: 13,
    lineHeight: 20,
    color: "#FFFFFF",
    marginTop: 10,
    fontStyle: 'italic',
  },
  wingAccessHint: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "transparent",
  },
  wingAccessHintText: {
    fontSize: 13,
    color: "#FFFFFF",
    textAlign: 'center',
  },
  wingGrowthHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 12,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: "transparent",
  },
  wingGrowthHintText: {
    fontSize: 12,
    color: "#FFFFFF",
    fontStyle: 'italic',
  },

  // At a Glance Tab Styles
  glanceCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    padding: 16,
  },
  glanceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "rgba(128, 128, 128, 0.2)",
  },
  glanceIconContainer: {
    width: 32,
    alignItems: 'center',
    marginRight: 12,
  },
  glanceContent: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  glanceLabel: {
    fontSize: 14,
    color: "#FFFFFF",
  },
  glanceValue: {
    fontSize: 14,
    fontWeight: '500',
    color: "#FFFFFF",
    textAlign: 'right',
  },
  glanceSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    color: "#FFFFFF",
    marginBottom: 12,
  },
  glanceTagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  glanceTag: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "transparent",
  },
  glanceTagText: {
    fontSize: 13,
    color: "#FFFFFF",
  },
  glanceRefGrid: {
    flexDirection: 'row',
    gap: 16,
  },
  glanceRefItem: {
    flex: 1,
  },
  glanceRefLabel: {
    fontSize: 12,
    color: "#FFFFFF",
    marginBottom: 4,
  },
  glanceRefValue: {
    fontSize: 14,
    color: "#FFFFFF",
    lineHeight: 20,
  },
  glanceFooter: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  glanceFooterText: {
    fontSize: 12,
    color: "#FFFFFF",
  },
  
  // ============================================
  // PATTERN SUMMARY CARD STYLES
  // ============================================
  patternSummaryCard: {
    backgroundColor: "transparent",
    borderRadius: 16,
    marginBottom: 20,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    padding: 20,
  },
  patternSummaryTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: "#FFFFFF",
    marginBottom: 16,
  },
  patternSummaryBody: {
    fontSize: 15,
    lineHeight: 24,
    color: "#FFFFFF",
    marginBottom: 14,
  },
  patternSummaryEmphasized: {
    fontStyle: 'italic',
    marginBottom: 0,
  },
  
  // ============================================
  // COLLAPSIBLE SECTIONS STYLES
  // ============================================
  collapsibleSection: {
    backgroundColor: "transparent",
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: "transparent",
    overflow: 'hidden',
  },
  collapsibleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  collapsibleTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: "#FFFFFF",
  },
  collapsibleChevron: {
    fontSize: 10,
  },
  collapsibleContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  collapsibleItem: {
    marginBottom: 16,
  },
  collapsibleItemLabel: {
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    color: "#FFFFFF",
    marginBottom: 6,
  },
  collapsibleItemText: {
    fontSize: 14,
    lineHeight: 22,
    color: "#FFFFFF",
  },
  collapsibleItemQuote: {
    fontStyle: 'italic',
  },
  
  // ============================================
  // STRUCTURE SECTION STYLES
  // ============================================
  structureSectionHeader: {
    borderTopWidth: 1,
    borderTopColor: "rgba(128, 128, 128, 0.2)",
    paddingTop: 24,
    marginTop: 8,
    marginBottom: 16,
  },
  structureSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.8,
    color: "#FFFFFF",
  },
  
  loadingContainer: {
    padding: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 14,
    marginTop: 8,
    color: "#FFFFFF",
  },
  // Keystone Explanation Card styles
  keystoneExplanationCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    borderWidth: 1,
    borderLeftWidth: 3,
  },
  keystoneAnchor: {
    marginBottom: 16,
  },
  keystoneEyebrow: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  keystoneLabel: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 12,
  },
  keystoneSequence: {
    gap: 6,
  },
  keystoneSequenceLine: {
    fontSize: 15,
    lineHeight: 22,
  },
  keystoneDivider: {
    height: 1,
    marginVertical: 16,
  },
  keystoneExplanation: {
    gap: 8,
  },
  keystoneRoleLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },
  keystoneExplanationTitle: {
    fontSize: 17,
    fontWeight: '600',
    marginTop: 4,
  },
  keystoneExplanationBody: {
    fontSize: 15,
    lineHeight: 23,
    marginTop: 4,
  },

  // ============================================
  // ENNEAGRAM WHEEL STYLES (New Summary Tab)
  // ============================================
  wheelContainer: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 16,
  },
  wheelWrapper: {
    width: 240,
    height: 240,
    alignSelf: 'center',
    position: 'relative',
  },
  wheelNode: {
    position: 'absolute',
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  wheelNumber: {
    fontSize: 18,
    fontWeight: '600',
  },
  wheelLabel: {
    fontSize: 8,
    fontWeight: '600',
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  wheelCenter: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -40 }, { translateY: -25 }],
    width: 80,
    alignItems: 'center',
  },
  wheelCenterType: {
    fontSize: 20,
    fontWeight: '700',
  },
  wheelCenterName: {
    fontSize: 11,
    marginTop: 2,
    textAlign: 'center',
  },
  wheelLegend: {
    marginTop: 20,
    gap: 8,
  },
  wheelLegendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  wheelLegendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  wheelLegendText: {
    fontSize: 12,
  },

  // ============================================
  // STRUCTURE SUMMARY CARD STYLES
  // ============================================
  structureCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  structureHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  structureType: {
    fontSize: 20,
    fontWeight: '700',
    flex: 1,
  },
  confidenceBadge: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 12,
    borderWidth: 1,
  },
  confidenceBadgeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  structureSubtext: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 12,
  },
  structureBridge: {
    fontSize: 15,
    lineHeight: 22,
  },

  // ============================================
  // PATTERN CARD STYLES
  // ============================================
  patternCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  patternTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  patternBody: {
    fontSize: 15,
    lineHeight: 23,
  },

  // ============================================
  // SIGNALS CARD STYLES
  // ============================================
  signalsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  signalRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  signalType: {
    width: 60,
    fontSize: 13,
    fontWeight: '500',
  },
  signalBarContainer: {
    flex: 1,
    height: 12,
    backgroundColor: 'rgba(128,128,128,0.1)',
    borderRadius: 6,
    marginHorizontal: 10,
    overflow: 'hidden',
  },
  signalBar: {
    height: '100%',
    borderRadius: 6,
  },
  signalPercent: {
    width: 40,
    fontSize: 13,
    fontWeight: '500',
    textAlign: 'right',
  },

  // ============================================
  // HERO RESULT CARD STYLES (New Summary Tab)
  // ============================================
  heroResultCard: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 24,
    marginBottom: 20,
    alignItems: 'center',
  },
  heroResultLabel: {
    fontSize: 48,
    fontWeight: '700',
    letterSpacing: -1,
    marginBottom: 4,
  },
  heroResultName: {
    fontSize: 18,
    fontWeight: '500',
    marginBottom: 12,
  },
  heroConfidenceRow: {
    marginBottom: 16,
  },
  heroConfidenceBadge: {
    paddingVertical: 5,
    paddingHorizontal: 14,
    borderRadius: 14,
  },
  heroConfidenceText: {
    fontSize: 12,
    fontWeight: '600',
  },
  heroSummaryText: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
    paddingHorizontal: 8,
    marginBottom: 12,
  },
  heroNote: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
  },

  // ============================================
  // CORE STORY CARD STYLES (New Summary Tab)
  // ============================================
  coreStoryCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 16,
  },
  coreStoryTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  coreStorySection: {
    marginBottom: 16,
  },
  coreStorySectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 6,
  },
  coreStoryBody: {
    fontSize: 15,
    lineHeight: 23,
  },

  // ============================================
  // WING INFLUENCE CARD STYLES (New Summary Tab)
  // ============================================
  wingInfluenceCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 16,
  },
  wingInfluenceTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  wingInfluenceBody: {
    fontSize: 15,
    lineHeight: 23,
  },

  // ============================================
  // SIGNALS CARD STYLES (Updated for New Summary)
  // ============================================
  signalsTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  signalTypeContainer: {
    width: 65,
  },

  // ============================================
  // WHEEL SUPPORT CARD STYLES (New Summary Tab)
  // ============================================
  wheelSupportCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 20,
  },
  wheelSupportTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 16,
    textAlign: 'center',
  },
  wheelNodeCompact: {
    position: 'absolute',
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  wheelNumberCompact: {
    fontSize: 16,
    fontWeight: '600',
  },
  wheelCenterCompact: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: [{ translateX: -25 }, { translateY: -15 }],
    width: 50,
    alignItems: 'center',
  },
  wheelCenterTypeCompact: {
    fontSize: 18,
    fontWeight: '700',
  },
  wheelLegendCompact: {
    marginTop: 16,
    gap: 6,
  },
  wheelLegendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  wheelLegendItemCompact: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  wheelLegendDotCompact: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  wheelLegendTextCompact: {
    fontSize: 12,
  },

  // ============================================
  // MOVEMENT PATTERNS CARD STYLES (Section 4)
  // ============================================
  summaryDataCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 16,
  },
  summaryDataTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  movementRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  movementIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  movementIconText: {
    fontSize: 18,
  },
  movementContent: {
    flex: 1,
  },
  movementLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  movementDesc: {
    fontSize: 13,
    lineHeight: 19,
  },

  // ============================================
  // TOP SIGNALS SUBTITLE STYLE
  // ============================================
  signalsSubtitle: {
    fontSize: 12,
    marginTop: -12,
    marginBottom: 16,
  },
});
