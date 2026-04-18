// =========================================================================
// Pattern Running Me V2 — "Share Forum Update" 4-step flow
// =========================================================================
// Route: /forums/pattern-running-me?forumId=...
// Contract (see backend services/pattern_running_me_v2.py):
//   1. Title  (1 line, max 80 chars)
//   2. Emotions (multi-select, max 3, from fixed vocab of 10)
//   3. Story  (free text)
//   4. Guided reflection (appears AFTER the user starts typing the story):
//        a) What does this say about you?
//        b) Why does this matter to you?
//        c) How is this affecting you?
// =========================================================================

import React, { useEffect, useMemo, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { Stack, useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import api from '../../services/api';

const TITLE_MAX = 80;
const STORY_MAX = 5000;

// Fallback emotion vocab — also fetched live from the backend to guarantee
// parity with the canonical list.
const FALLBACK_EMOTIONS = [
  'Frustrated',
  'Anxious',
  'Overwhelmed',
  'Pressured',
  'Avoidant',
  'Disconnected',
  'Conflicted',
  'Energized',
  'Clear',
  'Hopeful',
];

export default function PatternRunningMeScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ forumId?: string }>();
  const { theme } = useTheme();
  const { user } = useAppStore();
  const insets = useSafeAreaInsets();

  const forumId = typeof params.forumId === 'string' ? params.forumId : undefined;

  // ---------- state ----------
  const [emotions, setEmotions] = useState<string[]>(FALLBACK_EMOTIONS);
  const [title, setTitle] = useState('');
  const [selectedEmotions, setSelectedEmotions] = useState<string[]>([]);
  const [story, setStory] = useState('');
  const [meaning, setMeaning] = useState('');
  const [importance, setImportance] = useState('');
  const [impact, setImpact] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Load canonical emotion vocab from backend
  useEffect(() => {
    let cancelled = false;
    api
      .get('/pattern-running-me/emotions')
      .then((r) => {
        if (!cancelled && Array.isArray(r.data?.emotions)) setEmotions(r.data.emotions);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  // ---------- derived ----------
  const storyStarted = story.trim().length >= 3;
  const canSubmit =
    title.trim().length > 0 &&
    selectedEmotions.length >= 1 &&
    story.trim().length > 0 &&
    !submitting;

  const toggleEmotion = (e: string) => {
    setSelectedEmotions((prev) => {
      if (prev.includes(e)) return prev.filter((x) => x !== e);
      if (prev.length >= 3) return prev; // cap at 3
      return [...prev, e];
    });
  };

  const submit = async () => {
    if (!canSubmit || !user?.id) return;
    setSubmitting(true);
    try {
      await api.post(
        `/pattern-running-me?user_id=${encodeURIComponent(user.id)}`,
        {
          title: title.trim(),
          emotions: selectedEmotions,
          story: story.trim(),
          reflection: {
            meaning: meaning.trim(),
            importance: importance.trim(),
            impact: impact.trim(),
          },
          forum_id: forumId || null,
          visibility: forumId ? 'forum' : 'private',
        }
      );
      router.back();
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Could not save. Try again.';
      Alert.alert('Something got in the way', msg);
    } finally {
      setSubmitting(false);
    }
  };

  const titleRemaining = useMemo(() => TITLE_MAX - title.length, [title]);

  // ---------- render ----------
  return (
    <View style={[styles.container, { backgroundColor: theme.background, paddingTop: insets.top }]}>
      <Stack.Screen options={{ headerShown: false }} />

      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity onPress={() => router.back()} style={styles.headerBtn}>
          <Text style={[styles.headerBtnText, { color: theme.textSecondary }]}>Cancel</Text>
        </TouchableOpacity>
        <Text style={[styles.headerTitle, { color: theme.text }]}>
          The pattern running me
        </Text>
        <TouchableOpacity
          onPress={submit}
          disabled={!canSubmit}
          style={[
            styles.headerSubmit,
            { backgroundColor: canSubmit ? theme.accent : theme.border },
          ]}
        >
          {submitting ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.headerSubmitText}>Share</Text>
          )}
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + 40 }]}
          keyboardShouldPersistTaps="handled"
        >
          {/* ============================================ */}
          {/* STEP 1 — TITLE */}
          {/* ============================================ */}
          <View style={styles.section}>
            <Text style={[styles.stepLabel, { color: theme.textTertiary }]}>
              STEP 1 · TITLE
            </Text>
            <TextInput
              style={[
                styles.titleInput,
                { color: theme.text, borderColor: theme.border, backgroundColor: theme.surface },
              ]}
              value={title}
              onChangeText={(t) => setTitle(t.slice(0, TITLE_MAX))}
              placeholder="One line. What's running you?"
              placeholderTextColor={theme.textTertiary}
              maxLength={TITLE_MAX}
            />
            <Text style={[styles.counter, { color: theme.textTertiary }]}>
              {titleRemaining} characters left
            </Text>
          </View>

          {/* ============================================ */}
          {/* STEP 2 — EMOTIONS */}
          {/* ============================================ */}
          <View style={styles.section}>
            <Text style={[styles.stepLabel, { color: theme.textTertiary }]}>
              STEP 2 · EMOTIONS · {selectedEmotions.length}/3
            </Text>
            <Text style={[styles.helper, { color: theme.textSecondary }]}>
              Pick up to 3 that fit.
            </Text>
            <View style={styles.chipRow}>
              {emotions.map((e) => {
                const selected = selectedEmotions.includes(e);
                const atCap = !selected && selectedEmotions.length >= 3;
                return (
                  <TouchableOpacity
                    key={e}
                    onPress={() => toggleEmotion(e)}
                    disabled={atCap}
                    activeOpacity={0.7}
                    style={[
                      styles.chip,
                      {
                        borderColor: selected ? theme.accent : theme.border,
                        backgroundColor: selected ? theme.accent + '22' : theme.surface,
                        opacity: atCap ? 0.4 : 1,
                      },
                    ]}
                  >
                    <Text
                      style={[
                        styles.chipText,
                        { color: selected ? theme.accent : theme.textSecondary },
                      ]}
                    >
                      {e}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>

          {/* ============================================ */}
          {/* STEP 3 — STORY */}
          {/* ============================================ */}
          <View style={styles.section}>
            <Text style={[styles.stepLabel, { color: theme.textTertiary }]}>
              STEP 3 · STORY
            </Text>
            <Text style={[styles.helper, { color: theme.textSecondary }]}>
              What happened? Just write it as it happened.
            </Text>
            <TextInput
              style={[
                styles.storyInput,
                { color: theme.text, borderColor: theme.border, backgroundColor: theme.surface },
              ]}
              value={story}
              onChangeText={(t) => setStory(t.slice(0, STORY_MAX))}
              placeholder="Start here…"
              placeholderTextColor={theme.textTertiary}
              multiline
              textAlignVertical="top"
            />
          </View>

          {/* ============================================ */}
          {/* STEP 4 — GUIDED REFLECTION (appears after user starts typing) */}
          {/* ============================================ */}
          {storyStarted ? (
            <View style={styles.section}>
              <Text style={[styles.stepLabel, { color: theme.textTertiary }]}>
                STEP 4 · REFLECTION
              </Text>

              <Text style={[styles.reflectionPrompt, { color: theme.text }]}>
                What does this say about you?
              </Text>
              <TextInput
                style={[
                  styles.reflectionInput,
                  { color: theme.text, borderColor: theme.border, backgroundColor: theme.surface },
                ]}
                value={meaning}
                onChangeText={setMeaning}
                placeholder="Write what surfaces…"
                placeholderTextColor={theme.textTertiary}
                multiline
                textAlignVertical="top"
              />

              <Text style={[styles.reflectionPrompt, { color: theme.text }]}>
                Why does this matter to you?
              </Text>
              <TextInput
                style={[
                  styles.reflectionInput,
                  { color: theme.text, borderColor: theme.border, backgroundColor: theme.surface },
                ]}
                value={importance}
                onChangeText={setImportance}
                placeholder="Name the weight of it…"
                placeholderTextColor={theme.textTertiary}
                multiline
                textAlignVertical="top"
              />

              <Text style={[styles.reflectionPrompt, { color: theme.text }]}>
                How is this affecting you?
              </Text>
              <TextInput
                style={[
                  styles.reflectionInput,
                  { color: theme.text, borderColor: theme.border, backgroundColor: theme.surface },
                ]}
                value={impact}
                onChangeText={setImpact}
                placeholder="What's it costing, changing, or opening…"
                placeholderTextColor={theme.textTertiary}
                multiline
                textAlignVertical="top"
              />
            </View>
          ) : null}

          {/* Primary submit button (sticky-feeling at the bottom of the scroll) */}
          <TouchableOpacity
            onPress={submit}
            disabled={!canSubmit}
            activeOpacity={0.85}
            style={[
              styles.primaryBtn,
              { backgroundColor: canSubmit ? theme.accent : theme.border },
            ]}
          >
            {submitting ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.primaryBtnText}>
                {forumId ? 'Share with this circle' : 'Save privately'}
              </Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  flex: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerBtn: { padding: 4 },
  headerBtnText: { fontSize: 15 },
  headerTitle: { fontSize: 16, fontWeight: '700' },
  headerSubmit: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    minWidth: 64,
    alignItems: 'center',
  },
  headerSubmitText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  scroll: { padding: 16, paddingBottom: 60 },
  section: { marginBottom: 24 },
  stepLabel: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1,
    marginBottom: 8,
  },
  helper: { fontSize: 13, marginBottom: 10, lineHeight: 18 },
  titleInput: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    fontSize: 16,
  },
  counter: { fontSize: 11, marginTop: 6, textAlign: 'right' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 4 },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 18,
    borderWidth: 1,
  },
  chipText: { fontSize: 13, fontWeight: '600' },
  storyInput: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
    minHeight: 140,
    fontSize: 15,
    lineHeight: 22,
  },
  reflectionPrompt: { fontSize: 14, fontWeight: '700', marginTop: 14, marginBottom: 6 },
  reflectionInput: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    minHeight: 80,
    fontSize: 14,
    lineHeight: 20,
  },
  primaryBtn: {
    marginTop: 8,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryBtnText: { color: '#fff', fontWeight: '700', fontSize: 15 },
});
