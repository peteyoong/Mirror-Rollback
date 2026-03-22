/**
 * AstrologyTimelineTab.tsx
 * 
 * "THE YEAR AS IT UNFOLDS"
 * Dedicated tab for yearly strategic timeline view
 * 
 * This shows a Master Astrologer level view of the year's arc.
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
  ScrollView,
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

interface TimelinePhase {
  id: string;
  dateRange: string;
  phaseName: string;
  whatsHappening: string[];
  whatThisCreates: string[];
  wherePeopleGetItWrong: string[];
  whatItsAskingOfYou: string[];
  isPrimary?: boolean;
}

interface TurningPoint {
  id: string;
  date: string;
  whyThisMatters: string;
  whatBecomesClear: string;
  whatHappensIfAvoided: string;
}

interface DecisionWindow {
  id: string;
  dateRange: string;
  prompt: string;
  ifYouAct: string;
  ifYouWait: string;
}

interface TimelineData {
  yearTheme: string;
  primaryArc: string;
  phases: TimelinePhase[];
  turningPoints: TurningPoint[];
  decisionWindows: DecisionWindow[];
}

interface AstrologyTimelineTabProps {
  fullChartData: FullChartData | null;
  theme: any;
  onOpenChat: () => void;
}

// ============================================
// TIMELINE DATA GENERATOR
// ============================================

function generateTimelineData(
  fullChartData: FullChartData | null
): TimelineData {
  const planets = fullChartData?.natal?.planets || {};
  const sunSign = planets.Sun?.sign || 'Aries';
  
  const currentYear = new Date().getFullYear();
  
  // Default pattern based on sun sign
  const dominantPattern = sunSign === 'Aries' ? 'urgency vs patience' :
                          sunSign === 'Taurus' ? 'holding vs releasing' :
                          sunSign === 'Gemini' ? 'scattered vs focused' :
                          sunSign === 'Cancer' ? 'protecting vs opening' :
                          sunSign === 'Leo' ? 'performing vs being' :
                          sunSign === 'Virgo' ? 'fixing vs accepting' :
                          sunSign === 'Libra' ? 'pleasing vs choosing' :
                          sunSign === 'Scorpio' ? 'controlling vs trusting' :
                          sunSign === 'Sagittarius' ? 'escaping vs committing' :
                          sunSign === 'Capricorn' ? 'working vs resting' :
                          sunSign === 'Aquarius' ? 'detaching vs connecting' :
                          'absorbing vs protecting';

  const yearTheme = `This is a year where the tension between ${dominantPattern} keeps returning until you learn to hold both.`;
  
  const primaryArc = `Across the year, you'll notice the same pattern appearing in different contexts—${dominantPattern}. Each time it shows up, the question gets clearer. The year isn't trying to break this pattern. It's teaching you to work with it consciously.`;

  const phases: TimelinePhase[] = [
    {
      id: 'q1',
      dateRange: `January - March ${currentYear}`,
      phaseName: 'Seeds and Signals',
      whatsHappening: [
        'The year\'s dominant pattern begins to emerge',
        'Early signals you might dismiss or overlook',
      ],
      whatThisCreates: [
        'A subtle sense that something familiar is returning',
        'Opportunities to catch the pattern early',
      ],
      wherePeopleGetItWrong: [
        'Treating early signals as isolated incidents',
        'Missing the connection between different situations',
      ],
      whatItsAskingOfYou: [
        'Pay attention to what keeps coming up',
        'Notice without rushing to fix',
      ],
      isPrimary: false,
    },
    {
      id: 'q2',
      dateRange: `April - June ${currentYear}`,
      phaseName: 'Pressure Builds',
      whatsHappening: [
        'The pattern becomes harder to ignore',
        'External situations mirror internal tensions',
      ],
      whatThisCreates: [
        'Moments of discomfort that demand attention',
        'Choices that feel more consequential',
      ],
      wherePeopleGetItWrong: [
        'Blaming circumstances instead of seeing the pattern',
        'Making reactive decisions to escape discomfort',
      ],
      whatItsAskingOfYou: [
        'Acknowledge what you\'ve been avoiding',
        'Choose from clarity, not reactivity',
      ],
      isPrimary: true,
    },
    {
      id: 'q3',
      dateRange: `July - September ${currentYear}`,
      phaseName: 'The Crossroads',
      whatsHappening: [
        'The year\'s central choice becomes visible',
        'Old patterns and new possibilities coexist',
      ],
      whatThisCreates: [
        'A clear before/after moment',
        'The weight of choosing a direction',
      ],
      wherePeopleGetItWrong: [
        'Waiting for certainty that never comes',
        'Choosing based on fear instead of alignment',
      ],
      whatItsAskingOfYou: [
        'Make the choice you\'ve been preparing for',
        'Trust what you\'ve learned this year',
      ],
      isPrimary: true,
    },
    {
      id: 'q4',
      dateRange: `October - December ${currentYear}`,
      phaseName: 'Integration',
      whatsHappening: [
        'The consequences of earlier choices become visible',
        'The year\'s lessons start to settle',
      ],
      whatThisCreates: [
        'Either: Earned clarity and new capacity',
        'Or: Recognition that the lesson needs another cycle',
      ],
      wherePeopleGetItWrong: [
        'Forcing closure before it\'s ready',
        'Dismissing what the year tried to teach',
      ],
      whatItsAskingOfYou: [
        'Honest inventory of what changed',
        'Gratitude for growth, acceptance for what remains',
      ],
      isPrimary: false,
    },
  ];

  const turningPoints: TurningPoint[] = [
    {
      id: 'tp1',
      date: `Late April ${currentYear}`,
      whyThisMatters: 'The pattern you\'ve been tolerating becomes impossible to ignore. Something makes it undeniably present.',
      whatBecomesClear: 'What you\'ve been tolerating and why. The real cost of continuing as you have been.',
      whatHappensIfAvoided: 'The pattern intensifies. What could be addressed now becomes a crisis later.',
    },
    {
      id: 'tp2',
      date: `Mid-August ${currentYear}`,
      whyThisMatters: 'This is the year\'s primary decision point. The options are clear. The information is sufficient.',
      whatBecomesClear: 'Which direction aligns with who you\'re becoming, not just who you\'ve been.',
      whatHappensIfAvoided: 'The choice gets made for you by circumstances. You lose authorship of your own direction.',
    },
    {
      id: 'tp3',
      date: `Early November ${currentYear}`,
      whyThisMatters: 'The year\'s arc reaches its natural conclusion point. What was started is ready to be named.',
      whatBecomesClear: 'Whether the year\'s lesson landed or needs to repeat.',
      whatHappensIfAvoided: 'You enter next year carrying what this year tried to resolve.',
    },
  ];

  const decisionWindows: DecisionWindow[] = [
    {
      id: 'dw1',
      dateRange: `March 15-31, ${currentYear}`,
      prompt: 'You can commit early. Or you can keep gathering information.',
      ifYouAct: 'You gain momentum but may need to adjust course later.',
      ifYouWait: 'You gain clarity but certain options may no longer be available.',
    },
    {
      id: 'dw2',
      dateRange: `June 1-15, ${currentYear}`,
      prompt: 'You can have the conversation you\'ve been avoiding. Or you can let things continue.',
      ifYouAct: 'Short-term discomfort, long-term clarity. Something transforms.',
      ifYouWait: 'The tension remains but so does the situation. For now.',
    },
    {
      id: 'dw3',
      dateRange: `September 1-20, ${currentYear}`,
      prompt: 'You can lock in the new direction. Or you can preserve your options.',
      ifYouAct: 'Commitment creates momentum. Some doors close, others open.',
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
}

// ============================================
// COMPONENT
// ============================================

export default function AstrologyTimelineTab({
  fullChartData,
  theme,
  onOpenChat,
}: AstrologyTimelineTabProps) {
  const { isDark } = useTheme();
  const [expandedPhaseId, setExpandedPhaseId] = useState<string | null>(null);

  // Generate timeline data
  const timelineData = useMemo(() => {
    return generateTimelineData(fullChartData);
  }, [fullChartData]);

  const togglePhase = (phaseId: string) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setExpandedPhaseId(expandedPhaseId === phaseId ? null : phaseId);
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerContainer}>
        <Text style={[styles.headerTitle, { color: theme.text }]}>
          THE YEAR AS IT UNFOLDS
        </Text>
        <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]}>
          Where things build, break, and shift
        </Text>
        <Text style={[styles.headerHelper, { color: theme.textSecondary }]}>
          This is the longer arc behind what you're experiencing day to day.
        </Text>
      </View>

      {/* Year Theme */}
      <View style={[styles.yearThemeCard, { backgroundColor: isDark ? 'rgba(139, 92, 246, 0.08)' : 'rgba(139, 92, 246, 0.05)', borderColor: Colors.accent + '30' }]}>
        <Text style={[styles.yearThemeLabel, { color: Colors.accent }]}>YEAR THEME</Text>
        <Text style={[styles.yearThemeText, { color: theme.text }]}>
          {timelineData.yearTheme}
        </Text>
      </View>

      {/* Primary Arc */}
      <View style={styles.primaryArcContainer}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>PRIMARY ARC</Text>
        <Text style={[styles.primaryArcText, { color: theme.textSecondary }]}>
          {timelineData.primaryArc}
        </Text>
      </View>

      {/* Key Phases */}
      <View style={styles.phasesContainer}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>KEY PHASES</Text>
        
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
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
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
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
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

      {/* Ask Mirror Button */}
      <TouchableOpacity
        style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
        onPress={onOpenChat}
      >
        <Text style={{ fontSize: 16, color: theme.background }}>💬</Text>
        <Text style={[styles.askMirrorText, { color: theme.background }]}>Ask about this year</Text>
      </TouchableOpacity>
    </View>
  );
}

