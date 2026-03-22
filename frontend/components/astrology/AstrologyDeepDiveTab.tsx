// ============================================
// ASTROLOGY DEEP DIVE TAB
// Renders: Section groups, Deep Dive cards, expand/collapse, actions
// MIRROR FRAMEWORK: Master Insight + Identity + Tension + Genius + Where This Shows Up + Practical Shift + Reflection
// UNIFIED PATTERN: One integrated pattern that runs through the entire chart
// ============================================

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

import {
  FullChartData,
  CorePlacements,
  AstrologyDeepDiveCard,
} from '../../services/astrology/astrologyTypes';

import {
  SIGN_QUALITIES,
  HOUSE_MEANINGS,
  getHouseTheme,
  getPlanetImportanceLine,
  buildAspectPatternAnalysis,
  buildLifeChapterAnalysis,
  getDominantTruth,
  getUnifiedPattern,
  UnifiedPattern,
} from '../../services/astrology/astrologyInterpreter';

// ============================================
// PROPS INTERFACE
// ============================================

interface AstrologyDeepDiveTabProps {
  placements: CorePlacements;
  fullChartData: FullChartData | null;
  expandedCards: Set<string>;
  toggleCard: (cardId: string) => void;
  onReflect: (card: AstrologyDeepDiveCard) => void;
  onJournal: (card: AstrologyDeepDiveCard) => void;
  onAskMirror: (card: AstrologyDeepDiveCard) => void;
  theme: any;
}

// ============================================
// MIRROR LAYER TYPES
// ============================================

interface MirrorLayer {
  identity: string;       // "You are someone who..."
  tension: string;        // "This can turn into..."
  genius: string;         // "When this is working, you..."
  whereItShowsUp: string[]; // Real-life contexts
  practicalShift: string; // ONE behavioral nudge
  reflection: string;     // Upgraded reflection question
  connectorPhrase?: string; // Optional link to unified pattern
}

// ============================================
// HELPER FUNCTIONS FOR CARD GENERATION
// ============================================

// Planet tension/gift helpers
const getSunTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Can become self-centered, impatient, or combative.',
    'Taurus': 'Can become stubborn, possessive, or resistant to change.',
    'Gemini': 'Can become scattered, superficial, or inconsistent.',
    'Cancer': 'Can become moody, clingy, or overly protective.',
    'Leo': 'Can become arrogant, dramatic, or attention-seeking.',
    'Virgo': 'Can become critical, anxious, or perfectionist.',
    'Libra': 'Can become indecisive, people-pleasing, or conflict-avoidant.',
    'Scorpio': 'Can become controlling, suspicious, or obsessive.',
    'Sagittarius': 'Can become preachy, overcommitted, or escapist.',
    'Capricorn': 'Can become cold, workaholic, or status-obsessed.',
    'Aquarius': 'Can become detached, contrarian, or emotionally unavailable.',
    'Pisces': 'Can become escapist, boundary-less, or martyred.'
  };
  return tensions[sign] || 'A shadow aspect that needs awareness.';
};

const getSunGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'The courage to begin, the ability to act decisively, pioneering spirit.',
    'Taurus': 'The ability to build lasting value, to appreciate beauty, to endure.',
    'Gemini': 'The gift of connection, curiosity that opens doors, mental agility.',
    'Cancer': 'Deep emotional intelligence, the ability to nurture and protect.',
    'Leo': 'Natural warmth and generosity, the ability to inspire and lead.',
    'Virgo': 'The gift of improvement, practical wisdom, devoted service.',
    'Libra': 'The ability to create harmony, natural diplomacy, aesthetic sense.',
    'Scorpio': 'Transformative power, emotional depth, psychological insight.',
    'Sagittarius': 'The gift of meaning-making, expansive vision, infectious optimism.',
    'Capricorn': 'The ability to achieve, structural thinking, responsible leadership.',
    'Aquarius': 'Innovative thinking, humanitarian vision, authentic individuality.',
    'Pisces': 'Transcendent compassion, creative imagination, spiritual sensitivity.'
  };
  return gifts[sign] || 'A distinctive life gift.';
};

const getMoonTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Emotional impatience; reactions that outrun understanding.',
    'Taurus': 'Emotional stubbornness; comfort-seeking that resists necessary change.',
    'Gemini': 'Emotional restlessness; feelings that get intellectualized rather than felt.',
    'Cancer': 'Emotional flooding; boundaries that dissolve under pressure.',
    'Leo': 'Emotional drama; need for recognition that complicates relationships.',
    'Virgo': 'Emotional criticism; feelings processed through perfectionism.',
    'Libra': 'Emotional dependency; feelings sacrificed for harmony.',
    'Scorpio': 'Emotional intensity; feelings that become overwhelming or controlling.',
    'Sagittarius': 'Emotional avoidance; optimism that bypasses difficult feelings.',
    'Capricorn': 'Emotional suppression; feelings managed rather than experienced.',
    'Aquarius': 'Emotional detachment; feelings observed rather than inhabited.',
    'Pisces': 'Emotional absorption; boundaries that let too much in.'
  };
  return tensions[sign] || 'An emotional pattern that needs awareness.';
};

const getMoonGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Emotional courage; quick recovery; ability to feel and move forward.',
    'Taurus': 'Emotional stability; grounded presence; ability to soothe.',
    'Gemini': 'Emotional adaptability; ability to articulate feelings; mental-emotional bridge.',
    'Cancer': 'Deep emotional intuition; nurturing capacity; emotional memory.',
    'Leo': 'Emotional warmth; generosity of heart; ability to celebrate.',
    'Virgo': 'Emotional discernment; practical care; devotion in action.',
    'Libra': 'Emotional grace; relational attunement; harmonizing presence.',
    'Scorpio': 'Emotional depth; transformative feeling; unflinching honesty.',
    'Sagittarius': 'Emotional resilience; hopeful heart; meaningful feeling.',
    'Capricorn': 'Emotional endurance; reliable presence; responsible care.',
    'Aquarius': 'Emotional objectivity; humanitarian feeling; unique sensitivity.',
    'Pisces': 'Emotional compassion; transcendent empathy; imaginative heart.'
  };
  return gifts[sign] || 'A distinctive emotional capacity.';
};

const getMoonNeed = (sign: string): string => {
  const needs: { [key: string]: string } = {
    'Aries': 'action, independence, and something to conquer',
    'Taurus': 'stability, comfort, and tangible security',
    'Gemini': 'mental stimulation, conversation, and variety',
    'Cancer': 'emotional safety, belonging, and nurturing',
    'Leo': 'recognition, creative expression, and warmth',
    'Virgo': 'order, usefulness, and practical contribution',
    'Libra': 'harmony, partnership, and beauty',
    'Scorpio': 'depth, intensity, and emotional truth',
    'Sagittarius': 'meaning, adventure, and philosophical understanding',
    'Capricorn': 'achievement, structure, and respect',
    'Aquarius': 'freedom, intellectual connection, and authenticity',
    'Pisces': 'transcendence, compassion, and spiritual connection'
  };
  return needs[sign] || 'emotional attunement';
};

const getAscTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Can come across as aggressive or self-centered before people know you.',
    'Taurus': 'Can seem rigid or slow to engage when first meeting.',
    'Gemini': 'Can appear scattered or superficial on first impression.',
    'Cancer': 'Can seem guarded or moody before trust is established.',
    'Leo': 'Can come across as attention-seeking or dramatic at first.',
    'Virgo': 'Can seem critical or reserved in new situations.',
    'Libra': 'Can appear indecisive or overly accommodating initially.',
    'Scorpio': 'Can seem intense or intimidating on first meeting.',
    'Sagittarius': 'Can come across as preachy or restless when first engaging.',
    'Capricorn': 'Can seem cold or overly serious on first impression.',
    'Aquarius': 'Can appear detached or contrary when first meeting.',
    'Pisces': 'Can seem vague or spacey in new situations.'
  };
  return tensions[sign] || 'A first-impression pattern that may need awareness.';
};

const getAscGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'A bold, direct presence that initiates and inspires.',
    'Taurus': 'A grounded, reliable presence that creates calm.',
    'Gemini': 'A curious, engaging presence that connects easily.',
    'Cancer': 'A nurturing, protective presence that creates safety.',
    'Leo': 'A warm, magnetic presence that uplifts.',
    'Virgo': 'A helpful, discerning presence that improves.',
    'Libra': 'A graceful, harmonizing presence that creates ease.',
    'Scorpio': 'A powerful, perceptive presence that sees deeply.',
    'Sagittarius': 'An optimistic, expansive presence that inspires growth.',
    'Capricorn': 'A capable, authoritative presence that builds respect.',
    'Aquarius': 'An original, innovative presence that challenges norms.',
    'Pisces': 'A compassionate, intuitive presence that transcends.'
  };
  return gifts[sign] || 'A distinctive way of meeting the world.';
};

const getMercuryLearningStyle = (sign: string): string => {
  const styles: { [key: string]: string } = {
    'Aries': 'direct experience and quick engagement',
    'Taurus': 'practical application and sensory learning',
    'Gemini': 'conversation, variety, and making connections',
    'Cancer': 'emotional connection and personal relevance',
    'Leo': 'creative involvement and personal expression',
    'Virgo': 'systematic analysis and detailed understanding',
    'Libra': 'discussion, comparison, and relational context',
    'Scorpio': 'deep investigation and understanding motives',
    'Sagittarius': 'big picture first, then exploring connections',
    'Capricorn': 'structured progression and practical outcomes',
    'Aquarius': 'innovative approaches and pattern recognition',
    'Pisces': 'intuitive absorption and imaginative connection'
  };
  return styles[sign] || 'varied approaches';
};

const getMercuryTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Can speak before thinking, interrupt, or become impatient with detail.',
    'Taurus': 'Can be mentally stubborn, slow to update views, or resistant to new ideas.',
    'Gemini': 'Can be scattered, superficial, or unable to settle on one perspective.',
    'Cancer': 'Can be moody in communication, defensive, or take things personally.',
    'Leo': 'Can be dramatic in expression, fixed in opinion, or need to be heard.',
    'Virgo': 'Can be overly critical, anxious about details, or perfectionist.',
    'Libra': 'Can be indecisive, conflict-avoidant, or overly diplomatic.',
    'Scorpio': 'Can be secretive, suspicious, or obsessive in thinking.',
    'Sagittarius': 'Can be preachy, over-promise, or lack follow-through.',
    'Capricorn': 'Can be pessimistic, rigid, or overly focused on outcomes.',
    'Aquarius': 'Can be contrarian, detached, or stubborn about unconventional views.',
    'Pisces': 'Can be vague, confused, or too impressionable.'
  };
  return tensions[sign] || 'A communication pattern that needs awareness.';
};

const getMercuryGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Direct, decisive communication that cuts through complexity.',
    'Taurus': 'Practical, grounded thinking that builds lasting understanding.',
    'Gemini': 'Versatile, quick-minded communication that makes connections.',
    'Cancer': 'Intuitive, emotionally intelligent communication.',
    'Leo': 'Expressive, creative communication that inspires.',
    'Virgo': 'Precise, analytical thinking that improves and refines.',
    'Libra': 'Diplomatic, balanced communication that creates understanding.',
    'Scorpio': 'Penetrating, insightful thinking that sees beneath surface.',
    'Sagittarius': 'Expansive, meaning-making communication that inspires.',
    'Capricorn': 'Strategic, authoritative thinking that achieves.',
    'Aquarius': 'Innovative, original thinking that challenges convention.',
    'Pisces': 'Imaginative, intuitive communication that transcends.'
  };
  return gifts[sign] || 'A distinctive communication capacity.';
};

const getVenusLoveLanguage = (sign: string): string => {
  const languages: { [key: string]: string } = {
    'Aries': 'bold pursuit and direct expression of desire',
    'Taurus': 'physical affection and sensory pleasure',
    'Gemini': 'conversation, mental connection, and variety',
    'Cancer': 'nurturing, protection, and emotional presence',
    'Leo': 'generous gestures, celebration, and admiration',
    'Virgo': 'acts of service and practical devotion',
    'Libra': 'romantic gestures, beauty, and partnership',
    'Scorpio': 'emotional intensity and transformative connection',
    'Sagittarius': 'shared adventure and philosophical connection',
    'Capricorn': 'commitment, responsibility, and building together',
    'Aquarius': 'intellectual connection and respecting independence',
    'Pisces': 'imaginative romance and spiritual connection'
  };
  return languages[sign] || 'distinctive expressions of care';
};

const getVenusTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Love can be impatient, competitive, or self-focused.',
    'Taurus': 'Love can become possessive, materialistic, or stagnant.',
    'Gemini': 'Love can be fickle when variety competes with commitment.',
    'Cancer': 'Love can be smothering when nurturing becomes control.',
    'Leo': 'Love can demand recognition, making partners feel like audiences.',
    'Virgo': 'Love can be critical, improving instead of accepting.',
    'Libra': 'Love can lose self in partnership, abandoning personal needs.',
    'Scorpio': 'Love can become obsessive or test loyalty destructively.',
    'Sagittarius': 'Love can prioritize freedom over presence.',
    'Capricorn': 'Love can be conditional, tied to achievement or status.',
    'Aquarius': 'Love can be emotionally distant or afraid of closeness.',
    'Pisces': 'Love can lose boundaries, becoming sacrifice.'
  };
  return tensions[sign] || 'A relational pattern that needs awareness.';
};

const getVenusGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Passionate love that fights for what it values.',
    'Taurus': 'Devoted love that builds lasting beauty.',
    'Gemini': 'Stimulating love that keeps connection alive.',
    'Cancer': 'Nurturing love that creates deep belonging.',
    'Leo': 'Generous love that celebrates and uplifts.',
    'Virgo': 'Devoted love that shows up in practical ways.',
    'Libra': 'Harmonizing love that creates beauty together.',
    'Scorpio': 'Transformative love that goes all the way.',
    'Sagittarius': 'Expansive love that grows through shared meaning.',
    'Capricorn': 'Committed love that builds something lasting.',
    'Aquarius': 'Accepting love that honors individuality.',
    'Pisces': 'Transcendent love that sees the soul.'
  };
  return gifts[sign] || 'A distinctive way of loving.';
};

const getMarsAngerStyle = (sign: string): string => {
  const styles: { [key: string]: string } = {
    'Aries': 'quick flare-ups that pass fast',
    'Taurus': 'slow burn that builds to explosion',
    'Gemini': 'sharp words and cutting remarks',
    'Cancer': 'passive aggression or emotional withdrawal',
    'Leo': 'dramatic displays that demand attention',
    'Virgo': 'critical analysis and cold distance',
    'Libra': 'avoidance until resentment overflows',
    'Scorpio': 'strategic retaliation or cutting silence',
    'Sagittarius': 'blunt honesty that can be tactless',
    'Capricorn': 'controlled coldness or withholding',
    'Aquarius': 'detached dismissal or sudden rebellion',
    'Pisces': 'martyrdom or passive aggression'
  };
  return styles[sign] || 'distinctive reactions';
};

const getMarsTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Can be reckless, combative, or burn bridges.',
    'Taurus': 'Can be stubborn, possessive, or explosively angry when pushed.',
    'Gemini': 'Can be inconsistent, scattered, or cutting with words.',
    'Cancer': 'Can be passive-aggressive or manipulative when hurt.',
    'Leo': 'Can be dominating, dramatic, or need to always win.',
    'Virgo': 'Can be critical, cold, or obsessively controlling.',
    'Libra': 'Can be passive, indecisive, or resentful of others\' choices.',
    'Scorpio': 'Can be vindictive, obsessive, or destructively intense.',
    'Sagittarius': 'Can be reckless, preachy, or commit without follow-through.',
    'Capricorn': 'Can be cold, calculating, or ruthlessly ambitious.',
    'Aquarius': 'Can be rebellious, detached, or stubbornly unconventional.',
    'Pisces': 'Can be passive, escapist, or martyr to others\' desires.'
  };
  return tensions[sign] || 'An action pattern that needs awareness.';
};

const getMarsGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Courageous action that initiates and leads.',
    'Taurus': 'Determined persistence that builds and protects.',
    'Gemini': 'Quick, adaptable action that outmaneuvers.',
    'Cancer': 'Protective action that defends what matters.',
    'Leo': 'Creative action that inspires and leads with heart.',
    'Virgo': 'Precise action that improves and serves.',
    'Libra': 'Strategic action that creates fairness.',
    'Scorpio': 'Powerful action that transforms completely.',
    'Sagittarius': 'Expansive action that opens new territory.',
    'Capricorn': 'Strategic action that achieves lasting goals.',
    'Aquarius': 'Innovative action that breaks old patterns.',
    'Pisces': 'Inspired action that serves something greater.'
  };
  return gifts[sign] || 'A distinctive action capacity.';
};

// ============================================
// MIRROR LAYER GENERATORS
// ============================================

