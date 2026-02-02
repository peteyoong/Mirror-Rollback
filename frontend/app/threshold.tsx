import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../constants/colors';
import { useAppStore } from '../store';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

export default function ThresholdScreen() {
  const router = useRouter();
  const { user, hasTriedSessionRestore, isRestoringSession } = useAppStore();

  // Determine if user has an existing session
  const hasExistingSession = !!user?.id;

  const handleBeginNewReflection = () => {
    // New users → onboarding
    router.push('/onboarding');
  };

  const handleContinueJourney = () => {
    // Existing users → pre-landing page before Mirror
    router.push('/prelanding');
  };

  // Show nothing while session is being restored
  if (!hasTriedSessionRestore || isRestoringSession) {
    return null;
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <View style={styles.content}>
        {/* Spacer to push content toward center-top */}
        <View style={styles.topSpacer} />

        {/* Main Content */}
        <View style={styles.mainContent}>
          {/* Title */}
          <Text style={styles.title}>Project Mirror</Text>

          {/* Subline */}
          <Text style={styles.subline}>
            A mirror for self-understanding — not a map of your future.
          </Text>

          {/* Body */}
          <View style={styles.bodyContainer}>
            <Text style={styles.bodyText}>
              This space reflects patterns and perspectives.
            </Text>
            <Text style={styles.bodyText}>
              Nothing here defines you. You decide what stays.
            </Text>
          </View>
        </View>

        {/* Spacer */}
        <View style={styles.middleSpacer} />

        {/* Actions */}
        <View style={styles.actionsContainer}>
          {/* Primary CTA */}
          <Pressable
            style={styles.primaryButton}
            onPress={handleBeginNewReflection}
          >
            <Text style={styles.primaryButtonText}>Begin a new reflection</Text>
          </Pressable>

          {/* Secondary CTA - only show if user has existing session */}
          {hasExistingSession && (
            <Pressable
              style={styles.secondaryButton}
              onPress={handleContinueJourney}
            >
              <Text style={styles.secondaryButtonText}>Continue my journey</Text>
            </Pressable>
          )}
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
    flex: 0.25,
  },
  mainContent: {
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: '300',
    color: Colors.text,
    letterSpacing: 1,
    marginBottom: 16,
    textAlign: 'center',
  },
  subline: {
    fontSize: 16,
    fontWeight: '400',
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 40,
    fontStyle: 'italic',
  },
  bodyContainer: {
    alignItems: 'center',
  },
  bodyText: {
    fontSize: 15,
    fontWeight: '400',
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
  middleSpacer: {
    flex: 0.35,
  },
  actionsContainer: {
    alignItems: 'center',
    gap: 16,
  },
  primaryButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    minWidth: 240,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.surface,
    letterSpacing: 0.3,
  },
  secondaryButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textTertiary,
  },
  bottomSpacer: {
    flex: 0.15,
  },
});
