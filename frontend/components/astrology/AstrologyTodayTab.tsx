// ============================================
// ASTROLOGY TODAY TAB
// Renders: Today/Week/Month content with live timing layer
// Upgraded: Premium timing layer with real transit data
// ============================================

import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';

import {
  FullChartData,
  TransitHit,
  TransitWindow,
  Timeframe,
  CollapsedInsights,
} from '../../services/astrology/astrologyTypes';

import {
  HOUSE_MEANINGS,
  getChartRuler,
  getDominantHouses,
  isChartRulerActivated,
  detectChapterTransits,
  detectRepeatPatterns,
  detectPersonalRelevance,
  getActivatedHouses,
  buildRulershipChains,
  detectThemeConcentration,
  prioritizeTransits,
  buildAspectPatternAnalysis,
  isPatternActivatedByTransit,
  buildLifeChapterAnalysis,
  getChapterContextLine,
  buildCollapsedInsights,
} from '../../services/astrology/astrologyInterpreter';

import {
  getDailyEnergySynthesis,
  getWhatThisMayFeelLike,
  getMistakeToWatch,
  getReflectionQuestion,
  getLifeAreaContext,
  getMoonPhaseContext,
  getPersonalRelevanceLine,
  getChartRulerContextLine,
  getDominantHouseRulerLine,
  getRulershipChainLine,
  getChapterLine,
  getRepeatPatternLine,
  getThemeCollapseLineIfApplicable,
} from '../../services/astrology/astrologyNarrative';

import { cleanText } from '../../utils/languageGuard';

// ============================================
// LIFE DOMAIN MAPPING - Translate houses/planets to real life
// ============================================

const HOUSE_TO_LIFE_DOMAIN: { [key: number]: string } = {
  1: 'identity / self-expression / physical presence',
  2: 'money / resources / self-worth',
  3: 'communication / thinking / voice / learning',
  4: 'home / family / inner life / emotional roots',
  5: 'creativity / self-expression / romance / joy',
  6: 'work / health / daily routines / service',
  7: 'partnership / relating / commitments / reciprocity',
  8: 'intimacy / shared resources / emotional depth / transformation',
  9: 'beliefs / meaning / travel / expansion',
  10: 'career / public role / responsibility / achievement',
  11: 'community / friendship / hopes / collective connection',
  12: 'solitude / rest / spirituality / what operates beneath awareness',
};

const PLANET_TO_THEME: { [key: string]: string } = {
  'Sun': 'core identity / vitality / self-expression',
  'Moon': 'emotional life / needs / comfort / inner rhythms',
  'Mercury': 'communication / thinking / perception',
  'Venus': 'relationships / values / pleasure / closeness',
  'Mars': 'action / drive / assertion / conflict',
  'Jupiter': 'growth / expansion / opportunity / optimism',
  'Saturn': 'pressure / responsibility / limits / maturity',
  'Uranus': 'disruption / change / freedom / individuality',
  'Neptune': 'imagination / idealism / dissolution / spirituality',
  'Pluto': 'power / transformation / intensity / depth',
  'Chiron': 'sensitivity / old wounds / healing / wisdom',
  'North Node': 'growth direction / developmental edge',
  'South Node': 'familiar patterns / comfort zone',
};

// ============================================
// TRANSIT HUMAN TRANSLATIONS
// ============================================

interface TransitTranslation {
  label: string;
  humanLine: string;
}