const generateSunMirrorLayer = (sign: string, house?: number): MirrorLayer => {
  const identityMap: { [key: string]: string } = {
    'Aries': 'You are someone who needs to lead with courage. Starting things, taking initiative, being first—this is how you feel most alive.',
    'Taurus': 'You are someone who builds. Slowly, deliberately, with your hands and your values. Stability isn\'t boring to you—it\'s the foundation.',
    'Gemini': 'You are someone who connects ideas. Your mind doesn\'t rest; it bridges, links, and weaves information into meaning.',
    'Cancer': 'You are someone who protects. You feel things deeply, remember everything, and create safety for those you love.',
    'Leo': 'You are someone who radiates. Your presence matters, your expression matters, and you light up when you\'re seen for who you actually are.',
    'Virgo': 'You are someone who improves. You notice what\'s not working, and something in you needs to fix it, refine it, make it better.',
    'Libra': 'You are someone who harmonizes. You see both sides, you weigh things, and you need beauty and balance to feel whole.',
    'Scorpio': 'You are someone who goes deep. Surface-level isn\'t enough. You need truth, intensity, and transformation.',
    'Sagittarius': 'You are someone who seeks meaning. Adventure, philosophy, the big picture—you need to understand why any of this matters.',
    'Capricorn': 'You are someone who achieves. Structure, discipline, long-term thinking—you build things that last.',
    'Aquarius': 'You are someone who breaks patterns. Convention doesn\'t convince you. You need to find your own way.',
    'Pisces': 'You are someone who transcends. Boundaries blur for you. You feel everything, imagine everything, dissolve into the larger whole.'
  };
  
  const tensionMap: { [key: string]: string } = {
    'Aries': 'This can turn into impatience that burns bridges. You might notice it when you\'ve already moved on while others are still processing. The need to win can override the need to connect.',
    'Taurus': 'This can turn into stubbornness that keeps you stuck. You might notice it when you\'re holding onto something that stopped working long ago. Comfort becomes a cage.',
    'Gemini': 'This can turn into scattered attention that never lands. You might notice it when conversations feel exhausting instead of energizing. Too many ideas, not enough depth.',
    'Cancer': 'This can turn into emotional flooding that overwhelms. You might notice it when your mood controls the room. Protection becomes smothering.',
    'Leo': 'This can turn into a need for constant validation. You might notice it when you\'re performing instead of being. The light you give starts to feel like a transaction.',
    'Virgo': 'This can turn into criticism that nothing escapes. You might notice it when the voice in your head won\'t stop finding flaws—in yourself, in others, in everything. Perfection becomes paralysis.',
    'Libra': 'This can turn into losing yourself in other people\'s preferences. You might notice it when you realize you have no idea what you actually want. Harmony becomes self-abandonment.',
    'Scorpio': 'This can turn into intensity that exhausts everyone, including you. You might notice it when you\'re testing people\'s loyalty or holding grudges that poison you more than them.',
    'Sagittarius': 'This can turn into restlessness that never settles. You might notice it when commitment feels like suffocation. The search for meaning becomes an escape from the present.',
    'Capricorn': 'This can turn into coldness that shuts people out. You might notice it when work has replaced everything else. Achievement becomes the only measure of worth.',
    'Aquarius': 'This can turn into detachment that keeps everyone at arm\'s length. You might notice it when being different matters more than being connected. Independence becomes isolation.',
    'Pisces': 'This can turn into losing yourself entirely. You might notice it when you can\'t tell where you end and others begin. Compassion becomes self-erasure.'
  };
  
  const geniusMap: { [key: string]: string } = {
    'Aries': 'When this is working, you\'re the spark that starts things. You move first, and your courage gives others permission to follow. You show people what\'s possible when fear doesn\'t drive.',
    'Taurus': 'When this is working, you\'re the ground others stand on. Your steadiness calms chaos. You show people what\'s possible when you don\'t rush.',
    'Gemini': 'When this is working, you\'re the bridge between worlds. Your mind connects things no one else sees. You show people that everything is related.',
    'Cancer': 'When this is working, you\'re the emotional anchor. Your care creates containers where people feel safe to be vulnerable. You show people what it means to truly belong.',
    'Leo': 'When this is working, you\'re the sun around which others orbit. Your warmth is genuine, your generosity bottomless. You show people what it means to fully shine.',
    'Virgo': 'When this is working, you\'re the one who makes things better. Your eye for improvement is a gift—not a judgment. You show people that care lives in the details.',
    'Libra': 'When this is working, you\'re the one who creates peace. Your ability to hold multiple perspectives without judgment is rare. You show people that fairness is possible.',
    'Scorpio': 'When this is working, you\'re the one who sees what\'s hidden. Your emotional X-ray vision cuts through pretense. You show people that truth, however painful, is freedom.',
    'Sagittarius': 'When this is working, you\'re the one who expands horizons. Your enthusiasm is contagious, your optimism earned. You show people that meaning exists if you look for it.',
    'Capricorn': 'When this is working, you\'re the one who builds things that last. Your discipline creates structures others can rely on. You show people that some things are worth sacrificing for.',
    'Aquarius': 'When this is working, you\'re the one who sees what\'s next. Your vision isn\'t weird—it\'s ahead of its time. You show people that the rules were always negotiable.',
    'Pisces': 'When this is working, you\'re the one who feels what others can\'t. Your sensitivity is a gift that lets you access the transcendent. You show people that there\'s more to reality than what\'s visible.'
  };
  
  const whereItShowsUpMap: { [key: string]: string[] } = {
    'Aries': ['In conversations, when you cut to the point while others are still warming up', 'In decisions, when you\'ve already acted while others are still debating', 'In relationships, when you push for directness over diplomacy', 'In your internal dialogue, when patience feels like weakness'],
    'Taurus': ['In conversations, when you need time to think before responding', 'In decisions, when you resist changes that feel rushed', 'In relationships, when you show love through consistency, not grand gestures', 'In your internal dialogue, when stability feels like the only safe option'],
    'Gemini': ['In conversations, when you connect ideas others miss', 'In decisions, when you see too many angles to choose quickly', 'In relationships, when you need mental stimulation to stay engaged', 'In your internal dialogue, when multiple voices compete for attention'],
    'Cancer': ['In conversations, when you remember emotional details from years ago', 'In decisions, when gut feelings override logic', 'In relationships, when you create safety before you share', 'In your internal dialogue, when past hurts still run the show'],
    'Leo': ['In conversations, when you naturally become the center', 'In decisions, when your self-expression is non-negotiable', 'In relationships, when you need to feel special to feel loved', 'In your internal dialogue, when not being seen feels like disappearing'],
    'Virgo': ['In conversations, when you notice the flaw no one else sees', 'In decisions, when you analyze every possible outcome', 'In relationships, when you help by fixing instead of just listening', 'In your internal dialogue, when the critic never rests'],
    'Libra': ['In conversations, when you see both sides of every argument', 'In decisions, when choosing feels like losing', 'In relationships, when you mirror the other person\'s preferences', 'In your internal dialogue, when "what do I want?" draws a blank'],
    'Scorpio': ['In conversations, when you sense the subtext no one\'s saying', 'In decisions, when you trust your gut over evidence', 'In relationships, when you test people before trusting them', 'In your internal dialogue, when letting go feels like betrayal'],
    'Sagittarius': ['In conversations, when you connect the anecdote to the philosophy', 'In decisions, when freedom trumps security', 'In relationships, when you need room to grow', 'In your internal dialogue, when settling feels like dying'],
    'Capricorn': ['In conversations, when you cut the small talk and get to business', 'In decisions, when long-term outcomes matter more than immediate comfort', 'In relationships, when you show love through responsibility', 'In your internal dialogue, when rest feels like laziness'],
    'Aquarius': ['In conversations, when you argue the unconventional position', 'In decisions, when doing it the normal way feels wrong', 'In relationships, when you need space to be yourself', 'In your internal dialogue, when fitting in feels like selling out'],
    'Pisces': ['In conversations, when you absorb the other person\'s mood', 'In decisions, when intuition speaks louder than logic', 'In relationships, when boundaries blur and merge', 'In your internal dialogue, when reality and imagination mix']
  };
  
  const practicalShiftMap: { [key: string]: string } = {
    'Aries': 'Before you act, ask: "What happens after I win?"',
    'Taurus': 'When you feel stuck, change one small thing today.',
    'Gemini': 'Pick one idea and follow it deeper, not wider.',
    'Cancer': 'Say what you need before you get hurt.',
    'Leo': 'Give without needing applause. Just once. Notice how it feels.',
    'Virgo': 'Name something that\'s good enough—and leave it alone.',
    'Libra': 'State your preference before asking for theirs.',
    'Scorpio': 'Trust someone before they\'ve proven themselves. Small stakes.',
    'Sagittarius': 'Stay with one thing past the point of boredom.',
    'Capricorn': 'Do something with no productive outcome. Call it rest.',
    'Aquarius': 'Agree with someone today—just to see what it feels like.',
    'Pisces': 'Say "no" to one request. Your needs are real too.'
  };
  
  const reflectionMap: { [key: string]: string } = {
    'Aries': 'When was the last time you stayed in something hard instead of starting something new?',
    'Taurus': 'What are you holding onto that you already know isn\'t working?',
    'Gemini': 'What would you discover if you stopped gathering information and started deciding?',
    'Cancer': 'What would you ask for if you weren\'t afraid of being too much?',
    'Leo': 'When do you perform instead of just being yourself?',
    'Virgo': 'What would happen if you stopped fixing things for one week?',
    'Libra': 'What do you actually want—not what seems fair, not what they want—what do you want?',
    'Scorpio': 'What grudge is costing you more than the person who caused it?',
    'Sagittarius': 'What are you running from by always running toward?',
    'Capricorn': 'When did ambition become a hiding place?',
    'Aquarius': 'What would change if being different stopped being your identity?',
    'Pisces': 'Where does your compassion for others turn into abandonment of yourself?'
  };
  
  return {
    identity: identityMap[sign] || `You are someone defined by ${sign} qualities.`,
    tension: tensionMap[sign] || `This can turn into a shadow pattern when taken too far.`,
    genius: geniusMap[sign] || `When this is working, you express the highest form of ${sign}.`,
    whereItShowsUp: whereItShowsUpMap[sign] || ['In various life situations'],
    practicalShift: practicalShiftMap[sign] || 'Notice this pattern in action today.',
    reflection: reflectionMap[sign] || `How does ${sign} show up in your daily life?`
  };
};

