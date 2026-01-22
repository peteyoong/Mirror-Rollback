import { useEffect } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';

export default function Index() {
  const router = useRouter();
  const { hasCompletedOnboarding, user } = useAppStore();

  useEffect(() => {
    // Navigate based on onboarding status
    if (hasCompletedOnboarding && user) {
      router.replace('/(tabs)');
    } else {
      router.replace('/onboarding');
    }
  }, [hasCompletedOnboarding, user]);

  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.background }}>
      <ActivityIndicator size="large" color={Colors.textSecondary} />
    </View>
  );
}
