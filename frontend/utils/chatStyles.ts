/**
 * Shared Chat Bubble Utilities
 * 
 * This file provides consistent role normalization and bubble styles
 * across all chat components in the app.
 * 
 * Usage:
 * import { normalizeRole, getChatBubbleStyles } from '../utils/chatStyles';
 */

import { StyleSheet, Platform } from 'react-native';

/**
 * Normalize any role string to a standard role type.
 * IMPORTANT: Unknown roles default to 'assistant' (dark bubble), NEVER 'user'.
 */
export type ChatRole = 'user' | 'assistant' | 'system';

export function normalizeRole(msg: any): ChatRole {
  const raw = String(msg?.role ?? msg?.sender ?? msg?.type ?? '').toLowerCase();
  
  // Only explicitly 'user' roles become user
  if (raw.includes('user')) return 'user';
  
  // System messages
  if (raw.includes('system')) return 'system';
  
  // Everything else (assistant, ai, bot, unknown) => assistant
  // This ensures unknown roles get dark bubbles with light text
  return 'assistant';
}

/**
 * Get raw role string for debugging purposes
 */
export function getRawRole(msg: any): string {
  return String(msg?.role ?? msg?.sender ?? msg?.type ?? '').toLowerCase();
}

/**
 * Shared bubble style constants
 * These values ensure readable text contrast on all backgrounds
 */
export const BubbleColors = {
  // User bubble: white/light background with dark text
  user: {
    background: 'rgba(255,255,255,0.92)',
    text: 'rgba(0,0,0,0.88)',
    border: 'transparent',
  },
  // Assistant bubble: dark translucent background with light text
  assistant: {
    background: 'rgba(255,255,255,0.06)',
    text: 'rgba(255,255,255,0.92)',
    border: 'rgba(255,255,255,0.10)',
  },
  // System bubble: slightly dimmer than assistant
  system: {
    background: 'rgba(255,255,255,0.05)',
    text: 'rgba(255,255,255,0.85)',
    border: 'rgba(255,255,255,0.08)',
  },
};

/**
 * Get bubble style based on normalized role
 */
export function getBubbleStyle(role: ChatRole) {
  return role === 'user' ? chatBubbleStyles.userBubble
    : role === 'system' ? chatBubbleStyles.systemBubble
    : chatBubbleStyles.assistantBubble;
}

/**
 * Get text style based on normalized role
 */
export function getTextStyle(role: ChatRole) {
  return role === 'user' ? chatBubbleStyles.userText
    : role === 'system' ? chatBubbleStyles.systemText
    : chatBubbleStyles.assistantText;
}

/**
 * Pre-built StyleSheet for chat bubbles
 * Import these directly or use getBubbleStyle/getTextStyle functions
 */
export const chatBubbleStyles = StyleSheet.create({
  // Base message bubble (apply to all)
  messageBubble: {
    maxWidth: '85%',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 16,
    marginBottom: 12,
  },
  
  // User bubble: white/light background, aligned right
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: BubbleColors.user.background,
    borderBottomRightRadius: 6,
  },
  
  // Assistant bubble: dark translucent background, aligned left
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: BubbleColors.assistant.background,
    borderColor: BubbleColors.assistant.border,
    borderWidth: 1,
    borderBottomLeftRadius: 6,
  },
  
  // System bubble: similar to assistant but slightly dimmer
  systemBubble: {
    alignSelf: 'flex-start',
    backgroundColor: BubbleColors.system.background,
    borderColor: BubbleColors.system.border,
    borderWidth: 1,
    borderBottomLeftRadius: 6,
  },
  
  // Base message text
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  
  // User text: dark on light background
  userText: {
    color: BubbleColors.user.text,
  },
  
  // Assistant text: light on dark background
  assistantText: {
    color: BubbleColors.assistant.text,
  },
  
  // System text: slightly dimmer light on dark background
  systemText: {
    color: BubbleColors.system.text,
  },
  
  // Timestamp (always visible)
  timestamp: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.45)',
    marginTop: 4,
  },
});

/**
 * Helper to check if debug mode is enabled via URL param
 */
export function isDebugMode(): boolean {
  if (Platform.OS !== 'web') return false;
  try {
    const params = new URLSearchParams(window.location.search);
    return params.get('debug') === '1';
  } catch {
    return false;
  }
}
