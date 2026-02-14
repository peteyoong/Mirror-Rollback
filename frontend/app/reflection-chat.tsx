import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter, useLocalSearchParams, useFocusEffect } from 'expo-router';
import { Colors } from '../constants/colors';
import { useAppStore } from '../store';
import { Ionicons } from '@expo/vector-icons';
import { API_BASE_URL, joinUrl } from '../services/api';
import { storageGet, storageSet, getStorageBackend } from '../utils/storage';

// Thread key for reflection chat
const THREAD_KEY = 'reflection:default';
const STORAGE_PREFIX = 'mirror_chat_messages';

// Message interface - timestamp as string for JSON safety
interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string; // ISO string for JSON safety
}

/**
 * Reflection Chat - BULLETPROOF PERSISTENCE
 * 
 * SCREEN: REFLECTION-CHAT (modal route)
 * 
 * Features:
 * - Cross-platform storage (localStorage on web, AsyncStorage on native)
 * - Per-userId hydration guard (handles userId changes)
 * - Debounced persistence on message changes
 * - Flush on blur/unfocus
 * - Visible debug banner
 */
export default function ReflectionChat() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    context?: string;
    dismissed?: string;
  }>();
  
  // Only pull stable primitives from store
  const userId = useAppStore(s => s.user?.id);
  
  // Compute storage key
  const storageKey = userId ? `${STORAGE_PREFIX}:${userId}:${THREAD_KEY}` : null;
  
  // LOCAL STATE for messages - NOT from Zustand store
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Debug state
  const [lastSavedAt, setLastSavedAt] = useState<string>('never');
  const [lastLoadedAt, setLastLoadedAt] = useState<string>('never');
  const [storageBackend, setStorageBackend] = useState<string>('unknown');
  
  const scrollViewRef = useRef<ScrollView>(null);
  
  // Per-userId hydration guard - allows re-hydration if userId changes
  const hydratedForRef = useRef<string | null>(null);
  const persistTimerRef = useRef<any>(null);
  const messagesRef = useRef<Message[]>([]); // For blur callback
  
  // Keep messagesRef in sync
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);
  
  // Generate context-aware opening message
  const getOpeningMessage = useCallback((): Message => {
    const context = params.context;
    const dismissed = params.dismissed === 'true';
    
    let content: string;
    if (dismissed) {
      content = "No need to go anywhere specific.\nWhat's here right now?";
    } else if (context) {
      content = `This may relate to ${context}.\nWhat comes to mind?`;
    } else {
      content = "We can keep this light.\nWhat stood out today?";
    }
    
    return {
      id: 'intro',
      role: 'assistant',
      content,
      timestamp: new Date().toISOString(),
    };
  }, [params.context, params.dismissed]);

  // =========================================================================
  // PER-USER HYDRATION: Load from storage when userId becomes available
  // Re-hydrates if userId changes (e.g., different user logs in)
  // =========================================================================
  useEffect(() => {
    if (!userId || !storageKey) return;
    if (hydratedForRef.current === userId) return; // Already hydrated for this user
    
    hydratedForRef.current = userId;
    console.log(`[ReflectionChat] Hydrating for userId=${userId}, key=${storageKey}`);
    
    (async () => {
      try {
        const raw = await storageGet(storageKey);
        setStorageBackend(getStorageBackend());
        
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed) && parsed.length > 0) {
            console.log(`[ReflectionChat] ✓ Loaded ${parsed.length} messages from storage`);
            setMessages(parsed);
            setLastLoadedAt(new Date().toLocaleTimeString());
            return;
          }
        }
      } catch (e) {
        console.error('[ReflectionChat] Hydration error:', e);
      }
      
      // Only if NO stored messages - create default intro
      console.log('[ReflectionChat] No stored messages, creating intro');
      const intro = getOpeningMessage();
      setMessages([intro]);
      setLastLoadedAt(new Date().toLocaleTimeString());
    })();
  }, [userId, storageKey, getOpeningMessage]);

  // =========================================================================
  // DEBOUNCED PERSISTENCE: Save to storage on message changes
  // =========================================================================
  useEffect(() => {
    if (!userId || !storageKey) return;
    if (hydratedForRef.current !== userId) return; // Don't persist before hydrate
    if (!messages?.length) return;
    
    // Clear any pending persist
    clearTimeout(persistTimerRef.current);
    
    persistTimerRef.current = setTimeout(async () => {
      try {
        await storageSet(storageKey, JSON.stringify(messages));
        setStorageBackend(getStorageBackend());
        setLastSavedAt(new Date().toLocaleTimeString());
        console.log(`[ReflectionChat] ✓ Persisted ${messages.length} messages`);
      } catch (e) {
        console.error('[ReflectionChat] Persist error:', e);
      }
    }, 150);
    
    return () => clearTimeout(persistTimerRef.current);
  }, [messages, userId, storageKey]);

  // =========================================================================
  // FLUSH ON BLUR: Immediately persist when screen loses focus
  // =========================================================================
  useFocusEffect(
    useCallback(() => {
      // On focus - nothing special
      return () => {
        // On blur/unfocus - flush persistence immediately
        if (userId && storageKey && messagesRef.current?.length) {
          console.log(`[ReflectionChat] Blur detected, flushing ${messagesRef.current.length} messages`);
          storageSet(storageKey, JSON.stringify(messagesRef.current));
        }
      };
    }, [userId, storageKey])
  );

  // Auto-scroll when messages change
  useEffect(() => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages.length]);

  // Handle send
  const handleSend = async () => {
    if (!inputText.trim() || isLoading || !userId) return;
    
    const userContent = inputText.trim();
    setInputText('');
    setError(null);
    
    // Add user message to UI immediately (optimistic)
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userContent,
      timestamp: new Date().toISOString(),
    };
    
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setIsLoading(true);
    
    try {
      const endpoint = joinUrl(API_BASE_URL, '/reflection/chat');
      
      // Build conversation history
      const conversationHistory = newMessages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({ role: m.role, content: m.content }));
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'bypass-tunnel-reminder': 'true',
        },
        body: JSON.stringify({
          user_id: userId,
          messages: conversationHistory,
          context: params.context || null,
        }),
        credentials: 'omit',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      const assistantContent = data.response || "I'm here. What else is on your mind?";
      
      // Add assistant message
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, assistantMsg]);
      
    } catch (err: any) {
      console.error('[ReflectionChat] Error:', err);
      setError(err.message || 'Failed to get response');
      
      // Add error message to chat
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: "I'm having trouble connecting. Please try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle back
  const handleBack = () => {
    router.back();
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="light" />
      
      {/* SCREEN IDENTIFIER + DEBUG BANNER */}
      <View style={styles.screenBanner}>
        <Text style={styles.screenName}>SCREEN: REFLECTION-CHAT</Text>
      </View>
      <View style={styles.debugBanner}>
        <Text style={styles.debugText}>
          user={userId?.slice(0, 8) || 'null'} | hydratedFor={hydratedForRef.current?.slice(0, 8) || 'null'} | msgs={messages.length}
        </Text>
        <Text style={styles.debugText}>
          backend={storageBackend} | loaded={lastLoadedAt} | saved={lastSavedAt}
        </Text>
      </View>
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Ionicons name="chevron-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <View style={styles.headerText}>
          <Text style={styles.headerTitle}>Reflection</Text>
          <Text style={styles.headerSubtitle}>A space for noticing</Text>
        </View>
        <View style={styles.headerSpacer} />
      </View>
      
      <KeyboardAvoidingView 
        style={styles.keyboardAvoid}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        {/* Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {messages.map((msg) => (
            <View
              key={msg.id}
              style={[
                styles.messageBubble,
                msg.role === 'user' ? styles.userBubble : styles.assistantBubble,
              ]}
            >
              <Text
                style={[
                  styles.messageText,
                  msg.role === 'user' ? styles.userText : styles.assistantText,
                ]}
              >
                {msg.content}
              </Text>
            </View>
          ))}
          
          {isLoading && (
            <View style={[styles.messageBubble, styles.assistantBubble]}>
              <ActivityIndicator size="small" color={Colors.textSecondary} />
            </View>
          )}
          
          {error && (
            <Text style={styles.errorText}>{error}</Text>
          )}
        </ScrollView>
        
        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="What's on your mind..."
            placeholderTextColor={Colors.textTertiary}
            multiline
            maxLength={1000}
            returnKeyType="default"
          />
          <TouchableOpacity
            style={[
              styles.sendButton,
              (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
            ]}
            onPress={handleSend}
            disabled={!inputText.trim() || isLoading}
          >
            <Ionicons
              name="send"
              size={20}
              color={inputText.trim() && !isLoading ? Colors.surface : Colors.textTertiary}
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  screenBanner: {
    backgroundColor: '#0066cc',
    paddingVertical: 6,
    paddingHorizontal: 8,
  },
  screenName: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
    textAlign: 'center',
  },
  debugBanner: {
    backgroundColor: '#222',
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  debugText: {
    color: '#0f0',
    fontSize: 9,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    textAlign: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backButton: {
    padding: 8,
  },
  headerText: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  headerSubtitle: {
    fontSize: 12,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  headerSpacer: {
    width: 40,
  },
  keyboardAvoid: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 20,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 12,
  },
  userBubble: {
    backgroundColor: Colors.accent,
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: Colors.surfaceLight,
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: Colors.surface,
  },
  assistantText: {
    color: Colors.text,
  },
  errorText: {
    color: '#ff6b6b',
    fontSize: 12,
    textAlign: 'center',
    marginTop: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    paddingRight: 40,
    fontSize: 15,
    color: Colors.text,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sendButton: {
    position: 'absolute',
    right: 24,
    bottom: 20,
    backgroundColor: Colors.accent,
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: Colors.border,
  },
});
