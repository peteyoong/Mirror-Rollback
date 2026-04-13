/**
 * AstrologyTimelineSection.tsx
 * 
 * "THE YEAR AS IT UNFOLDS"
 * Master Astrologer Timeline - renders a guru-level yearly unfolding section
 * 
 * Placement: Below Dominant Truth, Above Supporting Evidence
 */

import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { Colors } from '../../constants/colors';
import { FullChartData } from '../../services/astrology/astrologyTypes';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// ============================================
// TYPES
// ============================================

export interface TimelinePhase {
  id: string;
  dateRange: string;
  phaseName: string;
  whatsHappening: string[];
  whatThisCreates: string[];
  wherePeopleGetItWrong: string[];
  whatItsAskingOfYou: string[];
  isPrimary?: boolean;
}

export interface TurningPoint {
  id: string;
  date: string;
  whyThisMatters: string;
  whatBecomesClear: string;
  whatHappensIfAvoided: string;
}

export interface DecisionWindow {
  id: string;
  dateRange: string;
  prompt: string;
  ifYouAct: string;
  ifYouWait: string;
}

export interface TimelineData {
  yearTheme: string;
  primaryArc: string;
  phases: TimelinePhase[];
  turningPoints: TurningPoint[];
  decisionWindows: DecisionWindow[];
}

interface AstrologyTimelineSectionProps {
  fullChartData: FullChartData | null;
  lifeChapterAnalysis?: any;
  patternAnalysis?: any;
  dominantTruth?: any;
  activeAltitude: 'today' | 'week' | 'month';
  timelineData?: TimelineData | null;
}

// ============================================
// TIMELINE DATA GENERATOR
// ============================================

