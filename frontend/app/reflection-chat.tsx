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
import { API_BASE_URL, API_URL_MISSING, API_URL_ERROR_MESSAGE, joinUrl } from '../services/api';
import { updateDebugInfo } from '../components/DebugOverlay';

// DEBUG MODE - Set to true to show network trace panel
const DEBUG_MODE = true;

// Pre-compute debug URLs using joinUrl helper
const REFLECTION_CHAT_URL = joinUrl(API_BASE_URL, '/reflection/chat');

// Debug state interface
interface DebugState {
  resolvedApiBaseUrl: string;
  reflectionChatUrl: string;
  envValue: string;
  lastHttpStatus: number | null;
  lastResponseText: string;
  lastParsedResponse: string;
  lastError: string;
  apiUrlMissing: boolean;
}

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
  
  // Debug state for network trace
  const [debugExpanded, setDebugExpanded] = useState(true);
  const [debugState, setDebugState] = useState<DebugState>({
    resolvedApiBaseUrl: API_BASE_URL,
    reflectionChatUrl: REFLECTION_CHAT_URL,
    envValue: process.env.EXPO_PUBLIC_API_BASE_URL || '(not set)',
    lastHttpStatus: null,
    lastResponseText: '',
    lastParsedResponse: '',
    lastError: API_URL_MISSING ? API_URL_ERROR_MESSAGE : '',
    apiUrlMissing: API_URL_MISSING,
  });

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

    // Check if API URL is missing
    if (API_URL_MISSING) {
      setDebugState(prev => ({
        ...prev,
        lastError: 'API_BASE_URL_MISSING - Cannot send request',
        lastHttpStatus: null,
      }));
      return;
    }

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

    // Use the pre-computed URL
    const endpoint = REFLECTION_CHAT_URL;
    
    // Build conversation history for API - ensure correct format
    // Backend expects: { role: "user"|"assistant", content: "..." }
    const conversationHistory = messages
      .filter(m => m.role === 'user' || m.role === 'assistant')
      .map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }));
    conversationHistory.push({ role: 'user', content: userMessage.content });

    // Build the request payload - EXACT schema expected by backend
    const payload = {
      user_id: user.id,
      messages: conversationHistory,
      context: params.context || null,
    };
    
    // Update debug state - clear previous results
    setDebugState(prev => ({
      ...prev,
      lastHttpStatus: null,
      lastResponseText: '',
      lastParsedResponse: '',
      lastError: '',
    }));

    try {
      console.log('[ReflectionChat] Sending request to:', endpoint);
      console.log('[ReflectionChat] Payload:', JSON.stringify(payload));
      
      // FIX: Use credentials: 'omit' to avoid CORS issues with wildcard origins
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        credentials: 'omit',  // FIX: Required for CORS with allow_origins=*
      });
      
      const responseText = await response.text();
      
      // Update debug state with response
      setDebugState(prev => ({
        ...prev,
        lastHttpStatus: response.status,
        lastResponseText: responseText,
      }));
      
      // Also update global debug info for DebugOverlay
      updateDebugInfo({
        lastHttpStatus: response.status,
        lastResponseText: responseText.slice(0, 600),
        lastError: '',
      });
      
      console.log('[ReflectionChat] Status:', response.status);
      console.log('[ReflectionChat] Response text:', responseText);
      
      // Check for non-200 status
      if (!response.ok) {
        const errorMsg = `HTTP ${response.status}: ${responseText}`;
        setDebugState(prev => ({
          ...prev,
          lastError: errorMsg,
        }));
        
        // Show error in chat
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `⚠️ HTTP ${response.status} error. Check debug panel.`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }
      
      // Try to parse the response
      let parsedData: { response?: string } = {};
      try {
        parsedData = JSON.parse(responseText);
        setDebugState(prev => ({
          ...prev,
          lastParsedResponse: JSON.stringify(parsedData, null, 2),
        }));
      } catch (parseError: any) {
        const parseErrorMsg = `JSON parse error: ${parseError.message}`;
        setDebugState(prev => ({
          ...prev,
          lastError: parseErrorMsg,
        }));
        
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `⚠️ Failed to parse response. Check debug panel.`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }
      
      // Extract the response text
      const assistantContent = parsedData.response;
      if (!assistantContent) {
        setDebugState(prev => ({
          ...prev,
          lastError: 'Response missing "response" field',
        }));
        
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `⚠️ Response missing "response" field. Check debug panel.`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: assistantContent,
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
    } catch (error: any) {
      console.error('[ReflectionChat] Fetch error:', error);
      
      // Detect CORS/network errors specifically
      const isCorsError = error.message?.toLowerCase().includes('cors') ||
                         error.message?.toLowerCase().includes('network') ||
                         error.message?.toLowerCase().includes('failed to fetch') ||
                         error.name === 'TypeError';
      
      const errorMsg = isCorsError 
        ? `Network/CORS error: ${error.message || 'Failed to fetch'}`
        : (error.message || 'Unknown fetch error');
      
      setDebugState(prev => ({
        ...prev,
        lastError: errorMsg,
        lastHttpStatus: isCorsError ? -1 : null,  // -1 indicates network-level failure
      }));
      
      // Show appropriate error in chat
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: isCorsError 
          ? `⚠️ Network/CORS blocked in web preview. Check debug panel.`
          : `⚠️ Fetch error: ${errorMsg}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
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
      
      {/* Debug Panel - ON-SCREEN NETWORK TRACE */}
      {DEBUG_MODE && (
        <View style={styles.debugPanel}>
          <TouchableOpacity 
            style={styles.debugHeader}
            onPress={() => setDebugExpanded(!debugExpanded)}
            activeOpacity={0.7}
          >
            <Text style={styles.debugTitle}>🔧 DEBUG TRACE</Text>
            <Ionicons 
              name={debugExpanded ? "chevron-up" : "chevron-down"} 
              size={16} 
              color="#FF6B00" 
            />
          </TouchableOpacity>
          
          {debugExpanded && (
            <ScrollView style={styles.debugContent} nestedScrollEnabled>
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>EXPO_PUBLIC_API_BASE_URL:</Text>
                <Text style={[styles.debugValue, debugState.apiUrlMissing && styles.debugError]} selectable>
                  {debugState.envValue}
                </Text>
              </View>
              
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>resolvedApiBaseUrl:</Text>
                <Text style={[styles.debugValue, debugState.apiUrlMissing && styles.debugError]} selectable>
                  {debugState.resolvedApiBaseUrl}
                </Text>
              </View>
              
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>reflectionChatUrl:</Text>
                <Text style={styles.debugValue} selectable>{debugState.reflectionChatUrl}</Text>
              </View>
              
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>lastHttpStatus:</Text>
                <Text style={[
                  styles.debugValue,
                  debugState.lastHttpStatus && debugState.lastHttpStatus !== 200 && styles.debugError
                ]}>
                  {debugState.lastHttpStatus !== null ? debugState.lastHttpStatus : '(no request yet)'}
                </Text>
              </View>
              
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>lastResponseText (raw):</Text>
                <Text style={styles.debugCode} selectable>
                  {debugState.lastResponseText 
                    ? (debugState.lastResponseText.length > 500 
                        ? debugState.lastResponseText.slice(0, 500) + '...' 
                        : debugState.lastResponseText)
                    : '(none)'}
                </Text>
              </View>
              
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>lastParsedResponse:</Text>
                <Text style={styles.debugCode} selectable>{debugState.lastParsedResponse || '(none)'}</Text>
              </View>
              
              <View style={styles.debugRow}>
                <Text style={styles.debugLabel}>lastError:</Text>
                <Text style={[styles.debugValue, styles.debugError]} selectable>
                  {debugState.lastError || '(none)'}
                </Text>
              </View>
            </ScrollView>
          )}
        </View>
      )}
      
      {/* API URL Missing Banner */}
      {API_URL_MISSING && (
        <View style={styles.errorBanner}>
          <Ionicons name="warning" size={20} color="#FF4444" />
          <Text style={styles.errorBannerText}>Service Unavailable: API URL not configured</Text>
        </View>
      )}
      
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
  // FIX: User bubble is light with dark text
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: 'rgba(255,255,255,0.92)',
  },
  // FIX: Assistant bubble is dark with light text
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderColor: 'rgba(255,255,255,0.10)',
    borderWidth: 1,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 24,
  },
  // FIX: User text must be dark on light background
  userText: {
    color: 'rgba(0,0,0,0.88)',
  },
  // FIX: Assistant text must be light on dark background
  assistantText: {
    color: 'rgba(255,255,255,0.92)',
  },
  // System/intro text style
  systemText: {
    color: 'rgba(255,255,255,0.85)',
  },
  // Timestamp style
  timestamp: {
    color: 'rgba(255,255,255,0.35)',
    fontSize: 11,
    marginTop: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    paddingBottom: Platform.OS === 'web' ? 80 : 12, // Extra padding for web banner
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    gap: 12,
    backgroundColor: Colors.background, // Ensure solid background
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
  // Micro-Reflection Prompt styles
  microPromptContainer: {
    alignItems: 'center',
    marginVertical: 16,
    paddingHorizontal: 8,
  },
  microPromptCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    maxWidth: '90%',
  },
  microPromptText: {
    fontSize: 14,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 20,
  },
  microPromptDismiss: {
    marginTop: 10,
    paddingVertical: 4,
    paddingHorizontal: 12,
  },
  microPromptDismissText: {
    fontSize: 12,
    color: Colors.textTertiary,
    textDecorationLine: 'underline',
  },
  // Error Banner styles
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#330000',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#FF4444',
    gap: 8,
  },
  errorBannerText: {
    color: '#FF4444',
    fontSize: 13,
    fontWeight: '600',
    flex: 1,
  },
  // Debug Panel styles
  debugPanel: {
    backgroundColor: '#1a1a1a',
    borderBottomWidth: 1,
    borderBottomColor: '#FF6B00',
    maxHeight: 280,
  },
  debugHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#252525',
  },
  debugTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#FF6B00',
    letterSpacing: 1,
  },
  debugContent: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  debugRow: {
    marginBottom: 8,
  },
  debugLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#888',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  debugValue: {
    fontSize: 11,
    color: '#00FF88',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  debugCode: {
    fontSize: 10,
    color: '#AADDFF',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    backgroundColor: '#0d0d0d',
    padding: 6,
    borderRadius: 4,
    overflow: 'hidden',
  },
  debugError: {
    color: '#FF4444',
  },
});
