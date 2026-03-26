/**
 * ActionCard - "What to do next" card for Directive mode
 * 
 * DIAGNOSIS-ALIGNED: Derives actions from the pattern diagnosis, not generic templates.
 * Only shown in directive mode when users want structured, action-oriented content.
 * 
 * Uses `/api/pattern-diagnosis/{user_id}` for:
 * - what_would_be_wise
 * - moment_type
 * - constitution.recurring_failure_mode
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { getPatternDiagnosis, PatternDiagnosisResponse } from '../services/api';

interface ActionCardProps {
  userId: string;
  theme: any;
  patternTitle?: string;
}

interface ActionData {
  action: string;
  context: string;
  timeframe: 'now' | 'today' | 'this_week';
  cta: string;
}

export default function ActionCard({ userId, theme }: ActionCardProps) {
  const router = useRouter();
  const [diagnosis, setDiagnosis] = useState<PatternDiagnosisResponse | null>(null);
  const [actionData, setActionData] = useState<ActionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDiagnosisAndDeriveAction();
  }, [userId]);

  const fetchDiagnosisAndDeriveAction = async () => {
    try {
      const diagnosisResponse = await getPatternDiagnosis(userId);
      setDiagnosis(diagnosisResponse);
      
      // Derive action from diagnosis
      const action = deriveActionFromDiagnosis(diagnosisResponse);
      setActionData(action);
    } catch (error) {
      console.error('[ActionCard] Error:', error);
      // Fallback
      setActionData({
        action: 'Identify one thing you can decide or do today.',
        context: 'Even small actions create momentum.',
        timeframe: 'today',
        cta: 'Take one step',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const deriveActionFromDiagnosis = (diag: PatternDiagnosisResponse): ActionData => {
    const momentType = diag.moment_type;
    const failureMode = diag.constitution?.recurring_failure_mode || '';
    
    // Moment-type specific actions derived from diagnosis
    const momentActions: Record<string, ActionData> = {
      premature_initiation: {
        action: 'Before acting, answer: What is this pause protecting?',
        context: diag.what_would_be_wise || 'The drive is real, but the field may not be ready.',
        timeframe: 'today',
        cta: 'Clarify what is blocking',
      },
      pause_stall: {
        action: 'Name the one thing that would let you move, even slightly.',
        context: 'The pause exists because something hasn\'t landed—identifying it matters more than pushing through.',
        timeframe: 'today',
        cta: 'Name the block',
      },
      threshold_moment: {
        action: 'Decide: are you ready to cross this threshold?',
        context: 'This is a real crossroads. The question isn\'t whether to cross—it\'s whether you\'re clear about what you\'re crossing into.',
        timeframe: 'today',
        cta: 'Face the threshold',
      },
      overreach_risk: {
        action: 'Identify one thing you could stop trying to control.',
        context: 'The urge to force resolution could create more problems than it solves.',
        timeframe: 'today',
        cta: 'Release one thing',
      },
      unresolved_wave: {
        action: 'Wait for emotional neutrality before deciding.',
        context: 'If you\'re still in the wave—high or low—your view is distorted. The truth lives in the middle.',
        timeframe: 'today',
        cta: 'Wait for neutral',
      },
      structure_not_ready: {
        action: 'Name one foundation element that needs strengthening.',
        context: 'The intention is right. The structure isn\'t. Build before pushing.',
        timeframe: 'today',
        cta: 'Strengthen one thing',
      },
      clean_initiation: {
        action: 'Choose one thing to act on today.',
        context: 'This is as clean as initiation gets. If you\'ve been waiting for a signal—this is closer to it.',
        timeframe: 'today',
        cta: 'Act now',
      },
      consolidation: {
        action: 'Identify what needs more foundation before the next push.',
        context: 'Build now, push later. Use this quieter moment to strengthen what will support the next move.',
        timeframe: 'this_week',
        cta: 'Build foundation',
      },
      forcing_window: {
        action: 'Decide: ride this momentum or let it pass?',
        context: 'The timing is creating pressure. The question is whether this force is aligned with what you actually want.',
        timeframe: 'now',
        cta: 'Decide now',
      },
      review_recalibration: {
        action: 'Review one assumption you\'ve been operating on.',
        context: 'This is a recalibration moment. The timing supports review and adjustment, not forward push.',
        timeframe: 'today',
        cta: 'Review one thing',
      },
    };

    // Use moment-specific action if available
    if (momentType && momentActions[momentType]) {
      const action = momentActions[momentType];
      
      // If we have a specific failure mode, add context
      if (failureMode && failureMode.includes('moving before')) {
        action.context = `Watch for your pattern: ${failureMode}. ${action.context}`;
      }
      
      return action;
    }

    // Fallback using what_would_be_wise from diagnosis
    if (diag.what_would_be_wise) {
      return {
        action: diag.what_would_be_wise.split('.')[0] + '.',
        context: diag.what_is_happening || 'Something is surfacing that wants attention.',
        timeframe: 'today',
        cta: 'Take one step',
      };
    }

    // Ultimate fallback
    return {
      action: 'Identify one thing you can decide or do today.',
      context: 'Even small actions create momentum.',
      timeframe: 'today',
      cta: 'Take one step',
    };
  };

  const handleTakeStep = () => {
    router.push('/(tabs)/reflect?view=mirror');
  };

  const getTimeframeLabel = (timeframe: string) => {
    switch (timeframe) {
      case 'now': return 'Right now';
      case 'today': return 'Today';
      case 'this_week': return 'This week';
      default: return 'When ready';
    }
  };

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
        </View>
      </View>
    );
  }

  if (!actionData) return null;

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      {/* Label */}
      <Text style={[styles.label, { color: theme.textTertiary }]}>WHAT TO DO NEXT</Text>
      
      {/* Action - derived from diagnosis */}
      <Text style={[styles.action, { color: theme.text }]}>
        {actionData.action}
      </Text>
      
      {/* Context - from diagnosis */}
      <Text style={[styles.context, { color: theme.textSecondary }]}>
        {actionData.context}
      </Text>
      
      {/* Timeframe badge */}
      <View style={[styles.timeframeBadge, { backgroundColor: theme.accent + '15' }]}>
        <Text style={[styles.timeframeText, { color: theme.accent }]}>
          {getTimeframeLabel(actionData.timeframe)}
        </Text>
      </View>
      
      {/* CTA - diagnosis-aligned */}
      <TouchableOpacity
        style={[styles.ctaButton, { backgroundColor: theme.accent + '20', borderColor: theme.accent + '40' }]}
        onPress={handleTakeStep}
        activeOpacity={0.7}
      >
        <Text style={[styles.ctaText, { color: theme.text }]}>{actionData.cta}</Text>
        <Text style={[styles.ctaArrow, { color: theme.textTertiary }]}>→</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  loadingContainer: {
    paddingVertical: 30,
    alignItems: 'center',
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  action: {
    fontSize: 17,
    fontWeight: '600',
    lineHeight: 24,
    marginBottom: 8,
  },
  context: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 14,
    fontStyle: 'italic',
  },
  timeframeBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 16,
  },
  timeframeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
  },
  ctaText: {
    fontSize: 15,
    fontWeight: '600',
  },
  ctaArrow: {
    fontSize: 16,
    fontWeight: '400',
  },
});