function generateTimelineData(
  fullChartData: FullChartData | null,
  lifeChapterAnalysis: any,
  patternAnalysis: any,
  dominantTruth: any
): TimelineData | null {
  // Remove strict null check - always generate timeline with defaults
  try {
    const planets = fullChartData?.natal?.planets || {};
    const sunSign = planets.Sun?.sign || 'Aries';
    const moonSign = planets.Moon?.sign || 'Cancer';
    const risingSign = fullChartData?.natal?.houses?.cusps?.[0]?.sign || 'Leo';
    
    // Extract life chapter info
    const chapterPhase = lifeChapterAnalysis?.phase || 'building';
    const chapterTheme = lifeChapterAnalysis?.theme || 'growth';
    
    // Extract dominant pattern
    const dominantPattern = dominantTruth?.dominantTheme || patternAnalysis?.primaryPattern || 'self-awareness';
    
    // Build year theme based on chart + chapter
    const yearThemeMap: { [key: string]: string } = {
      'building': `This is a year of constructing something real. The pattern of ${dominantPattern} keeps showing you where the foundation needs work.`,
      'releasing': `This is a year where holding on stops working. The ${dominantPattern} pattern is asking you to let go before you're ready.`,
      'integrating': `This is a year of making sense of what you've been through. The ${dominantPattern} theme connects pieces you thought were separate.`,
      'emerging': `This is a year of becoming visible. The ${dominantPattern} pattern will test whether you're ready to be seen.`,
      'consolidating': `This is a year of choosing what stays. The ${dominantPattern} dynamic will force clarity about what matters.`,
    };
    
    const yearTheme = yearThemeMap[chapterPhase] || 
      `This is a year where ${dominantPattern} keeps showing up until you address it directly.`;
    
    // Build primary arc
    const primaryArcMap: { [key: string]: string } = {
      'building': `Across the year, you'll notice the same tension returning in different forms—${dominantPattern}. Each time it appears, the question sharpens. This year isn't trying to break you. It's teaching you to build something that can hold weight.`,
      'releasing': `The arc of this year is release, not accumulation. You'll feel the ${dominantPattern} pattern intensify until letting go becomes easier than holding. The year isn't punishing you—it's clearing space for what comes next.`,
      'integrating': `This year connects threads you didn't know were related. The ${dominantPattern} theme appears in your work, your relationships, your inner dialogue. The year is asking you to see the pattern whole, not fix each instance separately.`,
      'emerging': `The year builds toward visibility. The ${dominantPattern} pattern has been private—this year it becomes public. What you've been practicing in secret will be tested in the open.`,
      'consolidating': `This year is about choosing. The ${dominantPattern} dynamic will create multiple moments where you must decide what stays and what goes. Indecision has a cost this year.`,
    };
    
    const primaryArc = primaryArcMap[chapterPhase] ||
      `Across the year, the ${dominantPattern} pattern keeps returning. Each appearance teaches you something the previous one couldn't. The year is building toward a choice you'll recognize when you see it.`;

    // Generate phases based on quarter structure
    const currentYear = new Date().getFullYear();
    const phases: TimelinePhase[] = [
      {
        id: 'q1',
        dateRange: `January - March ${currentYear}`,
        phaseName: 'Foundation Setting',
        whatsHappening: [
          `The ${dominantPattern} pattern establishes itself early`,
          'Initial resistance feels strongest here',
        ],
        whatThisCreates: [
          'A sense of urgency that may be premature',
          'Early decisions that set the tone for later',
        ],
        wherePeopleGetItWrong: [
          'Forcing resolution before the pattern is clear',
          'Treating symptoms instead of seeing the system',
        ],
        whatItsAskingOfYou: [
          'Patience with the unfolding',
          'Observation before action',
        ],
        isPrimary: false,
      },
      {
        id: 'q2',
        dateRange: `April - June ${currentYear}`,
        phaseName: 'Pressure Intensifies',
        whatsHappening: [
          'The same theme returns with more clarity',
          'External circumstances amplify internal tensions',
        ],
        whatThisCreates: [
          'Moments where avoidance becomes harder',
          'Relationships that mirror the core pattern',
        ],
        wherePeopleGetItWrong: [
          'Blaming external factors for internal resistance',
          'Acting from reactivity rather than intention',
        ],
        whatItsAskingOfYou: [
          'Honest acknowledgment of what keeps repeating',
          'The courage to name what you see',
        ],
        isPrimary: true,
      },
      {
        id: 'q3',
        dateRange: `July - September ${currentYear}`,
        phaseName: 'Critical Choice Window',
        whatsHappening: [
          'The pattern crystallizes into clear options',
          'What was theoretical becomes practical',
        ],
        whatThisCreates: [
          'A moment where the old way and new way are both visible',
          'Pressure to commit to a direction',
        ],
        wherePeopleGetItWrong: [
          'Choosing based on fear rather than clarity',
          'Waiting for perfect information that never comes',
        ],
        whatItsAskingOfYou: [
          'A decision that matches what you now understand',
          'Trust in the pattern you\'ve observed',
        ],
        isPrimary: true,
      },
      {
        id: 'q4',
        dateRange: `October - December ${currentYear}`,
        phaseName: 'Integration or Reset',
        whatsHappening: [
          'Consequences of earlier choices become visible',
          'The year\'s theme reaches resolution or recycles',
        ],
        whatThisCreates: [
          'Either: A sense of completion and earned clarity',
          'Or: Recognition that the pattern needs another cycle',
        ],
        wherePeopleGetItWrong: [
          'Rushing closure before it\'s natural',
          'Ignoring what the year tried to teach',
        ],
        whatItsAskingOfYou: [
          'Honest assessment of what changed',
          'Gratitude or acceptance, depending on what unfolded',
        ],
        isPrimary: false,
      },
    ];

    // Generate turning points
    const turningPoints: TurningPoint[] = [
      {
        id: 'tp1',
        date: `Late April ${currentYear}`,
        whyThisMatters: `The ${dominantPattern} pattern reaches a point where it can no longer be background noise. Something makes it undeniably present.`,
        whatBecomesClear: 'What you\'ve been tolerating and why. The real cost of the status quo.',
        whatHappensIfAvoided: 'The pattern intensifies in Q3. What could have been addressed early becomes a crisis later.',
      },
      {
        id: 'tp2',
        date: `Mid-August ${currentYear}`,
        whyThisMatters: 'This is the year\'s primary decision point. The options are clear. The information is sufficient. What remains is choice.',
        whatBecomesClear: 'Which direction aligns with who you\'re becoming, not just who you\'ve been.',
        whatHappensIfAvoided: 'The choice gets made for you by circumstances. You lose authorship of your own direction.',
      },
      {
        id: 'tp3',
        date: `Early November ${currentYear}`,
        whyThisMatters: 'The year\'s arc reaches its natural conclusion point. What was started is now ready to be named.',
        whatBecomesClear: 'Whether the year\'s lesson landed or needs to repeat.',
        whatHappensIfAvoided: 'You enter next year carrying what this year tried to resolve.',
      },
    ];

    // Generate decision windows
    const decisionWindows: DecisionWindow[] = [
      {
        id: 'dw1',
        dateRange: `March 15-31, ${currentYear}`,
        prompt: 'You can commit early. Or you can keep gathering information.',
        ifYouAct: 'You gain momentum but may need to correct course later.',
        ifYouWait: 'You gain clarity but may miss the window for certain options.',
      },
      {
        id: 'dw2',
        dateRange: `June 1-15, ${currentYear}`,
        prompt: 'You can have the difficult conversation. Or you can let it resolve itself.',
        ifYouAct: 'Short-term discomfort, long-term clarity. The relationship transforms.',
        ifYouWait: 'The tension remains but so does the relationship as it is. For now.',
      },
      {
        id: 'dw3',
        dateRange: `September 1-20, ${currentYear}`,
        prompt: 'You can lock in the new direction. Or you can preserve optionality.',
        ifYouAct: 'Commitment creates momentum. Doors close but others open.',
        ifYouWait: 'Flexibility remains but focus diffuses. Energy spreads thin.',
      },
    ];

    return {
      yearTheme,
      primaryArc,
      phases,
      turningPoints,
      decisionWindows,
    };
  } catch (error) {
    console.warn('[AstrologyTimeline] Failed to generate timeline data:', error);
    return null;
  }
}

