import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { useRouter } from 'expo-router';

// ============================================
// TYPES
// ============================================

interface AstrologySection {
  label: string;
  body: string;
}

interface ChartStructure {
  dominant_element?: string;
  dominant_modality?: string;
  strongest_houses?: number[];
  stellium?: { sign: string; planets: string[] } | null;
  chart_shape?: string;
}

interface CorePlacements {
  sun: string;
  sun_house?: number;
  moon: string;
  moon_house?: number;
  ascendant: string;
  mercury?: string;
  mercury_house?: number;
  venus?: string;
  venus_house?: number;
  mars?: string;
  mars_house?: number;
}

interface AstrologyDeepDiveCard {
  id: string;
  title: string;
  subtitle: string;
  preview: string;
  whatThisIs: string;
  whatYouMightNotice: string[];
  tensionLabel: string;
  tension: string;
  giftLabel: string;
  gift: string;
  reflection: string;
}

interface AstrologySummaryData {
  title?: string;
  sections?: AstrologySection[];
  mirror_prompt?: string;
  core_placements?: CorePlacements;
  success?: boolean;
  error?: string;
  message?: string;
}

// ============================================
// SIGN DATA - Deterministic content
// ============================================

const SIGN_ELEMENTS: { [key: string]: string } = {
  'Aries': 'Fire', 'Leo': 'Fire', 'Sagittarius': 'Fire',
  'Taurus': 'Earth', 'Virgo': 'Earth', 'Capricorn': 'Earth',
  'Gemini': 'Air', 'Libra': 'Air', 'Aquarius': 'Air',
  'Cancer': 'Water', 'Scorpio': 'Water', 'Pisces': 'Water'
};

const SIGN_MODALITIES: { [key: string]: string } = {
  'Aries': 'Cardinal', 'Cancer': 'Cardinal', 'Libra': 'Cardinal', 'Capricorn': 'Cardinal',
  'Taurus': 'Fixed', 'Leo': 'Fixed', 'Scorpio': 'Fixed', 'Aquarius': 'Fixed',
  'Gemini': 'Mutable', 'Virgo': 'Mutable', 'Sagittarius': 'Mutable', 'Pisces': 'Mutable'
};

const SIGN_QUALITIES: { [key: string]: string[] } = {
  'Aries': ['initiating', 'direct', 'pioneering', 'independent'],
  'Taurus': ['grounded', 'sensual', 'steady', 'value-oriented'],
  'Gemini': ['curious', 'versatile', 'communicative', 'adaptable'],
  'Cancer': ['nurturing', 'protective', 'intuitive', 'emotionally attuned'],
  'Leo': ['expressive', 'warm', 'creative', 'generous'],
  'Virgo': ['analytical', 'service-oriented', 'precise', 'practical'],
  'Libra': ['relational', 'harmonizing', 'aesthetic', 'diplomatic'],
  'Scorpio': ['intense', 'penetrating', 'transformative', 'resourceful'],
  'Sagittarius': ['expansive', 'truth-seeking', 'adventurous', 'philosophical'],
  'Capricorn': ['structured', 'ambitious', 'responsible', 'enduring'],
  'Aquarius': ['innovative', 'humanitarian', 'independent', 'visionary'],
  'Pisces': ['imaginative', 'empathic', 'fluid', 'transcendent']
};

// ============================================
// SYNTHESIS HELPERS
// ============================================

const getSynthesis = (sun: string, moon: string, asc: string): string => {
  const sunQualities = SIGN_QUALITIES[sun] || [];
  const moonQualities = SIGN_QUALITIES[moon] || [];
  const ascQualities = SIGN_QUALITIES[asc] || [];
  
  const sunElement = SIGN_ELEMENTS[sun] || 'Unknown';
  const moonElement = SIGN_ELEMENTS[moon] || 'Unknown';
  
  // Create a unique synthesis based on element combinations
  if (sunElement === 'Water' && moonElement === 'Fire') {
    return `You carry depth and sensitivity at your core, but your emotional nature moves quickly and needs action. ${asc} rising means you meet life with ${ascQualities[0] || 'openness'} energy. This combination blends inner fluidity with outer motion.`;
  } else if (sunElement === 'Fire' && moonElement === 'Earth') {
    return `You have a bold, initiating core that's grounded by practical emotional needs. ${asc} rising gives you a ${ascQualities[0] || 'distinctive'} way of entering new situations. Vision meets stability in your chart.`;
  } else if (sunElement === 'Air' && moonElement === 'Water') {
    return `Your mind is quick and curious, but your emotional world runs deep and intuitive. ${asc} rising colors how others first experience you—${ascQualities[0] || 'uniquely'}. Thought and feeling weave together here.`;
  } else if (sunElement === 'Earth' && moonElement === 'Air') {
    return `You're practical and grounded at your core, but emotionally you need variety and mental stimulation. ${asc} rising brings ${ascQualities[0] || 'presence'} to how you meet the world. Stability and movement coexist.`;
  } else if (sunElement === moonElement) {
    return `Both your core identity and emotional nature share ${sunElement.toLowerCase()} energy—there's consistency between who you are and how you feel. ${asc} rising adds ${ascQualities[0] || 'dimension'} to how this expresses outwardly.`;
  }
  
  return `Your ${sun} Sun gives you a ${sunQualities[0] || 'distinctive'} core orientation, while your ${moon} Moon shapes how you process feeling—${moonQualities[0] || 'deeply'}. ${asc} rising means you approach life ${ascQualities[0] || 'openly'}. Together, these create your unique pattern.`;
};

const getThemeChips = (sun: string, moon: string, asc: string): string[] => {
  const chips: string[] = [];
  const sunQualities = SIGN_QUALITIES[sun] || [];
  const moonQualities = SIGN_QUALITIES[moon] || [];
  const ascQualities = SIGN_QUALITIES[asc] || [];
  
  // Add unique qualities from each placement
  if (sunQualities[0]) chips.push(sunQualities[0]);
  if (moonQualities[1] && !chips.includes(moonQualities[1])) chips.push(moonQualities[1]);
  if (ascQualities[0] && !chips.includes(ascQualities[0])) chips.push(ascQualities[0]);
  if (sunQualities[2] && !chips.includes(sunQualities[2])) chips.push(sunQualities[2]);
  if (moonQualities[0] && !chips.includes(moonQualities[0])) chips.push(moonQualities[0]);
  if (ascQualities[2] && !chips.includes(ascQualities[2])) chips.push(ascQualities[2]);
  
  return chips.slice(0, 6);
};

