import { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { View, ActivityIndicator } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';

export default function RootLayout() {
  const segments = useSegments();
  const router = useRouter();
  const { hasCompletedOnboarding, user, loadPersistedData } = useAppStore();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Load persisted data on app start
    loadPersistedData().then(() => {
      setTimeout(() => setIsReady(true), 100);
    });
  }, []);

  useEffect(() => {
    if (!isReady) return;

    // Use setTimeout to avoid navigation during render
    setTimeout(() => {
      const inTabsGroup = segments[0] === '(tabs)';
      const inOnboarding = segments[0] === 'onboarding';

      if (hasCompletedOnboarding && user) {
        // User has completed onboarding, navigate to main app
        if (!inTabsGroup && segments.length === 0) {
          router.replace('/(tabs)');
        }
      } else {
        // User hasn't completed onboarding, navigate to onboarding
        if (!inOnboarding && segments.length === 0) {
          router.replace('/onboarding');
        }
      }
    }, 0);
  }, [isReady, hasCompletedOnboarding, user]);

  if (!isReady) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.background }}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
      </View>
    );
  }

  return (
    <Stack screenOptions={{
      headerShown: false,
      contentStyle: { backgroundColor: Colors.background },
    }} />
  );
}
