import React, { useState, useRef, useEffect, useMemo } from 'react';
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
  Pressable,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';
import { storage, CHAT_SESSION_KEYS, useAppStore, ChatMessage } from '../store';

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

// ===== ISOLATION FLAG: Set to true to disable chat persistence and stop crash =====
const DISABLE_CHAT_PERSISTENCE = true;  // TEMPORARY: Toggle to isolate loop source

// Stable empty array to avoid new reference on each render
const EMPTY_MESSAGES: Message[] = [];

export default function MirrorChat({
  userId,
  lens = null,
  placeholder = "Say what's real right now…",
  headerTitle = "Mirror",
  headerSubtitle = "A mirror, not a verdict.",
  onClose,
  keystoneContext = null,
}: MirrorChatProps) {
  // ===== PERSISTENCE: Use Zustand store as single source of truth =====
  // Thread key for this chat context - stable primitive
  const threadKey = lens ? `mirror:${lens}` : 'mirror:home';
  const storageKey = userId ? `${userId}:${threadKey}` : null;
  
  // Get messages from store - use stable selector with null-safety and stable empty ref
  const storeMessages = useAppStore(s => {
    if (!storageKey) return EMPTY_MESSAGES;
    const msgs = s.chatMessages?.[storageKey];
    return msgs && msgs.length > 0 ? msgs : EMPTY_MESSAGES;
  });
  const loadChatMessages = useAppStore(s => s.loadChatMessages);
  const addChatMessage = useAppStore(s => s.addChatMessage);
  
  // ===== ISOLATION: Use local state if persistence disabled =====
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const messages = DISABLE_CHAT_PERSISTENCE ? localMessages : storeMessages;
  
  // Local UI state only (not persisted)
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
  
  // ===== DEBUG STATE for send instrumentation =====
  const [sendPressCount, setSendPressCount] = useState(0);
  const [lastSendAt, setLastSendAt] = useState<string>('');
  const [lastBailReason, setLastBailReason] = useState<string>('');
  const [lastFetchUrl, setLastFetchUrl] = useState<string>('');
  const [lastHttpStatus, setLastHttpStatus] = useState<string>('');
  const [lastError, setLastError] = useState<string>('');
  
  // ===== DEBUG STATE for focus instrumentation =====
  const [focusCount, setFocusCount] = useState(0);
  const [blurCount, setBlurCount] = useState(0);
  const [lastFocusAt, setLastFocusAt] = useState<string>('');
  const [lastBlurAt, setLastBlurAt] = useState<string>('');
  const [lastTouchAt, setLastTouchAt] = useState<string>('');
  
  // Get debug flag from URL params
  const searchParams = useLocalSearchParams<{ debug?: string }>();
  const isDebugMode = searchParams.debug === '1';
  
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const insets = useSafeAreaInsets();
  
  // ===== IDEMPOTENT HYDRATION REF - NEVER RESET =====
  const didInitRef = useRef(false);

  // Convert store messages to Message format with Date objects
  const displayMessages: Message[] = messages.map((m: any) => ({
    ...m,
    timestamp: typeof m.timestamp === 'string' ? new Date(m.timestamp) : m.timestamp,
  })) as Message[];

  // ===== HYDRATION: One-time initialization on mount =====
  useEffect(() => {
    if (!userId) return;
    if (didInitRef.current) return;
    didInitRef.current = true;
    
    console.log(`[MirrorChat] Initializing chat for ${threadKey}, persistence=${!DISABLE_CHAT_PERSISTENCE}`);
    
    if (DISABLE_CHAT_PERSISTENCE) {
      // Just add intro message locally
      const greeting = lens
        ? `I'm here to explore your ${lens === 'human_design' ? 'Human Design' : lens.charAt(0).toUpperCase() + lens.slice(1)} chart with you. What would you like to understand?`
        : "I'm here as a companion for self-understanding. Share what's on your mind, and I'll reflect what I notice.";
      
      setLocalMessages([{
        id: `intro_${Date.now()}`,
        role: 'assistant',
        content: greeting,
        timestamp: new Date(),
      }]);
      return;
    }
    
    (async () => {
      const loaded = await loadChatMessages(threadKey);
      
      // Update debug overlay
      (globalThis as any).__MIRROR_CHAT_KEY = `mirror_chat_messages:${userId}:${threadKey}`;
      (globalThis as any).__MIRROR_CHAT_COUNT = loaded?.length ?? 0;
      (globalThis as any).__MIRROR_THREAD_KEY = threadKey;
      
      console.log(`[MirrorChat] Loaded ${loaded?.length ?? 0} messages from storage`);
      
      // Seed intro ONCE if empty after load
      if (!loaded || loaded.length === 0) {
        const greeting = lens
          ? `I'm here to explore your ${lens === 'human_design' ? 'Human Design' : lens.charAt(0).toUpperCase() + lens.slice(1)} chart with you. What would you like to understand?`
          : "I'm here as a companion for self-understanding. Share what's on your mind, and I'll reflect what I notice.";
        
        await addChatMessage(threadKey, {
          id: `intro_${Date.now()}`,
          role: 'assistant',
          content: greeting,
          timestamp: new Date().toISOString(),
        });
        
        // Update debug count after adding intro
        (globalThis as any).__MIRROR_CHAT_COUNT = 1;
        console.log(`[MirrorChat] Seeded intro message for ${threadKey}`);
      }
    })();
  }, [userId]); // ONLY depends on userId - threadKey is derived from props

  // ===== DEBUG: Update overlay with chat count on message changes =====
  useEffect(() => {
    if (userId && threadKey) {
      (globalThis as any).__MIRROR_CHAT_KEY = `mirror_chat_messages:${userId}:${threadKey}`;
      (globalThis as any).__MIRROR_CHAT_COUNT = messages.length;
      (globalThis as any).__MIRROR_THREAD_KEY = threadKey;
    }
  }, [userId, threadKey, messages.length]);

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

  // ===== KEYSTONE CONTINUATION AUTO-TRIGGER =====
  // When keystoneContext is provided, automatically send continuation message
  const didTriggerKeystoneRef = useRef(false);
  
  useEffect(() => {
    async function triggerKeystoneContinuation() {
      if (!keystoneContext || !sessionId || hasTriggeredKeystone || isLoading) return;
      if (didTriggerKeystoneRef.current) return;
      
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
      
      didTriggerKeystoneRef.current = true;
      console.log('[MirrorChat] Triggering keystone continuation for date:', keystoneContext.date);
      setHasTriggeredKeystone(true);
      setIsLoading(true);
      
      // Add a user message indicating continuation - use store
      const userMessage: ChatMessage = {
        id: `user-keystone-${Date.now()}`,
        role: 'user',
        content: "Continue from today's reflection…",
        timestamp: new Date().toISOString(),
      };
      await addChatMessage(threadKey, userMessage);
      
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
        
        const assistantMessage: ChatMessage = {
          id: `assistant-keystone-${Date.now()}`,
          role: 'assistant',
          content: response.data.response,
          timestamp: response.data.timestamp || new Date().toISOString(),
        };
        
        await addChatMessage(threadKey, assistantMessage);
        
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
        const fallbackMessage: ChatMessage = {
          id: `assistant-fallback-${Date.now()}`,
          role: 'assistant',
          content: "I'm here with you. What's present right now?",
          timestamp: new Date().toISOString(),
        };
        await addChatMessage(threadKey, fallbackMessage);
      } finally {
        setIsLoading(false);
      }
    }
    
    if (keystoneContext && sessionId && !isLoadingSession && !hasTriggeredKeystone) {
      triggerKeystoneContinuation();
    }
  }, [keystoneContext, sessionId, isLoadingSession, hasTriggeredKeystone, userId, threadKey]);

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

  // ===== BULLETPROOF SEND HANDLER =====
  const handleSendPress = () => {
    // Always increment press count and timestamp
    setSendPressCount(prev => prev + 1);
    setLastSendAt(new Date().toISOString());
    console.log(`[MirrorChat] SEND PRESS #${sendPressCount + 1} at ${new Date().toISOString()}`);
    
    // Call the actual send logic
    handleSend();
  };

  const handleSend = async () => {
    // Clear previous debug state
    setLastBailReason('');
    setLastFetchUrl('');
    setLastHttpStatus('');
    setLastError('');
    
    // Bail checks with reason tracking
    if (!userId) {
      setLastBailReason('no_userId');
      console.log('[MirrorChat] BAIL: no_userId');
      return;
    }
    if (!inputText.trim()) {
      setLastBailReason('empty_input');
      console.log('[MirrorChat] BAIL: empty_input');
      return;
    }
    if (isLoading) {
      setLastBailReason('already_sending');
      console.log('[MirrorChat] BAIL: already_sending');
      return;
    }
    if (!sessionId) {
      setLastBailReason('no_sessionId');
      console.log('[MirrorChat] BAIL: no_sessionId');
      return;
    }

    const messageContent = inputText.trim();
    
    // Optimistic UI: Add user message immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageContent,
      timestamp: new Date().toISOString(),
    };

    // Handle message addition based on persistence mode
    if (DISABLE_CHAT_PERSISTENCE) {
      setLocalMessages(prev => [...prev, userMessage as any]);
    } else {
      await addChatMessage(threadKey, userMessage);
    }
    
    setInputText('');
    setIsLoading(true);
    Keyboard.dismiss();

    // Build the fetch URL - use api client's base
    const fetchUrl = '/mirror/chat';
    setLastFetchUrl(fetchUrl);
    console.log(`[MirrorChat] Calling API: ${fetchUrl}`);

    // AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 15000); // 15 second timeout

    try {
      const response = await api.post(fetchUrl, {
        user_id: userId,
        message: messageContent,
        lens: lens,
        session_id: sessionId,
        include_journal: true,
        include_history: true,
      }, {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      
      // Capture HTTP status
      setLastHttpStatus('200');
      console.log('[MirrorChat] API response OK');

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp || new Date().toISOString(),
      };

      // Handle message addition based on persistence mode
      if (DISABLE_CHAT_PERSISTENCE) {
        setLocalMessages(prev => [...prev, assistantMessage as any]);
      } else {
        await addChatMessage(threadKey, assistantMessage);
      }
      
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
      
      console.log(`[MirrorChat] Message sent successfully, total messages: ${displayMessages.length + 2}`);
    } catch (error: any) {
      clearTimeout(timeoutId);
      
      // Capture error details
      if (error.name === 'AbortError' || error.code === 'ECONNABORTED') {
        setLastError('timeout_15s');
        console.error('[MirrorChat] Request timeout');
      } else if (error.response) {
        // HTTP error response
        setLastHttpStatus(String(error.response.status));
        const errorText = typeof error.response.data === 'string' 
          ? error.response.data.substring(0, 300)
          : JSON.stringify(error.response.data).substring(0, 300);
        setLastError(`HTTP ${error.response.status}: ${errorText}`);
        console.error(`[MirrorChat] HTTP Error ${error.response.status}:`, errorText);
      } else if (error.request) {
        // Network error
        setLastError('network_error');
        console.error('[MirrorChat] Network error:', error.message);
      } else {
        setLastError(error.message?.substring(0, 300) || 'unknown_error');
        console.error('[MirrorChat] Unknown error:', error);
      }
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: "I'm having trouble connecting right now. Please try again in a moment.",
        timestamp: new Date().toISOString(),
      };
      
      if (DISABLE_CHAT_PERSISTENCE) {
        setLocalMessages(prev => [...prev, errorMessage as any]);
      } else {
        await addChatMessage(threadKey, errorMessage);
      }
    } finally {
      // ALWAYS reset loading state
      setIsLoading(false);
      console.log('[MirrorChat] isLoading reset to false');
    }
  };

  const renderMessage = ({ item, index }: { item: Message; index: number }) => {
    // Use shared role normalizer - unknown roles default to 'assistant'
    const rawRole = String(item?.role ?? '').toLowerCase();
    const role = rawRole.includes('user') ? 'user' 
      : rawRole.includes('system') ? 'system' 
      : 'assistant'; // default
    
    const isUser = role === 'user';
    const isFirstMessage = index === 0;
    
    // Get styles based on normalized role
    const getBubbleStyle = () => {
      if (role === 'user') return styles.userBubble;
      if (role === 'system') return styles.systemBubble;
      return styles.assistantBubble;
    };
    
    const getTextStyle = () => {
      if (role === 'user') return styles.userText;
      if (role === 'system') return styles.systemText;
      return styles.assistantText;
    };
    
    return (
      <View style={[
        styles.messageWrapper,
        isUser ? styles.userWrapper : styles.assistantWrapper,
        isFirstMessage && styles.firstMessage,
      ]}>
        <View style={[styles.messageBubble, getBubbleStyle()]}>
          <Text style={[styles.messageText, getTextStyle()]}>
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
  
  // Debug: log canSend status
  console.log(`[MirrorChat] canSend=${canSend}: text="${inputText.trim().substring(0, 20)}", loading=${isLoading}, session=${!!sessionId}`);

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
        data={displayMessages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        contentContainerStyle={[
          styles.messagesContainer,
          { paddingBottom: 100 + insets.bottom }
        ]}
        showsVerticalScrollIndicator={false}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        keyboardShouldPersistTaps="always"
        keyboardDismissMode="on-drag"
        ListFooterComponent={
          isLoading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Reflecting…</Text>
            </View>
          ) : null
        }
      />

      {/* Input Bar */}
      <View style={[styles.inputBar, { paddingBottom: Math.max(insets.bottom, 12) }]}>
        {/* Debug display (only when ?debug=1) */}
        {isDebugMode && (
          <View style={styles.debugDisplay}>
            <Text style={styles.debugText}>
              SEND_PRESS={sendPressCount} | bail={lastBailReason || 'none'} | url={lastFetchUrl || 'none'} | http={lastHttpStatus || 'none'} | err={lastError || 'none'}
            </Text>
          </View>
        )}
        {/* Transparency line (only in generalist Mirror Chat, not lens modals) */}
        {!lens && (
          <Text style={styles.transparencyLine}>
            Mirror reflects patterns from what you share. Nothing here predicts your future.
          </Text>
        )}
        <View style={[styles.inputContainer, { pointerEvents: 'auto', zIndex: 99999, position: 'relative' }]}>
          <TextInput
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder={placeholder}
            placeholderTextColor={Colors.textTertiary}
            multiline
            maxLength={2000}
            editable={!isLoading}
            returnKeyType="send"
            blurOnSubmit={false}
            onSubmitEditing={() => {
              if (canSend) {
                handleSendPress();
              }
            }}
          />
          <Pressable
            style={[styles.sendButton, !canSend && styles.sendButtonDisabled, { pointerEvents: 'auto', zIndex: 100000 }]}
            onPress={handleSendPress}
            onPressIn={() => console.log('[MirrorChat] onPressIn send button')}
            disabled={!canSend}
          >
            <Ionicons 
              name="arrow-up" 
              size={18} 
              color={canSend ? Colors.surface : Colors.textTertiary} 
            />
          </Pressable>
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
  
  // Screen Banner
  screenBanner: {
    backgroundColor: '#990099',
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  screenName: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center',
  },
  screenSubtext: {
    color: '#fff',
    fontSize: 9,
    textAlign: 'center',
    opacity: 0.8,
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
  // User bubble: white/light background with dark text
  userBubble: {
    backgroundColor: 'rgba(255,255,255,0.92)',
    borderBottomRightRadius: 6,
  },
  // Assistant bubble: dark translucent background with light text
  assistantBubble: {
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderColor: 'rgba(255,255,255,0.10)',
    borderWidth: 1,
    borderBottomLeftRadius: 6,
  },
  // System bubble: similar to assistant but slightly dimmer
  systemBubble: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderColor: 'rgba(255,255,255,0.08)',
    borderWidth: 1,
    borderBottomLeftRadius: 6,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  // User text: dark on light background
  userText: {
    color: 'rgba(0,0,0,0.88)',
  },
  // Assistant text: light on dark background  
  assistantText: {
    color: 'rgba(255,255,255,0.92)',
  },
  // System text: slightly dimmer light on dark background
  systemText: {
    color: 'rgba(255,255,255,0.85)',
  },
  timestamp: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.45)',
    marginTop: 4,
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
  
  // Debug display
  debugDisplay: {
    backgroundColor: '#1a1a2e',
    paddingVertical: 6,
    paddingHorizontal: 8,
    marginBottom: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#3a3a5e',
  },
  debugText: {
    fontSize: 9,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#4ade80',
    lineHeight: 12,
  },
});
