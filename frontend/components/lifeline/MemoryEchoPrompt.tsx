/**
 * MemoryEchoPrompt Component
 * 
 * Prompts users to add earlier related events when a turning point
 * resembles a past pattern. Uses associative memory triggers to help
 * users expand their Lifeline naturally.
 * 
 * Triggers:
 * - New Lifeline event added
 * - Strong pattern arc detected
 * - Category event repeats
 * - Large timeline gap (>5 years)
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

// =============================================================================
// TYPES
// =============================================================================

export type EchoTriggerType = 
  | 'new_event'      // A new event was just added
  | 'pattern_arc'    // A pattern arc was detected
  | 'category_repeat'// Same category appears multiple times
  | 'timeline_gap';  // Gap > 5 years in timeline

export interface MemoryEchoData {
  type: EchoTriggerType;
  triggerEventId?: string;
  category?: string;
  year?: number;
  gapStartYear?: number;
  gapEndYear?: number;
  message: string;
  subMessage?: string;
}

interface Props {
  echo: MemoryEchoData;
  onAddEarlierMoment: (prefill: EarlierMomentPrefill) => void;
  onDismiss: () => void;
  variant?: 'inline' | 'card';
}

export interface EarlierMomentPrefill {
  suggestedCategory?: string;
  suggestedYear?: number;
  helperText: string;
}

// =============================================================================
// STORAGE KEYS
// =============================================================================

const ECHO_DISMISS_KEY = '@mirror_echo_dismissed';
const ECHO_SESSION_COUNT_KEY = '@mirror_echo_session_count';
const MAX_ECHOES_PER_SESSION = 3;

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Check if echo prompts should be shown (respects limits)
 */
export async function canShowEcho(): Promise<boolean> {
  try {
    const countStr = await AsyncStorage.getItem(ECHO_SESSION_COUNT_KEY);
    const count = countStr ? parseInt(countStr, 10) : 0;
    return count < MAX_ECHOES_PER_SESSION;
  } catch {
    return true;
  }
}

/**
 * Increment echo count for this session
 */
export async function incrementEchoCount(): Promise<void> {
  try {
    const countStr = await AsyncStorage.getItem(ECHO_SESSION_COUNT_KEY);
    const count = countStr ? parseInt(countStr, 10) : 0;
    await AsyncStorage.setItem(ECHO_SESSION_COUNT_KEY, String(count + 1));
  } catch {
    // Ignore storage errors
  }
}

/**
 * Reset echo count (call on app launch or new session)
 */
export async function resetEchoCount(): Promise<void> {
  try {
    await AsyncStorage.setItem(ECHO_SESSION_COUNT_KEY, '0');
  } catch {
    // Ignore storage errors
  }
}

/**
 * Generate echo data based on trigger type
 */
