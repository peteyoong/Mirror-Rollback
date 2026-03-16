/**
 * LifelineGapPrompt
 * 
 * Displays gentle prompts for detected timeline gaps.
 * Encourages reflection about unexplored periods without being intrusive.
 * 
 * Design principles:
 * - Curious, not demanding
 * - Supportive, not intrusive
 * - Optional and dismissible
 * - Trauma-safe language
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';

export interface GapPromptData {
  start_year: number;
  end_year: number;
  gap_length: number;
  prompt_text: string;
  reflection_text: string;
  cta_text: string;
}

interface Props {
  gap: GapPromptData;
  onAddMoment: (startYear: number, endYear: number) => void;
  onDismiss?: (gap: GapPromptData) => void;
  isCompact?: boolean;
}

export default function LifelineGapPrompt({ gap, onAddMoment, onDismiss, isCompact = false }: Props) {
  const { theme } = useTheme();
  const [isDismissed, setIsDismissed] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(1));
  
  if (isDismissed) {
    return null;
  }
  
  const handleDismiss = () => {
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: true,
    }).start(() => {
      setIsDismissed(true);
      onDismiss?.(gap);
    });
  };
  
  const handleAddMoment = () => {
    onAddMoment(gap.start_year, gap.end_year);
  };
  
  // Format the period text for display
  const periodText = gap.start_year === gap.end_year 
    ? `${gap.start_year}` 
    : `${gap.start_year}–${gap.end_year}`;
  
  if (isCompact) {
    // Inline version for between timeline events
    return (
      <Animated.View style={[styles.compactContainer, { opacity: fadeAnim, borderColor: theme.border }]}>
        <View style={styles.compactContent}>
          <View style={[styles.compactIcon, { backgroundColor: `${theme.textTertiary}15` }]}>
            <Ionicons name="help-circle-outline" size={16} color={theme.textTertiary} />
          </View>
          <Text style={[styles.compactText, { color: theme.textTertiary }]}>
            Quiet period: {periodText}
          </Text>
          <TouchableOpacity 
            style={[styles.compactAddBtn, { backgroundColor: theme.surface }]}
            onPress={handleAddMoment}
          >
            <Ionicons name="add" size={14} color={theme.textSecondary} />
          </TouchableOpacity>
        </View>
      </Animated.View>
    );
  }
  
  // Full card version
  return (
    <Animated.View 
      style={[
        styles.container, 
        { 
          opacity: fadeAnim,
          backgroundColor: theme.surface,
          borderColor: theme.border,
        }
      ]}
    >
      {/* Dismiss button */}
      <TouchableOpacity 
        style={styles.dismissButton}
        onPress={handleDismiss}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
      >
        <Ionicons name="close" size={16} color={theme.textTertiary} />
      </TouchableOpacity>
      
      {/* Header with icon */}
      <View style={styles.header}>
        <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}08` }]}>
          <Ionicons name="time-outline" size={20} color={theme.textSecondary} />
        </View>
      </View>
      
      {/* Main prompt text */}
      <Text style={[styles.promptText, { color: theme.text }]}>
        {gap.prompt_text}
      </Text>
      
      {/* Reflection invitation */}
      <Text style={[styles.reflectionText, { color: theme.textSecondary }]}>
        {gap.reflection_text}
      </Text>
      
      {/* CTA Button */}
      <TouchableOpacity 
        style={[styles.ctaButton, { backgroundColor: theme.background, borderColor: theme.border }]}
        onPress={handleAddMoment}
      >
        <Ionicons name="add-circle-outline" size={16} color={theme.textSecondary} />
        <Text style={[styles.ctaText, { color: theme.textSecondary }]}>
          {gap.cta_text}
        </Text>
      </TouchableOpacity>
      
      {/* Skip link */}
      <TouchableOpacity 
        style={styles.skipButton}
        onPress={handleDismiss}
      >
        <Text style={[styles.skipText, { color: theme.textTertiary }]}>
          Not now
        </Text>
      </TouchableOpacity>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
    position: 'relative',
  },
  dismissButton: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 1,
    padding: 4,
  },
  header: {
    marginBottom: 12,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  promptText: {
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 22,
    marginBottom: 6,
    paddingRight: 24,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 20,
    fontStyle: 'italic',
    marginBottom: 16,
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 8,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '500',
  },
  skipButton: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  skipText: {
    fontSize: 13,
  },
  
  // Compact inline styles
  compactContainer: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    marginVertical: 8,
    marginLeft: 32,
    borderLeftWidth: 2,
    borderStyle: 'dashed',
  },
  compactContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  compactIcon: {
    width: 24,
    height: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  compactText: {
    flex: 1,
    fontSize: 13,
    fontStyle: 'italic',
  },
  compactAddBtn: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