const getCoreTensions = (sun: string, moon: string, asc: string): string[] => {
  const tensions: string[] = [];
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  const sunModality = SIGN_MODALITIES[sun];
  const moonModality = SIGN_MODALITIES[moon];
  
  // Element-based tensions
  if (sunElement === 'Water' && moonElement === 'Fire') {
    tensions.push('sensitivity vs. impulsiveness');
  }
  if (sunElement === 'Air' && moonElement === 'Earth') {
    tensions.push('ideas vs. practicality');
  }
  if (sunElement === 'Fire' && moonElement === 'Water') {
    tensions.push('action vs. reflection');
  }
  if (sunElement === 'Earth' && moonElement === 'Air') {
    tensions.push('stability vs. restlessness');
  }
  
  // Modality-based tensions
  if (sunModality === 'Fixed' && moonModality === 'Mutable') {
    tensions.push('consistency vs. adaptability');
  }
  if (sunModality === 'Cardinal' && moonModality === 'Fixed') {
    tensions.push('initiating vs. maintaining');
  }
  
  // Sign-specific tensions
  if (sun === 'Pisces') tensions.push('boundaries vs. merging');
  if (moon === 'Aries') tensions.push('patience vs. immediacy');
  if (asc === 'Sagittarius') tensions.push('depth vs. breadth');
  if (asc === 'Scorpio') tensions.push('openness vs. privacy');
  
  return tensions.slice(0, 4);
};

const getCoreGifts = (sun: string, moon: string, asc: string): string[] => {
  const gifts: string[] = [];
  const sunElement = SIGN_ELEMENTS[sun];
  const moonElement = SIGN_ELEMENTS[moon];
  
  // Element-based gifts
  if (sunElement === 'Water') gifts.push('imaginative perception');
  if (sunElement === 'Fire') gifts.push('natural enthusiasm');
  if (sunElement === 'Earth') gifts.push('practical wisdom');
  if (sunElement === 'Air') gifts.push('mental agility');
  
  if (moonElement === 'Fire') gifts.push('emotional honesty');
  if (moonElement === 'Water') gifts.push('deep empathy');
  if (moonElement === 'Earth') gifts.push('emotional steadiness');
  if (moonElement === 'Air') gifts.push('emotional objectivity');
  
  // Asc-based gifts
  if (SIGN_QUALITIES[asc]) {
    const ascQuality = SIGN_QUALITIES[asc][3];
    if (ascQuality && !gifts.includes(ascQuality)) {
      gifts.push(ascQuality);
    }
  }
  
  // Unique combinations
  if (sun === 'Pisces' && moon === 'Aries') gifts.push('intuitive decisiveness');
  if (sun === 'Leo' && asc === 'Virgo') gifts.push('expressive precision');
  
  return gifts.slice(0, 4);
};

// ============================================
// DEEP DIVE CARD GENERATOR
// ============================================