const generateMoonMirrorLayer = (sign: string, house?: number): MirrorLayer => {
  const identityMap: { [key: string]: string } = {
    'Aries': 'You are someone who processes feelings through action. Sitting with emotions feels unbearable—you need to move, fight, fix.',
    'Taurus': 'You are someone who needs emotional stability to function. Change unsettles you. You process feelings slowly, through the body.',
    'Gemini': 'You are someone who thinks about feelings more than feels them. Your emotional life runs through your mind first.',
    'Cancer': 'You are someone with an emotional ocean inside. You feel everything—yours and everyone else\'s. Memory and mood are intertwined.',
    'Leo': 'You are someone who needs to be seen emotionally. Your feelings are large, dramatic, and need expression to be real.',
    'Virgo': 'You are someone who processes emotions through analysis. You need to understand your feelings before you can have them.',
    'Libra': 'You are someone who feels through others. Relationships are your emotional ecosystem. Alone, your feelings get confusing.',
    'Scorpio': 'You are someone who feels at full intensity. Your emotions don\'t do moderate. You need depth or nothing.',
    'Sagittarius': 'You are someone who needs emotional freedom. Heavy feelings need to be converted into meaning to be bearable.',
    'Capricorn': 'You are someone who manages emotions like tasks. Feelings are handled, contained, scheduled if necessary.',
    'Aquarius': 'You are someone who observes your emotions from a distance. You think about feelings more than you swim in them.',
    'Pisces': 'You are someone without clear emotional boundaries. You absorb everything—your feelings, their feelings, the room\'s feelings.'
  };
  
  const tensionMap: { [key: string]: string } = {
    'Aries': 'This can turn into reacting before understanding. You might notice it when anger makes the decision, or when you\'ve moved on while still hurt.',
    'Taurus': 'This can turn into emotional stubbornness—holding onto feelings past their usefulness. You might notice it when comfort becomes avoidance.',
    'Gemini': 'This can turn into intellectualizing your way out of feeling. You might notice it when you can explain the emotion but can\'t actually experience it.',
    'Cancer': 'This can turn into drowning in your own feelings or using emotions to control. You might notice it when your mood runs the household.',
    'Leo': 'This can turn into needing an audience for your feelings. You might notice it when emotions that aren\'t witnessed don\'t feel real.',
    'Virgo': 'This can turn into criticizing yourself for having feelings. You might notice it when emotions feel like failures to fix.',
    'Libra': 'This can turn into losing your own feelings in someone else\'s. You might notice it when you don\'t know what you feel until you see their reaction.',
    'Scorpio': 'This can turn into emotional intensity that overwhelms everything. You might notice it when jealousy or suspicion takes the wheel.',
    'Sagittarius': 'This can turn into escaping difficult feelings through optimism or adventure. You might notice it when sadness gets converted to philosophy too fast.',
    'Capricorn': 'This can turn into suppressing emotions until they become physical symptoms. You might notice it when you literally don\'t have time for feelings.',
    'Aquarius': 'This can turn into analyzing feelings instead of having them. You might notice it when emotions feel like problems to solve.',
    'Pisces': 'This can turn into emotional chaos without boundaries. You might notice it when you can\'t tell whose feelings you\'re actually carrying.'
  };
  
  const geniusMap: { [key: string]: string } = {
    'Aries': 'When this is working, you process feelings quickly and move forward clean. Your emotional courage lets you feel things others avoid.',
    'Taurus': 'When this is working, you\'re emotionally unshakeable. Your calm steadies everyone around you. You feel in your body, not your head.',
    'Gemini': 'When this is working, you name emotions precisely. Your ability to articulate feelings helps others understand their own.',
    'Cancer': 'When this is working, you create emotional safety for everyone. Your intuition about feelings is almost psychic. You remember what matters.',
    'Leo': 'When this is working, you warm every room you\'re in. Your emotional generosity is genuine, not performance. You celebrate freely.',
    'Virgo': 'When this is working, you show care through specific, practical acts. Your emotional discernment catches what needs attention.',
    'Libra': 'When this is working, you harmonize emotional atmospheres. Your attunement to others creates peace. You feel grace.',
    'Scorpio': 'When this is working, you go places emotionally that others fear. Your intensity is healing, not overwhelming. You see truth.',
    'Sagittarius': 'When this is working, you find meaning in difficult emotions. Your resilience is real, not a bypass. You stay hopeful without faking.',
    'Capricorn': 'When this is working, you\'re emotionally reliable. Your steadiness in crisis anchors everyone. You feel responsibility as care.',
    'Aquarius': 'When this is working, you see emotions clearly without drowning. Your objectivity about feelings helps you and others understand.',
    'Pisces': 'When this is working, you feel for the whole. Your compassion is bottomless. You access emotional realms others can\'t reach.'
  };
  
  const whereItShowsUpMap: { [key: string]: string[] } = {
    'Aries': ['In conflict, when you fight instead of feel', 'In relationships, when you need action to process hurt', 'In sadness, when you convert it to anger', 'In your private moments, when stillness feels threatening'],
    'Taurus': ['In change, when your body resists before your mind agrees', 'In relationships, when you cling to what\'s familiar', 'In stress, when you reach for comfort', 'In your private moments, when routine feels like safety'],
    'Gemini': ['In difficult conversations, when you explain instead of express', 'In relationships, when you need to talk through feelings', 'In sadness, when you analyze instead of cry', 'In your private moments, when your mind won\'t stop'],
    'Cancer': ['In relationships, when you know what they feel before they do', 'In conflict, when past hurts flood present situations', 'In stress, when you retreat to safety', 'In your private moments, when memories run the show'],
    'Leo': ['In relationships, when you need recognition for your feelings', 'In conflict, when drama amplifies', 'In joy, when you need to share it to feel it', 'In your private moments, when unseen emotions feel less real'],
    'Virgo': ['In stress, when you try to fix your feelings', 'In relationships, when you help instead of sharing', 'In vulnerability, when analysis protects you', 'In your private moments, when the inner critic never stops'],
    'Libra': ['In relationships, when you adjust to their emotional needs', 'In conflict, when you can\'t find your position', 'In alone time, when your feelings get foggy', 'In your private moments, when you need others to know yourself'],
    'Scorpio': ['In relationships, when you test trust before you give it', 'In conflict, when you go quiet and strategic', 'In hurt, when you remember everything', 'In your private moments, when intensity is your baseline'],
    'Sagittarius': ['In relationships, when you need freedom to feel safe', 'In sadness, when you convert it to a lesson', 'In commitment, when the walls close in', 'In your private moments, when meaning-making overrides feeling'],
    'Capricorn': ['In relationships, when you show love through doing', 'In vulnerability, when you manage instead of feel', 'In stress, when you work harder', 'In your private moments, when rest feels irresponsible'],
    'Aquarius': ['In relationships, when you need space to process', 'In conflict, when you detach to think', 'In vulnerability, when feelings feel irrational', 'In your private moments, when you watch your emotions from above'],
    'Pisces': ['In relationships, when you absorb their emotions as yours', 'In conflict, when you escape into imagination', 'In overwhelm, when boundaries dissolve', 'In your private moments, when reality blurs with dreams']
  };
  
  const practicalShiftMap: { [key: string]: string } = {
    'Aries': 'Feel it for 60 seconds before you do anything about it.',
    'Taurus': 'Name one emotion you\'ve been sitting on too long.',
    'Gemini': 'Let yourself cry without explaining why.',
    'Cancer': 'Check: is this feeling yours, or theirs?',
    'Leo': 'Feel something fully without telling anyone.',
    'Virgo': 'Have the feeling without trying to fix it.',
    'Libra': 'What do YOU feel? Say it first.',
    'Scorpio': 'Let something go that you\'ve been holding against someone.',
    'Sagittarius': 'Sit with sadness without making it meaningful.',
    'Capricorn': 'Cancel one thing to feel whatever\'s underneath.',
    'Aquarius': 'Let an emotion be irrational and have it anyway.',
    'Pisces': 'Name one feeling that\'s definitely yours.'
  };
  
  const reflectionMap: { [key: string]: string } = {
    'Aries': 'What feeling are you avoiding by staying busy?',
    'Taurus': 'What emotion would change if you let it, but you won\'t let it?',
    'Gemini': 'What feeling have you explained to death but never actually felt?',
    'Cancer': 'Whose emotions are you carrying that aren\'t yours?',
    'Leo': 'What would you feel if no one was watching?',
    'Virgo': 'What emotion do you judge yourself for having?',
    'Libra': 'If their reaction didn\'t matter, what would you actually feel?',
    'Scorpio': 'What are you punishing yourself for by holding onto?',
    'Sagittarius': 'What sadness have you converted to a story instead of grieving?',
    'Capricorn': 'What would you feel if you let yourself stop achieving?',
    'Aquarius': 'What emotion scares you because it doesn\'t make sense?',
    'Pisces': 'Where do you end and the world begins?'
  };
  
  return {
    identity: identityMap[sign] || `You process emotions through ${sign} qualities.`,
    tension: tensionMap[sign] || `This can turn into an emotional shadow pattern.`,
    genius: geniusMap[sign] || `When this is working, you express emotional ${sign} at its best.`,
    whereItShowsUp: whereItShowsUpMap[sign] || ['In various emotional situations'],
    practicalShift: practicalShiftMap[sign] || 'Notice your emotional patterns today.',
    reflection: reflectionMap[sign] || `How do your ${sign} emotions really work?`
  };
};

const generateAscendantMirrorLayer = (sign: string): MirrorLayer => {
  const identityMap: { [key: string]: string } = {
    'Aries': 'You are someone who enters every room like you\'re starting something. Direct, immediate, undisguised.',
    'Taurus': 'You are someone who enters every room like you\'re settling in. Grounded, unhurried, present.',
    'Gemini': 'You are someone who enters every room like you\'re looking for the conversation. Curious, quick, adaptable.',
    'Cancer': 'You are someone who enters every room reading the emotional temperature. Careful, protective, feeling your way in.',
    'Leo': 'You are someone who enters every room like you belong at the center. Warm, confident, taking up space.',
    'Virgo': 'You are someone who enters every room noticing what needs improvement. Helpful, observant, unassuming.',
    'Libra': 'You are someone who enters every room creating harmony. Graceful, diplomatic, adjusting to the atmosphere.',
    'Scorpio': 'You are someone who enters every room scanning for depth and danger. Intense, controlled, seeing everything.',
    'Sagittarius': 'You are someone who enters every room like it\'s an opportunity. Optimistic, expansive, ready for adventure.',
    'Capricorn': 'You are someone who enters every room assessing the hierarchy. Serious, capable, quietly in charge.',
    'Aquarius': 'You are someone who enters every room as the individual. Detached, unique, slightly outside.',
    'Pisces': 'You are someone who enters every room absorbing its essence. Soft, permeable, dreamy.'
  };
  
  const tensionMap: { [key: string]: string } = {
    'Aries': 'This can come across as aggressive or self-absorbed before people know you. You might notice it when people seem defensive around you for no reason.',
    'Taurus': 'This can come across as stubborn or slow before people know you. You might notice it when people assume you\'re not interested.',
    'Gemini': 'This can come across as scattered or superficial before people know you. You might notice it when people don\'t take you seriously.',
    'Cancer': 'This can come across as guarded or moody before people know you. You might notice it when people feel they need to walk on eggshells.',
    'Leo': 'This can come across as attention-seeking or arrogant before people know you. You might notice it when people assume you\'re performing.',
    'Virgo': 'This can come across as critical or cold before people know you. You might notice it when people feel judged around you.',
    'Libra': 'This can come across as indecisive or fake before people know you. You might notice it when people aren\'t sure who you really are.',
    'Scorpio': 'This can come across as intimidating or secretive before people know you. You might notice it when people seem guarded around you.',
    'Sagittarius': 'This can come across as preachy or careless before people know you. You might notice it when people assume you\'re not serious.',
    'Capricorn': 'This can come across as cold or humorless before people know you. You might notice it when people seem intimidated.',
    'Aquarius': 'This can come across as aloof or contrary before people know you. You might notice it when people assume you think you\'re better than them.',
    'Pisces': 'This can come across as spacey or unreliable before people know you. You might notice it when people don\'t trust you with practical things.'
  };
  
  const geniusMap: { [key: string]: string } = {
    'Aries': 'When this is working, you initiate what needs to happen. Your directness cuts through social fog. People feel alive around you.',
    'Taurus': 'When this is working, you calm every room you enter. Your groundedness is contagious. People feel steadier around you.',
    'Gemini': 'When this is working, you connect instantly with anyone. Your curiosity opens doors. People feel interesting around you.',
    'Cancer': 'When this is working, you create emotional safety instantly. Your warmth is protective. People feel cared for around you.',
    'Leo': 'When this is working, you brighten every room. Your presence is warm, not demanding. People feel celebrated around you.',
    'Virgo': 'When this is working, you improve every situation you touch. Your helpfulness is genuine. People feel supported around you.',
    'Libra': 'When this is working, you create grace wherever you go. Your diplomacy is real. People feel more beautiful around you.',
    'Scorpio': 'When this is working, you see what others miss. Your intensity is magnetic, not threatening. People feel truly seen around you.',
    'Sagittarius': 'When this is working, you expand every conversation. Your optimism is earned, not naive. People feel more possible around you.',
    'Capricorn': 'When this is working, you bring competence to every situation. Your seriousness is respected. People feel they can rely on you.',
    'Aquarius': 'When this is working, you bring originality everywhere. Your difference is refreshing. People feel permission to be weird around you.',
    'Pisces': 'When this is working, you bring gentleness to every interaction. Your sensitivity is healing. People feel understood around you.'
  };
  
  const whereItShowsUpMap: { [key: string]: string[] } = {
    'Aries': ['In first meetings, when you come on strong', 'In groups, when you naturally take charge', 'In your body language, when you lead with your face and chest', 'In small talk, when you cut to the chase'],
    'Taurus': ['In first meetings, when you take your time to warm up', 'In groups, when you find your spot and stay there', 'In your body language, when you ground through your feet', 'In small talk, when you prefer silence to filler'],
    'Gemini': ['In first meetings, when you ask questions immediately', 'In groups, when you work the room', 'In your body language, when your hands talk as much as your mouth', 'In small talk, when you actually enjoy it'],
    'Cancer': ['In first meetings, when you feel people out before opening up', 'In groups, when you gravitate to the edges first', 'In your body language, when you create protective barriers', 'In small talk, when you remember personal details'],
    'Leo': ['In first meetings, when you\'re the one people notice', 'In groups, when attention finds you without trying', 'In your body language, when you take up space naturally', 'In small talk, when you turn it into connection'],
    'Virgo': ['In first meetings, when you assess what\'s needed', 'In groups, when you find a way to be useful', 'In your body language, when you notice before speaking', 'In small talk, when you listen more than talk'],
    'Libra': ['In first meetings, when you mirror the other person', 'In groups, when you create balance', 'In your body language, when you lean toward harmony', 'In small talk, when you make others comfortable'],
    'Scorpio': ['In first meetings, when you observe before revealing', 'In groups, when you see the dynamics others miss', 'In your body language, when your eyes do the talking', 'In small talk, when you go deep fast'],
    'Sagittarius': ['In first meetings, when you bring enthusiasm', 'In groups, when you expand the energy', 'In your body language, when you lean forward with interest', 'In small talk, when you turn it philosophical'],
    'Capricorn': ['In first meetings, when you assess the situation', 'In groups, when you naturally command respect', 'In your body language, when you carry authority', 'In small talk, when you prefer meaningful exchange'],
    'Aquarius': ['In first meetings, when you come across as different', 'In groups, when you stand slightly outside', 'In your body language, when you seem a step removed', 'In small talk, when you\'d rather discuss ideas'],
    'Pisces': ['In first meetings, when you absorb the atmosphere', 'In groups, when you blend with the collective', 'In your body language, when your edges seem soft', 'In small talk, when you drift into imagination']
  };
  
  const practicalShiftMap: { [key: string]: string } = {
    'Aries': 'Let someone else lead the conversation for five minutes.',
    'Taurus': 'Speed up your response time by one beat.',
    'Gemini': 'Let a silence exist without filling it.',
    'Cancer': 'Share something real before you feel safe.',
    'Leo': 'Ask about them before sharing about yourself.',
    'Virgo': 'Give a compliment instead of a suggestion.',
    'Libra': 'State an opinion before asking for theirs.',
    'Scorpio': 'Share something personal earlier than feels comfortable.',
    'Sagittarius': 'Listen fully without planning your next point.',
    'Capricorn': 'Let yourself seem uncertain about something.',
    'Aquarius': 'Find one thing you genuinely have in common.',
    'Pisces': 'Be concrete about one thing you want.'
  };
  
  const reflectionMap: { [key: string]: string } = {
    'Aries': 'How does being first make you feel safe?',
    'Taurus': 'What would happen if you responded faster?',
    'Gemini': 'What are you avoiding by keeping things light?',
    'Cancer': 'What would you show if you weren\'t protecting yourself?',
    'Leo': 'What happens when you\'re not the center of attention?',
    'Virgo': 'When did helping become your way of hiding?',
    'Libra': 'Who are you when you\'re not adapting to them?',
    'Scorpio': 'What are you protecting by staying mysterious?',
    'Sagittarius': 'What depth are you escaping by staying expansive?',
    'Capricorn': 'When did competence become your shield?',
    'Aquarius': 'What are you afraid of in connection?',
    'Pisces': 'Where did your edges go?'
  };
  
  return {
    identity: identityMap[sign] || `You appear to the world with ${sign} qualities.`,
    tension: tensionMap[sign] || `This first impression can sometimes mislead.`,
    genius: geniusMap[sign] || `When this is working, your ${sign} presence opens doors.`,
    whereItShowsUp: whereItShowsUpMap[sign] || ['In first impressions and new situations'],
    practicalShift: practicalShiftMap[sign] || 'Adjust how you enter your next interaction.',
    reflection: reflectionMap[sign] || `What mask does ${sign} create for you?`
  };
};

