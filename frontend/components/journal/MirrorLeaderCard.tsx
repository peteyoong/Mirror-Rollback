/**
 * MirrorLeaderCard
 * 
 * Leader/framing card for the Mirror tab within Reflect.
 * Explains what Mirror does in a human, emotionally resonant tone.
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

export default function MirrorLeaderCard() {
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
          Make sense of what you're going through
        </Text>
        
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
