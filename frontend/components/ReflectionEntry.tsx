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
        activeOpacity={0.6}
      >
        <Text style={styles.entryText}>Reflect</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 4,
  },
  entry: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 6,
  },
  entryText: {
    fontSize: 13,
    color: Colors.textTertiary,
    fontWeight: '500',
    letterSpacing: 0.3,
  },
});
