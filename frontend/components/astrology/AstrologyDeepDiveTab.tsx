// ============================================
// ASTROLOGY DEEP DIVE TAB
// Renders: Section groups, Deep Dive cards, expand/collapse, actions
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
    'Sagittarius': 'Love can resist commitment in pursuit of freedom.',
    'Capricorn': 'Love can become conditional on achievement.',
    'Aquarius': 'Love can be too detached, maintaining distance as safety.',
    'Pisces': 'Love can lose boundaries, sacrificing self for merger.'
  };
  return tensions[sign] || 'A relational pattern that needs awareness.';
};

const getVenusGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Passionate, direct love that doesn\'t play games.',
    'Taurus': 'Loyal, sensual love that creates lasting stability.',
    'Gemini': 'Curious, communicative love that keeps relating fresh.',
    'Cancer': 'Nurturing, devoted love that creates emotional home.',
    'Leo': 'Generous, warm love that makes partners feel special.',
    'Virgo': 'Attentive, devoted love shown through care.',
    'Libra': 'Graceful, harmonious love that creates true partnership.',
    'Scorpio': 'Deep, transformative love that demands authenticity.',
    'Sagittarius': 'Adventurous, generous love that expands both people.',
    'Capricorn': 'Committed, supportive love that builds over time.',
    'Aquarius': 'Accepting, freedom-giving love that respects individuality.',
    'Pisces': 'Compassionate, imaginative love that transcends the ordinary.'
  };
  return gifts[sign] || 'A distinctive relational capacity.';
};

const getMarsAngerStyle = (sign: string): string => {
  const styles: { [key: string]: string } = {
    'Aries': 'quick, direct, and usually over fast',
    'Taurus': 'slow-building but explosive when pushed too far',
    'Gemini': 'verbal, sharp, sometimes passive-aggressive',
    'Cancer': 'moody, indirect, sometimes through withdrawal',
    'Leo': 'dramatic, proud, needing acknowledgment',
    'Virgo': 'critical, nitpicking, sometimes self-directed',
    'Libra': 'passive-aggressive, conflict-avoiding',
    'Scorpio': 'intense, strategic, holding grudges',
    'Sagittarius': 'righteous, philosophical, then forgotten',
    'Capricorn': 'cold, controlled, expressed through authority',
    'Aquarius': 'detached, intellectual, sometimes erratic',
    'Pisces': 'indirect, victimized, or turned inward'
  };
  return styles[sign] || 'a distinctive pattern';
};

const getMarsTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Aggression can be impulsive, creating conflict unnecessarily.',
    'Taurus': 'Stubbornness can resist necessary change or confrontation.',
    'Gemini': 'Scattered energy can dilute the power of focused action.',
    'Cancer': 'Passive-aggression can undermine direct communication.',
    'Leo': 'Pride can make every conflict about ego rather than issues.',
    'Virgo': 'Perfectionism can create frustration with self and others.',
    'Libra': 'Conflict avoidance can let resentment build silently.',
    'Scorpio': 'Intensity can become controlling or manipulative.',
    'Sagittarius': 'Over-promise and under-deliver when enthusiasm fades.',
    'Capricorn': 'Ambition can override ethics or relationships.',
    'Aquarius': 'Detachment can make assertiveness feel cold.',
    'Pisces': 'Passive tendencies can prevent necessary self-assertion.'
  };
  return tensions[sign] || 'An action pattern that needs awareness.';
};

const getMarsGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Pure courage and the ability to begin what others hesitate on.',
    'Taurus': 'Unstoppable persistence once committed to a path.',
    'Gemini': 'Versatile energy that can adapt strategy mid-course.',
    'Cancer': 'Fierce protectiveness and emotional courage.',
    'Leo': 'Inspiring leadership and the courage of conviction.',
    'Virgo': 'Precise, effective action that improves everything it touches.',
    'Libra': 'The ability to fight fairly and for partnership.',
    'Scorpio': 'Transformative power and the courage to face darkness.',
    'Sagittarius': 'Enthusiastic energy that inspires collective action.',
    'Capricorn': 'Strategic, enduring effort that achieves long-term goals.',
    'Aquarius': 'The courage to be different and fight for ideals.',
    'Pisces': 'The strength to surrender and the power of non-resistance.'
  };
  return gifts[sign] || 'A distinctive action capacity.';
};

const getHouseOrdinal = (house: number): string => {
  const ordinals = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th', '11th', '12th'];
  return ordinals[house - 1] || `${house}th`;
};

// ============================================
// CARD GENERATION FUNCTION
// ============================================

