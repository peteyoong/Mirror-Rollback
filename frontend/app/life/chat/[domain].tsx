/**
 * Life Tab Master Voice — focused multi-turn chat surface
 * =======================================================
 *
 * Lives at `/life/chat/[domain]` where domain ∈ {relationships, work, self}.
 *
 * This is the deep-reflection counterpart to the lightweight
 * `AskAboutLifeModal`.  Different product surface, different posture:
 *
 *   AskAboutLifeModal     →  micro-reflection, one-shot, fast probing.
 *   /life/chat/[domain]   →  longitudinal reflective conversation, with
 *                            full memory continuity, compression, intensity,
 *                            relational awareness, pattern memory and
 *                            anti-identity-locking applied behind the scenes.
 *
 * Voice is INTEGRATIVE.  No lens chips.  No "Astrology says X / HD says Y."
 * Framework names are hidden by default; if the user asks "why is this
 * showing up?", the backend voice prompt unlocks framework provenance.
 *
 * Calls `POST /api/mirror/chat` with the new `life_domain` field.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { useTheme } from '../../../contexts/ThemeContext';
import { BUILD_ID } from '../../../constants/buildMarker';
import api from '../../../services/api';
import { useAppStore } from '../../../store';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type LifeDomain = 'relationships' | 'work' | 'self';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  timestamp: Date;
}

interface MasterVoiceDebug {
  marker?: string;
  domain?: string;
  contributing_frameworks?: string[];
  signals_count?: number;
  dominant_signal?: { framework?: string; signal?: string; why?: string } | null;
  depth_mode?: string;
  intensity_mode?: string;
}

interface PatternMemoryDebug {
  marker?: string;
  matched_patterns?: Array<{ pattern_key?: string; confidence?: string }>;
  growth_keys?: string[];
  softened_due_to_fatigue?: string[];
  suppressed_due_to_fatigue?: string[];
}

interface MirrorDebug {
  compression_mode?: string;
  intensity_mode?: string;
  master_voice?: MasterVoiceDebug;
  pattern_memory?: PatternMemoryDebug;
  relational?: { relationship_class?: string };
}

// ---------------------------------------------------------------------------
// Per-domain voice copy (UI-side cues; the actual stance lives backend-side)
// ---------------------------------------------------------------------------

const DOMAIN_META: Record<LifeDomain, {
  title: string;
  subtitle: string;
  opener: string;
  placeholder: string;
}> = {
  relationships: {
    title: 'Relationships',
    subtitle: 'A quiet line for the field between you and the people in your life.',
    opener:
      "Anything alive in your relationships right now? — a friction that keeps returning, a closeness that's shifting, a pattern you notice in yourself.",
    placeholder: 'What\u2019s present for you, relationally?',
  },
  work: {
    title: 'Work',
    subtitle: 'Pressure, capacity, ambition, meaning — the structure you live inside.',
    opener:
      "What's the texture of your work right now? Where is the pressure landing — and what part of you is carrying it?",
    placeholder: 'What\u2019s happening in your work?',
  },
  self: {
    title: 'Self',
    subtitle: 'The inner weather. What\u2019s organising, what\u2019s loosening.',
    opener:
      "What's surfacing in you right now? Even one line is enough to start.",
    placeholder: 'What\u2019s alive in you right now?',
  },
};

function isValidDomain(d: string): d is LifeDomain {
  return d === 'relationships' || d === 'work' || d === 'self';
}

// ---------------------------------------------------------------------------
// Screen
// ---------------------------------------------------------------------------

export default function LifeMasterVoiceChat() {
  const { theme, isDark } = useTheme();
  const router = useRouter();
  const params = useLocalSearchParams<{ domain: string }>();
  const rawDomain = String(params.domain || 'self');
  const domain: LifeDomain = isValidDomain(rawDomain) ? rawDomain : 'self';

  const user = useAppStore((s) => s.user);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [lastDebug, setLastDebug] = useState<MirrorDebug | null>(null);

  const listRef = useRef<FlatList<ChatMessage>>(null);

  // Stable session id (one per visit).
  useEffect(() => {
    if (!sessionId) {
      setSessionId(
        `life-${domain}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
      );
    }
  }, [sessionId, domain]);

  const meta = useMemo(() => DOMAIN_META[domain], [domain]);

  // -------------------------------------------------------------------------
  // Send a turn
  // -------------------------------------------------------------------------
  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || sending || !user?.id || !sessionId) return;

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 50);

    try {
      const payload = {
        user_id: user.id,
        message: trimmed,
        lens: null,
        session_id: sessionId,
        include_journal: true,
        include_history: true,
        life_domain: domain,
      };

      const resp = await api.post('/mirror/chat', payload);
      const data = resp?.data ?? {};

      const assistantText: string =
        typeof data.response === 'string' && data.response.length > 0
          ? data.response
          : "I'm here. Take your time — say a little more when you're ready.";

      const asstMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: assistantText,
        timestamp: new Date(data.timestamp || Date.now()),
      };
      setMessages((prev) => [...prev, asstMsg]);

      if (data.debug && typeof data.debug === 'object') {
        setLastDebug(data.debug as MirrorDebug);
      }
      if (typeof data.session_id === 'string' && data.session_id.length > 0) {
        setSessionId(data.session_id);
      }
    } catch (e: any) {
      console.error('[LifeMasterVoiceChat] error:', e);
      const errMsg: ChatMessage = {
        id: `e-${Date.now()}`,
        role: 'error',
        content:
          e?.response?.data?.detail ||
          e?.message ||
          'Mirror could not reach the field just now. Try again in a moment.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
    }
  }, [input, sending, user?.id, sessionId, domain]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <StatusBar style={isDark ? 'light' : 'dark'} />

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        {/* ─── Header ─────────────────────────────────────────────────── */}
        <View style={styles.headerBar}>
          <TouchableOpacity
            onPress={() => router.back()}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Text style={[styles.headerTitle, { color: theme.text }]}>{meta.title}</Text>
            <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]} numberOfLines={1}>
              Mirror · integrative reflection
            </Text>
          </View>
          <View style={{ width: 50 }} />
        </View>

        {/* ─── Messages ───────────────────────────────────────────────── */}
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(m) => m.id}
          style={styles.list}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View
              style={[
                styles.openerCard,
                { backgroundColor: theme.surface, borderColor: theme.border },
              ]}
            >
              <Text style={[styles.openerSubtitle, { color: theme.textSecondary }]}>
                {meta.subtitle}
              </Text>
              <Text style={[styles.openerBody, { color: theme.text }]}>
                {meta.opener}
              </Text>
            </View>
          }
          renderItem={({ item }) => (
            <View
              style={[
                styles.bubbleRow,
                item.role === 'user' ? styles.bubbleRowRight : styles.bubbleRowLeft,
              ]}
            >
              <View
                style={[
                  styles.bubble,
                  item.role === 'user'
                    ? {
                        backgroundColor: theme.accent + '20',
                        borderColor: theme.accent + '55',
                      }
                    : item.role === 'error'
                    ? { backgroundColor: '#FF3B3033', borderColor: '#FF3B30' }
                    : { backgroundColor: theme.surface, borderColor: theme.border },
                ]}
              >
                <Text style={[styles.bubbleText, { color: theme.text }]}>{item.content}</Text>
              </View>
            </View>
          )}
        />

        {sending && (
          <View style={styles.typingRow}>
            <ActivityIndicator size="small" color={theme.textTertiary} />
            <Text style={[styles.typingText, { color: theme.textTertiary }]}>
              Mirror is reading the field…
            </Text>
          </View>
        )}

        {process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true' && lastDebug && (
          <DebugPill debug={lastDebug} theme={theme} />
        )}

        {/* ─── Composer ───────────────────────────────────────────────── */}
        <View
          style={[
            styles.composer,
            { backgroundColor: theme.background, borderTopColor: theme.border },
          ]}
        >
          <TextInput
            style={[
              styles.input,
              {
                backgroundColor: theme.surface,
                borderColor: theme.border,
                color: theme.text,
              },
            ]}
            value={input}
            onChangeText={setInput}
            placeholder={meta.placeholder}
            placeholderTextColor={theme.textTertiary}
            multiline
            maxLength={1500}
            editable={!sending}
            blurOnSubmit={false}
            returnKeyType="default"
            onSubmitEditing={handleSend}
          />
          <TouchableOpacity
            onPress={handleSend}
            disabled={!input.trim() || sending}
            style={[
              styles.sendBtn,
              {
                backgroundColor:
                  !input.trim() || sending ? theme.border : theme.buttonPrimaryBg,
              },
            ]}
            accessibilityRole="button"
            accessibilityLabel="Send message"
          >
            <Text style={[styles.sendText, { color: theme.buttonPrimaryText }]}>Send</Text>
          </TouchableOpacity>
        </View>

        <Text style={[styles.buildMarker, { color: theme.textTertiary }]}>{BUILD_ID}</Text>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ---------------------------------------------------------------------------
