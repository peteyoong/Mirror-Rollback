/**
 * Action Tracking Service for Mirror - V1
 * ========================================
 * 
 * Tracks user behavior for the Recent Action Echo Layer.
 * Sends real behavioral data to backend for adaptive responses.
 * 
 * TRACKED EVENTS:
 * - HOME: open, close, duration, CTA taps
 * - CHAT: enter, send, close_no_send, duration
 * - LENSES: open, close, duration, exit destinations
 * - REFLECTION: open, save, close_no_save
 */

import api from './api';
import { storage } from '../store';

// =============================================================================
// TYPES
// =============================================================================

export type TrackingEventType = 
  // Home Events
  | 'home_open'
  | 'home_close'
  | 'home_cta_tap'
  | 'home_reflect_tap'
  | 'home_chat_tap'
  | 'home_lens_tap'
  // Chat Events
  | 'entered_chat'
  | 'chat_send'
  | 'chat_close_no_send'
  // Lens Events
  | 'lens_open'
  | 'lens_close'
  | 'lens_to_chat'
  | 'lens_to_home'
  // Reflection Events
  | 'reflect_open'
  | 'reflect_save'
  | 'reflect_close_no_save';

export type BackendEventType = 
  | 'open'
  | 'close'
  | 'interact'
  | 'enter_lens'
  | 'enter_chat'
  | 'chat_send';

export interface TrackingPayload {
  user_id: string;
  session_id: string;
  event_type: BackendEventType;
  time_on_home?: number;
  pattern_shown?: string;
  behavior_snap_shown?: string;
  life_arena_shown?: string;
  chat_message_sent?: boolean;
  lens_time?: number;
  scroll_depth?: number;
}

export interface TrackingContext {
  patternShown?: string;
  behaviorSnapShown?: string;
  lifeArenaShown?: string;
}

// =============================================================================
// SESSION MANAGEMENT
// =============================================================================

let currentSessionId: string | null = null;
let sessionStartTime: number | null = null;
let chatStartTime: number | null = null;
let lensStartTime: number | null = null;
let reflectStartTime: number | null = null;
let chatMessageSent: boolean = false;
let reflectSaved: boolean = false;
let currentLensId: string | null = null;
let trackingContext: TrackingContext = {};

// Generate unique session ID
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Get current user ID from storage
const getUserId = async (): Promise<string | null> => {
  try {
    const userData = await storage.getItem('user');
    if (userData) {
      const user = JSON.parse(userData);
      return user.id || null;
    }
    return null;
  } catch {
    return null;
  }
};

// =============================================================================
// DEBUG LOGGING
// =============================================================================

const DEBUG_TRACKING = __DEV__ || process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true';

const logTracking = (eventType: string, data: Record<string, unknown>) => {
  if (DEBUG_TRACKING) {
    console.log(`[ActionTracking] ${eventType}:`, JSON.stringify(data, null, 2));
  }
};

// =============================================================================
// CORE TRACKING FUNCTION
// =============================================================================

const sendTrackingEvent = async (
  eventType: BackendEventType,
  additionalData: Partial<TrackingPayload> = {}
): Promise<boolean> => {
  try {
    const userId = await getUserId();
    if (!userId) {
      logTracking('SKIP', { reason: 'no_user_id', eventType });
      return false;
    }

    if (!currentSessionId) {
      currentSessionId = generateSessionId();
    }

    const payload: TrackingPayload = {
      user_id: userId,
      session_id: currentSessionId,
      event_type: eventType,
      pattern_shown: trackingContext.patternShown,
      behavior_snap_shown: trackingContext.behaviorSnapShown,
      life_arena_shown: trackingContext.lifeArenaShown,
      ...additionalData,
    };

    logTracking('SEND', { eventType, payload });

    const response = await api.post('/engagement/track', payload);
    
    logTracking('RESPONSE', { eventType, response: response.data });

    return response.data?.success === true;
  } catch (error) {
    logTracking('ERROR', { eventType, error: String(error) });
    return false;
  }
};

// =============================================================================
// HOME TRACKING
// =============================================================================

export const trackHomeOpen = async (context?: TrackingContext): Promise<void> => {
  currentSessionId = generateSessionId();
  sessionStartTime = Date.now();
  
  if (context) {
    trackingContext = { ...context };
  }
  
  await sendTrackingEvent('open');
};

export const trackHomeClose = async (): Promise<void> => {
  const duration = sessionStartTime 
    ? (Date.now() - sessionStartTime) / 1000 
    : 0;
  
  await sendTrackingEvent('close', {
    time_on_home: duration,
    chat_message_sent: chatMessageSent,
  });
  
  // Reset session state
  sessionStartTime = null;
  chatMessageSent = false;
};

