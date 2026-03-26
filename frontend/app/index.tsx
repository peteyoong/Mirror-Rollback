import { Redirect } from 'expo-router';
import { useAppStore } from '../store';

/**
 * App Entry Point - Smart Routing Based on User State
 * 
 * ROUTING LOGIC:
 * 1. Wait for session restore to complete
 * 2. If user is authenticated AND onboarding complete → go to /home (tabs)
 * 3. Otherwise → go to /welcome
 */
export default function Index() {
  const { 
    hasTriedSessionRestore, 
    isRestoringSession, 
    user, 
    hasCompletedOnboarding 
  } = useAppStore();

  // Don't redirect until session restore is complete
  // This prevents the race condition where we redirect to welcome
  // before the session has been restored
  if (!hasTriedSessionRestore || isRestoringSession) {
    // The root _layout.tsx shows the loading screen, so we just return null here
    return null;
  }

  // Check user state
  const isAuthenticated = !!user?.id;
  
  // RETURNING USER PATH:
  // If authenticated AND onboarding complete → skip welcome, go directly to home
  if (isAuthenticated && hasCompletedOnboarding) {
    console.log('[Index] Returning user detected → routing to /home');
    return <Redirect href="/(tabs)" />;
  }

  // NEW USER / INCOMPLETE ONBOARDING PATH:
  // Go to welcome page for new users or users who haven't completed onboarding
  console.log('[Index] New user or incomplete onboarding → routing to /welcome');
  return <Redirect href="/welcome" />;
}
