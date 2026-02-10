/**
 * EnneagramAssessmentIntro
 * ========================
 * Welcome screen for the P2 Deep Enneagram Assessment.
 * Sets tone and expectations with calm, reflective language.
 * 
 * Supports Resume Prompt when an in-progress session exists.
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';

interface Props {
  onBegin: () => void;
  isLoading: boolean;
  // Resume prompt props
  showResumePrompt?: boolean;
  onResume?: () => void;
  onStartFresh?: () => void;
}

export const EnneagramAssessmentIntro: React.FC<Props> = ({ 
  onBegin, 
  isLoading,
  showResumePrompt = false,
  onResume,
  onStartFresh,
}) => {
  return (
    <View style={styles.container}>
      {/* Resume Prompt Card */}
      {showResumePrompt && (
        <View style={styles.resumePromptCard}>
          <Ionicons name="bookmark-outline" size={24} color={Colors.accent} style={styles.resumeIcon} />
          <Text style={styles.resumeTitle}>Pick up where you left off?</Text>
          <Text style={styles.resumeBody}>
            You were partway through a deep assessment.{'\n'}
            You can continue, or start fresh.
          </Text>
          <View style={styles.resumeButtons}>
            <TouchableOpacity
              style={styles.resumePrimaryButton}
              onPress={onResume}
              activeOpacity={0.8}
            >
              <Text style={styles.resumePrimaryButtonText}>Continue</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.resumeSecondaryButton}
              onPress={onStartFresh}
              activeOpacity={0.8}
            >
              <Text style={styles.resumeSecondaryButtonText}>Start over</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Header Icon */}
      <View style={styles.iconContainer}>
        <Ionicons name="compass-outline" size={48} color={Colors.text} />
      </View>

      {/* Title */}
      <Text style={styles.title}>Enneagram Deep Assessment</Text>
      
      {/* Subtitle */}
      <Text style={styles.subtitle}>
        A reflective exploration of how you tend to respond under pressure.
      </Text>

      {/* Time Estimate */}
      <View style={styles.timeContainer}>
        <Ionicons name="time-outline" size={18} color={Colors.textSecondary} />
        <Text style={styles.timeText}>About 20–30 minutes</Text>
      </View>

      {/* Bullet Points */}
      <View style={styles.bulletContainer}>
        <View style={styles.bulletItem}>
          <View style={styles.bulletDot} />
          <Text style={styles.bulletText}>One question at a time</Text>
        </View>
        <View style={styles.bulletItem}>
          <View style={styles.bulletDot} />
          <Text style={styles.bulletText}>No right or wrong answers</Text>
        </View>
        <View style={styles.bulletItem}>
          <View style={styles.bulletDot} />
          <Text style={styles.bulletText}>Answer for what's most automatic, not ideal</Text>
        </View>
      </View>

      {/* Begin Button - hidden when resume prompt is showing */}
      {!showResumePrompt && (
        <TouchableOpacity
          style={[styles.beginButton, isLoading && styles.beginButtonDisabled]}
          onPress={onBegin}
          disabled={isLoading}
          activeOpacity={0.8}
        >
          {isLoading ? (
            <ActivityIndicator color={Colors.surface} size="small" />
          ) : (
            <>
              <Text style={styles.beginButtonText}>Begin</Text>
              <Ionicons name="arrow-forward" size={20} color={Colors.surface} />
            </>
          )}
        </TouchableOpacity>
      )}

      {/* Footer Note */}
      <Text style={styles.footerNote}>
        This isn't a test. It's a way of noticing patterns.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // Resume Prompt Styles
  resumePromptCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.accent,
    maxWidth: 340,
    width: '100%',
  },
  resumeIcon: {
    marginBottom: 8,
  },
  resumeTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
    textAlign: 'center',
  },
  resumeBody: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
  },
  resumeButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  resumePrimaryButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
  },
  resumePrimaryButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.surface,
  },
  resumeSecondaryButton: {
    backgroundColor: 'transparent',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  resumeSecondaryButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  // Original Intro Styles
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.surfaceLight,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    fontSize: 26,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 20,
    maxWidth: 320,
  },
  timeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 32,
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 20,
  },
  timeText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  bulletContainer: {
    alignSelf: 'stretch',
    maxWidth: 340,
    marginBottom: 40,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.textTertiary,
    marginRight: 12,
  },
  bulletText: {
    fontSize: 15,
    color: Colors.text,
    flex: 1,
  },
  beginButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    marginBottom: 24,
    minWidth: 160,
  },
  beginButtonDisabled: {
    opacity: 0.6,
  },
  beginButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.surface,
  },
  footerNote: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
    maxWidth: 280,
  },
});

export default EnneagramAssessmentIntro;
