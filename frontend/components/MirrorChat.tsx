import React, { useState, useRef, useEffect, useCallback } from 'react';
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
  Animated,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import api, { createMirrorInsight } from '../services/api';
import { storage, CHAT_SESSION_KEYS } from '../store';
import MirrorLeaderCard from './journal/MirrorLeaderCard';
import { useDominantTruthForChat } from '../hooks/useDominantTruth';
import { buildMirrorResponse, getAskMirrorContext, getAskMirrorOpener } from '../services/mirrorResponseEngine';
// Action Tracking for Engagement Adaptation
import { trackChatEnter, trackChatSend, trackChatClose } from '../services/actionTracking';
// evidence-drawer-v2 — curated "Why this is showing up" drawer
import EvidenceDrawer from './EvidenceDrawer';
// micro-reflection-v2 — one-tap ambient reflection chips
import MicroReflectionBar from './MicroReflectionBar';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'error' | 'system';
  content: string;
  timestamp: Date;
  isError?: boolean;  // Legacy flag for backward compatibility
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
  lens?: 'astrology' | 'human_design' | 'numerology' | 'bazi' | null;
  placeholder?: string;
  headerTitle?: string;
  headerSubtitle?: string;
  onClose?: () => void;
  keystoneContext?: KeystoneContext | null;  // For keystone continuation
  initialMessage?: string | null;  // Pre-filled question for Ask flows
  // V1: Pattern Thread Context for Lens → Chat continuity
  patternThreadContext?: PatternThreadContext | null;
}

