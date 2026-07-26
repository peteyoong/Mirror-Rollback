/**
 * JournalLeaderCard (Collapsible)
 * 
 * Leader/framing card for the Journal tab within Reflect.
 * Now collapsible for better mobile UX - auto-collapses on input focus/typing/scroll.
 * 
 * Collapsed state: Compact one-liner that preserves emotional tone
 * Expanded state: Full intro with writing guidance
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  LayoutAnimation,
  UIManager,
  Platform,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface JournalLeaderCardProps {
  isExpanded: boolean;
  onToggle: () => void;
}

export default function JournalLeaderCard({ isExpanded, onToggle }: JournalLeaderCardProps) {
  const { theme, isDark } = useTheme();
  
  const handleToggle = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    onToggle();
  };
  
  // Collapsed state — REFLECT V3: minimal, calm, no hard border.
  // Reads as "Need help starting?" rather than the old prompt-machinery
  // language. Tap reveals the full prompt block.
  if (!isExpanded) {
    return (
      <TouchableOpacity
        style={styles.collapsedContainer}
        onPress={handleToggle}
        activeOpacity={0.6}
        accessibilityLabel="Show writing prompt"
        accessibilityRole="button"
      >
        <View style={styles.collapsedContent}>
          <Text style={[styles.collapsedText, { color: theme.textTertiary }]}>
            Need help starting?
          </Text>
          <Text style={[styles.expandToggle, { color: theme.textTertiary }]}>
            ›
          </Text>
        </View>
      </TouchableOpacity>
    );
  }
  
  // Expanded state - full intro card
  return (
    <View style={[
      styles.container,
      { 
        backgroundColor: theme.surface,
        borderColor: theme.border,
      }
    ]}>
      {/* Subtle gradient overlay */}
      <LinearGradient
        colors={isDark 
          ? ['rgba(255,255,255,0.02)', 'transparent']
          : ['rgba(0,0,0,0.01)', 'transparent']
        }
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradientOverlay}
      />
      
      <View style={styles.content}>
        {/* Header with collapse control */}
        <View style={styles.header}>
          <Text style={[styles.title, { color: theme.text }]}>
            Capture what's real, while it's happening
          </Text>
          <TouchableOpacity
            style={styles.collapseButton}
            onPress={handleToggle}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={[styles.collapseText, { color: theme.textTertiary }]}>
              Hide
            </Text>
          </TouchableOpacity>
        </View>
        
        {/* Body - slightly tightened spacing */}
        <View style={styles.bodyContainer}>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            Some moments pass quickly. Some stay longer than you expect.
          </Text>
          
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            Writing them down helps you notice what's actually changing.
          </Text>
          
          <Text style={[styles.bodyText, styles.lastParagraph, { color: theme.textSecondary }]}>
            This doesn't have to be perfect. Just honest.
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  // Collapsed state styles - tighter
  collapsedContainer: {
    // REFLECT V3: no hard border. The collapsed state should read as a
    // subtle text link, not a card. Soft inline affordance.
    marginBottom: 16,
    marginTop: 4,
    paddingVertical: 10,
    paddingHorizontal: 4,
  },
  collapsedContent: {
    flexDirection: 'row',
    justifyContent: 'flex-start',
    alignItems: 'center',
    gap: 6,
  },
  collapsedText: {
    fontSize: 13,
    fontWeight: '400',
    letterSpacing: 0.1,
  },
  expandToggle: {
    fontSize: 14,
    fontWeight: '400',
    opacity: 0.6,
  },
  
  // Expanded state styles - more compact
  container: {
    borderRadius: 12, // Reduced from 14
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 8, // Reduced from 12
    position: 'relative',
    overflow: 'hidden',
  },
  gradientOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  content: {
    padding: 14, // Reduced from 16
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10, // Reduced from 12
  },
  title: {
    fontSize: 15, // Reduced from 16
    fontWeight: '500',
    lineHeight: 20,
    flex: 1,
    paddingRight: 10,
  },
  collapseButton: {
    paddingVertical: 2,
    paddingHorizontal: 6,
  },
  collapseText: {
    fontSize: 11, // Reduced from 12
    fontWeight: '500',
  },
  bodyContainer: {
    gap: 6, // Reduced from 8
  },
  bodyText: {
    fontSize: 13, // Reduced from 14
    lineHeight: 18, // Reduced from 20
  },
  lastParagraph: {
    fontStyle: 'italic',
  },
});
