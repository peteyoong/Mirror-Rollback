/**
 * Debug Overlay Component
 * =======================
 * 
 * A lightweight debug panel that shows environment info when:
 * - URL contains ?debug=1 (web)
 * - __DEV__ is true (native)
 * 
 * Shows:
 * - Frontend build version
 * - API base URL
 * - Backend health check response
 */

import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Platform, TouchableOpacity } from 'react-native';
import { BUILD_VERSION, BUILD_ID, getApiBaseUrl } from '../utils/buildInfo';

// ============================================
// FRONTEND BUILD ID (update on each deploy)
// ============================================
export const FRONTEND_BUILD_ID = 'v16-debug-overlay';

// ============================================
// Debug Flag Helper
// ============================================
export function getDebugFlag(): boolean {
  // Native: use __DEV__
  if (Platform.OS !== 'web') {
    return __DEV__;
  }
  
  // Web: check URL query param
  if (typeof window !== 'undefined' && window.location) {
    const params = new URLSearchParams(window.location.search);
    return params.get('debug') === '1';
  }
  
  return false;
}

// ============================================
// Health Check Response Type
// ============================================
interface HealthResponse {
  build: string;
  env: string;
  timestamp_utc: string;
  git_sha: string | null;
  db_name: string;
}

// ============================================
// Debug Overlay Component
// ============================================
export function DebugOverlay() {
  const [isDebug, setIsDebug] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  
  const apiBaseUrl = getApiBaseUrl();
  
  // Check debug flag on mount
  useEffect(() => {
    setIsDebug(getDebugFlag());
  }, []);
  
  // Fetch health on mount (only if debug mode)
  useEffect(() => {
    if (!isDebug) return;
    
    const fetchHealth = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/health`);
        if (!response.ok) throw new Error('Health check failed');
        const data = await response.json();
        setHealth(data);
        setHealthError(false);
      } catch (err) {
        console.error('[DebugOverlay] Health check error:', err);
        setHealthError(true);
      }
    };
    
    fetchHealth();
  }, [isDebug, apiBaseUrl]);
  
  // Don't render if not in debug mode
  if (!isDebug) return null;
  
  return (
    <TouchableOpacity 
      style={styles.overlay}
      onPress={() => setCollapsed(!collapsed)}
      activeOpacity={0.9}
    >
      <Text style={styles.title}>🔧 DEBUG</Text>
      
      {!collapsed && (
        <>
          {/* Frontend Info */}
          <Text style={styles.section}>Frontend:</Text>
          <Text style={styles.text}>BUILD: {FRONTEND_BUILD_ID}</Text>
          <Text style={styles.text}>VERSION: {BUILD_VERSION}</Text>
          <Text style={styles.text}>API: {apiBaseUrl}</Text>
          
          {/* Backend Health */}
          <Text style={styles.section}>Backend:</Text>
          {healthError ? (
            <Text style={styles.error}>health: error</Text>
          ) : health ? (
            <>
              <Text style={styles.text}>build: {health.build}</Text>
              <Text style={styles.text}>env: {health.env}</Text>
              <Text style={styles.text}>git: {health.git_sha || 'n/a'}</Text>
              <Text style={styles.text}>db: {health.db_name}</Text>
            </>
          ) : (
            <Text style={styles.text}>loading...</Text>
          )}
          
          <Text style={styles.hint}>(tap to collapse)</Text>
        </>
      )}
      
      {collapsed && (
        <Text style={styles.hint}>(tap to expand)</Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  overlay: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 50 : 10,
    right: 10,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    borderRadius: 8,
    padding: 10,
    minWidth: 180,
    maxWidth: 250,
    zIndex: 99999,
    elevation: 99999,
    borderWidth: 1,
    borderColor: '#00FF00',
  },
  title: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#00FF00',
    marginBottom: 6,
  },
  section: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#00FFFF',
    marginTop: 4,
    marginBottom: 2,
  },
  text: {
    fontSize: 9,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#00FF00',
    marginBottom: 1,
  },
  error: {
    fontSize: 9,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#FF6B6B',
  },
  hint: {
    fontSize: 8,
    color: '#888',
    marginTop: 4,
    textAlign: 'center',
  },
});

export default DebugOverlay;