// V1: Pattern Thread Context - Passed when navigating from Home/Lens to Chat
interface PatternThreadContext {
  source_surface: 'home' | 'numerology' | 'astrology' | 'bazi' | 'human_design';
  pattern_key?: string;  // e.g., "life_path_1", "sun_scorpio"
  core_truth?: string;
  echo?: string;
  cross_link?: string;
  memory_line?: string;  // Only if real
  current_shift?: string;
  genius?: string;
  lens_specific_truth?: string;
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

// ===== RESPONSE NORMALIZATION =====
// Normalizes backend response to a consistent format, handling various edge cases
interface NormalizedResponse {
  text: string | null;
  status: 'ok' | 'empty' | 'error';
  errorMessage?: string;
}

function normalizeMirrorResponse(response: any): NormalizedResponse {
  // Log raw response for debugging
  console.log('[MIRROR_NORMALIZE] Raw response:', {
    type: typeof response,
    hasData: !!response?.data,
    dataKeys: response?.data ? Object.keys(response.data) : [],
  });
  
  // Handle null/undefined response
  if (!response) {
    console.log('[MIRROR_NORMALIZE] Response is null/undefined');
    return { text: null, status: 'error', errorMessage: 'No response received from Mirror.' };
  }
  
  // Handle axios response wrapper
  const data = response.data || response;
  
  // Log response data shape
  console.log('[MIRROR_NORMALIZE] Response data:', {
    hasResponse: 'response' in data,
    hasText: 'text' in data,
    hasMessage: 'message' in data,
    hasContent: 'content' in data,
    hasAnswer: 'answer' in data,
  });
  
  // Try multiple possible response fields (in order of priority)
  let text: string | null = null;
  
  // Check for response field (primary)
  if (typeof data.response === 'string') {
    text = data.response;
  }
  // Fallback to other common field names
  else if (typeof data.text === 'string') {
    text = data.text;
  }
  else if (typeof data.message === 'string' && !data.error) {
    text = data.message;
  }
  else if (typeof data.content === 'string') {
    text = data.content;
  }
  else if (typeof data.answer === 'string') {
    text = data.answer;
  }
  // Handle nested response structures
  else if (data.data?.response) {
    text = data.data.response;
  }
  
  // Trim whitespace and validate
  if (text) {
    text = text.trim();
  }
  
  // Check for empty content
  if (!text || text.length === 0) {
    console.log('[MIRROR_NORMALIZE] Response text is empty after normalization');
    return { text: null, status: 'empty', errorMessage: 'Mirror returned an empty response.' };
  }
  
  console.log('[MIRROR_NORMALIZE] Success:', { textLength: text.length, preview: text.substring(0, 50) });
  return { text, status: 'ok' };
}

// Validate if a message should be rendered
function isValidMessageContent(content: string | null | undefined): boolean {
  if (!content) return false;
  const trimmed = content.trim();
  return trimmed.length > 0;
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

// Generate a reflective insight summary from memory update
// Guidelines: 1-2 sentences, reflective tone, not prescriptive, no advice
function generateInsightSummary(memoryUpdate: MemoryUpdate): string {
  const { themes, recurring_tensions, inferred_state, confidence } = memoryUpdate;
  
  // Priority 1: If there's a recurring tension, focus on that
  if (recurring_tensions.length > 0) {
    const tension = recurring_tensions[0];
    // Make it reflective, not diagnostic
    if (tension.toLowerCase().includes('and')) {
      return `A tension between ${tension.toLowerCase()} surfaced in this reflection.`;
    }
    return `Something around ${tension.toLowerCase()} appears to be present.`;
  }
  
  // Priority 2: If there are strong themes
  if (themes.length > 0) {
    const theme = themes[0];
    if (themes.length > 1) {
      return `Themes of ${theme.toLowerCase()} and ${themes[1].toLowerCase()} emerged in this conversation.`;
    }
    return `A sense of ${theme.toLowerCase()} seems to be moving through.`;
  }
  
  // Priority 3: Use inferred state
  const stateDescriptions: Record<string, string> = {
    'grounding': 'A need for grounding and stability surfaced.',
    'stabilizing': 'A process of finding balance seems underway.',
    'exploring': 'An openness to exploring new perspectives emerged.',
    'integrating': 'A moment of integration and understanding appeared.',
    'unclear': 'Something is shifting, though its shape is still forming.',
  };
  
  return stateDescriptions[inferred_state] || 'A reflection moment was captured.';
}

// Map inferred state to pattern domains
function mapStateToDomains(state: string, themes: string[]): string[] {
  const domainMap: Record<string, string[]> = {
    'grounding': ['energy_vitality', 'mind_meaning'],
    'stabilizing': ['emotional_landscape', 'relationships_boundaries'],
    'exploring': ['identity_direction', 'growth_transformation'],
    'integrating': ['mind_meaning', 'growth_transformation'],
    'unclear': ['emotional_landscape'],
  };
  
  return domainMap[state] || ['emotional_landscape'];
}

export default function MirrorChat({
  userId,
  lens = null,
  placeholder = "Say what's real right now…",
  headerTitle = "Mirror",
  headerSubtitle = "A mirror, not a verdict.",
  onClose,
  keystoneContext = null,
  initialMessage = null,
  patternThreadContext = null,
}: MirrorChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState(initialMessage || '');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [memoryUpdate, setMemoryUpdate] = useState<MemoryUpdate | null>(null);
  const [isMemoryExpanded, setIsMemoryExpanded] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const [hasTriggeredKeystone, setHasTriggeredKeystone] = useState(false);
  
  // V1: Track if pattern thread context has been used
  const [hasUsedPatternThreadContext, setHasUsedPatternThreadContext] = useState(false);
  
  // Leader card expansion state
  // - Default expanded when chat is empty (onboarding state)
  // - Auto-collapse when user sends first message
  // - User can manually toggle
  const [isLeaderExpanded, setIsLeaderExpanded] = useState(true);
  const [userManuallyToggledLeader, setUserManuallyToggledLeader] = useState(false);
  
  // Thread state for "Today's thread" pill
  const [threadState, setThreadState] = useState<ThreadState | null>(null);
  const [showThreadModal, setShowThreadModal] = useState(false);
  
  // Track if insight has been saved for this session
  const [insightSavedForSession, setInsightSavedForSession] = useState(false);
  
  // Dominant Truth for contextual awareness (Master Layer Integration)
  const { data: dominantTruthData, isLoading: isDominantTruthLoading, hasPattern: hasDominantPattern } = useDominantTruthForChat(userId);
  
  // Keyboard state for better scroll handling
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  
  // Animation for loading indicator
  const loadingOpacity = useRef(new Animated.Value(0)).current;
  
  const flatListRef = useRef<FlatList>(null);
  const inputRef = useRef<TextInput>(null);
  const insets = useSafeAreaInsets();

  // Track keyboard visibility for better UX
  useEffect(() => {
    const keyboardWillShow = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
      () => {
        setKeyboardVisible(true);
        // Scroll to end when keyboard appears
        setTimeout(() => {
          flatListRef.current?.scrollToEnd({ animated: true });
        }, 100);
      }
    );
    const keyboardWillHide = Keyboard.addListener(
      Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
      () => {
        setKeyboardVisible(false);
      }
    );

    return () => {
      keyboardWillShow.remove();
      keyboardWillHide.remove();
    };
  }, []);

  // Animate loading indicator
  useEffect(() => {
    if (isLoading) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(loadingOpacity, {
            toValue: 1,
            duration: 600,
            useNativeDriver: true,
          }),
          Animated.timing(loadingOpacity, {
            toValue: 0.4,
            duration: 600,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      loadingOpacity.setValue(0);
    }
  }, [isLoading]);

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
  // ===== GREETING MESSAGE INITIALIZATION =====
  // Only set greeting on initial mount, NOT on every lens change
  useEffect(() => {
    console.log('[MIRROR_CHAT_DEBUG] Greeting useEffect triggered - lens:', lens, 'messages.length:', messages.length);
    
    // Only set greeting if messages is empty (first mount)
    if (messages.length === 0) {
      const greeting = lens
        ? `I'm here to explore your ${lens === 'human_design' ? 'Human Design' : lens.charAt(0).toUpperCase() + lens.slice(1)} chart with you. What would you like to understand?`
        : "I'm here as a companion for self-understanding. Share what's on your mind, and I'll reflect what I notice.";
      
      console.log('[MIRROR_CHAT_DEBUG] Setting greeting message (messages was empty)');
      setMessages([{
        id: 'greeting',
        role: 'assistant',
        content: greeting,
        timestamp: new Date(),
      }]);
    } else {
      console.log('[MIRROR_CHAT_DEBUG] Skipping greeting - messages already has', messages.length, 'items');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lens]); // Only run when lens changes, and check messages.length inside

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

    // Track chat send event for engagement adaptation
    trackChatSend().catch(console.error);

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date(),
    };

    // ===== DEBUG: Log current state before update =====
    console.log('[MIRROR_CHAT_DEBUG] Before setMessages - current messages count:', messages.length);
    console.log('[MIRROR_CHAT_DEBUG] Adding user message:', { id: userMessage.id, content: userMessage.content.substring(0, 50) });
    
    setMessages(prev => {
      console.log('[MIRROR_CHAT_DEBUG] setMessages callback - prev count:', prev.length, 'adding user message');
      const newMessages = [...prev, userMessage];
      console.log('[MIRROR_CHAT_DEBUG] setMessages callback - new count:', newMessages.length);
      return newMessages;
    });
    
    const sentText = inputText.trim();
    setInputText('');
    setIsLoading(true);
    
    // Scroll to end after sending, don't dismiss keyboard immediately
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);

    // ============================================
    // DEBUG LOGGING - MIRROR CHAT REQUEST
    // ============================================
    // Build unified Mirror context using the engine (for generalist chat only)
    let mirrorEngineContext: string | undefined;
    if (!lens && hasDominantPattern && dominantTruthData) {
      const mirrorResponse = buildMirrorResponse({
        dominantTruth: {
          dominantTheme: dominantTruthData.systemContext?.split('\n')[0] || 'general',
          confidenceScore: 70,
        },
        hasHistory: messages.length > 2,
        variationSeed: Date.now(),
      });
      mirrorEngineContext = getAskMirrorContext(mirrorResponse);
    }
    
    const requestPayload = {
      user_id: userId,
      message: userMessage.content,
      lens: lens,
      session_id: sessionId,
      include_journal: true,
      include_history: true,
      // Master Layer Integration: Inject unified Mirror context
      dominant_pattern_context: mirrorEngineContext || (!lens && hasDominantPattern ? dominantTruthData?.systemContext : undefined),
      // V1: Pattern Thread Context for Lens → Chat continuity
      pattern_thread_context: (!hasUsedPatternThreadContext && patternThreadContext) ? {
        source_surface: patternThreadContext.source_surface,
        pattern_key: patternThreadContext.pattern_key,
        core_truth: patternThreadContext.core_truth,
        echo: patternThreadContext.echo,
        cross_link: patternThreadContext.cross_link,
        memory_line: patternThreadContext.memory_line,
        current_shift: patternThreadContext.current_shift,
        genius: patternThreadContext.genius,
      } : undefined,
    };
    
    // Mark pattern thread context as used after first message
    if (patternThreadContext && !hasUsedPatternThreadContext) {
      setHasUsedPatternThreadContext(true);
    }
    
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

      // ===== NORMALIZE RESPONSE =====
      const normalized = normalizeMirrorResponse(response);
      console.log('[MIRROR_CHAT_NORMALIZED]', {
        status: normalized.status,
        hasText: !!normalized.text,
        textLength: normalized.text?.length || 0,
        errorMessage: normalized.errorMessage,
      });
      
      // Handle empty/error responses - do NOT create blank bubbles
      if (normalized.status === 'empty' || normalized.status === 'error') {
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'error',
          content: normalized.errorMessage || "Mirror couldn't respond just now. Please try again.",
          timestamp: new Date(),
          isError: true,
        };
        setMessages(prev => [...prev, errorMessage]);
        console.log('[MIRROR_CHAT] Empty/error response - showing error card instead of blank bubble');
        return;
      }