// ============================================
// COMPONENT
// ============================================

export default function AstrologyTimelineSection({
  fullChartData,
  lifeChapterAnalysis,
  patternAnalysis,
  dominantTruth,
  activeAltitude,
  timelineData: providedTimelineData,
}: AstrologyTimelineSectionProps) {
  const { theme, isDark } = useTheme();
  const [expanded, setExpanded] = useState(false);
  const [expandedPhaseId, setExpandedPhaseId] = useState<string | null>(null);

  // Generate or use provided timeline data
  const timelineData = useMemo(() => {
    if (providedTimelineData) return providedTimelineData;
    return generateTimelineData(fullChartData, lifeChapterAnalysis, patternAnalysis, dominantTruth);
  }, [fullChartData, lifeChapterAnalysis, patternAnalysis, dominantTruth, providedTimelineData]);

  // Altitude-specific intro
  const altitudeIntro = useMemo(() => {
    switch (activeAltitude) {
      case 'today':
        return 'This sits inside a larger yearly pattern.';
      case 'week':
        return 'This week is part of a larger yearly unfolding.';
      case 'month':
        return 'This month makes more sense when you see the larger arc.';
      default:
        return '';
    }
  }, [activeAltitude]);

  const toggleExpand = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpanded(!expanded);
  };

  const togglePhase = (phaseId: string) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedPhaseId(expandedPhaseId === phaseId ? null : phaseId);
  };

  // DEBUG: Temporary visible fallback when no data
  if (!timelineData) {
    return (
      <View style={[styles.container, { position: 'relative' }]}>
        <View style={[styles.headerContainer, { borderColor: theme.border, backgroundColor: theme.surface }]}>
          <View style={styles.headerTextContainer}>
            <Text style={[styles.sectionTitle, { color: theme.text }]}>
              THE YEAR AS IT UNFOLDS
            </Text>
            <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>
              Timeline is loading or unavailable.
            </Text>
          </View>
          <Text style={{ position: 'absolute', top: 4, right: 8, fontSize: 8, color: theme.textTertiary }}>
            timeline mounted
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { position: 'relative' }]}>
      {/* DEBUG: Temporary marker */}
      <Text style={{ position: 'absolute', top: 4, right: 8, fontSize: 8, color: theme.textTertiary, zIndex: 10 }}>
        timeline mounted
      </Text>
      
      {/* Section Header - Always visible */}
      <TouchableOpacity
        style={[styles.headerContainer, { borderColor: theme.border }]}
        onPress={toggleExpand}
        activeOpacity={0.7}
      >
        <View style={styles.headerTextContainer}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            THE YEAR AS IT UNFOLDS
          </Text>
          <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>
            Where things build, break, and shift
          </Text>
        </View>
        <Text style={[styles.expandIcon, { color: theme.textSecondary }]}>
          {expanded ? '▴' : '▾'}
        </Text>
      </TouchableOpacity>

      {expanded && (
        <View style={[styles.contentContainer, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          {/* Altitude Intro */}
          <Text style={[styles.altitudeIntro, { color: theme.textTertiary }]}>
            {altitudeIntro}
          </Text>

          {/* Year Theme */}
          <View style={[styles.yearThemeCard, { backgroundColor: isDark ? 'rgba(139, 92, 246, 0.08)' : 'rgba(139, 92, 246, 0.05)', borderColor: Colors.accent + '30' }]}>
            <Text style={[styles.yearThemeLabel, { color: Colors.accent }]}>YEAR THEME</Text>
            <Text style={[styles.yearThemeText, { color: theme.text }]}>
              {timelineData.yearTheme}
            </Text>
          </View>

          {/* Primary Arc */}
          <View style={styles.primaryArcContainer}>
            <Text style={[styles.primaryArcLabel, { color: theme.textTertiary }]}>PRIMARY ARC</Text>
            <Text style={[styles.primaryArcText, { color: theme.textSecondary }]}>
              {timelineData.primaryArc}
            </Text>
          </View>

          {/* Key Phases */}
          <View style={styles.phasesContainer}>
            <Text style={[styles.phasesLabel, { color: theme.textTertiary }]}>KEY PHASES</Text>
            
            {timelineData.phases.map((phase) => (
              <TouchableOpacity
                key={phase.id}
                style={[
                  styles.phaseCard,
                  { 
                    backgroundColor: theme.surface, 
                    borderColor: phase.isPrimary ? Colors.accent + '40' : theme.border,
                    borderWidth: phase.isPrimary ? 1.5 : 1,
                  }
                ]}
                onPress={() => togglePhase(phase.id)}
                activeOpacity={0.8}
              >
                <View style={styles.phaseHeader}>
                  <View style={styles.phaseHeaderLeft}>
                    {phase.isPrimary && (
                      <Text style={[styles.primaryBadge, { color: Colors.accent }]}>⭐</Text>
                    )}
                    <View>
                      <Text style={[styles.phaseDateRange, { color: theme.textTertiary }]}>
                        {phase.dateRange}
                      </Text>
                      <Text style={[styles.phaseName, { color: theme.text }]}>
                        {phase.phaseName}
                      </Text>
                    </View>
                  </View>
                  <Text style={[styles.phaseExpandIcon, { color: theme.textSecondary }]}>
                    {expandedPhaseId === phase.id ? '−' : '+'}
                  </Text>
                </View>

                {expandedPhaseId === phase.id && (
                  <View style={styles.phaseDetails}>
                    <View style={styles.phaseSection}>
                      <Text style={[styles.phaseSectionTitle, { color: theme.textSecondary }]}>
                        What's actually happening
                      </Text>
                      {phase.whatsHappening.map((item, i) => (
                        <Text key={i} style={[styles.phaseBullet, { color: theme.text }]}>• {item}</Text>
                      ))}
                    </View>

                    <View style={styles.phaseSection}>
                      <Text style={[styles.phaseSectionTitle, { color: theme.textSecondary }]}>
                        What this tends to create
                      </Text>
                      {phase.whatThisCreates.map((item, i) => (
                        <Text key={i} style={[styles.phaseBullet, { color: theme.text }]}>• {item}</Text>
                      ))}
                    </View>

                    <View style={styles.phaseSection}>
                      <Text style={[styles.phaseSectionTitle, { color: '#FF6347' }]}>
                        Where people get it wrong
                      </Text>
                      {phase.wherePeopleGetItWrong.map((item, i) => (
                        <Text key={i} style={[styles.phaseBullet, { color: theme.textSecondary }]}>• {item}</Text>
                      ))}
                    </View>

                    <View style={styles.phaseSection}>
                      <Text style={[styles.phaseSectionTitle, { color: Colors.accent }]}>
                        What this phase is asking of you
                      </Text>
                      {phase.whatItsAskingOfYou.map((item, i) => (
                        <Text key={i} style={[styles.phaseBullet, { color: theme.text }]}>• {item}</Text>
                      ))}
                    </View>
                  </View>
                )}
              </TouchableOpacity>
            ))}
          </View>

          {/* Primary Turning Points */}
          <View style={styles.turningPointsContainer}>
            <Text style={[styles.turningPointsLabel, { color: theme.textTertiary }]}>
              ⭐ PRIMARY TURNING POINTS
            </Text>
            
            {timelineData.turningPoints.map((tp) => (
              <View
                key={tp.id}
                style={[styles.turningPointCard, { backgroundColor: isDark ? 'rgba(255, 215, 0, 0.06)' : 'rgba(255, 215, 0, 0.04)', borderColor: '#FFD70040' }]}
              >
                <Text style={[styles.turningPointDate, { color: '#DAA520' }]}>
                  ⭐ {tp.date}
                </Text>
                
                <View style={styles.turningPointSection}>
                  <Text style={[styles.turningPointSectionTitle, { color: theme.textSecondary }]}>
                    Why this matters
                  </Text>
                  <Text style={[styles.turningPointText, { color: theme.text }]}>
                    {tp.whyThisMatters}
                  </Text>
                </View>

                <View style={styles.turningPointSection}>
                  <Text style={[styles.turningPointSectionTitle, { color: theme.textSecondary }]}>
                    What becomes clear
                  </Text>
                  <Text style={[styles.turningPointText, { color: theme.text }]}>
                    {tp.whatBecomesClear}
                  </Text>
                </View>

                <View style={styles.turningPointSection}>
                  <Text style={[styles.turningPointSectionTitle, { color: '#FF6347' }]}>
                    What happens if avoided
                  </Text>
                  <Text style={[styles.turningPointText, { color: theme.textSecondary }]}>
                    {tp.whatHappensIfAvoided}
                  </Text>
                </View>
              </View>
            ))}
          </View>

          {/* Decision Windows */}
          <View style={styles.decisionWindowsContainer}>
            <Text style={[styles.decisionWindowsLabel, { color: theme.textTertiary }]}>
              DECISION WINDOWS
            </Text>
            
            {timelineData.decisionWindows.map((dw) => (
              <View
                key={dw.id}
                style={[styles.decisionWindowCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
              >
                <Text style={[styles.decisionWindowDateRange, { color: theme.textTertiary }]}>
                  {dw.dateRange}
                </Text>
                
                <Text style={[styles.decisionWindowPrompt, { color: theme.text }]}>
                  "{dw.prompt}"
                </Text>

                <View style={styles.decisionOutcomes}>
                  <View style={[styles.decisionOutcome, { backgroundColor: isDark ? 'rgba(76, 175, 80, 0.1)' : 'rgba(76, 175, 80, 0.05)' }]}>
                    <Text style={[styles.decisionOutcomeLabel, { color: '#4CAF50' }]}>If you act →</Text>
                    <Text style={[styles.decisionOutcomeText, { color: theme.textSecondary }]}>{dw.ifYouAct}</Text>
                  </View>
                  <View style={[styles.decisionOutcome, { backgroundColor: isDark ? 'rgba(255, 152, 0, 0.1)' : 'rgba(255, 152, 0, 0.05)' }]}>
                    <Text style={[styles.decisionOutcomeLabel, { color: '#FF9800' }]}>If you wait →</Text>
                    <Text style={[styles.decisionOutcomeText, { color: theme.textSecondary }]}>{dw.ifYouWait}</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        </View>
      )}
    </View>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    marginTop: 16,
    marginBottom: 16,
  },
  headerContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderRadius: 12,
  },
  headerTextContainer: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  sectionSubtitle: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: 2,
  },
  expandIcon: {
    fontSize: 16,
    marginLeft: 12,
  },
  contentContainer: {
    marginTop: 8,
    padding: 16,
    borderWidth: 1,
    borderRadius: 12,
  },
  altitudeIntro: {
    fontSize: 14,
    fontStyle: 'italic',
    marginBottom: 16,
  },
  
  // Year Theme
  yearThemeCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 16,
  },
  yearThemeLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 14,
  },
  yearThemeText: {
    fontSize: 17,
    lineHeight: 30,
    fontWeight: '500',
  },

  // Primary Arc
  primaryArcContainer: {
    marginBottom: 20,
  },
  primaryArcLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 14,
  },
  primaryArcText: {
    fontSize: 16,
    lineHeight: 30,
  },

  // Phases
  phasesContainer: {
    marginBottom: 20,
  },
  phasesLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  phaseCard: {
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 14,
    overflow: 'hidden',
  },
  phaseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
  },
  phaseHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  primaryBadge: {
    fontSize: 16,
    marginRight: 8,
  },
  phaseDateRange: {
    fontSize: 14,
  },
  phaseName: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 2,
  },
  phaseExpandIcon: {
    fontSize: 22,
    fontWeight: '300',
  },
  phaseDetails: {
    paddingHorizontal: 12,
    paddingBottom: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(0,0,0,0.1)',
    paddingTop: 12,
  },
  phaseSection: {
    marginBottom: 16,
  },
  phaseSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  phaseBullet: {
    fontSize: 16,
    lineHeight: 32,
    marginLeft: 4,
  },

  // Turning Points
  turningPointsContainer: {
    marginBottom: 20,
  },
  turningPointsLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  turningPointCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 14,
  },
  turningPointDate: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 16,
  },
  turningPointSection: {
    marginBottom: 14,
  },
  turningPointSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 3,
  },
  turningPointText: {
    fontSize: 16,
    lineHeight: 32,
  },

  // Decision Windows
  decisionWindowsContainer: {
    marginBottom: 14,
  },
  decisionWindowsLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 16,
  },
  decisionWindowCard: {
    padding: 14,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 14,
  },
  decisionWindowDateRange: {
    fontSize: 14,
    marginBottom: 6,
  },
  decisionWindowPrompt: {
    fontSize: 16,
    fontStyle: 'italic',
    fontWeight: '500',
    marginBottom: 16,
  },
  decisionOutcomes: {
    gap: 8,
  },
  decisionOutcome: {
    padding: 10,
    borderRadius: 8,
  },
  decisionOutcomeLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 3,
  },
  decisionOutcomeText: {
    fontSize: 14,
    lineHeight: 17,
  },
});
