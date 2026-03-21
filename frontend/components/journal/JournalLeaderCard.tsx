/**
 * JournalLeaderCard
 * 
 * Leader/framing card for the Journal tab within Reflect.
 * Explains why journaling matters in a human, grounded tone.
 * 
 * Design language matches LifelineFramingCard - subtle, premium, not loud.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';

export default function JournalLeaderCard() {
  const { theme, isDark } = useTheme();
  
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
        {/* Title */}
        <Text style={[styles.title, { color: theme.text }]}>
          Capture what's real, while it's happening
        </Text>
        
        {/* Body */}
        <View style={styles.bodyContainer}>
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            Some moments pass quickly.{'\n'}
            Some stay with you longer than you expect.
          </Text>
          
          <Text style={[styles.bodyText, { color: theme.textSecondary }]}>
            Writing them down helps you notice what's actually changing —{'\n'}
            in your thoughts, your relationships, and yourself.
          </Text>
          
          <Text style={[styles.bodyText, styles.lastParagraph, { color: theme.textSecondary }]}>
            This doesn't have to be perfect.{'\n'}
            Just honest.
          </Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
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
  title: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 24,
    marginBottom: 16,
  },
  bodyContainer: {
    gap: 12,
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 23,
  },
  lastParagraph: {
    fontStyle: 'italic',
  },
});
