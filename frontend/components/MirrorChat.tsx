import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
} from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';
import { storage, CHAT_SESSION_KEYS } from '../store';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface MirrorChatProps {
  userId: string;
  lens?: 'astrology' | 'human_design' | 'numerology' | null;
  placeholder?: string;
  headerTitle?: string;
  onClose?: () => void;
}

// Helper to get storage key for a lens context
function getSessionStorageKey(lens: string | null): string {
  if (lens === 'astrology') return CHAT_SESSION_KEYS.astrology;
  if (lens === 'human_design') return CHAT_SESSION_KEYS.human_design;
  return CHAT_SESSION_KEYS.mirror;
}

// Generate a stable session ID (uuid-like)
function generateSessionId(lens: string | null): string {
  const prefix = lens || 'mirror';
  const uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
  return `${prefix}_${uuid}`;
}

export default function MirrorChat({
  userId,
  lens = null,
  placeholder = "What's on your mind?",
  headerTitle = "Mirror",
  onClose,
}: MirrorChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const flatListRef = useRef<FlatList>(null);

  // Load or create persistent session ID
  useEffect(() => {
    async function loadOrCreateSessionId() {
      const storageKey = getSessionStorageKey(lens);
      
      try {
        // Try to load existing session ID
        const existingSessionId = await storage.getItem(storageKey);
        
        if (existingSessionId) {
          console.log(`[MirrorChat] Loaded existing session: ${existingSessionId}`);
          setSessionId(existingSessionId);
        } else {
          // Create new session ID and persist it
          const newSessionId = generateSessionId(lens);
          await storage.setItem(storageKey, newSessionId);
          console.log(`[MirrorChat] Created new session: ${newSessionId}`);
          setSessionId(newSessionId);
        }
      } catch (error) {
        console.error('[MirrorChat] Error loading session:', error);
        // Fallback to in-memory session
        const fallbackId = generateSessionId(lens);
        setSessionId(fallbackId);
      } finally {
        setIsLoadingSession(false);
      }
    }
    
    loadOrCreateSessionId();
  }, [lens]);

  // Add initial greeting
  useEffect(() => {
    const greeting = lens
      ? `I'm here to explore your ${lens === 'human_design' ? 'Human Design' : lens.charAt(0).toUpperCase() + lens.slice(1)} chart with you. What would you like to understand?`
      : "I'm here as a companion for self-understanding. Share what's on your mind, and I'll reflect what I notice.";
    
    setMessages([{
      id: 'greeting',
      role: 'assistant',
      content: greeting,
      timestamp: new Date(),
    }]);
  }, [lens]);

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    Keyboard.dismiss();

    try {
      const response = await api.post('/mirror/chat', {
        user_id: userId,
        message: userMessage.content,
        lens: lens,
        session_id: sessionId,
        include_journal: true,
        include_history: true,
      });

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date(response.data.timestamp),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setSessionId(response.data.session_id);
    } catch (error: any) {
      console.error('Mirror chat error:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: "I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={[
      styles.messageBubble,
      item.role === 'user' ? styles.userBubble : styles.assistantBubble
    ]}>
      {item.role === 'assistant' && (
        <View style={styles.assistantHeader}>
          <Ionicons name="sparkles" size={14} color={Colors.accent} />
          <Text style={styles.assistantName}>Mirror</Text>
        </View>
      )}
      <Text style={[
        styles.messageText,
        item.role === 'user' ? styles.userText : styles.assistantText
      ]}>
        {item.content}
      </Text>
    </View>
  );

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Ionicons name="sparkles" size={20} color={Colors.accent} />
          <Text style={styles.headerTitle}>{headerTitle}</Text>
          {lens && (
            <View style={styles.lensTag}>
              <Text style={styles.lensTagText}>
                {lens === 'human_design' ? 'HD' : lens.charAt(0).toUpperCase() + lens.slice(1)}
              </Text>
            </View>
          )}
        </View>
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={Colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        contentContainerStyle={styles.messagesContainer}
        showsVerticalScrollIndicator={false}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
      />

      {/* Loading indicator */}
      {isLoading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={Colors.accent} />
          <Text style={styles.loadingText}>Mirror is reflecting...</Text>
        </View>
      )}

      {/* Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder={placeholder}
          placeholderTextColor={Colors.textTertiary}
          multiline
          maxLength={2000}
          editable={!isLoading}
        />
        <TouchableOpacity
          style={[styles.sendButton, (!inputText.trim() || isLoading) && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={!inputText.trim() || isLoading}
        >
          <Ionicons 
            name="send" 
            size={20} 
            color={!inputText.trim() || isLoading ? Colors.textTertiary : Colors.surface} 
          />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    backgroundColor: Colors.surface,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  lensTag: {
    backgroundColor: Colors.accent + '20',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  lensTagText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.accent,
  },
  closeButton: {
    padding: 4,
  },
  messagesContainer: {
    padding: 16,
    paddingBottom: 8,
  },
  messageBubble: {
    maxWidth: '85%',
    marginBottom: 12,
    padding: 14,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: Colors.text,
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: Colors.surface,
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  assistantHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 8,
  },
  assistantName: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.accent,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: Colors.background,
  },
  assistantText: {
    color: Colors.text,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    gap: 8,
  },
  loadingText: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    backgroundColor: Colors.surface,
    gap: 10,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.background,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    paddingTop: 10,
    fontSize: 15,
    color: Colors.text,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.accent,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
});
