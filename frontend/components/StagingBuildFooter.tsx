/**
 * Staging Build Footer (Minimal Pill)
 * ====================================
 * 
 * A minimal, non-intrusive indicator for staging builds.
 * Designed for external testers - production-grade UX with clear staging identification.
 * 
 * Features:
 * - COLLAPSED by default (tiny pill)
 * - Tap to expand details
 * - NO auto-expand on any action
 * - Uses pointerEvents="box-none" so it NEVER blocks touches
 * - Positioned ABOVE the tab bar
 * 
 * Only visible when EXPO_PUBLIC_ENV === 'staging'
 */

import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, Platform, Pressable } from 'react-native';
import { API_BASE_URL } from '../utils/apiBase';

const TAB_BAR_HEIGHT = 72;      // matches tab bar height

// Environment check
const IS_STAGING = process.env.EXPO_PUBLIC_ENV === 'staging';

// Build info
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'unknown';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';
const APP_ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';

interface StagingBuildFooterProps {
  // Optional overrides for testing
  env?: string;
  api?: string;
  buildVersion?: string;
  buildId?: string;
  host?: string;
  db?: string;
  dbName?: string;
  inf?: string;
  inferenceVersion?: string;
}

export function StagingBuildFooter(props: StagingBuildFooterProps) {
  // Don't render in non-staging environments
  if (!IS_STAGING) {
    return null;
  }

  // Use props or fall back to env vars / defaults
  const env = props?.env || APP_ENV.toUpperCase();
  const api = props?.api || API_BASE_URL;
  const buildVersion = props?.buildVersion || BUILD_VERSION;
  const buildId = props?.buildId || BUILD_ID;
  
  // Get host - window.location.host on web, 'native' on mobile
  const [host, setHost] = useState(props?.host || 'native');
  const db = props?.db || props?.dbName || '--';
  const inf = props?.inf || props?.inferenceVersion || 'v2';

  // COLLAPSED by default - user must tap to expand
  const [expanded, setExpanded] = useState(false);

  // Get window host on web
  useEffect(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      setHost(window.location?.host || 'unknown');
    }
  }, []);

  const collapsedLine = useMemo(() => {
    const shortId = typeof buildId === 'string' ? buildId.slice(-8) : String(buildId);
    return `STAGING • ${buildVersion}`;
  }, [buildVersion]);

  return (
    // IMPORTANT: box-none means this wrapper will NOT block touches behind it.
    <View pointerEvents="box-none" style={styles.wrap}>
      {/* Minimal pill - only expands on tap */}
      <Pressable
        onPress={() => setExpanded(v => !v)}
        hitSlop={8}
        style={styles.pill}
      >
        {expanded ? (
          <View style={styles.expandedContent}>
            <Text style={styles.linePrimary}>STAGING BUILD</Text>
            <Text style={styles.line}>{buildVersion} ({buildId.slice(-10)})</Text>
            <Text style={styles.line}>API: {api}</Text>
            <Text style={styles.line}>HOST: {host}</Text>
            <Text style={styles.hint}>Tap to collapse</Text>
          </View>
        ) : (
          <Text style={styles.collapsedText}>{collapsedLine}</Text>
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    position: 'absolute',
    left: 0,
    right: 0,

    // Put it ABOVE the bottom tab bar so it can't block tab taps:
    bottom: TAB_BAR_HEIGHT + (Platform.OS === 'ios' ? 10 : 8),

    alignItems: 'center',
    zIndex: 9999,
  },
  pill: {
    maxWidth: '96%',
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: 'rgba(0,0,0,0.45)',
    borderWidth: 1,
    borderColor: 'rgba(0,229,255,0.25)',
  },
  pillPinned: {
    borderColor: 'rgba(201,169,98,0.55)', // subtle gold when pinned
  },
  linePrimary: {
    fontSize: 12,
    lineHeight: 14,
    color: '#00E5FF',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  details: {
    marginTop: 6,
  },
  line: {
    fontSize: 11,
    lineHeight: 14,
    color: '#00E5FF',
    textAlign: 'center',
    opacity: 0.95,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  hint: {
    marginTop: 6,
    fontSize: 10,
    lineHeight: 13,
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
  },
});

export default StagingBuildFooter;
