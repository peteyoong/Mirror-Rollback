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
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { 
  sendEnneagramChat, 
  getEnneagramTraits,
  askEnneagramQuestion,
  getEnneagramDeepDive,
  EnneagramTraitCard,
  EnneagramComputedDetails,
  EnneagramDeepDiveSection,
  EnneagramDeepDiveResponse
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

type TabType = 'summary' | 'today' | 'deep_dive';
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
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, activeTab === 'summary' && styles.activeTabText]}>
          Overview
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
    const isSelfDeclared = result.source === 'self_declared' || result.method === 'self_declared';
    
    // Self-declared results show "Self-declared" instead of confidence
    if (isSelfDeclared) {
      return (
        <View style={styles.sourceBadge}>
          <Ionicons name="person-outline" size={12} color={Colors.textSecondary} />
          <Text style={styles.sourceBadgeText}>Self-declared</Text>
        </View>
      );
    }
    
    // Assessment results show confidence tier
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

  const renderSummaryTab = () => {
    const manifestations = PATTERN_MANIFESTATIONS[core];
    
    return (
      <>
        {/* Identity Card */}
        <View style={styles.identityCard}>
          <View style={styles.identityMain}>
            <View style={styles.identityTitleRow}>
              <Text style={styles.identityType}>
                {wing !== 'balanced' ? `${core}w${wing}` : `Type ${core}`}
              </Text>
              <TouchableOpacity 
                style={styles.editTypeInline}
                onPress={handleEditType}
              >
                <Ionicons name="pencil" size={14} color={Colors.textTertiary} />
              </TouchableOpacity>
            </View>
            <Text style={styles.identityName}>{TYPE_NAMES[core]}</Text>
          </View>
          {renderConfidenceBadge()}
          <Text style={styles.identityNote}>
            This lens reflects strategy, not identity.
          </Text>
        </View>

        {/* Core Pattern Card */}
        <View style={styles.overviewCard}>
          <Text style={styles.overviewCardTitle}>Your Core Pattern</Text>
          <Text style={styles.overviewCardBody}>
            {CORE_PATTERNS[core]}
          </Text>
        </View>

        {/* What Drives This Card */}
        <View style={styles.overviewCard}>
          <Text style={styles.overviewCardTitle}>What Drives This</Text>
          <Text style={styles.overviewCardBody}>
            {PATTERN_DRIVERS[core]}
          </Text>
        </View>

        {/* Where This Shows Up Card */}
        <View style={styles.overviewCard}>
          <Text style={styles.overviewCardTitle}>Where This Often Appears</Text>
          <View style={styles.manifestationList}>
            <View style={styles.manifestationItem}>
              <Text style={styles.manifestationLabel}>Decision making</Text>
              <Text style={styles.manifestationText}>{manifestations.decisions}</Text>
            </View>
            <View style={styles.manifestationItem}>
              <Text style={styles.manifestationLabel}>Work & creativity</Text>
              <Text style={styles.manifestationText}>{manifestations.work}</Text>
            </View>
            <View style={styles.manifestationItem}>
              <Text style={styles.manifestationLabel}>Relationships</Text>
              <Text style={styles.manifestationText}>{manifestations.relationships}</Text>
            </View>
            <View style={styles.manifestationItem}>
              <Text style={styles.manifestationLabel}>Under stress</Text>
              <Text style={styles.manifestationText}>{manifestations.stress}</Text>
            </View>
          </View>
        </View>

        {/* Reflection Prompt Card */}
        <View style={styles.reflectionCard}>
          <Text style={styles.reflectionLabel}>A REFLECTION</Text>
          <Text style={styles.reflectionText}>
            "{OVERVIEW_REFLECTIONS[core]}"
          </Text>
        </View>

        {/* Subtle CTA */}
        <TouchableOpacity
          style={styles.subtleLink}
          onPress={() => setActiveTab('deep_dive')}
        >
          <Text style={styles.subtleLinkText}>Explore Deep Dive</Text>
          <Ionicons name="chevron-forward" size={14} color={Colors.textTertiary} />
        </TouchableOpacity>
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
          <ActivityIndicator size="large" color={Colors.textSecondary} />
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
        <View style={styles.accordionCard}>
          <TouchableOpacity 
            style={styles.accordionHeader} 
            onPress={() => toggleSection(id)}
            activeOpacity={0.7}
          >
            <View style={styles.accordionHeaderText}>
              <Text style={styles.accordionTitle}>{title}</Text>
              <Text style={styles.accordionSubtitle}>{subtitle}</Text>
            </View>
            <Ionicons 
              name={isExpanded ? "chevron-up" : "chevron-down"} 
              size={20} 
              color={Colors.textSecondary} 
            />
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
        <Text style={styles.sectionDividerText}>{title}</Text>
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
        <View style={styles.deepDiveHeader}>
          <View style={styles.deepDiveHeaderTop}>
            <View style={styles.identityTitleRow}>
              <Text style={styles.deepDiveType}>{typeLabel}</Text>
              <TouchableOpacity 
                style={styles.editTypeInline}
                onPress={handleEditType}
              >
                <Ionicons name="pencil" size={14} color={Colors.textTertiary} />
              </TouchableOpacity>
            </View>
            {isSelfDeclared ? (
              <View style={styles.sourceBadge}>
                <Ionicons name="person-outline" size={12} color={Colors.textSecondary} />
                <Text style={styles.sourceBadgeText}>Self-declared</Text>
              </View>
            ) : (
              <View style={[
                styles.confidenceBadge,
                confidence === 'high' && styles.confidenceHigh,
                confidence === 'medium' && styles.confidenceMedium,
                confidence === 'low' && styles.confidenceLow,
              ]}>
                <Text style={styles.confidenceBadgeText}>
                  {confidence === 'high' ? 'High Confidence' : confidence === 'medium' ? 'Moderate Confidence' : 'Exploratory'}
                </Text>
              </View>
            )}
          </View>
          <Text style={styles.deepDiveWingStance}>{typeName}</Text>
          <Text style={styles.deepDiveNote}>This lens reflects strategy, not identity.</Text>
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
                <Text style={styles.accordionBodyTitle}>{section.label}</Text>
              )}
              <Text style={styles.accordionBodyText}>{section.body}</Text>
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
                  <Ionicons name="star" size={16} color={Colors.accent} />
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
                  <Ionicons name="flask-outline" size={14} color={Colors.accent} />
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
              <Ionicons name="star-outline" size={16} color={Colors.textSecondary} />
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
              <Ionicons name="flask-outline" size={14} color={Colors.accent} />
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
                <Ionicons name="arrow-down" size={16} color="#E57373" />
              </View>
              <Text style={styles.flowLabel}>Under Stress → Type {(data?.computed_details || computedDetails)?.stress_line_to || '—'}</Text>
            </View>
            <View style={styles.flowItem}>
              <View style={styles.flowIconContainer}>
                <Ionicons name="arrow-up" size={16} color="#81C784" />
              </View>
              <Text style={styles.flowLabel}>When Resourced → Type {(data?.computed_details || computedDetails)?.growth_line_to || '—'}</Text>
            </View>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>Under Stress</Text>
            <Text style={styles.accordionBodyText}>{STRESS_PATTERNS[core]}</Text>
          </View>
          <View style={styles.accordionBodySection}>
            <Text style={styles.accordionBodyTitle}>When Resourced</Text>
            <Text style={styles.accordionBodyText}>{GROWTH_PATTERNS[core]}</Text>
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
  // MAIN RENDER
  // ============================================

  const isSelfDeclared = result.source === 'self_declared' || result.method === 'self_declared';

  return (
    <View style={styles.container}>
      {renderTabs()}
      
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {activeTab === 'summary' && renderSummaryTab()}
        {activeTab === 'today' && renderTodayTab()}
        {activeTab === 'deep_dive' && renderDeepDiveTab()}
        
        {/* Shared Footer - visible on all tabs */}
        <View style={styles.sharedFooter}>
          <View style={styles.footerDivider} />
          <View style={styles.footerActions}>
            <TouchableOpacity
              style={styles.footerAction}
              onPress={() => setShowRetakeModal(true)}
            >
              <Ionicons name="refresh-outline" size={16} color={Colors.textSecondary} />
              <Text style={styles.footerActionText}>Retake Assessment</Text>
            </TouchableOpacity>
            
            <View style={styles.footerDot} />
            
            <TouchableOpacity
              style={styles.footerAction}
              onPress={handleEditType}
            >
              <Ionicons name="pencil-outline" size={16} color={Colors.textSecondary} />
              <Text style={styles.footerActionText}>Edit Type</Text>
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

  // Deep Dive Sub-Tabs
  deepDiveSubTabContainer: {
    flexDirection: 'row',
    backgroundColor: Colors.surface,
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
    backgroundColor: Colors.text,
  },
  deepDiveSubTabText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.textTertiary,
  },
  deepDiveSubTabTextActive: {
    color: Colors.surface,
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
    backgroundColor: Colors.surface,
    borderRadius: 10,
    marginBottom: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
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
    color: Colors.text,
    marginBottom: 1,
  },
  accordionSubtitle: {
    fontSize: 12,
    color: Colors.textTertiary,
    lineHeight: 16,
  },
  accordionContent: {
    paddingHorizontal: 14,
    paddingBottom: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
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
    color: Colors.text,
    marginBottom: 4,
    letterSpacing: 0.1,
  },
  accordionBodyText: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textSecondary,
  },

  // Wing Card (inside accordion)
  wingCard: {
    backgroundColor: 'rgba(255,255,255,0.03)',
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
    color: Colors.textSecondary,
  },
  wingCardName: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },

  // Structure Grid Compact
  structureGridCompact: {
    backgroundColor: 'rgba(255,255,255,0.03)',
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
    color: Colors.textTertiary,
    marginBottom: 2,
  },
  structureGridValue: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
  },

  // Flow Row (stress/growth)
  flowRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: 'rgba(255,255,255,0.03)',
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
    backgroundColor: 'rgba(255,255,255,0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 4,
  },
  flowLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
  },

  // Alternative Rows
  alternativeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  alternativeRank: {
    width: 22,
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textTertiary,
  },
  alternativeInfo: {
    flex: 1,
  },
  alternativeType: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
  },
  alternativeName: {
    fontSize: 11,
    color: Colors.textTertiary,
  },
  alternativePercent: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textSecondary,
  },

  // Disclaimer Card
  disclaimerCard: {
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  disclaimerText: {
    fontSize: 12,
    lineHeight: 18,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    textAlign: 'center',
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
  heroDisclaimer: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 8,
    fontStyle: 'italic',
  },

  // ============================================
  // OVERVIEW TAB STYLES (Redesigned)
  // ============================================

  // Identity Card (new compact design)
  identityCard: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 16,
    alignItems: 'center',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    marginBottom: 10,
  },
  identityMain: {
    alignItems: 'center',
    marginBottom: 8,
  },
  identityType: {
    fontSize: 22,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 2,
  },
  identityName: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  identityNote: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 6,
    fontStyle: 'italic',
  },

  // Overview Cards
  overviewCard: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    marginBottom: 10,
  },
  overviewCardTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  overviewCardBody: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textSecondary,
  },

  // Manifestation List (Where This Shows Up)
  manifestationList: {
    gap: 10,
  },
  manifestationItem: {
    paddingBottom: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  manifestationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 3,
  },
  manifestationText: {
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSecondary,
  },

  // Reflection Card
  reflectionCard: {
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 10,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 2,
    borderLeftColor: Colors.textTertiary,
  },
  reflectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textSecondary,
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
    color: Colors.textTertiary,
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
    gap: 6,
    marginBottom: 8,
  },
  experimentLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.accent,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  experimentText: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.text,
    fontStyle: 'italic',
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
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  sourceBadgeText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.textSecondary,
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
    backgroundColor: 'rgba(255,255,255,0.05)',
  },
  
  // Shared footer (across all tabs)
  sharedFooter: {
    marginTop: 24,
    paddingTop: 16,
  },
  footerDivider: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: Colors.border,
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
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  footerActionText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  footerDot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: Colors.textTertiary,
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
  structureSubValue: {
    fontSize: 11,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 2,
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

  // Section Divider (text-based)
  sectionDivider: {
    marginTop: 12,
    marginBottom: 6,
    paddingVertical: 4,
  },
  sectionDividerText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
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
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
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
    color: Colors.text,
  },
  deepDiveWingStance: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.textSecondary,
    marginBottom: 4,
  },
  deepDiveNote: {
    fontSize: 11,
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
});