const generateMercuryMirrorLayer = (sign: string): MirrorLayer => ({
  identity: `You are someone whose mind works through ${SIGN_QUALITIES[sign]?.[0] || sign} patterns. Information enters, processes, and exits in a distinctly ${sign} way.`,
  tension: getMercuryTension(sign).replace('Can be', 'This can turn into being').replace(/\.$/, ' when you\'re stressed or defensive.'),
  genius: `When this is working, ${getMercuryGift(sign).toLowerCase()} You think in ways others can\'t replicate.`,
  whereItShowsUp: [
    `In arguments, when your ${SIGN_QUALITIES[sign]?.[0] || 'particular'} style takes over`,
    `In learning, when ${getMercuryLearningStyle(sign)} is the only way that sticks`,
    `In decisions, when your mind ${sign === 'Gemini' ? 'sees too many options' : sign === 'Virgo' ? 'analyzes endlessly' : sign === 'Scorpio' ? 'digs for hidden motives' : 'processes in its characteristic way'}`,
    `In conversations, when you ${sign === 'Aries' ? 'interrupt' : sign === 'Taurus' ? 'take time to respond' : sign === 'Gemini' ? 'jump topics' : 'show your mental signature'}`
  ],
  practicalShift: sign === 'Aries' ? 'Count to three before responding.' : 
                  sign === 'Taurus' ? 'Update one opinion you\'ve held too long.' :
                  sign === 'Gemini' ? 'Finish one thought completely before starting another.' :
                  sign === 'Cancer' ? 'State your point before sharing how it makes you feel.' :
                  sign === 'Leo' ? 'Ask their opinion before sharing yours.' :
                  sign === 'Virgo' ? 'Accept "good enough" on one thing today.' :
                  sign === 'Libra' ? 'Make one decision without consulting anyone.' :
                  sign === 'Scorpio' ? 'Say what you mean directly, without subtext.' :
                  sign === 'Sagittarius' ? 'Follow through on one thing you promised.' :
                  sign === 'Capricorn' ? 'Entertain an impractical idea fully.' :
                  sign === 'Aquarius' ? 'Explain something the conventional way, just once.' :
                  'Trust one intuition without explaining it.',
  reflection: sign === 'Aries' ? 'What have you missed by thinking too fast?' :
              sign === 'Taurus' ? 'What idea are you holding that should have evolved?' :
              sign === 'Gemini' ? 'What would you know if you stopped gathering and started deciding?' :
              sign === 'Cancer' ? 'When does your emotional intelligence become emotional reasoning?' :
              sign === 'Leo' ? 'What would you think if it wasn\'t about you?' :
              sign === 'Virgo' ? 'When did analyzing become avoiding?' :
              sign === 'Libra' ? 'What would you argue for if you had to pick a side?' :
              sign === 'Scorpio' ? 'What are you investigating that you should just ask about?' :
              sign === 'Sagittarius' ? 'What truth are you avoiding by staying philosophical?' :
              sign === 'Capricorn' ? 'What thoughts do you dismiss because they\'re not useful?' :
              sign === 'Aquarius' ? 'What conventional wisdom have you rejected that might actually be right?' :
              'What message from your intuition are you not acting on?'
});

const generateVenusMirrorLayer = (sign: string): MirrorLayer => ({
  identity: `You are someone who loves and values through ${SIGN_QUALITIES[sign]?.[0] || sign} patterns. What feels beautiful, who feels attractive, how connection works—it\'s all ${sign}.`,
  tension: getVenusTension(sign).replace(/^Love can/, 'This can turn into love that'),
  genius: `When this is working, ${getVenusGift(sign).toLowerCase().replace(/\.$/, '')}—and it transforms everyone it touches.`,
  whereItShowsUp: [
    `In attraction, when you find yourself drawn to ${SIGN_QUALITIES[sign]?.[0] || 'particular'} qualities`,
    `In relationships, when you show love through ${getVenusLoveLanguage(sign)}`,
    `In conflict with partners, when ${sign === 'Aries' ? 'you compete' : sign === 'Taurus' ? 'you won\'t budge' : sign === 'Gemini' ? 'you deflect with words' : sign === 'Cancer' ? 'you retreat emotionally' : sign === 'Leo' ? 'your pride takes over' : 'your pattern emerges'}`,
    `In your aesthetic choices, when ${sign === 'Libra' ? 'balance matters more than anything' : sign === 'Taurus' ? 'quality trumps quantity' : sign === 'Leo' ? 'drama and warmth are required' : `${sign} values show through`}`
  ],
  practicalShift: sign === 'Aries' ? 'Let them take the lead in planning something.' :
                  sign === 'Taurus' ? 'Try something new with your partner.' :
                  sign === 'Gemini' ? 'Stay present through one entire conversation.' :
                  sign === 'Cancer' ? 'Ask for what you need instead of hinting.' :
                  sign === 'Leo' ? 'Celebrate them without making it about you.' :
                  sign === 'Virgo' ? 'Compliment without suggesting improvement.' :
                  sign === 'Libra' ? 'Express a preference, even if they disagree.' :
                  sign === 'Scorpio' ? 'Trust without testing them.' :
                  sign === 'Sagittarius' ? 'Stay instead of exploring something new.' :
                  sign === 'Capricorn' ? 'Be useless together. Call it connection.' :
                  sign === 'Aquarius' ? 'Get closer than is comfortable.' :
                  'Maintain one boundary you usually dissolve.',
  reflection: sign === 'Aries' ? 'When does pursuing become pushing away?' :
              sign === 'Taurus' ? 'What relationship pattern are you holding onto past its expiration?' :
              sign === 'Gemini' ? 'Who would you be to them if you stopped charming?' :
              sign === 'Cancer' ? 'Where does your nurturing become control?' :
              sign === 'Leo' ? 'Can you be loved without being admired?' :
              sign === 'Virgo' ? 'What if they didn\'t need to be fixed?' :
              sign === 'Libra' ? 'What do you want that isn\'t what they want?' :
              sign === 'Scorpio' ? 'What would you have to feel if you stopped controlling the depth?' :
              sign === 'Sagittarius' ? 'What intimacy are you avoiding by keeping things adventurous?' :
              sign === 'Capricorn' ? 'When did love become another achievement?' :
              sign === 'Aquarius' ? 'What would happen if you let yourself be ordinary in love?' :
              'Where do you end and your partner begin?'
});

