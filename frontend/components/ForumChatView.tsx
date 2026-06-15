import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Platform,
  Keyboard,
} from 'react-native';
// FORUM-COMPOSER-KBD-V1 (Option B):
// Use react-native-keyboard-controller's KeyboardAvoidingView instead of
// the stock react-native one.  Reason: on iPhone Safari (web), the stock
// KeyboardAvoidingView does not subscribe to `window.visualViewport`
// resize events, so the soft-keyboard overlay leaves the composer
// hidden behind the keyboard.  The keyboard-controller version handles
// both native iOS/Android keyboard events AND the visualViewport API on
// web.  Chat surfaces should use `translate-with-padding` per the
// expo-keyboard-experience skill recommendation.
import { KeyboardAvoidingView } from 'react-native-keyboard-controller';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useAppStore } from '../store';
import {
  ForumChatMode,
  ForumChatMessage,
  ForumPulseMemberCard,
  ClarificationCandidate,
  ResolvedContextBlock,
  getForumChatHistory,
  sendForumChatMessage,
} from '../services/api';
import ResolvedContextChip from './forum/ResolvedContextChip';
import AmbiguityClarificationPanel from './forum/AmbiguityClarificationPanel';

// Slice C — FORUM_CHAT_AUTO_CONTEXT flag (frontend mirror of the backend flag).
// When `true`, the Me/Member/Forum tab strip is hidden and the resolver-decided
// context chip is shown above each Mirror response.  When unset / not "true",
// the legacy mode-driven UI is preserved byte-for-byte.
const AUTO_CTX_ENABLED =
  (process.env.EXPO_PUBLIC_FORUM_CHAT_AUTO_CONTEXT || '').toLowerCase() === 'true';

interface ForumChatViewProps {
  forumId: string;
  members: ForumPulseMemberCard[];
  onClose: () => void;
  initialMode?: ForumChatMode;
  initialMember?: ForumPulseMemberCard | null;
}

// Suggested prompts for each mode
const SUGGESTED_PROMPTS: Record<ForumChatMode, string[]> = {
  self: [
    "How might my lenses influence how I show up in this forum?",
    "What patterns might I be exploring in this group?",
  ],
  member: [
    "What strengths might this member bring to the forum?",
    "What perspective might this member contribute?",
  ],
  forum: [
    "What themes seem to be emerging in our forum?",
    "What strengths does this group composition bring?",
    "What tensions might help the group grow?",
  ],
};

