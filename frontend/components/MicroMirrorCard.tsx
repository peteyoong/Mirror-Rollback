/**
 * MicroMirrorCard Component
 * 
 * Displays a contextual Mirror response inline under a journal entry.
 * Features fade-in animation and lifecycle management.
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

interface MicroMirrorCardProps {
  text: string;
  visible: boolean;
  onReflect?: () => void;
  onAskMirror?: () => void;
  entryId?: string;
}

const MicroMirrorCard: React.FC<MicroMirrorCardProps> = ({
  text,
  visible,
  onReflect,
  onAskMirror,
  entryId,
}) => {
  const { theme, isDark } = useTheme();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const [isExpanded, setIsExpanded] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const [isFaded, setIsFaded] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Parse text into lines (recognition + optional choice)
  const lines = text.split('\n').filter(line => line.trim());
  const recognitionLine = lines[0] || '';
  const choiceLines = lines.slice(1);

  useEffect(() => {
    if (visible) {
      // Reset state on new mount
      setIsExpanded(false);
      setShowActions(false);
      setIsFaded(false);

      // Fade in
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();

      // After 4 seconds, fade to 50% opacity
      timerRef.current = setTimeout(() => {
        Animated.timing(fadeAnim, {
          toValue: 0.5,
          duration: 500,
          useNativeDriver: true,
        }).start(() => {
          setIsFaded(true);
        });
      }, 4000);
    } else {
      // Fade out completely
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }).start();
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [visible, fadeAnim]);

  const handleTap = () => {
    // Clear any pending fade timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Expand to full visibility
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 200,
      useNativeDriver: true,
    }).start();

    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIsExpanded(true);
    setShowActions(true);
    setIsFaded(false);
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
        {/* Recognition Line - Always visible, italic */}
        <Text style={[styles.recognitionLine, { color: theme.text }]}>
          {recognitionLine}
        </Text>

        {/* Choice Lines - Collapsed when faded, expanded on tap */}
        {(isExpanded || !isFaded) && choiceLines.length > 0 && (
          <View style={styles.choiceContainer}>
            {choiceLines.map((line, index) => (
              <Text key={index} style={[styles.choiceLine, { color: theme.textSecondary }]}>
                {line}
              </Text>
            ))}
          </View>
        )}

        {/* Collapsed indicator when faded */}
        {isFaded && !isExpanded && choiceLines.length > 0 && (
          <Text style={[styles.expandHint, { color: theme.textTertiary }]}>
            tap to expand
          </Text>
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
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 10,
    marginBottom: 6,
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
  recognitionLine: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
    fontWeight: '500',
  },
  choiceContainer: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(139, 92, 246, 0.15)',
  },
  choiceLine: {
    fontSize: 14,
    lineHeight: 21,
    marginTop: 4,
  },
  expandHint: {
    fontSize: 11,
    marginTop: 8,
    textAlign: 'center',
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 10,
    paddingHorizontal: 14,
    paddingBottom: 14,
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
    fontSize: 13,
    fontWeight: '500',
  },
});

export default MicroMirrorCard;