const generateDeepDiveCards = (placements: CorePlacements): AstrologyDeepDiveCard[] => {
  const { sun, sun_house, moon, moon_house, ascendant, mercury, mercury_house, venus, venus_house, mars, mars_house } = placements;
  
  const sunQualities = SIGN_QUALITIES[sun] || ['distinctive'];
  const moonQualities = SIGN_QUALITIES[moon] || ['deep'];
  const ascQualities = SIGN_QUALITIES[ascendant] || ['open'];
  const mercQualities = SIGN_QUALITIES[mercury || sun] || ['quick'];
  const venusQualities = SIGN_QUALITIES[venus || moon] || ['receptive'];
  const marsQualities = SIGN_QUALITIES[mars || sun] || ['direct'];
  
  const cards: AstrologyDeepDiveCard[] = [
    {
      id: 'sun',
      title: 'Sun — Core Identity',
      subtitle: 'The essential tone of who you are.',
      preview: 'The core tone of your identity and orientation.',
      whatThisIs: `Your Sun in ${sun}${sun_house ? ` (House ${sun_house})` : ''} represents your essential self—the part of you that seeks expression and recognition. This isn't your whole identity, but it's the thread that runs through everything.`,
      whatYouMightNotice: [
        `a ${sunQualities[0]} quality to how you express yourself`,
        `natural draw toward ${sunQualities[2] || sunQualities[1]} activities`,
        `feeling most yourself when you can be ${sunQualities[1]}`,
        sun_house ? `this energy concentrated in ${getHouseTheme(sun_house)} areas of life` : `this as a general life orientation`
      ],
      tensionLabel: 'The shadow',
      tension: getSunTension(sun),
      giftLabel: 'Your genius',
      gift: getSunGift(sun),
      reflection: `When do you feel most like yourself? What conditions let your ${sunQualities[0]} nature shine?`
    },
    {
      id: 'moon',
      title: 'Moon — Emotional Nature',
      subtitle: 'How feelings move through you.',
      preview: 'How feelings move through you before thought catches up.',
      whatThisIs: `Your Moon in ${moon}${moon_house ? ` (House ${moon_house})` : ''} shapes your emotional instincts—what makes you feel safe, how you nurture yourself and others, and what you need when you're depleted.`,
      whatYouMightNotice: [
        `emotional responses that feel ${moonQualities[0]}`,
        `needing ${getMoonNeed(moon)} to feel emotionally settled`,
        `comfort patterns that involve ${moonQualities[2] || moonQualities[1]} activities`,
        moon_house ? `emotional sensitivity concentrated around ${getHouseTheme(moon_house)}` : `a general emotional coloring`
      ],
      tensionLabel: 'What tightens',
      tension: getMoonTension(moon),
      giftLabel: 'Hidden gift',
      gift: getMoonGift(moon),
      reflection: `What do you reach for when you need comfort? What does "feeling safe" actually mean to you?`
    },
    {
      id: 'ascendant',
      title: 'Ascendant — How You Meet Life',
      subtitle: 'Your instinctive approach to new situations.',
      preview: 'The way you naturally meet people, change, and new situations.',
      whatThisIs: `${ascendant} rising colors the lens through which you approach everything new—first meetings, fresh starts, unfamiliar territory. It's not who you are inside, but how you instinctively engage.`,
      whatYouMightNotice: [
        `first impressions that come across as ${ascQualities[0]}`,
        `an instinctive ${ascQualities[1]} approach to new situations`,
        `others often perceive you as ${ascQualities[2] || ascQualities[0]} initially`,
        `your physical presence and style reflecting ${ascQualities[0]} energy`
      ],
      tensionLabel: 'The mask',
      tension: getAscTension(ascendant),
      giftLabel: 'What opens doors',
      gift: getAscGift(ascendant),
      reflection: `How do you typically enter a room of strangers? What energy do you project before people know you?`
    },
    {
      id: 'mercury',
      title: 'Mercury — Mind & Communication',
      subtitle: 'How you think, learn, and express.',
      preview: 'How your mind sorts, connects, and communicates.',
      whatThisIs: `Mercury in ${mercury || sun}${mercury_house ? ` (House ${mercury_house})` : ''} shapes how your mind works—your thinking style, how you learn best, and how you communicate what you know.`,
      whatYouMightNotice: [
        `a ${mercQualities[0]} quality to your thinking`,
        `learning best through ${getMercuryLearningStyle(mercury || sun)} methods`,
        `communication that tends to be ${mercQualities[1]}`,
        mercury_house ? `mental focus often on ${getHouseTheme(mercury_house)} topics` : `broad intellectual interests`
      ],
      tensionLabel: 'Mental trap',
      tension: getMercuryTension(mercury || sun),
      giftLabel: 'Cognitive strength',
      gift: getMercuryGift(mercury || sun),
      reflection: `How do you process new information? What helps you think clearly?`
    },
    {
      id: 'venus',
      title: 'Venus — Love & Relating',
      subtitle: 'What draws you and softens you.',
      preview: 'What draws you, softens you, and matters in connection.',
      whatThisIs: `Venus in ${venus || moon}${venus_house ? ` (House ${venus_house})` : ''} reveals what you find beautiful, how you attract and relate, and what you value in love and friendship.`,
      whatYouMightNotice: [
        `attraction to ${venusQualities[0]} people or environments`,
        `showing love through ${getVenusLoveLanguage(venus || moon)}`,
        `valuing ${venusQualities[2] || venusQualities[1]} in relationships`,
        venus_house ? `relationship energy concentrated in ${getHouseTheme(venus_house)}` : `a general approach to relating`
      ],
      tensionLabel: 'Relational blind spot',
      tension: getVenusTension(venus || moon),
      giftLabel: 'Gift in connection',
      gift: getVenusGift(venus || moon),
      reflection: `What do you find genuinely beautiful? How do you show someone they matter to you?`
    },
    {
      id: 'mars',
      title: 'Mars — Drive & Friction',
      subtitle: 'How you assert and create friction.',
      preview: 'How you act, push, defend, and create friction.',
      whatThisIs: `Mars in ${mars || sun}${mars_house ? ` (House ${mars_house})` : ''} shows how you take action, what ignites your drive, and how you handle conflict and desire.`,
      whatYouMightNotice: [
        `a ${marsQualities[0]} style of taking action`,
        `anger that expresses as ${getMarsAngerStyle(mars || sun)}`,
        `motivation fueled by ${marsQualities[2] || marsQualities[1]} pursuits`,
        mars_house ? `drive concentrated in ${getHouseTheme(mars_house)} areas` : `general assertive energy`
      ],
      tensionLabel: 'Where you clash',
      tension: getMarsTension(mars || sun),
      giftLabel: 'Your power',
      gift: getMarsGift(mars || sun),
      reflection: `What makes you want to fight for something? How do you handle frustration?`
    },
    {
      id: 'houses',
      title: 'House Emphasis',
      subtitle: 'Where life concentrates most strongly.',
      preview: 'Where life concentrates most strongly in your chart.',
      whatThisIs: `The houses where your planets fall show where life's themes concentrate. ${sun_house ? `With Sun in House ${sun_house} and Moon in House ${moon_house || 'Unknown'}` : 'Your placements'}, certain areas of life naturally call more of your attention.`,
      whatYouMightNotice: [
        sun_house ? `identity themes playing out through ${getHouseTheme(sun_house)}` : `a broad identity expression`,
        moon_house ? `emotional needs tied to ${getHouseTheme(moon_house)}` : `emotional needs across many areas`,
        `repeated lessons in certain life domains`,
        `some areas of life feeling more "charged" than others`
      ],
      tensionLabel: 'Over-concentration',
      tension: `When too much energy flows to particular life areas, others may feel neglected. Balance across houses creates a fuller life experience.`,
      giftLabel: 'Natural focus',
      gift: `Your chart's concentration means you can develop real depth in specific areas. This isn't limitation—it's specialization.`,
      reflection: `Which areas of life demand the most from you? Which feel underdeveloped?`
    },
    {
      id: 'tensions',
      title: 'Core Chart Tensions',
      subtitle: 'The inner pulls that shape your experience.',
      preview: 'The inner pulls that shape your experience.',
      whatThisIs: `Every chart contains productive tensions—places where different parts of you want different things. These aren't flaws; they're the creative friction that makes you complex.`,
      whatYouMightNotice: [
        ...getCoreTensions(sun, moon, ascendant).map(t => `a pull between ${t}`),
        `these tensions showing up in decision-making`
      ],
      tensionLabel: 'The bind',
      tension: `When these tensions feel like problems to solve, you may flip between extremes. The work is integration, not resolution.`,
      giftLabel: 'Creative friction',
      gift: `These tensions create range and flexibility. You can access multiple modes because you contain multitudes.`,
      reflection: `Which inner contradiction feels most alive in you right now?`
    },
    {
      id: 'opens',
      title: 'What This Chart Opens',
      subtitle: 'What becomes possible as you grow.',
      preview: 'What becomes possible when the chart matures.',
      whatThisIs: `Your chart isn't a limitation—it's a specific kind of instrument. As you mature and integrate, certain capacities naturally develop from this particular configuration.`,
      whatYouMightNotice: [
        ...getCoreGifts(sun, moon, ascendant).map(g => `growing capacity for ${g}`),
        `earlier tensions becoming sources of wisdom`
      ],
      tensionLabel: 'What you\'re releasing',
      tension: `Growth asks you to release rigid identification with any single part of your chart. You are not your Sun sign—you're the whole pattern.`,
      giftLabel: 'What emerges',
      gift: `As you integrate all parts of this chart, you develop a unique form of wisdom that only this combination can produce.`,
      reflection: `What part of yourself are you just beginning to trust?`
    }
  ];
  
  return cards;
};

// Helper functions for card content
const getHouseTheme = (house: number): string => {
  const themes: { [key: number]: string } = {
    1: 'self and identity',
    2: 'resources and values',
    3: 'communication and learning',
    4: 'home and roots',
    5: 'creativity and pleasure',
    6: 'work and health',
    7: 'relationships and partnership',
    8: 'transformation and shared resources',
    9: 'beliefs and expansion',
    10: 'career and public role',
    11: 'community and future vision',
    12: 'spirituality and the unconscious'
  };
  return themes[house] || 'various life areas';
};

const getSunTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Impatience and self-centeredness when the pioneering spirit isn\'t channeled productively.',
    'Taurus': 'Stubbornness and resistance to change when comfort becomes more important than growth.',
    'Gemini': 'Superficiality and restlessness when curiosity scatters without depth.',
    'Cancer': 'Over-protectiveness and moodiness when security feels threatened.',
    'Leo': 'Pride and need for attention when self-expression becomes performance for approval.',
    'Virgo': 'Criticism and perfectionism when the desire to improve turns harsh.',
    'Libra': 'Indecision and people-pleasing when harmony-seeking avoids necessary conflict.',
    'Scorpio': 'Control and intensity when depth becomes obsession or manipulation.',
    'Sagittarius': 'Over-promising and restlessness when expansion lacks grounding.',
    'Capricorn': 'Rigidity and workaholism when ambition forgets life\'s other dimensions.',
    'Aquarius': 'Detachment and contrarianism when independence becomes isolation.',
    'Pisces': 'Escapism and boundary issues when sensitivity lacks containment.'
  };
  return tensions[sign] || 'Over-identification with one mode of expression.';
};

const getSunGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'The ability to initiate, to begin, to bring courage when others hesitate.',
    'Taurus': 'The capacity to build lasting value and bring steadiness to chaos.',
    'Gemini': 'Mental versatility and the gift of making connections others miss.',
    'Cancer': 'Emotional intelligence and the ability to create safety for others.',
    'Leo': 'Warmth and the capacity to bring joy and recognition to others.',
    'Virgo': 'Discernment and the ability to improve anything you touch.',
    'Libra': 'Grace in relationship and the gift of creating beauty and harmony.',
    'Scorpio': 'Depth of perception and the power to transform what others avoid.',
    'Sagittarius': 'Vision and the ability to inspire others toward meaning.',
    'Capricorn': 'Mastery and the capacity to build structures that endure.',
    'Aquarius': 'Original thinking and the gift of seeing future possibilities.',
    'Pisces': 'Imagination and the ability to access dimensions others can\'t perceive.'
  };
  return gifts[sign] || 'A unique orientation that only you can bring.';
};

const getMoonNeed = (sign: string): string => {
  const needs: { [key: string]: string } = {
    'Aries': 'action and independence',
    'Taurus': 'stability and sensory comfort',
    'Gemini': 'mental stimulation and variety',
    'Cancer': 'emotional security and belonging',
    'Leo': 'recognition and warmth',
    'Virgo': 'order and usefulness',
    'Libra': 'harmony and connection',
    'Scorpio': 'emotional depth and privacy',
    'Sagittarius': 'freedom and meaning',
    'Capricorn': 'structure and achievement',
    'Aquarius': 'space and intellectual engagement',
    'Pisces': 'transcendence and creative flow'
  };
  return needs[sign] || 'specific conditions';
};

const getMoonTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Emotional impulsiveness can create conflict before reflection catches up.',
    'Taurus': 'Emotional stubbornness can make it hard to adapt when circumstances change.',
    'Gemini': 'Emotional restlessness can prevent deep processing of difficult feelings.',
    'Cancer': 'Over-attachment to the past can limit present emotional availability.',
    'Leo': 'The need for appreciation can make emotional expression performative.',
    'Virgo': 'Self-criticism can interrupt the natural flow of feeling.',
    'Libra': 'The need for others\' approval can disconnect you from your own feelings.',
    'Scorpio': 'Emotional intensity can overwhelm both self and others.',
    'Sagittarius': 'The urge to find meaning can bypass necessary grief.',
    'Capricorn': 'Emotional control can create distance from vulnerability.',
    'Aquarius': 'Emotional detachment can feel like safety but create loneliness.',
    'Pisces': 'Emotional permeability can blur boundaries and absorb others\' feelings.'
  };
  return tensions[sign] || 'A particular emotional pattern that needs awareness.';
};

const getMoonGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Emotional honesty and the ability to take action from feeling.',
    'Taurus': 'Emotional steadiness that others can rely on.',
    'Gemini': 'Emotional flexibility and the ability to articulate feeling.',
    'Cancer': 'Deep empathy and the instinct to nurture and protect.',
    'Leo': 'Emotional generosity and the gift of making others feel seen.',
    'Virgo': 'Emotional precision and the ability to show love through care.',
    'Libra': 'Emotional grace and the capacity for true partnership.',
    'Scorpio': 'Emotional depth and the power to transform through feeling.',
    'Sagittarius': 'Emotional resilience and the ability to find hope.',
    'Capricorn': 'Emotional maturity and the capacity for responsibility.',
    'Aquarius': 'Emotional objectivity and the ability to hold space.',
    'Pisces': 'Emotional attunement and access to collective feeling.'
  };
  return gifts[sign] || 'A particular emotional capacity.';
};

const getAscTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'The mask can be too aggressive, intimidating others before they know you.',
    'Taurus': 'The mask can be too fixed, making you seem resistant to change.',
    'Gemini': 'The mask can be too scattered, making you seem unreliable.',
    'Cancer': 'The mask can be too protective, making connection feel risky.',
    'Leo': 'The mask can demand too much attention, overshadowing others.',
    'Virgo': 'The mask can be too critical, putting others on the defensive.',
    'Libra': 'The mask can be too accommodating, hiding your real preferences.',
    'Scorpio': 'The mask can be too intense, creating distance through intimidation.',
    'Sagittarius': 'The mask can promise more than you deliver, creating disappointment.',
    'Capricorn': 'The mask can be too serious, hiding your warmth.',
    'Aquarius': 'The mask can be too detached, making connection feel impossible.',
    'Pisces': 'The mask can be too diffuse, making it hard for others to find you.'
  };
  return tensions[sign] || 'The way you present can sometimes obscure who you really are.';
};

const getAscGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Your directness and courage make you a natural initiator.',
    'Taurus': 'Your steadiness makes others feel safe in your presence.',
    'Gemini': 'Your curiosity makes you instantly engaging and adaptable.',
    'Cancer': 'Your warmth makes others feel cared for immediately.',
    'Leo': 'Your presence lights up rooms and draws people in.',
    'Virgo': 'Your competence and helpfulness earn immediate respect.',
    'Libra': 'Your grace and charm create instant ease with others.',
    'Scorpio': 'Your depth and presence make interactions feel meaningful.',
    'Sagittarius': 'Your enthusiasm and openness invite adventure.',
    'Capricorn': 'Your seriousness and reliability inspire trust.',
    'Aquarius': 'Your uniqueness makes you memorable and intriguing.',
    'Pisces': 'Your gentleness and receptivity make others feel accepted.'
  };
  return gifts[sign] || 'A distinctive way of meeting the world.';
};

