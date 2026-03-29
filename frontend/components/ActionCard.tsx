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
    
    // Moment-type specific actions derived from diagnosis (Scene-specific language)
    const momentActions: Record<string, ActionData> = {
      premature_initiation: {
        action: 'Before you close this, name what still doesn\'t sit right.',
        context: diag.what_would_be_wise || 'The drive is real—but the target isn\'t ready.',
        timeframe: 'today',
        cta: 'Name what\'s unresolved',
      },
      pause_stall: {
        action: 'Name the one thing that would let you move—even slightly.',
        context: 'Something in you hasn\'t landed. Identifying it matters more than pushing through.',
        timeframe: 'today',
        cta: 'Name what\'s stuck',
      },
      threshold_moment: {
        action: 'Before crossing, name what you\'re leaving and what you\'re walking into.',
        context: 'This is a real threshold. The question isn\'t whether to cross—it\'s whether you\'re clear about what changes.',
        timeframe: 'today',
        cta: 'Name both sides',
      },
      overreach_risk: {
        action: 'Identify one thing you could stop trying to control.',
        context: 'Sitting in discomfort is hard—but collapsing it prematurely will just make you revisit it later.',
        timeframe: 'today',
        cta: 'Release one thing',
      },
      unresolved_wave: {
        action: 'Wait for neutral before deciding.',
        context: 'You\'re trying to decide while still in the wave. Clarity will come—but not while you\'re high or low.',
        timeframe: 'today',
        cta: 'Wait for neutral',
      },
      structure_not_ready: {
        action: 'Name one thing that needs building before you push forward.',
        context: 'The intention is clear. The foundation isn\'t. Build what\'s missing first.',
        timeframe: 'today',
        cta: 'Build one thing',
      },
      clean_initiation: {
        action: 'Choose one thing to act on today.',
        context: 'This is as clean a window as you\'ll get. If you\'ve been waiting for a signal—this is closer to it.',
        timeframe: 'today',
        cta: 'Move now',
      },
      consolidation: {
        action: 'Identify what needs strengthening before the next push.',
        context: 'Build now, push later. Strengthen what you\'re standing on.',
        timeframe: 'this_week',
        cta: 'Strengthen foundation',
      },
      forcing_window: {
        action: 'Decide: are you moving toward something—or away from discomfort?',
        context: 'There\'s momentum here. The question is whether it\'s aligned with what you actually want.',
        timeframe: 'now',
        cta: 'Name the direction',
      },
      review_recalibration: {
        action: 'Name one assumption you\'ve been operating on that might be off.',
        context: 'This is a moment for review, not resolution. Stop trying to figure it out—let the answer find you.',
        timeframe: 'today',
        cta: 'Question one thing',
      },
    };

    // Use moment-specific action if available
    if (momentType && momentActions[momentType]) {
      const action = momentActions[momentType];
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