      // Valid response - create assistant message
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: normalized.text!,
        timestamp: new Date(response.data.timestamp || new Date()),
        evidence: response.data?.evidence ?? null,
      };
      
      // Final validation before adding to messages
      if (!isValidMessageContent(assistantMessage.content)) {
        console.log('[MIRROR_CHAT] Content validation failed - not rendering message');
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: 'error',
          content: "Mirror's response couldn't be displayed. Please try again.",
          timestamp: new Date(),
          isError: true,
        };
        setMessages(prev => [...prev, errorMessage]);
        return;
      }

      setMessages(prev => [...prev, assistantMessage]);
      setSessionId(response.data.session_id);
      
      // Store memory update if present and save insight to timeline
      if (response.data.memory_update) {
        const update = response.data.memory_update;
        setMemoryUpdate(update);
        
        // Save insight to timeline (only once per session, and only for generalist chat)
        // Only save if confidence is high enough to be meaningful
        if (!insightSavedForSession && !lens && update.confidence >= 0.5) {
          try {
            const insightSummary = generateInsightSummary(update);
            const domains = mapStateToDomains(update.inferred_state, update.themes);
            const tags = [...update.themes.slice(0, 2), ...update.recurring_tensions.slice(0, 1)];
            
            await createMirrorInsight({
              user_id: userId,
              summary: insightSummary,
              domains,
              tags,
              confidence: update.confidence,
            });
            
            setInsightSavedForSession(true);
            console.log('[MirrorChat] Insight saved to timeline:', insightSummary);
          } catch (insightError) {
            console.error('[MirrorChat] Failed to save insight:', insightError);
            // Don't fail the chat - this is a secondary feature
          }
        }
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
        role: 'error',
        content: errorContent,
        timestamp: new Date(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = ({ item, index }: { item: Message; index: number }) => {
    const isUser = item.role === 'user';
    const isError = item.role === 'error' || item.isError === true;
    const isSystem = item.role === 'system';
    const isFirstMessage = index === 0;
    
    // ===== CONTENT VALIDATION =====
    // Never render empty bubbles - this prevents the "blank white bubble" bug
    const content = item.content?.trim() || '';
    if (!content && !isError) {
      console.log('[MIRROR_RENDER] Skipping empty message:', { id: item.id, role: item.role });
      return null;
    }
    
    // ===== ERROR MESSAGE RENDERING =====
    // Error messages get a distinct visual treatment
    if (isError) {
      console.log('[MIRROR_RENDER] Rendering error message:', { id: item.id, content: content.substring(0, 50) });
      return (
        <View style={[
          styles.messageWrapper,
          styles.assistantWrapper,
          isFirstMessage && styles.firstMessage,
        ]}>
          <View style={styles.errorBubble}>
            <Text style={styles.errorIcon}>⚠️</Text>
            <Text style={styles.errorText}>
              {content || "Mirror couldn't respond just now. Please try again."}
            </Text>
          </View>
          <Text style={[styles.timestamp, styles.timestampLeft]}>
            {formatTime(item.timestamp)}
          </Text>
        </View>
      );
    }
    
    // ===== SYSTEM MESSAGE RENDERING =====
    if (isSystem) {
      return (
        <View style={[styles.messageWrapper, styles.systemWrapper]}>
          <Text style={styles.systemText}>{content}</Text>
        </View>
      );
    }
    
    // ===== NORMAL MESSAGE RENDERING =====
    console.log('[MIRROR_RENDER] Rendering message:', { 
      id: item.id, 
      role: item.role, 
      contentLength: content.length,
      isUser,
    });
    
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
            {content}
          </Text>
          {/* evidence-drawer-v2 — curated "Why this is showing up" drawer */}
          {!isUser && item.evidence && (
            <EvidenceDrawer evidence={item.evidence} />
          )}
          {/* micro-reflection-v2 — one-tap ambient reflection chips */}
          {!isUser && userId && (
            <MicroReflectionBar
              userId={userId}
              source="mirror"
              isLatest={index === messages.length - 1}
              sourceSession={sessionId}
              sourceMessage={item.id}
              contextLens={lens || null}
            />
          )}
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
            size={20} 
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

  // ===== DEBUG: Log messages array on every render =====
  useEffect(() => {
    console.log('[MIRROR_DEBUG] Messages array updated:', {
      count: messages.length,
      ids: messages.map(m => m.id),
      roles: messages.map(m => m.role),
      lastMessage: messages.length > 0 ? {
        id: messages[messages.length - 1].id,
        role: messages[messages.length - 1].role,
        content: messages[messages.length - 1].content?.substring(0, 50),
      } : null,
    });
  }, [messages]);

  // Scroll to end helper
  const scrollToEnd = useCallback(() => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  }, []);

  // ===== LEADER CARD AUTO-COLLAPSE LOGIC =====
  // Auto-collapse when user sends first message (messages > greeting)
  // If user manually toggled, respect their choice for this session
  useEffect(() => {
    const hasUserMessages = messages.some(m => m.role === 'user');
    
    // Only auto-collapse if:
    // 1. There are user messages (conversation has started)
    // 2. User hasn't manually toggled the leader card
    if (hasUserMessages && !userManuallyToggledLeader) {
      if (isLeaderExpanded) {
        console.log('[MIRROR_LEADER] Auto-collapsing - user sent first message');
        LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
        setIsLeaderExpanded(false);
      }
    }
  }, [messages, userManuallyToggledLeader, isLeaderExpanded]);

  // Handler for manual leader card toggle
  const handleLeaderToggle = useCallback(() => {
    console.log('[MIRROR_LEADER] Manual toggle:', isLeaderExpanded ? 'collapsing' : 'expanding');
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIsLeaderExpanded(prev => !prev);
    setUserManuallyToggledLeader(true);
  }, [isLeaderExpanded]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 10 : 0}
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

      {/* REFLECT V4.1 — Dominant Truth Chip + Memory Card intentionally
          removed from the top of the chat. They competed with the
          conversation for vertical space and made Mirror feel like a
          dashboard. Contextual signals can be surfaced inline within
          Mirror's responses, not as widgets above the input. */}

      {/* Thread Modal */}
      {renderThreadModal()}

      {/* ─────────────────────────────────────────────────────────────
          REFLECT V4 — Mirror Chat redesigned for emotional immediacy.
          The previous "Make sense of what you're going through" leader
          card has been removed in favour of an immersive chat surface.
          Users should be able to start typing within seconds, no
          accordion intro, no marketing copy above the fold.
          ───────────────────────────────────────────────────────────── */}

      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        extraData={messages.length}  // Force re-render when messages change
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        contentContainerStyle={[
          styles.messagesContainer,
          { paddingBottom: 16 }
        ]}
        showsVerticalScrollIndicator={false}
        onContentSizeChange={scrollToEnd}
        onLayout={scrollToEnd}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
        ListFooterComponent={
          isLoading ? (
            <Animated.View style={[styles.loadingContainer, { opacity: loadingOpacity }]}>
              <View style={styles.loadingBubble}>
                <View style={styles.loadingDots}>
                  <View style={[styles.loadingDot, styles.loadingDot1]} />
                  <View style={[styles.loadingDot, styles.loadingDot2]} />
                  <View style={[styles.loadingDot, styles.loadingDot3]} />
                </View>
                <Text style={styles.loadingText}>Mirror is reflecting…</Text>
              </View>
            </Animated.View>
          ) : null
        }
        style={styles.messagesList}
      />

      {/* Input Bar - persistent, sticky, always visible above the fold.
          Disclaimer copy intentionally removed in Reflect V4 to keep
          the surface emotionally immediate — explanatory text moved to
          Settings / About if needed. */}
      <View style={[
        styles.inputBar, 
        { paddingBottom: Math.max(insets.bottom, 8) }
      ]}>
        <View style={styles.inputContainer}>
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
            autoCorrect={true}
            blurOnSubmit={false}
            textAlignVertical="top"
            returnKeyType="default"
            scrollEnabled={true}
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
  
  // Leader Card (collapsible intro)
  leaderCardWrapper: {
    paddingHorizontal: 16,
    paddingTop: 4,
  },
  
  // Header — kept intentionally tight in V4.1 so the conversation
  // can start as close to the top as possible.
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 8,
    backgroundColor: Colors.background,
  },
  headerContent: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '600',
    color: Colors.text,
    letterSpacing: -0.3,
  },
  headerSubtitle: {
    fontSize: 14,
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
    fontSize: 14,
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
    marginBottom: 14,
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
    fontSize: 16,
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
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  memoryItem: {
    fontSize: 16,
    color: Colors.text,
    lineHeight: 32,
    marginBottom: 2,
  },
  stateContainer: {
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  stateLabel: {
    fontSize: 14,
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
    fontSize: 14,
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
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
    opacity: 0.7,
  },
  evidenceItem: {
    fontSize: 14,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    lineHeight: 17,
    marginBottom: 4,
    opacity: 0.8,
  },
  memoryFooter: {
    marginTop: 14,
    fontSize: 14,
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
    marginBottom: 14,
    gap: 6,
  },
  threadPillText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
  },
  threadPillDate: {
    fontSize: 14,
    color: Colors.textTertiary,
  },

  // Dominant Truth Chip (Master Layer Integration)
  dominantTruthChip: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    alignSelf: 'center',
    paddingVertical: 8,
    paddingHorizontal: 14,
    backgroundColor: 'rgba(139, 92, 246, 0.08)',
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: 'rgba(139, 92, 246, 0.3)',
    marginBottom: 14,
    marginHorizontal: 16,
    gap: 8,
  },
  dominantTruthChipIcon: {
    fontSize: 14,
    color: Colors.accent,
    marginTop: 2,
  },
  dominantTruthChipText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.accent,
    flex: 1,
    lineHeight: 31,
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
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    marginBottom: 16,
    marginRight: 30,
  },
  threadModalKeystone: {
    fontSize: 16,
    lineHeight: 30,
    color: Colors.text,
    marginBottom: 16,
  },
  threadModalAffirmation: {
    fontSize: 16,
    lineHeight: 30,
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
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.2,
    marginBottom: 14,
  },
  threadModalReflectQuestion: {
    fontSize: 17,
    lineHeight: 32,
    color: Colors.text,
  },
  threadModalFooter: {
    marginTop: 20,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  threadModalFooterText: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    fontStyle: 'italic',
  },

  // Messages
  messagesContainer: {
    paddingHorizontal: 16,
    paddingTop: 8,
    flexGrow: 1,
  },
  messagesList: {
    flex: 1,
  },
  messageWrapper: {
    marginBottom: 18,
    maxWidth: '92%',
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
    paddingHorizontal: 18,
    paddingVertical: 14,
    borderRadius: 20,
  },
  userBubble: {
    backgroundColor: Colors.text,
    borderBottomRightRadius: 6,
  },
  assistantBubble: {
    // REFLECT V4.1 — Mirror response is conversational, not a card.
    // No background, no border. The text itself carries the weight,
    // which is the design intent: an intimate, notebook-like dialogue
    // rather than a stack of UI widgets.
    backgroundColor: 'transparent',
    paddingHorizontal: 4,
    paddingVertical: 4,
  },
  messageText: {
    fontSize: 18,
    lineHeight: 32,
  },
  userText: {
    color: Colors.surface,
  },
  assistantText: {
    color: Colors.text,
  },
  
  // ===== ERROR MESSAGE STYLES =====
  // Error messages get distinct visual treatment to avoid confusion with normal responses
  errorBubble: {
    backgroundColor: '#2C1A1A',  // Subtle red-tinted dark background
    borderRadius: 18,
    borderBottomLeftRadius: 6,
    padding: 14,
    borderWidth: 1,
    borderColor: Colors.error + '40',
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  errorIcon: {
    fontSize: 16,
    marginTop: 2,
  },
  errorText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 32,
    color: Colors.error,
  },
  
  // ===== SYSTEM MESSAGE STYLES =====
  systemWrapper: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  systemText: {
    fontSize: 14,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  timestamp: {
    fontSize: 14,
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
    paddingVertical: 16,
    paddingHorizontal: 4,
    alignSelf: 'flex-start',
  },
  loadingBubble: {
    // FIXED: Use dark surface color to match assistant bubbles
    backgroundColor: Colors.surface,
    borderRadius: 18,
    borderBottomLeftRadius: 6,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  loadingDots: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 10,
  },
  loadingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.textTertiary,
    marginHorizontal: 2,
  },
  loadingDot1: {
    opacity: 0.4,
  },
  loadingDot2: {
    opacity: 0.6,
  },
  loadingDot3: {
    opacity: 0.8,
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },

  // Input Bar — REFLECT V4.1: softer, taller, more inviting. Removed
  // the hard top border in favour of a subtle background-only
  // separation. The pill grows to a comfortable two-line height by
  // default so users feel invited to write more than one sentence.
  inputBar: {
    backgroundColor: Colors.background,
    paddingHorizontal: 16,
    paddingTop: 10,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: Colors.surface,
    borderRadius: 28,
    paddingLeft: 18,
    paddingRight: 8,
    paddingVertical: 10,
    minHeight: 60,
  },
  input: {
    flex: 1,
    fontSize: 17,
    color: Colors.text,
    maxHeight: 160,
    minHeight: 44,
    paddingVertical: 8,
    paddingTop: Platform.OS === 'ios' ? 10 : 8,
    lineHeight: 26,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.text,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },
  sendButtonDisabled: {
    backgroundColor: Colors.border,
  },
  // Transparency line
  transparencyLine: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 14,
    opacity: 0.6,
    fontStyle: 'italic',
  },
});
