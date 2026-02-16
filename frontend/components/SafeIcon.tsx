/**
 * SafeIcon - Wrapper for Ionicons that prevents "Unexpected text node" errors
 * 
 * In React Native Web, icon fonts can sometimes render fallback characters
 * as text nodes inside Views, causing console errors. This wrapper ensures
 * the icon is always contained within a Text component.
 */

import React from 'react';
import { Text, StyleSheet, TextStyle, ViewStyle } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

type IoniconsName = React.ComponentProps<typeof Ionicons>['name'];

interface SafeIconProps {
  name: IoniconsName;
  size?: number;
  color?: string;
  style?: TextStyle | ViewStyle;
}

/**
 * SafeIcon wraps Ionicons in a Text component to prevent
 * "Unexpected text node" errors in React Native Web.
 * 
 * Usage:
 *   <SafeIcon name="chevron-forward" size={14} color="#666" />
 */
export function SafeIcon({ name, size = 24, color = '#000', style }: SafeIconProps) {
  return (
    <Text style={[styles.iconWrapper, style]}>
      <Ionicons name={name} size={size} color={color} />
    </Text>
  );
}

const styles = StyleSheet.create({
  iconWrapper: {
    // Ensure the wrapper doesn't add extra space
    lineHeight: undefined,
  },
});

export default SafeIcon;
