// ============================================
// CROSS-LENS PATTERN BRIDGE
// ============================================
// Shows patterns that appear across multiple lenses
// "This pattern isn't coming from just one place."

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { getCrossLensSignals, shouldShowCrossLensBridge, CrossLensInput } from '../utils/crossLensMatcher';

interface CrossLensPatternBridgeProps {
  // From Human Design
  hdTypePattern?: string;
  hdAuthorityPattern?: string;
  
  // From Astrology
  astroAxisLines?: string[];
  astroMostImportantFactors?: string[];
  astroChartSpine?: string[];
  
  // From Pattern Engine (journal)
  compressedPatternLine?: string;
  selectedFacet?: string;
  facetLine?: string;
}

export const CrossLensPatternBridge: React.FC<CrossLensPatternBridgeProps> = ({
  hdTypePattern,
  hdAuthorityPattern,
  astroAxisLines,
  astroMostImportantFactors,
  astroChartSpine,
  compressedPatternLine,
  selectedFacet,
  facetLine,
}) => {
  const { theme } = useTheme();
  
  // Build input and get signals
  const input: CrossLensInput = {
    hdTypePattern,
    hdAuthorityPattern,
    astroAxisLines,
    astroMostImportantFactors,
    astroChartSpine,
    compressedPatternLine,
    selectedFacet,
    facetLine,
  };
  
  const signals = getCrossLensSignals(input);
  
  // Don't render if no cross-lens signals found
  if (!shouldShowCrossLensBridge(signals)) {
    return null;
  }
  
  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.textTertiary }]}>SEEN ACROSS YOUR PATTERNS</Text>
        <Text style={[styles.subtitle, { color: theme.textTertiary }]}>
          This pattern isn't coming from just one place.
        </Text>
      </View>
      
      <View style={styles.signalList}>
        {signals.map((signal, index) => (
          <View key={index} style={styles.signalItem}>
            <Text style={[styles.bullet, { color: theme.accent }]}>•</Text>
            <Text style={[styles.signalText, { color: theme.text }]}>{signal}</Text>
          </View>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 10,
    padding: 14,
    marginBottom: 14,
    borderWidth: StyleSheet.hairlineWidth,
  },
  header: {
    marginBottom: 12,
  },
  title: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 12,
    fontStyle: 'italic',
    opacity: 0.8,
  },
  signalList: {
    gap: 8,
  },
  signalItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  bullet: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 1,
  },
  signalText: {
    fontSize: 14,
    lineHeight: 20,
    flex: 1,
  },
});

export default CrossLensPatternBridge;
