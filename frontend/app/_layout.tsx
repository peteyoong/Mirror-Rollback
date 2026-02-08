import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';

export default function RootLayout() {
  const { 
    restoreSession, 
    isRestoringSession, 
    hasTriedSessionRestore 
  } = useAppStore();

  useEffect(() => {
    // Trigger session restore on app start
    console.log('[RootLayout] Starting session restore...');
    restoreSession();
  }, []);

  // Block rendering until we've tried to restore the session
  // This is the AUTH HYDRATION GATE
  if (!hasTriedSessionRestore || isRestoringSession) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
        <Text style={styles.loadingText}>Restoring your profile...</Text>
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

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.background,
    gap: 16,
    maxWidth: 400,
    alignSelf: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginTop: 12,
  },
});
