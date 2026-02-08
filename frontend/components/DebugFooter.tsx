import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Constants from 'expo-constants';

// Enable debug mode via environment variable
const DEBUG_MIRROR = Constants.expoConfig?.extra?.DEBUG_MIRROR === 'true' || 
                     process.env.DEBUG_MIRROR === 'true' ||
                     __DEV__;  // Always show in development

interface SectionDebugInfo {
  label: string;
  body: string;
}

interface Props {
  lens: string;
  sections: SectionDebugInfo[];
  source?: string;  // 'cache', 'llm', 'fallback'
}

export default function DebugFooter({ lens, sections, source }: Props) {
  if (!DEBUG_MIRROR) return null;

  const totalChars = sections.reduce((sum, s) => sum + (s.body?.length || 0), 0);
  const totalWords = sections.reduce((sum, s) => sum + (s.body?.split(' ').length || 0), 0);

  return (
    <View style={styles.container}>
      <Text style={styles.header}>🔍 DEBUG: {lens.toUpperCase()}</Text>
      <Text style={styles.info}>Source: {source || 'unknown'} | Sections: {sections.length}</Text>
      <Text style={styles.info}>Total: {totalChars} chars / {totalWords} words</Text>
      {sections.map((section, i) => {
        const chars = section.body?.length || 0;
        const words = section.body?.split(' ').length || 0;
        const truncated = section.body?.endsWith('...') || section.body?.endsWith('…');
        const short = words < 100;
        return (
          <Text 
            key={i} 
            style={[styles.section, short && styles.warning, truncated && styles.error]}
          >
            {i+1}. {section.label?.substring(0, 25)}... | {chars}c/{words}w {truncated ? '⚠️TRUNCATED' : ''} {short ? '⚠️SHORT' : ''}
          </Text>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(0,0,0,0.8)',
    padding: 8,
    marginTop: 16,
    borderRadius: 8,
  },
  header: {
    color: '#00FF00',
    fontSize: 12,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  info: {
    color: '#FFFFFF',
    fontSize: 10,
    marginBottom: 2,
  },
  section: {
    color: '#AAAAAA',
    fontSize: 9,
    marginLeft: 8,
  },
  warning: {
    color: '#FFAA00',
  },
  error: {
    color: '#FF0000',
  },
});
