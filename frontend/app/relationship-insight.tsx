/**
 * Relationship Insight Screen — V2 3-Layer Architecture
 * 
 * Route: /relationship-insight?name=Mel&context=...
 * 
 * 3-Layer Progressive Reveal:
 * Layer 1 = STORY (Default view)
 * Layer 2 = PATTERNS (Scroll to reveal)
 * Layer 3 = SIGNALS (Expandable "Why this is so strong")
 */

import React from 'react';
import { View, StyleSheet, SafeAreaView, StatusBar } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useAppStore } from '../store';
import { useTheme } from '../contexts/ThemeContext';
import RelationshipInsightV2Card from '../components/RelationshipInsightV2Card';

export default function RelationshipInsightScreen() {
  const router = useRouter();
  const { user } = useAppStore();
  const { theme, isDark } = useTheme();
  
  // Get params from URL
  const { name, context } = useLocalSearchParams<{ name: string; context?: string }>();
  
  // Use logged in user or test user for development
  const userId = user?.id || '697f0c6abf35c0528ff06954';
  const otherName = name || 'Someone';
  const relationshipContext = context || '';

  const handleClose = () => {
    router.back();
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <StatusBar barStyle={isDark ? 'light-content' : 'dark-content'} />
      
      <View style={styles.content}>
        <RelationshipInsightV2Card
          userId={userId}
          otherName={otherName}
          relationshipContext={relationshipContext}
          theme={theme}
          onClose={handleClose}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 16,
  },
});