// ============================================
// STYLES
// ============================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  headerContainer: {
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 8,
  },
  headerHelper: {
    fontSize: 12,
    lineHeight: 18,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 12,
  },
  
  // Year Theme
  yearThemeCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 20,
  },
  yearThemeLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  yearThemeText: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '500',
  },

  // Primary Arc
  primaryArcContainer: {
    marginBottom: 24,
  },
  primaryArcText: {
    fontSize: 14,
    lineHeight: 22,
  },

  // Phases
  phasesContainer: {
    marginBottom: 24,
  },
  phaseCard: {
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
    overflow: 'hidden',
  },
  phaseHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
  },
  phaseHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  primaryBadge: {
    fontSize: 14,
    marginRight: 10,
  },
  phaseDateRange: {
    fontSize: 11,
  },
  phaseName: {
    fontSize: 15,
    fontWeight: '600',
    marginTop: 2,
  },
  phaseExpandIcon: {
    fontSize: 20,
    fontWeight: '300',
  },
  phaseDetails: {
    paddingHorizontal: 14,
    paddingBottom: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(0,0,0,0.1)',
    paddingTop: 14,
  },
  phaseSection: {
    marginBottom: 14,
  },
  phaseSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 6,
  },
  phaseBullet: {
    fontSize: 13,
    lineHeight: 20,
    marginLeft: 4,
    marginBottom: 2,
  },

  // Turning Points
  turningPointsContainer: {
    marginBottom: 24,
  },
  turningPointCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  turningPointDate: {
    fontSize: 14,
    fontWeight: '700',
    marginBottom: 14,
  },
  turningPointSection: {
    marginBottom: 12,
  },
  turningPointSectionTitle: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 4,
  },
  turningPointText: {
    fontSize: 13,
    lineHeight: 20,
  },

  // Decision Windows
  decisionWindowsContainer: {
    marginBottom: 24,
  },
  decisionWindowCard: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 12,
  },
  decisionWindowDateRange: {
    fontSize: 11,
    marginBottom: 8,
  },
  decisionWindowPrompt: {
    fontSize: 15,
    fontStyle: 'italic',
    fontWeight: '500',
    marginBottom: 14,
  },
  decisionOutcomes: {
    gap: 10,
  },
  decisionOutcome: {
    padding: 12,
    borderRadius: 8,
  },
  decisionOutcomeLabel: {
    fontSize: 11,
    fontWeight: '600',
    marginBottom: 4,
  },
  decisionOutcomeText: {
    fontSize: 13,
    lineHeight: 18,
  },

  // Ask Mirror Button
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    marginTop: 8,
    marginBottom: 40,
  },
  askMirrorText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
