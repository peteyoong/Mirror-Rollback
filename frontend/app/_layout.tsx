import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import WelcomeGate from '../components/WelcomeGate';

/**
 * ROOT LAYOUT - RESTORE DISABLED FOR DEBUGGING
 */
export default function RootLayout() {
  
  // Select stable primitives only
  const userId = useAppStore(s => s.user?.id);
  const isRestoringSession = useAppStore(s => s.isRestoringSession);
  const hasTriedSessionRestore = useAppStore(s => s.hasTriedSessionRestore);

  // STEP 1: DISABLED restoreSession - DO NOT CALL
  // useEffect(() => {
  //   useAppStore.getState().restoreSession();
  // }, []);
  
  // TEMP: Mark session restore as "tried" immediately so UI doesn't block
  useEffect(() => {
    console.log("[RootLayout] Setting hasTriedSessionRestore=true (NO restore call)");
    useAppStore.setState({ hasTriedSessionRestore: true, isRestoringSession: false });
  }, []);

  // Show loading while restoring - but we've disabled restore so this should be brief
  if (!hasTriedSessionRestore || isRestoringSession) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  // No user - show WelcomeGate
  if (!userId) {
    return <WelcomeGate />;
  }

  // User exists - render app
  return (
    <Stack screenOptions={{
      headerShown: false,
      contentStyle: { backgroundColor: Colors.background },
    }}>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="reflection-chat" options={{ presentation: 'modal' }} />
      <Stack.Screen name="welcome" options={{ headerShown: false }} />
    </Stack>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginTop: 12,
  },
});