export function generateEchoData(
  type: EchoTriggerType,
  options?: {
    category?: string;
    year?: number;
    gapStartYear?: number;
    gapEndYear?: number;
  }
): MemoryEchoData {
  switch (type) {
    case 'new_event':
      return {
        type,
        category: options?.category,
        year: options?.year,
        message: "Did something like this happen earlier?",
        subMessage: "This moment may echo an earlier turning point.",
      };
    
    case 'pattern_arc':
      return {
        type,
        message: "This pattern may have roots in your past.",
        subMessage: "Have you experienced a similar sequence before?",
      };
    
    case 'category_repeat':
      const categoryName = options?.category || 'life';
      return {
        type,
        category: options?.category,
        message: `Have you experienced a similar ${categoryName.toLowerCase()} turning point earlier?`,
        subMessage: `This category appears multiple times in your timeline.`,
      };
    
    case 'timeline_gap':
      const years = options?.gapEndYear && options?.gapStartYear 
        ? options.gapEndYear - options.gapStartYear 
        : 5;
      return {
        type,
        gapStartYear: options?.gapStartYear,
        gapEndYear: options?.gapEndYear,
        message: "This period may contain a moment you haven't added yet.",
        subMessage: `${years} years passed between these events.`,
      };
    
    default:
      return {
        type: 'new_event',
        message: "Did something like this happen earlier?",
      };
  }
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function MemoryEchoPrompt({ 
  echo, 
  onAddEarlierMoment, 
  onDismiss,
  variant = 'card',
}: Props) {
  const { theme } = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const [isVisible, setIsVisible] = useState(true);
  
  // Fade in on mount
  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 400,
      useNativeDriver: false,
    }).start();
    
    // Track that we showed an echo
    incrementEchoCount();
  }, []);
  
  // Handle dismiss with fade out
  const handleDismiss = () => {
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: false,
    }).start(() => {
      setIsVisible(false);
      onDismiss();
    });
  };
  
  // Handle add earlier moment
  const handleAddEarlier = () => {
    const prefill: EarlierMomentPrefill = {
      suggestedCategory: echo.category,
      suggestedYear: echo.gapStartYear || (echo.year ? echo.year - 5 : undefined),
      helperText: getHelperText(echo.type),
    };
    
    Animated.timing(fadeAnim, {
      toValue: 0,
      duration: 200,
      useNativeDriver: false,
    }).start(() => {
      setIsVisible(false);
      onAddEarlierMoment(prefill);
    });
  };
  
  if (!isVisible) return null;
  
  // Inline variant (for between events)
  if (variant === 'inline') {
    return (
      <Animated.View style={[styles.inlineContainer, { opacity: fadeAnim }]}>
        <View style={[styles.inlineCard, { backgroundColor: `${theme.accent}08`, borderColor: `${theme.accent}25` }]}>
          <View style={styles.inlineIconContainer}>
            <Ionicons name="time-outline" size={16} color={theme.accent} />
          </View>
          <View style={styles.inlineContent}>
            <Text style={[styles.inlineMessage, { color: theme.textSecondary }]}>
              {echo.message}
            </Text>
            <TouchableOpacity
              style={[styles.inlineButton, { backgroundColor: `${theme.accent}15` }]}
              onPress={handleAddEarlier}
              activeOpacity={0.7}
            >
              <Text style={[styles.inlineButtonText, { color: theme.accent }]}>
                Add a moment from this time
              </Text>
            </TouchableOpacity>
          </View>
          <TouchableOpacity style={styles.inlineDismiss} onPress={handleDismiss}>
            <Ionicons name="close" size={16} color={theme.textTertiary} />
          </TouchableOpacity>
        </View>
      </Animated.View>
    );
  }
  
  // Card variant (default)
  return (
    <Animated.View style={[styles.container, { opacity: fadeAnim }]}>
      <View style={[styles.card, { backgroundColor: `${theme.accent}08`, borderColor: `${theme.accent}25` }]}>
        {/* Header */}
        <View style={styles.header}>
          <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}15` }]}>
            <Ionicons name="sparkles-outline" size={18} color={theme.accent} />
          </View>
          <TouchableOpacity style={styles.dismissButton} onPress={handleDismiss}>
            <Ionicons name="close" size={18} color={theme.textTertiary} />
          </TouchableOpacity>
        </View>
        
        {/* Content */}
        <View style={styles.content}>
          <Text style={[styles.message, { color: theme.text }]}>
            {echo.message}
          </Text>
          {echo.subMessage && (
            <Text style={[styles.subMessage, { color: theme.textSecondary }]}>
              {echo.subMessage}
            </Text>
          )}
        </View>
        
        {/* Actions */}
        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.primaryButton, { backgroundColor: theme.accent }]}
            onPress={handleAddEarlier}
            activeOpacity={0.8}
          >
            <Text style={styles.primaryButtonText}>Add earlier moment</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={handleDismiss}
            activeOpacity={0.7}
          >
            <Text style={[styles.secondaryButtonText, { color: theme.textSecondary }]}>
              Not now
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </Animated.View>
  );
}

// =============================================================================
// HELPER TEXT GENERATOR
// =============================================================================

function getHelperText(type: EchoTriggerType): string {
  switch (type) {
    case 'new_event':
      return "You may remember a similar moment earlier in your life.";
    case 'pattern_arc':
      return "This pattern may have begun earlier than you realize.";
    case 'category_repeat':
      return "Think about earlier moments in this area of your life.";
    case 'timeline_gap':
      return "What was happening during this quiet period?";
    default:
      return "You may remember a similar moment earlier in your life.";
  }
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  // Card variant
  container: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dismissButton: {
    padding: 4,
  },
  content: {
    marginBottom: 16,
  },
  message: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 6,
    lineHeight: 22,
  },
  subMessage: {
    fontSize: 14,
    lineHeight: 20,
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  primaryButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '500',
  },
  secondaryButton: {
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  secondaryButtonText: {
    fontSize: 14,
  },
  
  // Inline variant
  inlineContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  inlineCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
  },
  inlineIconContainer: {
    marginRight: 10,
    marginTop: 2,
  },
  inlineContent: {
    flex: 1,
  },
  inlineMessage: {
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 8,
  },
  inlineButton: {
    alignSelf: 'flex-start',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 14,
  },
  inlineButtonText: {
    fontSize: 12,
    fontWeight: '500',
  },
  inlineDismiss: {
    padding: 4,
    marginLeft: 8,
  },
});
