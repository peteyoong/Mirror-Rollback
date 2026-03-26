/**
 * ActionCard - "What to do next" card for Directive mode
 * 
 * Provides clear, actionable guidance derived from the daily pattern.
 * Only shown in directive mode when users want structured, action-oriented content.
 * 
 * NOW: Uses pattern-family derived actions from backend instead of generic templates.
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import api from '../services/api';

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

// Fallback action derivation (only used if backend doesn't provide action_guidance)
const deriveActionFromPattern = (patternTitle: string): ActionData => {
  const title = patternTitle.toLowerCase();
  
  // Pattern-family specific fallbacks
  if (title.includes('pause') || title.includes('stall') || title.includes('waiting')) {
    return {
      action: 'Name the one thing that would let you move, even slightly.',
      context: 'The block is rarely everything—it\'s usually one specific thing.',
      timeframe: 'today',
      cta: 'Name the block',
    };
  }
  
  if (title.includes('forward') || title.includes('back') || title.includes('push')) {
    return {
      action: 'Identify the one decision underneath this back-and-forth.',
      context: 'The push-pull often masks a simpler question you\'re avoiding.',
      timeframe: 'today',
      cta: 'Name the real decision',
    };
  }
  
  if (title.includes('unsaid') || title.includes('holding back') || title.includes('silent')) {
    return {
      action: 'Decide: is this something to say, or something to release?',
      context: 'You can choose silence intentionally, rather than by default.',
      timeframe: 'today',
      cta: 'Choose your silence',
    };
  }
  
  if (title.includes('grip') || title.includes('release') || title.includes('control')) {
    return {
      action: 'Name one thing you\'re trying to control that isn\'t yours to control.',
      context: 'Releasing that frees energy for what you can actually influence.',
      timeframe: 'today',
      cta: 'Identify what to release',
    };
  }
  
  if (title.includes('search') || title.includes('clarity') || title.includes('fog') || title.includes('processing')) {
    return {
      action: 'Make one small decision without waiting for full clarity.',
      context: 'Progress creates clarity faster than waiting for it.',
      timeframe: 'today',
      cta: 'Decide one thing now',
    };
  }
  
  if (title.includes('moving') || title.includes('forward')) {
    return {
      action: 'Pick the single most important thing to move on today.',
      context: 'Forward momentum works best with focus.',
      timeframe: 'today',
      cta: 'Choose one priority',
    };
  }
  
  if (title.includes('letting go')) {
    return {
      action: 'Decide what to do with the space you\'ve created.',
      context: 'Letting go is step one. Choosing what comes next is step two.',
      timeframe: 'today',
      cta: 'Choose what\'s next',
    };
  }
  
  // Default fallback - still pattern-aware
  return {
    action: 'Identify one thing you can decide or do today.',
    context: 'Even small actions create momentum.',
    timeframe: 'today',
    cta: 'Take one step',
  };
};

export default function ActionCard({ userId, theme, patternTitle }: ActionCardProps) {
  const router = useRouter();
  const [actionData, setActionData] = useState<ActionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchPatternAndDeriveAction();
  }, [userId]);

  const fetchPatternAndDeriveAction = async () => {
    try {
      const response = await api.get(`/today-pattern/${userId}`);
      
      // PRIORITY: Use backend-provided action_guidance if available
      if (response.data?.action_guidance) {
        const guidance = response.data.action_guidance;
        setActionData({
          action: guidance.action || 'Identify one thing you can decide or do today.',
          context: guidance.context || 'Even small actions create momentum.',
          timeframe: guidance.timeframe || 'today',
          cta: guidance.cta || 'Take one step',
        });
      } else if (response.data?.title) {
        // Fallback: Derive from title using pattern-family mapping
        const action = deriveActionFromPattern(response.data.title);
        setActionData(action);
      } else {
        setActionData(deriveActionFromPattern(''));
      }
    } catch (error) {
      console.error('[ActionCard] Error fetching pattern:', error);
      setActionData(deriveActionFromPattern(patternTitle || ''));
    } finally {
      setIsLoading(false);
    }
  };

  const handleTakeStep = () => {
    // Navigate to reflect with action context
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
      
      {/* Action */}
      <Text style={[styles.action, { color: theme.text }]}>
        {actionData.action}
      </Text>
      
      {/* Context */}
      <Text style={[styles.context, { color: theme.textSecondary }]}>
        {actionData.context}
      </Text>
      
      {/* Timeframe badge */}
      <View style={[styles.timeframeBadge, { backgroundColor: theme.accent + '15' }]}>
        <Text style={[styles.timeframeText, { color: theme.accent }]}>
          {getTimeframeLabel(actionData.timeframe)}
        </Text>
      </View>
      
      {/* CTA - Now uses pattern-specific CTA text */}
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
