/**
 * PATTERNS TAB - V1 Redirect
 * 
 * Patterns V1 now lives on the HOME screen as "Today's Pattern"
 * This tab shows a simple redirect message.
 * 
 * Future: This tab may be repurposed or removed entirely.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';

export default function PatternsScreen() {
  const { theme } = useTheme();
  const router = useRouter();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.content}>
        <Text style={[styles.title, { color: theme.text }]}>
          Mirror shows you the pattern you're in right now
        </Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          You don't need to figure it out. Just notice it.
        </Text>
        <TouchableOpacity
          style={[styles.button, { backgroundColor: theme.accent }]}
          onPress={() => router.push('/(tabs)/')}
          activeOpacity={0.8}
        >
          <Text style={[styles.buttonText, { color: theme.textInverse }]}>
            Show me my pattern
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: '500',
    marginBottom: 12,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    marginBottom: 32,
  },
  button: {
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '500',
  },
});
