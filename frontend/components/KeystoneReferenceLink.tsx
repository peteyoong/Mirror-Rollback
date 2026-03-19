/**
 * KeystoneReferenceLink.tsx
 * 
 * ARCHITECTURE LOCK: Lenses reference the Keystone, they don't display it.
 * 
 * This lightweight component shows:
 * "TODAY'S PATTERN → [pattern_label]"
 * 
 * Tapping navigates to Home tab where the full Keystone card lives.
 * Home = truth. Lenses = explanation.
 */

import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';

interface Props {
  patternLabel: string | null | undefined;
}

export default function KeystoneReferenceLink({ patternLabel }: Props) {
  const { theme } = useTheme();
  const router = useRouter();

  const handlePress = () => {
    // Navigate to Home tab
    router.push('/(tabs)');
  };

  if (!patternLabel) {
    return null;
  }

  return (
    <TouchableOpacity
      style={[styles.container, { borderBottomColor: theme.border }]}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <Text style={[styles.label, { color: theme.textTertiary }]}>
        TODAY'S PATTERN
      </Text>
      <View style={styles.row}>
        <Text style={[styles.patternLabel, { color: theme.text }]} numberOfLines={1}>
          {patternLabel}
        </Text>
        <Text style={[styles.arrow, { color: theme.accent }]}>→</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 4,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  patternLabel: {
    fontSize: 15,
    fontWeight: '500',
    flex: 1,
    marginRight: 8,
  },
  arrow: {
    fontSize: 18,
    fontWeight: '500',
  },
});
