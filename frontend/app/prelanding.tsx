import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../constants/colors';
import { useAppStore } from '../store';

export default function PreLandingScreen() {
  const router = useRouter();
  const { user } = useAppStore();

  // Get preferred name or fallback
  const preferredName = user?.name || 'friend';

  const handleEnterMirror = () => {
    router.replace('/(tabs)');
  };

  // If no user, redirect to threshold
  if (!user?.id) {
    router.replace('/threshold');
    return null;
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <View style={styles.content}>
        {/* Spacer to push content toward center */}
        <View style={styles.topSpacer} />

        {/* Main Content */}
        <View style={styles.mainContent}>
          {/* Title */}
          <Text style={styles.title}>
            Welcome back, {preferredName}
          </Text>

          {/* Body */}
          <Text style={styles.body}>
            Take a moment. Nothing needs to be figured out.
          </Text>
        </View>

        {/* Spacer */}
        <View style={styles.middleSpacer} />

        {/* CTA */}
        <View style={styles.ctaContainer}>
          <Pressable
            style={styles.ctaButton}
            onPress={handleEnterMirror}
          >
            <Text style={styles.ctaButtonText}>Enter the Mirror</Text>
          </Pressable>
        </View>

        {/* Bottom spacer for balance */}
        <View style={styles.bottomSpacer} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: 32,
  },
  topSpacer: {
    flex: 0.3,
  },
  mainContent: {
    alignItems: 'center',
  },
  title: {
    fontSize: 26,
    fontWeight: '300',
    color: Colors.text,
    marginBottom: 24,
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  body: {
    fontSize: 16,
    fontWeight: '400',
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 26,
  },
  middleSpacer: {
    flex: 0.35,
  },
  ctaContainer: {
    alignItems: 'center',
  },
  ctaButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 40,
    borderRadius: 12,
  },
  ctaButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
    letterSpacing: 0.3,
  },
  bottomSpacer: {
    flex: 0.2,
  },
});
