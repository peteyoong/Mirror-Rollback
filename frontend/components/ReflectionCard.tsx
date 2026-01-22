import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../constants/colors';

interface ReflectionCardProps {
  insight: string;
  question: string;
  perspective: string;
}

export default function ReflectionCard({
  insight,
  question,
  perspective,
}: ReflectionCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Today's Insight</Text>
        <Text style={styles.insightText}>{insight}</Text>
      </View>

      <View style={styles.divider} />

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Reflect On</Text>
        <Text style={styles.questionText}>{question}</Text>
      </View>

      <View style={styles.divider} />

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Another Perspective</Text>
        <Text style={styles.perspectiveText}>{perspective}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    marginHorizontal: 16,
  },
  section: {
    marginVertical: 12,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  insightText: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.text,
  },
  questionText: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  perspectiveText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: 8,
  },
});