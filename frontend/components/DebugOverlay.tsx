import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Platform, Pressable } from 'react-native';
import { API_BASE_URL, API_URL_MISSING, joinUrl } from '../services/api';
import { useAppStore } from '../store';

/**
 * BUILD TAG: 2026-02-14-send-debug-v2
 * 
 * DebugOverlay - Full debug visibility for chat debugging
 * 
 * Shows (BIG + OBVIOUS):
 * - BUILD_ID
 * - userId (from store)
 * - sendPressCount (proves button fires)
 * - lastSendAt
 * - lastBailReason
 * - lastFetchUrl
 * - lastHttpStatus
 * - lastError
 */

// BUILD ID - change this to verify you're on the right build
const BUILD_ID = 'v2-send-debug-2026-02-14';

// Toggle this to enable/disable the debug overlay globally
const DEBUG_OVERLAY_ENABLED = true;

// Global state for debug info (can be updated from other components)
export interface DebugInfo {
  lastHttpStatus: number | null;
  lastResponseText: string;
  lastError: string;
  pingStatus: 'pending' | 'ok' | 'fail';
  pingError: string;
  // NEW: Send button debug fields
  sendPressCount: number;
  lastSendAt: string;
  lastBailReason: string;
  lastFetchUrl: string;
}

// Global debug state - can be updated from other components
let globalDebugInfo: DebugInfo = {
  lastHttpStatus: null,
  lastResponseText: '',
  lastError: '',
  pingStatus: 'pending',
  pingError: '',
  // NEW fields
  sendPressCount: 0,
  lastSendAt: '',
  lastBailReason: '',
  lastFetchUrl: '',
};

let debugListeners: ((info: DebugInfo) => void)[] = [];

export function updateDebugInfo(partial: Partial<DebugInfo>) {
  globalDebugInfo = { ...globalDebugInfo, ...partial };
  debugListeners.forEach(fn => fn(globalDebugInfo));
}

export function incrementSendPressCount() {
  globalDebugInfo = { 
    ...globalDebugInfo, 
    sendPressCount: globalDebugInfo.sendPressCount + 1,
    lastSendAt: new Date().toISOString(),
  };
  debugListeners.forEach(fn => fn(globalDebugInfo));
  console.log('[DebugOverlay] sendPressCount:', globalDebugInfo.sendPressCount);
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
  const [expanded, setExpanded] = useState(true); // Default expanded for debugging
  
  // Get user from store
  const user = useAppStore(state => state.user);
  
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
          🔧 {BUILD_ID} | Press: {debugInfo.sendPressCount} | {debugInfo.pingStatus === 'ok' ? '✓' : debugInfo.pingStatus === 'fail' ? '✗' : '...'}
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
          
          {/* BIG + OBVIOUS debug fields */}
          <View pointerEvents="none">
            {/* BUILD_ID */}
            <Text style={styles.bigRow}>
              <Text style={styles.bigLabel}>BUILD: </Text>
              <Text style={styles.bigValue}>{BUILD_ID}</Text>
            </Text>
            
            {/* userId */}
            <Text style={styles.bigRow}>
              <Text style={styles.bigLabel}>USER_ID: </Text>
              <Text style={user?.id ? styles.bigValueOk : styles.bigValueError}>
                {user?.id || 'NO_USER'}
              </Text>
            </Text>
            
            {/* sendPressCount */}
            <Text style={styles.bigRow}>
              <Text style={styles.bigLabel}>SEND_PRESS_COUNT: </Text>
              <Text style={debugInfo.sendPressCount > 0 ? styles.bigValueOk : styles.bigValueError}>
                {debugInfo.sendPressCount}
              </Text>
            </Text>
            
            {/* lastSendAt */}
            <Text style={styles.row}>
              <Text style={styles.label}>lastSendAt: </Text>
              <Text style={styles.value}>{debugInfo.lastSendAt || '(never)'}</Text>
            </Text>
            
            {/* lastBailReason */}
            {debugInfo.lastBailReason ? (
              <Text style={styles.bigRow}>
                <Text style={styles.bigLabel}>BAIL: </Text>
                <Text style={styles.bigValueError}>{debugInfo.lastBailReason}</Text>
              </Text>
            ) : null}
            
            {/* lastFetchUrl */}
            <Text style={styles.row} numberOfLines={1}>
              <Text style={styles.label}>lastFetchUrl: </Text>
              <Text style={styles.value}>{debugInfo.lastFetchUrl || '(none)'}</Text>
            </Text>
            
            {/* lastHttpStatus */}
            <Text style={styles.bigRow}>
              <Text style={styles.bigLabel}>HTTP_STATUS: </Text>
              <Text style={debugInfo.lastHttpStatus === 200 ? styles.bigValueOk : debugInfo.lastHttpStatus ? styles.bigValueError : styles.bigValue}>
                {debugInfo.lastHttpStatus ?? '(none)'}
              </Text>
            </Text>
            
            {/* lastError */}
            {debugInfo.lastError ? (
              <Text style={styles.bigRow}>
                <Text style={styles.bigLabel}>ERROR: </Text>
                <Text style={styles.bigValueError}>{debugInfo.lastError}</Text>
              </Text>
            ) : null}
            
            {/* Ping status */}
            <Text style={styles.row}>
              <Text style={styles.label}>Ping: </Text>
              <Text style={debugInfo.pingStatus === 'ok' ? styles.ok : debugInfo.pingStatus === 'fail' ? styles.error : styles.value}>
                {debugInfo.pingStatus} {debugInfo.pingError ? `(${debugInfo.pingError})` : ''}
              </Text>
            </Text>
            
            {/* Response preview */}
            {debugInfo.lastResponseText ? (
              <Text style={styles.row} numberOfLines={2}>
                <Text style={styles.label}>Response: </Text>
                <Text style={styles.code}>{debugInfo.lastResponseText.slice(0, 200)}</Text>
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
    backgroundColor: 'rgba(0,0,0,0.98)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    paddingTop: Platform.OS === 'ios' ? 50 : 30,
    borderBottomWidth: 2,
    borderBottomColor: '#FFCC00',
  },
  headerText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
    flex: 1,
  },
  headerToggle: {
    fontSize: 12,
    color: '#FFCC00',
    fontWeight: '700',
  },
  content: {
    backgroundColor: 'rgba(0,0,0,0.98)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 2,
    borderBottomColor: '#FFCC00',
  },
  touchProbe: {
    backgroundColor: '#003300',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    marginBottom: 8,
    borderWidth: 2,
    borderColor: '#00FF88',
  },
  touchProbeText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#00FF88',
    textAlign: 'center',
  },
  // BIG + OBVIOUS styles
  bigRow: {
    fontSize: 12,
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 4,
    fontWeight: '700',
  },
  bigLabel: {
    color: '#FFCC00',
    fontWeight: '700',
  },
  bigValue: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  bigValueOk: {
    color: '#00FF88',
    fontWeight: '700',
  },
  bigValueError: {
    color: '#FF4444',
    fontWeight: '700',
  },
  // Regular rows
  row: {
    fontSize: 10,
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 2,
  },
  label: {
    color: '#AAAAAA',
    fontWeight: '600',
  },
  value: {
    color: '#FFFFFF',
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
    fontSize: 9,
  },
});