const getTransitHumanLine = (
  transitPoint: string,
  aspectType: string,
  natalPoint: string
): string => {
  const aspect = aspectType.toLowerCase();
  const transit = transitPoint;
  const natal = natalPoint;
  
  // Jupiter transits
  if (transit === 'Jupiter') {
    if (natal === 'Saturn') return aspect === 'square' || aspect === 'opposition' 
      ? 'Expansion is meeting resistance—growth may require more patience than speed.'
      : 'Growth and structure are finding productive alignment.';
    if (natal === 'Sun') return aspect === 'square' || aspect === 'opposition'
      ? 'Confidence may be stretching beyond current capacity.'
      : 'A natural expansiveness is supporting self-expression.';
    if (natal === 'Moon') return aspect === 'square' || aspect === 'opposition'
      ? 'Emotional needs may be inflating or feeling harder to contain.'
      : 'Emotional generosity and optimism are flowing more easily.';
    if (natal === 'Mars') return 'Action and expansion are in active conversation.';
    if (natal === 'Venus') return 'Relationships and pleasure may be amplified.';
    if (natal === 'Mercury') return 'Thinking and communication are expanding.';
  }
  
  // Saturn transits
  if (transit === 'Saturn') {
    if (natal === 'Sun') return 'Identity is being tested by responsibility and limits.';
    if (natal === 'Moon') return 'Emotional life is carrying more weight than usual.';
    if (natal === 'Mars') return 'Action is meeting friction—patience may be required.';
    if (natal === 'Venus') return 'Relationships may be under pressure to mature.';
    if (natal === 'Jupiter') return 'Optimism is being asked to get realistic.';
    if (natal === 'Mercury') return 'Thinking is being asked to be more serious or precise.';
  }
  
  // Pluto transits
  if (transit === 'Pluto') {
    if (natal === 'Mars') return 'Pressure may be intensifying how action and control are handled.';
    if (natal === 'Sun') return 'Deep transformation is touching the core of identity.';
    if (natal === 'Moon') return 'Emotional intensity is running higher than usual.';
    if (natal === 'Venus') return 'Relationships are being pulled into deeper territory.';
    if (natal === 'Saturn') return 'Power and structure are being renegotiated.';
  }
  
  // Uranus transits
  if (transit === 'Uranus') {
    if (natal === 'Jupiter') return 'Sudden opportunities or disruptions to growth are possible.';
    if (natal === 'Saturn') return 'Structures are being challenged to change or break.';
    if (natal === 'Sun') return 'Identity is being pushed toward something less predictable.';
    if (natal === 'Moon') return 'Emotional life may feel more erratic or restless.';
    if (natal === 'Venus') return 'Relationships may be feeling unpredictable or changing.';
    if (natal === 'Mars') return 'Action may be more impulsive or erratic.';
  }
  
  // Neptune transits
  if (transit === 'Neptune') {
    if (natal === 'Chiron') return 'Older sensitivities may be closer to the surface.';
    if (natal === 'Sun') return 'Identity may feel more diffuse or idealized.';
    if (natal === 'Moon') return 'Emotional boundaries may be more permeable.';
    if (natal === 'Venus') return 'Love and idealism are deeply connected right now.';
    if (natal === 'Saturn') return 'Reality and imagination may be harder to distinguish.';
    if (natal === 'Mercury') return 'Thinking may be more imaginative but less precise.';
  }
  
  // Generic fallback based on aspect type
  if (aspect === 'conjunction') return `${transit} is amplifying ${natal.toLowerCase()} themes.`;
  if (aspect === 'square') return `${transit} is creating friction with ${natal.toLowerCase()} patterns.`;
  if (aspect === 'opposition') return `${transit} is creating tension with ${natal.toLowerCase()} expression.`;
  if (aspect === 'trine') return `${transit} is supporting ${natal.toLowerCase()} energy naturally.`;
  if (aspect === 'sextile') return `${transit} is opening opportunities around ${natal.toLowerCase()}.`;
  
  return `${transit} is activating ${natal.toLowerCase()} themes.`;
};

// ============================================
// PSYCHOLOGICAL ACTIVATION BULLETS - Enhanced for timeframe differentiation
// ============================================

const getActivationBullets = (transits: TransitHit[], emphasisTags: string[], timeframe?: Timeframe): string[] => {
  const bullets: string[] = [];
  const seen = new Set<string>();
  
  // From emphasis tags - core themes
  if (emphasisTags.includes('expansion') && emphasisTags.includes('structure')) {
    bullets.push('growth meeting limits');
  } else if (emphasisTags.includes('expansion')) {
    bullets.push('openness to new possibilities');
  }
  
  if (emphasisTags.includes('transformation') || emphasisTags.includes('power')) {
    bullets.push('intensity or pressure building beneath the surface');
  }
  
  if (emphasisTags.includes('communication')) {
    bullets.push('communication or expression asking for attention');
  }
  
  if (emphasisTags.includes('drive') && !seen.has('drive')) {
    bullets.push('forward momentum being tested or redirected');
    seen.add('drive');
  }
  
  if (emphasisTags.includes('opportunity') && !seen.has('opportunity')) {
    bullets.push('doors opening that require discernment');
    seen.add('opportunity');
  }
  
  // From specific transits - deeper themes
  for (const t of transits.slice(0, 6)) {
    const transit = t.transit_point || (t as any).transit_planet;
    const natal = t.natal_point || (t as any).natal_planet;
    const aspect = t.aspect_type;
    
    if (!transit || !natal) continue;
    
    // Neptune + Chiron
    if (transit === 'Neptune' && natal === 'Chiron' && !seen.has('sensitivity')) {
      bullets.push('older sensitivity becoming easier to feel');
      seen.add('sensitivity');
    }
    
    // Pluto + Mars
    if (transit === 'Pluto' && natal === 'Mars' && !seen.has('action-pressure')) {
      bullets.push('pressure on action and follow-through');
      seen.add('action-pressure');
    }
    
    // Uranus transits
    if (transit === 'Uranus' && !seen.has('change')) {
      if (natal === 'Jupiter') {
        bullets.push('unexpected shifts in growth or meaning');
      } else {
        bullets.push('unexpected shifts asking for flexibility');
      }
      seen.add('change');
    }
    
    // Saturn involvement
    if ((transit === 'Saturn' || natal === 'Saturn') && !seen.has('responsibility')) {
      if (aspect === 'square' || aspect === 'opposition') {
        bullets.push('responsibility or delay requiring patience');
      } else {
        bullets.push('structures being tested or refined');
      }
      seen.add('responsibility');
    }
    
    // Jupiter square Saturn - unique combination
    if (transit === 'Jupiter' && natal === 'Saturn' && !seen.has('expansion-structure')) {
      bullets.push('ambition and limitation in active dialogue');
      seen.add('expansion-structure');
    }
    
    // Venus activation
    if (natal === 'Venus' && !seen.has('relating')) {
      bullets.push('relationships or values coming into focus');
      seen.add('relating');
    }
    
    // Sun activation (identity)
    if (natal === 'Sun' && (transit === 'Pluto' || transit === 'Saturn') && !seen.has('identity')) {
      bullets.push('identity or self-definition under examination');
      seen.add('identity');
    }
    
    // Moon activation (emotional)
    if (natal === 'Moon' && !seen.has('emotional')) {
      bullets.push('emotional needs or patterns surfacing');
      seen.add('emotional');
    }
  }
  
  // Cap based on timeframe - today gets fewer, month gets more
  const maxBullets = timeframe === 'today' ? 3 : timeframe === 'week' ? 4 : 4;
  return bullets.slice(0, maxBullets);
};

