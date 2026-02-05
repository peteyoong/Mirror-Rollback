import { Redirect } from 'expo-router';
import { useAppStore } from '../store';

export default function Index() {
  const { hasTriedSessionRestore, isRestoringSession } = useAppStore();

  // Don't redirect until session restore is complete
  // This prevents the race condition where we redirect to welcome
  // before the session has been restored
  if (!hasTriedSessionRestore || isRestoringSession) {
    // The root _layout.tsx shows the loading screen, so we just return null here
    return null;
  }

  // Always go to welcome page first - it handles the routing based on user state
  return <Redirect href="/welcome" />;
}
