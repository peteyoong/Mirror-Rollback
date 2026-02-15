/**
 * Mirror V2 - CRASH-PROOF Implementation
 * 
 * NO useFocusEffect - uses navigation.addListener instead
 * Kill-switch prevents crash loops
 * DEBUG mode gated by ?debug=1
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
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import api from '../../services/api';
import { loadMessages, ChatMessage, DEFAULT_THREAD_KEY } from '../../utils/chatPersistence';

// Debug mode - only logs when ?debug=1 is in URL
const DEBUG = Platform.OS === 'web' && typeof window !== 'undefined' && window.location?.search?.includes('debug=1');

// Use the SAME thread key as reflection-chat for unified persistence
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
  if (DEBUG) console.log("[MirrorV2] render", Date.now());
  
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const navigation = useNavigation();
  
  // ONLY pull stable primitives from store
  const userId = useAppStore(s => s.user?.id);
  const userName = useAppStore(s => s.user?.name);
  const hasTriedRestore = useAppStore(s => s.hasTriedSessionRestore);
  const isRestoring = useAppStore(s => s.isRestoringSession);
  
  // LOCAL state
  const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [chatPreview, setChatPreview] = useState<ChatMessage[]>([]);
  
  // CRITICAL REFS for crash prevention
  const chatPreviewRef = useRef<ChatMessage[]>([]);
  const isMountedRef = useRef(true);
  const inFlightRef = useRef(false);
  const killSwitchRef = useRef(false);
  const lastFocusRefreshRef = useRef(0);
  const didInitRef = useRef(false);
  
  // Track mounted state
  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);
  
  // Keep chatPreviewRef in sync (no setState here)
  useEffect(() => {
    chatPreviewRef.current = chatPreview;
  }, [chatPreview]);
  
  // CRASH-PROOF refresh function with kill-switch
  const refreshPreview = useCallback(async (reason: string) => {
    if (DEBUG) console.log("[MirrorV2] refreshPreview called:", reason, Date.now());
    
    // Kill-switch: if we've had errors, stop trying
    if (killSwitchRef.current) {
      if (DEBUG) console.log("[MirrorV2] kill-switch active, skipping");
      return;
    }
    
    // No user = nothing to refresh
    if (!userId) {
      if (DEBUG) console.log("[MirrorV2] no userId, skipping");
      return;
    }
    
    // Debounce: prevent rapid calls
    const now = Date.now();
    if (now - lastFocusRefreshRef.current < 500) {
      if (DEBUG) console.log("[MirrorV2] debounce, skipping");
      return;
    }
    
    // Prevent concurrent calls
    if (inFlightRef.current) {
      if (DEBUG) console.log("[MirrorV2] in-flight, skipping");
      return;
    }
    
    inFlightRef.current = true;
    lastFocusRefreshRef.current = now;
    
    try {
      if (DEBUG) console.log("[MirrorV2] load start", Date.now());
      const loaded = await loadMessages(userId, THREAD_KEY);
      if (DEBUG) console.log("[MirrorV2] load end", Date.now(), "count:", loaded.length);
      
      // Compare without causing rerenders
      const current = chatPreviewRef.current;
      const different = 
        loaded.length !== current.length ||
        (loaded.at(-1)?.id ?? "") !== (current.at(-1)?.id ?? "");
      
      if (different && isMountedRef.current) {
        if (DEBUG) console.log("[MirrorV2] messages different, updating state");
        chatPreviewRef.current = loaded;
        setChatPreview(loaded);
      } else {
        if (DEBUG) console.log("[MirrorV2] messages same or unmounted, skipping setState");
      }
    } catch (e) {
      // Kill-switch ON to prevent crash loops
      killSwitchRef.current = true;
      console.error("[MirrorV2] preview refresh failed -> killSwitch ON", e);
    } finally {
      inFlightRef.current = false;
    }
  }, [userId]); // ONLY depend on userId
  
  // NAVIGATION FOCUS LISTENER - does NOT recreate on every render
  useEffect(() => {
    if (!navigation) return;
    
    const unsubscribe = navigation.addListener('focus', () => {
      if (DEBUG) console.log("[MirrorV2] focus event", Date.now());
      void refreshPreview("focus");
    });
    
    return unsubscribe;
  }, [navigation, refreshPreview]); // refreshPreview is stable due to useCallback
  
  // ONE-TIME initial load
  useEffect(() => {
    if (!userId) return;
    if (!hasTriedRestore || isRestoring) return;
    if (didInitRef.current) return;
    didInitRef.current = true;
    
    if (DEBUG) console.log("[MirrorV2] initial mount load");
    loadKeystone();
    void refreshPreview("mount");
  }, [userId, hasTriedRestore, isRestoring, refreshPreview]);
  
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
        keystone: "Something in you brought you here today. That's worth noticing.",
        reflect_question: "What feels most present right now?",
        micro_affirmation: "You don't have to have it figured out to be here.",
        source_signals: { used: ["fallback"], tone: "grounding" },
        daily_seed: "fallback",
        is_first_visit: false,
      });
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadKeystone();
    await refreshPreview("pull-to-refresh");
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
  
  // Not logged in
  if (!userId) {
    return (
      <View style={[styles.container, { paddingTop: insets.top }]}>
        <View style={styles.centered}>
          <Text style={styles.loadingText}>Please log in to continue</Text>
        </View>
      </View>
    );
  }
  
  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
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
        {/* Daily Keystone */}
        {isLoading ? (
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
        ) : null}
        
        {/* Chat Preview */}
        <View style={styles.chatPreviewCard}>
          <View style={styles.chatPreviewHeader}>
            <Text style={styles.chatPreviewTitle}>Recent Reflections</Text>
            <TouchableOpacity onPress={handleOpenChat}>
              <Text style={styles.openChatLink}>Open Chat →</Text>
            </TouchableOpacity>
          </View>
          
          {chatPreview.length === 0 ? (
            <Text style={styles.noChatText}>No conversations yet. Start reflecting!</Text>
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
        
        {/* Welcome message for new users */}
        {!chatPreview.length && (
          <View style={[styles.card, styles.welcomeCard]}>
            <Text style={styles.welcomeText}>
              {userName ? `Welcome, ${userName}` : 'Welcome'}
            </Text>
            <Text style={styles.welcomeSubtext}>
              This is your space to reflect, notice, and explore.
            </Text>
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
  welcomeCard: {
    padding: 16,
    alignItems: 'center',
  },
  welcomeText: {
    fontSize: 18,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 8,
  },
  welcomeSubtext: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
});
