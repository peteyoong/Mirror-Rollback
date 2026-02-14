import React from 'react';
import { View, StyleSheet, Platform, ViewStyle, StatusBar as RNStatusBar } from 'react-native';
import { SafeAreaView, Edge } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Colors } from '../constants/colors';

interface AppScreenProps {
  children: React.ReactNode;
  edges?: Edge[];
  style?: ViewStyle;
  noPadding?: boolean;
}

/**
 * AppScreen - Reusable dark-themed screen wrapper
 * 
 * Ensures:
 * - Dark background (#111214) on all views
 * - SafeAreaView with proper insets
 * - StatusBar styled for dark theme
 * - Consistent padding unless noPadding is set
 */
export default function AppScreen({ 
  children, 
  edges = ['top', 'bottom'],
  style,
  noPadding = false,
}: AppScreenProps) {
  return (
    <View style={styles.rootContainer}>
      <StatusBar style="light" />
      <SafeAreaView style={[styles.safeArea, style]} edges={edges}>
        <View style={[styles.content, noPadding && styles.noPadding]}>
          {children}
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  rootContainer: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  safeArea: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  noPadding: {
    padding: 0,
  },
});