export default function ForumChatView({ forumId, members, onClose, initialMode, initialMember }: ForumChatViewProps) {
  const { theme } = useTheme();
  const { user } = useAppStore();
  
  // State - use initial values if provided
  const [mode, setMode] = useState<ForumChatMode>(initialMode || 'self');
  const [selectedMember, setSelectedMember] = useState<ForumPulseMemberCard | null>(initialMember || null);
  const [showMemberPicker, setShowMemberPicker] = useState(false);
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<ForumChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Slice C — auto-context state.  Holds the most recent target_user_id
  // so a follow-up pronoun ("she", "they") can be resolved by the backend.
  const [lastTargetId, setLastTargetId] = useState<string | null>(null);
  // Holds the AMBIGUOUS clarification banner data, if any.
  const [clarification, setClarification] = useState<{
    candidates: ClarificationCandidate[];
    originalMessage: string;
  } | null>(null);
  
  const scrollViewRef = useRef<ScrollView>(null);
  
  // Load chat history on mount
  useEffect(() => {
    if (user?.id) {
      loadChatHistory();
    }
  }, [user?.id, forumId]);
  
  const loadChatHistory = async () => {
    if (!user?.id) return;
    
    try {
      setInitialLoading(true);
      const response = await getForumChatHistory(forumId, user.id);
      setMessages(response.messages || []);
    } catch (err) {
      console.error('[ForumChat] Error loading history:', err);
    } finally {
      setInitialLoading(false);
    }
  };
  
  // Scroll to bottom when messages change
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);
  
  // Handle mode change
  const handleModeChange = (newMode: ForumChatMode) => {
    setMode(newMode);
    setSelectedMember(null);
    // Always close the member picker when changing modes
    setShowMemberPicker(false);
  };
  
  // Handle opening member picker (only in member mode with available members)
  const handleOpenMemberPicker = () => {
    if (mode === 'member' && otherMembers.length > 0) {
      setShowMemberPicker(true);
    }
  };
  
  // Handle member selection
  const handleSelectMember = (member: ForumPulseMemberCard) => {
    setSelectedMember(member);
    setShowMemberPicker(false);
  };
  
  // Handle send message
  const handleSend = async (text?: string, opts?: {
    overrideTargetId?: string;
  }) => {
    const messageText = text || message.trim();
    if (!messageText || !user?.id) return;
    
    // Validate member mode — only when AUTO_CTX is OFF (legacy contract)
    if (!AUTO_CTX_ENABLED && mode === 'member' && !selectedMember) {
      setError('Please select a member first');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setMessage('');
      setClarification(null);
      Keyboard.dismiss();

      // Build the request.  When AUTO_CTX is on we OMIT `mode` so the
      // backend resolver decides; when off, we send the legacy fields.
      const requestBody = AUTO_CTX_ENABLED
        ? {
            user_id:          user.id,
            message:          messageText,
            target_member_id: opts?.overrideTargetId,
            last_target_id:   lastTargetId || undefined,
          }
        : {
            user_id:          user.id,
            message:          messageText,
            mode:             mode,
            target_member_id: selectedMember?.user_id,
          };

      const response = await sendForumChatMessage(forumId, requestBody);

      // Slice C — handle the AMBIGUOUS short-circuit.  The backend
      // returned 200 with `requires_clarification=true` and a list of
      // candidates; render the panel and STOP (do not append a message).
      if (response.requires_clarification) {
        setClarification({
          candidates:      response.clarification_candidates || [],
          originalMessage: messageText,
        });
        return;
      }

      const rc = response.resolved_context ?? null;

      // Track the most recently resolved target so pronoun follow-ups
      // can find it on the next turn.
      if (rc?.target_user_id) {
        setLastTargetId(rc.target_user_id);
      }

      // Derive a display mode for legacy renderers (the chip carries
      // the real frame info; this is only the message bubble's icon).
      const displayMode: ForumChatMode = (() => {
        if (!AUTO_CTX_ENABLED) return mode;
        if (!rc)                return 'self';
        switch (rc.frame) {
          case 'MEMBER':
          case 'PAIRWISE':
            return 'member';
          case 'FORUM':
          case 'MULTI_PERSON':
            return 'forum';
          default:
            return 'self';
        }
      })();

      // Add to messages
      const newMessage: ForumChatMessage = {
        id:                 response.message_id,
        mode:               displayMode,
        target_member_id:   rc?.target_user_id   ?? (selectedMember?.user_id ?? null),
        target_member_name: rc?.target_name      ?? (selectedMember?.name    ?? null),
        message:            messageText,
        response:           response.response,
        timestamp:          response.timestamp,
        resolved_context:   rc,
      };
      
      setMessages(prev => [...prev, newMessage]);
      
    } catch (err: any) {
      console.error('[ForumChat] Send error:', err);
      if (err.response?.status === 429) {
        setError('Please wait a moment before sending another message.');
      } else {
        setError('Failed to send message. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Slice C — clarification chooser.  Re-issues the original message with
  // the user-picked candidate as `target_member_id` so the resolver binds
  // unambiguously on the second pass.
  const handleClarificationPick = (cand: ClarificationCandidate) => {
    if (!clarification) return;
    const originalMessage = clarification.originalMessage;
    setClarification(null);
    if (cand.user_id) {
      setLastTargetId(cand.user_id);
    }
    handleSend(originalMessage, { overrideTargetId: cand.user_id || undefined });
  };
  
  // Get mode label
  const getModeLabel = (m: ForumChatMode): string => {
    switch (m) {
      case 'self': return 'Ask about me';
      case 'member': return 'Ask about a member';
      case 'forum': return 'Ask about our forum';
    }
  };
  
  // Get mode icon
  const getModeIcon = (m: ForumChatMode): string => {
    switch (m) {
      case 'self': return 'person-outline';
      case 'member': return 'people-outline';
      case 'forum': return 'globe-outline';
    }
  };
  
  // Filter out current user from member list
  const otherMembers = members.filter(m => m.user_id !== user?.id);
  
  // Show suggested prompts only if no messages yet
  const showSuggested = messages.length === 0 && !initialLoading;
  
  return (
    <KeyboardAvoidingView 
      style={[styles.container, { backgroundColor: theme.background }]}
      // FORUM-COMPOSER-KBD-V1:
      // 'translate-with-padding' is the chat-style behavior recommended by
      // the expo-keyboard-experience skill for messaging UIs.  On iOS it
      // pads-and-translates the content above the keyboard; on Android it
      // falls back to height resizing; on web it consumes
      // visualViewport.resize events so the composer no longer hides
      // behind the iOS Safari soft keyboard.
      behavior={Platform.OS === 'ios' ? 'translate-with-padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
    >
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity onPress={onClose} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
          <Ionicons name="arrow-back" size={24} color={theme.text} />
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>Ask Mirror</Text>
        <View style={{ width: 24 }} />
      </View>
      
      {/* Mode Selector — Slice C: hidden when auto-context is enabled */}
      {!AUTO_CTX_ENABLED && (
        <View style={[styles.modeSelector, { backgroundColor: theme.surface }]}>
          {(['self', 'member', 'forum'] as ForumChatMode[]).map((m) => (
            <TouchableOpacity
              key={m}
              style={[
                styles.modeButton,
                mode === m && { backgroundColor: theme.accent + '20' },
              ]}
              onPress={() => handleModeChange(m)}
            >
              <Ionicons
                name={getModeIcon(m) as any}
                size={18}
                color={mode === m ? theme.accent : theme.textSecondary}
              />
              <Text
                style={[
                  styles.modeButtonText,
                  { color: mode === m ? theme.accent : theme.textSecondary },
                ]}
                numberOfLines={1}
              >
                {m === 'self' ? 'Me' : m === 'member' ? 'Member' : 'Forum'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
      
      {/* Member Picker (for member mode) — also hidden when auto-context is on */}
      {!AUTO_CTX_ENABLED && mode === 'member' && (
        otherMembers.length > 0 ? (
          // Show member picker button when there are members
          <TouchableOpacity
            style={[styles.memberPickerButton, { backgroundColor: theme.surface, borderColor: theme.border }]}
            onPress={handleOpenMemberPicker}
          >
            <Ionicons name="person-circle-outline" size={20} color={theme.textSecondary} />
            <Text style={[styles.memberPickerText, { color: selectedMember ? theme.text : theme.textTertiary }]}>
              {selectedMember ? selectedMember.name : 'Select a member...'}
            </Text>
            <Ionicons name="chevron-down" size={18} color={theme.textTertiary} />
          </TouchableOpacity>
        ) : (
          // Show inline empty state when no other members
          <View style={[styles.memberEmptyState, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Ionicons name="people-outline" size={20} color={theme.textTertiary} />
            <Text style={[styles.memberEmptyText, { color: theme.textTertiary }]}>
              No other members in this forum yet.
            </Text>
          </View>
        )
      )}
      
      {/* Member Picker Dropdown — Slice C: hidden when auto-context is enabled */}
      {!AUTO_CTX_ENABLED && mode === 'member' && showMemberPicker && otherMembers.length > 0 && (
        <View style={[styles.memberPickerDropdown, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <ScrollView style={styles.memberPickerList}>
            {otherMembers.map((member) => (
              <TouchableOpacity
                key={member.user_id}
                style={[styles.memberPickerItem, { borderBottomColor: theme.border }]}
                onPress={() => handleSelectMember(member)}
              >
                <Text style={[styles.memberPickerItemName, { color: theme.text }]}>{member.name}</Text>
                {member.hd_type && (
                  <Text style={[styles.memberPickerItemType, { color: theme.textTertiary }]}>
                    {member.hd_type}
                  </Text>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
          <TouchableOpacity
            style={[styles.memberPickerClose, { borderTopColor: theme.border }]}
            onPress={() => setShowMemberPicker(false)}
          >
            <Text style={[styles.memberPickerCloseText, { color: theme.textSecondary }]}>Cancel</Text>
          </TouchableOpacity>
        </View>
      )}
      
      {/* Chat Messages */}
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={styles.messagesContent}
        keyboardShouldPersistTaps="handled"
      >
        {initialLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color={theme.accent} />
            <Text style={[styles.loadingText, { color: theme.textTertiary }]}>Loading chat...</Text>
          </View>
        ) : showSuggested ? (
          <View style={styles.suggestedContainer}>
            <Text style={[styles.suggestedTitle, { color: theme.text }]}>
              {AUTO_CTX_ENABLED ? 'Ask Mirror' : getModeLabel(mode)}
            </Text>
            <Text style={[styles.suggestedSubtitle, { color: theme.textTertiary }]}>
              {AUTO_CTX_ENABLED
                ? 'Ask anything — about yourself, a member, or the forum'
                : 'Tap a prompt or type your own question'}
            </Text>
            <View style={styles.suggestedPrompts}>
              {SUGGESTED_PROMPTS[mode].map((prompt, idx) => (
                <TouchableOpacity
                  key={idx}
                  style={[styles.suggestedPrompt, { backgroundColor: theme.surface, borderColor: theme.border }]}
                  onPress={() => handleSend(prompt)}
                  disabled={loading || (!AUTO_CTX_ENABLED && mode === 'member' && !selectedMember)}
                >
                  <Text style={[styles.suggestedPromptText, { color: theme.text }]}>{prompt}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ) : (
          messages.map((msg) => (
            <View key={msg.id} style={styles.messageGroup}>
              {/* User message */}
              <View style={[styles.userMessage, { backgroundColor: theme.accent + '15' }]}>
                <View style={styles.messageHeader}>
                  <Ionicons name={getModeIcon(msg.mode) as any} size={14} color={theme.textTertiary} />
                  <Text style={[styles.messageMode, { color: theme.textTertiary }]}>
                    {msg.mode === 'self' ? 'About me' : 
                     msg.mode === 'member' ? `About ${msg.target_member_name || 'member'}` : 
                     'About forum'}
                  </Text>
                </View>
                <Text style={[styles.userMessageText, { color: theme.text }]}>{msg.message}</Text>
              </View>
              
              {/* Mirror response */}
              <View style={[styles.mirrorMessage, { backgroundColor: theme.surface }]}>
                {/* Slice C — resolved context chip (auto-context only) */}
                {AUTO_CTX_ENABLED && msg.resolved_context && (
                  <ResolvedContextChip ctx={msg.resolved_context} />
                )}
                <View style={styles.messageHeader}>
                  <Text style={[styles.mirrorLabel, { color: theme.accent }]}>Mirror</Text>
                </View>
                <Text style={[styles.mirrorMessageText, { color: theme.text }]}>{msg.response}</Text>
              </View>
            </View>
          ))
        )}

        {/* Slice C — clarification banner shown when backend returns
            requires_clarification=true.  Tapping a candidate re-issues
            the original message with the resolved target_member_id. */}
        {clarification && (
          <AmbiguityClarificationPanel
            candidates={clarification.candidates}
            originalMessage={clarification.originalMessage}
            onChoose={handleClarificationPick}
            onCancel={() => setClarification(null)}
          />
        )}
        
        {/* Loading indicator */}
        {loading && (
          <View style={[styles.loadingMessage, { backgroundColor: theme.surface }]}>
            <ActivityIndicator size="small" color={theme.accent} />
            <Text style={[styles.loadingMessageText, { color: theme.textTertiary }]}>Mirror is reflecting...</Text>
          </View>
        )}
      </ScrollView>
      
      {/* Error message */}
      {error && (
        <View style={[styles.errorContainer, { backgroundColor: theme.error + '15' }]}>
          <Text style={[styles.errorText, { color: theme.error }]}>{error}</Text>
          <TouchableOpacity onPress={() => setError(null)}>
            <Ionicons name="close-circle" size={18} color={theme.error} />
          </TouchableOpacity>
        </View>
      )}
      
      {/* Input */}
      <View style={[styles.inputContainer, { borderTopColor: theme.border, backgroundColor: theme.background }]}>
        <TextInput
          style={[styles.input, { backgroundColor: theme.surface, color: theme.text, borderColor: theme.border }]}
          value={message}
          onChangeText={setMessage}
          placeholder={
            !AUTO_CTX_ENABLED && mode === 'member' && !selectedMember
              ? 'Select a member first...'
              : 'Type your question...'
          }
          placeholderTextColor={theme.textTertiary}
          multiline
          maxLength={500}
          editable={!loading && !(!AUTO_CTX_ENABLED && mode === 'member' && !selectedMember)}
          // FORUM-COMPOSER-KBD-V1:
          // When focus lands on the composer, give the layout a tick for
          // KeyboardAvoidingView to translate, then bring the latest
          // message into view above the keyboard.  Without this, the
          // last bubble stays clipped behind the lifted composer on
          // iPhone Safari.
          onFocus={() => {
            setTimeout(() => {
              try { scrollViewRef.current?.scrollToEnd({ animated: true }); } catch {}
            }, 150);
          }}
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            { backgroundColor: message.trim() && !loading ? theme.accent : theme.border },
          ]}
          onPress={() => handleSend()}
          disabled={!message.trim() || loading || (!AUTO_CTX_ENABLED && mode === 'member' && !selectedMember)}
        >
          <Ionicons name="send" size={18} color={message.trim() && !loading ? '#fff' : theme.textTertiary} />
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

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
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
  },
  modeSelector: {
    flexDirection: 'row',
    paddingHorizontal: 12,
    paddingVertical: 8,
    gap: 8,
  },
  modeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  modeButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  memberPickerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginVertical: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    gap: 8,
  },
  memberPickerText: {
    flex: 1,
    fontSize: 16,
  },
  memberPickerDropdown: {
    position: 'absolute',
    top: 120,
    left: 16,
    right: 16,
    maxHeight: 300,
    borderRadius: 12,
    borderWidth: 1,
    zIndex: 100,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
  },
  memberPickerList: {
    maxHeight: 220,
  },
  memberPickerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  memberPickerItemName: {
    fontSize: 17,
    fontWeight: '500',
  },
  memberPickerItemType: {
    fontSize: 14,
  },
  memberPickerEmpty: {
    padding: 20,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  memberEmptyState: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginVertical: 8,
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    gap: 10,
  },
  memberEmptyText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  memberPickerClose: {
    alignItems: 'center',
    paddingVertical: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  memberPickerCloseText: {
    fontSize: 16,
    fontWeight: '500',
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 24,
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
  },
  suggestedContainer: {
    alignItems: 'center',
    paddingTop: 24,
  },
  suggestedTitle: {
    fontSize: 22,
    fontWeight: '600',
    marginBottom: 14,
  },
  suggestedSubtitle: {
    fontSize: 16,
    marginBottom: 24,
  },
  suggestedPrompts: {
    width: '100%',
    gap: 12,
  },
  suggestedPrompt: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  suggestedPromptText: {
    fontSize: 16,
    lineHeight: 32,
  },
  messageGroup: {
    marginBottom: 20,
    gap: 12,
  },
  messageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  messageMode: {
    fontSize: 14,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  mirrorLabel: {
    fontSize: 14,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  userMessage: {
    padding: 14,
    borderRadius: 12,
    borderTopRightRadius: 4,
    alignSelf: 'flex-end',
    maxWidth: '90%',
  },
  userMessageText: {
    fontSize: 16,
    lineHeight: 32,
  },
  mirrorMessage: {
    padding: 14,
    borderRadius: 12,
    borderTopLeftRadius: 4,
    alignSelf: 'flex-start',
    maxWidth: '95%',
  },
  mirrorMessageText: {
    fontSize: 16,
    lineHeight: 30,
  },
  loadingMessage: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 14,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  loadingMessageText: {
    fontSize: 16,
    fontStyle: 'italic',
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginHorizontal: 16,
    marginBottom: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 8,
  },
  errorText: {
    flex: 1,
    fontSize: 16,
    marginRight: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 10,
  },
  input: {
    flex: 1,
    // FORUM-COMPOSER-KBD-V1:
    // 44px is the Apple HIG minimum touch target and also gives the
    // caret enough vertical room that typed characters are not clipped
    // by paddingVertical on iOS Safari multiline inputs.  Previously 40.
    minHeight: 44,
    maxHeight: 100,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    fontSize: 17,
    // textAlignVertical was set to 'center' here — that prop is
    // Android-only and gets stripped on RN-Web, which on iOS Safari
    // combined with multiline made typed text appear obscured.
    // Removed intentionally.
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
