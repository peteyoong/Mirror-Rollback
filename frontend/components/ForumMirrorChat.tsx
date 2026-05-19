/**
 * ForumMirrorChat — "Talk to the room" (forum-conversational-field-v1)
 * ====================================================================
 *
 * A quiet, spacious chat surface where the calling user talks WITH the
 * field of a forum.  Field-observer voice only — never names members,
 * never diagnoses, never quantifies.
 *
 * The component:
 *   - Loads recent per-user history from
 *       GET /api/forums/:forum_id/mirror-chat/history?user_id=...
 *   - Sends new turns to
 *       POST /api/forums/:forum_id/mirror-chat
 *   - Renders evidence in field language via EvidenceDrawer.
 *   - Allows micro-reflection taps on assistant bubbles via
 *     MicroReflectionBar (source='other').
 *
 * Visual posture: spacious padding, hairline borders, no headers,
 * no debug pill, no chips dashboard.  Reads like a journal, not a
 * dashboard.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Keyboard,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';
import EvidenceDrawer, { CuratedEvidence } from './EvidenceDrawer';
import MicroReflectionBar from './MicroReflectionBar';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'error';
  content: string;
  ts: string;
  evidence?: CuratedEvidence | null;
}

interface Props {
  userId: string;
  forumId: string;
}

// Soft prompt seeds shown above the input when the thread is empty.
const SEED_PROMPTS = [
  'What is this room avoiding?',
  'Why does this conversation keep circling?',
  'What softens this room?',
  'What feels unspoken lately?',
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ForumMirrorChat({ userId, forumId }: Props) {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const listRef = useRef<FlatList<Message>>(null);

  // ── Load per-user history. ───────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const resp = await api.get(
          `/forums/${forumId}/mirror-chat/history?user_id=${userId}&limit=40`,
        );
        if (cancelled) return;
        const raw = (resp?.data?.messages || []) as Array<{
          id: string;
          role: string;
          content: string;
          ts: string;
          session_id?: string;
        }>;
        const parsed: Message[] = raw.map((r) => ({
          id: r.id,
          role: (r.role as Message['role']) || 'assistant',
          content: r.content || '',
          ts: r.ts || '',
        }));
        setMessages(parsed);
        if (parsed.length) {
          const lastSession =
            raw[raw.length - 1]?.session_id || null;
          if (lastSession) setSessionId(lastSession);
        }
      } catch {
        // Silent — empty history is a valid state.
      } finally {
        if (!cancelled) setLoadingHistory(false);
      }
    };
    if (userId && forumId) void load();
    return () => {
      cancelled = true;
    };
  }, [userId, forumId]);

  // ── Send a new turn. ─────────────────────────────────────────────────
  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || sending) return;
    Keyboard.dismiss();

    const userMsg: Message = {
      id: `u_${Date.now()}`,
      role: 'user',
      content: text,
      ts: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const resp = await api.post(`/forums/${forumId}/mirror-chat`, {
        user_id: userId,
        forum_id: forumId,
        message: text,
        session_id: sessionId,
        include_history: true,
      });
      const data = resp?.data || {};
      const aiMsg: Message = {
        id: `a_${Date.now()}`,
        role: 'assistant',
        content: data.response || '',
        ts: data.timestamp || new Date().toISOString(),
        evidence: (data.evidence as CuratedEvidence | null) || null,
      };
      if (data.session_id && !sessionId) setSessionId(data.session_id);
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          id: `e_${Date.now()}`,
          role: 'error',
          content:
            'The room felt a little quiet just now — try once more in a moment.',
          ts: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
      // Scroll-to-end after layout.
      setTimeout(() => {
        listRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [input, sending, userId, forumId, sessionId]);

  // ── Empty state seed prompts. ────────────────────────────────────────
  const seedPress = (seed: string) => {
    setInput(seed);
  };

  // ── Render an individual message. ────────────────────────────────────
  const renderItem = ({ item, index }: { item: Message; index: number }) => {
    if (item.role === 'user') {
      return (
        <View style={[styles.userBubbleWrap]}>
          <View
            style={[
              styles.userBubble,
              { backgroundColor: theme.surface, borderColor: theme.border },
            ]}
          >
            <Text style={[styles.userText, { color: theme.text }]}>
              {item.content}
            </Text>
          </View>
        </View>
      );
    }

    if (item.role === 'error') {
      return (
        <View style={styles.assistantWrap}>
          <Text style={[styles.assistantText, { color: theme.textTertiary, fontStyle: 'italic' }]}>
            {item.content}
          </Text>
        </View>
      );
    }

    // assistant
    const isLatestAssistant =
      index === messages.length - 1 ||
      messages
        .slice(index + 1)
        .every((m) => m.role !== 'assistant');

    return (
      <View style={styles.assistantWrap}>
        <Text style={[styles.assistantText, { color: theme.text }]}>
          {item.content}
        </Text>
        {item.evidence && (
          <EvidenceDrawer
            evidence={item.evidence}
            title="What the room is showing"
          />
        )}
        <MicroReflectionBar
          userId={userId}
          source="other"
          isLatest={isLatestAssistant}
          sourceSession={sessionId}
          sourceMessage={item.id}
        />
      </View>
    );
  };

  // ── Empty state. ─────────────────────────────────────────────────────
  const renderEmpty = () => {
    if (loadingHistory) {
      return (
        <View style={styles.emptyWrap}>
          <ActivityIndicator size="small" color={theme.textTertiary} />
          <Text style={[styles.emptyText, { color: theme.textTertiary }]}>
            Listening to the room…
          </Text>
        </View>
      );
    }
    return (
      <View style={styles.emptyWrap}>
        <Text style={[styles.emptyTitle, { color: theme.text }]}>
          Talk to the room.
        </Text>
        <Text style={[styles.emptySub, { color: theme.textSecondary }]}>
          Field-level reflections. No diagnosis. No naming.{'\n'}Ask what's
          softening, what keeps circling, what feels unspoken.
        </Text>
        <View style={styles.seedRow}>
          {SEED_PROMPTS.map((s) => (
            <TouchableOpacity
              key={s}
              activeOpacity={0.7}
              onPress={() => seedPress(s)}
              style={[
                styles.seedChip,
                { borderColor: theme.border, backgroundColor: theme.surface },
              ]}
            >
              <Text style={[styles.seedText, { color: theme.textSecondary }]}>
                {s}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? insets.top + 50 : 0}
      style={{ flex: 1 }}
    >
      <FlatList
        ref={listRef}
        data={messages}
        keyExtractor={(m) => m.id}
        renderItem={renderItem}
        ListEmptyComponent={renderEmpty}
        contentContainerStyle={[
          styles.listContent,
          { paddingBottom: insets.bottom + 110 },
        ]}
        onContentSizeChange={() =>
          listRef.current?.scrollToEnd({ animated: false })
        }
        keyboardShouldPersistTaps="handled"
      />

      <View
        style={[
          styles.composer,
          {
            backgroundColor: theme.background,
            borderTopColor: theme.border,
            paddingBottom: Math.max(insets.bottom, 12),
          },
        ]}
      >
        <TextInput
          style={[
            styles.input,
            { color: theme.text, backgroundColor: theme.surface, borderColor: theme.border },
          ]}
          placeholder="What do you notice in the room?"
          placeholderTextColor={theme.textTertiary}
          value={input}
          onChangeText={setInput}
          multiline
          editable={!sending}
          maxLength={2000}
        />
        <TouchableOpacity
          onPress={send}
          disabled={sending || !input.trim()}
          activeOpacity={0.7}
          style={[
            styles.sendBtn,
            {
              borderColor: theme.border,
              backgroundColor: input.trim() && !sending ? theme.text : 'transparent',
              opacity: sending || !input.trim() ? 0.5 : 1,
            },
          ]}
          accessibilityRole="button"
          accessibilityLabel="Send"
        >
          {sending ? (
            <ActivityIndicator size="small" color={theme.background} />
          ) : (
            <Ionicons
              name="arrow-up"
              size={18}
              color={input.trim() ? theme.background : theme.textTertiary}
            />
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

// ---------------------------------------------------------------------------
// Styles — quiet, generous spacing, no chrome.
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  listContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 24,
    gap: 18,
  },

  // Empty state
  emptyWrap: {
    paddingTop: 40,
    paddingHorizontal: 8,
    gap: 14,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    letterSpacing: -0.3,
  },
  emptySub: {
    fontSize: 14,
    lineHeight: 21,
  },
  emptyText: {
    fontSize: 12,
    fontStyle: 'italic',
    marginTop: 8,
  },
  seedRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 10,
  },
  seedChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: StyleSheet.hairlineWidth,
  },
  seedText: {
    fontSize: 12.5,
    letterSpacing: 0.1,
  },

  // User bubble
  userBubbleWrap: {
    alignItems: 'flex-end',
    marginVertical: 4,
  },
  userBubble: {
    maxWidth: '85%',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
  },
  userText: {
    fontSize: 15,
    lineHeight: 22,
  },

  // Assistant — no bubble, just spacious text (journal feel).
  assistantWrap: {
    paddingVertical: 8,
    gap: 6,
  },
  assistantText: {
    fontSize: 15.5,
    lineHeight: 24,
  },

  // Composer
  composer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingTop: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  input: {
    flex: 1,
    minHeight: 42,
    maxHeight: 120,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
    fontSize: 15,
    lineHeight: 20,
  },
  sendBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: StyleSheet.hairlineWidth,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
