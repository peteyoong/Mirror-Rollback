import { Redirect } from 'expo-router';
import { useAppStore } from '../store';

export default function Index() {
  const { hasCompletedOnboarding, user } = useAppStore();

  // Navigate based on onboarding status
  if (hasCompletedOnboarding && user) {
    return <Redirect href="/(tabs)" />;
  }
  
  return <Redirect href="/onboarding" />;
}
