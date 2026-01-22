import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/constants/theme';

export default function Welcome() {
  const router = useRouter();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>Mirror</Text>
          <Text style={styles.subtitle}>A space for reflection</Text>
        </View>

        <View style={styles.middle}>
          <Text style={styles.quote}>
            "The mirror reflects all objects without being sullied."
          </Text>
        </View>

        <View style={styles.buttons}>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => router.push('/(auth)/register')}
          >
            <Text style={styles.primaryButtonText}>Begin</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.secondaryButton}
            onPress={() => router.push('/(auth)/login')}
          >
            <Text style={styles.secondaryButtonText}>I already have an account</Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: SPACING.lg,
    justifyContent: 'space-between',
    paddingVertical: SPACING.xxl,
  },
  header: {
    alignItems: 'center',
    paddingTop: SPACING.xxl,
  },
  title: {
    fontSize: 42,
    fontWeight: '300',
    color: COLORS.primary,
    letterSpacing: 4,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.secondary,
    marginTop: SPACING.sm,
    letterSpacing: 1,
  },
  middle: {
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
  },
  quote: {
    fontSize: 18,
    color: COLORS.secondary,
    textAlign: 'center',
    lineHeight: 28,
    fontStyle: 'italic',
  },
  buttons: {
    gap: SPACING.md,
  },
  primaryButton: {
    backgroundColor: COLORS.accent,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    paddingVertical: SPACING.md,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: COLORS.secondary,
    fontSize: 14,
  },
});
