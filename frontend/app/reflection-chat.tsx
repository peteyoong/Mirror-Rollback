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
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Colors } from '../constants/colors';
import { useAppStore } from '../store';
import { Ionicons } from '@expo/vector-icons';
import { API_BASE_URL, joinUrl } from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';

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

// Default intro message
const DEFAULT_INTRO_MESSAGE: Message = {
  id: 'intro',
  role: 'assistant',
  content: "We can keep this light.\nWhat stood out today?",
  timestamp: new Date().toISOString(),
};

/**
 * Reflection Chat - LOOP-PROOF Implementation with LOCAL persistence
 * 
 * NO Zustand chatMessages - all persistence is local to this component
 * Uses AsyncStorage directly with debounced writes
 * One-shot hydration guard prevents overwrites
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
  const [hydrated, setHydrated] = useState(false);
  
  const scrollViewRef = useRef<ScrollView>(null);
  const didHydrateRef = useRef(false);
  const persistTimerRef = useRef<any>(null);
  
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
  // ONE-SHOT HYDRATION: Load from storage ONCE when userId becomes available
  // =========================================================================
  useEffect(() => {
    if (!userId || !storageKey) return;
    if (didHydrateRef.current) return;
    didHydrateRef.current = true;
    
    console.log(`[ReflectionChat] Hydrating from storage: ${storageKey}`);
    
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(storageKey);
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed) && parsed.length > 0) {
            console.log(`[ReflectionChat] Loaded ${parsed.length} messages from storage`);
            setMessages(parsed);
            setHydrated(true);
            return;
          }
        }
      } catch (e) {
        console.error('[ReflectionChat] Hydration error:', e);
      }
      
      // Only if no stored messages - create default intro
      console.log('[ReflectionChat] No stored messages, creating intro');
      const intro = getOpeningMessage();
      setMessages([intro]);
      setHydrated(true);
    })();
  }, [userId, storageKey, getOpeningMessage]);

  // =========================================================================
  // DEBOUNCED PERSISTENCE: Save to storage on message changes
  // =========================================================================
  useEffect(() => {
    if (!userId || !storageKey) return;
    if (!didHydrateRef.current) return; // Don't persist before hydrate
    if (!messages?.length) return;
    
    // Clear any pending persist
    clearTimeout(persistTimerRef.current);
    
    persistTimerRef.current = setTimeout(async () => {
      try {
        await AsyncStorage.setItem(storageKey, JSON.stringify(messages));
        console.log(`[ReflectionChat] Persisted ${messages.length} messages`);
      } catch (e) {
        console.error('[ReflectionChat] Persist error:', e);
      }
    }, 150);
    
    return () => clearTimeout(persistTimerRef.current);
  }, [messages, userId, storageKey]);

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
    
    // Note: Persistence is handled by the debounced effect
    
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
      
      {/* DEBUG BANNER (temporary) */}
      <View style={styles.debugBanner}>
        <Text style={styles.debugText}>
          hydrated={hydrated ? 'true' : 'false'} | msgs={messages.length} | key={storageKey?.slice(-20) || 'null'}
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.cardBorder,
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
    color: Colors.textPrimary,
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
    backgroundColor: Colors.card,
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.cardBorder,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: Colors.surface,
  },
  assistantText: {
    color: Colors.textPrimary,
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
    borderTopColor: Colors.cardBorder,
    backgroundColor: Colors.surface,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.card,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    paddingRight: 40,
    fontSize: 15,
    color: Colors.textPrimary,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: Colors.cardBorder,
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
    backgroundColor: Colors.cardBorder,
  },
});
