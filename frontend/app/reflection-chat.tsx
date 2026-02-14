import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Pressable,
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
import { useAppStore, ChatMessage } from '../store';
import { Ionicons } from '@expo/vector-icons';
import { API_BASE_URL, API_URL_MISSING, API_URL_ERROR_MESSAGE, joinUrl } from '../services/api';
import { updateDebugInfo, incrementSendPressCount } from '../components/DebugOverlay';

// DEBUG MODE - Set to true to show network trace panel
const DEBUG_MODE = true;

// Thread key for reflection chat
const REFLECTION_THREAD_KEY = 'reflection:default';

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
  
  // Get store values and actions
  const user = useAppStore(state => state.user);
  const chatMessages = useAppStore(state => state.chatMessages);
  const loadChatMessages = useAppStore(state => state.loadChatMessages);
  const addChatMessage = useAppStore(state => state.addChatMessage);
  
  const userId = user?.id;
  const threadKey = REFLECTION_THREAD_KEY;
  
  // SINGLE SOURCE OF TRUTH: Read messages directly from store
  const storeKey = userId ? `${userId}:${threadKey}` : '';
  const storedMessages = storeKey ? (chatMessages[storeKey] || []) : [];
  
  // Convert stored messages to Message format for rendering
  const messages: Message[] = storedMessages.map(m => ({
    ...m,
    timestamp: new Date(m.timestamp),
  }));
  
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

  // Load/initialize chat messages when userId becomes available
  useEffect(() => {
    const initChat = async () => {
      if (!userId) {
        console.log('[ReflectionChat] No userId yet, skipping init');
        return;
      }
      
      // Only initialize once per userId
      const initKey = `init_${userId}_${threadKey}`;
      if (hasInitializedRef.current) {
        console.log('[ReflectionChat] Already initialized');
        return;
      }
      hasInitializedRef.current = true;
      
      console.log(`[ReflectionChat] Loading messages for userId=${userId}, threadKey=${threadKey}`);
      const loaded = await loadChatMessages(threadKey);
      
      // If no messages exist, create opening message
      if (loaded.length === 0) {
        console.log('[ReflectionChat] No stored messages, creating opening message');
        const opening = getOpeningMessage();
        const openingMessage: ChatMessage = {
          id: 'opening',
          role: 'assistant',
          content: opening,
          timestamp: new Date().toISOString(),
        };
        await addChatMessage(threadKey, openingMessage);
      } else {
        console.log(`[ReflectionChat] Loaded ${loaded.length} messages from store`);
      }
    };
    
    initChat();
  }, [userId, threadKey, loadChatMessages, addChatMessage, getOpeningMessage]);

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

  // Helper to append a system message (visible in chat) - persist to store
  const appendSystemMessage = useCallback(async (content: string) => {
    if (!userId) return;
    const sysMsg: ChatMessage = {
      id: `sys-${Date.now()}`,
      role: 'system',
      content,
      timestamp: new Date().toISOString(),
    };
    await addChatMessage(threadKey, sysMsg);
  }, [userId, threadKey, addChatMessage]);

  const handleSend = async () => {
    // DEBUG: Increment send press count first (proves button fires)
    incrementSendPressCount();
    
    // Update debug state immediately
    updateDebugInfo({
      lastSendAt: new Date().toISOString(),
      lastBailReason: '',
      lastError: '',
    });
    
    console.log('[ReflectionChat] ══════════════════════════════════');
    console.log('[ReflectionChat] SEND PRESSED');
    console.log('[ReflectionChat] inputText:', inputText);
    console.log('[ReflectionChat] isLoading:', isLoading);
    console.log('[ReflectionChat] userId:', userId);
    
    // Check for bail conditions - show visible system messages
    if (!inputText.trim()) {
      console.log('[ReflectionChat] BAIL: empty text');
      updateDebugInfo({ lastBailReason: 'empty_text' });
      await appendSystemMessage('⚠️ BAIL: empty_text - Please enter a message');
      return;
    }
    if (isLoading) {
      console.log('[ReflectionChat] BAIL: already loading');
      updateDebugInfo({ lastBailReason: 'already_loading' });
      await appendSystemMessage('⚠️ BAIL: already_loading - Wait for response');
      return;
    }
    if (!userId) {
      console.log('[ReflectionChat] BAIL: no user id');
      updateDebugInfo({ lastBailReason: 'missing_user_id' });
      await appendSystemMessage('⚠️ BAIL: missing_user_id - Not logged in');
      return;
    }

    // Check if API URL is missing
    if (API_URL_MISSING) {
      updateDebugInfo({ 
        lastBailReason: 'API_URL_MISSING',
        lastError: 'API_BASE_URL not configured',
      });
      appendSystemMessage('⚠️ BAIL: API_URL_MISSING - Service not configured');
      setDebugState(prev => ({
        ...prev,
        lastError: 'API_BASE_URL_MISSING - Cannot send request',
        lastHttpStatus: null,
      }));
      return;
    }

    // OPTIMISTIC: Show user message immediately (before API call)
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date().toISOString(),
    };
    
    // Clear input immediately
    setInputText('');
    
    // Persist user message to store (this updates in-memory AND storage)
    await addChatMessage(threadKey, userMessage);
    
    // Track user message count for micro-prompt logic
    userMessageCountRef.current += 1;
    setIsLoading(true);

    // Scroll to bottom
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    // Use the pre-computed URL
    const endpoint = REFLECTION_CHAT_URL;
    
    // Update debug info with fetch URL
    updateDebugInfo({ lastFetchUrl: endpoint });
    
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
      // Enhanced debug logging
      console.log('[ReflectionChat] ══════════════════════════════════');
      console.log('[ReflectionChat] FINAL URL:', endpoint);
      console.log('[ReflectionChat] Payload:', JSON.stringify(payload));
      console.log('[ReflectionChat] credentials: omit');
      
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
      
      // Enhanced logging for debug
      console.log('[ReflectionChat] STATUS:', response.status);
      console.log('[ReflectionChat] RESPONSE (first 300 chars):', responseText.slice(0, 300));
      console.log('[ReflectionChat] ══════════════════════════════════');
      
      // Update debug state with response
      setDebugState(prev => ({
        ...prev,
        lastHttpStatus: response.status,
        lastResponseText: responseText,
      }));
      
      // Also update global debug info for DebugOverlay
      updateDebugInfo({
        lastHttpStatus: response.status,
        lastResponseText: responseText.slice(0, 300),
        lastError: '',
      });
      
      // Check for non-200 status
      if (!response.ok) {
        const errorMsg = `HTTP ${response.status}: ${responseText}`;
        setDebugState(prev => ({
          ...prev,
          lastError: errorMsg,
        }));
        
        // Show error in chat
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `⚠️ HTTP ${response.status} error. Check debug panel.`,
          timestamp: new Date().toISOString(),
        };
        await addChatMessage(threadKey, errorMessage);
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
        
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `⚠️ Failed to parse response. Check debug panel.`,
          timestamp: new Date().toISOString(),
        };
        await addChatMessage(threadKey, errorMessage);
        return;
      }
      
      // Extract the response text
      const assistantContent = parsedData.response;
      if (!assistantContent) {
        setDebugState(prev => ({
          ...prev,
          lastError: 'Response missing "response" field',
        }));
        
        const errorMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `⚠️ Response missing "response" field. Check debug panel.`,
          timestamp: new Date().toISOString(),
        };
        await addChatMessage(threadKey, errorMessage);
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
        
        // Persist assistant message to store
        addChatMessage(REFLECTION_THREAD_KEY, {
          ...assistantMessage,
          timestamp: assistantMessage.timestamp.toISOString(),
        } as unknown as ChatMessage);
        
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
      
      // Update global debug info
      updateDebugInfo({
        lastError: errorMsg,
        lastHttpStatus: isCorsError ? -1 : null,
      });
      
      // Show error in chat (visible to user)
      appendSystemMessage(`❌ ERROR: ${isCorsError ? 'CORS/Network' : ''} ${String(errorMsg).slice(0, 120)}`);
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
      
      {/* Local Debug Panel - DISABLED (using global DebugOverlay instead) */}
      {false && DEBUG_MODE && (
        <View style={[styles.debugPanel, { pointerEvents: 'none' }]}>
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
          {/* Empty state - visible when no messages */}
          {messages.length === 0 && !isLoading && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>Say what's real right now…</Text>
            </View>
          )}
          
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
            
            // FIX: Normalize roles before styling - handle any role string
            // Unknown roles MUST render as assistant (dark bubble + light text)
            const rawRole = ((message as any).role ?? (message as any).sender ?? (message as any).type ?? '').toString().toLowerCase();
            const role: 'user' | 'assistant' | 'system' =
              rawRole.includes('user') ? 'user'
              : rawRole.includes('system') ? 'system'
              : 'assistant'; // DEFAULT: Everything else is assistant (dark bubble)
            
            // Get bubble and text styles based on role
            const getBubbleStyle = () => {
              if (role === 'user') return styles.userBubble;
              if (role === 'system') return styles.systemBubble;
              return styles.assistantBubble; // default
            };
            
            const getTextStyle = () => {
              if (role === 'user') return styles.userText;
              if (role === 'system') return styles.systemText;
              return styles.assistantText; // default
            };
            
            return (
              <View
                key={message.id}
                style={[styles.messageBubble, getBubbleStyle()]}
              >
                <Text style={[styles.messageText, getTextStyle()]}>
                  {message.content}
                </Text>
              </View>
            );
          })}
          
          {isLoading && (
            <View style={[styles.messageBubble, styles.assistantBubble]}>
              <ActivityIndicator size="small" color="rgba(255,255,255,0.6)" />
            </View>
          )}
        </ScrollView>
        
        {/* Input - explicitly interactive with VERY high zIndex */}
        <View style={[styles.inputContainer, { pointerEvents: 'auto' }]}>
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder="What's present..."
            placeholderTextColor={Colors.textTertiary}
            multiline
            maxLength={1000}
            returnKeyType="send"
            blurOnSubmit={false}
            editable={!isLoading}
            onSubmitEditing={() => {
              console.log('[ReflectionChat] onSubmitEditing triggered');
              if (inputText.trim() && !isLoading) {
                handleSend();
              }
            }}
          />
          {/* Send button wrapper - explicit style.pointerEvents for web compatibility */}
          <View style={[styles.sendButtonWrapper, { pointerEvents: 'auto' }]}>
            <Pressable
              style={({ pressed }) => [
                styles.sendButton,
                (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
                pressed && { opacity: 0.7, transform: [{ scale: 0.95 }] },
              ]}
              onPress={() => {
                console.log('[ReflectionChat] ════════════════════════════');
                console.log('[ReflectionChat] onPress FIRED!');
                handleSend();
              }}
              onPressIn={() => {
                console.log('[ReflectionChat] onPressIn FIRED!');
                incrementSendPressCount();
              }}
              // Web-specific handlers
              {...(Platform.OS === 'web' ? {
                onPointerDown: () => {
                  console.log('[ReflectionChat] onPointerDown FIRED!');
                  incrementSendPressCount();
                },
                onTouchStart: () => {
                  console.log('[ReflectionChat] onTouchStart FIRED!');
                  incrementSendPressCount();
                },
              } : {})}
              disabled={!inputText.trim() || isLoading}
              hitSlop={{ top: 16, bottom: 16, left: 16, right: 16 }}
            >
              <Ionicons 
                name="arrow-up" 
                size={22} 
                color={inputText.trim() && !isLoading ? Colors.background : Colors.textTertiary} 
              />
            </Pressable>
          </View>
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
  // FIX: System bubble - same as assistant but explicitly defined
  systemBubble: {
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
  // Empty state - visible prompt when no messages
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    color: 'rgba(255,255,255,0.75)',
    fontSize: 17,
    fontStyle: 'italic',
    textAlign: 'center',
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
    zIndex: 99999, // FIX: VERY high to ensure above AddToHomeScreenBanner
    position: 'relative', // FIX: Required for zIndex to work
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
    width: 48, // FIX: Larger touch target (minimum 44px)
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonWrapper: {
    zIndex: 100000, // FIX: Ensure send button wrapper is above everything
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
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 18,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.10)',
    alignItems: 'center',
    maxWidth: '90%',
  },
  microPromptText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.75)',
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
    color: 'rgba(255,255,255,0.45)',
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