// ============================================
// LIFE DOMAIN EXTRACTION - Enhanced with richer mapping
// ============================================

interface LifeDomainResult {
  domains: string[];
  detailedDomains: string[];
  primaryHouses: number[];
}

const getLifeDomainsEnhanced = (transits: TransitHit[]): LifeDomainResult => {
  const houseCounts: { [key: number]: number } = {};
  const planetThemes = new Set<string>();
  
  for (const t of transits) {
    const house = t.natal_house;
    if (house) {
      houseCounts[house] = (houseCounts[house] || 0) + 1;
    }
    
    // Also gather planetary themes
    const natal = t.natal_point || (t as any).natal_planet;
    if (natal && PLANET_TO_THEME[natal]) {
      // Get first theme for planet
      const theme = PLANET_TO_THEME[natal].split(' / ')[0];
      planetThemes.add(theme);
    }
  }
  
  // Get top 4 houses by frequency
  const sortedHouses = Object.entries(houseCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 4)
    .map(([h]) => parseInt(h));
  
  const domains: string[] = [];
  const detailedDomains: string[] = [];
  
  for (const house of sortedHouses) {
    const fullDomain = HOUSE_TO_LIFE_DOMAIN[house];
    if (fullDomain) {
      // Short version for compact display
      const shortDomain = fullDomain.split(' / ')[0];
      domains.push(shortDomain);
      // Detailed version
      detailedDomains.push(fullDomain);
    }
  }
  
  return {
    domains,
    detailedDomains,
    primaryHouses: sortedHouses,
  };
};

const getLifeDomainLine = (transits: TransitHit[], timeframe: Timeframe): string => {
  const { domains, detailedDomains } = getLifeDomainsEnhanced(transits);
  if (domains.length === 0) return '';
  
  // More specific phrasing based on timeframe
  const prefix = timeframe === 'today' 
    ? 'This may show up most today in'
    : timeframe === 'week'
    ? 'This week, watch for activity in'
    : 'This month, themes may concentrate in';
  
  if (domains.length === 1) {
    return `${prefix} ${domains[0]}.`;
  }
  
  if (domains.length === 2) {
    return `${prefix} ${domains[0]} and ${domains[1]}.`;
  }
  
  // For 3+, use the detailed first item and short for rest
  const [first, ...rest] = domains;
  const last = rest.pop();
  return `${prefix} ${first}, ${rest.join(', ')}, and ${last}.`;
};

// Get compact domain list for context
const getLifeDomains = (transits: TransitHit[]): string[] => {
  return getLifeDomainsEnhanced(transits).domains;
};

// ============================================
// SUPPORT LINE GENERATION
// ============================================

const getSupportLine = (transits: TransitHit[], emphasisTags: string[], timeframe: Timeframe): string => {
  const hasSaturn = transits.some(t => 
    (t.transit_point || (t as any).transit_planet) === 'Saturn' ||
    (t.natal_point || (t as any).natal_planet) === 'Saturn'
  );
  
  const hasPluto = transits.some(t => 
    (t.transit_point || (t as any).transit_planet) === 'Pluto'
  );
  
  const hasNeptune = transits.some(t => 
    (t.transit_point || (t as any).transit_planet) === 'Neptune'
  );
  
  const hasUranus = transits.some(t => 
    (t.transit_point || (t as any).transit_planet) === 'Uranus'
  );
  
  const hasExpansionStructure = emphasisTags.includes('expansion') && emphasisTags.includes('structure');
  
  if (hasExpansionStructure) {
    return 'Let clarity come before commitment where possible.';
  }
  
  if (hasSaturn && hasPluto) {
    return 'If something feels overcharged, it may help to name it before acting on it.';
  }
  
  if (hasSaturn) {
    return 'Slowing the pace may reveal more than pushing through.';
  }
  
  if (hasPluto) {
    return 'What is surfacing may need witnessing before it needs solving.';
  }
  
  if (hasNeptune) {
    return 'Let what is unclear remain unclear a little longer if needed.';
  }
  
  if (hasUranus) {
    return 'Flexibility may serve better than rigid planning right now.';
  }
  
  // Timeframe-specific defaults
  if (timeframe === 'today') {
    return 'Notice what is being touched before trying to fix it.';
  }
  
  if (timeframe === 'week') {
    return 'Let the week reveal its rhythm before over-scheduling.';
  }
  
  return 'Let what is emerging become clearer before trying to resolve it.';
};

