/**
 * EnneagramAssessmentIntro
 * ========================
 * Welcome screen for the P2 Deep Enneagram Assessment.
 * Sets tone and expectations with calm, reflective language.
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
}

export const EnneagramAssessmentIntro: React.FC<Props> = ({ onBegin, isLoading }) => {
  return (
    <View style={styles.container}>
      {/* Header Icon */}
      <View style={styles.iconContainer}>
        <Ionicons name="compass-outline" size={48} color={Colors.text} />
      </View>

      {/* Title */}
      <Text style={styles.title}>Enneagram Deep Assessment</Text>
      
      {/* Subtitle */}
      <Text style={styles.subtitle}>
        A reflective assessment of how you tend to respond under pressure.
      </Text>

      {/* Time Estimate */}
      <View style={styles.timeContainer}>
        <Ionicons name="time-outline" size={18} color={Colors.textSecondary} />
        <Text style={styles.timeText}>~20–30 minutes</Text>
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

      {/* Begin Button */}
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

      {/* Footer Note */}
      <Text style={styles.footerNote}>
        Your answers remain private and are used only to identify patterns.
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
