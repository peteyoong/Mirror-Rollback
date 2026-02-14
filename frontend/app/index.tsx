import { Redirect } from 'expo-router';
import { useAppStore } from '../store';

export default function Index() {
  const { user, hasTriedSessionRestore, isRestoringSession } = useAppStore();

  // Don't redirect until session restore is complete
  // This prevents the race condition where we redirect to welcome
  // before the session has been restored
  if (!hasTriedSessionRestore || isRestoringSession) {
    // The root _layout.tsx shows the loading screen, so we just return null here
    return null;
  }

  // If user exists, go directly to tabs (skip welcome screen)
  if (user) {
    return <Redirect href="/(tabs)" />;
  }

  // No user - go to welcome page for login/onboarding
  return <Redirect href="/welcome" />;
}
