import React, { useEffect } from 'react';
import { View, Text, ActivityIndicator, TouchableOpacity, StyleSheet } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';

interface SessionRestoreWrapperProps {
  children: React.ReactNode;
}

export default function SessionRestoreWrapper({ children }: SessionRestoreWrapperProps) {
  const { 
    user, 
    chart, 
    isRestoringSession, 
    hasTriedSessionRestore,
    sessionRestoreError, 
    restoreSession,
    retrySessionRestore 
  } = useAppStore();
  
  useEffect(() => {
    // Only attempt restore if we haven't tried yet and don't have user/chart
    if (!hasTriedSessionRestore && !isRestoringSession && (!user || !chart)) {
      console.log('[SessionRestoreWrapper] Attempting session restore...');
      restoreSession();
    }
  }, [hasTriedSessionRestore, isRestoringSession, user, chart, restoreSession]);
  
  // Show loader while restoring or before first attempt
  if (isRestoringSession || !hasTriedSessionRestore) {
    return (
      <View style={styles.container}>
        <View style={styles.content}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Restoring your session...</Text>
          <Text style={styles.subText}>Loading your profile and chart data</Text>
        </View>
      </View>
    );
  }
  
  // Show error state with retry button (only if restore failed AND no user)
  if (sessionRestoreError && !user && !chart) {
    return (
      <View style={styles.container}>
        <View style={styles.content}>
          <Ionicons name="alert-circle-outline" size={48} color={Colors.error} />
          <Text style={styles.errorTitle}>Session Restore Failed</Text>
          <Text style={styles.errorText}>{sessionRestoreError}</Text>
          <TouchableOpacity 
            style={styles.retryButton}
            onPress={retrySessionRestore}
          >
            <Ionicons name="refresh" size={20} color={Colors.surface} />
            <Text style={styles.retryButtonText}>Reload my profile</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }
  
  // Render children (normal app flow)
  return <>{children}</>;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  content: {
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 22,
    fontWeight: '500',
    color: Colors.text,
    marginTop: 16,
  },
  subText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: '500',
    color: Colors.text,
    marginTop: 16,
  },
  errorText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 8,
  },
  retryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginTop: 16,
  },
  retryButtonText: {
    color: Colors.surface,
    fontSize: 16,
    fontWeight: '500',
  },
});
