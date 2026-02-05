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
import api from '../services/api';

interface Message {
  id: string;
  role: 'system' | 'user' | 'assistant' | 'micro-prompt';
  content: string;
  timestamp: Date;
}

/**
 * Reflection Chat - Layer 3 of Daily Flow
 * 
 * A gentle space for daily reflection.
 * Pre-seeded with an opening based on context state.
 * 
 * Rules:
 * - Mirroring, not coaching
 * - Noticing, not advising
 * - Short answers are valid
 * - User may leave anytime
 */
export default function ReflectionChat() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    context?: string;
    dismissed?: string;
  }>();
  const { user } = useAppStore();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const hasInitializedRef = useRef(false);
  
  // Micro-Reflection Prompt state (session only, not persisted)
  const [microPromptShown, setMicroPromptShown] = useState(false);
  const [microPromptDismissed, setMicroPromptDismissed] = useState(false);
  const userMessageCountRef = useRef(0);

  // Generate pre-seeded opening message based on state
  const getOpeningMessage = useCallback((): string => {
    const context = params.context;
    const dismissed = params.dismissed === 'true';
    
    // C) If user recently dismissed Daily Focus Card
    if (dismissed) {
      return "No need to go anywhere specific.\nWhat's here right now?";
    }
    
    // B) If Daily Focus Card context was shown
    if (context) {
      return `This may relate to ${context}.\nWhat comes to mind?`;
    }
    
    // A) Default opening (no recent activity)
    return "We can keep this light.\nWhat stood out today?";
  }, [params.context, params.dismissed]);

  // Initialize with opening message
  useEffect(() => {
    if (!hasInitializedRef.current) {
      hasInitializedRef.current = true;
      const opening = getOpeningMessage();
      setMessages([{
        id: 'opening',
        role: 'assistant',
        content: opening,
        timestamp: new Date(),
      }]);
    }
  }, [getOpeningMessage]);

  // Check if we should show micro-reflection prompt
  const shouldShowMicroPrompt = useCallback(() => {
    // Only show once per session, after 2+ user messages, and not if dismissed
    return !microPromptShown && 
           !microPromptDismissed && 
           userMessageCountRef.current >= 2;
  }, [microPromptShown, microPromptDismissed]);

  // Handle dismissing micro-reflection prompt
  const handleDismissMicroPrompt = () => {
    setMicroPromptDismissed(true);
    // Remove the micro-prompt from messages
    setMessages(prev => prev.filter(m => m.role !== 'micro-prompt'));
  };

  const handleSend = async () => {
    if (!inputText.trim() || isLoading || !user?.id) return;

    // Track user message count for micro-prompt logic
    userMessageCountRef.current += 1;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    try {
      // Build conversation history for API
      const conversationHistory = messages.map(m => ({
        role: m.role,
        content: m.content,
      }));
      conversationHistory.push({ role: 'user', content: userMessage.content });

      // Call reflection chat API
      const response = await api.post('/reflection/chat', {
        user_id: user.id,
        messages: conversationHistory,
        context: params.context || null,
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date(),
      };

      setMessages(prev => {
        const newMessages = [...prev, assistantMessage];
        
        // Check if we should inject micro-reflection prompt
        // Only after 2+ user messages, once per session, not if dismissed
        if (shouldShowMicroPrompt() && !microPromptShown) {
          setMicroPromptShown(true);
          const microPrompt: Message = {
            id: 'micro-prompt',
            role: 'micro-prompt',
            content: 'You could pause here, or write a sentence if that feels right.',
            timestamp: new Date(),
          };
          return [...newMessages, microPrompt];
        }
        
        return newMessages;
      });
    } catch (error) {
      console.error('Reflection chat error:', error);
      // Graceful fallback - don't show error, just acknowledge
      const fallbackMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "That feels significant.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  };

  const handleBack = () => {
    router.back();
  };

  if (!user) {
    router.replace('/welcome');
    return null;
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          onPress={handleBack}
          style={styles.backButton}
          hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        >
          <Ionicons name="chevron-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Reflect</Text>
        <View style={styles.headerSpacer} />
      </View>
      
      {/* Messages */}
      <KeyboardAvoidingView 
        style={styles.chatContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
      >
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={() => {
            scrollViewRef.current?.scrollToEnd({ animated: false });
          }}
        >
          {messages.map((message) => {
            // Render micro-reflection prompt with special styling
            if (message.role === 'micro-prompt') {
              return (
                <View key={message.id} style={styles.microPromptContainer}>
                  <View style={styles.microPromptCard}>
                    <Text style={styles.microPromptText}>{message.content}</Text>
                    <TouchableOpacity
                      style={styles.microPromptDismiss}
                      onPress={handleDismissMicroPrompt}
                      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                    >
                      <Text style={styles.microPromptDismissText}>Dismiss</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              );
            }
            
            return (
              <View
                key={message.id}
                style={[
                  styles.messageBubble,
                  message.role === 'user' ? styles.userBubble : styles.assistantBubble,
                ]}
              >
                <Text style={[
                  styles.messageText,
                  message.role === 'user' ? styles.userText : styles.assistantText,
                ]}>
                  {message.content}
                </Text>
              </View>
            );
          })}
          
          {isLoading && (
            <View style={[styles.messageBubble, styles.assistantBubble]}>
              <ActivityIndicator size="small" color={Colors.textTertiary} />
            </View>
          )}
        </ScrollView>
        
        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="What's present..."
            placeholderTextColor={Colors.textTertiary}
            multiline
            maxLength={1000}
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
              name="arrow-up" 
              size={20} 
              color={inputText.trim() && !isLoading ? Colors.background : Colors.textTertiary} 
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
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backButton: {
    width: 40,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '500',
    color: Colors.text,
  },
  headerSpacer: {
    width: 40,
  },
  chatContainer: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 8,
  },
  messageBubble: {
    maxWidth: '85%',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 16,
    marginBottom: 12,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: 'transparent',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 24,
  },
  userText: {
    color: Colors.text,
  },
  assistantText: {
    color: Colors.textSecondary,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    gap: 12,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.surface,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    paddingTop: 10,
    fontSize: 16,
    color: Colors.text,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
  },
});
