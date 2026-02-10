import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { Colors } from '../constants/colors';

interface Props {
  visible: boolean;
  testID?: string;
}

/**
 * Preliminary View Label
 * ======================
 * A subtle label shown near the type header when result_is_preliminary = true.
 * Disappears automatically once a deep assessment exists.
 * 
 * Design: Non-intrusive, informative, never blocking.
 */
export default function PreliminaryLabel({ visible, testID }: Props) {
  if (!visible) return null;
  
  return (
    <View style={styles.container} testID={testID}>
      <View style={styles.dot} />
      <Text style={styles.text}>Preliminary view</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 4,
    paddingHorizontal: 10,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    alignSelf: 'center',
    marginTop: 8,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.textTertiary,
  },
  text: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontWeight: '500',
  },
});
