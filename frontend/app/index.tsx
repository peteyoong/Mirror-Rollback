import { Redirect } from 'expo-router';

/**
 * BUILD TAG: 2026-02-14-nav-architecture-fix
 * 
 * Root Index - Simple redirect to tabs
 * 
 * The authentication/welcome gate is handled by _layout.tsx.
 * If this component renders, the user is already authenticated.
 * We simply redirect to the main tabs.
 */
export default function Index() {
  // User is authenticated (handled by _layout.tsx)
  // Go directly to tabs
  return <Redirect href="/(tabs)" />;
}
