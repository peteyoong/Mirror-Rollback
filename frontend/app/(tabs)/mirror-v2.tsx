/**
 * Mirror V2 - Loop-Proof Implementation
 * 
 * Uses LOCAL state for everything except userId from store.
 * NO Zustand chatMessages dependency.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import api from '../../services/api';
import { loadMessages, ChatMessage } from '../../utils/chatPersistence';

const THREAD_KEY = 'mirror:home';

// ============================================================================
// globalThis guard survives Fast Refresh / HMR
// ============================================================================
const g: any = globalThis as any;
g.__mirror_screen_guard ??= { effectRan: false, renderCount: 0 };
const MIRROR_GUARD = g.__mirror_screen_guard;

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
  MIRROR_GUARD.renderCount++;
  console.log(`[MirrorV2] Render #${MIRROR_GUARD.renderCount}`);
  
  const insets = useSafeAreaInsets();
  const router = useRouter();
  
  // ONLY pull stable primitives from store - NO arrays/objects that change
  const userId = useAppStore(s => s.user?.id);
  const userName = useAppStore(s => s.user?.name);
  const hasTriedRestore = useAppStore(s => s.hasTriedSessionRestore);
  const isRestoring = useAppStore(s => s.isRestoringSession);
  
  // LOCAL state - NOT from Zustand store
  const [keystone, setKeystone] = useState<DailyKeystone | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [chatPreview, setChatPreview] = useState<ChatMessage[]>([]);
  
  // One-shot init guard - NEVER reset
  const didInitRef = useRef(false);
  
  // LOOP-PROOF: Load data ONCE on mount
  useEffect(() => {
    if (!userId) return;
    if (!hasTriedRestore || isRestoring) return;
    if (didInitRef.current) return;
    didInitRef.current = true;
    
    console.log('[MirrorV2] Initializing...');
    loadKeystone();
    loadChatPreview();
  }, [userId, hasTriedRestore, isRestoring]);
  
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
  
  const loadChatPreview = async () => {
    if (!userId) return;
    const messages = await loadMessages(userId, THREAD_KEY);
    setChatPreview(messages.slice(-3));
  };
  
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadKeystone();
    await loadChatPreview();
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
          <Text style={styles.loadingText}>Please log in</Text>
          <TouchableOpacity
            style={styles.button}
            onPress={() => router.replace('/welcome')}
          >
            <Text style={styles.buttonText}>Go to Login</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }
  
  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* SCREEN IDENTIFIER */}
      <View style={styles.screenBanner}>
        <Text style={styles.screenName}>SCREEN: MIRROR-HOME (Tab)</Text>
        <Text style={styles.screenSubtext}>Chat opens: reflection-chat modal</Text>
      </View>
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Mirror</Text>
        <Text style={styles.headerSubtitle}>A mirror, not a verdict.</Text>
      </View>
      
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.accent}
          />
        }
      >
        {/* Daily Keystone Card */}
        {isLoading ? (
          <View style={styles.card}>
            <ActivityIndicator size="small" color={Colors.accent} />
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
            chatPreview.map((msg) => (
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
            <Text style={styles.openChatButtonText}>Continue Reflection</Text>
          </TouchableOpacity>
        </View>
        
        {/* Welcome message */}
        <View style={styles.welcomeCard}>
          <Text style={styles.welcomeText}>Welcome back, {userName || 'friend'}.</Text>
        </View>
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
    borderBottomColor: Colors.cardBorder,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.textPrimary,
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
    backgroundColor: Colors.card,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.cardBorder,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 12,
  },
  cardKeystone: {
    fontSize: 16,
    color: Colors.textPrimary,
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
    backgroundColor: Colors.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.cardBorder,
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
    color: Colors.textPrimary,
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
    backgroundColor: Colors.cardBorder,
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
    color: Colors.textPrimary,
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
    fontSize: 14,
    color: Colors.textTertiary,
  },
  button: {
    backgroundColor: Colors.accent,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 16,
  },
  buttonText: {
    color: Colors.surface,
    fontSize: 16,
    fontWeight: '600',
  },
});
