/**
 * Staging Build Footer
 * ====================
 * 
 * Shows build info at the bottom of every screen in STAGING only.
 * 
 * ALWAYS VISIBLE in staging environment to verify:
 * - Testers are on the correct environment
 * - API_BASE_URL matches the deployed URL
 * - Build version and ID for debugging
 * 
 * DEBUG DIAGNOSTICS shown:
 * - BUILD_VERSION | BUILD_ID | ENV
 * - API_BASE_URL (hostname)
 * - HOST: window.location.host
 * - DB: database name from /api/health
 * - USER + ENNEAGRAM info when logged in
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAppStore } from '../store';

// Environment variables
const APP_ENV = process.env.EXPO_PUBLIC_ENV || 'unknown';
const BUILD_VERSION = process.env.EXPO_PUBLIC_BUILD_VERSION || 'dev';
const BUILD_ID = process.env.EXPO_PUBLIC_BUILD_ID || 'unknown';
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || 'not-set';
const DEBUG_MIRROR = process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

// Only show in staging
const IS_STAGING = APP_ENV === 'staging';

// Inference version - hardcoded since this is the unified version
const INFERENCE_VERSION = 'v2';

interface HealthInfo {
  env: string;
  db_name: string;
  build_version: string;
  inference_version: string;
}

interface EnneagramDebugInfo {
  result_id: string;
  updated_at: string;
  depth: string;
  confidence_tier: string;
  core_type: number | null;
  wing: string | number | null;
}

export const StagingBuildFooter: React.FC = () => {
  const insets = useSafeAreaInsets();
  const [showFooter, setShowFooter] = useState(false);
  const [windowHost, setWindowHost] = useState<string>('--');
  const [healthInfo, setHealthInfo] = useState<HealthInfo | null>(null);
  const [enneagramInfo, setEnneagramInfo] = useState<EnneagramDebugInfo | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  
  // Get user from store
  const user = useAppStore(s => s.user);
  const userId = user?.id || '--';
  
  // Check URL param on mount (client-side only)
  useEffect(() => {
    // Must be staging environment
    if (!IS_STAGING) {
      setShowFooter(false);
      return;
    }
    
    // ALWAYS show footer in staging for verification
    // This ensures testers can verify they're on the right environment
    setShowFooter(true);
  }, []);
  
  // Fetch debug info when footer is visible
  useEffect(() => {
    if (!showFooter) return;
    
    // Get window host (web only)
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      setWindowHost(window.location?.host || 'unknown');
    } else {
      setWindowHost('native');
    }
    
    // Fetch /api/health for env and db_name
    const fetchHealth = async () => {
      try {
        const response = await fetch('/api/health', {
          cache: 'no-store',
          headers: { 'Cache-Control': 'no-cache' }
        });
        if (response.ok) {
          const data = await response.json();
          setHealthInfo({
            env: data.env || 'unknown',
            db_name: data.db_name || 'unknown',
            build_version: data.build_version || 'unknown',
            inference_version: data.inference_version || 'unknown',
          });
          setHealthError(null);
        } else {
          setHealthError(`${response.status}`);
        }
      } catch (err: any) {
        setHealthError(err.message || 'fetch-error');
      }
    };
    
    fetchHealth();
  }, [showFooter]);
  
  // Fetch Enneagram result when user changes
  useEffect(() => {
    if (!showFooter || !userId || userId === '--') return;
    
    const fetchEnneagram = async () => {
      try {
        const response = await fetch(`/api/users/${userId}/enneagram/result`, {
          cache: 'no-store',
          headers: { 'Cache-Control': 'no-cache' }
        });
        if (response.ok) {
          const data = await response.json();
          setEnneagramInfo({
            result_id: data.id || data._id || '--',
            updated_at: data.created_at || data.updated_at || '--',
            depth: data.method || data.assessment_depth || '--',
            confidence_tier: data.confidence_tier || '--',
            core_type: data.inferred_core || null,
            wing: data.inferred_wing || null,
          });
        } else {
          setEnneagramInfo({
            result_id: '--',
            updated_at: '--',
            depth: `err:${response.status}`,
            confidence_tier: '--',
            core_type: null,
            wing: null,
          });
        }
      } catch (err: any) {
        setEnneagramInfo({
          result_id: '--',
          updated_at: '--',
          depth: 'fetch-err',
          confidence_tier: '--',
          core_type: null,
          wing: null,
        });
      }
    };
    
    fetchEnneagram();
  }, [showFooter, userId]);
  
  // Don't render if not showing - no layout shift
  if (!showFooter) {
    return null;
  }

  // Extract just the hostname from API_BASE_URL for brevity
  let apiHost = API_BASE_URL;
  try {
    const url = new URL(API_BASE_URL);
    apiHost = url.hostname;
  } catch {
    // Keep full value if not a valid URL
  }
  
  // Format timestamps for brevity
  const formatTimestamp = (ts: string) => {
    if (!ts || ts === '--') return '--';
    try {
      // Just show date and time portion
      const date = new Date(ts);
      return date.toISOString().slice(5, 16).replace('T', ' ');
    } catch {
      return ts.slice(-12);
    }
  };

  return (
    <View 
      style={[
        styles.container, 
        { paddingBottom: Math.max(insets.bottom, 4) }
      ]}
      pointerEvents="none"
    >
      {/* Row 1: Build info */}
      <Text style={styles.text}>
        BUILD: {BUILD_VERSION} | ID: {BUILD_ID.slice(-12)} | INF: {INFERENCE_VERSION}
      </Text>
      
      {/* Row 2: HOST + ENV */}
      <Text style={styles.textSmall}>
        HOST: {windowHost} | ENV: {healthInfo?.env || '--'} | DB: {healthInfo?.db_name || '--'}
      </Text>
      
      {/* Row 3: USER + ENNEAGRAM */}
      <Text style={styles.textSmall}>
        USER: {userId.slice(-8)} | 
        E: {enneagramInfo?.core_type ?? '--'}
        {enneagramInfo?.wing ? `w${enneagramInfo.wing}` : ''} 
        ({enneagramInfo?.confidence_tier?.slice(0, 3) || '--'}) 
        [{enneagramInfo?.depth?.slice(-6) || '--'}]
      </Text>
      
      {/* Row 4: Enneagram result ID and timestamp */}
      <Text style={styles.textTiny}>
        E_ID: {enneagramInfo?.result_id?.slice(-8) || '--'} | 
        TS: {formatTimestamp(enneagramInfo?.updated_at || '')}
        {healthError ? ` | ERR: ${healthError}` : ''}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    paddingVertical: 6,
    paddingHorizontal: 8,
    zIndex: 9999,
  },
  text: {
    color: '#00ff00',
    fontSize: 9,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'center',
  },
  textSmall: {
    color: '#00ff00',
    fontSize: 8,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'center',
    opacity: 0.9,
  },
  textTiny: {
    color: '#ffff00',
    fontSize: 7,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'center',
    opacity: 0.8,
  },
});

export default StagingBuildFooter;
