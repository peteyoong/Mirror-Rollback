import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Platform, Pressable, ScrollView } from 'react-native';
import { API_BASE_URL, API_URL_MISSING, joinUrl } from '../services/api';
import { useAppStore } from '../store';

/**
 * BUILD TAG: v3-non-blocking-2026-02-14
 * 
 * DebugOverlay - NON-BLOCKING debug panel
 * 
 * CRITICAL: Only the handle bar is interactive.
 * The panel itself uses pointerEvents="none" so it NEVER blocks the app.
 * 
 * Shows:
 * - BUILD_ID, userId, sendPressCount, lastSendAt
 * - lastBailReason, lastFetchUrl, lastHttpStatus, lastError
 */

// BUILD ID - change this to verify you're on the right build
const BUILD_ID = 'v3-non-blocking-2026-02-14';

// Toggle this to enable/disable the debug overlay globally
const DEBUG_OVERLAY_ENABLED = true;

// Global state for debug info (can be updated from other components)
export interface DebugInfo {
  lastHttpStatus: number | null;
  lastResponseText: string;
  lastError: string;
  pingStatus: 'pending' | 'ok' | 'fail';
  pingError: string;
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
  // Default COLLAPSED so it never blocks first-time flows
  const [expanded, setExpanded] = useState(false);
  const [debugInfo, setDebugInfo] = useState<DebugInfo>(globalDebugInfo);
  
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
  
  const pingIcon = debugInfo.pingStatus === 'ok' ? '✓' : debugInfo.pingStatus === 'fail' ? '✗' : '…';
  
  return (
    <View style={[styles.root, { pointerEvents: 'box-none' }]}>
      {/* Handle: the ONLY interactive part */}
      <View style={[styles.handleWrap, { pointerEvents: 'auto' }]}>
        <Pressable
          onPress={() => setExpanded(v => !v)}
          style={({ pressed }) => [styles.handle, pressed && styles.handlePressed]}
          hitSlop={12}
        >
          <Text style={styles.handleText}>
            {expanded ? `DEBUG ▾ tap to collapse | ${pingIcon}` : `DEBUG ▸ tap to expand | Press:${debugInfo.sendPressCount} | ${pingIcon}`}
          </Text>
        </Pressable>
      </View>

      {/* Panel: visually on top, but does NOT intercept touches */}
      {expanded && (
        <View style={[styles.panel, { pointerEvents: 'none' }]}>
          <ScrollView style={styles.scrollContent} showsVerticalScrollIndicator={false}>
            {/* BUILD_ID */}
            <Text style={styles.row}>
              <Text style={styles.label}>BUILD: </Text>
              <Text style={styles.valueHighlight}>{BUILD_ID}</Text>
            </Text>
            
            {/* userId */}
            <Text style={styles.row}>
              <Text style={styles.label}>USER_ID: </Text>
              <Text style={user?.id ? styles.valueOk : styles.valueError}>
                {user?.id || 'NO_USER'}
              </Text>
            </Text>
            
            {/* sendPressCount */}
            <Text style={styles.row}>
              <Text style={styles.label}>SEND_PRESS: </Text>
              <Text style={debugInfo.sendPressCount > 0 ? styles.valueOk : styles.valueError}>
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
              <Text style={styles.row}>
                <Text style={styles.label}>BAIL: </Text>
                <Text style={styles.valueError}>{debugInfo.lastBailReason}</Text>
              </Text>
            ) : null}
            
            {/* lastFetchUrl */}
            <Text style={styles.row} numberOfLines={1}>
              <Text style={styles.label}>fetchUrl: </Text>
              <Text style={styles.value}>{debugInfo.lastFetchUrl || '(none)'}</Text>
            </Text>
            
            {/* lastHttpStatus */}
            <Text style={styles.row}>
              <Text style={styles.label}>HTTP: </Text>
              <Text style={debugInfo.lastHttpStatus === 200 ? styles.valueOk : debugInfo.lastHttpStatus ? styles.valueError : styles.value}>
                {debugInfo.lastHttpStatus ?? '(none)'}
              </Text>
            </Text>
            
            {/* lastError */}
            {debugInfo.lastError ? (
              <Text style={styles.row}>
                <Text style={styles.label}>ERROR: </Text>
                <Text style={styles.valueError}>{debugInfo.lastError.slice(0, 100)}</Text>
              </Text>
            ) : null}
            
            {/* Ping status */}
            <Text style={styles.row}>
              <Text style={styles.label}>Ping: </Text>
              <Text style={debugInfo.pingStatus === 'ok' ? styles.valueOk : debugInfo.pingStatus === 'fail' ? styles.valueError : styles.value}>
                {debugInfo.pingStatus} {debugInfo.pingError ? `(${debugInfo.pingError})` : ''}
              </Text>
            </Text>
            
            {/* Response preview */}
            {debugInfo.lastResponseText ? (
              <Text style={styles.row} numberOfLines={2}>
                <Text style={styles.label}>Resp: </Text>
                <Text style={styles.valueCode}>{debugInfo.lastResponseText.slice(0, 150)}</Text>
              </Text>
            ) : null}
          </ScrollView>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 999999,
  },
  handleWrap: {
    alignSelf: 'stretch',
    paddingTop: Platform.OS === 'ios' ? 48 : 24,
    paddingHorizontal: 10,
  },
  handle: {
    borderWidth: 1,
    borderColor: 'rgba(255,165,0,0.8)',
    backgroundColor: 'rgba(0,0,0,0.85)',
    borderRadius: 10,
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  handlePressed: { 
    opacity: 0.7,
    backgroundColor: 'rgba(255,165,0,0.3)',
  },
  handleText: { 
    color: 'rgba(255,165,0,0.95)', 
    fontWeight: '700',
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  panel: {
    marginTop: 6,
    marginHorizontal: 10,
    borderWidth: 1,
    borderColor: 'rgba(255,165,0,0.6)',
    backgroundColor: 'rgba(0,0,0,0.85)',
    borderRadius: 10,
    padding: 10,
    maxHeight: 200,
  },
  scrollContent: {
    flex: 1,
  },
  row: {
    fontSize: 10,
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 3,
  },
  label: {
    color: '#FFAA00',
    fontWeight: '700',
  },
  value: {
    color: '#FFFFFF',
  },
  valueHighlight: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  valueOk: {
    color: '#00FF88',
    fontWeight: '700',
  },
  valueError: {
    color: '#FF4444',
    fontWeight: '700',
  },
  valueCode: {
    color: '#88CCFF',
    fontSize: 9,
  },
});