// Debug pill — dev-only summary of which layers fired
// ---------------------------------------------------------------------------

function DebugPill({ debug, theme }: { debug: MirrorDebug; theme: any }) {
  const mv = debug.master_voice;
  const pm = debug.pattern_memory;
  const markers: string[] = [];
  if (mv?.marker) markers.push(mv.marker);
  if (pm?.marker) markers.push(pm.marker);
  if (debug.relational?.relationship_class) markers.push('relational-awareness-v1');
  if (debug.compression_mode) markers.push(`compression:${debug.compression_mode}`);
  if (debug.intensity_mode) markers.push(`intensity:${debug.intensity_mode}`);
  if (debug.compression_mode && debug.intensity_mode) markers.push('emotional-timing-v1');
  return (
    <View style={[styles.debugPill, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <Text style={[styles.debugTitle, { color: theme.textTertiary }]}>DEBUG</Text>
      <Text style={[styles.debugBody, { color: theme.textSecondary }]} numberOfLines={5}>
        {markers.join(' · ')}
        {mv?.domain ? `\ndomain: ${mv.domain}` : ''}
        {mv?.contributing_frameworks && mv.contributing_frameworks.length > 0
          ? `\nframeworks: ${mv.contributing_frameworks.join(', ')}`
          : ''}
        {mv?.dominant_signal
          ? `\ndominant: ${mv.dominant_signal.framework} — ${mv.dominant_signal.why}`
          : ''}
        {pm?.matched_patterns && pm.matched_patterns.length > 0
          ? `\npatterns: ${pm.matched_patterns
              .map((p) => `${p.pattern_key}(${p.confidence})`)
              .join(', ')}`
          : ''}
        {pm?.growth_keys && pm.growth_keys.length > 0
          ? `\ngrowth: ${pm.growth_keys.join(', ')}`
          : ''}
      </Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles — calm, intimate, low-chrome
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1 },

  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: 10,
  },
  backText: { fontSize: 15, fontWeight: '500', width: 50 },
  headerCenter: { flex: 1, alignItems: 'center' },
  headerTitle: { fontSize: 17, fontWeight: '600', letterSpacing: -0.2 },
  headerSubtitle: { fontSize: 11, marginTop: 2, fontStyle: 'italic' },

  list: { flex: 1 },
  listContent: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 16, gap: 10 },

  openerCard: {
    borderWidth: 1,
    borderRadius: 16,
    padding: 18,
    marginTop: 16,
  },
  openerSubtitle: { fontSize: 12, marginBottom: 12, lineHeight: 18, letterSpacing: 0.2 },
  openerBody: { fontSize: 16, lineHeight: 24 },

  bubbleRow: { width: '100%', flexDirection: 'row' },
  bubbleRowLeft: { justifyContent: 'flex-start' },
  bubbleRowRight: { justifyContent: 'flex-end' },
  bubble: {
    maxWidth: '88%',
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderRadius: 16,
    borderWidth: 1,
  },
  bubbleText: { fontSize: 15, lineHeight: 23 },

  typingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 20,
    paddingVertical: 6,
  },
  typingText: { fontSize: 12, fontStyle: 'italic' },

  debugPill: {
    marginHorizontal: 16,
    marginBottom: 6,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  debugTitle: { fontSize: 9, fontWeight: '700', letterSpacing: 1.5, marginBottom: 2 },
  debugBody: {
    fontSize: 11,
    lineHeight: 15,
    fontFamily: Platform.select({
      ios: 'Menlo',
      android: 'monospace',
      default: 'monospace',
    }),
  },

  composer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
    paddingTop: 8,
    paddingBottom: Platform.OS === 'ios' ? 8 : 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 140,
    paddingHorizontal: 14,
    paddingTop: 11,
    paddingBottom: 11,
    fontSize: 15,
    borderRadius: 22,
    borderWidth: 1,
  },
  sendBtn: {
    minWidth: 64,
    paddingHorizontal: 14,
    paddingVertical: 11,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendText: { fontSize: 14, fontWeight: '600' },

  buildMarker: {
    fontSize: 9,
    textAlign: 'center',
    paddingBottom: 6,
    letterSpacing: 0.6,
  },
});
