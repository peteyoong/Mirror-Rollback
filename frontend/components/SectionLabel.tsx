import React from 'react';
import { Text, StyleSheet, TextStyle, ViewStyle } from 'react-native';
import { sectionLabel } from '../constants/typography';

interface SectionLabelProps {
  children: string;
  style?: TextStyle;
  marginBottom?: number;
  marginTop?: number;
}

/**
 * SectionLabel - Reusable uppercase label component
 * 
 * Used for structural labels like:
 * - THE MIRROR
 * - TODAY
 * - REFLECT
 * - JOURNAL
 * - TIMELINE
 * 
 * Ensures consistent styling across all screens.
 */
export default function SectionLabel({ 
  children, 
  style,
  marginBottom = 12,
  marginTop = 0,
}: SectionLabelProps) {
  return (
    <Text 
      style={[
        styles.label,
        { marginBottom, marginTop },
        style,
      ]}
    >
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  label: {
    ...sectionLabel,
  },
});
