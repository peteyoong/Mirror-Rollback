/**
 * MicroMirrorCard Component
 * 
 * Displays a contextual Mirror response inline under a journal entry.
 * 
 * TIMING (v2 - Refined for readability):
 * - Fade in: 250ms
 * - Stay fully visible: 7 seconds
 * - Fade to: 65% opacity (not fully hidden)
 * - NEVER auto-remove - stays visible until:
 *   - User starts typing new entry
 *   - User explicitly dismisses
 *   - User navigates away
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  TouchableOpacity,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Colors } from '../constants/colors';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// ============================================
// TIMING CONSTANTS (v2 - Refined)
// ============================================
const FADE_IN_DURATION = 250;        // Quick fade in
const VISIBLE_DURATION = 7000;       // Stay fully visible for 7 seconds
const FADE_DURATION = 600;           // Gentle fade to reduced opacity
const RESTING_OPACITY = 0.65;        // Rest at 65% - still clearly visible

interface MicroMirrorCardProps {
  text: string;
  visible: boolean;
  onReflect?: () => void;
  onAskMirror?: () => void;
  onDismiss?: () => void;
  entryId?: string;
}

const MicroMirrorCard: React.FC<MicroMirrorCardProps> = ({
  text,
  visible,
  onReflect,
  onAskMirror,
  onDismiss,
  entryId,
}) => {
  const { theme, isDark } = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const [isExpanded, setIsExpanded] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const [hasSettled, setHasSettled] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Parse text into lines (recognition + optional choice)
  const lines = text.split('\n').filter(line => line.trim());
  const recognitionLine = lines[0] || '';
  const choiceLines = lines.slice(1);

  useEffect(() => {
    if (visible) {
      // Reset state on new mount
      setIsExpanded(false);
      setShowActions(false);
      setHasSettled(false);

      // Fade in quickly
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: FADE_IN_DURATION,
        useNativeDriver: true,
      }).start();

      // After VISIBLE_DURATION, gently fade to resting opacity (NOT hidden)
      timerRef.current = setTimeout(() => {
        Animated.timing(fadeAnim, {
          toValue: RESTING_OPACITY,
          duration: FADE_DURATION,
          useNativeDriver: true,
        }).start(() => {
          setHasSettled(true);
        });
      }, VISIBLE_DURATION);
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [visible, fadeAnim]);

  // When visibility changes to false, do NOT auto-fade out
  // Let parent control removal by setting visible=false
  useEffect(() => {
    if (!visible) {
      // Only animate out if we're actually being dismissed
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start();
    }
  }, [visible, fadeAnim]);

  const handleTap = () => {
    // Clear any pending fade timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Restore to full visibility
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 200,
      useNativeDriver: true,
    }).start();

    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIsExpanded(true);
    setShowActions(true);
    setHasSettled(false);
  };

  const handleDismiss = () => {
    if (onDismiss) {
      onDismiss();
    }
  };

  if (!visible || !text) {
    return null;
  }

  return (
    <Animated.View
      style={[
        styles.container,
        {
          backgroundColor: isDark ? 'rgba(139, 92, 246, 0.08)' : 'rgba(139, 92, 246, 0.06)',
          borderColor: isDark ? 'rgba(139, 92, 246, 0.2)' : 'rgba(139, 92, 246, 0.15)',
          opacity: fadeAnim,
        },
      ]}
    >
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={handleTap}
        style={styles.touchable}
      >
        {/* Mirror noticed label - subtle */}
        <View style={styles.headerRow}>
          <Text style={[styles.mirrorLabel, { color: isDark ? 'rgba(139, 92, 246, 0.7)' : 'rgba(139, 92, 246, 0.8)' }]}>
            ✧ Mirror noticed
          </Text>
          {hasSettled && !isExpanded && (
            <Text style={[styles.tapHint, { color: theme.textTertiary }]}>
              tap to expand
            </Text>
          )}
        </View>

        {/* Recognition Line - Always visible, italic */}
        <Text style={[styles.recognitionLine, { color: theme.text }]}>
          {recognitionLine}
        </Text>

        {/* Choice Lines - Collapsed when settled, expanded on tap */}
        {(isExpanded || !hasSettled) && choiceLines.length > 0 && (
          <View style={styles.choiceContainer}>
            {choiceLines.map((line, index) => (
              <Text key={index} style={[styles.choiceLine, { color: theme.textSecondary }]}>
                {line}
              </Text>
            ))}
          </View>
        )}
      </TouchableOpacity>

      {/* Actions - Only shown after tap */}
      {showActions && (
        <View style={styles.actionsContainer}>
          <TouchableOpacity
            style={[styles.actionButton, { borderColor: theme.border }]}
            onPress={onReflect}
          >
            <Text style={[styles.actionText, { color: theme.textSecondary }]}>Reflect</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.actionButton, { backgroundColor: Colors.accent, borderColor: Colors.accent }]}
            onPress={onAskMirror}
          >
            <Text style={[styles.actionText, { color: '#fff' }]}>Ask Mirror</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Dismiss button - subtle, always available when expanded */}
      {showActions && (
        <TouchableOpacity
          style={styles.dismissButton}
          onPress={handleDismiss}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Text style={[styles.dismissText, { color: theme.textTertiary }]}>dismiss</Text>
        </TouchableOpacity>
      )}
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 12,
    marginBottom: 14,
    borderRadius: 12,
    borderWidth: 1,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  touchable: {
    padding: 14,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  mirrorLabel: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.3,
  },
  tapHint: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  recognitionLine: {
    fontSize: 17,
    lineHeight: 26,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  choiceContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(139, 92, 246, 0.15)',
  },
  choiceLine: {
    fontSize: 16,
    lineHeight: 26,
    marginTop: 4,
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 14,
    paddingBottom: 10,
    paddingTop: 4,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  actionText: {
    fontSize: 16,
    fontWeight: '500',
  },
  dismissButton: {
    alignSelf: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  dismissText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
});

export default MicroMirrorCard;
