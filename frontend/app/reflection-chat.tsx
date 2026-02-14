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
import { getApiBaseUrl, joinUrl } from '../utils/apiBase';
import { getChatStorageKey, DEFAULT_THREAD_KEY, saveMessages, loadMessages, ChatMessage } from '../utils/chatPersistence';

// Use shared thread key for unified persistence
const THREAD_KEY = DEFAULT_THREAD_KEY;

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

/**
 * Reflection Chat - Clean, Bulletproof Persistence
 */
export default function ReflectionChat() {
  const router = useRouter();
  const params = useLocalSearchParams<{ context?: string; dismissed?: string }>();
  
  const userId = useAppStore(s => s.user?.id);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const scrollViewRef = useRef<ScrollView>(null);
  const hydratedForRef = useRef<string | null>(null);
  const persistTimerRef = useRef<any>(null);
  const messagesRef = useRef<Message[]>([]);
  
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);
  
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

  // Hydrate messages from storage
  useEffect(() => {
    if (!userId) return;
    if (hydratedForRef.current === userId) return;
    
    hydratedForRef.current = userId;
    
    (async () => {
      try {
        const loaded = await loadMessages(userId, THREAD_KEY);
        if (loaded.length > 0) {
          setMessages(loaded as Message[]);
          return;
        }
      } catch (e) {
        console.error('[ReflectionChat] Hydration error:', e);
      }
      
      const intro = getOpeningMessage();
      setMessages([intro]);
    })();
  }, [userId, getOpeningMessage]);

  // Persist messages (debounced)
  useEffect(() => {
    if (!userId) return;
    if (hydratedForRef.current !== userId) return;
    if (!messages?.length) return;
    
    clearTimeout(persistTimerRef.current);
    persistTimerRef.current = setTimeout(async () => {
      try {
        await saveMessages(userId, THREAD_KEY, messages as ChatMessage[]);
      } catch (e) {
        console.error('[ReflectionChat] Persist error:', e);
      }
    }, 200);
    
    return () => clearTimeout(persistTimerRef.current);
  }, [messages, userId, storageKey]);

  // Flush on blur
  useFocusEffect(
    useCallback(() => {
      return () => {
        if (userId && messagesRef.current?.length) {
          saveMessages(userId, THREAD_KEY, messagesRef.current as ChatMessage[]);
        }
      };
    }, [userId])
  );

  useEffect(() => {
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, [messages.length]);

  const handleSend = async () => {
    if (!inputText.trim() || isLoading || !userId) return;
    
    const userContent = inputText.trim();
    setInputText('');
    setError(null);
    
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
      const endpoint = joinUrl(getApiBaseUrl(), '/reflection/chat');
      
      const conversationHistory = newMessages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({ role: m.role, content: m.content }));
      
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'omit',
        mode: 'cors',
        body: JSON.stringify({
          user_id: userId,
          messages: conversationHistory,
          context: params.context || null,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      const assistantContent = data.response || "I'm here. What else is on your mind?";
      
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, assistantMsg]);
      
    } catch (err: any) {
      setError(err.message || 'Failed to get response');
      
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

  const handleBack = () => {
    router.back();
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="light" />
      
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
          
          {error && <Text style={styles.errorText}>{error}</Text>}
        </ScrollView>
        
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