export const trackHomeCTATap = async (): Promise<void> => {
  await sendTrackingEvent('interact');
};

export const trackHomeReflectTap = async (): Promise<void> => {
  await sendTrackingEvent('interact');
};

export const trackHomeChatTap = async (): Promise<void> => {
  chatStartTime = Date.now();
  chatMessageSent = false;
  await sendTrackingEvent('enter_chat');
};

export const trackHomeLensTap = async (lensId?: string): Promise<void> => {
  lensStartTime = Date.now();
  currentLensId = lensId || null;
  await sendTrackingEvent('enter_lens');
};

// =============================================================================
// CHAT TRACKING
// =============================================================================

export const trackChatEnter = async (): Promise<void> => {
  if (!chatStartTime) {
    chatStartTime = Date.now();
  }
  chatMessageSent = false;
  await sendTrackingEvent('enter_chat');
};

export const trackChatSend = async (): Promise<void> => {
  chatMessageSent = true;
  await sendTrackingEvent('chat_send', {
    chat_message_sent: true,
  });
};

export const trackChatClose = async (messageSent: boolean = false): Promise<void> => {
  const duration = chatStartTime 
    ? (Date.now() - chatStartTime) / 1000 
    : 0;
  
  chatMessageSent = messageSent || chatMessageSent;
  
  // Chat close is part of home close or lens close
  // We just update the tracking context
  logTracking('CHAT_CLOSE', { 
    duration, 
    messageSent: chatMessageSent,
  });
  
  chatStartTime = null;
};

// =============================================================================
// LENS TRACKING
// =============================================================================

export const trackLensOpen = async (lensId: string): Promise<void> => {
  lensStartTime = Date.now();
  currentLensId = lensId;
  await sendTrackingEvent('enter_lens');
};

export const trackLensClose = async (): Promise<void> => {
  const duration = lensStartTime 
    ? (Date.now() - lensStartTime) / 1000 
    : 0;
  
  logTracking('LENS_CLOSE', { 
    lensId: currentLensId,
    duration,
    exitFast: duration < 8,
  });
  
  lensStartTime = null;
  currentLensId = null;
};

export const trackLensToChat = async (): Promise<void> => {
  chatStartTime = Date.now();
  chatMessageSent = false;
  await sendTrackingEvent('enter_chat');
};

export const trackLensToHome = async (): Promise<void> => {
  await trackLensClose();
};

// =============================================================================
// REFLECTION TRACKING
// =============================================================================

export const trackReflectOpen = async (): Promise<void> => {
  reflectStartTime = Date.now();
  reflectSaved = false;
  await sendTrackingEvent('interact');
};

export const trackReflectSave = async (): Promise<void> => {
  reflectSaved = true;
  await sendTrackingEvent('interact');
};

export const trackReflectClose = async (saved: boolean = false): Promise<void> => {
  const duration = reflectStartTime 
    ? (Date.now() - reflectStartTime) / 1000 
    : 0;
  
  logTracking('REFLECT_CLOSE', { 
    duration, 
    saved: saved || reflectSaved,
  });
  
  reflectStartTime = null;
  reflectSaved = false;
};

// =============================================================================
// CONTEXT UPDATES
// =============================================================================

export const updateTrackingContext = (context: TrackingContext): void => {
  trackingContext = { ...trackingContext, ...context };
  logTracking('CONTEXT_UPDATE', trackingContext);
};

export const clearTrackingContext = (): void => {
  trackingContext = {};
};

// =============================================================================
// COMPUTED STATES (for frontend use)
// =============================================================================

export const getCurrentSessionDuration = (): number => {
  if (!sessionStartTime) return 0;
  return (Date.now() - sessionStartTime) / 1000;
};

export const getChatDuration = (): number => {
  if (!chatStartTime) return 0;
  return (Date.now() - chatStartTime) / 1000;
};

export const getLensDuration = (): number => {
  if (!lensStartTime) return 0;
  return (Date.now() - lensStartTime) / 1000;
};

export const wasChatMessageSent = (): boolean => chatMessageSent;

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

const ActionTracking = {
  // Home
  trackHomeOpen,
  trackHomeClose,
  trackHomeCTATap,
  trackHomeReflectTap,
  trackHomeChatTap,
  trackHomeLensTap,
  // Chat
  trackChatEnter,
  trackChatSend,
  trackChatClose,
  // Lens
  trackLensOpen,
  trackLensClose,
  trackLensToChat,
  trackLensToHome,
  // Reflection
  trackReflectOpen,
  trackReflectSave,
  trackReflectClose,
  // Context
  updateTrackingContext,
  clearTrackingContext,
  // State
  getCurrentSessionDuration,
  getChatDuration,
  getLensDuration,
  wasChatMessageSent,
};

export default ActionTracking;