const generateMarsMirrorLayer = (sign: string): MirrorLayer => ({
  identity: `You are someone who takes action through ${SIGN_QUALITIES[sign]?.[0] || sign} patterns. How you fight, pursue, and assert—it\'s unmistakably ${sign}.`,
  tension: getMarsTension(sign).replace(/^Can be/, 'This can turn into being'),
  genius: `When this is working, ${getMarsGift(sign).toLowerCase()} You move in ways others can\'t match.`,
  whereItShowsUp: [
    `In anger, when ${getMarsAngerStyle(sign)} takes over`,
    `In pursuit, when you ${sign === 'Aries' ? 'go straight for it' : sign === 'Scorpio' ? 'strategize before striking' : sign === 'Capricorn' ? 'play the long game' : 'show your action signature'}`,
    `In competition, when your ${SIGN_QUALITIES[sign]?.[0] || 'characteristic'} drive emerges`,
    `In conflict, when you ${sign === 'Libra' ? 'avoid until you can\'t' : sign === 'Cancer' ? 'defend what matters' : sign === 'Pisces' ? 'absorb instead of assert' : 'default to your fighting style'}`
  ],
  practicalShift: sign === 'Aries' ? 'Pause before acting on impulse today.' :
                  sign === 'Taurus' ? 'Move faster on something you\'ve been sitting on.' :
                  sign === 'Gemini' ? 'Pick one thing and pursue it completely.' :
                  sign === 'Cancer' ? 'Defend yourself, not just others.' :
                  sign === 'Leo' ? 'Take action without needing credit.' :
                  sign === 'Virgo' ? 'Act before the plan is perfect.' :
                  sign === 'Libra' ? 'Pick a side and fight for it.' :
                  sign === 'Scorpio' ? 'Be direct instead of strategic.' :
                  sign === 'Sagittarius' ? 'Finish what you started before starting new.' :
                  sign === 'Capricorn' ? 'Do something that has no career benefit.' :
                  sign === 'Aquarius' ? 'Join instead of rebel.' :
                  'Assert one need clearly.',
  reflection: sign === 'Aries' ? 'What have you destroyed by moving too fast?' :
              sign === 'Taurus' ? 'What are you not fighting for that you should be?' :
              sign === 'Gemini' ? 'What would you commit to if commitment wasn\'t scary?' :
              sign === 'Cancer' ? 'When did protecting become hiding?' :
              sign === 'Leo' ? 'What would you do if no one was watching?' :
              sign === 'Virgo' ? 'What would you create if it didn\'t have to be perfect?' :
              sign === 'Libra' ? 'What fight are you avoiding that needs to happen?' :
              sign === 'Scorpio' ? 'What would change if you stopped being strategic?' :
              sign === 'Sagittarius' ? 'What would you build if you stayed in one place?' :
              sign === 'Capricorn' ? 'What passion have you sacrificed for achievement?' :
              sign === 'Aquarius' ? 'What would you fight for if it wasn\'t about being different?' :
              'What would you go after if you believed you deserved it?'
});

// ============================================
// DEEP DIVE CARD GENERATOR
// ============================================

const generateDeepDiveCards = (placements: CorePlacements, fullChartData: FullChartData | null): AstrologyDeepDiveCard[] => {
  const { sun, moon, ascendant, mercury, venus, mars } = placements;
  const { mercury_house, venus_house, mars_house, moon_house, sun_house } = placements;
  
  // Get qualities for each sign
  const sunQualities = SIGN_QUALITIES[sun] || ['distinctive', 'unique', 'particular'];
  const moonQualities = SIGN_QUALITIES[moon] || ['distinctive', 'unique', 'particular'];
  const ascQualities = SIGN_QUALITIES[ascendant] || ['distinctive', 'unique', 'particular'];
  const mercQualities = mercury ? SIGN_QUALITIES[mercury] || sunQualities : sunQualities;
  const venusQualities = venus ? SIGN_QUALITIES[venus] || moonQualities : moonQualities;
  const marsQualities = mars ? SIGN_QUALITIES[mars] || sunQualities : sunQualities;

  const cards: AstrologyDeepDiveCard[] = [
    {
      id: 'sun',
      title: 'Core Identity',
      subtitle: 'Who you are becoming',
      preview: `The ${sunQualities[0]} path you're here to walk. What lights you up when you stop pretending.`,
      whatThisIs: `Your Sun in ${sun}${sun_house ? ` in the ${sun_house}${getOrdinalSuffix(sun_house)} house` : ''} defines the life path you're here to grow into. This isn't who you already are—it's who you're becoming. There's a ${sunQualities[0]} quality to your essential self: ${sunQualities[1]}, ${sunQualities[2] || sunQualities[0]}.`,
      whatYouMightNotice: [
        `Feeling most yourself when expressing ${sunQualities[0]} qualities`,
        `A natural pull toward ${sunQualities[1]} approaches to life`,
        `Recognition when you meet your ${sunQualities[2] || sunQualities[0]} tendencies honestly`,
        sun_house ? `Life lessons concentrated in ${getHouseTheme(sun_house)} areas` : `A broad application of your core energy`
      ],
      tensionLabel: 'Shadow side',
      tension: getSunTension(sun),
      giftLabel: 'What you are here to express',
      gift: getSunGift(sun),
      reflection: `Where do you feel most alive? What lights you up when no one is watching?`
    },
    {
      id: 'moon',
      title: 'Emotional Core',
      subtitle: 'What you actually need',
      preview: `What settles you when nothing else does. The feeling-self underneath the thinking-self.`,
      whatThisIs: `Your Moon in ${moon}${moon_house ? ` in the ${moon_house}${getOrdinalSuffix(moon_house)} house` : ''} reveals your emotional nature—not what you show the world, but what you need to feel safe and nourished. There's a ${moonQualities[0]} quality to your emotional core, a need for ${getMoonNeed(moon)}.`,
      whatYouMightNotice: [
        `Craving ${moonQualities[0]} environments when stressed`,
        `Feeling nourished by ${moonQualities[1]} experiences`,
        `Emotional reactions that are distinctly ${moonQualities[2] || moonQualities[0]}`,
        moon_house ? `Emotional needs concentrated in ${getHouseTheme(moon_house)}` : `Emotional patterns across all life areas`
      ],
      tensionLabel: 'Emotional shadow',
      tension: getMoonTension(moon),
      giftLabel: 'Emotional gift',
      gift: getMoonGift(moon),
      reflection: `What do you need to feel emotionally safe? What calms you when nothing else does?`
    },
    {
      id: 'ascendant',
      title: 'First Impression',
      subtitle: 'The you people first meet',
      preview: `Your first move in any new room. The costume you didn't know you were wearing.`,
      whatThisIs: `There's a ${ascQualities[0]} quality to how you approach everything new—first meetings, fresh starts, unfamiliar territory. It's not who you are inside, but how you instinctively engage with the world.`,
      whatYouMightNotice: [
        `First impressions that come across as ${ascQualities[0]}`,
        `An instinctive ${ascQualities[1]} approach to new situations`,
        `Others often perceive you as ${ascQualities[2] || ascQualities[0]} initially`,
        `Your physical presence and style reflecting ${ascQualities[0]} energy`
      ],
      tensionLabel: 'The mask',
      tension: getAscTension(ascendant),
      giftLabel: 'What opens doors',
      gift: getAscGift(ascendant),
      reflection: `How do you typically enter a room of strangers? What energy do you project before people know you?`
    },
    {
      id: 'mercury',
      title: 'Mind & Communication',
      subtitle: 'How you naturally think',
      preview: `What your mind does when you're not steering it. The way you make sense of things.`,
      whatThisIs: `Your mind has a ${mercQualities[0]} quality—how you sort information, what kind of thinking comes easily, and how you express what you know. ${mercury_house ? `Mental energy naturally gravitates toward ${getHouseTheme(mercury_house)}.` : ''}`,
      whatYouMightNotice: [
        `A ${mercQualities[0]} quality to how you think and process`,
        `Learning that works best through ${getMercuryLearningStyle(mercury || sun)} methods`,
        `Communication that tends to be ${mercQualities[1]}—even when you try otherwise`,
        mercury_house ? `Mental focus naturally gravitating toward ${getHouseTheme(mercury_house)} topics` : `Broad intellectual interests without a single focus`
      ],
      tensionLabel: 'Where the mind gets stuck',
      tension: getMercuryTension(mercury || sun),
      giftLabel: 'Your cognitive edge',
      gift: getMercuryGift(mercury || sun),
      reflection: `How do you process new information? What conditions help you think most clearly?`
    },
    {
      id: 'venus',
      title: 'Love & Relating',
      subtitle: 'What you genuinely value',
      preview: `How you love when you stop trying to love correctly. What you find beautiful without deciding to.`,
      whatThisIs: `There's a ${venusQualities[0]} quality to what you find beautiful, how you attract and are attracted, and what you value in love and friendship. ${venus_house ? `Connection and aesthetics play out most intensely through ${getHouseTheme(venus_house)}.` : ''}`,
      whatYouMightNotice: [
        `Attraction to ${venusQualities[0]} people, places, and experiences`,
        `Showing love through ${getVenusLoveLanguage(venus || moon)}—sometimes before you realize it`,
        `Valuing ${venusQualities[2] || venusQualities[1]} qualities in relationships`,
        venus_house ? `Relationship themes concentrated in ${getHouseTheme(venus_house)} areas` : `A general approach to relating across contexts`
      ],
      tensionLabel: 'Relational blind spot',
      tension: getVenusTension(venus || moon),
      giftLabel: 'Gift in connection',
      gift: getVenusGift(venus || moon),
      reflection: `What do you find genuinely beautiful? How do you show someone they matter to you?`
    },
    {
      id: 'mars',
      title: 'Drive & Friction',
      subtitle: 'How you take action',
      preview: `What wakes you up. What makes you dangerous. How you move when you stop thinking.`,
      whatThisIs: `You have a ${marsQualities[0]} way of taking action—how you go after what you want, what ignites your drive, and how you handle conflict and desire. ${mars_house ? `This assertive energy concentrates in ${getHouseTheme(mars_house)}—where you push hardest and clash most easily.` : ''}`,
      whatYouMightNotice: [
        `A ${marsQualities[0]} style when you take action or initiate`,
        `Anger that tends to express as ${getMarsAngerStyle(mars || sun)}`,
        `Motivation strongest when pursuing ${marsQualities[2] || marsQualities[1]} goals`,
        mars_house ? `Drive and friction concentrated in ${getHouseTheme(mars_house)} areas` : `General assertive energy across contexts`
      ],
      tensionLabel: 'Where you clash',
      tension: getMarsTension(mars || sun),
      giftLabel: 'Your power',
      gift: getMarsGift(mars || sun),
      reflection: `What makes you want to fight for something? How do you handle frustration?`
    },
  ];

  return cards;
};

