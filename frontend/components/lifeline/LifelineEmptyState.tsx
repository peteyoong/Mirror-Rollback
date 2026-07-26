/**
 * LifelineEmptyState
 * 
 * Shows when user has no lifeline events yet.
 * Encourages first event entry with a supportive tone.
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { useTheme } from '../../contexts/ThemeContext';

interface Props {
  onAddEvent: () => void;
}

export default function LifelineEmptyState({ onAddEvent }: Props) {
  const { theme } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      {/* Visual */}
      <View style={[styles.iconContainer, { backgroundColor: `${theme.accent}15` }]}>
        <Ionicons name="time-outline" size={32} color={theme.accent} />
      </View>

      {/* Message */}
      <Text style={[styles.title, { color: theme.text }]}>
        Your Lifeline begins here
      </Text>
      
      <Text style={[styles.description, { color: theme.textSecondary }]}>
        Start with one moment that changed something for you—a turning point, a loss, a beginning.
      </Text>

      <Text style={[styles.hint, { color: theme.textTertiary }]}>
        You can add more over time. There's no rush.
      </Text>

      {/* CTA */}
      <TouchableOpacity
        style={[styles.addButton, { backgroundColor: theme.accent }]}
        onPress={onAddEvent}
        activeOpacity={0.8}
      >
        <Ionicons name="add" size={18} color="#FFFFFF" />
        <Text style={styles.addButtonText}>Add your first moment</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 28,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 22,
    fontWeight: '500',
    marginBottom: 12,
    textAlign: 'center',
  },
  description: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 8,
    paddingHorizontal: 8,
  },
  hint: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
    marginBottom: 24,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 24,
    gap: 8,
  },
  addButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#FFFFFF',
  },
});
