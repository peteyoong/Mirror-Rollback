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
  TouchableWithoutFeedback,
  InputAccessoryView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useLocalSearchParams } from 'expo-router';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import api, { getApiBaseUrl } from '../services/api';
import { useAppStore, ChatMessage, storage, CHAT_SESSION_KEYS } from '../store';
import { loadMessages, saveMessages, DEFAULT_THREAD_KEY } from '../utils/chatPersistence';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

// Unique ID for InputAccessoryView
const INPUT_ACCESSORY_VIEW_ID = 'mirror-chat-input-accessory';

// ===== API CALL HELPER WITH RETRY =====
interface ApiCallResult {
  ok: boolean;
  status: number | null;
  text: string | null;
  json: any | null;
  err: string | null;
  attempts: number;
}

const RETRY_DELAYS = [800, 2000]; // Increased delays for lens chat which can be slow
const RETRYABLE_STATUSES = [0, 502, 503, 504];
const REQUEST_TIMEOUT = 45000; // 45 seconds for lens chat which uses more context

async function callMirrorChatApi(
  payload: any,
  signal?: AbortSignal
): Promise<ApiCallResult> {
  let attempts = 0;
  let lastError: string | null = null;
  let lastStatus: number | null = null;
  let lastText: string | null = null;
  
  const maxAttempts = RETRY_DELAYS.length + 1;
  
  while (attempts < maxAttempts) {
    attempts++;
    
    try {
      const response = await api.post('/mirror/chat', payload, { signal });
      
      // Success
      return {
        ok: true,
        status: response.status || 200,
        text: null,
        json: response.data,
        err: null,
        attempts,
      };
    } catch (error: any) {
      // Determine if retryable
      const status = error.response?.status || 0;
      lastStatus = status;
      lastError = error.message || 'Unknown error';
      
      // Try to get response text
      if (error.response?.data) {
        lastText = typeof error.response.data === 'string'
          ? error.response.data.substring(0, 300)
          : JSON.stringify(error.response.data).substring(0, 300);
      }
      
      // Check if timeout or abort
      const isTimeout = error.name === 'AbortError' || 
        error.code === 'ECONNABORTED' || 
        signal?.aborted ||
        error.message?.toLowerCase().includes('timeout');
      
      // Check if retryable (including timeouts)
      const isRetryable = isTimeout ||
        RETRYABLE_STATUSES.includes(status) || 
        error.code === 'ECONNREFUSED' ||
        error.message?.includes('Network Error');
      
      if (isRetryable && attempts < maxAttempts) {
        const delay = RETRY_DELAYS[attempts - 1];
        console.log(`[MirrorChat] Retry ${attempts}/${maxAttempts} after ${delay}ms (status=${status}, timeout=${isTimeout})`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      
      // Non-retryable error or max retries reached
      if (isTimeout) {
        return {
          ok: false,
          status: null,
          text: null,
          json: null,
          err: 'Request timed out. Tap to retry.',
          attempts,
        };
      }
      
      return {
        ok: false,
        status: lastStatus,
        text: lastText,
        json: null,
        err: lastError,
        attempts,
      };
    }
  }
  
  // Should not reach here
  return {
    ok: false,
    status: lastStatus,
    text: lastText,
    json: null,
    err: lastError || 'Max retries exceeded',
    attempts,
  };
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

// ===== CONTEXT VALIDATION HELPER =====
// Evaluates context_bundle to determine what data is available
interface ContextEvaluation {
  hasContext: boolean;
  contextBytes: number;
  lenses: {
    astrology: boolean;
    human_design: boolean;
    numerology: boolean;
    enneagram: boolean;
  };
  astro: {
    planets: boolean;
    nodes: boolean;
    houses: boolean;
  };
  profile: {
    name: boolean;
    birth: boolean;
  };
}

function evaluateContextBundle(context: any): ContextEvaluation {
  const empty: ContextEvaluation = {
    hasContext: false,
    contextBytes: 0,
    lenses: {
      astrology: false,
      human_design: false,
      numerology: false,
      enneagram: false,
    },
    astro: {
      planets: false,
      nodes: false,
      houses: false,
    },
    profile: {
      name: false,
      birth: false,
    },
  };

  if (!context) return empty;

  const lenses = context.lenses || {};
  const astrology = lenses.astrology || {};
  const humanDesign = lenses.human_design || {};
  const numerology = lenses.numerology || {};
  const enneagram = lenses.enneagram || {};
  const profile = context.profile || {};

  // Check for planets (any of the major planets)
  const planetKeys = ['sun', 'moon', 'ascendant', 'rising', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto'];
  const hasPlanets = planetKeys.some(k => astrology[k]?.sign || astrology[k]?.formatted);

  // Check for nodes
  const hasNodes = !!(astrology.north_node?.sign && astrology.south_node?.sign);

  // Check for houses (house placements on planets or explicit houses object)
  const hasHouses = !!(
    astrology.houses || 
    astrology.rising?.sign || 
    astrology.sun?.house || 
    astrology.moon?.house
  );

  // Check profile
  const hasName = !!profile.name;
  const hasBirth = !!(
    profile.birth_date || 
    profile.birth?.date || 
    (profile.birth_place && profile.birth_time) ||
    (profile.birth?.place && profile.birth?.time)
  );

  return {
    hasContext: true,
    contextBytes: JSON.stringify(context).length,
    lenses: {
      astrology: !!astrology.computed || hasPlanets,
      human_design: !!humanDesign.computed || !!humanDesign.type,
      numerology: !!numerology.computed || !!numerology.life_path,
      enneagram: !!enneagram.computed || !!enneagram.core_type,
    },
    astro: {
      planets: hasPlanets,
      nodes: hasNodes,
      houses: hasHouses,
    },
    profile: {
      name: hasName,
      birth: hasBirth,
    },
  };
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
  // Thread key for this chat context
  // Use DEFAULT_THREAD_KEY for main Mirror chat, lens-specific for lens chats
  const threadKey = lens ? `mirror:${lens}` : DEFAULT_THREAD_KEY;
  
  // Local state for messages - persisted via chatPersistence helpers
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const messagesRef = useRef<ChatMessage[]>([]);
  
  // Keep ref in sync with state for comparison in hydration
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);
  
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
  
  // ===== DEBUG STATE for API calls (only shown when ?debug=1) =====
  const [debugInfo, setDebugInfo] = useState<{
    lastRequestId: string | null;
    lastUrl: string | null;
    lastStatus: number | null;
    lastErr: string | null;
    lastResponseSnippet: string | null;
    lastAttemptCount: number;
    apiBaseUrl: string | null;
  }>({
    lastRequestId: null,
    lastUrl: null,
    lastStatus: null,
    lastErr: null,
    lastResponseSnippet: null,
    lastAttemptCount: 0,
    apiBaseUrl: null,
  });
  
  // ===== RETRY BANNER STATE (PART A - visible failures) =====
  // Store the last payload so we can retry on tap
  const [lastPayload, setLastPayload] = useState<any | null>(null);
  const [showRetryBanner, setShowRetryBanner] = useState(false);
  const [retryBannerMessage, setRetryBannerMessage] = useState<string>('');
  
  // Ephemeral error message (not persisted) - legacy, kept for compatibility
  const [ephemeralError, setEphemeralError] = useState<string | null>(null);
  
  // ===== USER CONTEXT STATE (lenses + journal + timeline) =====
  const [contextBundle, setContextBundle] = useState<any | null>(null);
  const [isLoadingContext, setIsLoadingContext] = useState(false);
  const [contextError, setContextError] = useState<string | null>(null);
  const contextFetchedRef = useRef(false);
  
  // ===== CONTEXT DEBUG STATE =====
  const [contextDebug, setContextDebug] = useState<ContextEvaluation | null>(null);
  
  // ===== DEBUG MODE: Web + Native Support =====
  // Web: ?debug=1 query param or EXPO_PUBLIC_DEBUG_MIRROR env
  // Native: Tap "Mirror" title 7 times within 2 seconds
  const searchParams = useLocalSearchParams<{ debug?: string }>();
  const [debugEnabled, setDebugEnabled] = useState(false);
  const [debugTapCount, setDebugTapCount] = useState(0);
  const debugTapTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Handle title tap for native debug mode
  const handleTitlePress = () => {
    // Increment tap count
    const newCount = debugTapCount + 1;
    setDebugTapCount(newCount);
    
    // Clear existing timeout
    if (debugTapTimeoutRef.current) {
      clearTimeout(debugTapTimeoutRef.current);
    }
    
    // Check if we hit 7 taps
    if (newCount >= 7) {
      setDebugEnabled(true);
      setDebugTapCount(0);
      console.log('[MirrorChat] Debug mode enabled via tap gesture');
    } else {
      // Reset count after 2 seconds of inactivity
      debugTapTimeoutRef.current = setTimeout(() => {
        setDebugTapCount(0);
      }, 2000);
    }
  };
  
  // Compute isDebugMode from multiple sources (no window.location.search)
  const isDebugMode = useMemo(() => {
    // 1. Native tap gesture enabled
    if (debugEnabled) return true;
    // 2. URL param via expo-router
    if (searchParams.debug === '1') return true;
    // 3. Environment variable
    if (process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true') return true;
    return false;
  }, [debugEnabled, searchParams.debug]);
  
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const insets = useSafeAreaInsets();
  
  // ===== FETCH USER CONTEXT ON MOUNT =====
  useEffect(() => {
    if (!userId || contextFetchedRef.current) return;
    
    const fetchContext = async () => {
      setIsLoadingContext(true);
      setContextError(null);
      
      // Retry up to 2 times with backoff
      const retries = [0, 500, 1500];
      
      for (let i = 0; i < retries.length; i++) {
        if (i > 0) {
          await new Promise(r => setTimeout(r, retries[i]));
        }
        
        try {
          const response = await api.get(`/mirror/context/${userId}`);
          if (response.data) {
            console.log('[MirrorChat] Context loaded:', Object.keys(response.data.lenses || {}).filter(k => response.data.lenses[k]?.computed).join(', '));
            setContextBundle(response.data);
            
            // Evaluate and set debug info
            const evaluated = evaluateContextBundle(response.data);
            setContextDebug(evaluated);
            console.log('[MirrorChat] Context evaluated:', JSON.stringify(evaluated));
            
            contextFetchedRef.current = true;
            setIsLoadingContext(false);
            return;
          }
        } catch (error: any) {
          console.error(`[MirrorChat] Context fetch attempt ${i + 1} failed:`, error.message);
          if (i === retries.length - 1) {
            setContextError('Unable to load your profile data. Chat may not have full context.');
            // Set empty context debug
            setContextDebug(evaluateContextBundle(null));
          }
        }
      }
      
      setIsLoadingContext(false);
    };
    
    fetchContext();
  }, [userId]);
  
  // ===== HYDRATION: Load messages on mount and when userId changes =====
  const [isHydrated, setIsHydrated] = useState(false);
  
  useEffect(() => {
    let alive = true;
    
    const hydrate = async () => {
      if (!userId) return;
      
      try {
        const loaded = await loadMessages(userId, threadKey);
        if (!alive) return;
        
        // Only update state if we have messages to load
        if (loaded.length > 0) {
          console.log(`[MirrorChat] Hydrating ${loaded.length} messages for ${threadKey}`);
          setMessages(loaded);
        }
        
        setIsHydrated(true);
      } catch (e) {
        console.error('[MirrorChat] Hydration error:', e);
        setIsHydrated(true);
      }
    };
    
    hydrate();
    
    return () => {
      alive = false;
    };
  }, [userId, threadKey]);

  // Convert messages to display format with Date objects
  const displayMessages: Message[] = messages.map((m: any) => ({
    ...m,
    timestamp: typeof m.timestamp === 'string' ? new Date(m.timestamp) : m.timestamp,
  })) as Message[];

  // ===== INTRO MESSAGE: Seed if no messages loaded =====
  useEffect(() => {
    if (!userId || !isHydrated) return;
    
    // Only seed intro if we've hydrated and have no messages
    if (messages.length === 0) {
      const greeting = lens
        ? `I'm here to explore your ${lens === 'human_design' ? 'Human Design' : lens.charAt(0).toUpperCase() + lens.slice(1)} chart with you. What would you like to understand?`
        : "I'm here as a companion for self-understanding. Share what's on your mind, and I'll reflect what I notice.";
      
      const introMessage: ChatMessage = {
        id: `intro_${Date.now()}`,
        role: 'assistant',
        content: greeting,
        timestamp: new Date().toISOString(),
      };
      
      setMessages([introMessage]);
      saveMessages(userId, threadKey, [introMessage]);
      console.log(`[MirrorChat] Seeded intro message for ${threadKey}`);
    }
  }, [userId, threadKey, isHydrated, messages.length]);

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
        const lastFollowupDate = localStorage?.getItem(KEYSTONE_FOLLOWUP_KEY);
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
      
      // Add a user message indicating continuation
      const userMessage: ChatMessage = {
        id: `user-keystone-${Date.now()}`,
        role: 'user',
        content: "Continue from today's reflection…",
        timestamp: new Date().toISOString(),
      };
      const messagesWithUser = [...messages, userMessage];
      setMessages(messagesWithUser);
      await saveMessages(userId!, threadKey, messagesWithUser);
      
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
        
        const messagesWithAssistant = [...messagesWithUser, assistantMessage];
        setMessages(messagesWithAssistant);
        await saveMessages(userId!, threadKey, messagesWithAssistant);
        
        if (response.data.memory_update) {
          setMemoryUpdate(response.data.memory_update);
        }
        
        // Capture thread state from keystone continuation
        if (response.data.thread) {
          setThreadState(response.data.thread);
        }
        
        // Mark this date as followed up
        try {
          localStorage?.setItem(KEYSTONE_FOLLOWUP_KEY, keystoneContext.date);
        } catch (e) {}
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
        const messagesWithFallback = [...messagesWithUser, fallbackMessage];
        setMessages(messagesWithFallback);
        await saveMessages(userId!, threadKey, messagesWithFallback);
      } finally {
        setIsLoading(false);
      }
    }
    
    if (keystoneContext && sessionId && !isLoadingSession && !hasTriggeredKeystone) {
      triggerKeystoneContinuation();
    }
  }, [keystoneContext, sessionId, isLoadingSession, hasTriggeredKeystone, userId, threadKey, messages]);

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

  // ===== SEND HANDLER =====
  const handleSend = async () => {
    // Bail checks
    if (!userId || !inputText.trim() || isLoading || !sessionId) {
      return;
    }

    const messageContent = inputText.trim();
    const requestId = `req_${Date.now()}`;
    
    // Clear ephemeral error
    setEphemeralError(null);
    
    // Update debug info at start
    setDebugInfo(prev => ({
      ...prev,
      lastRequestId: requestId,
      lastUrl: '/mirror/chat',
      lastStatus: null,
      lastErr: null,
      lastResponseSnippet: null,
      lastAttemptCount: 0,
    }));
    
    // Optimistic UI: Add user message immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageContent,
      timestamp: new Date().toISOString(),
    };

    // Add to local state
    const messagesWithUser = [...messages, userMessage];
    setMessages(messagesWithUser);
    
    // Save to storage immediately (user message only)
    await saveMessages(userId, threadKey, messagesWithUser);
    
    setInputText('');
    setIsLoading(true);
    Keyboard.dismiss();

    // AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, REQUEST_TIMEOUT);

    try {
      const result = await callMirrorChatApi({
        user_id: userId,
        message: messageContent,
        lens: lens,
        session_id: sessionId,
        thread_key: threadKey,
        include_journal: true,
        include_history: true,
        context_bundle: contextBundle, // Pass full user context (lenses + journal + timeline)
      }, controller.signal);

      clearTimeout(timeoutId);
      
      // Update debug info with result
      setDebugInfo(prev => ({
        ...prev,
        lastStatus: result.status,
        lastErr: result.err,
        lastResponseSnippet: result.text || (result.json ? JSON.stringify(result.json).substring(0, 100) : null),
        lastAttemptCount: result.attempts,
      }));

      if (result.ok && result.json) {
        // SUCCESS - create and persist assistant message
        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: result.json.response,
          timestamp: result.json.timestamp || new Date().toISOString(),
        };

        // Add assistant message to local state
        const messagesWithAssistant = [...messagesWithUser, assistantMessage];
        setMessages(messagesWithAssistant);
        
        // Save to storage (including successful response)
        await saveMessages(userId, threadKey, messagesWithAssistant);
        
        setSessionId(result.json.session_id);
        
        // Store memory update if present
        if (result.json.memory_update) {
          setMemoryUpdate(result.json.memory_update);
        }
        
        // Update thread state from response (only for generalist chat)
        if (!lens && result.json.thread) {
          setThreadState(result.json.thread);
        } else if (!lens && !result.json.thread) {
          setThreadState(null);
        }
      } else {
        // FAILURE - show ephemeral error, do NOT persist
        const errorDetail = result.err || `HTTP ${result.status}`;
        console.error(`[MirrorChat] Send failed after ${result.attempts} attempts: ${errorDetail}`);
        
        // Set ephemeral error (shown in UI but not persisted)
        setEphemeralError(
          result.status 
            ? `Request failed (HTTP ${result.status}) after ${result.attempts} attempt(s)`
            : `Request failed: ${result.err || 'Unknown error'}`
        );
        
        // Do NOT add error message to messages array or save to storage
        // The user can try again
      }
    } catch (error: any) {
      clearTimeout(timeoutId);
      console.error('[MirrorChat] Unexpected send error:', error.message);
      
      setDebugInfo(prev => ({
        ...prev,
        lastErr: error.message,
        lastStatus: null,
      }));
      
      setEphemeralError('Unexpected error. Please try again.');
    } finally {
      // ALWAYS reset loading state
      setIsLoading(false);
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

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
    >
      {/* Header */}
      <View style={styles.header}>
        <Pressable style={styles.headerContent} onPress={handleTitlePress}>
          <Text style={styles.headerTitle}>
            {headerTitle}
            {debugTapCount > 0 && debugTapCount < 7 && (
              <Text style={styles.debugTapIndicator}> ({debugTapCount}/7)</Text>
            )}
          </Text>
          <Text style={styles.headerSubtitle}>{headerSubtitle}</Text>
        </Pressable>
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

      {/* Messages - wrapped in TouchableWithoutFeedback for keyboard dismiss */}
      <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
        <View style={{ flex: 1 }}>
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
            keyboardShouldPersistTaps="handled"
            keyboardDismissMode="on-drag"
            ListFooterComponent={
              isLoading ? (
                <View style={styles.loadingContainer}>
                  <Text style={styles.loadingText}>Reflecting…</Text>
                </View>
              ) : null
            }
          />
        </View>
      </TouchableWithoutFeedback>

      {/* Input Bar */}
      <View style={[styles.inputBar, { paddingBottom: Math.max(insets.bottom, 12) }]}>
        {/* Context Debug Panel (only when debug mode enabled) */}
        {isDebugMode && contextDebug && (
          <View style={styles.contextDebugPanel}>
            <Text style={styles.contextDebugTitle}>CONTEXT DEBUG</Text>
            <Text style={styles.contextDebugText}>
              LENSES: astrology={String(contextDebug.lenses.astrology)} | human_design={String(contextDebug.lenses.human_design)} | numerology={String(contextDebug.lenses.numerology)} | enneagram={String(contextDebug.lenses.enneagram)}
            </Text>
            <Text style={styles.contextDebugText}>
              ASTRO: planets={String(contextDebug.astro.planets)} | nodes={String(contextDebug.astro.nodes)} | houses={String(contextDebug.astro.houses)}
            </Text>
            <Text style={styles.contextDebugText}>
              PROFILE: name={String(contextDebug.profile.name)} | birth={String(contextDebug.profile.birth)}
            </Text>
            <Text style={styles.contextDebugText}>
              has_context={String(contextDebug.hasContext)} | context_bytes={contextDebug.contextBytes}
            </Text>
          </View>
        )}
        
        {/* Context Warning - Partial Astrology (nodes missing but planets exist) */}
        {contextDebug?.hasContext &&
         contextDebug?.astro?.planets &&
         !contextDebug?.astro?.nodes && (
          <View style={styles.contextWarningBanner}>
            <Ionicons name="alert-circle-outline" size={14} color="#ffaa00" />
            <Text style={styles.contextWarningText}>
              Astrology context partial — lunar nodes missing.
            </Text>
          </View>
        )}
        
        {/* API Debug panel (only when debug mode enabled) */}
        {isDebugMode && (
          <View style={styles.debugPanel}>
            <Text style={styles.debugTitle}>API Debug</Text>
            <Text style={styles.debugText}>
              req: {debugInfo.lastRequestId || 'none'}{'\n'}
              url: {debugInfo.lastUrl || 'none'}{'\n'}
              status: {debugInfo.lastStatus ?? 'pending'}{'\n'}
              attempts: {debugInfo.lastAttemptCount}{'\n'}
              err: {debugInfo.lastErr || 'none'}{'\n'}
              resp: {debugInfo.lastResponseSnippet || 'none'}
            </Text>
          </View>
        )}
        
        {/* Ephemeral error banner (not persisted) */}
        {ephemeralError && (
          <View style={styles.errorBanner}>
            <Ionicons name="alert-circle" size={16} color="#fff" />
            <Text style={styles.errorBannerText}>{ephemeralError}</Text>
            <Pressable onPress={() => setEphemeralError(null)} hitSlop={8}>
              <Ionicons name="close" size={16} color="#fff" />
            </Pressable>
          </View>
        )}
        
        {/* Transparency line (only in generalist Mirror Chat, not lens modals) */}
        {!lens && (
          <Text style={styles.transparencyLine}>
            Mirror reflects patterns from what you share. Nothing here predicts your future.
          </Text>
        )}
        {/* Input container with tap-to-focus wrapper for iOS */}
        <Pressable
          onPress={() => inputRef.current?.focus()}
          style={styles.inputContainer}
        >
          <TextInput
            ref={inputRef}
            style={styles.input}
            value={inputText}
            onChangeText={setInputText}
            placeholder={placeholder}
            placeholderTextColor={Colors.textTertiary}
            multiline
            maxLength={2000}
            editable={!isLoading}
            returnKeyType="done"
            blurOnSubmit={true}
            showSoftInputOnFocus={true}
            autoCorrect={false}
            inputAccessoryViewID={Platform.OS === 'ios' ? INPUT_ACCESSORY_VIEW_ID : undefined}
            onSubmitEditing={() => {
              if (canSend) {
                handleSend();
              } else {
                Keyboard.dismiss();
              }
            }}
          />
          <Pressable
            style={[styles.sendButton, !canSend && styles.sendButtonDisabled]}
            onPress={handleSend}
            disabled={!canSend}
          >
            <Ionicons 
              name="arrow-up" 
              size={18} 
              color={canSend ? Colors.surface : Colors.textTertiary} 
            />
          </Pressable>
        </Pressable>
      </View>
      
      {/* iOS Input Accessory View with "Done" button */}
      {Platform.OS === 'ios' && (
        <InputAccessoryView nativeID={INPUT_ACCESSORY_VIEW_ID}>
          <View style={styles.inputAccessoryBar}>
            <TouchableOpacity
              style={styles.doneButton}
              onPress={() => Keyboard.dismiss()}
            >
              <Text style={styles.doneButtonText}>Done</Text>
            </TouchableOpacity>
          </View>
        </InputAccessoryView>
      )}
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
  debugTapIndicator: {
    fontSize: 12,
    fontWeight: '400',
    color: Colors.textTertiary,
    opacity: 0.6,
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
  
  // iOS Input Accessory View
  inputAccessoryBar: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  doneButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  doneButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.accent,
  },
  
  // Debug panel (only shown when ?debug=1)
  debugPanel: {
    backgroundColor: '#1a1a2e',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#3a3a5e',
  },
  debugTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#4ade80',
    marginBottom: 6,
  },
  debugText: {
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#888',
    lineHeight: 14,
  },
  
  // Context Debug Panel (only shown when ?debug=1)
  contextDebugPanel: {
    backgroundColor: '#111',
    padding: 8,
    borderRadius: 6,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#333',
  },
  contextDebugTitle: {
    fontSize: 10,
    fontWeight: '700',
    color: '#0f0',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  contextDebugText: {
    fontSize: 10,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#0f0',
    lineHeight: 14,
  },
  
  // Context Warning Banner (partial context)
  contextWarningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#442200',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 6,
    marginBottom: 8,
    gap: 6,
  },
  contextWarningText: {
    flex: 1,
    fontSize: 12,
    color: '#ffaa00',
  },
  
  // Error banner (ephemeral, not persisted)
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#dc2626',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: 10,
    gap: 8,
  },
  errorBannerText: {
    flex: 1,
    fontSize: 12,
    color: '#fff',
  },
});