// Helper for ordinal suffixes
const getOrdinalSuffix = (n: number): string => {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
};

// ============================================
// CARD GROUPS
// ============================================

const CARD_GROUPS = [
  { id: 'core', label: 'CORE SELF', cards: ['sun', 'moon', 'ascendant'] },
  { id: 'mind', label: 'MIND & COMMUNICATION', cards: ['mercury'] },
  { id: 'relating', label: 'RELATING & ACTION', cards: ['venus', 'mars'] },
  { id: 'structure', label: 'STRUCTURE & INTEGRATION', cards: ['pressure'] },
];

// ============================================
// MAIN COMPONENT
// ============================================

const AstrologyDeepDiveTab: React.FC<AstrologyDeepDiveTabProps> = ({
  placements,
  fullChartData,
  expandedCards,
  toggleCard,
  onReflect,
  onJournal,
  onAskMirror,
  theme,
}) => {
  const cards = generateDeepDiveCards(placements, fullChartData);
  
  // Build pressure pattern analysis
  const patternAnalysis = buildAspectPatternAnalysis(fullChartData);
  const howPressureBuilds = patternAnalysis.howPressureBuilds;
  
  // Create a pressure card if there's a significant pattern
  const pressureCard: AstrologyDeepDiveCard | null = howPressureBuilds.hasSignificantPattern ? {
    id: 'pressure',
    title: 'How This Chart Builds Pressure',
    subtitle: 'The shape of tension in your psychology',
    preview: 'What keeps tightening, where it collects, and what it asks of you.',
    whatThisIs: howPressureBuilds.mainStatement,
    whatYouMightNotice: [
      howPressureBuilds.whatKeepsTightening,
      howPressureBuilds.whereItCollects,
      howPressureBuilds.howItTriesToResolve,
    ].filter(Boolean),
    tensionLabel: 'What keeps tightening',
    tension: howPressureBuilds.whatKeepsTightening,
    giftLabel: 'The gift inside the pressure',
    gift: howPressureBuilds.giftInsideThePressure,
    reflection: howPressureBuilds.reflectionQuestion
  } : null;
  
  // Create a map for quick card lookup
  const cardMap = new Map(cards.map(c => [c.id, c]));
  if (pressureCard) {
    cardMap.set('pressure', pressureCard);
  }

  // Function to get mirror layer for a card
  const getMirrorLayer = (cardId: string): MirrorLayer | null => {
    switch (cardId) {
      case 'sun':
        return generateSunMirrorLayer(placements.sun, placements.sun_house);
      case 'moon':
        return generateMoonMirrorLayer(placements.moon, placements.moon_house);
      case 'ascendant':
        return generateAscendantMirrorLayer(placements.ascendant);
      case 'mercury':
        return generateMercuryMirrorLayer(placements.mercury || placements.sun);
      case 'venus':
        return generateVenusMirrorLayer(placements.venus || placements.moon);
      case 'mars':
        return generateMarsMirrorLayer(placements.mars || placements.sun);
      default:
        return null;
    }
  };

  // Build the unified pattern with defensive handling
  const lifeChapterAnalysis = buildLifeChapterAnalysis(fullChartData);
  let dominantTruth = null;
  let unifiedPattern: UnifiedPattern | null = null;
  
  try {
    dominantTruth = getDominantTruth(fullChartData, lifeChapterAnalysis, patternAnalysis, 'today');
    unifiedPattern = getUnifiedPattern({
      chartData: fullChartData,
      placements,
      dominantTruth,
      aspectPatterns: patternAnalysis,
      lifeChapter: lifeChapterAnalysis
    });
  } catch (error) {
    console.warn('[AstrologyDeepDive] Could not build unified pattern:', error);
    // Continue rendering without unified pattern - graceful degradation
  }

  return (
    <View style={styles.deepDiveContainer}>
      {/* UNIFIED PATTERN BLOCK - Top of Deep Dive */}
      {unifiedPattern && (
        <View style={[styles.unifiedPatternBlock, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.unifiedPatternLabel, { color: theme.textTertiary }]}>
            THE PATTERN RUNNING THROUGH THIS CHART
          </Text>
          <Text style={[styles.unifiedPatternHeadline, { color: theme.text }]}>
            {unifiedPattern.headline}
          </Text>
          <Text style={[styles.unifiedPatternCore, { color: theme.textSecondary }]}>
            {unifiedPattern.corePattern}
          </Text>
          <View style={[styles.unifiedPatternTensionBox, { backgroundColor: theme.accent + '08' }]}>
            <Text style={[styles.unifiedPatternTension, { color: theme.text }]}>
              {unifiedPattern.tension}
            </Text>
          </View>
        </View>
      )}

      {CARD_GROUPS.map(group => {
        // Skip structure group if no pressure pattern
        if (group.id === 'structure' && !pressureCard) return null;
        
        return (
          <View key={group.id} style={styles.cardGroup}>
            <Text style={[styles.groupLabel, { color: theme.textTertiary }]}>{group.label}</Text>
            
            {group.cards.map(cardId => {
              const card = cardMap.get(cardId);
              if (!card) return null;
              
              const isExpanded = expandedCards.has(card.id);
              const mirrorLayer = getMirrorLayer(cardId);
              // Add connector phrase from unified pattern to mirror layer
              if (mirrorLayer && unifiedPattern) {
                mirrorLayer.connectorPhrase = unifiedPattern.connectorPhrase;
              }
              const importanceLine = cardId !== 'pressure' ? getPlanetImportanceLine(
                card.id === 'sun' ? 'Sun' : 
                card.id === 'moon' ? 'Moon' : 
                card.id === 'ascendant' ? 'Ascendant' :
                card.id === 'mercury' ? 'Mercury' :
                card.id === 'venus' ? 'Venus' :
                card.id === 'mars' ? 'Mars' : '',
                fullChartData
              ) : '';
              
              // For pressure card, render the existing special version
              if (cardId === 'pressure') {
                return (
                  <TouchableOpacity
                    key={card.id}
                    style={[styles.deepDiveCard, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}
                    onPress={() => toggleCard(card.id)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.deepDiveCardHeader}>
                      <View style={styles.deepDiveCardTitleRow}>
                        <Text style={[styles.deepDiveCardTitle, { color: theme.text }]}>{card.title}</Text>
                        <Text style={[styles.deepDiveExpandIcon, { color: theme.textTertiary }]}>
                          {isExpanded ? '▴' : '▾'}
                        </Text>
                      </View>
                      <Text style={[styles.deepDiveCardSubtitle, { color: theme.textTertiary }]}>{card.subtitle}</Text>
                      {!isExpanded && (
                        <Text style={[styles.deepDiveCardPreview, { color: theme.textSecondary }]}>
                          {card.preview}
                        </Text>
                      )}
                    </View>
                    
                    {isExpanded && (
                      <View style={styles.deepDiveCardContent}>
                        {/* Pattern connector line */}
                        {unifiedPattern && (
                          <Text style={[styles.patternConnectorLine, { color: theme.accent }]}>
                            This is one part of how pressure builds and redirects in your chart.
                          </Text>
                        )}
                        
                        {/* The Pattern - Master Insight */}
                        <View style={styles.deepDiveSection}>
                          <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>MASTER INSIGHT</Text>
                          <Text style={[styles.masterInsightText, { color: theme.text }]}>{card.whatThisIs}</Text>
                          {howPressureBuilds.lifeAreaStatement && (
                            <Text style={[styles.masterInsightText, { color: theme.textSecondary, fontStyle: 'italic', marginTop: 8 }]}>
                              {howPressureBuilds.lifeAreaStatement}
                            </Text>
                          )}
                        </View>
                        
                        {/* Divider */}
                        <View style={[styles.sectionDivider, { backgroundColor: theme.border }]} />
                        
                        {/* What Keeps Tightening */}
                        <View style={styles.deepDiveSection}>
                          <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>TENSION</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text }]}>{howPressureBuilds.whatKeepsTightening}</Text>
                        </View>
                        
                        {/* Where It Collects */}
                        <View style={styles.deepDiveSection}>
                          <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>WHERE IT SHOWS UP</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text }]}>{howPressureBuilds.whereItCollects}</Text>
                        </View>
                        
                        {/* Gift */}
                        <View style={[styles.deepDiveSection, { backgroundColor: '#E8F5E910', padding: 12, borderRadius: 8 }]}>
                          <Text style={[styles.deepDiveSectionLabel, { color: '#5A8A62' }]}>GENIUS</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text }]}>{howPressureBuilds.giftInsideThePressure}</Text>
                        </View>
                        
                        {/* Divider */}
                        <View style={[styles.sectionDivider, { backgroundColor: theme.border }]} />
                        
                        {/* Practical Shift */}
                        <View style={[styles.practicalShiftSection, { backgroundColor: theme.accent + '08' }]}>
                          <Text style={[styles.practicalShiftLabel, { color: theme.accent }]}>PRACTICAL SHIFT</Text>
                          <Text style={[styles.practicalShiftText, { color: theme.text }]}>
                            {howPressureBuilds.howItTriesToResolve.split('.')[0] + '.'}
                          </Text>
                        </View>
                        
                        {/* Divider */}
                        <View style={[styles.sectionDivider, { backgroundColor: theme.border }]} />
                        
                        {/* Reflection Question */}
                        <View style={[styles.deepDiveReflection, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
                          <Text style={[styles.deepDiveReflectionLabel, { color: theme.accent }]}>REFLECTION</Text>
                          <Text style={[styles.deepDiveReflectionText, { color: theme.text }]}>
                            {howPressureBuilds.reflectionQuestion}
                          </Text>
                        </View>
                        
                        {/* Actions */}
                        <View style={styles.deepDiveActions}>
                          <TouchableOpacity
                            style={[styles.deepDiveActionButton, { backgroundColor: theme.accent + '10' }]}
                            onPress={() => onReflect(card)}
                          >
                            <Text style={[styles.deepDiveActionText, { color: theme.accent }]}>Reflect</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            style={[styles.deepDiveActionButton, { backgroundColor: theme.surfaceLight }]}
                            onPress={() => onJournal(card)}
                          >
                            <Text style={[styles.deepDiveActionText, { color: theme.textSecondary }]}>Journal</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            style={[styles.deepDiveActionButton, { backgroundColor: theme.accent, borderColor: theme.accent }]}
                            onPress={() => onAskMirror(card)}
                          >
                            <Text style={[styles.deepDiveActionText, { color: theme.background }]}>Ask Mirror</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
                    )}
                  </TouchableOpacity>
                );
              }
              
              // Render standard card with Mirror framework
              return (
                <TouchableOpacity
                  key={card.id}
                  style={[styles.deepDiveCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
                  onPress={() => toggleCard(card.id)}
                  activeOpacity={0.7}
                >
                  {/* Card Header */}
                  <View style={styles.deepDiveCardHeader}>
                    <View style={styles.deepDiveCardTitleRow}>
                      <Text style={[styles.deepDiveCardTitle, { color: theme.text }]}>{card.title}</Text>
                      <Text style={[styles.deepDiveExpandIcon, { color: theme.textTertiary }]}>
                        {isExpanded ? '▴' : '▾'}
                      </Text>
                    </View>
                    <Text style={[styles.deepDiveCardSubtitle, { color: theme.textTertiary }]}>{card.subtitle}</Text>
                    {!isExpanded && (
                      <Text style={[styles.deepDiveCardPreview, { color: theme.textSecondary }]}>
                        {card.preview}
                      </Text>
                    )}
                  </View>

                  {/* Card Content - Mirror Framework */}
                  {isExpanded && (
                    <View style={styles.deepDiveCardContent}>
                      {/* Pattern Connector Line - Links to Unified Pattern */}
                      {mirrorLayer?.connectorPhrase && (
                        <Text style={[styles.patternConnectorLine, { color: theme.accent }]}>
                          {mirrorLayer.connectorPhrase.charAt(0).toUpperCase() + mirrorLayer.connectorPhrase.slice(1)}.
                        </Text>
                      )}

                      {/* Planet Importance Line */}
                      {importanceLine && (
                        <View style={[styles.deepDiveSection, { marginBottom: 8 }]}>
                          <Text style={[styles.planetImportanceLine, { color: theme.accent }]}>
                            {importanceLine}
                          </Text>
                        </View>
                      )}

                      {/* MASTER INSIGHT - Preserved original rich content */}
                      <View style={styles.deepDiveSection}>
                        <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>MASTER INSIGHT</Text>
                        <Text style={[styles.masterInsightText, { color: theme.text }]}>{card.whatThisIs}</Text>
                      </View>

                      {/* Divider */}
                      <View style={[styles.sectionDivider, { backgroundColor: theme.border }]} />

                      {/* MIRROR LAYER - Behavioral translation */}
                      {mirrorLayer && (
                        <>
                          {/* IDENTITY */}
                          <View style={styles.deepDiveSection}>
                            <Text style={[styles.mirrorSectionLabel, { color: theme.text }]}>IDENTITY</Text>
                            <Text style={[styles.mirrorSectionText, { color: theme.textSecondary }]}>{mirrorLayer.identity}</Text>
                          </View>

                          {/* TENSION */}
                          <View style={[styles.deepDiveSection, { backgroundColor: '#FFEBEE10', padding: 12, borderRadius: 8 }]}>
                            <Text style={[styles.mirrorSectionLabel, { color: '#B71C1C' }]}>TENSION</Text>
                            <Text style={[styles.mirrorSectionText, { color: theme.text }]}>{mirrorLayer.tension}</Text>
                          </View>

                          {/* GENIUS */}
                          <View style={[styles.deepDiveSection, { backgroundColor: '#E8F5E910', padding: 12, borderRadius: 8 }]}>
                            <Text style={[styles.mirrorSectionLabel, { color: '#1B5E20' }]}>GENIUS</Text>
                            <Text style={[styles.mirrorSectionText, { color: theme.text }]}>{mirrorLayer.genius}</Text>
                          </View>

                          {/* WHERE THIS SHOWS UP */}
                          <View style={styles.deepDiveSection}>
                            <Text style={[styles.mirrorSectionLabel, { color: theme.text }]}>WHERE THIS SHOWS UP</Text>
                            {mirrorLayer.whereItShowsUp.map((item, i) => (
                              <Text key={i} style={[styles.whereItShowsUpItem, { color: theme.textSecondary }]}>
                                • {item}
                              </Text>
                            ))}
                          </View>

                          {/* Divider */}
                          <View style={[styles.sectionDivider, { backgroundColor: theme.border }]} />

                          {/* PRACTICAL SHIFT - Highlighted */}
                          <View style={[styles.practicalShiftSection, { backgroundColor: theme.accent + '08' }]}>
                            <Text style={[styles.practicalShiftLabel, { color: theme.accent }]}>PRACTICAL SHIFT</Text>
                            <Text style={[styles.practicalShiftText, { color: theme.text }]}>{mirrorLayer.practicalShift}</Text>
                          </View>

                          {/* Divider */}
                          <View style={[styles.sectionDivider, { backgroundColor: theme.border }]} />

                          {/* REFLECTION - Upgraded */}
                          <View style={[styles.deepDiveReflection, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
                            <Text style={[styles.deepDiveReflectionLabel, { color: theme.accent }]}>REFLECTION</Text>
                            <Text style={[styles.deepDiveReflectionText, { color: theme.text }]}>
                              {mirrorLayer.reflection}
                            </Text>
                          </View>
                        </>
                      )}

                      {/* Actions */}
                      <View style={styles.deepDiveActions}>
                        <TouchableOpacity
                          style={[styles.deepDiveActionButton, { borderColor: theme.border }]}
                          onPress={() => onReflect(card)}
                        >
                          <Text style={[styles.deepDiveActionText, { color: theme.textSecondary }]}>Reflect</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={[styles.deepDiveActionButton, { borderColor: theme.border }]}
                          onPress={() => onJournal(card)}
                        >
                          <Text style={[styles.deepDiveActionText, { color: theme.textSecondary }]}>Journal</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                          style={[styles.deepDiveActionButton, { backgroundColor: theme.accent, borderColor: theme.accent }]}
                          onPress={() => onAskMirror(card)}
                        >
                          <Text style={[styles.deepDiveActionText, { color: theme.background }]}>Ask Mirror</Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        );
      })}
    </View>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  deepDiveContainer: {
    padding: 16,
    gap: 16,
  },
  
  // Unified Pattern Block styles
  unifiedPatternBlock: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 20,
    marginBottom: 8,
  },
  unifiedPatternLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  unifiedPatternHeadline: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 24,
    marginBottom: 12,
  },
  unifiedPatternCore: {
    fontSize: 15,
    lineHeight: 23,
    marginBottom: 16,
  },
  unifiedPatternTensionBox: {
    padding: 14,
    borderRadius: 10,
  },
  unifiedPatternTension: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  
  // Pattern connector line (links cards to unified pattern)
  patternConnectorLine: {
    fontSize: 12,
    fontStyle: 'italic',
    fontWeight: '500',
    marginBottom: 4,
    paddingBottom: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(139, 92, 246, 0.2)',
  },
  
  cardGroup: {
    gap: 8,
  },
  groupLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  deepDiveCard: {
    borderRadius: 12,
    borderWidth: 1,
    overflow: 'hidden',
  },
  deepDiveCardHeader: {
    padding: 16,
  },
  deepDiveCardTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  deepDiveCardTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  deepDiveExpandIcon: {
    fontSize: 12,
  },
  deepDiveCardSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  deepDiveCardPreview: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 8,
    fontStyle: 'italic',
  },
  deepDiveCardContent: {
    padding: 16,
    paddingTop: 0,
    gap: 16,
  },
  deepDiveSection: {
    gap: 6,
  },
  deepDiveSectionLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  deepDiveSectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  
  // Master Insight styles
  masterInsightText: {
    fontSize: 15,
    lineHeight: 23,
    fontWeight: '400',
  },
  
  // Mirror Layer styles
  mirrorSectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 4,
  },
  mirrorSectionText: {
    fontSize: 14,
    lineHeight: 21,
  },
  whereItShowsUpItem: {
    fontSize: 13,
    lineHeight: 20,
    paddingLeft: 4,
    marginTop: 4,
  },
  
  // Practical Shift styles
  practicalShiftSection: {
    padding: 14,
    borderRadius: 10,
  },
  practicalShiftLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  practicalShiftText: {
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '500',
    fontStyle: 'italic',
  },
  
  // Divider
  sectionDivider: {
    height: 1,
    marginVertical: 4,
  },
  
  deepDiveNoticeBullet: {
    fontSize: 13,
    lineHeight: 20,
    paddingLeft: 4,
  },
  deepDiveTensionGiftRow: {
    flexDirection: 'row',
    gap: 8,
  },
  deepDiveTensionCard: {
    flex: 1,
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
  },
  deepDiveTensionLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  deepDiveTensionText: {
    fontSize: 12,
    lineHeight: 18,
  },
  deepDiveGiftCard: {
    flex: 1,
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
  },
  deepDiveGiftLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  deepDiveGiftText: {
    fontSize: 12,
    lineHeight: 18,
  },
  deepDiveReflection: {
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
  },
  deepDiveReflectionLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  deepDiveReflectionText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },
  deepDiveActions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  deepDiveActionButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  deepDiveActionText: {
    fontSize: 13,
    fontWeight: '500',
  },
  planetImportanceLine: {
    fontSize: 13,
    fontStyle: 'italic',
    fontWeight: '500',
    lineHeight: 20,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: 'rgba(139, 128, 99, 0.04)',
    borderRadius: 6,
    borderLeftWidth: 2,
    borderLeftColor: 'rgba(139, 128, 99, 0.3)',
  },
});

export default AstrologyDeepDiveTab;