// ============================================
// REFLECTION QUESTION GENERATION
// ============================================

const getTimingReflectionQuestion = (transits: TransitHit[], emphasisTags: string[], timeframe: Timeframe): string => {
  const hasExpansionStructure = emphasisTags.includes('expansion') && emphasisTags.includes('structure');
  
  const hasSensitivity = transits.some(t => {
    const natal = t.natal_point || (t as any).natal_planet;
    return natal === 'Chiron';
  });
  
  const hasIdentityPressure = transits.some(t => {
    const natal = t.natal_point || (t as any).natal_planet;
    const transit = t.transit_point || (t as any).transit_planet;
    return (natal === 'Sun' && (transit === 'Saturn' || transit === 'Pluto'));
  });
  
  const hasRelationshipActivation = transits.some(t => {
    const natal = t.natal_point || (t as any).natal_planet;
    return natal === 'Venus';
  });
  
  if (hasExpansionStructure) {
    return 'Where is growth asking for maturity rather than speed?';
  }
  
  if (hasSensitivity) {
    return 'What is being touched here that may be older than this moment?';
  }
  
  if (hasIdentityPressure) {
    return 'What are you trying to prove—and to whom?';
  }
  
  if (hasRelationshipActivation) {
    return 'What becomes possible when you stop managing how others see you?';
  }
  
  // Timeframe defaults
  if (timeframe === 'today') {
    return 'What would shift if you stopped trying to control the outcome?';
  }
  
  if (timeframe === 'week') {
    return 'What are you trying to solve before you\'ve fully named what is happening?';
  }
  
  return 'What becomes clearer if you stop trying to force resolution?';
};

// ============================================
// BUILD TIMING CONTEXT FOR ASK MIRROR - Enhanced
// ============================================

interface TimingContext {
  timeframe: Timeframe;
  timeframeLabel: string;
  topTransits: string[];
  topTransitDescriptions: string[];
  activatedNatalPoints: string[];
  activatedNatalHouses: number[];
  lifeDomains: string[];
  lifeDomainsSentence: string;
  questionToSitWith: string;
  supportLine: string;
  emphasisTags: string[];
  activationThemes: string[];
}

const buildTimingContext = (
  transits: TransitHit[],
  emphasisTags: string[],
  timeframe: Timeframe
): TimingContext => {
  const topTransits = transits.slice(0, 3).map(t => {
    const transit = t.transit_point || (t as any).transit_planet || '?';
    const natal = t.natal_point || (t as any).natal_planet || '?';
    return `${transit} ${t.aspect_type} ${natal}`;
  });
  
  const topTransitDescriptions = transits.slice(0, 3).map(t => {
    const transit = t.transit_point || (t as any).transit_planet || '?';
    const natal = t.natal_point || (t as any).natal_planet || '?';
    return getTransitHumanLine(transit, t.aspect_type, natal);
  });
  
  const activatedNatalPoints = [...new Set(transits.slice(0, 5).map(t => 
    t.natal_point || (t as any).natal_planet
  ).filter(Boolean))];
  
  const activatedNatalHouses = [...new Set(transits.slice(0, 5).map(t => 
    t.natal_house
  ).filter(h => h !== undefined && h !== null))] as number[];
  
  const { domains, detailedDomains } = getLifeDomainsEnhanced(transits);
  const lifeDomainsSentence = getLifeDomainLine(transits, timeframe);
  const questionToSitWith = getTimingReflectionQuestion(transits, emphasisTags, timeframe);
  const supportLine = getSupportLine(transits, emphasisTags, timeframe);
  const activationThemes = getActivationBullets(transits, emphasisTags, timeframe);
  
  const timeframeLabel = timeframe === 'today' ? 'Today' : 
                         timeframe === 'week' ? 'This Week' : 'This Month';
  
  return {
    timeframe,
    timeframeLabel,
    topTransits,
    topTransitDescriptions,
    activatedNatalPoints,
    activatedNatalHouses,
    lifeDomains: domains,
    lifeDomainsSentence,
    questionToSitWith,
    supportLine,
    emphasisTags,
    activationThemes,
  };
};

// ============================================
// SIGNALS SECTION COMPONENT (Now "Evidence" when dominant truth exists)
// ============================================

interface SignalsSectionProps {
  transits: TransitHit[];
  expanded: boolean;
  onToggle: () => void;
  theme: any;
  label?: string;
}

const getAspectSymbol = (aspectType: string): string => {
  const symbols: { [key: string]: string } = {
    'conjunction': '☌',
    'opposition': '☍',
    'trine': '△',
    'square': '□',
    'sextile': '⚹'
  };
  return symbols[aspectType] || '•';
};