const generateDeepDiveCards = (
  placements: CorePlacements,
  fullChartData: FullChartData | null
): AstrologyDeepDiveCard[] => {
  const {
    sun, moon, ascendant,
    sun_house, moon_house,
    mercury, mercury_house,
    venus, venus_house,
    mars, mars_house,
  } = placements;
  
  const sunQualities = SIGN_QUALITIES[sun] || ['distinctive', 'unique', 'particular'];
  const moonQualities = SIGN_QUALITIES[moon] || ['responsive', 'sensitive', 'intuitive'];
  const ascQualities = SIGN_QUALITIES[ascendant] || ['approachable', 'present', 'engaged'];
  const mercQualities = SIGN_QUALITIES[mercury || sun] || ['thoughtful', 'communicative', 'curious'];
  const venusQualities = SIGN_QUALITIES[venus || moon] || ['relational', 'aesthetic', 'harmonious'];
  const marsQualities = SIGN_QUALITIES[mars || sun] || ['driven', 'active', 'motivated'];

  const cards: AstrologyDeepDiveCard[] = [
    {
      id: 'sun',
      title: 'Core Identity',
      subtitle: 'Your essential nature',
      preview: `The part of you that doesn't change when everything else does. The thread that runs through all the versions.`,
      whatThisIs: `There's a ${sunQualities[0]} quality at the center of who you are. This isn't your whole identity—but it's the thread that runs through everything, the part that seeks expression and recognition. ${sun_house ? `This sense of self develops most through ${getHouseTheme(sun_house)}.` : ''}`,
      whatYouMightNotice: [
        `A ${sunQualities[0]} quality running through how you express yourself`,
        `Natural attraction toward ${sunQualities[2] || sunQualities[1]} activities and people`,
        `Feeling most yourself when you can be genuinely ${sunQualities[1]}`,
        sun_house ? `Identity themes playing out specifically through ${getHouseTheme(sun_house)}` : `This as your general life orientation`
      ],
      tensionLabel: 'The shadow side',
      tension: getSunTension(sun),
      giftLabel: 'What you are here to express',
      gift: getSunGift(sun),
      reflection: `When do you feel most like yourself? What conditions allow this ${sunQualities[0]} nature to come through naturally?`
    },
    {
      id: 'moon',
      title: 'Emotional Nature',
      subtitle: 'How you feel before you think',
      preview: `What you reach for when you want relief. The feeling you have before you've decided how to feel.`,
      whatThisIs: `Your emotional substrate has a ${moonQualities[0]} quality—what you need before you can think, what makes you feel safe, how you nurture and are nurtured. ${moon_house ? `Your inner life meets outer reality most intensely around ${getHouseTheme(moon_house)}.` : ''} This is the part of you that responds before you've decided how to respond.`,
      whatYouMightNotice: [
        `Emotional responses that feel ${moonQualities[0]}—before thought catches up`,
        `A need for ${getMoonNeed(moon)} to feel genuinely settled`,
        `Comfort patterns that involve ${moonQualities[2] || moonQualities[1]} activities`,
        moon_house ? `Emotional sensitivity concentrated around ${getHouseTheme(moon_house)} matters` : `This emotional coloring present everywhere`
      ],
      tensionLabel: 'What tightens emotionally',
      tension: getMoonTension(moon),
      giftLabel: 'The gift in how you feel',
      gift: getMoonGift(moon),
      reflection: `What do you reach for when you need comfort? What does "feeling safe" actually require?`
    },
    {
      id: 'ascendant',
      title: 'How You Meet Life',
      subtitle: 'Your instinctive approach to new situations',
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

  return (
    <View style={styles.deepDiveContainer}>
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
              const importanceLine = cardId !== 'pressure' ? getPlanetImportanceLine(
                card.id === 'sun' ? 'Sun' : 
                card.id === 'moon' ? 'Moon' : 
                card.id === 'ascendant' ? 'Ascendant' :
                card.id === 'mercury' ? 'Mercury' :
                card.id === 'venus' ? 'Venus' :
                card.id === 'mars' ? 'Mars' : '',
                fullChartData
              ) : '';
              
              // For pressure card, render a special version
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
                        {/* What This Is */}
                        <View style={styles.deepDiveSection}>
                          <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>THE PATTERN</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text }]}>{card.whatThisIs}</Text>
                          {howPressureBuilds.lifeAreaStatement && (
                            <Text style={[styles.deepDiveSectionText, { color: theme.textSecondary, fontStyle: 'italic', marginTop: 8 }]}>
                              {howPressureBuilds.lifeAreaStatement}
                            </Text>
                          )}
                        </View>
                        
                        {/* What Keeps Tightening */}
                        <View style={styles.deepDiveSection}>
                          <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>WHAT KEEPS TIGHTENING</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text }]}>{howPressureBuilds.whatKeepsTightening}</Text>
                        </View>
                        
                        {/* Where It Collects */}
                        <View style={styles.deepDiveSection}>
                          <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>WHERE IT COLLECTS</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text }]}>{howPressureBuilds.whereItCollects}</Text>
                        </View>
                        
                        {/* How It Tries to Resolve */}
                        <View style={styles.deepDiveSection}>
                          <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>HOW IT TRIES TO RESOLVE</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text }]}>{howPressureBuilds.howItTriesToResolve}</Text>
                        </View>
                        
                        {/* Gift */}
                        <View style={[styles.deepDiveSection, { backgroundColor: '#E8F5E910', padding: 12, borderRadius: 8 }]}>
                          <Text style={[styles.deepDiveSectionLabel, { color: '#5A8A62' }]}>THE GIFT INSIDE THE PRESSURE</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text }]}>{howPressureBuilds.giftInsideThePressure}</Text>
                        </View>
                        
                        {/* Reflection Question */}
                        <View style={[styles.deepDiveSection, { backgroundColor: theme.accent + '08', padding: 12, borderRadius: 8 }]}>
                          <Text style={[styles.deepDiveSectionLabel, { color: theme.accent }]}>A QUESTION TO SIT WITH</Text>
                          <Text style={[styles.deepDiveSectionText, { color: theme.text, fontStyle: 'italic' }]}>
                            {howPressureBuilds.reflectionQuestion}
                          </Text>
                        </View>
                        
                        {/* Actions */}
                        <View style={styles.deepDiveActions}>
                          <TouchableOpacity
                            style={[styles.deepDiveActionButton, { backgroundColor: theme.accent + '10' }]}
                            onPress={() => onReflect(card)}
                          >
                            <Text style={[styles.deepDiveActionText, { color: theme.accent }]}>Reflect on this</Text>
                          </TouchableOpacity>
                          <TouchableOpacity
                            style={[styles.deepDiveActionButton, { backgroundColor: theme.surfaceLight }]}
                            onPress={() => onJournal(card)}
                          >
                            <Text style={[styles.deepDiveActionText, { color: theme.textSecondary }]}>Journal</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
                    )}
                  </TouchableOpacity>
                );
              }
              
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

                  {/* Card Content */}
                  {isExpanded && (
                    <View style={styles.deepDiveCardContent}>
                      {/* Planet Importance Line */}
                      {importanceLine && (
                        <View style={[styles.deepDiveSection, { marginBottom: 8 }]}>
                          <Text style={[styles.planetImportanceLine, { color: theme.accent }]}>
                            {importanceLine}
                          </Text>
                        </View>
                      )}

                      {/* What this is */}
                      <View style={styles.deepDiveSection}>
                        <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>WHAT THIS IS</Text>
                        <Text style={[styles.deepDiveSectionText, { color: theme.textSecondary }]}>{card.whatThisIs}</Text>
                      </View>

                      {/* What you might notice */}
                      <View style={styles.deepDiveSection}>
                        <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>WHAT YOU MIGHT NOTICE</Text>
                        {card.whatYouMightNotice.map((item, i) => (
                          <Text key={i} style={[styles.deepDiveNoticeBullet, { color: theme.textSecondary }]}>
                            • {item}
                          </Text>
                        ))}
                      </View>

                      {/* Tension & Gift */}
                      <View style={styles.deepDiveTensionGiftRow}>
                        <View style={[styles.deepDiveTensionCard, { backgroundColor: '#FFEBEE', borderColor: '#FFCDD2' }]}>
                          <Text style={[styles.deepDiveTensionLabel, { color: '#B71C1C' }]}>{card.tensionLabel.toUpperCase()}</Text>
                          <Text style={[styles.deepDiveTensionText, { color: '#6B3333' }]}>{card.tension}</Text>
                        </View>
                        <View style={[styles.deepDiveGiftCard, { backgroundColor: '#E8F5E9', borderColor: '#C8E6C9' }]}>
                          <Text style={[styles.deepDiveGiftLabel, { color: '#1B5E20' }]}>{card.giftLabel.toUpperCase()}</Text>
                          <Text style={[styles.deepDiveGiftText, { color: '#2E5932' }]}>{card.gift}</Text>
                        </View>
                      </View>

                      {/* Reflection */}
                      <View style={[styles.deepDiveReflection, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
                        <Text style={[styles.deepDiveReflectionLabel, { color: theme.accent }]}>REFLECTION</Text>
                        <Text style={[styles.deepDiveReflectionText, { color: theme.text }]}>{card.reflection}</Text>
                      </View>

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
