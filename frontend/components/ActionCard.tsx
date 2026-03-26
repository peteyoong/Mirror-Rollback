/**
 * ActionCard - "What to do next" card for Directive mode
 * 
 * Provides clear, actionable guidance derived from the daily pattern.
 * Only shown in directive mode when users want structured, action-oriented content.
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
}

// Generate action from pattern (derived locally for now)
const deriveActionFromPattern = (patternTitle: string): ActionData => {
  // Simple keyword-based action derivation
  const title = patternTitle.toLowerCase();
  
  if (title.includes('decision') || title.includes('choice')) {
    return {
      action: 'Write down one decision you need to make today.',
      context: 'Clarity comes from naming what needs attention.',
      timeframe: 'today',
    };
  }
  
  if (title.includes('tension') || title.includes('conflict')) {
    return {
      action: 'Identify one thing you can let go of.',
      context: 'Not everything needs resolution right now.',
      timeframe: 'today',
    };
  }
  
  if (title.includes('energy') || title.includes('tired') || title.includes('rest')) {
    return {
      action: 'Schedule 15 minutes of uninterrupted quiet.',
      context: 'Rest is productive when you need it.',
      timeframe: 'now',
    };
  }
  
  if (title.includes('growth') || title.includes('change') || title.includes('shift')) {
    return {
      action: 'Name one small step you can take this week.',
      context: 'Progress is built one action at a time.',
      timeframe: 'this_week',
    };
  }
  
  if (title.includes('relationship') || title.includes('connection')) {
    return {
      action: 'Reach out to someone you have been meaning to contact.',
      context: 'Connection starts with a single message.',
      timeframe: 'today',
    };
  }
  
  // Default action
  return {
    action: 'Take 5 minutes to write down what is on your mind.',
    context: 'Sometimes clarity starts with simply naming what is present.',
    timeframe: 'now',
  };
};

export default function ActionCard({ userId, theme, patternTitle }: ActionCardProps) {
  const router = useRouter();
  const [actionData, setActionData] = useState<ActionData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (patternTitle) {
      const action = deriveActionFromPattern(patternTitle);
      setActionData(action);
      setIsLoading(false);
    } else {
      // Fetch pattern to derive action
      fetchPatternAndDeriveAction();
    }
  }, [patternTitle, userId]);

  const fetchPatternAndDeriveAction = async () => {
    try {
      const response = await api.get(`/today-pattern/${userId}`);
      if (response.data?.title) {
        const action = deriveActionFromPattern(response.data.title);
        setActionData(action);
      } else {
        setActionData(deriveActionFromPattern(''));
      }
    } catch (error) {
      console.error('[ActionCard] Error fetching pattern:', error);
      setActionData(deriveActionFromPattern(''));
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
      
      {/* CTA */}
      <TouchableOpacity
        style={[styles.ctaButton, { backgroundColor: theme.accent + '20', borderColor: theme.accent + '40' }]}
        onPress={handleTakeStep}
        activeOpacity={0.7}
      >
        <Text style={[styles.ctaText, { color: theme.text }]}>Take one step</Text>
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
