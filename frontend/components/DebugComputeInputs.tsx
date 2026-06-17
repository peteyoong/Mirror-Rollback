/**
 * Debug Compute Inputs Panel
 * ==========================
 * 
 * Shows the canonical input payload stored on server for verification:
 * - birth date
 * - birth time (or noon fallback)
 * - timezone
 * - location
 * - stable user_id
 * 
 * Only visible when DEBUG_MIRROR=true
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';
import axios from 'axios';
import Constants from 'expo-constants';
import { getStableUserId, maskUserId } from '../utils/stableUserId';

// Check if debug mode is enabled
// DISABLED FOR TESTER RELEASE
const DEBUG_MIRROR = false;

// Get backend URL (same logic as NumerologyLensView)
const DEV_BACKEND_FALLBACK = 'http://localhost:8001';

function getBackendBaseUrl(): string {
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.length > 0) {
    return envUrl;
  }
  
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
  if (extraUrl && typeof extraUrl === 'string' && extraUrl.length > 0) {
    return extraUrl;
  }
  
  if (Platform.OS === 'web') {
    const hostname = typeof window !== 'undefined' ? window.location.hostname : '';
    const isLocalDev = hostname === 'localhost' || hostname === '127.0.0.1';
    const isPreview = hostname.includes('preview') || hostname.includes('emergent');
    
    if (isLocalDev || isPreview) {
      return DEV_BACKEND_FALLBACK;
    }
    return '';
  }
  
  return DEV_BACKEND_FALLBACK;
}

const BACKEND_BASE_URL = getBackendBaseUrl();

interface ComputeInputs {
  user_id: string;
  birth_date: string;
  birth_time: string;
  birth_time_source: string; // 'user' or 'noon_fallback'
  timezone: string;
  location: {
    city: string;
    country: string;
    latitude: number;
    longitude: number;
  };
  raw_user_data?: any;
}

interface Props {
  userId: string;
}

export default function DebugComputeInputs({ userId }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<ComputeInputs | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stableId, setStableId] = useState<string | null>(null);

  // Fetch stable user ID on mount.
  // NOTE: useEffect MUST be called unconditionally on every render
  // (rules-of-hooks).  The DEBUG_MIRROR gate is applied AFTER all
  // hooks, by returning null from the render output.
  useEffect(() => {
    getStableUserId().then(setStableId);
  }, []);

  // Don't render anything if debug mode is off.  Early-return AFTER
  // all hooks so the hook call order stays stable across renders.
  if (!DEBUG_MIRROR) {
    return null;
  }

  const fetchComputeInputs = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Fetch user data from API
      const userUrl = BACKEND_BASE_URL 
        ? `${BACKEND_BASE_URL}/api/users/${userId}`
        : `/api/users/${userId}`;
      
      console.log('[DEBUG_MIRROR] Fetching compute inputs from:', userUrl);
      
      const response = await axios.get(userUrl, { timeout: 10000 });
      const userData = response.data;
      
      // Parse birth time
      let birthTime = 'Not set';
      let birthTimeSource = 'noon_fallback';
      
      if (userData.birth_time) {
        birthTime = userData.birth_time;
        birthTimeSource = 'user';
      } else if (userData.birth_date) {
        birthTime = '12:00 (noon fallback)';
        birthTimeSource = 'noon_fallback';
      }
      
      // Build compute inputs object
      const inputs: ComputeInputs = {
        user_id: userId,
        birth_date: userData.birth_date || 'Not set',
        birth_time: birthTime,
        birth_time_source: birthTimeSource,
        timezone: userData.timezone || userData.birth_location?.timezone || 'Not set',
        location: userData.birth_location || {
          city: 'Not set',
          country: 'Not set',
          latitude: 0,
          longitude: 0,
        },
        raw_user_data: userData,
      };
      
      setData(inputs);
      console.log('[DEBUG_MIRROR] Compute inputs:', inputs);
      
    } catch (err: any) {
      console.error('[DEBUG_MIRROR] Failed to fetch compute inputs:', err);
      setError(err?.message || 'Failed to fetch');
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = () => {
    if (!isExpanded && !data) {
      fetchComputeInputs();
    }
    setIsExpanded(!isExpanded);
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity 
        style={styles.header}
        onPress={handleToggle}
        activeOpacity={0.7}
      >
        <View style={styles.headerLeft}>
          <Ionicons 
            name="bug-outline" 
            size={16} 
            color={Colors.accent} 
          />
          <Text style={styles.headerText}>DEBUG: Compute Inputs</Text>
        </View>
        <Ionicons 
          name={isExpanded ? 'chevron-up' : 'chevron-down'} 
          size={20} 
          color={Colors.textTertiary} 
        />
      </TouchableOpacity>
      
      {isExpanded && (
        <View style={styles.content}>
          {isLoading ? (
            <ActivityIndicator size="small" color={Colors.accent} />
          ) : error ? (
            <Text style={styles.errorText}>Error: {error}</Text>
          ) : data ? (
            <>
              <View style={styles.row}>
                <Text style={styles.label}>stable_user_id:</Text>
                <Text style={[
                  styles.value,
                  stableId === userId ? styles.valueOk : styles.valueWarning
                ]}>
                  {maskUserId(stableId)} {stableId === userId ? '✓' : '⚠️ mismatch'}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>prop_user_id:</Text>
                <Text style={styles.value}>{maskUserId(userId)}</Text>
              </View>
              <View style={styles.divider} />
              <View style={styles.row}>
                <Text style={styles.label}>birth_date:</Text>
                <Text style={styles.value}>{data.birth_date}</Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>birth_time:</Text>
                <Text style={[
                  styles.value,
                  data.birth_time_source === 'noon_fallback' && styles.valueWarning
                ]}>
                  {data.birth_time}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>time_source:</Text>
                <Text style={[
                  styles.value,
                  data.birth_time_source === 'noon_fallback' ? styles.valueWarning : styles.valueOk
                ]}>
                  {data.birth_time_source}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>timezone:</Text>
                <Text style={styles.value}>{data.timezone}</Text>
              </View>
              <View style={styles.divider} />
              <View style={styles.row}>
                <Text style={styles.label}>location:</Text>
                <Text style={styles.value}>
                  {data.location.city}, {data.location.country}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>lat/lng:</Text>
                <Text style={styles.value}>
                  {data.location.latitude?.toFixed(4)}, {data.location.longitude?.toFixed(4)}
                </Text>
              </View>
              <View style={styles.divider} />
              <View style={styles.row}>
                <Text style={styles.label}>backend_url:</Text>
                <Text style={styles.valueSmall}>{BACKEND_BASE_URL || '(relative)'}</Text>
              </View>
              
              {/* Refresh button */}
              <TouchableOpacity 
                style={styles.refreshButton}
                onPress={fetchComputeInputs}
              >
                <Ionicons name="refresh" size={14} color={Colors.accent} />
                <Text style={styles.refreshText}>Refresh</Text>
              </TouchableOpacity>
            </>
          ) : (
            <Text style={styles.emptyText}>Tap to load compute inputs</Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: 'rgba(0, 0, 0, 0.03)',
    borderRadius: 8,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.accent,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  content: {
    paddingHorizontal: 12,
    paddingBottom: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.05)',
    paddingTop: 12,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  label: {
    fontSize: 11,
    color: Colors.textTertiary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  value: {
    fontSize: 11,
    color: Colors.text,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'right',
    flex: 1,
    marginLeft: 8,
  },
  valueSmall: {
    fontSize: 9,
    color: Colors.textSecondary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'right',
    flex: 1,
    marginLeft: 8,
  },
  valueOk: {
    color: '#4CAF50',
  },
  valueWarning: {
    color: '#FF9800',
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
    marginVertical: 8,
  },
  errorText: {
    fontSize: 11,
    color: '#D32F2F',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  emptyText: {
    fontSize: 11,
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    marginTop: 8,
    paddingVertical: 6,
  },
  refreshText: {
    fontSize: 11,
    color: Colors.accent,
  },
});
