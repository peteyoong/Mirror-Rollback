import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  LayoutAnimation,
  UIManager,
  Modal,
  TextInputProps,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';
import { storage, CHAT_SESSION_KEYS } from '../store';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface MemoryUpdate {
  themes: string[];
  recurring_tensions: string[];
  supportive_moves: string[];
  drainers: string[];
  inferred_state: string;
  confidence: number;
  evidence: string[];
  updated_at_iso: string;
}

interface KeystoneContext {
  date: string;
  title: string;
  keystone: string;
  reflect_question: string;
  micro_affirmation: string;
  tone: string;
  daily_seed: string;
}

interface ThreadState {
  active: boolean;
  thread_type: string;
  thread_date: string;
  remaining_turns: number;
  title?: string;
  keystone?: string;
  reflect_question?: string;
  micro_affirmation?: string;
  tone?: string;
}

interface MirrorChatProps {
  userId: string;
  lens?: 'astrology' | 'human_design' | 'numerology' | null;
  placeholder?: string;
  headerTitle?: string;
  headerSubtitle?: string;
  onClose?: () => void;
  keystoneContext?: KeystoneContext | null;  // For keystone continuation
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

// Format timestamp subtly
function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

// Format inferred state for display
function formatState(state: string): string {
  const labels: Record<string, string> = {
    'grounding': 'grounding',
    'stabilizing': 'stabilizing',
    'exploring': 'exploring',
    'integrating': 'integrating',
    'unclear': 'in flux',
  };
  return labels[state] || state;
}

export default function MirrorChat({
  userId,
  lens = null,
  placeholder = "Say what's real right now…",
  headerTitle = "Mirror",
  headerSubtitle = "A mirror, not a verdict.",
  onClose,
  keystoneContext = null,
}: MirrorChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [memoryUpdate, setMemoryUpdate] = useState<MemoryUpdate | null>(null);
  const [isMemoryExpanded, setIsMemoryExpanded] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const [hasTriggeredKeystone, setHasTriggeredKeystone] = useState(false);
  
  // Thread state for "Today's thread" pill
  const [threadState, setThreadState] = useState<ThreadState | null>(null);
  const [showThreadModal, setShowThreadModal] = useState(false);
  
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const insets = useSafeAreaInsets();

  // Load or create persistent session ID
  useEffect(() => {
    async function loadOrCreateSessionId() {
      const storageKey = getSessionStorageKey(lens);
      
      try {
        const existingSessionId = await storage.getItem(storageKey);
        
        if (existingSessionId) {
          console.log(`[MirrorChat] Loaded existing session: ${existingSessionId}`);
          setSessionId(existingSessionId);
        } else {
          const newSessionId = generateSessionId(lens);
          await storage.setItem(storageKey, newSessionId);
          console.log(`[MirrorChat] Created new session: ${newSessionId}`);
          setSessionId(newSessionId);
        }
      } catch (error) {
        console.error('[MirrorChat] Error loading session:', error);
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

  // ===== KEYSTONE CONTINUATION AUTO-TRIGGER =====
  // When keystoneContext is provided, automatically send continuation message
  useEffect(() => {
    async function triggerKeystoneContinuation() {
      if (!keystoneContext || !sessionId || hasTriggeredKeystone || isLoading) return;
      
      // Check if we've already triggered for this date (once per day)
      const KEYSTONE_FOLLOWUP_KEY = 'last_keystone_followup_date';
      try {
        const lastFollowupDate = await storage.getItem(KEYSTONE_FOLLOWUP_KEY);
        if (lastFollowupDate === keystoneContext.date) {
          console.log('[MirrorChat] Keystone continuation already triggered today');
          setHasTriggeredKeystone(true);
          return;
        }
      } catch (e) {
        // Continue if storage read fails
      }
      
      console.log('[MirrorChat] Triggering keystone continuation for date:', keystoneContext.date);
      setHasTriggeredKeystone(true);
      setIsLoading(true);
      
      // Add a user message indicating continuation
      const userMessage: Message = {
        id: `user-keystone-${Date.now()}`,
        role: 'user',
        content: "Continue from today's reflection…",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, userMessage]);
      
      try {
        const response = await api.post('/mirror/chat', {
          user_id: userId,
          message: "Continue from today's keystone.",
          lens: null,
          session_id: sessionId,
          include_journal: true,
          include_history: true,
          keystone_context: keystoneContext,
        });
        
        const assistantMessage: Message = {
          id: `assistant-keystone-${Date.now()}`,
          role: 'assistant',
          content: response.data.response,
          timestamp: new Date(response.data.timestamp),
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        
        if (response.data.memory_update) {
          setMemoryUpdate(response.data.memory_update);
        }
        
        // Capture thread state from keystone continuation
        if (response.data.thread) {
          setThreadState(response.data.thread);
        }
        
        // Mark this date as followed up
        await storage.setItem(KEYSTONE_FOLLOWUP_KEY, keystoneContext.date);
        console.log('[MirrorChat] Keystone continuation complete');
        
      } catch (error) {
        console.error('[MirrorChat] Keystone continuation error:', error);
        // Add a fallback message
        const fallbackMessage: Message = {
          id: `assistant-fallback-${Date.now()}`,
          role: 'assistant',
          content: "I'm here with you. What's present right now?",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, fallbackMessage]);
      } finally {
        setIsLoading(false);
      }
    }
    
    if (keystoneContext && sessionId && !isLoadingSession && !hasTriggeredKeystone) {
      triggerKeystoneContinuation();
    }
  }, [keystoneContext, sessionId, isLoadingSession, hasTriggeredKeystone, userId]);

  const toggleMemoryExpanded = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIsMemoryExpanded(!isMemoryExpanded);
    if (isMemoryExpanded) {
      setShowEvidence(false); // Reset evidence when collapsing
    }
  };

  const toggleEvidence = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setShowEvidence(!showEvidence);
  };

  const handleSend = async () => {
    if (!inputText.trim() || isLoading || !sessionId) return;

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

    // ============================================
    // DEBUG LOGGING - MIRROR CHAT REQUEST
    // ============================================
    const requestPayload = {
      user_id: userId,
      message: userMessage.content,
      lens: lens,
      session_id: sessionId,
      include_journal: true,
      include_history: true,
    };
    
    console.log('[MIRROR_CHAT_REQUEST]', {
      endpoint: '/api/mirror/chat',
      user_id: userId,
      payload: requestPayload,
      build: process.env.EXPO_PUBLIC_BUILD_VERSION || 'unknown',
    });
    
    // Log API base URL for debugging
    console.log('[MIRROR_CHAT_DEBUG] API_BASE_URL:', api.defaults.baseURL);

    try {
      const response = await api.post('/mirror/chat', requestPayload);

      // ============================================
      // DEBUG LOGGING - MIRROR CHAT RESPONSE
      // ============================================
      console.log('[MIRROR_CHAT_RESPONSE]', {
        status: response.status,
        has_response: !!response.data?.response,
        session_id: response.data?.session_id,
        has_memory_update: !!response.data?.memory_update,
        has_thread: !!response.data?.thread,
      });

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date(response.data.timestamp),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setSessionId(response.data.session_id);
      
      // Store memory update if present
      if (response.data.memory_update) {
        setMemoryUpdate(response.data.memory_update);
      }
      
      // Update thread state from response (only for generalist chat)
      if (!lens && response.data.thread) {
        setThreadState(response.data.thread);
      } else if (!lens && !response.data.thread) {
        setThreadState(null);
      }
    } catch (error: any) {
      // ============================================
      // DEBUG LOGGING - MIRROR CHAT ERROR
      // ============================================
      console.error('[MIRROR_CHAT_ERROR]', {
        message: error?.message,
        status: error?.response?.status,
        statusText: error?.response?.statusText,
        data: error?.response?.data,
        code: error?.code,
      });
      
      // Check for structured error response
      const errorData = error?.response?.data?.detail;
      const errorCode = typeof errorData === 'object' ? errorData?.error_code : null;
      
      // Determine error message based on status and error_code
      let errorContent = "Mirror couldn't reach its reflection service. Please try again.";
      
      // Handle structured error codes
      if (errorCode === 'mirror_interpret_failed') {
        errorContent = "Mirror lost the thread while preparing that reflection. Please try again.";
      } else if (error?.response?.status === 429) {
        errorContent = "Mirror needs a pause. Try again in a little while.";
      } else if (error?.response?.status === 404) {
        errorContent = "Your profile wasn't found. Please try logging in again.";
      } else if (error?.response?.status === 500) {
        // Use structured message if available, otherwise generic
        const detail = typeof errorData === 'object' ? errorData?.message : errorData;
        errorContent = detail || "Mirror encountered an issue. Please try again.";
      } else if (error?.code === 'ECONNABORTED') {
        errorContent = "The reflection took too long. Please try a shorter message.";
      } else if (!error?.response) {
        errorContent = "Unable to connect to Mirror. Please check your connection.";
      }
      
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: errorContent,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = ({ item, index }: { item: Message; index: number }) => {
    const isUser = item.role === 'user';
    const isFirstMessage = index === 0;
    
    return (
      <View style={[
        styles.messageWrapper,
        isUser ? styles.userWrapper : styles.assistantWrapper,
        isFirstMessage && styles.firstMessage,
      ]}>
        <View style={[
          styles.messageBubble,
          isUser ? styles.userBubble : styles.assistantBubble
        ]}>
          <Text style={[
            styles.messageText,
            isUser ? styles.userText : styles.assistantText
          ]}>
            {item.content}
          </Text>
        </View>
        <Text style={[
          styles.timestamp,
          isUser ? styles.timestampRight : styles.timestampLeft
        ]}>
          {formatTime(item.timestamp)}
        </Text>
      </View>
    );
  };

  // Memory Card Component
  const renderMemoryCard = () => {
    if (!memoryUpdate || lens !== null) return null; // Only show in generalist Mirror Chat
    
    return (
      <View style={styles.memoryCard}>
        <TouchableOpacity 
          style={styles.memoryHeader} 
          onPress={toggleMemoryExpanded}
          activeOpacity={0.7}
        >
          <Text style={styles.memoryTitle}>What Mirror is noticing lately</Text>
          <Ionicons 
            name={isMemoryExpanded ? "chevron-up" : "chevron-down"} 
            size={18} 
            color={Colors.textTertiary} 
          />
        </TouchableOpacity>
        
        {isMemoryExpanded && (
          <View style={styles.memoryContent}>
            {/* Themes (max 2) */}
            {memoryUpdate.themes.length > 0 && (
              <View style={styles.memorySection}>
                <Text style={styles.memorySectionLabel}>Themes surfacing</Text>
                {memoryUpdate.themes.slice(0, 2).map((theme, i) => (
                  <Text key={i} style={styles.memoryItem}>• {theme}</Text>
                ))}
              </View>
            )}
            
            {/* Recurring tension (max 1) */}
            {memoryUpdate.recurring_tensions.length > 0 && (
              <View style={styles.memorySection}>
                <Text style={styles.memorySectionLabel}>A tension present</Text>
                <Text style={styles.memoryItem}>• {memoryUpdate.recurring_tensions[0]}</Text>
              </View>
            )}
            
            {/* Inferred state */}
            {memoryUpdate.inferred_state && memoryUpdate.inferred_state !== 'unclear' && (
              <View style={styles.stateContainer}>
                <Text style={styles.stateLabel}>
                  Current tone: <Text style={styles.stateValue}>{formatState(memoryUpdate.inferred_state)}</Text>
                </Text>
              </View>
            )}
            
            {/* Show details toggle */}
            <TouchableOpacity 
              style={styles.detailsToggle} 
              onPress={toggleEvidence}
              activeOpacity={0.7}
            >
              <Text style={styles.detailsToggleText}>
                {showEvidence ? 'Hide details' : 'Show details'}
              </Text>
            </TouchableOpacity>
            
            {/* Evidence (hidden by default) */}
            {showEvidence && memoryUpdate.evidence.length > 0 && (
              <View style={styles.evidenceSection}>
                <Text style={styles.evidenceLabel}>Based on</Text>
                {memoryUpdate.evidence.slice(0, 3).map((ev, i) => (
                  <Text key={i} style={styles.evidenceItem}>"{ev}"</Text>
                ))}
              </View>
            )}
            
            {/* Footer */}
            <Text style={styles.memoryFooter}>
              Take what resonates; leave what doesn't.
            </Text>
          </View>
        )}
      </View>
    );
  };

  // Thread Pill - shows when active keystone thread (generalist only)
  const renderThreadPill = () => {
    if (lens || !threadState?.active) return null;
    
    const formatDate = (dateStr: string) => {
      const date = new Date(dateStr + 'T00:00:00');
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };
    
    return (
      <TouchableOpacity
        style={styles.threadPill}
        onPress={() => setShowThreadModal(true)}
        activeOpacity={0.7}
      >
        <Ionicons name="link-outline" size={14} color={Colors.accent} />
        <Text style={styles.threadPillText}>Today's thread</Text>
        <Text style={styles.threadPillDate}>{formatDate(threadState.thread_date)}</Text>
        <Ionicons name="chevron-forward" size={12} color={Colors.textTertiary} />
      </TouchableOpacity>
    );
  };

  // Thread Modal - shows keystone recap
  const renderThreadModal = () => {
    if (!threadState) return null;
    
    return (
      <Modal
        visible={showThreadModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowThreadModal(false)}
      >
        <TouchableOpacity
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowThreadModal(false)}
        >
          <TouchableOpacity activeOpacity={1} onPress={(e) => e.stopPropagation()}>
            <View style={styles.threadModalContent}>
              {/* Close button */}
              <TouchableOpacity
                style={styles.threadModalClose}
                onPress={() => setShowThreadModal(false)}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              >
                <Ionicons name="close" size={20} color={Colors.textSecondary} />
              </TouchableOpacity>
              
              {/* Title */}
              {threadState.title && (
                <Text style={styles.threadModalTitle}>
                  {threadState.title.toUpperCase()}
                </Text>
              )}
              
              {/* Keystone text */}
              {threadState.keystone && (
                <Text style={styles.threadModalKeystone}>
                  {threadState.keystone}
                </Text>
              )}
              
              {/* Micro-affirmation */}
              {threadState.micro_affirmation && (
                <Text style={styles.threadModalAffirmation}>
                  {threadState.micro_affirmation}
                </Text>
              )}
              
              {/* Reflect question */}
              {threadState.reflect_question && (
                <View style={styles.threadModalReflect}>
                  <Text style={styles.threadModalReflectLabel}>REFLECT</Text>
                  <Text style={styles.threadModalReflectQuestion}>
                    {threadState.reflect_question}
                  </Text>
                </View>
              )}
              
              {/* Remaining turns indicator */}
              <View style={styles.threadModalFooter}>
                <Text style={styles.threadModalFooterText}>
                  {threadState.remaining_turns} turn{threadState.remaining_turns !== 1 ? 's' : ''} remaining in this thread
                </Text>
              </View>
            </View>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>
    );
  };

  const canSend = inputText.trim().length > 0 && !isLoading && sessionId;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
    >
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>{headerTitle}</Text>
          <Text style={styles.headerSubtitle}>{headerSubtitle}</Text>
        </View>
        {lens && (
          <View style={styles.lensTag}>
            <Text style={styles.lensTagText}>
              {lens === 'human_design' ? 'Human Design' : lens.charAt(0).toUpperCase() + lens.slice(1)}
            </Text>
          </View>
        )}
        {onClose && (
          <TouchableOpacity onPress={onClose} style={styles.closeButton} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Ionicons name="close" size={22} color={Colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      {/* Thread Pill (only for generalist chat with active thread) */}
      {renderThreadPill()}

      {/* Memory Card (above messages) */}
      {renderMemoryCard()}

      {/* Thread Modal */}
      {renderThreadModal()}

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        contentContainerStyle={[
          styles.messagesContainer,
          { paddingBottom: 100 + insets.bottom }
        ]}
        showsVerticalScrollIndicator={false}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        ListFooterComponent={
          isLoading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Reflecting…</Text>
            </View>
          ) : null
        }
      />

      {/* Input Bar - NOT absolute positioned for proper touch handling */}
      <View style={[styles.inputBar, { paddingBottom: Math.max(insets.bottom, 12) }]}>
        {/* Transparency line (only in generalist Mirror Chat, not lens modals) */}
        {!lens && (
          <Text style={styles.transparencyLine}>
            Mirror reflects patterns from what you share. Nothing here predicts your future.
          </Text>
        )}
        <View style={styles.inputContainer}>
          <TextInput
            ref={inputRef}
            style={styles.input}
            value={inputText}
            onChangeText={(text) => {
              console.log('[MIRROR_INPUT_CHANGE]', text.length);
              setInputText(text);
            }}
            onFocus={() => console.log('[MIRROR_INPUT_FOCUS]')}
            onBlur={() => console.log('[MIRROR_INPUT_BLUR]')}
            onPressIn={() => console.log('[MIRROR_INPUT_PRESS_IN]')}
            placeholder={placeholder}
            placeholderTextColor={Colors.textTertiary}
            multiline
            maxLength={2000}
            editable={!isLoading}
            autoCorrect={true}
            blurOnSubmit={false}
            textAlignVertical="top"
            returnKeyType="default"
          />
          <TouchableOpacity
            style={[styles.sendButton, !canSend && styles.sendButtonDisabled]}
            onPress={handleSend}
            disabled={!canSend}
            activeOpacity={0.7}
          >
            <Ionicons 
              name="arrow-up" 
              size={18} 
              color={canSend ? Colors.surface : Colors.textTertiary} 
            />
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: Colors.background,
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    letterSpacing: -0.3,
  },
  headerSubtitle: {
    fontSize: 13,
    color: Colors.textTertiary,
    marginTop: 2,
    fontStyle: 'italic',
  },
  lensTag: {
    backgroundColor: Colors.surfaceLight,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 12,
  },
  lensTagText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.surfaceLight,
    justifyContent: 'center',
    alignItems: 'center',
  },

  // Memory Card
  memoryCard: {
    marginHorizontal: 16,
    marginBottom: 8,
    backgroundColor: '#FDFCFA',
    borderRadius: 14,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  memoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  memoryTitle: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textSecondary,
    letterSpacing: -0.2,
  },
  memoryContent: {
    paddingHorizontal: 14,
    paddingBottom: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  memorySection: {
    marginTop: 12,
  },
  memorySectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  memoryItem: {
    fontSize: 13,
    color: Colors.text,
    lineHeight: 19,
    marginBottom: 2,
  },
  stateContainer: {
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  stateLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
  stateValue: {
    fontStyle: 'italic',
    color: Colors.textSecondary,
  },
  detailsToggle: {
    marginTop: 12,
    paddingVertical: 4,
  },
  detailsToggleText: {
    fontSize: 12,
    color: Colors.accent,
    fontWeight: '500',
  },
  evidenceSection: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  evidenceLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
    opacity: 0.7,
  },
  evidenceItem: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    lineHeight: 17,
    marginBottom: 4,
    opacity: 0.8,
  },
  memoryFooter: {
    marginTop: 14,
    fontSize: 11,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    textAlign: 'center',
    opacity: 0.7,
  },

  // Thread Pill
  threadPill: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: Colors.surface,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    marginBottom: 8,
    gap: 6,
  },
  threadPillText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.text,
  },
  threadPillDate: {
    fontSize: 11,
    color: Colors.textTertiary,
  },

  // Thread Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  threadModalContent: {
    backgroundColor: Colors.background,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
    position: 'relative',
  },
  threadModalClose: {
    position: 'absolute',
    top: 12,
    right: 12,
    zIndex: 1,
    padding: 4,
  },
  threadModalTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    marginBottom: 16,
    marginRight: 30,
  },
  threadModalKeystone: {
    fontSize: 16,
    lineHeight: 26,
    color: Colors.text,
    marginBottom: 16,
  },
  threadModalAffirmation: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    marginBottom: 20,
  },
  threadModalReflect: {
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  threadModalReflectLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  threadModalReflectQuestion: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.text,
  },
  threadModalFooter: {
    marginTop: 20,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  threadModalFooterText: {
    fontSize: 11,
    color: Colors.textTertiary,
    textAlign: 'center',
    fontStyle: 'italic',
  },

  // Messages
  messagesContainer: {
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  messageWrapper: {
    marginBottom: 10,
    maxWidth: '82%',
  },
  userWrapper: {
    alignSelf: 'flex-end',
  },
  assistantWrapper: {
    alignSelf: 'flex-start',
  },
  firstMessage: {
    marginTop: 4,
  },
  messageBubble: {
    padding: 14,
    borderRadius: 18,
  },
  userBubble: {
    backgroundColor: Colors.text,
    borderBottomRightRadius: 6,
  },
  assistantBubble: {
    backgroundColor: '#FDFCFA',
    borderBottomLeftRadius: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
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
  timestamp: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 4,
    opacity: 0.7,
  },
  timestampLeft: {
    marginLeft: 4,
  },
  timestampRight: {
    marginRight: 4,
    textAlign: 'right',
  },

  // Loading
  loadingContainer: {
    paddingVertical: 12,
    paddingHorizontal: 4,
  },
  loadingText: {
    fontSize: 14,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    opacity: 0.8,
  },

  // Input Bar
  inputBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: Colors.background,
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: Colors.surface,
    borderRadius: 24,
    paddingLeft: 16,
    paddingRight: 6,
    paddingVertical: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  input: {
    flex: 1,
    fontSize: 15,
    color: Colors.text,
    maxHeight: 100,
    paddingVertical: 8,
    lineHeight: 20,
  },
  sendButton: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: Colors.text,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  sendButtonDisabled: {
    backgroundColor: Colors.border,
  },
  // Transparency line
  transparencyLine: {
    fontSize: 11,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 10,
    opacity: 0.6,
    fontStyle: 'italic',
  },
});