const getMercuryLearningStyle = (sign: string): string => {
  const styles: { [key: string]: string } = {
    'Aries': 'active, hands-on',
    'Taurus': 'slow, sensory',
    'Gemini': 'varied, conversational',
    'Cancer': 'emotional, story-based',
    'Leo': 'creative, demonstrative',
    'Virgo': 'systematic, detailed',
    'Libra': 'collaborative, aesthetic',
    'Scorpio': 'deep, investigative',
    'Sagittarius': 'conceptual, philosophical',
    'Capricorn': 'structured, practical',
    'Aquarius': 'innovative, unconventional',
    'Pisces': 'intuitive, imaginative'
  };
  return styles[sign] || 'distinctive';
};

const getMercuryTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Thinking can be too quick, missing nuance in pursuit of conclusions.',
    'Taurus': 'Thinking can be too slow, struggling to adapt to new information.',
    'Gemini': 'Thinking can scatter, pursuing many threads without synthesis.',
    'Cancer': 'Thinking can be colored by mood, losing objectivity.',
    'Leo': 'Thinking can serve ego, dismissing ideas that don\'t flatter.',
    'Virgo': 'Thinking can get lost in details, missing bigger patterns.',
    'Libra': 'Thinking can defer to others, losing your own perspective.',
    'Scorpio': 'Thinking can become obsessive, unable to let go.',
    'Sagittarius': 'Thinking can be too broad, lacking precision.',
    'Capricorn': 'Thinking can be too rigid, missing creative possibilities.',
    'Aquarius': 'Thinking can be too abstract, disconnecting from practical reality.',
    'Pisces': 'Thinking can be too impressionistic, lacking structure.'
  };
  return tensions[sign] || 'A cognitive pattern that needs awareness.';
};

const getMercuryGift = (sign: string): string => {
  const gifts: { [key: string]: string } = {
    'Aries': 'Quick, decisive thinking that cuts to the point.',
    'Taurus': 'Thorough, practical thinking that builds solid foundations.',
    'Gemini': 'Versatile thinking that makes surprising connections.',
    'Cancer': 'Intuitive thinking that senses what isn\'t said.',
    'Leo': 'Creative thinking that inspires and persuades.',
    'Virgo': 'Precise thinking that catches what others miss.',
    'Libra': 'Balanced thinking that sees multiple perspectives.',
    'Scorpio': 'Deep thinking that penetrates to root causes.',
    'Sagittarius': 'Big-picture thinking that finds meaning in patterns.',
    'Capricorn': 'Strategic thinking that plans for the long term.',
    'Aquarius': 'Original thinking that sees future possibilities.',
    'Pisces': 'Imaginative thinking that transcends ordinary categories.'
  };
  return gifts[sign] || 'A distinctive cognitive capacity.';
};

const getVenusLoveLanguage = (sign: string): string => {
  const languages: { [key: string]: string } = {
    'Aries': 'direct action and enthusiasm',
    'Taurus': 'physical presence and gifts',
    'Gemini': 'conversation and mental connection',
    'Cancer': 'nurturing and emotional attunement',
    'Leo': 'grand gestures and admiration',
    'Virgo': 'acts of service and attention to detail',
    'Libra': 'romantic partnership and aesthetic sharing',
    'Scorpio': 'deep emotional intensity and loyalty',
    'Sagittarius': 'shared adventures and philosophical connection',
    'Capricorn': 'commitment and practical support',
    'Aquarius': 'intellectual friendship and freedom',
    'Pisces': 'romantic transcendence and emotional merging'
  };
  return languages[sign] || 'distinctive expressions of care';
};

const getVenusTension = (sign: string): string => {
  const tensions: { [key: string]: string } = {
    'Aries': 'Love can be impatient, demanding excitement over depth.',
    'Taurus': 'Love can become possessive when security feels threatened.',
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

// ============================================
// INLINE REFLECT BUTTON COMPONENT
// ============================================

interface InlineReflectButtonProps {
  source: {
    lens: string;
    type: string;
    name: string;
    id: string;
  };
  prompt: string;
}

const InlineReflectButton: React.FC<InlineReflectButtonProps> = ({ source, prompt }) => {
  const { theme } = useTheme();
  const router = useRouter();

  const handlePress = () => {
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: `Reflecting on ${source.name}: ${prompt}`
      }
    });
  };

  return (
    <TouchableOpacity
      style={[styles.inlineReflectButton, { borderColor: theme.border }]}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <Text style={{ fontSize: 14, color: theme.textSecondary }}>Reflect →</Text>
    </TouchableOpacity>
  );
};

// ============================================
// MAIN COMPONENT
// ============================================

interface AstrologyLensViewProps {
  onOpenChat: () => void;
}

