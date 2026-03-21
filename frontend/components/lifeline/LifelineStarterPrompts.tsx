/**
 * LifelineStarterPrompts
 * 
 * Clickable prompt chips for users with < 5 moments.
 * Reduces blank page anxiety by offering entry points.
 * 
 * Each chip prefills the add form with a starting point.
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

interface StarterPrompt {
  label: string;
  prefillTitle: string;
  category?: string;
}

const STARTER_PROMPTS: StarterPrompt[] = [
  { label: 'A turning point', prefillTitle: 'A turning point in my life', category: 'self' },
  { label: 'A difficult period', prefillTitle: 'A difficult period I went through', category: 'challenge' },
  { label: 'A moment I felt most alive', prefillTitle: 'A moment I felt most alive', category: 'joy' },
  { label: 'A relationship that changed me', prefillTitle: 'A relationship that changed me', category: 'relationship' },
  { label: 'A risk I took', prefillTitle: 'A risk I took', category: 'work' },
];

interface Props {
  eventCount: number;
  onSelectPrompt: (prefillTitle: string, category?: string) => void;
}

export default function LifelineStarterPrompts({ eventCount, onSelectPrompt }: Props) {
  const { theme } = useTheme();
  
  // Only show for users with < 5 moments
  if (eventCount >= 5) {
    return null;
  }
  
  return (
    <View style={styles.container}>
      <Text style={[styles.label, { color: theme.textSecondary }]}>
        You can start anywhere. Try one of these:
      </Text>
      
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chipsContainer}
      >
        {STARTER_PROMPTS.map((prompt, index) => (
          <TouchableOpacity
            key={prompt.label}
            style={[
              styles.chip,
              { 
                backgroundColor: theme.surface,
                borderColor: theme.border,
              }
            ]}
            onPress={() => onSelectPrompt(prompt.prefillTitle, prompt.category)}
            activeOpacity={0.7}
          >
            <Text style={[styles.chipText, { color: theme.text }]}>
              {prompt.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  chipsContainer: {
    flexDirection: 'row',
    gap: 8,
    paddingRight: 20,
  },
  chip: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 20,
    borderWidth: 1,
  },
  chipText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
