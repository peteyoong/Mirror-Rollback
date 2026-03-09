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
import { 
  sendEnneagramChat, 
  getEnneagramTraits,
  askEnneagramQuestion,
  getEnneagramDeepDive,
  getPatternDrift,
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
  result: EnneagramResult;
  userId: string;
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

export default function EnneagramLensView({ result, userId }: Props) {
  const router = useRouter();
  
  // Theme support - use the useTheme hook
  const { theme, isDark } = useTheme();
  
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [energyState, setEnergyState] = useState<EnergyState | null>(
    (result.state_calibration?.energy_state as EnergyState) || null
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

  // Debug logging on tab change
  useEffect(() => {
    console.log('[EnneagramLensView] activeTab changed to:', activeTab);
  }, [activeTab]);

  // Q&A Modal state (hidden initially per user request)
  const [showQAModal, setShowQAModal] = useState(false);
  const [qaQuestion, setQaQuestion] = useState('');
  const [qaAnswer, setQaAnswer] = useState<string | null>(null);
  const [qaLoading, setQaLoading] = useState(false);

  const core = result.inferred_core;
  const wing = result.inferred_wing;
  const wings = WING_NUMBERS[core];
  const otherWing = wing === wings.left ? wings.right : wings.left;
  
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

  // Load Deep Dive data when tab is selected
  useEffect(() => {
    const loadDeepDive = async () => {
      if (!userId || activeTab !== 'deep_dive' || deepDiveData) return;
      
      setDeepDiveLoading(true);
      try {
        const response = await getEnneagramDeepDive(userId);
        setDeepDiveData(response);
      } catch (error) {
        console.error('Failed to load deep dive:', error);
      } finally {
        setDeepDiveLoading(false);
      }
    };
    loadDeepDive();
  }, [userId, activeTab, deepDiveData]);

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
    const tier = result.confidence_tier;
    const isSelfDeclared = result.source === 'self_declared' || result.method === 'self_declared';
    
    // Self-declared results show "Self-declared" instead of confidence
    if (isSelfDeclared) {
      return (
        <View style={styles.sourceBadge}>
          <Text style={styles.sourceBadgeText}>Self-declared</Text>
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
  
  const renderChatBox = () => (
    <View style={styles.chatContainer}>
      <TouchableOpacity 
        style={styles.chatHeader}
        onPress={() => setChatExpanded(!chatExpanded)}
      >
        <View style={styles.chatHeaderLeft}>
          <Text style={styles.chatHeaderText}>Ask about this</Text>
        </View>
        <Text style={[styles.chatExpandText, { color: theme.textTertiary }]}>
          {chatExpanded ? '▼' : '▲'}
        </Text>
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
                  <ActivityIndicator size="small" color={theme.textSecondary} />
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
              placeholderTextColor={theme.textTertiary}
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
              <Text style={[
                styles.sendButtonText,
                { color: (!chatInput.trim() || chatLoading) ? theme.textTertiary : theme.background }
              ]}>
                ➤
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );

  // ============================================
  // SUMMARY TAB
  // ============================================

  const renderSummaryTab = () => {
    const manifestations = PATTERN_MANIFESTATIONS[core];
    
    return (
      <>
        {/* Identity Card */}
        <View style={[styles.identityCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <View style={styles.identityMain}>
            <View style={styles.identityTitleRow}>
              <Text style={[styles.identityType, { color: theme.text }]}>
                {wing !== 'balanced' ? `${core}w${wing}` : `Type ${core}`}
              </Text>
            </View>
            <Text style={[styles.identityName, { color: theme.textSecondary }]}>{TYPE_NAMES[core]}</Text>
          </View>
          {renderConfidenceBadge()}
          <Text style={[styles.identityNote, { color: theme.textTertiary }]}>
            This lens reflects strategy, not identity.
          </Text>
        </View>

        {/* Core Pattern Card */}
        <View style={[styles.overviewCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <Text style={[styles.overviewCardTitle, { color: theme.textTertiary }]}>Your Core Pattern</Text>
          <Text style={[styles.overviewCardBody, { color: theme.text }]}>
            {CORE_PATTERNS[core]}
          </Text>
        </View>

        {/* What Drives This Card */}
        <View style={[styles.overviewCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <Text style={[styles.overviewCardTitle, { color: theme.textTertiary }]}>What Drives This</Text>
          <Text style={[styles.overviewCardBody, { color: theme.text }]}>
            {PATTERN_DRIVERS[core]}
          </Text>
        </View>

        {/* Where This Shows Up Card */}
        <View style={[styles.overviewCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
          <Text style={[styles.overviewCardTitle, { color: theme.textTertiary }]}>Where This Often Appears</Text>
          <View style={styles.manifestationList}>
            <View style={styles.manifestationItem}>
              <Text style={[styles.manifestationLabel, { color: theme.textTertiary }]}>Decision making</Text>
              <Text style={[styles.manifestationText, { color: theme.textSecondary }]}>{manifestations.decisions}</Text>
            </View>
            <View style={styles.manifestationItem}>
              <Text style={[styles.manifestationLabel, { color: theme.textTertiary }]}>Work & creativity</Text>
              <Text style={[styles.manifestationText, { color: theme.textSecondary }]}>{manifestations.work}</Text>
            </View>
            <View style={styles.manifestationItem}>
              <Text style={[styles.manifestationLabel, { color: theme.textTertiary }]}>Relationships</Text>
              <Text style={[styles.manifestationText, { color: theme.textSecondary }]}>{manifestations.relationships}</Text>
            </View>
            <View style={styles.manifestationItem}>
              <Text style={[styles.manifestationLabel, { color: theme.textTertiary }]}>Under stress</Text>
              <Text style={[styles.manifestationText, { color: theme.textSecondary }]}>{manifestations.stress}</Text>
            </View>
          </View>
        </View>

        {/* Reflection Prompt Card */}
        <View style={[styles.reflectionCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
          <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>A REFLECTION</Text>
          <Text style={[styles.reflectionText, { color: theme.text }]}>
            "{OVERVIEW_REFLECTIONS[core]}"
          </Text>
        </View>

        {/* Subtle CTA */}
        <TouchableOpacity
          style={styles.subtleLink}
          onPress={() => setActiveTab('deep_dive')}
        >
          <Text style={[styles.subtleLinkText, { color: theme.textTertiary }]}>Explore Deep Dive →</Text>
        </TouchableOpacity>

        {/* Chat Box */}
        {renderChatBox()}
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
    
    // Basic fear and desire based on type
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

    return (
      <>
        {/* Loading state */}
        {traitsLoading && !details && (
          <View style={[styles.loadingContainer, { backgroundColor: theme.cardBg }]}>
            <ActivityIndicator size="small" color={theme.textSecondary} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>Loading profile...</Text>
          </View>
        )}

        {/* Profile Grid */}
        {details && (
          <>
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

            {/* Social Style Card */}
            {socialStyleTags.length > 0 && (
              <View style={[styles.glanceCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
                <Text style={[styles.glanceSectionTitle, { color: theme.textTertiary }]}>SOCIAL STYLE</Text>
                <View style={styles.glanceTagsContainer}>
                  {socialStyleTags.map((tag, index) => (
                    <View key={index} style={[styles.glanceTag, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
                      <Text style={[styles.glanceTagText, { color: theme.text }]}>{tag}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Quick Reference Card */}
            <View style={[styles.glanceCard, { backgroundColor: theme.cardBg, borderColor: theme.cardBorder }]}>
              <Text style={[styles.glanceSectionTitle, { color: theme.textTertiary }]}>QUICK REFERENCE</Text>
              <View style={styles.glanceRefGrid}>
                <View style={styles.glanceRefItem}>
                  <Text style={[styles.glanceRefLabel, { color: theme.textTertiary }]}>Basic Fear</Text>
                  <Text style={[styles.glanceRefValue, { color: theme.text }]}>{TYPE_BASIC_FEARS[core]}</Text>
                </View>
                <View style={styles.glanceRefItem}>
                  <Text style={[styles.glanceRefLabel, { color: theme.textTertiary }]}>Basic Desire</Text>
                  <Text style={[styles.glanceRefValue, { color: theme.text }]}>{TYPE_BASIC_DESIRES[core]}</Text>
                </View>
              </View>
            </View>

            {/* Confidence Badge */}
            <View style={styles.glanceFooter}>
              <Text style={[styles.glanceFooterText, { color: theme.textTertiary }]}>
                {result.confidence_tier === 'high' ? 'High' : result.confidence_tier === 'medium' ? 'Moderate' : 'Low'} confidence
              </Text>
              <Text style={[styles.glanceFooterText, { color: theme.textTertiary }]}>
                {' '}·{' '}Based on assessment_inference_v2 results
              </Text>
            </View>
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
    const topProb = result.top_candidates[0]?.probability || 0;
    if (topProb >= 0.7) return { text: 'High confidence', tier: 'high' };
    if (topProb >= 0.5) return { text: 'Moderate confidence', tier: 'medium' };
    return { text: 'Exploratory', tier: 'low' };
  };

  const renderDeepDiveTab = () => {
    // Show loading state
    if (deepDiveLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.textSecondary} />
          <Text style={styles.loadingText}>Loading your Deep Dive...</Text>
        </View>
      );
    }

    // Use API data if available, fallback to local data
    const data = deepDiveData;
    const confidence = data?.confidence_tier || result.confidence_tier;
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
    const isSelfDeclared = result.source === 'self_declared' || result.method === 'self_declared';

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
              {section.label !== 'Core Story' && (
                <Text style={[styles.accordionBodyTitle, { color: theme.text }]}>{section.label}</Text>
              )}
              <Text style={[styles.accordionBodyText, { color: theme.textSecondary }]}>{section.body}</Text>
            </View>
          ))}
        </AccordionSection>

        {/* ═══════════════════════════════════════════════════════════════
            SECTION 2 — STRUCTURE BLOCK
            Understanding your type structure
        ═══════════════════════════════════════════════════════════════ */}
        
        <SectionDivider title="Understanding Your Structure" />

        {/* Your Core Strategy */}
        <AccordionSection
          id="core_strategy"
          title="Your Core Strategy"
          subtitle="How you naturally approach the world"
        >
          <Text style={styles.accordionBodyText}>
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
                  <Text style={styles.structureGridLabel}>Center</Text>
                  <Text style={styles.structureGridValue}>{formatGroupLabel((data?.computed_details || computedDetails)?.center)}</Text>
                </View>
                <View style={styles.structureGridItem}>
                  <Text style={styles.structureGridLabel}>Social Style</Text>
                  <Text style={styles.structureGridValue}>{formatGroupLabel((data?.computed_details || computedDetails)?.hornevian_group)}</Text>
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
                  <Text style={styles.wingCardTitle}>Wing {wing} · {TYPE_NAMES[wing as number]}</Text>
                </View>
              </View>
              
              {/* Core Pattern */}
              <View style={styles.accordionBodySection}>
                <Text style={styles.accordionBodyTitle}>Core Pattern</Text>
                <Text style={styles.accordionBodyText}>
                  {WING_FLAVORS[`${core}w${wing}`]?.pattern || `Your ${wing}-wing adds the qualities of ${TYPE_NAMES[wing as number]} to your core pattern.`}
                </Text>
              </View>
              
              {/* The Tradeoff */}
              <View style={styles.accordionBodySection}>
                <Text style={styles.accordionBodyTitle}>The Tradeoff</Text>
                <Text style={styles.accordionBodyText}>
                  {WING_FLAVORS[`${core}w${wing}`]?.tradeoff || ''}
                </Text>
              </View>
              
              {/* Potential Strength */}
              <View style={styles.accordionBodySection}>
                <Text style={styles.accordionBodyTitle}>Potential Strength</Text>
                <Text style={styles.accordionBodyText}>
                  {WING_FLAVORS[`${core}w${wing}`]?.strength || ''}
                </Text>
              </View>
              
              {/* Experiment */}
              <View style={styles.experimentCard}>
                <View style={styles.experimentHeader}>
                  <Text style={styles.experimentLabel}>Try This</Text>
                </View>
                <Text style={styles.experimentText}>
                  {WING_FLAVORS[`${core}w${wing}`]?.experiment || ''}
                </Text>
              </View>
            </>
          ) : (
            <Text style={styles.accordionBodyText}>
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
              <Text style={styles.wingCardTitle}>Wing {otherWing} · {TYPE_NAMES[otherWing]}</Text>
            </View>
          </View>
          
          {/* Core Pattern */}
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>Core Pattern</Text>
            <Text style={styles.accordionBodyText}>
              {WING_FLAVORS[`${core}w${otherWing}`]?.pattern || `The ${otherWing}-wing offers access to ${TYPE_NAMES[otherWing]} qualities.`}
            </Text>
          </View>
          
          {/* Strength */}
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>Potential Strength</Text>
            <Text style={styles.accordionBodyText}>
              {WING_FLAVORS[`${core}w${otherWing}`]?.strength || ''}
            </Text>
          </View>
          
          {/* Experiment */}
          <View style={styles.experimentCard}>
            <View style={styles.experimentHeader}>
              <Text style={styles.experimentLabel}>Try This</Text>
            </View>
            <Text style={styles.experimentText}>
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
            <Text style={styles.accordionBodyTitle}>The Core Tradeoff</Text>
            <Text style={styles.accordionBodyText}>
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
            <Text style={styles.accordionBodyTitle}>Daily Reflection</Text>
            <Text style={styles.accordionBodyText}>{JOURNAL_PROMPTS[core]}</Text>
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
              <Text style={styles.flowLabel}>Under Stress → Type {(data?.computed_details || computedDetails)?.stress_line_to || '—'}</Text>
            </View>
            <View style={styles.flowItem}>
              <View style={styles.flowIconContainer}>
                <Text style={[styles.flowIconText, { color: '#2E7D32' }]}>↑</Text>
              </View>
              <Text style={styles.flowLabel}>When Resourced → Type {(data?.computed_details || computedDetails)?.growth_line_to || '—'}</Text>
            </View>
          </View>
          
          {/* Stress Section */}
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>Under Stress</Text>
            <Text style={styles.accordionBodyText}>{STRESS_PATTERNS[core]?.pattern}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>The Tradeoff</Text>
            <Text style={styles.accordionBodyText}>{STRESS_PATTERNS[core]?.tradeoff}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>Potential Strength</Text>
            <Text style={styles.accordionBodyText}>{STRESS_PATTERNS[core]?.strength}</Text>
          </View>
          <View style={styles.experimentCard}>
            <View style={styles.experimentHeader}>
              <Text style={styles.experimentLabel}>Try This</Text>
            </View>
            <Text style={styles.experimentText}>{STRESS_PATTERNS[core]?.experiment}</Text>
          </View>
          
          {/* Growth Section */}
          <View style={[styles.accordionBodySection, { marginTop: 24 }]}>
            <Text style={styles.accordionBodyTitle}>When Resourced</Text>
            <Text style={styles.accordionBodyText}>{GROWTH_PATTERNS[core]?.pattern}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>The Tradeoff</Text>
            <Text style={styles.accordionBodyText}>{GROWTH_PATTERNS[core]?.tradeoff}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>Potential Strength</Text>
            <Text style={styles.accordionBodyText}>{GROWTH_PATTERNS[core]?.strength}</Text>
          </View>
          <View style={styles.experimentCard}>
            <View style={styles.experimentHeader}>
              <Text style={styles.experimentLabel}>Try This</Text>
            </View>
            <Text style={styles.experimentText}>{GROWTH_PATTERNS[core]?.experiment}</Text>
          </View>
        </AccordionSection>

        {/* Top Alternatives */}
        <AccordionSection
          id="top_alternatives"
          title="Top Alternatives"
          subtitle="Other patterns worth exploring"
        >
          <Text style={styles.accordionBodyText}>
            Your responses showed resonance with these types. Worth exploring if your primary type doesn't fully land.
          </Text>
          {result.top_candidates.slice(0, 3).map((candidate, index) => (
            <View key={candidate.type} style={styles.alternativeRow}>
              <Text style={styles.alternativeRank}>{index + 1}</Text>
              <View style={styles.alternativeInfo}>
                <Text style={styles.alternativeType}>Type {candidate.type}</Text>
                <Text style={styles.alternativeName}>{TYPE_NAMES[candidate.type]}</Text>
              </View>
              <Text style={styles.alternativePercent}>
                {Math.round(candidate.probability * 100)}%
              </Text>
            </View>
          ))}
        </AccordionSection>

        {/* ═══════════════════════════════════════════════════════════════
            FOOTER
        ═══════════════════════════════════════════════════════════════ */}

        {/* Disclaimer */}
        <View style={styles.disclaimerCard}>
          <Text style={styles.disclaimerText}>
            This isn't a rule—just a Type {core} pattern you might notice; you're free to take what resonates, 
            leave the rest, and only engage it if it feels useful.
          </Text>
        </View>
        
        {/* Chat Box */}
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
              <Text style={[styles.closeButtonText, { color: theme.textSecondary }]}>✕</Text>
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
              <ActivityIndicator size="small" color={theme.textSecondary} />
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
              placeholderTextColor={theme.textTertiary}
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
              <Text style={[
                styles.sendButtonText,
                { color: (!qaQuestion.trim() || qaLoading) ? theme.textTertiary : theme.background }
              ]}>
                ➤
              </Text>
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
  // MAIN RENDER
  // ============================================

  const isSelfDeclared = result.source === 'self_declared' || result.method === 'self_declared';

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {renderTabs()}
      
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
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
    color: "inherit",
  },
  activeTabText: {
    color: "inherit",
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
    color: "inherit",
  },
  deepDiveSubTabTextActive: {
    color: "inherit",
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
    color: "inherit",
    marginBottom: 1,
  },
  accordionSubtitle: {
    fontSize: 12,
    color: "inherit",
    lineHeight: 16,
  },
  accordionChevron: {
    fontSize: 14,
    color: "inherit",
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
    color: "inherit",
    marginBottom: 4,
    letterSpacing: 0.1,
  },
  accordionBodyText: {
    fontSize: 14,
    lineHeight: 21,
    color: "inherit",
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
    color: "inherit",
  },
  wingCardName: {
    fontSize: 15,
    fontWeight: '600',
    color: "inherit",
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
    color: "inherit",
    marginBottom: 2,
  },
  structureGridValue: {
    fontSize: 13,
    fontWeight: '500',
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
  },
  alternativeInfo: {
    flex: 1,
  },
  alternativeType: {
    fontSize: 13,
    fontWeight: '500',
    color: "inherit",
  },
  alternativeName: {
    fontSize: 11,
    color: "inherit",
  },
  alternativePercent: {
    fontSize: 13,
    fontWeight: '500',
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
  },
  heroTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 4,
  },
  heroSubtitle: {
    fontSize: 16,
    color: "inherit",
    marginBottom: 12,
  },
  heroDisclaimer: {
    fontSize: 12,
    color: "inherit",
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
    color: "inherit",
    marginBottom: 2,
  },
  identityName: {
    fontSize: 14,
    color: "inherit",
  },
  identityNote: {
    fontSize: 11,
    color: "inherit",
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
    color: "inherit",
    marginBottom: 8,
  },
  overviewCardBody: {
    fontSize: 14,
    lineHeight: 21,
    color: "inherit",
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
    color: "inherit",
    marginBottom: 3,
  },
  manifestationText: {
    fontSize: 13,
    lineHeight: 19,
    color: "inherit",
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
    color: "inherit",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 22,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    marginBottom: 8,
  },
  cardSubtitle: {
    fontSize: 13,
    color: "inherit",
    marginBottom: 12,
  },
  cardBody: {
    fontSize: 15,
    lineHeight: 22,
    color: "inherit",
  },
  cardNote: {
    fontSize: 13,
    lineHeight: 19,
    color: "inherit",
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
    color: "inherit",
    marginBottom: 4,
  },
  wingValue: {
    fontSize: 16,
    fontWeight: '600',
    color: "inherit",
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
    color: "inherit",
  },
  candidateType: {
    flex: 1,
    fontSize: 14,
    color: "inherit",
  },
  candidatePercent: {
    fontSize: 14,
    fontWeight: '600',
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
  },
  energyButtonTextSelected: {
    color: "inherit",
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
    color: "inherit",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  practiceBody: {
    fontSize: 15,
    lineHeight: 22,
    color: "inherit",
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
    color: "inherit",
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  promptBody: {
    fontSize: 16,
    lineHeight: 24,
    color: "inherit",
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
    color: "inherit",
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  patternValue: {
    fontSize: 14,
    lineHeight: 20,
    color: "inherit",
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
    color: "inherit",
    marginBottom: 4,
  },
  wingFlightValue: {
    fontSize: 20,
    fontWeight: '700',
    color: "inherit",
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
    color: "inherit",
  },
  masteryButtonTextSelected: {
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  experimentText: {
    fontSize: 14,
    lineHeight: 21,
    color: "inherit",
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
    color: "inherit",
  },
  verificationPercent: {
    fontSize: 14,
    fontWeight: '600',
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    flex: 1,
  },
  patternMovementTitleMuted: {
    color: "inherit",
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
    color: "inherit",
  },
  typeCircleNumberMuted: {
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  driftValue: {
    fontSize: 14,
    color: "inherit",
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
    color: "inherit",
  },
  driftSummary: {
    fontSize: 13,
    lineHeight: 19,
    color: "inherit",
    fontStyle: 'italic',
    marginTop: 8,
    textAlign: 'center',
  },
  driftSummaryNeutral: {
    fontSize: 13,
    lineHeight: 19,
    color: "inherit",
    marginTop: 4,
    textAlign: 'center',
  },
  driftDisclaimer: {
    fontSize: 11,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    marginBottom: 12,
  },
  modalText: {
    fontSize: 15,
    lineHeight: 22,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
  },
  chatExpandText: {
    fontSize: 12,
    color: "inherit",
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
    color: "inherit",
  },
  chatMessageTextUser: {
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
  },
  closeButtonText: {
    fontSize: 24,
    fontWeight: '400',
    color: "inherit",
  },
  flowIconText: {
    fontSize: 16,
    fontWeight: '600',
    color: "inherit",
  },
  movementArrowText: {
    fontSize: 18,
    fontWeight: '600',
    color: "inherit",
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
    color: "inherit",
    marginBottom: 2,
  },
  microLessonSubtitle: {
    fontSize: 11,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  microLessonBody: {
    marginBottom: 14,
  },
  microLessonBodyText: {
    fontSize: 15,
    lineHeight: 23,
    color: "inherit",
  },
  microLessonBoldText: {
    fontWeight: '600',
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  structureValue: {
    fontSize: 13,
    fontWeight: '500',
    color: "inherit",
    textAlign: 'center',
  },
  structureSubValue: {
    fontSize: 11,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    marginBottom: 6,
  },
  traitCardBody: {
    fontSize: 14,
    lineHeight: 21,
    color: "inherit",
  },
  traitCardCitation: {
    fontSize: 11,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
  },
  deepDiveWingStance: {
    fontSize: 15,
    fontWeight: '500',
    color: "inherit",
    marginBottom: 4,
  },
  deepDiveNote: {
    fontSize: 11,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    marginBottom: 10,
  },
  deepDiveSectionBody: {
    fontSize: 15,
    lineHeight: 24,
    color: "inherit",
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
    color: "inherit",
    letterSpacing: 0.5,
  },
  mirrorPromptText: {
    fontSize: 15,
    lineHeight: 22,
    color: "inherit",
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
    color: "inherit",
  },
  confidenceText: {
    fontSize: 13,
    fontWeight: '600',
    color: "inherit",
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
    color: "inherit",
    marginBottom: 10,
  },
  wingSectionBody: {
    fontSize: 14,
    lineHeight: 21,
    color: "inherit",
  },
  wingGrowthNoteText: {
    fontSize: 13,
    lineHeight: 20,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
  },
  glanceValue: {
    fontSize: 14,
    fontWeight: '500',
    color: "inherit",
    textAlign: 'right',
  },
  glanceSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
    marginBottom: 4,
  },
  glanceRefValue: {
    fontSize: 14,
    color: "inherit",
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
    color: "inherit",
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
    color: "inherit",
  },
});