export default function AstrologyLensView({ onOpenChat }: AstrologyLensViewProps) {
  const { theme } = useTheme();
  const { user } = useAuth();
  const router = useRouter();
  const userId = user?.id;

  const [activeTab, setActiveTab] = useState<'at_a_glance' | 'today' | 'deep_dive'>('at_a_glance');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryData, setSummaryData] = useState<AstrologySummaryData | null>(null);
  const [deepDiveData, setDeepDiveData] = useState<any>(null);
  const [snapshotData, setSnapshotData] = useState<any>(null);
  const [activeAltitude, setActiveAltitude] = useState<'today' | 'week' | 'month'>('today');
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set(['sun']));

  useEffect(() => {
    if (userId) {
      loadTabData(activeTab);
    }
  }, [userId, activeTab]);

  const loadTabData = async (tab: string) => {
    if (!userId) return;
    setIsLoading(true);
    setError(null);

    try {
      if (tab === 'at_a_glance' || tab === 'summary') {
        const response = await api.get(`/astrology/summary/${userId}`);
        setSummaryData(response.data);
      } else if (tab === 'today') {
        try {
          const response = await api.get(`/astrology/snapshot/${userId}`);
          setSnapshotData(response.data);
        } catch {
          const response = await api.get(`/astrology/today/${userId}`);
          setSummaryData(response.data);
        }
      } else if (tab === 'deep_dive') {
        const response = await api.get(`/astrology/deep-dive/${userId}`);
        setDeepDiveData(response.data);
      }
    } catch (err: any) {
      console.error('Tab data error:', err);
      setError('Unable to load astrology data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCard = (cardId: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(cardId)) {
        newSet.delete(cardId);
      } else {
        newSet.add(cardId);
      }
      return newSet;
    });
  };

  // Action handlers
  const handleReflect = (card: AstrologyDeepDiveCard) => {
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: `I'd like to reflect on "${card.title}": ${card.reflection}`
      }
    });
  };

  const handleJournal = (card: AstrologyDeepDiveCard) => {
    const journalPrompt = `Reflecting on: ${card.title}\n\n"${card.reflection}"\n\nMy thoughts:\n`;
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'journal',
        prefill: journalPrompt
      }
    });
  };

  const handleAskMirror = (card: AstrologyDeepDiveCard) => {
    const mirrorContext = `I want to explore ${card.title.toLowerCase()} in my chart. ${card.whatThisIs}`;
    router.push({
      pathname: '/(tabs)/reflect',
      params: {
        tab: 'mirror',
        context: mirrorContext
      }
    });
  };

  // Get placements from available data
  const getPlacements = (): CorePlacements => {
    if (deepDiveData?.core_placements) {
      return deepDiveData.core_placements;
    }
    if (summaryData?.core_placements) {
      return summaryData.core_placements;
    }
    return {
      sun: 'Unknown',
      moon: 'Unknown',
      ascendant: 'Unknown'
    };
  };

  const placements = getPlacements();

  // ============================================
  // RENDER: TABS
  // ============================================
  const renderTabs = () => (
    <View style={[styles.tabContainer, { borderBottomColor: theme.border }]}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'at_a_glance' && styles.activeTab]}
        onPress={() => setActiveTab('at_a_glance')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'at_a_glance' && { color: theme.text }]}>
          At a Glance
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'today' && styles.activeTab]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'today' && { color: theme.text }]}>
          Today
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text }]}>
          Deep Dive
        </Text>
      </TouchableOpacity>
    </View>
  );

  // ============================================
  // RENDER: AT A GLANCE (Premium Summary)
  // ============================================
  const renderAtAGlance = () => {
    const sun = placements.sun || 'Unknown';
    const moon = placements.moon || 'Unknown';
    const asc = placements.ascendant || 'Unknown';
    
    if (sun === 'Unknown' && moon === 'Unknown' && asc === 'Unknown') {
      return (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
            Your chart data is still loading or incomplete.
          </Text>
        </View>
      );
    }

    const synthesis = getSynthesis(sun, moon, asc);
    const themeChips = getThemeChips(sun, moon, asc);
    const tensions = getCoreTensions(sun, moon, asc);
    const gifts = getCoreGifts(sun, moon, asc);

    return (
      <View style={styles.atAGlanceContainer}>
        {/* Big 3 Hero Strip */}
        <View style={[styles.big3Card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.big3Label, { color: theme.textTertiary }]}>SUN · MOON · ASCENDANT</Text>
          <View style={styles.big3Row}>
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>☉</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{sun}</Text>
            </View>
            <View style={[styles.big3Divider, { backgroundColor: theme.border }]} />
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>☽</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{moon}</Text>
            </View>
            <View style={[styles.big3Divider, { backgroundColor: theme.border }]} />
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>↑</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{asc}</Text>
            </View>
          </View>
        </View>

        {/* Core Synthesis */}
        <View style={[styles.synthesisCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.synthesisText, { color: theme.text }]}>{synthesis}</Text>
        </View>

        {/* Theme Chips */}
        <View style={styles.chipsContainer}>
          {themeChips.map((chip, i) => (
            <View key={i} style={[styles.chip, { backgroundColor: theme.accent + '15', borderColor: theme.accent + '30' }]}>
              <Text style={[styles.chipText, { color: theme.accent }]}>{chip}</Text>
            </View>
          ))}
        </View>

        {/* Structure Section */}
        <View style={[styles.structureCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.structureTitle, { color: theme.textSecondary }]}>STRUCTURE BEHIND YOUR CHART</Text>
          <View style={styles.structureGrid}>
            <View style={styles.structureItem}>
              <Text style={[styles.structureLabel, { color: theme.textTertiary }]}>Dominant Element</Text>
              <Text style={[styles.structureValue, { color: theme.text }]}>{SIGN_ELEMENTS[sun] || 'Mixed'}</Text>
            </View>
            <View style={styles.structureItem}>
              <Text style={[styles.structureLabel, { color: theme.textTertiary }]}>Sun Modality</Text>
              <Text style={[styles.structureValue, { color: theme.text }]}>{SIGN_MODALITIES[sun] || 'Mixed'}</Text>
            </View>
            <View style={styles.structureItem}>
              <Text style={[styles.structureLabel, { color: theme.textTertiary }]}>Moon Element</Text>
              <Text style={[styles.structureValue, { color: theme.text }]}>{SIGN_ELEMENTS[moon] || 'Unknown'}</Text>
            </View>
            <View style={styles.structureItem}>
              <Text style={[styles.structureLabel, { color: theme.textTertiary }]}>Rising Quality</Text>
              <Text style={[styles.structureValue, { color: theme.text }]}>{SIGN_MODALITIES[asc] || 'Unknown'}</Text>
            </View>
          </View>
        </View>

        {/* Core Tensions */}
        {tensions.length > 0 && (
          <View style={[styles.tensionsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.tensionsTitle, { color: '#E57373' }]}>CORE TENSIONS</Text>
            {tensions.map((t, i) => (
              <View key={i} style={styles.tensionItem}>
                <Text style={[styles.tensionBullet, { color: '#E57373' }]}>•</Text>
                <Text style={[styles.tensionText, { color: theme.textSecondary }]}>{t}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Core Gifts */}
        {gifts.length > 0 && (
          <View style={[styles.giftsCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.giftsTitle, { color: '#81C784' }]}>CORE GIFTS</Text>
            {gifts.map((g, i) => (
              <View key={i} style={styles.giftItem}>
                <Text style={[styles.giftBullet, { color: '#81C784' }]}>•</Text>
                <Text style={[styles.giftText, { color: theme.textSecondary }]}>{g}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Reflection Prompt */}
        <View style={[styles.reflectionCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
          <Text style={[styles.reflectionLabel, { color: theme.accent }]}>A QUESTION TO SIT WITH</Text>
          <Text style={[styles.reflectionText, { color: theme.text }]}>
            When you feel most like yourself, which of these qualities are present?
          </Text>
        </View>

        {/* Ask Mirror Button */}
        <TouchableOpacity
          style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
          onPress={onOpenChat}
        >
          <Text style={{ fontSize: 16, color: theme.background }}>💬</Text>
          <Text style={[styles.askMirrorText, { color: theme.background }]}>Ask about your chart</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // ============================================
  // RENDER: TODAY SNAPSHOT
  // ============================================
  const renderTodaySnapshot = () => {
    if (snapshotData) {
      const currentAltitude = snapshotData[activeAltitude];
      if (!currentAltitude) {
        return (
          <View style={styles.emptyState}>
            <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
              Today's snapshot is still forming...
            </Text>
          </View>
        );
      }

      return (
        <View style={styles.todayContainer}>
          {/* Altitude Selector */}
          <View style={[styles.altitudeSelector, { backgroundColor: theme.surfaceLight }]}>
            {['today', 'week', 'month'].map((alt) => (
              <TouchableOpacity
                key={alt}
                style={[
                  styles.altitudeTab,
                  activeAltitude === alt && [styles.altitudeTabActive, { backgroundColor: theme.surface }]
                ]}
                onPress={() => setActiveAltitude(alt as 'today' | 'week' | 'month')}
              >
                <Text style={[
                  styles.altitudeTabText,
                  { color: activeAltitude === alt ? theme.text : theme.textTertiary }
                ]}>
                  {alt === 'today' ? 'Today' : alt === 'week' ? 'This Week' : 'This Month'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Narrative */}
          <View style={[styles.narrativeCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Text style={[styles.narrativeText, { color: theme.text }]}>
              {currentAltitude.body}
            </Text>
            {currentAltitude.cause && activeAltitude === 'today' && (
              <Text style={[styles.causeText, { color: theme.textSecondary }]}>
                {currentAltitude.cause}
              </Text>
            )}
          </View>

          <InlineReflectButton
            source={{
              lens: 'astrology',
              type: `snapshot_${activeAltitude}`,
              name: currentAltitude.title || 'Today',
              id: `astrology_snapshot_${activeAltitude}`,
            }}
            prompt={`Reflect on today: ${currentAltitude.body?.slice(0, 150) || ''}...`}
          />
        </View>
      );
    }

    // Fallback
    return (
      <View style={styles.emptyState}>
        <Text style={[styles.emptyStateText, { color: theme.textSecondary }]}>
          Today's timing lens is still forming...
        </Text>
      </View>
    );
  };

  // ============================================
  // RENDER: DEEP DIVE CARDS
  // ============================================
  const renderDeepDive = () => {
    const cards = generateDeepDiveCards(placements);

    return (
      <View style={styles.deepDiveContainer}>
        {/* Header */}
        <View style={[styles.deepDiveHeader, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.big3Row}>
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>☉</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{placements.sun}</Text>
            </View>
            <View style={[styles.big3Divider, { backgroundColor: theme.border }]} />
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>☽</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{placements.moon}</Text>
            </View>
            <View style={[styles.big3Divider, { backgroundColor: theme.border }]} />
            <View style={styles.big3Item}>
              <Text style={[styles.big3Symbol, { color: theme.accent }]}>↑</Text>
              <Text style={[styles.big3Sign, { color: theme.text }]}>{placements.ascendant}</Text>
            </View>
          </View>
          <Text style={[styles.deepDiveNote, { color: theme.textTertiary }]}>
            Nine reflection cards exploring your chart structure.
          </Text>
        </View>

        {/* Cards */}
        {cards.map((card, index) => {
          const isExpanded = expandedCards.has(card.id);
          
          // Badge colors by card type
          const getBadgeColor = () => {
            switch (card.id) {
              case 'sun': return theme.accent;
              case 'moon': return '#B39DDB';
              case 'ascendant': return '#64B5F6';
              case 'mercury': return '#FFD54F';
              case 'venus': return '#F48FB1';
              case 'mars': return '#E57373';
              case 'houses': return '#81C784';
              case 'tensions': return '#FFB74D';
              case 'opens': return '#4DD0E1';
              default: return theme.accent;
            }
          };

          return (
            <View 
              key={card.id} 
              style={[styles.deepDiveCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
            >
              {/* Card Header */}
              <TouchableOpacity
                style={styles.deepDiveCardHeader}
                onPress={() => toggleCard(card.id)}
                activeOpacity={0.7}
              >
                <View style={styles.deepDiveCardHeaderContent}>
                  <View style={[styles.deepDiveCardNumber, { backgroundColor: getBadgeColor() + '15' }]}>
                    <Text style={[styles.deepDiveCardNumberText, { color: getBadgeColor() }]}>{index + 1}</Text>
                  </View>
                  <View style={styles.deepDiveCardTitleContainer}>
                    <Text style={[styles.deepDiveCardTitle, { color: theme.text }]}>{card.title}</Text>
                    <Text style={[styles.deepDiveCardSubtitle, { color: theme.textSecondary }]}>{card.subtitle}</Text>
                    {!isExpanded && (
                      <Text style={[styles.deepDiveCardPreview, { color: theme.textTertiary }]}>{card.preview}</Text>
                    )}
                  </View>
                </View>
                <Text style={[styles.deepDiveChevron, { color: theme.textTertiary }]}>
                  {isExpanded ? '▼' : '▶'}
                </Text>
              </TouchableOpacity>

              {/* Card Content */}
              {isExpanded && (
                <View style={styles.deepDiveCardContent}>
                  {/* What this is */}
                  <View style={styles.deepDiveSection}>
                    <Text style={[styles.deepDiveSectionLabel, { color: theme.textTertiary }]}>WHAT THIS IS</Text>
                    <Text style={[styles.deepDiveSectionText, { color: theme.textSecondary }]}>{card.whatThisIs}</Text>
                  </View>

                  {/* What you might notice */}
                  <View style={styles.deepDiveSection}>
                    <Text style={[styles.deepDiveSectionLabel, { color: theme.accent }]}>WHAT YOU MIGHT NOTICE</Text>
                    <View style={styles.bulletList}>
                      {card.whatYouMightNotice.map((item, i) => (
                        <View key={i} style={styles.bulletItem}>
                          <Text style={[styles.bullet, { color: theme.accent }]}>•</Text>
                          <Text style={[styles.bulletText, { color: theme.text }]}>{item}</Text>
                        </View>
                      ))}
                    </View>
                  </View>

                  {/* Tension */}
                  <View style={[styles.deepDiveSection, styles.tensionSection]}>
                    <Text style={[styles.deepDiveSectionLabel, { color: '#E57373' }]}>{card.tensionLabel.toUpperCase()}</Text>
                    <Text style={[styles.deepDiveSectionText, { color: theme.textSecondary }]}>{card.tension}</Text>
                  </View>

                  {/* Gift */}
                  <View style={[styles.deepDiveSection, styles.giftSection]}>
                    <Text style={[styles.deepDiveSectionLabel, { color: '#81C784' }]}>{card.giftLabel.toUpperCase()}</Text>
                    <Text style={[styles.deepDiveSectionText, { color: theme.textSecondary }]}>{card.gift}</Text>
                  </View>

                  {/* Reflection */}
                  <View style={[styles.reflectionBox, { backgroundColor: theme.accent + '06', borderColor: theme.border }]}>
                    <Text style={[styles.reflectionBoxLabel, { color: theme.accent }]}>A QUESTION TO SIT WITH</Text>
                    <Text style={[styles.reflectionBoxText, { color: theme.textSecondary }]}>{card.reflection}</Text>
                  </View>

                  {/* Action Buttons */}
                  <View style={styles.actionButtons}>
                    <TouchableOpacity
                      style={[styles.actionButton, { borderColor: theme.border }]}
                      onPress={() => handleReflect(card)}
                      activeOpacity={0.6}
                    >
                      <Text style={styles.actionIcon}>💭</Text>
                      <Text style={[styles.actionText, { color: theme.textSecondary }]}>Reflect</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.actionButton, { borderColor: theme.border }]}
                      onPress={() => handleJournal(card)}
                      activeOpacity={0.6}
                    >
                      <Text style={styles.actionIcon}>📝</Text>
                      <Text style={[styles.actionText, { color: theme.textSecondary }]}>Journal</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.actionButton, { borderColor: theme.border }]}
                      onPress={() => handleAskMirror(card)}
                      activeOpacity={0.6}
                    >
                      <Text style={styles.actionIcon}>✨</Text>
                      <Text style={[styles.actionText, { color: theme.textSecondary }]}>Ask Mirror</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
            </View>
          );
        })}

        {/* Footer */}
        <Text style={[styles.footer, { color: theme.textTertiary }]}>
          A lens for understanding patterns, not a definition of identity.
        </Text>
      </View>
    );
  };

  // ============================================
  // MAIN RENDER
  // ============================================
  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {renderTabs()}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.textTertiary} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              {activeTab === 'deep_dive'
                ? 'Generating your personalized reading...'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Text style={{ fontSize: 28, color: theme.textTertiary }}>⚠</Text>
            <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryButton, { backgroundColor: theme.surface }]}
              onPress={() => loadTabData(activeTab)}
            >
              <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            {activeTab === 'at_a_glance' && renderAtAGlance()}
            {activeTab === 'today' && renderTodaySnapshot()}
            {activeTab === 'deep_dive' && renderDeepDive()}
          </>
        )}
      </ScrollView>
    </View>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  activeTab: {},
  tabText: {
    fontSize: 13,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    textAlign: 'center',
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginTop: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  emptyState: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyStateText: {
    fontSize: 14,
    fontStyle: 'italic',
  },

  // At a Glance
  atAGlanceContainer: {
    gap: 12,
  },
  big3Card: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    alignItems: 'center',
  },
  big3Label: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
  },
  big3Row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  big3Item: {
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  big3Symbol: {
    fontSize: 16,
    marginBottom: 4,
  },
  big3Sign: {
    fontSize: 15,
    fontWeight: '600',
  },
  big3Divider: {
    width: 1,
    height: 32,
  },
  synthesisCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  synthesisText: {
    fontSize: 15,
    lineHeight: 22,
  },
  chipsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
  },
  chipText: {
    fontSize: 12,
    fontWeight: '500',
  },
  structureCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  structureTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  structureGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  structureItem: {
    width: '50%',
    marginBottom: 12,
  },
  structureLabel: {
    fontSize: 10,
    marginBottom: 2,
  },
  structureValue: {
    fontSize: 14,
    fontWeight: '500',
  },
  tensionsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  tensionsTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  tensionItem: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  tensionBullet: {
    fontSize: 14,
    marginRight: 8,
  },
  tensionText: {
    fontSize: 14,
    flex: 1,
  },
  giftsCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  giftsTitle: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  giftItem: {
    flexDirection: 'row',
    marginBottom: 6,
  },
  giftBullet: {
    fontSize: 14,
    marginRight: 8,
  },
  giftText: {
    fontSize: 14,
    flex: 1,
  },
  reflectionCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  reflectionLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 14,
    borderRadius: 10,
    gap: 8,
    marginTop: 4,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
  },

  // Today
  todayContainer: {
    gap: 12,
  },
  altitudeSelector: {
    flexDirection: 'row',
    padding: 4,
    borderRadius: 10,
  },
  altitudeTab: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
  },
  altitudeTabActive: {},
  altitudeTabText: {
    fontSize: 13,
    fontWeight: '500',
  },
  narrativeCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
  },
  narrativeText: {
    fontSize: 15,
    lineHeight: 22,
  },
  causeText: {
    fontSize: 13,
    marginTop: 12,
    fontStyle: 'italic',
  },
  inlineReflectButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    alignSelf: 'flex-start',
  },

  // Deep Dive
  deepDiveContainer: {
    gap: 10,
  },
  deepDiveHeader: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    alignItems: 'center',
    marginBottom: 4,
  },
  deepDiveNote: {
    fontSize: 12,
    marginTop: 12,
    textAlign: 'center',
  },
  deepDiveCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  deepDiveCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  deepDiveCardHeaderContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    flex: 1,
  },
  deepDiveCardNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  deepDiveCardNumberText: {
    fontSize: 12,
    fontWeight: '600',
  },
  deepDiveCardTitleContainer: {
    flex: 1,
  },
  deepDiveCardTitle: {
    fontSize: 15,
    fontWeight: '600',
  },
  deepDiveCardSubtitle: {
    fontSize: 12,
    marginTop: 2,
    opacity: 0.75,
  },
  deepDiveCardPreview: {
    fontSize: 12,
    marginTop: 6,
    fontStyle: 'italic',
  },
  deepDiveChevron: {
    fontSize: 10,
    marginLeft: 8,
  },
  deepDiveCardContent: {
    paddingHorizontal: 14,
    paddingBottom: 14,
  },
  deepDiveSection: {
    marginBottom: 14,
  },
  tensionSection: {
    paddingLeft: 10,
    borderLeftWidth: 2,
    borderLeftColor: '#E57373',
  },
  giftSection: {
    paddingLeft: 10,
    borderLeftWidth: 2,
    borderLeftColor: '#81C784',
  },
  deepDiveSectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  deepDiveSectionText: {
    fontSize: 14,
    lineHeight: 20,
  },
  bulletList: {
    gap: 5,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  bullet: {
    fontSize: 13,
    marginRight: 8,
    lineHeight: 19,
  },
  bulletText: {
    fontSize: 14,
    lineHeight: 19,
    flex: 1,
  },
  reflectionBox: {
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
    marginBottom: 12,
  },
  reflectionBoxLabel: {
    fontSize: 9,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  reflectionBoxText: {
    fontSize: 13,
    lineHeight: 19,
    fontStyle: 'italic',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 6,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: StyleSheet.hairlineWidth,
    gap: 4,
  },
  actionIcon: {
    fontSize: 11,
  },
  actionText: {
    fontSize: 11,
    fontWeight: '500',
  },
  footer: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
    fontStyle: 'italic',
  },
});
