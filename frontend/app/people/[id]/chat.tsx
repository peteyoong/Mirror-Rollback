/**
 * Ask About [Name] — focused relational chat surface (ask-about-person-v1)
 * ========================================================================
 *
 * Lives at `/people/[id]/chat`.  Opens from the "Ask about this person"
 * button on the Relationship Profile page.
 *
 * v1 scope:
 *   - Calls `POST /api/mirror/chat` with `about_person_id` set so the
 *     backend Relational Awareness Layer (relational-awareness-v1)
 *     activates: relationship class, projection-risk detection, intensity
 *     ceiling per class.
 *   - Preserves conversational continuity across turns via `session_id`.
 *   - Lets the user pick a lens: Mirror (generalist, default), Astrology,
 *     Human Design, Numerology, Enneagram, BaZi — only the ones we have
 *     data to support for THIS person are pre-enabled; the rest are
 *     selectable but the backend is honest about missing data.
 *   - Shows a compact debug pill at the bottom (markers + compression +
 *     intensity) when EXPO_PUBLIC_DEBUG_MIRROR=true.
 *
 * NB: we deliberately do NOT use the huge `components/MirrorChat.tsx`
 * shell here.  That one is loaded with surfaces (journals, keystone,
 * dominant truth, memory expander) that aren't appropriate for a focused
 * person-scoped chat.  This screen is intentionally lean and only the
 * Mirror Chat backend pipeline is reused — which is the whole point of
 * relational-awareness-v1 living server-side.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
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
import {
  formatRelationshipType,
  friendlyPeopleError,
  getSavedPerson,
  SavedPerson,
} from '../../../services/people';
import { useAppStore } from '../../../store';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type LensKey = null | 'astrology' | 'human_design' | 'numerology' | 'enneagram' | 'bazi';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  timestamp: Date;
}

interface RelationalDebug {
  relationship_class?: string;
  relationship_type?: string;
  intensity_ceiling?: string;
  projection_risk?: string | boolean;
  applied_intensity?: string;
}

interface PatternMemoryDebug {
  marker?: string;
  matched_patterns?: Array<{ pattern_key?: string; confidence?: string }>;
  surfaceable_count?: number;
  growth_shifts_count?: number;
  surfaced_keys?: string[];
  growth_keys?: string[];
  suppressed_due_to_fatigue?: string[];
  softened_due_to_fatigue?: string[];
}

interface MirrorDebug {
  compression_mode?: string;
  intensity_mode?: string;
  active_entity?: string;
  relational?: RelationalDebug;
  pattern_memory?: PatternMemoryDebug;
  // emotional-timing-v1 markers may live at top-level or inside lens
  emotional_timing_marker?: string;
}

// ---------------------------------------------------------------------------
// Lens chip metadata
// ---------------------------------------------------------------------------

const LENS_LABELS: { key: LensKey; label: string }[] = [
  { key: null, label: 'Mirror' },
  { key: 'astrology', label: 'Astrology' },
  { key: 'human_design', label: 'Human Design' },
  { key: 'numerology', label: 'Numerology' },
  { key: 'enneagram', label: 'Enneagram' },
  { key: 'bazi', label: 'BaZi' },
];

function availableLensesForPerson(p: SavedPerson | null): LensKey[] {
  if (!p) return [null];
  const supported: LensKey[] = [null]; // Mirror is always available
  if (p.birth_date) {
    supported.push('astrology', 'numerology', 'bazi');
  }
  if (p.birth_date && p.birth_time_accuracy === 'exact') {
    supported.push('human_design');
  }
  if (p.enneagram_type) {
    supported.push('enneagram');
  }
  return supported;
}

// ---------------------------------------------------------------------------
// Screen
// ---------------------------------------------------------------------------

export default function AskAboutPersonChatScreen() {
  const { theme, isDark } = useTheme();
  const router = useRouter();
  const params = useLocalSearchParams<{ id: string }>();
  const personId = String(params.id || '');
  const user = useAppStore((s) => s.user);

  const [person, setPerson] = useState<SavedPerson | null>(null);
  const [loading, setLoading] = useState(true);
  const [personError, setPersonError] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [lens, setLens] = useState<LensKey>(null); // default = Mirror/generalist
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [lastDebug, setLastDebug] = useState<MirrorDebug | null>(null);

  const listRef = useRef<FlatList<ChatMessage>>(null);

  // -------------------------------------------------------------------------
  // Load person on mount
  // -------------------------------------------------------------------------
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!user?.id || !personId) return;
      setLoading(true);
      setPersonError(null);
      try {
        const p = await getSavedPerson(user.id, personId);
        if (!cancelled) setPerson(p);
      } catch (e) {
        if (!cancelled) setPersonError(friendlyPeopleError(e));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user?.id, personId]);

  // -------------------------------------------------------------------------
  // Stable session id (one per visit) — kept client-side; the backend will
  // also persist sessions but we lock continuity here so even if the user
  // switches lens mid-thread the same session_id is reused.
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!sessionId && personId) {
      setSessionId(
        `ask-${personId}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
      );
    }
  }, [sessionId, personId]);

  const supportedLenses = useMemo(() => availableLensesForPerson(person), [person]);

  // -------------------------------------------------------------------------
  // Send a turn
  // -------------------------------------------------------------------------
  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || sending || !user?.id || !personId || !sessionId || !person) return;

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
        lens: lens, // null = Mirror generalist; backend supports the rest
        session_id: sessionId,
        include_journal: true,
        include_history: true, // backend uses this to thread continuity
        about_person_id: personId, // <-- the key relational signal
      };

      const resp = await api.post('/mirror/chat', payload);
      const data = resp?.data ?? {};

      const assistantText: string =
        typeof data.response === 'string' && data.response.length > 0
          ? data.response
          : "I'm here. Could you say a little more about what's on your mind?";

      const asstMsg: ChatMessage = {
        id: `a-${Date.now()}`,
        role: 'assistant',
        content: assistantText,
        timestamp: new Date(data.timestamp || Date.now()),
      };
      setMessages((prev) => [...prev, asstMsg]);

      // Capture debug for dev pill.
      if (data.debug && typeof data.debug === 'object') {
        setLastDebug(data.debug as MirrorDebug);
      }

      // Honour the backend session_id if returned (keeps continuity stable).
      if (typeof data.session_id === 'string' && data.session_id.length > 0) {
        setSessionId(data.session_id);
      }
    } catch (e: any) {
      console.error('[AskAboutPerson] chat error:', e);
      const errMsg: ChatMessage = {
        id: `e-${Date.now()}`,
        role: 'error',
        content:
          e?.response?.data?.detail ||
          e?.message ||
          'Mirror could not reach the relational layer just now. Try again in a moment.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 80);
    }
  }, [input, sending, user?.id, personId, sessionId, lens, person]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------
  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.centered}>
          <ActivityIndicator color={theme.text} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Opening the line…
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (personError || !person) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.headerBar}>
          <TouchableOpacity
            onPress={() => router.back()}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.centered}>
          <Text style={[styles.errorText, { color: theme.text }]}>
            {personError || 'Profile not found.'}
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  const lensSubtitle = supportedLenses
    .map((l) => LENS_LABELS.find((x) => x.key === l)?.label)
    .filter(Boolean)
    .join(' · ');

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <StatusBar style={isDark ? 'light' : 'dark'} />

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
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
            <Text style={[styles.headerTitle, { color: theme.text }]} numberOfLines={1}>
              Ask about {person.name}
            </Text>
            <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]} numberOfLines={1}>
              {formatRelationshipType(person.relationship_type)}
              {lensSubtitle ? ` · ${lensSubtitle}` : ''}
            </Text>
          </View>
          <View style={{ width: 50 }} />
        </View>

        {/* ─── Lens selector ──────────────────────────────────────────── */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.lensRow}
          contentContainerStyle={styles.lensRowContent}
        >
          {LENS_LABELS.map((l) => {
            const active = l.key === lens;
            const supported = supportedLenses.includes(l.key);
            return (
              <TouchableOpacity
                key={l.label}
                onPress={() => setLens(l.key)}
                style={[
                  styles.lensChip,
                  {
                    borderColor: active ? theme.accent : theme.border,
                    backgroundColor: active ? theme.accent + '15' : theme.surface,
                  },
                ]}
                activeOpacity={0.7}
                accessibilityRole="button"
                accessibilityLabel={`Use ${l.label} lens`}
              >
                <Text
                  style={[
                    styles.lensChipText,
                    {
                      color: active
                        ? theme.accent
                        : supported
                        ? theme.text
                        : theme.textTertiary,
                      fontWeight: active ? '600' : '500',
                    },
                  ]}
                >
                  {l.label}
                  {!supported ? ' *' : ''}
                </Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>

        {/* ─── Message list ───────────────────────────────────────────── */}
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(m) => m.id}
          style={styles.list}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={
            <View style={[styles.openerCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.openerTitle, { color: theme.text }]}>
                A private line to Mirror about {person.name}.
              </Text>
              <Text style={[styles.openerBody, { color: theme.textSecondary }]}>
                Mirror will use what you have on file ({lensSubtitle || 'name + relationship'}) and
                stay honest about what it can and can't read.
              </Text>
              <Text style={[styles.openerHint, { color: theme.textTertiary }]}>
                Try: “What should I understand about them?” or “Why does this keep coming up
                between us?”
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
                    ? { backgroundColor: theme.accent + '22', borderColor: theme.accent + '55' }
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

        {/* ─── Debug pill (dev only) ──────────────────────────────────── */}
        {process.env.EXPO_PUBLIC_DEBUG_MIRROR === 'true' && lastDebug && (
          <DebugPill debug={lastDebug} theme={theme} />
        )}

        {/* ─── Composer ───────────────────────────────────────────────── */}
        <View style={[styles.composer, { backgroundColor: theme.background, borderTopColor: theme.border }]}>
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
            placeholder={`Ask about ${person.name}…`}
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
                backgroundColor: !input.trim() || sending ? theme.border : theme.buttonPrimaryBg,
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
// Debug pill — compact view of the relational + memory layers that just fired.
// ---------------------------------------------------------------------------

function DebugPill({ debug, theme }: { debug: MirrorDebug; theme: any }) {
  const rel = debug.relational;
  const pm = debug.pattern_memory;
  const markers: string[] = [];
  if (rel?.relationship_class) markers.push('relational-awareness-v1');
  if (pm?.marker) markers.push(pm.marker);
  if (debug.compression_mode) markers.push(`compression:${debug.compression_mode}`);
  if (debug.intensity_mode) markers.push(`intensity:${debug.intensity_mode}`);
  // emotional-timing-v1 is implicit when compression+intensity exist
  if (debug.compression_mode && debug.intensity_mode) markers.push('emotional-timing-v1');
  return (
    <View style={[styles.debugPill, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <Text style={[styles.debugTitle, { color: theme.textTertiary }]}>DEBUG</Text>
      <Text style={[styles.debugBody, { color: theme.textSecondary }]} numberOfLines={3}>
        {markers.join(' · ')}
        {rel?.relationship_class
          ? `\nclass: ${rel.relationship_class}${
              rel.intensity_ceiling ? ` (ceiling: ${rel.intensity_ceiling})` : ''
            }${rel.projection_risk ? ` · projection: ${rel.projection_risk}` : ''}`
          : ''}
        {pm?.matched_patterns && pm.matched_patterns.length > 0
          ? `\npatterns: ${pm.matched_patterns
              .map((p) => `${p.pattern_key}(${p.confidence})`)
              .join(', ')}`
          : ''}
        {pm?.growth_keys && pm.growth_keys.length > 0
          ? `\ngrowth: ${pm.growth_keys.join(', ')}`
          : ''}
        {pm?.softened_due_to_fatigue && pm.softened_due_to_fatigue.length > 0
          ? `\nsoftened: ${pm.softened_due_to_fatigue.join(', ')}`
          : ''}
        {pm?.suppressed_due_to_fatigue && pm.suppressed_due_to_fatigue.length > 0
          ? `\nsuppressed: ${pm.suppressed_due_to_fatigue.join(', ')}`
          : ''}
      </Text>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1 },
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10, padding: 20 },
  loadingText: { fontSize: 14 },
  errorText: { fontSize: 15, textAlign: 'center', paddingHorizontal: 24 },

  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: 8,
  },
  backText: { fontSize: 15, fontWeight: '500', width: 50 },
  headerCenter: { flex: 1, alignItems: 'center' },
  headerTitle: { fontSize: 16, fontWeight: '600' },
  headerSubtitle: { fontSize: 11, marginTop: 2 },

  lensRow: { flexGrow: 0, maxHeight: 48, paddingVertical: 6 },
  lensRowContent: { paddingHorizontal: 16, gap: 8, alignItems: 'center' },
  lensChip: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 999,
    borderWidth: 1,
    minHeight: 32,
    justifyContent: 'center',
  },
  lensChipText: { fontSize: 12 },

  list: { flex: 1 },
  listContent: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 16, gap: 8 },

  openerCard: { borderWidth: 1, borderRadius: 14, padding: 16, marginTop: 12 },
  openerTitle: { fontSize: 15, fontWeight: '600', marginBottom: 8 },
  openerBody: { fontSize: 14, lineHeight: 21, marginBottom: 12 },
  openerHint: { fontSize: 12, lineHeight: 18, fontStyle: 'italic' },

  bubbleRow: { width: '100%', flexDirection: 'row' },
  bubbleRowLeft: { justifyContent: 'flex-start' },
  bubbleRowRight: { justifyContent: 'flex-end' },
  bubble: {
    maxWidth: '88%',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 14,
    borderWidth: 1,
  },
  bubbleText: { fontSize: 15, lineHeight: 22 },

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
  debugBody: { fontSize: 11, lineHeight: 15, fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace', default: 'monospace' }) },

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
