import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import LifeContextView from '../../components/LifeContextView';
import api from '../../services/api';

/**
 * Life Tab Screen
 * 
 * ARCHITECTURE RULE:
 * - Tabs (Relationships, Work, Self) ALWAYS visible
 * - Empty state renders INSIDE tabs, not replacing them
 * - No full-screen replacement for missing data
 * 
 * Structure:
 * <LifeScreen>
 *   <TopTabs /> (always rendered via LifeContextView)
 *   <TabContent>
 *     {hasData ? <Content /> : <EmptyState />}
 *   </TabContent>
 * </LifeScreen>
 */

export default function LifeScreen() {
  const { user } = useAppStore();
  const { theme, isDark } = useTheme();
  const router = useRouter();
  
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.id) {
      // Just check user exists, let LifeContextView handle data loading
      setLoading(false);
    }
  }, [user?.id]);

  // ONLY show loading if no user yet
  if (!user?.id || loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.accent} />
          {!user?.id && (
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              Loading...
            </Text>
          )}
        </View>
      </SafeAreaView>
    );
  }

  // ============================================================
  // ALWAYS RENDER TAB STRUCTURE
  // LifeContextView renders the tabs (Lifeline, Relationships, Work, Self)
  // Empty state handling is INSIDE each tab, not replacing the screen
  // ============================================================
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <LifeContextView 
        userId={user.id}
        initialContext="lifeline"
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
  },
});
