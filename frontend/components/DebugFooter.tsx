import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import Constants from 'expo-constants';

// Enable debug mode via environment variable - GATED behind DEBUG_MIRROR
// To enable: set DEBUG_MIRROR=true in environment
const DEBUG_MIRROR = Constants.expoConfig?.extra?.DEBUG_MIRROR === 'true' || 
                     process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true' ||
                     process.env.DEBUG_MIRROR === 'true';

// Export for use in other components
export const isDebugEnabled = () => DEBUG_MIRROR;

interface SectionDebugInfo {
  label: string;
  body: string;
}

interface DebugStamp {
  fallback_used?: boolean;
  source?: string;
  timestamp?: string;
  cached?: boolean;
}

interface Props {
  lens: string;
  sections: SectionDebugInfo[];
  source?: string;  // 'cache', 'llm', 'fallback'
  rawDataLength?: number;  // Total chars from API response
  debugStamp?: DebugStamp;
  extraDebug?: Record<string, any>;  // Additional debug info
}

// Individual Section Debug - shows inline with each section
export function SectionDebug({ label, body, index }: { label: string; body: string; index: number }) {
  if (!DEBUG_MIRROR) return null;
  
  const chars = body?.length || 0;
  const words = body?.split(' ').length || 0;
  const truncated = body?.endsWith('...') || body?.endsWith('…');
  const short = words < 100;
  
  return (
    <View style={styles.sectionDebug}>
      <Text style={[
        styles.sectionDebugText,
        short && styles.sectionDebugWarning,
        truncated && styles.sectionDebugError
      ]}>
        [{index+1}] {chars}c / {words}w {truncated ? '⚠️TRUNC' : ''} {short ? '⚠️SHORT' : '✓'}
      </Text>
    </View>
  );
}

export default function DebugFooter({ lens, sections, source, rawDataLength, debugStamp, extraDebug }: Props) {
  if (!DEBUG_MIRROR) return null;

  const totalChars = sections.reduce((sum, s) => sum + (s.body?.length || 0), 0);
  const totalWords = sections.reduce((sum, s) => sum + (s.body?.split(' ').length || 0), 0);
  const shortSections = sections.filter(s => (s.body?.split(' ').length || 0) < 100).length;
  const truncatedSections = sections.filter(s => s.body?.endsWith('...') || s.body?.endsWith('…')).length;

  // Calculate if there's a mismatch between raw API data and rendered data
  const dataMismatch = rawDataLength && Math.abs(rawDataLength - totalChars) > 50;

  return (
    <View style={styles.container}>
      <Text style={styles.header}>🔍 DEBUG: {lens.toUpperCase()}</Text>
      
      {/* Source info */}
      <Text style={styles.info}>
        Source: {debugStamp?.source || source || 'unknown'} | 
        Cached: {debugStamp?.cached ? 'YES' : 'NO'} | 
        Fallback: {debugStamp?.fallback_used ? 'YES' : 'NO'}
      </Text>
      
      {/* Summary stats */}
      <Text style={styles.info}>
        Sections: {sections.length} | Total: {totalChars}c / {totalWords}w
      </Text>
      
      {/* Data integrity check */}
      {rawDataLength && (
        <Text style={[styles.info, dataMismatch && styles.error]}>
          API Response: {rawDataLength}c | Rendered: {totalChars}c | 
          {dataMismatch ? ' ⚠️ MISMATCH!' : ' ✓ Match'}
        </Text>
      )}
      
      {/* Extra debug info (e.g., profile data) */}
      {extraDebug && (
        <View style={styles.extraDebugContainer}>
          {Object.entries(extraDebug).map(([key, value]) => (
            <Text key={key} style={styles.extraDebugLine}>
              {key}: {String(value)}
            </Text>
          ))}
        </View>
      )}
      
      {/* Warnings summary */}
      {(shortSections > 0 || truncatedSections > 0) && (
        <Text style={styles.warningLine}>
          ⚠️ Issues: {shortSections} short, {truncatedSections} truncated
        </Text>
      )}
      
      {/* Per-section breakdown */}
      <View style={styles.sectionsContainer}>
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
              {i+1}. {section.label?.substring(0, 20)}.. | {chars}c/{words}w {truncated ? '⛔' : ''} {short ? '⚠️' : '✓'}
            </Text>
          );
        })}
      </View>
      
      {/* Timestamp */}
      {debugStamp?.timestamp && (
        <Text style={styles.timestamp}>Generated: {debugStamp.timestamp}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(0,0,0,0.9)',
    padding: 12,
    marginTop: 16,
    marginBottom: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#00FF00',
  },
  header: {
    color: '#00FF00',
    fontSize: 13,
    fontWeight: 'bold',
    marginBottom: 6,
  },
  info: {
    color: '#FFFFFF',
    fontSize: 11,
    marginBottom: 3,
  },
  warningLine: {
    color: '#FFAA00',
    fontSize: 11,
    fontWeight: 'bold',
    marginTop: 4,
    marginBottom: 4,
  },
  sectionsContainer: {
    marginTop: 6,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.2)',
  },
  section: {
    color: '#AAAAAA',
    fontSize: 10,
    marginLeft: 4,
    marginBottom: 2,
  },
  warning: {
    color: '#FFAA00',
  },
  error: {
    color: '#FF0000',
    fontWeight: 'bold',
  },
  timestamp: {
    color: '#666666',
    fontSize: 9,
    marginTop: 6,
    fontStyle: 'italic',
  },
  // Section-level inline debug
  sectionDebug: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginTop: 4,
    alignSelf: 'flex-start',
  },
  sectionDebugText: {
    color: '#00FF00',
    fontSize: 9,
    fontFamily: 'monospace',
  },
  sectionDebugWarning: {
    color: '#FFAA00',
  },
  sectionDebugError: {
    color: '#FF0000',
  },
  extraDebugContainer: {
    marginTop: 4,
    paddingTop: 4,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,255,255,0.3)',
  },
  extraDebugLine: {
    color: '#00FFFF',
    fontSize: 10,
    marginBottom: 2,
  },
});