const SignalsSection: React.FC<SignalsSectionProps> = ({ transits, expanded, onToggle, theme, label }) => {
  if (!transits || transits.length === 0) return null;

  const displayLabel = label || 'What this is based on';

  return (
    <>
      <TouchableOpacity
        style={[styles.signalsToggle, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
        onPress={onToggle}
        activeOpacity={0.7}
      >
        <Text style={[styles.signalsToggleText, { color: theme.textSecondary }]}>
          {displayLabel} {expanded ? '▴' : '▾'}
        </Text>
      </TouchableOpacity>

      {expanded && (
        <View style={[styles.signalsContainer, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
          {/* Timing Pressures */}
          <View style={styles.signalsSection}>
            <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>TIMING PRESSURES</Text>
            <View style={styles.signalsCompactList}>
              {transits.slice(0, 4).map((hit, index) => (
                <View key={index} style={styles.signalsTransitRow}>
                  <Text style={[styles.signalsTransitText, { color: theme.textSecondary }]}>
                    {getAspectSymbol(hit.aspect_type)} {hit.transit_point} {hit.aspect_type} {hit.natal_point}
                  </Text>
                  <Text style={[styles.signalsTransitOrb, { color: theme.textTertiary }]}>
                    {hit.orb.toFixed(1)}°
                  </Text>
                </View>
              ))}
            </View>
          </View>

          {/* What's Being Touched */}
          {transits.length > 0 && (
            <View style={styles.signalsSection}>
              <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>WHAT'S BEING TOUCHED</Text>
              <View style={styles.signalsChipsRow}>
                {[...new Set(transits.slice(0, 6).map(t => t.natal_point))].map((point, i) => (
                  <View key={i} style={[styles.signalsChip, { backgroundColor: theme.accent + '10' }]}>
                    <Text style={[styles.signalsChipText, { color: theme.accent }]}>{point}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* Where This Is Landing */}
          <View style={styles.signalsSection}>
            <Text style={[styles.signalsSectionTitle, { color: theme.textTertiary }]}>WHERE THIS IS LANDING</Text>
            <View style={styles.signalsLifeAreas}>
              {transits.slice(0, 4).map((hit, i) => {
                const shortAreaMap: { [key: string]: string } = {
                  'Sun': 'Purpose, identity',
                  'Moon': 'Emotions, comfort',
                  'Mercury': 'Thinking, communication',
                  'Venus': 'Relationships, values',
                  'Mars': 'Action, drive',
                  'Jupiter': 'Growth, meaning',
                  'Saturn': 'Structure, maturity',
                  'Uranus': 'Change, freedom',
                  'Neptune': 'Intuition, boundaries',
                  'Pluto': 'Power, transformation',
                  'Chiron': 'Wounds, healing'
                };
                return (
                  <Text key={i} style={[styles.signalsLifeAreaText, { color: theme.textSecondary }]}>
                    • {hit.natal_point}: {shortAreaMap[hit.natal_point] || hit.natal_point}
                  </Text>
                );
              })}
            </View>
          </View>
        </View>
      )}
    </>
  );
};

// ============================================
// PROPS INTERFACE
// ============================================

interface AstrologyTodayTabProps {
  fullChartData: FullChartData | null;
  theme: any;
  onOpenChat: () => void;
  onReflect: (question: string) => void;
  onSwitchToTimeline?: () => void;
}

// ============================================
// TIMELINE PHASE DETECTION
// ============================================

interface CurrentPhase {
  name: string;
  dateRange: string;
  summary: string;
  isPrimary: boolean;
  id: string;
}

function getCurrentTimelinePhase(): CurrentPhase | null {
  const now = new Date();
  const currentMonth = now.getMonth(); // 0-11
  const currentYear = now.getFullYear();
  
  // Q1: Jan-Mar (months 0-2)
  if (currentMonth >= 0 && currentMonth <= 2) {
    return {
      id: 'q1',
      name: 'Recognition',
      dateRange: `Jan – Mar ${currentYear}`,
      summary: 'The year\'s dominant tension is beginning to show itself in small, easy-to-dismiss moments.',
      isPrimary: false,
    };
  }
  
  // Q2: Apr-Jun (months 3-5)
  if (currentMonth >= 3 && currentMonth <= 5) {
    return {
      id: 'q2',
      name: 'Confrontation',
      dateRange: `Apr – Jun ${currentYear}`,
      summary: 'What you\'ve been tolerating becomes harder to keep calling "manageable."',
      isPrimary: true,
    };
  }
  
  // Q3: Jul-Sep (months 6-8)
  if (currentMonth >= 6 && currentMonth <= 8) {
    return {
      id: 'q3',
      name: 'The Crossroads',
      dateRange: `Jul – Sep ${currentYear}`,
      summary: 'Two versions of your direction become visible—the question is which one you\'ll commit to.',
      isPrimary: true,
    };
  }
  
  // Q4: Oct-Dec (months 9-11)
  if (currentMonth >= 9 && currentMonth <= 11) {
    return {
      id: 'q4',
      name: 'Integration',
      dateRange: `Oct – Dec ${currentYear}`,
      summary: 'The year\'s lessons are settling—either as earned clarity or recognition of what needs another cycle.',
      isPrimary: false,
    };
  }
  
  return null;
}

function getTimelineLinkingLine(phase: CurrentPhase | null, altitude: Timeframe): string | null {
  if (!phase) return null;
  
  const phaseName = phase.name;
  
  if (altitude === 'today') {
    if (phase.isPrimary) {
      return `This isn't just today—this is part of your ${phaseName} phase.`;
    }
    return `This moment is connected to a larger ${phaseName.toLowerCase()} happening this quarter.`;
  }
  
  if (altitude === 'week') {
    return `This week sits inside your ${phaseName} phase.`;
  }
  
  if (altitude === 'month') {
    return `This month is where your ${phaseName} phase becomes more visible.`;
  }
  
  return null;
}

// ============================================
// MAIN COMPONENT
// ============================================

const AstrologyTodayTab: React.FC<AstrologyTodayTabProps> = ({
  fullChartData,
  theme,
  onOpenChat,
  onReflect,
  onSwitchToTimeline,
}) => {
  const [activeAltitude, setActiveAltitude] = useState<Timeframe>('today');
  const [signalsExpanded, setSignalsExpanded] = useState(false);

  // Get current timeline phase
  const currentPhase = getCurrentTimelinePhase();
  const timelineLinkingLine = getTimelineLinkingLine(currentPhase, activeAltitude);

  // Get transit window based on timeframe
  const getTransitWindow = (): TransitWindow | null => {
    if (!fullChartData?.transits?.windows) return null;
    
    switch (activeAltitude) {
      case 'today': return fullChartData.transits.windows.today;
      case 'week': return fullChartData.transits.windows.this_week;
      case 'month': return fullChartData.transits.windows.this_month;
      default: return fullChartData.transits.windows.today;
    }
  };

  const currentWindow = getTransitWindow();
  const transits = currentWindow?.strongest_hits || [];

  // Get activated houses for context
  const activatedHouses = getActivatedHouses(transits);

  // Generate all context lines from services
  const energySynthesis = getDailyEnergySynthesis(transits, activeAltitude);
  const lifeAreaContext = getLifeAreaContext(transits);
  const moonPhaseContext = getMoonPhaseContext(transits, fullChartData);
  
  // Personal relevance
  const personalRelevance = detectPersonalRelevance(fullChartData, transits);
  const personalRelevanceLine = getPersonalRelevanceLine(personalRelevance, activatedHouses, fullChartData);
  
  // Chart ruler context
  const chartRulerLine = getChartRulerContextLine(fullChartData, transits);
  
  // Rulership chain context
  const rulershipChainLine = getRulershipChainLine(fullChartData, transits);
  
  // Dominant house ruler context
  const dominantHouseRulerLine = getDominantHouseRulerLine(fullChartData, transits);
  
  // Theme collapse
  const themeCollapseLine = getThemeCollapseLineIfApplicable(fullChartData, transits);
  
  // Repeat patterns
  const repeatPatternLine = getRepeatPatternLine(fullChartData, transits);
  
  // Chapter awareness (for month view)
  const chapterInfo = detectChapterTransits(transits);
  const chapterLine = activeAltitude === 'month' ? getChapterLine(chapterInfo) : '';

  // Pattern activation check (Part 8)
  const patternAnalysis = buildAspectPatternAnalysis(fullChartData);
  const patternActivation = isPatternActivatedByTransit(patternAnalysis, transits);

  // Life Chapter context (Master Astrologer v4)
  const lifeChapterAnalysis = buildLifeChapterAnalysis(fullChartData);
  const lifeChapterContextLine = getChapterContextLine(lifeChapterAnalysis, activeAltitude);

  // DOMINANT TRUTH (Master Astrologer v5)
  const collapsedInsights = buildCollapsedInsights(fullChartData, lifeChapterAnalysis, patternAnalysis, activeAltitude);
  const hasDominantTruth = collapsedInsights.dominantTruth !== null && collapsedInsights.narrative !== null;

  // Get content based on timeframe (fallback if no dominant truth)
  const feelings = getWhatThisMayFeelLike(transits, activeAltitude).slice(0, 3);
  const mistakes = getMistakeToWatch(transits, activeAltitude).slice(0, 3);
  const question = getReflectionQuestion(transits, activeAltitude);
  
  // NEW: Premium Timing Layer Content
  const emphasisTags = currentWindow?.emphasis_tags || [];
  const topTransits = transits.slice(0, 3);
  const activationBullets = getActivationBullets(transits, emphasisTags, activeAltitude);
  const lifeDomainLine = getLifeDomainLine(transits, activeAltitude);
  const supportLine = getSupportLine(transits, emphasisTags, activeAltitude);
  const timingReflectionQuestion = getTimingReflectionQuestion(transits, emphasisTags, activeAltitude);
  const timingContext = buildTimingContext(transits, emphasisTags, activeAltitude);
  
  // Handle Ask Mirror with timing context
  const handleAskMirrorWithContext = () => {
    console.log('[AstrologyTodayTab] Timing context for Ask Mirror:', timingContext);
    onOpenChat();
  };

  return (
    <ScrollView style={styles.todayContainer} showsVerticalScrollIndicator={false}>
      {/* Altitude Selector */}
      <View style={[styles.altitudeSelector, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
        <TouchableOpacity
          style={[styles.altitudeButton, activeAltitude === 'today' && { backgroundColor: theme.surface }]}
          onPress={() => setActiveAltitude('today')}
        >
          <Text style={[styles.altitudeText, { color: activeAltitude === 'today' ? theme.text : theme.textTertiary }]}>
            Today
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.altitudeButton, activeAltitude === 'week' && { backgroundColor: theme.surface }]}
          onPress={() => setActiveAltitude('week')}
        >
          <Text style={[styles.altitudeText, { color: activeAltitude === 'week' ? theme.text : theme.textTertiary }]}>
            This Week
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.altitudeButton, activeAltitude === 'month' && { backgroundColor: theme.surface }]}
          onPress={() => setActiveAltitude('month')}
        >
          <Text style={[styles.altitudeText, { color: activeAltitude === 'month' ? theme.text : theme.textTertiary }]}>
            This Month
          </Text>
        </TouchableOpacity>
      </View>

      {/* TIMELINE CONTEXT STRIP - Connects Today to larger arc */}
      {currentPhase && onSwitchToTimeline && (
        <TouchableOpacity
          style={styles.timelineContextStrip}
          onPress={onSwitchToTimeline}
          activeOpacity={0.7}
        >
          <View style={styles.timelineContextLeft}>
            <Text style={[styles.timelineContextPhase, { color: theme.textSecondary }]}>
              {currentPhase.isPrimary ? '⭐ ' : ''}{currentPhase.name}
            </Text>
            <Text style={[styles.timelineContextDate, { color: theme.textTertiary }]}>
              {currentPhase.dateRange}
            </Text>
          </View>
          <Text style={[styles.timelineContextArrow, { color: theme.textTertiary }]}>→</Text>
        </TouchableOpacity>
      )}


      {/* ============================================ */}
      {/* SECTION 1: TOP ACTIVE TRANSITS */}
      {/* ============================================ */}
      {topTransits.length > 0 && (
        <View style={[styles.topTransitsSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>TOP ACTIVE TRANSITS</Text>
          <View style={styles.topTransitsList}>
            {topTransits.map((t, index) => {
              const transit = t.transit_point || (t as any).transit_planet || '?';
              const natal = t.natal_point || (t as any).natal_planet || '?';
              const aspectLabel = `${transit} ${t.aspect_type} ${natal}`;
              const humanLine = getTransitHumanLine(transit, t.aspect_type, natal);
              
              return (
                <View key={index} style={[styles.transitRow, index < topTransits.length - 1 && { borderBottomWidth: 1, borderBottomColor: theme.border }]}>
                  <Text style={[styles.transitLabel, { color: theme.text }]}>{aspectLabel}</Text>
                  <Text style={[styles.transitHumanLine, { color: theme.textSecondary }]}>{humanLine}</Text>
                </View>
              );
            })}
          </View>
        </View>
      )}

      {/* ============================================ */}
      {/* SECTION 2: WHAT IS BEING ACTIVATED */}
      {/* ============================================ */}
      {activationBullets.length > 0 && (
        <View style={[styles.activationSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>WHAT IS BEING ACTIVATED</Text>
          <View style={styles.bulletList}>
            {activationBullets.map((bullet, index) => (
              <Text key={index} style={[styles.bulletItem, { color: theme.textSecondary }]}>
                • {bullet}
              </Text>
            ))}
          </View>
        </View>
      )}

      {/* ============================================ */}
      {/* SECTION 3: WHERE THIS MAY LAND */}
      {/* ============================================ */}
      {lifeDomainLine && (
        <View style={[styles.domainSection, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>WHERE THIS MAY LAND</Text>
          <Text style={[styles.domainLine, { color: theme.text }]}>{lifeDomainLine}</Text>
        </View>
      )}

      {/* ============================================ */}
      {/* SECTION 4: WHAT HELPS NOW */}
      {/* ============================================ */}
      <View style={[styles.supportSection, { backgroundColor: '#10B98108', borderColor: '#10B98120' }]}>
        <Text style={[styles.sectionTitleGreen, { color: '#10B981' }]}>WHAT HELPS NOW</Text>
        <Text style={[styles.supportLine, { color: theme.text }]}>{supportLine}</Text>
      </View>

      {/* ============================================ */}
      {/* SECTION 5: A QUESTION TO SIT WITH */}
      {/* ============================================ */}
      <View style={[styles.questionSection, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
        <Text style={[styles.sectionTitleAccent, { color: theme.accent }]}>A QUESTION TO SIT WITH</Text>
        <Text style={[styles.questionLine, { color: theme.text }]}>{timingReflectionQuestion}</Text>
        <TouchableOpacity
          style={[styles.reflectButton, { backgroundColor: theme.accent }]}
          onPress={() => onReflect(timingReflectionQuestion)}
        >
          <Text style={[styles.reflectButtonText, { color: theme.background }]}>Reflect on this</Text>
        </TouchableOpacity>
      </View>

      {/* Signals Section - Evidence */}
      <SignalsSection 
        transits={transits}
        expanded={signalsExpanded}
        onToggle={() => setSignalsExpanded(!signalsExpanded)}
        theme={theme}
        label="ACTIVE SIGNALS"
      />
      {/* Ask Mirror Button */}
      <TouchableOpacity
        style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
        onPress={handleAskMirrorWithContext}
      >
        <Text style={{ fontSize: 16, color: theme.background }}>💬</Text>
        <Text style={[styles.askMirrorText, { color: theme.background }]}>
          {activeAltitude === 'today' ? 'Ask about today' : 
           activeAltitude === 'week' ? 'Ask about this week' : 
           'Ask about this month'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  todayContainer: {
    padding: 16,
    flex: 1,
  },
  altitudeSelector: {
    flexDirection: 'row',
    borderRadius: 10,
    padding: 4,
    borderWidth: 1,
    marginBottom: 12,
  },
  altitudeButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 8,
  },
  altitudeText: {
    fontSize: 13,
    fontWeight: '500',
  },
  // NEW: Premium Timing Layer Styles
  topTransitsSection: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  sectionTitleGreen: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  sectionTitleAccent: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  topTransitsList: {
    gap: 12,
  },
  transitRow: {
    paddingBottom: 12,
  },
  transitLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  transitHumanLine: {
    fontSize: 13,
    lineHeight: 19,
  },
  activationSection: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  bulletList: {
    gap: 6,
  },
  bulletItem: {
    fontSize: 14,
    lineHeight: 20,
  },
  domainSection: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  domainLine: {
    fontSize: 15,
    lineHeight: 22,
  },
  supportSection: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  supportLine: {
    fontSize: 15,
    lineHeight: 22,
  },
  questionSection: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  questionLine: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
    marginBottom: 12,
  },
  // Legacy styles (kept for SignalsSection compatibility)
  dailyEnergyCard: {
    borderRadius: 14,
    padding: 18,
    borderWidth: 1,
    borderLeftWidth: 3,
  },
  dailyEnergyLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  dailyEnergyHeadline: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 10,
    lineHeight: 26,
  },
  dailyEnergyBody: {
    fontSize: 15,
    lineHeight: 23,
  },
  contextLinesContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(0,0,0,0.08)',
    gap: 4,
  },
  contextLine: {
    fontSize: 12,
    lineHeight: 18,
  },
  compressedInsightsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  compressedInsightCard: {
    flex: 1,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
  },
  compressedInsightTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  compressedInsightText: {
    fontSize: 13,
    lineHeight: 19,
  },
  additionalInsightsCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  additionalSection: {
    marginBottom: 10,
  },
  additionalTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  additionalBullet: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 2,
  },
  reflectionCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
  },
  reflectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
    marginBottom: 12,
  },
  fallbackReflectButton: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
  },
  fallbackReflectButtonText: {
    fontSize: 13,
    fontWeight: '500',
  },
  signalsToggle: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  signalsToggleText: {
    fontSize: 12,
    fontWeight: '500',
  },
  signalsContainer: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
  },
  signalsSection: {
    marginBottom: 14,
  },
  signalsSectionTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  signalsCompactList: {
    gap: 4,
  },
  signalsTransitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  signalsTransitText: {
    fontSize: 12,
  },
  signalsTransitOrb: {
    fontSize: 11,
  },
  signalsChipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  signalsChip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  signalsChipText: {
    fontSize: 11,
    fontWeight: '500',
  },
  signalsLifeAreas: {
    gap: 2,
  },
  signalsLifeAreaText: {
    fontSize: 11,
    lineHeight: 16,
  },
  // DOMINANT TRUTH STYLES (Master Astrologer v5)
  dominantTruthCard: {
    borderRadius: 14,
    padding: 18,
    borderWidth: 1.5,
  },
  dominantTruthHeadline: {
    fontSize: 19,
    fontWeight: '600',
    lineHeight: 26,
    marginBottom: 8,
  },
  recognitionLine: {
    fontSize: 13,
    fontWeight: '500',
    fontStyle: 'italic',
    marginBottom: 12,
  },
  coreTruthText: {
    fontSize: 15,
    lineHeight: 23,
    marginBottom: 16,
  },
  whereShowsUp: {
    borderRadius: 10,
    padding: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  whereShowsUpLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  whereShowsUpText: {
    fontSize: 13,
    lineHeight: 19,
  },
  whatGoesWrong: {
    borderRadius: 10,
    padding: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  whatGoesWrongLabel: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  whatGoesWrongText: {
    fontSize: 13,
    lineHeight: 19,
  },
  questionContainer: {
    borderRadius: 10,
    padding: 14,
    borderWidth: 1,
    marginBottom: 14,
  },
  questionText: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  reflectButton: {
    alignSelf: 'center',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 20,
    marginBottom: 14,
  },
  reflectButtonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  timeframeContext: {
    fontSize: 11,
    textAlign: 'center',
    marginBottom: 4,
  },
  evidenceNote: {
    fontSize: 10,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 4,
    gap: 8,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
  },
  // TIMELINE CONTEXT STRIP STYLES
  timelineContextStrip: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    marginBottom: 10,
    borderRadius: 8,
    backgroundColor: 'transparent',
  },
  timelineContextLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  timelineContextPhase: {
    fontSize: 12,
    fontWeight: '500',
  },
  timelineContextDate: {
    fontSize: 11,
  },
  timelineContextArrow: {
    fontSize: 12,
  },
  timelineLinkingLine: {
    fontSize: 12,
    fontStyle: 'italic',
    marginBottom: 14,
    marginTop: -4,
  },
});

export default AstrologyTodayTab;
