import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Platform, Pressable } from 'react-native';
import { API_BASE_URL, API_URL_MISSING, joinUrl } from '../services/api';

/**
 * BUILD TAG: 2026-02-14-connectivity-probe
 * 
 * DebugOverlay - Connectivity + Touch Probe (dev only)
 * 
 * CRITICAL: All wrappers use pointerEvents="none" to NEVER intercept touches
 * 
 * Shows:
 * - API_BASE_URL (resolved)
 * - reflectionChatUrl (final)
 * - lastHttpStatus / lastResponseText / lastError
 * - pingStatus (ok/fail)
 * - touchProbeCount (proves no overlay is blocking)
 */

// Toggle this to enable/disable the debug overlay globally
const DEBUG_OVERLAY_ENABLED = true;

// Global state for debug info (can be updated from other components)
export interface DebugInfo {
  lastHttpStatus: number | null;
  lastResponseText: string;
  lastError: string;
  pingStatus: 'pending' | 'ok' | 'fail';
  pingError: string;
}

// Global debug state - can be updated from other components
let globalDebugInfo: DebugInfo = {
  lastHttpStatus: null,
  lastResponseText: '',
  lastError: '',
  pingStatus: 'pending',
  pingError: '',
};

let debugListeners: ((info: DebugInfo) => void)[] = [];

export function updateDebugInfo(partial: Partial<DebugInfo>) {
  globalDebugInfo = { ...globalDebugInfo, ...partial };
  debugListeners.forEach(fn => fn(globalDebugInfo));
}

export function getDebugInfo(): DebugInfo {
  return globalDebugInfo;
}

interface DebugOverlayProps {
  extra?: Record<string, any>;
}

export default function DebugOverlay({ extra = {} }: DebugOverlayProps) {
  const [debugInfo, setDebugInfo] = useState<DebugInfo>(globalDebugInfo);
  const [touchProbeCount, setTouchProbeCount] = useState(0);
  const [expanded, setExpanded] = useState(false);
  
  // Subscribe to debug info updates
  useEffect(() => {
    const listener = (info: DebugInfo) => setDebugInfo(info);
    debugListeners.push(listener);
    return () => {
      debugListeners = debugListeners.filter(fn => fn !== listener);
    };
  }, []);
  
  // Run ping on mount
  useEffect(() => {
    async function runPing() {
      try {
        const pingUrl = joinUrl(API_BASE_URL, '/debug/ping');
        const response = await fetch(pingUrl, {
          method: 'GET',
          credentials: 'omit',
        });
        if (response.ok) {
          updateDebugInfo({ pingStatus: 'ok', pingError: '' });
        } else {
          updateDebugInfo({ pingStatus: 'fail', pingError: `HTTP ${response.status}` });
        }
      } catch (err: any) {
        updateDebugInfo({ pingStatus: 'fail', pingError: err.message || 'Network error' });
      }
    }
    runPing();
  }, []);
  
  // Completely disable overlay when flag is false
  if (!DEBUG_OVERLAY_ENABLED) {
    return null;
  }
  
  const reflectionChatUrl = joinUrl(API_BASE_URL, '/reflection/chat');
  
  // P0 FIX: Entire overlay uses pointerEvents="none"
  // EXCEPT for the touch probe button which needs to capture touches to prove overlays are gone
  return (
    <View style={styles.container} pointerEvents="box-none">
      {/* Collapsed header - clickable */}
      <Pressable 
        style={styles.header} 
        onPress={() => setExpanded(!expanded)}
      >
        <Text style={styles.headerText}>
          🔧 DEBUG {debugInfo.pingStatus === 'ok' ? '✓' : debugInfo.pingStatus === 'fail' ? '✗' : '...'}
        </Text>
        <Text style={styles.headerToggle}>{expanded ? '▲' : '▼'}</Text>
      </Pressable>
      
      {expanded && (
        <View style={styles.content} pointerEvents="box-none">
          {/* Touch Probe - MUST be clickable to prove no overlay is blocking */}
          <Pressable 
            style={styles.touchProbe}
            onPress={() => {
              setTouchProbeCount(c => c + 1);
              console.log('[TouchProbe] Tapped! Count:', touchProbeCount + 1);
            }}
          >
            <Text style={styles.touchProbeText}>👆 Touch Probe: {touchProbeCount}</Text>
          </Pressable>
          
          {/* Rest of debug info - pointerEvents none */}
          <View pointerEvents="none">
            <Text style={styles.row}>
              <Text style={styles.label}>API_URL_MISSING: </Text>
              <Text style={API_URL_MISSING ? styles.error : styles.ok}>{String(API_URL_MISSING)}</Text>
            </Text>
            
            <Text style={styles.row} numberOfLines={1}>
              <Text style={styles.label}>API: </Text>
              <Text style={styles.value}>{API_BASE_URL || '(none)'}</Text>
            </Text>
            
            <Text style={styles.row} numberOfLines={1}>
              <Text style={styles.label}>Chat URL: </Text>
              <Text style={styles.value}>{reflectionChatUrl}</Text>
            </Text>
            
            <Text style={styles.row}>
              <Text style={styles.label}>Ping: </Text>
              <Text style={debugInfo.pingStatus === 'ok' ? styles.ok : debugInfo.pingStatus === 'fail' ? styles.error : styles.value}>
                {debugInfo.pingStatus} {debugInfo.pingError ? `(${debugInfo.pingError})` : ''}
              </Text>
            </Text>
            
            <Text style={styles.row}>
              <Text style={styles.label}>lastHttpStatus: </Text>
              <Text style={debugInfo.lastHttpStatus === 200 ? styles.ok : debugInfo.lastHttpStatus ? styles.error : styles.value}>
                {debugInfo.lastHttpStatus ?? '(none)'}
              </Text>
            </Text>
            
            {debugInfo.lastError ? (
              <Text style={styles.row}>
                <Text style={styles.label}>lastError: </Text>
                <Text style={styles.error}>{debugInfo.lastError}</Text>
              </Text>
            ) : null}
            
            {debugInfo.lastResponseText ? (
              <Text style={styles.row} numberOfLines={3}>
                <Text style={styles.label}>Response: </Text>
                <Text style={styles.code}>{debugInfo.lastResponseText.slice(0, 300)}</Text>
              </Text>
            ) : null}
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 9999,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.95)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    borderBottomWidth: 1,
    borderBottomColor: '#FF6B00',
  },
  headerText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#FF6B00',
  },
  headerToggle: {
    fontSize: 10,
    color: '#FF6B00',
  },
  content: {
    backgroundColor: 'rgba(0,0,0,0.95)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#FF6B00',
  },
  touchProbe: {
    backgroundColor: '#003300',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#00FF88',
  },
  touchProbeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#00FF88',
    textAlign: 'center',
  },
  row: {
    fontSize: 9,
    color: '#AAA',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 2,
  },
  label: {
    color: '#888',
    fontWeight: '600',
  },
  value: {
    color: '#AAA',
  },
  ok: {
    color: '#00FF88',
    fontWeight: '700',
  },
  error: {
    color: '#FF4444',
    fontWeight: '700',
  },
  code: {
    color: '#AADDFF',
    fontSize: 8,
  },
});
