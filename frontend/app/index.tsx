import { Redirect } from 'expo-router';
import { useAppStore } from '../store';

export default function Index() {
  const { user, hasTriedSessionRestore, isRestoringSession, shouldRedirectToOnboarding } = useAppStore();

  // Don't redirect until session restore is complete
  // This prevents the race condition where we redirect to onboarding
  // before the session has been restored
  if (!hasTriedSessionRestore || isRestoringSession) {
    // The root _layout.tsx shows the loading screen, so we just return null here
    return null;
  }

  // Navigate based on whether we should redirect to onboarding
  if (shouldRedirectToOnboarding()) {
    return <Redirect href="/onboarding" />;
  }
  
  // User exists - go to tabs
  return <Redirect href="/(tabs)" />;
}
