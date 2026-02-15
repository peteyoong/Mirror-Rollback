/**
 * Mirror V2 - BINARY SEARCH ISOLATION VERSION
 * 
 * Safe mode and feature flags for crash isolation
 * ?safe=1 → minimal static screen only
 * ?m1=1 → Today's Mirror content
 * ?m2=1 → Chat preview (no load)
 * ?m3=1 → Chat persistence/loadMessages
 * ?m4=1 → Focus refresh
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Platform,
  Pressable,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import api from '../../services/api';
import { loadMessages, ChatMessage, DEFAULT_THREAD_KEY } from '../../utils/chatPersistence';

// Feature flags from URL
const getFlags = () => {
  if (Platform.OS !== 'web' || typeof window === 'undefined') {
    return { SAFE: false, M1: true, M2: true, M3: true, M4: true, DEBUG: false };
  }
  const search = window.location?.search || '';
  return {
    SAFE: search.includes('safe=1'),
    M1: search.includes('m1=1'),
    M2: search.includes('m2=1'),
    M3: search.includes('m3=1'),
    M4: search.includes('m4=1'),
    DEBUG: search.includes('debug=1'),
  };
};

const THREAD_KEY = DEFAULT_THREAD_KEY;

interface DailyKeystone {
  date: string;
  title: string;
  keystone: string;
  reflect_question: string;
  micro_affirmation: string;
  source_signals?: { used: string[]; tone: string };
  daily_seed: string;
  is_first_visit: boolean;
}

export default function MirrorV2Screen() {
  const flags = getFlags();
  
  if (flags.DEBUG) console.log("[MirrorV2] render, flags:", flags);
  
  const insets = useSafeAreaInsets();
  const router = useRouter();
  
  // =========================================================================
  // SAFE MODE: Render ONLY minimal static screen - NO store, NO loads
  // =========================================================================
  if (flags.SAFE) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.safeHeader}>
          <Text style={styles.safeTitle}>Mirror (Safe Mode)</Text>
          <Text style={styles.safeSubtitle}>No store calls, no loads, no effects</Text>
        </View>
        <View style={styles.safeCentered}>
          <Text style={styles.safeText}>If you see this, Mirror tab can mount without crash.</Text>
          <Text style={styles.safeText}>The loop is in a feature, not the tab itself.</Text>
          
          <View style={styles.flagButtons}>
            <Text style={styles.flagTitle}>Test features one by one:</Text>
            <Pressable style={styles.flagButton} onPress={() => {
              if (typeof window !== 'undefined') window.location.search = '?m1=1';
            }}>
              <Text style={styles.flagButtonText}>?m1=1 - Today's Mirror API</Text>
            </Pressable>
            <Pressable style={styles.flagButton} onPress={() => {
              if (typeof window !== 'undefined') window.location.search = '?m2=1';
            }}>
              <Text style={styles.flagButtonText}>?m2=1 - Chat Preview UI</Text>
            </Pressable>
            <Pressable style={styles.flagButton} onPress={() => {
              if (typeof window !== 'undefined') window.location.search = '?m3=1';
            }}>
              <Text style={styles.flagButtonText}>?m3=1 - Chat Load/Persist</Text>
            </Pressable>
            <Pressable style={styles.flagButton} onPress={() => {
              if (typeof window !== 'undefined') window.location.search = '?m4=1';
            }}>
              <Text style={styles.flagButtonText}>?m4=1 - Focus Refresh</Text>
            </Pressable>
            <Pressable style={[styles.flagButton, { backgroundColor: '#cc0000' }]} onPress={() => {
              if (typeof window !== 'undefined') window.location.search = '';
            }}>
              <Text style={styles.flagButtonText}>Exit Safe Mode (full app)</Text>
            </Pressable>
          </View>
        </View>
      </View>
    );
  }
  
  // =========================================================================
  // NORMAL MODE with feature flags
  // =========================================================================
  const navigation = useNavigation();
  
  // Store selectors - ONLY stable primitives
  const userId = useAppStore(s => s.user?.id);
  const userName = useAppStore(s => s.user?.name);
  const hasTriedRestore = useAppStore(s => s.hasTriedSessionRestore);
  const isRestoring = useAppStore(s => s.isRestoringSession);
  
  // LOCAL state
  const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [chatPreview, setChatPreview] = useState<ChatMessage[]>([]);
  
  // Refs for crash prevention
  const chatPreviewRef = useRef<ChatMessage[]>([]);
  const isMountedRef = useRef(true);
  const inFlightRef = useRef(false);
  const killSwitchRef = useRef(false);
  const lastFocusRefreshRef = useRef(0);
  const didInitRef = useRef(false);
  
  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);
  
  useEffect(() => {
    chatPreviewRef.current = chatPreview;
  }, [chatPreview]);
  
  // M3: Chat refresh function (only if flag enabled)
  const refreshPreview = useCallback(async (reason: string) => {
    if (!flags.M3) return; // Feature disabled
    if (flags.DEBUG) console.log("[MirrorV2] refreshPreview:", reason);
    
    if (killSwitchRef.current) return;
    if (!userId) return;
    
    const now = Date.now();
    if (now - lastFocusRefreshRef.current < 500) return;
    if (inFlightRef.current) return;
    
    inFlightRef.current = true;
    lastFocusRefreshRef.current = now;
    
    try {
      const loaded = await loadMessages(userId, THREAD_KEY);
      
      const current = chatPreviewRef.current;
      const different = 
        loaded.length !== current.length ||
        (loaded.at(-1)?.id ?? "") !== (current.at(-1)?.id ?? "");
      
      if (different && isMountedRef.current) {
        chatPreviewRef.current = loaded;
        setChatPreview(loaded);
      }
    } catch (e) {
      killSwitchRef.current = true;
      console.error("[MirrorV2] refresh failed -> killSwitch ON", e);
    } finally {
      inFlightRef.current = false;
    }
  }, [userId, flags.M3, flags.DEBUG]);
  
  // M4: Focus listener (only if flag enabled)
  useEffect(() => {
    if (!flags.M4) return; // Feature disabled
    if (!navigation) return;
    
    const unsubscribe = navigation.addListener('focus', () => {
      if (flags.DEBUG) console.log("[MirrorV2] focus event");
      void refreshPreview("focus");
    });
    
    return unsubscribe;
  }, [navigation, refreshPreview, flags.M4, flags.DEBUG]);
  
  // Initial load
  useEffect(() => {
    if (!userId) return;
    if (!hasTriedRestore || isRestoring) return;
    if (didInitRef.current) return;
    didInitRef.current = true;
    
    if (flags.DEBUG) console.log("[MirrorV2] initial load");
    
    if (flags.M1) loadKeystone();
    if (flags.M3) void refreshPreview("mount");
  }, [userId, hasTriedRestore, isRestoring, flags.M1, flags.M3, refreshPreview, flags.DEBUG]);
  
  const loadKeystone = async () => {
    if (!userId) return;
    
    setIsLoading(true);
    
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await api.get(`/mirror/home/${userId}`, {
        params: { date: today }
      });
      setKeystone(response.data);
    } catch (err) {
      console.error('[MirrorV2] Keystone load error:', err);
      setKeystone({
        date: new Date().toISOString().split('T')[0],
        title: "A Quiet Arrival",
        keystone: "Something in you brought you here today.",
        reflect_question: "What feels most present right now?",
        micro_affirmation: "You don't have to have it figured out.",
        daily_seed: "fallback",
        is_first_visit: false,
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (flags.M1) await loadKeystone();
    if (flags.M3) await refreshPreview("pull-to-refresh");
    setIsRefreshing(false);
  };
  
  const handleOpenChat = () => {
    router.push('/reflection-chat');
  };
  
  // Loading state
  if (!hasTriedRestore || isRestoring) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Restoring session...</Text>
        </View>
      </View>
    );
  }
  
  if (!userId) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.centered}>
          <Text style={styles.loadingText}>Please log in</Text>
        </View>
      </View>
    );
  }
  
  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Debug banner */}
      {flags.DEBUG && (
        <View style={styles.debugBanner}>
          <Text style={styles.debugText}>
            M1={flags.M1?'ON':'off'} M2={flags.M2?'ON':'off'} M3={flags.M3?'ON':'off'} M4={flags.M4?'ON':'off'}
          </Text>
        </View>
      )}
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Mirror</Text>
        <Text style={styles.headerSubtitle}>A mirror, not a verdict.</Text>
      </View>
      
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.accent}
          />
        }
      >
        {/* M1: Today's Mirror content */}
        {flags.M1 && (
          isLoading ? (
            <View style={styles.centered}>
              <ActivityIndicator size="large" color={Colors.accent} />
            </View>
          ) : keystone ? (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>{keystone.title}</Text>
              <Text style={styles.cardKeystone}>{keystone.keystone}</Text>
              <Text style={styles.cardQuestion}>{keystone.reflect_question}</Text>
              <Text style={styles.cardAffirmation}>{keystone.micro_affirmation}</Text>
            </View>
          ) : null
        )}
        
        {/* M2: Chat Preview UI */}
        {flags.M2 && (
          <View style={styles.chatPreviewCard}>
            <View style={styles.chatPreviewHeader}>
              <Text style={styles.chatPreviewTitle}>Recent Reflections</Text>
              <TouchableOpacity onPress={handleOpenChat}>
                <Text style={styles.openChatLink}>Open Chat →</Text>
              </TouchableOpacity>
            </View>
            
            {chatPreview.length === 0 ? (
              <Text style={styles.noChatText}>No conversations yet.</Text>
            ) : (
              chatPreview.slice(-3).map((msg) => (
                <View
                  key={msg.id}
                  style={[
                    styles.chatBubble,
                    msg.role === 'user' ? styles.userBubble : styles.assistantBubble,
                  ]}
                >
                  <Text
                    style={[
                      styles.chatText,
                      msg.role === 'user' ? styles.userText : styles.assistantText,
                    ]}
                    numberOfLines={2}
                  >
                    {msg.content}
                  </Text>
                </View>
              ))
            )}
            
            <TouchableOpacity style={styles.openChatButton} onPress={handleOpenChat}>
              <Ionicons name="chatbubble-outline" size={20} color={Colors.surface} />
              <Text style={styles.openChatButtonText}>Continue Reflecting</Text>
            </TouchableOpacity>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  // Safe mode styles
  safeHeader: {
    padding: 20,
    backgroundColor: '#006600',
    alignItems: 'center',
  },
  safeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#fff',
  },
  safeSubtitle: {
    fontSize: 14,
    color: '#cfc',
    marginTop: 4,
  },
  safeCentered: {
    flex: 1,
    padding: 20,
    alignItems: 'center',
  },
  safeText: {
    fontSize: 16,
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  flagButtons: {
    marginTop: 24,
    gap: 12,
    width: '100%',
  },
  flagTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  flagButton: {
    backgroundColor: '#333',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  flagButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '500',
  },
  // Debug banner
  debugBanner: {
    backgroundColor: '#333',
    padding: 8,
  },
  debugText: {
    color: '#0f0',
    fontSize: 12,
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  // Normal styles
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: Colors.textSecondary,
    fontSize: 14,
    marginTop: 12,
  },
  header: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
  },
  headerSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 4,
    fontStyle: 'italic',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 100,
  },
  card: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  cardKeystone: {
    fontSize: 16,
    color: Colors.text,
    lineHeight: 24,
    marginBottom: 16,
  },
  cardQuestion: {
    fontSize: 15,
    color: Colors.accent,
    fontStyle: 'italic',
    marginBottom: 12,
  },
  cardAffirmation: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  chatPreviewCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chatPreviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  chatPreviewTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  openChatLink: {
    fontSize: 14,
    color: Colors.accent,
  },
  noChatText: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    paddingVertical: 20,
  },
  chatBubble: {
    padding: 10,
    borderRadius: 12,
    marginBottom: 8,
    maxWidth: '85%',
  },
  userBubble: {
    backgroundColor: Colors.accent,
    alignSelf: 'flex-end',
  },
  assistantBubble: {
    backgroundColor: Colors.border,
    alignSelf: 'flex-start',
  },
  chatText: {
    fontSize: 14,
    lineHeight: 20,
  },
  userText: {
    color: Colors.surface,
  },
  assistantText: {
    color: Colors.text,
  },
  openChatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent,
    paddingVertical: 12,
    borderRadius: 12,
    marginTop: 8,
    gap: 8,
  },
  openChatButtonText: {
    color: Colors.surface,
    fontSize: 15,
    fontWeight: '600',
  },
});
