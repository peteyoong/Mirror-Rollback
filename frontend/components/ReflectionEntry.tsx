import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Colors } from '../constants/colors';

interface ReflectionEntryProps {
  onPress: () => void;
}

/**
 * Reflection Entry - Layer 2 of Daily Flow
 * 
 * A subtle, optional entry point to reflection.
 * Must feel optional - no icons, no urgency.
 * 
 * "The user should feel: I can just be here."
 */
export default function ReflectionEntry({ onPress }: ReflectionEntryProps) {
  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.entry}
        onPress={onPress}
        activeOpacity={0.7}
      >
        <Text style={styles.entryText}>Reflect</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 16,
    alignItems: 'center',
  },
  entry: {
    paddingVertical: 12,
    paddingHorizontal: 32,
  },
  entryText: {
    fontSize: 15,
    color: Colors.textSecondary,
    fontWeight: '400',
    letterSpacing: 0.3,
  },
});
