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
 * - Positioned in TOP-RIGHT corner to avoid blocking content
 * 
 * Only visible when EXPO_PUBLIC_ENV === 'staging'
 */

import React, { useEffect, useMemo, useState } from 'react';
import { View, Text, StyleSheet, Platform, Pressable } from 'react-native';
import { API_BASE_URL } from '../utils/apiBase';

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
    return `STAGING`;
  }, []);

  return (
    // Position in TOP-RIGHT corner to avoid blocking content
    <View pointerEvents="box-none" style={styles.wrap}>
      <Pressable
        onPress={() => setExpanded(v => !v)}
        hitSlop={8}
        style={[styles.pill, expanded && styles.pillExpanded]}
      >
        {expanded ? (
          <View style={styles.expandedContent}>
            <Text style={styles.linePrimary}>STAGING</Text>
            <Text style={styles.line}>{buildVersion}</Text>
            <Text style={styles.hint}>tap to hide</Text>
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
    // TOP-RIGHT corner - doesn't block any content
    top: Platform.OS === 'ios' ? 50 : 35,
    right: 12,
    zIndex: 9999,
  },
  pill: {
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: 'rgba(0,0,0,0.6)',
    borderWidth: 1,
    borderColor: 'rgba(0,229,255,0.3)',
  },
  pillExpanded: {
    backgroundColor: 'rgba(0,0,0,0.85)',
  },
  collapsedText: {
    fontSize: 9,
    fontWeight: '600',
    color: '#00E5FF',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  expandedContent: {
    alignItems: 'center',
    paddingVertical: 2,
  },
  linePrimary: {
    fontSize: 10,
    fontWeight: '600',
    color: '#00E5FF',
    textAlign: 'center',
    marginBottom: 2,
  },
  line: {
    fontSize: 9,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 2,
  },
  hint: {
    marginTop: 4,
    fontSize: 8,
    color: 'rgba(255,255,255,0.4)',
    textAlign: 'center',
  },
});

export default StagingBuildFooter;
