/**
 * ExperienceSummaryCard
 * 
 * Shows "How Mirror will meet you" summary after onboarding
 * Displays the derived experience controls in a human-readable format
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { ExperienceSummary } from '../types/mirror-profile';

interface ExperienceSummaryCardProps {
  summary: ExperienceSummary;
}

export default function ExperienceSummaryCard({ summary }: ExperienceSummaryCardProps) {
  const { theme } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      <Text style={[styles.title, { color: theme.text }]}>
        How Mirror will meet you
      </Text>
      
      <View style={styles.itemsContainer}>
        <View style={styles.item}>
          <Text style={[styles.label, { color: theme.textTertiary }]}>FOCUS</Text>
          <Text style={[styles.value, { color: theme.text }]}>{summary.focus}</Text>
        </View>
        
        <View style={styles.item}>
          <Text style={[styles.label, { color: theme.textTertiary }]}>STYLE</Text>
          <Text style={[styles.value, { color: theme.text }]}>{summary.style}</Text>
        </View>
        
        <View style={styles.item}>
          <Text style={[styles.label, { color: theme.textTertiary }]}>IN UNCERTAINTY</Text>
          <Text style={[styles.value, { color: theme.text }]}>{summary.in_uncertainty}</Text>
        </View>
        
        <View style={styles.item}>
          <Text style={[styles.label, { color: theme.textTertiary }]}>WHAT HELPS MOST</Text>
          <Text style={[styles.value, { color: theme.text }]}>{summary.what_helps}</Text>
        </View>
      </View>
      
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        You can adjust these anytime in Settings
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    padding: 20,
    borderWidth: 1,
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '500',
    marginBottom: 20,
    textAlign: 'center',
  },
  itemsContainer: {
    gap: 16,
  },
  item: {
    gap: 4,
  },
  label: {
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 0.8,
  },
  value: {
    fontSize: 15,
    lineHeight: 21,
  },
  footer: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 20,
    fontStyle: 'italic',
  },
});
