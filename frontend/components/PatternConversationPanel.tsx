/**
 * PatternConversationPanel.tsx
 * 
 * Task 76: Conversational Intelligence Layer
 * 
 * A chat-style interface for exploring patterns interactively.
 * Entry points: Archetype card, Home screen, Patterns tab
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ScrollView,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import api from '../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface ConversationTurn {
  role: 'user' | 'mirror';
  content: string;
  timestamp: Date;
  archetype_icon?: string;
  referenced_events?: Array<{ year: number; title: string }>;
}

interface ArchetypeInfo {
  name: string;
  icon: string;
  summary: string;
}

interface ConversationPanelProps {
  visible: boolean;
  onClose: () => void;
  initialContext?: string; // Optional context to start the conversation
}

// =============================================================================
// COLORS
// =============================================================================

const COLORS = {
  accent: '#9B8AC4',
  accentLight: 'rgba(155, 138, 196, 0.15)',
  userBubble: 'rgba(155, 138, 196, 0.25)',
  mirrorBubble: 'rgba(255, 255, 255, 0.08)',
  border: 'rgba(255, 255, 255, 0.1)',
};

// =============================================================================
// COMPONENT
// =============================================================================

export default function PatternConversationPanel({ 
  visible, 
  onClose,
  initialContext 
}: ConversationPanelProps) {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const scrollViewRef = useRef<ScrollView>(null);
  
  // State
  const [messages, setMessages] = useState<ConversationTurn[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [archetype, setArchetype] = useState<ArchetypeInfo | null>(null);
  const [initialPrompt, setInitialPrompt] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Load initial prompt when panel opens
  useEffect(() => {
    if (visible && user?.id && messages.length === 0) {
      loadInitialPrompt();
    }
  }, [visible, user?.id]);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  const loadInitialPrompt = async () => {
    if (!user?.id) return;
    
    try {
      setIsLoading(true);
      const response = await api.get(`/pattern-conversation/${user.id}/start`);
      
      if (response.data?.success) {
        setInitialPrompt(response.data.prompt);
        setArchetype(response.data.archetype);
        
        // Add initial Mirror message
        const initialMessage: ConversationTurn = {
          role: 'mirror',
          content: response.data.prompt,
          timestamp: new Date(),
          archetype_icon: response.data.archetype?.icon || '◈'
        };
        setMessages([initialMessage]);
      }
    } catch (err) {
      console.log('[Conversation] Error loading initial prompt:', err);
      setError('Unable to start conversation. Try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputText.trim() || !user?.id || isLoading) return;
    
    const userMessage = inputText.trim();
    setInputText('');
    setError(null);
    
    // Add user message immediately
    const userTurn: ConversationTurn = {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userTurn]);
    
    try {
      setIsLoading(true);
      
      // Build conversation history for context
      const history = messages.map(m => ({
        role: m.role === 'mirror' ? 'assistant' : 'user',
        content: m.content
      }));
      
      const response = await api.post(`/pattern-conversation/${user.id}`, {
        message: userMessage,
        conversation_history: history
      });
      
      if (response.data?.success) {
        const mirrorTurn: ConversationTurn = {
          role: 'mirror',
          content: response.data.response,
          timestamp: new Date(),
          archetype_icon: response.data.archetype_icon || '◈',
          referenced_events: response.data.referenced_events
        };
        setMessages(prev => [...prev, mirrorTurn]);
        
        // Add follow-up question if provided
        if (response.data.follow_up_question) {
          setTimeout(() => {
            const followUp: ConversationTurn = {
              role: 'mirror',
              content: response.data.follow_up_question,
              timestamp: new Date(),
              archetype_icon: response.data.archetype_icon || '◈'
            };
            setMessages(prev => [...prev, followUp]);
          }, 1000);
        }
      } else {
        setError(response.data?.error || 'Unable to generate response');
      }
    } catch (err) {
      console.log('[Conversation] Error:', err);
      setError('Connection error. Try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setMessages([]);
    setInputText('');
    setError(null);
    onClose();
  };

  const renderMessage = (message: ConversationTurn, index: number) => {
    const isUser = message.role === 'user';
    
    return (
      <View 
        key={index} 
        style={[
          styles.messageBubble,
          isUser ? styles.userBubble : styles.mirrorBubble,
          { backgroundColor: isUser ? COLORS.userBubble : COLORS.mirrorBubble }
        ]}
      >
        {!isUser && (
          <View style={styles.mirrorHeader}>
            <Text style={styles.mirrorIcon}>{message.archetype_icon || '◈'}</Text>
            <Text style={[styles.mirrorLabel, { color: theme.textTertiary }]}>Mirror</Text>
          </View>
        )}
        
        <Text style={[
          styles.messageText, 
          { color: isUser ? theme.text : theme.text }
        ]}>
          {message.content}
        </Text>
        
        {/* Referenced events */}
        {message.referenced_events && message.referenced_events.length > 0 && (
          <View style={styles.referencedEvents}>
            {message.referenced_events.map((event, i) => (
              <View key={i} style={[styles.eventTag, { borderColor: COLORS.border }]}>
                <Text style={[styles.eventTagText, { color: theme.textTertiary }]}>
                  {event.year}: {event.title}
                </Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={handleClose}
    >
      <KeyboardAvoidingView 
        style={[styles.container, { backgroundColor: theme.background }]}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        {/* Header */}
        <View style={[styles.header, { borderBottomColor: COLORS.border }]}>
          <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={theme.text} />
          </TouchableOpacity>
          
          <View style={styles.headerCenter}>
            <Text style={[styles.headerTitle, { color: theme.text }]}>
              Explore with Mirror
            </Text>
            {archetype && (
              <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]}>
                {archetype.icon} {archetype.name} Pattern
              </Text>
            )}
          </View>
          
          <View style={styles.headerRight} />
        </View>

        {/* Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {messages.map((message, index) => renderMessage(message, index))}
          
          {isLoading && (
            <View style={[styles.messageBubble, styles.mirrorBubble, { backgroundColor: COLORS.mirrorBubble }]}>
              <View style={styles.loadingRow}>
                <ActivityIndicator size="small" color={COLORS.accent} />
                <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
                  Mirror is thinking...
                </Text>
              </View>
            </View>
          )}
          
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}
        </ScrollView>

        {/* Input */}
        <View style={[styles.inputContainer, { borderTopColor: COLORS.border, backgroundColor: theme.surface }]}>
          <TextInput
            style={[styles.textInput, { color: theme.text, backgroundColor: theme.background }]}
            placeholder="Share what's on your mind..."
            placeholderTextColor={theme.textTertiary}
            value={inputText}
            onChangeText={setInputText}
            multiline
            maxLength={500}
            editable={!isLoading}
            onSubmitEditing={sendMessage}
            blurOnSubmit={false}
          />
          
          <TouchableOpacity
            style={[
              styles.sendButton,
              { backgroundColor: inputText.trim() ? COLORS.accent : COLORS.accentLight }
            ]}
            onPress={sendMessage}
            disabled={!inputText.trim() || isLoading}
          >
            <Ionicons 
              name="arrow-up" 
              size={20} 
              color={inputText.trim() ? '#FFFFFF' : theme.textTertiary} 
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// =============================================================================
// INLINE ENTRY POINT BUTTON
// =============================================================================

interface ExploreButtonProps {
  onPress: () => void;
  label?: string;
  compact?: boolean;
}

export function ExploreWithMirrorButton({ 
  onPress, 
  label = "Explore this with Mirror",
  compact = false 
}: ExploreButtonProps) {
  const { theme } = useTheme();
  
  if (compact) {
    return (
      <TouchableOpacity 
        style={[styles.compactButton, { borderColor: COLORS.accent }]} 
        onPress={onPress}
        activeOpacity={0.7}
      >
        <Ionicons name="chatbubble-outline" size={14} color={COLORS.accent} />
        <Text style={[styles.compactButtonText, { color: COLORS.accent }]}>
          Explore
        </Text>
      </TouchableOpacity>
    );
  }
  
  return (
    <TouchableOpacity 
      style={[styles.exploreButton, { backgroundColor: COLORS.accentLight, borderColor: COLORS.accent }]} 
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Ionicons name="chatbubble-outline" size={16} color={COLORS.accent} />
      <Text style={[styles.exploreButtonText, { color: COLORS.accent }]}>
        {label}
      </Text>
      <Ionicons name="chevron-forward" size={14} color={COLORS.accent} />
    </TouchableOpacity>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  closeButton: {
    padding: 4,
    width: 40,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  headerSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  headerRight: {
    width: 40,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 24,
  },
  messageBubble: {
    maxWidth: '85%',
    borderRadius: 16,
    padding: 12,
    marginBottom: 16,
  },
  userBubble: {
    alignSelf: 'flex-end',
    borderBottomRightRadius: 4,
  },
  mirrorBubble: {
    alignSelf: 'flex-start',
    borderBottomLeftRadius: 4,
  },
  mirrorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
    gap: 6,
  },
  mirrorIcon: {
    fontSize: 16,
  },
  mirrorLabel: {
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  messageText: {
    fontSize: 17,
    lineHeight: 26,
  },
  referencedEvents: {
    marginTop: 10,
    gap: 4,
  },
  eventTag: {
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    alignSelf: 'flex-start',
  },
  eventTagText: {
    fontSize: 14,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  errorContainer: {
    alignSelf: 'center',
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    padding: 10,
    borderRadius: 8,
    marginTop: 8,
  },
  errorText: {
    color: '#EF4444',
    fontSize: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    padding: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  textInput: {
    flex: 1,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    maxHeight: 100,
    fontSize: 17,
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  exploreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginTop: 12,
  },
  exploreButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  compactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
  },
  compactButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
