/**
 * DecisionAwareness Component
 * 
 * Displays the user's detected decision style and a reflective prompt
 * to help them become aware of their decision tendencies.
 * 
 * Design: Reflective, non-directive, observational
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

// =============================================================================
// TYPES
// =============================================================================

export interface DecisionAwarenessData {
  style: string;
  style_display: string;
  prompt: string;
  confidence: number;
  source_year?: number;
}

interface DecisionAwarenessProps {
  awareness: DecisionAwarenessData;
}

// =============================================================================
// STYLE ICONS
// =============================================================================

const STYLE_ICONS: Record<string, string> = {
  pause_and_wait: '⏸',
  bold_leap: '🚀',
  withdraw: '🚪',
  speak_up: '💬',
  pivot: '↩️',
  commit: '🎯',
  restructure: '🔧',
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function DecisionAwareness({ awareness }: DecisionAwarenessProps) {
  const { theme } = useTheme();
  
  if (!awareness || !awareness.prompt) {
    return null;
  }
  
  const icon = STYLE_ICONS[awareness.style] || '💡';
  
  // Split the prompt into lines for better formatting
  const promptLines = awareness.prompt.split('\n').filter(line => line.trim());
  
  return (
    <View style={styles.container}>
      {/* Style Badge */}
      <View style={[styles.styleBadge, { backgroundColor: 'rgba(139, 92, 246, 0.1)' }]}>
        <Text style={styles.styleIcon}>{icon}</Text>
        <Text style={[styles.styleText, { color: '#8B5CF6' }]}>
          {awareness.style_display}
        </Text>
      </View>
      
      {/* Reflective Prompt */}
      <View style={[styles.promptCard, { borderColor: theme.border }]}>
        {promptLines.map((line, index) => (
          <Text 
            key={index} 
            style={[
              styles.promptText, 
              { color: theme.textSecondary },
              index > 0 && styles.promptSecondLine
            ]}
          >
            {line}
          </Text>
        ))}
      </View>
      
      {/* Confidence indicator */}
      {awareness.confidence > 0 && (
        <View style={styles.confidenceContainer}>
          <View style={[styles.confidenceBar, { backgroundColor: theme.border }]}>
            <View 
              style={[
                styles.confidenceFill, 
                { width: `${awareness.confidence * 100}%`, backgroundColor: '#8B5CF6' }
              ]} 
            />
          </View>
          <Text style={[styles.confidenceText, { color: theme.textTertiary }]}>
            Pattern match: {Math.round(awareness.confidence * 100)}%
          </Text>
        </View>
      )}
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    gap: 12,
  },
  styleBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    gap: 6,
  },
  styleIcon: {
    fontSize: 14,
  },
  styleText: {
    fontSize: 13,
    fontWeight: '500',
  },
  promptCard: {
    padding: 16,
    borderRadius: 10,
    borderWidth: 1,
    borderStyle: 'dashed',
  },
  promptText: {
    fontSize: 14,
    lineHeight: 22,
  },
  promptSecondLine: {
    marginTop: 8,
    fontStyle: 'italic',
  },
  confidenceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  confidenceBar: {
    flex: 1,
    height: 4,
    borderRadius: 2,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    borderRadius: 2,
  },
  confidenceText: {
    fontSize: 11,
    fontWeight: '500',
  },
});
