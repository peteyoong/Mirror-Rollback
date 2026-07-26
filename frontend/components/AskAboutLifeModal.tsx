import React, { useState, useRef, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  TouchableWithoutFeedback,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { askAboutLife, AskLifeChip } from '../services/api';
import ReflectModal from './ReflectModal';

/**
 * AskAboutLifeModal — conversational "ask about my life" surface.
 *
 * 7 chips → free-text question → grounded plain-text answer with 2-3
 * follow-up chips and a "✨ Reflect on this" CTA so the conversation can
 * keep moving without leaving the surface.
 */

interface Props {
  visible: boolean;
  onClose: () => void;
  userId: string;
  initialDomain?: AskLifeChip;
  /** Optional context for reflections opened from inside this modal. */
  phaseLabel?: string | null;
  patternHint?: string | null;
}

const CHIPS: { id: AskLifeChip; label: string }[] = [
  { id: 'self',          label: 'Self' },
  { id: 'work',          label: 'Work' },
  { id: 'money',         label: 'Money' },
  { id: 'relationships', label: 'Relationships' },
  { id: 'health',        label: 'Health' },
  { id: 'friends',       label: 'Friends' },
  { id: 'family',        label: 'Family' },
];

// Maps the 7 user-facing chips to the 3 reflection domains
// (kept in sync with backend _CHIP_TO_SYNTH_DOMAIN).
const CHIP_TO_REFLECT_DOMAIN: Record<AskLifeChip, 'self' | 'work' | 'relationships'> = {
  self:          'self',
  work:          'work',
  money:         'work',
  relationships: 'relationships',
  health:        'self',
  friends:       'relationships',
  family:        'relationships',
};

export default function AskAboutLifeModal({
  visible,
  onClose,
  userId,
  initialDomain,
  phaseLabel,
  patternHint,
}: Props) {
  const { theme } = useTheme();
  const [chip, setChip] = useState<AskLifeChip>(initialDomain || 'self');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [followUps, setFollowUps] = useState<string[]>([]);
  const [askedQuestion, setAskedQuestion] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reflectOpen, setReflectOpen] = useState(false);

  const scrollRef = useRef<ScrollView>(null);

  // Reset whenever the modal closes / reopens
  useEffect(() => {
    if (visible) {
      setChip(initialDomain || 'self');
    }
  }, [visible, initialDomain]);

  const reset = () => {
    setQuestion('');
    setAnswer(null);
    setFollowUps([]);
    setAskedQuestion(null);
    setError(null);
    setLoading(false);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  // Core request — accepts an optional override question (used by follow-up chips)
  const performAsk = async (q: string) => {
    Keyboard.dismiss();
    setLoading(true);
    setError(null);
    setAnswer(null);
    setFollowUps([]);
    setAskedQuestion(q);
    try {
      const resp = await askAboutLife(userId, { domain: chip, question: q });
      setAnswer(resp.answer || '');
      const fups = Array.isArray(resp.follow_ups) ? resp.follow_ups.filter(Boolean) : [];
      setFollowUps(fups.slice(0, 3));
      // Scroll the new answer into view shortly after render
      setTimeout(() => {
        scrollRef.current?.scrollToEnd({ animated: true });
      }, 80);
    } catch (e) {
      const msg = e && typeof e === 'object' && 'message' in e
        ? String((e as { message?: string }).message)
        : 'Could not load an answer.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleAsk = async () => {
    const q = question.trim();
    if (!q) {
      setError('Type a question first.');
      return;
    }
    await performAsk(q);
  };

  const handleFollowUpTap = async (q: string) => {
    if (loading) return;
    setQuestion(q);          // mirror the chip into the input for clarity
    await performAsk(q);
  };

  const handleReflectOnAnswer = () => {
    if (!answer) return;
    setReflectOpen(true);
  };

  const askDisabled = loading || !question.trim();

  // Build the prefilled reflection text — keeps the user's question and a short
  // excerpt of the answer so the captured thought stays anchored.
  const reflectInitialText = (() => {
    if (!answer) return '';
    const excerpt = answer.length > 280
      ? answer.slice(0, 280).replace(/\s+\S*$/, '') + '…'
      : answer;
    const qLine = askedQuestion ? `Q: ${askedQuestion}\n\n` : '';
    return `${qLine}${excerpt}\n\nWhat I'm noticing: `;
  })();

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={handleClose}>
      <View style={[styles.root, { backgroundColor: theme.background }]}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          {/* Header */}
          <View style={[styles.header, { borderBottomColor: theme.border }]}>
            <TouchableOpacity onPress={handleClose} hitSlop={10} activeOpacity={0.7}>
              <Text style={[styles.closeText, { color: theme.textSecondary }]}>Close</Text>
            </TouchableOpacity>
            <Text style={[styles.headerTitle, { color: theme.text }]}>Ask about your life</Text>
            <View style={{ width: 50 }} />
          </View>

          <ScrollView
            ref={scrollRef}
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={styles.scrollBody}
            showsVerticalScrollIndicator={false}
          >
            <Text style={[styles.subtle, { color: theme.textTertiary }]}>
              Pick a part of your life and ask anything you&apos;re sitting with.
            </Text>

            {/* Chip row */}
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.chipRow}
            >
              {CHIPS.map(c => {
                const active = c.id === chip;
                return (
                  <TouchableOpacity
                    key={c.id}
                    activeOpacity={0.7}
                    onPress={() => setChip(c.id)}
                    style={[
                      styles.chip,
                      {
                        backgroundColor: active ? theme.text : 'transparent',
                        borderColor: active ? theme.text : theme.border,
                      },
                    ]}
                  >
                    <Text
                      style={[
                        styles.chipText,
                        { color: active ? theme.background : theme.text },
                      ]}
                    >
                      {c.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </ScrollView>

            {/* Question input */}
            <TouchableWithoutFeedback>
              <View>
                <TextInput
                  style={[
                    styles.input,
                    {
                      color: theme.text,
                      backgroundColor: theme.surface,
                      borderColor: theme.border,
                    },
                  ]}
                  placeholder="What's on your mind?"
                  placeholderTextColor={theme.textTertiary}
                  multiline
                  numberOfLines={4}
                  textAlignVertical="top"
                  value={question}
                  onChangeText={(v) => {
                    setQuestion(v);
                    if (error) setError(null);
                  }}
                  maxLength={800}
                  editable={!loading}
                />
              </View>
            </TouchableWithoutFeedback>

            {!!error && (
              <Text style={[styles.error, { color: theme.error || '#C04848' }]}>
                {error}
              </Text>
            )}

            {/* CTA */}
            <TouchableOpacity
              activeOpacity={0.8}
              disabled={askDisabled}
              onPress={handleAsk}
              style={[
                styles.askBtn,
                {
                  backgroundColor: askDisabled ? theme.textTertiary : theme.text,
                  opacity: askDisabled ? 0.6 : 1,
                },
              ]}
            >
              {loading ? (
                <ActivityIndicator color={theme.background} />
              ) : (
                <Text style={[styles.askBtnText, { color: theme.background }]}>
                  Ask
                </Text>
              )}
            </TouchableOpacity>

            {/* Answer card */}
            {answer ? (
              <View
                style={[
                  styles.answerCard,
                  { backgroundColor: theme.surface, borderColor: theme.border },
                ]}
              >
                {answer.split(/\n\s*\n/).map((para, i) => (
                  <Text
                    key={i}
                    style={[
                      styles.answerPara,
                      { color: theme.text, marginBottom: 12 },
                    ]}
                  >
                    {para.trim()}
                  </Text>
                ))}

                {/* Reflect on this CTA */}
                <TouchableOpacity
                  onPress={handleReflectOnAnswer}
                  activeOpacity={0.75}
                  style={[
                    styles.reflectBtn,
                    {
                      borderColor: theme.border,
                      backgroundColor: 'transparent',
                    },
                  ]}
                >
                  <Text style={[styles.reflectBtnText, { color: theme.text }]}>
                    ✨ Reflect on this
                  </Text>
                </TouchableOpacity>
              </View>
            ) : null}

            {/* Follow-up chips */}
            {followUps.length > 0 ? (
              <View style={styles.followUpsWrap}>
                <Text style={[styles.followUpsHeader, { color: theme.textTertiary }]}>
                  You might also ask
                </Text>
                <View style={styles.followUpsList}>
                  {followUps.map((q, idx) => (
                    <TouchableOpacity
                      key={`${idx}-${q}`}
                      onPress={() => handleFollowUpTap(q)}
                      disabled={loading}
                      activeOpacity={0.75}
                      style={[
                        styles.followUpChip,
                        {
                          borderColor: theme.border,
                          backgroundColor: theme.surface,
                          opacity: loading ? 0.5 : 1,
                        },
                      ]}
                    >
                      <Text
                        style={[styles.followUpChipText, { color: theme.text }]}
                        numberOfLines={2}
                      >
                        {q}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
            ) : null}
          </ScrollView>
        </KeyboardAvoidingView>

        {/* Reflect modal mounted inside Ask modal so the overlay sits on top */}
        <ReflectModal
          visible={reflectOpen}
          onClose={() => setReflectOpen(false)}
          userId={userId}
          domain={CHIP_TO_REFLECT_DOMAIN[chip]}
          phaseLabel={phaseLabel || null}
          patternHint={patternHint || askedQuestion || null}
          source="ask_reflect"
          initialText={reflectInitialText}
          promptOverride="What's coming up for you reading this?"
        />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingTop: 50,
    paddingBottom: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  closeText: { fontSize: 14, fontWeight: '500' },
  headerTitle: { fontSize: 16, fontWeight: '500' },
  scrollBody: { paddingHorizontal: 16, paddingTop: 18, paddingBottom: 60 },
  subtle: {
    fontSize: 13,
    fontStyle: 'italic',
    lineHeight: 18,
    marginBottom: 14,
  },
  chipRow: {
    paddingVertical: 4,
    paddingRight: 16,
    gap: 8,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: StyleSheet.hairlineWidth,
    marginRight: 8,
  },
  chipText: { fontSize: 13, fontWeight: '500' },
  input: {
    marginTop: 18,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    minHeight: 110,
    fontSize: 15,
    lineHeight: 21,
  },
  error: { fontSize: 13, marginTop: 10 },
  askBtn: {
    marginTop: 16,
    paddingVertical: 14,
    borderRadius: 26,
    alignItems: 'center',
  },
  askBtnText: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.3,
  },
  answerCard: {
    marginTop: 24,
    padding: 18,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
  },
  answerPara: {
    fontSize: 15,
    lineHeight: 22,
  },
  reflectBtn: {
    marginTop: 6,
    alignSelf: 'flex-start',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 22,
    borderWidth: StyleSheet.hairlineWidth,
  },
  reflectBtnText: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.2,
  },
  followUpsWrap: {
    marginTop: 22,
  },
  followUpsHeader: {
    fontSize: 12,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 10,
  },
  followUpsList: {
    flexDirection: 'column',
    gap: 8,
  },
  followUpChip: {
    paddingHorizontal: 14,
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 8,
  },
  followUpChipText: {
    fontSize: 14,
    fontWeight: '500',
    lineHeight: 19,
  },
});
