/**
 * MirrorLeaderCard
 * 
 * Leader/framing card for the Mirror tab within Reflect.
 * Explains what Mirror does in a human, emotionally resonant tone.
 * 
 * COLLAPSIBLE BEHAVIOR:
 * - Expanded: Full intro shown when chat is empty (onboarding state)
 * - Collapsed: Compact header when chat has messages (conversation focus)
 * - User can manually expand/collapse with a tap
 * 
 * Design language matches LifelineFramingCard - subtle, premium, not loud.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';

interface MirrorLeaderCardProps {
  isExpanded: boolean;
  onToggle: () => void;
}

export default function MirrorLeaderCard({ isExpanded, onToggle }: MirrorLeaderCardProps) {
  const { theme, isDark } = useTheme();
  
  // Collapsed state - compact header
  if (!isExpanded) {
    return (
      <TouchableOpacity 
        activeOpacity={0.7}
        onPress={onToggle}
        style={[
          styles.collapsedContainer,
          { 
            backgroundColor: theme.surface,
            borderColor: theme.border,
          }
        ]}
      >
        <View style={styles.collapsedContent}>
          <View style={styles.collapsedTextContainer}>
            <Text style={[styles.collapsedTitle, { color: theme.text }]}>
              Make sense of what you're going through
            </Text>
            <Text style={[styles.collapsedSubtext, { color: theme.textTertiary }]}>
              Space to think clearly
            </Text>
          </View>
          <Text style={[styles.chevron, { color: theme.textTertiary }]}>
            ▼
          </Text>
        </View>
      </TouchableOpacity>
    );
  }
  
  // Expanded state - full intro
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
      
      <TouchableOpacity 
        activeOpacity={0.9}
        onPress={onToggle}
        style={styles.content}
      >
        {/* Header row with collapse hint */}
        <View style={styles.headerRow}>
          <Text style={[styles.title, { color: theme.text }]}>
            Make sense of what you're going through
          </Text>
          <Text style={[styles.chevronExpanded, { color: theme.textTertiary }]}>
            ▲
          </Text>
        </View>
        
        {/* Body */}
        <View style={styles.bodyContainer}>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            Sometimes you don't need answers —{'\n'}
            you need space to think clearly.
          </Text>
          
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            Mirror helps you reflect on what you've written,{'\n'}
            spot patterns, and see things from a different angle.
          </Text>
          
          <Text style={[styles.bodyText, styles.lastParagraph, { color: theme.textSecondary }]}>
            You can go as deep as you want.{'\n'}
            Or just start with a question.
          </Text>
        </View>
        
        {/* Optional subtle prompt */}
        <Text style={[styles.subtlePrompt, { color: theme.textTertiary }]}>
          Start with something that's been on your mind.
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  // ===== COLLAPSED STATE =====
  collapsedContainer: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 8,
    overflow: 'hidden',
  },
  collapsedContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  collapsedTextContainer: {
    flex: 1,
  },
  collapsedTitle: {
    fontSize: 14,
    fontWeight: '600',
    lineHeight: 18,
  },
  collapsedSubtext: {
    fontSize: 12,
    marginTop: 2,
    fontStyle: 'italic',
  },
  chevron: {
    fontSize: 10,
    marginLeft: 12,
  },
  
  // ===== EXPANDED STATE =====
  container: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 16,
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
    padding: 20,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  title: {
    flex: 1,
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 24,
  },
  chevronExpanded: {
    fontSize: 10,
    marginLeft: 12,
    marginTop: 6,
  },
  bodyContainer: {
    gap: 12,
    marginBottom: 16,
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 23,
  },
  lastParagraph: {
    fontStyle: 'italic',
  },
  subtlePrompt: {
    fontSize: 13,
    fontStyle: 'italic',
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128,128,128,0.2)',
  },
});
