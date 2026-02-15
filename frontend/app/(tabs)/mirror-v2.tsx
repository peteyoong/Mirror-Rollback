/**
 * Mirror V2 - FEATURE FLAG BINARY SEARCH VERSION
 * 
 * Use URL params to enable features incrementally:
 * ?m1=1 - Enable store access (user from store)
 * ?m2=1 - Enable daily focus fetch
 * ?m3=1 - Enable Today's Mirror content
 * ?m4=1 - Enable full chat functionality
 * 
 * Example: /mirror-v2?m1=1&m2=1 enables store + daily focus
 */

import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  ActivityIndicator,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { Ionicons } from '@expo/vector-icons';

// Conditional imports - only load if flags enabled
import { useAppStore } from '../../store';
import api from '../../services/api';

interface DailyFocus {
  ambient_line: string;
  context: string | null;
  confidence: number;
}

interface MirrorHome {
  greeting: string;
  keystone: string;
  reflect_question: string;
  micro_affirmation: string;
}

export default function MirrorV2Screen() {
  const params = useLocalSearchParams<{ 
    m1?: string;  // Store access
    m2?: string;  // Daily focus
    m3?: string;  // Today's mirror
    m4?: string;  // Full chat
  }>();
  
  // Parse feature flags
  const F_STORE = params.m1 === '1';
  const F_DAILY_FOCUS = params.m2 === '1';
  const F_TODAYS_MIRROR = params.m3 === '1';
  const F_FULL_CHAT = params.m4 === '1';
  
  const router = useRouter();
  
  // ============================================================================
  // FEATURE M1: Store access
  // ============================================================================
  const user = F_STORE ? useAppStore((s) => s.user) : null;
  const userId = user?.id || null;
  const userName = user?.name || 'Friend';
  
  // ============================================================================
  // STATE - only create if relevant flags enabled
  // ============================================================================
  const [dailyFocus, setDailyFocus] = useState<DailyFocus | null>(null);
  const [mirrorHome, setMirrorHome] = useState<MirrorHome | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // ============================================================================
  // FEATURE M2: Daily focus fetch
  // ============================================================================
  useEffect(() => {
    if (!F_DAILY_FOCUS || !userId) {
      console.log('[MirrorV2] Skipping daily focus (flag off or no userId)');
      return;
    }
    
    let cancelled = false;
    
    const fetchDailyFocus = async () => {
      try {
        console.log('[MirrorV2] Fetching daily focus...');
        const response = await api.get(`/daily-focus/${userId}`);
        if (!cancelled) {
          setDailyFocus(response.data);
          console.log('[MirrorV2] Daily focus loaded');
        }
      } catch (err) {
        console.error('[MirrorV2] Daily focus error:', err);
        if (!cancelled) {
          setError('Failed to load daily focus');
        }
      }
    };
    
    fetchDailyFocus();
    
    return () => {
      cancelled = true;
    };
  }, [F_DAILY_FOCUS, userId]);
  
  // ============================================================================
  // FEATURE M3: Today's Mirror content
  // ============================================================================
  useEffect(() => {
    if (!F_TODAYS_MIRROR || !userId) {
      console.log('[MirrorV2] Skipping todays mirror (flag off or no userId)');
      return;
    }
    
    let cancelled = false;
    
    const fetchMirrorHome = async () => {
      setIsLoading(true);
      try {
        console.log('[MirrorV2] Fetching mirror home...');
        const response = await api.get(`/mirror/home/${userId}`);
        if (!cancelled) {
          setMirrorHome(response.data);
          console.log('[MirrorV2] Mirror home loaded');
        }
      } catch (err) {
        console.error('[MirrorV2] Mirror home error:', err);
        if (!cancelled) {
          setError('Failed to load mirror home');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };
    
    fetchMirrorHome();
    
    return () => {
      cancelled = true;
    };
  }, [F_TODAYS_MIRROR, userId]);
  
  // ============================================================================
  // RENDER: Debug panel showing active flags
  // ============================================================================
  const renderDebugPanel = () => (
    <View style={styles.debugPanel}>
      <Text style={styles.debugTitle}>🔧 Binary Search Mode</Text>
      <View style={styles.flagsRow}>
        <View style={[styles.flag, F_STORE && styles.flagActive]}>
          <Text style={styles.flagText}>M1:Store {F_STORE ? '✓' : '✗'}</Text>
        </View>
        <View style={[styles.flag, F_DAILY_FOCUS && styles.flagActive]}>
          <Text style={styles.flagText}>M2:Focus {F_DAILY_FOCUS ? '✓' : '✗'}</Text>
        </View>
        <View style={[styles.flag, F_TODAYS_MIRROR && styles.flagActive]}>
          <Text style={styles.flagText}>M3:Home {F_TODAYS_MIRROR ? '✓' : '✗'}</Text>
        </View>
        <View style={[styles.flag, F_FULL_CHAT && styles.flagActive]}>
          <Text style={styles.flagText}>M4:Chat {F_FULL_CHAT ? '✓' : '✗'}</Text>
        </View>
      </View>
      <Text style={styles.debugHint}>
        Add ?m1=1&m2=1 etc. to URL to enable features
      </Text>
    </View>
  );
  
  // ============================================================================
  // RENDER: Quick enable buttons
  // ============================================================================
  const renderQuickEnable = () => (
    <View style={styles.quickEnable}>
      <Text style={styles.quickTitle}>Quick Enable</Text>
      <View style={styles.quickButtons}>
        <TouchableOpacity 
          style={styles.quickButton}
          onPress={() => router.replace('/mirror-v2?m1=1')}
        >
          <Text style={styles.quickButtonText}>+M1</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.quickButton}
          onPress={() => router.replace('/mirror-v2?m1=1&m2=1')}
        >
          <Text style={styles.quickButtonText}>+M2</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.quickButton}
          onPress={() => router.replace('/mirror-v2?m1=1&m2=1&m3=1')}
        >
          <Text style={styles.quickButtonText}>+M3</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={styles.quickButton}
          onPress={() => router.replace('/mirror-v2?m1=1&m2=1&m3=1&m4=1')}
        >
          <Text style={styles.quickButtonText}>ALL</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.quickButton, styles.resetButton]}
          onPress={() => router.replace('/mirror-v2')}
        >
          <Text style={styles.quickButtonText}>RESET</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
  
  // ============================================================================
  // RENDER: Content based on flags
  // ============================================================================
  const renderContent = () => {
    // No flags - show minimal
    if (!F_STORE && !F_DAILY_FOCUS && !F_TODAYS_MIRROR) {
      return (
        <View style={styles.minimalContent}>
          <Ionicons name="checkmark-circle" size={48} color="#4ade80" />
          <Text style={styles.minimalTitle}>Stable Base</Text>
          <Text style={styles.minimalText}>
            No features enabled. Use buttons above to add features one by one.
          </Text>
        </View>
      );
    }
    
    return (
      <ScrollView style={styles.scrollContent} contentContainerStyle={styles.scrollContentContainer}>
        {/* User greeting (M1) */}
        {F_STORE && (
          <View style={styles.card}>
            <Text style={styles.cardLabel}>M1: Store Access</Text>
            <Text style={styles.greeting}>Hello, {userName}</Text>
            <Text style={styles.userId}>User ID: {userId || 'Not logged in'}</Text>
          </View>
        )}
        
        {/* Daily focus (M2) */}
        {F_DAILY_FOCUS && (
          <View style={styles.card}>
            <Text style={styles.cardLabel}>M2: Daily Focus</Text>
            {dailyFocus ? (
              <>
                <Text style={styles.ambientLine}>{dailyFocus.ambient_line}</Text>
                {dailyFocus.context && (
                  <Text style={styles.context}>Context: {dailyFocus.context}</Text>
                )}
              </>
            ) : (
              <ActivityIndicator color={Colors.accent} />
            )}
          </View>
        )}
        
        {/* Today's mirror (M3) */}
        {F_TODAYS_MIRROR && (
          <View style={styles.card}>
            <Text style={styles.cardLabel}>M3: Today's Mirror</Text>
            {isLoading ? (
              <ActivityIndicator color={Colors.accent} />
            ) : mirrorHome ? (
              <>
                <Text style={styles.keystone}>{mirrorHome.keystone}</Text>
                <Text style={styles.reflectQuestion}>{mirrorHome.reflect_question}</Text>
              </>
            ) : error ? (
              <Text style={styles.errorText}>{error}</Text>
            ) : (
              <Text style={styles.placeholder}>Loading...</Text>
            )}
          </View>
        )}
        
        {/* Full chat (M4) - placeholder */}
        {F_FULL_CHAT && (
          <View style={styles.card}>
            <Text style={styles.cardLabel}>M4: Full Chat</Text>
            <Text style={styles.placeholder}>Chat functionality would go here</Text>
            <TouchableOpacity 
              style={styles.chatButton}
              onPress={() => router.push('/reflection-chat')}
            >
              <Ionicons name="chatbubble-outline" size={20} color="#fff" />
              <Text style={styles.chatButtonText}>Open Chat</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    );
  };
  
  console.log(`[MirrorV2] Render - Flags: M1=${F_STORE}, M2=${F_DAILY_FOCUS}, M3=${F_TODAYS_MIRROR}, M4=${F_FULL_CHAT}`);
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="light" />
      {renderDebugPanel()}
      {renderQuickEnable()}
      {renderContent()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  debugPanel: {
    backgroundColor: '#1a2f1a',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#2a4f2a',
  },
  debugTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#4ade80',
    marginBottom: 8,
  },
  flagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  flag: {
    backgroundColor: '#333',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  flagActive: {
    backgroundColor: '#166534',
  },
  flagText: {
    fontSize: 11,
    color: '#fff',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  debugHint: {
    fontSize: 11,
    color: '#666',
    marginTop: 8,
    fontStyle: 'italic',
  },
  quickEnable: {
    backgroundColor: Colors.surface,
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  quickTitle: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginBottom: 8,
  },
  quickButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  quickButton: {
    backgroundColor: Colors.accent,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
  },
  resetButton: {
    backgroundColor: '#dc2626',
  },
  quickButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  minimalContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  minimalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 16,
  },
  minimalText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  scrollContent: {
    flex: 1,
  },
  scrollContentContainer: {
    padding: 16,
    gap: 16,
  },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardLabel: {
    fontSize: 11,
    color: Colors.accent,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
  },
  greeting: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
  },
  userId: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 4,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  ambientLine: {
    fontSize: 16,
    color: Colors.text,
    lineHeight: 24,
    fontStyle: 'italic',
  },
  context: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 8,
  },
  keystone: {
    fontSize: 18,
    color: Colors.text,
    lineHeight: 26,
    marginBottom: 12,
  },
  reflectQuestion: {
    fontSize: 14,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  placeholder: {
    fontSize: 14,
    color: Colors.textTertiary,
  },
  errorText: {
    fontSize: 14,
    color: '#ef4444',
  },
  chatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.accent,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 12,
  },
  chatButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
  },
});
