import React, { useState } from 'react';
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

/**
 * AskAboutLifeModal — conversational "ask about my life" surface.
 *
 * 7 chips → free-text question → grounded plain-text answer. The UI is
 * full-screen on mobile to focus the user, with a clear back-out and a
 * scrollable answer area.
 */

interface Props {
  visible: boolean;
  onClose: () => void;
  userId: string;
  initialDomain?: AskLifeChip;
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

export default function AskAboutLifeModal({ visible, onClose, userId, initialDomain }: Props) {
  const { theme } = useTheme();
  const [chip, setChip] = useState<AskLifeChip>(initialDomain || 'self');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setQuestion('');
    setAnswer(null);
    setError(null);
    setLoading(false);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleAsk = async () => {
    const q = question.trim();
    if (!q) {
      setError('Type a question first.');
      return;
    }
    Keyboard.dismiss();
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      const resp = await askAboutLife(userId, { domain: chip, question: q });
      setAnswer(resp.answer || '');
    } catch (e) {
      const msg = e && typeof e === 'object' && 'message' in e
        ? String((e as { message?: string }).message)
        : 'Could not load an answer.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const askDisabled = loading || !question.trim();

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
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={styles.scrollBody}
            showsVerticalScrollIndicator={false}
          >
            <Text style={[styles.subtle, { color: theme.textTertiary }]}>
              Pick a part of your life and ask anything you're sitting with.
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
              </View>
            ) : null}
          </ScrollView>
        </KeyboardAvoidingView>
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
  headerTitle: { fontSize: 16, fontWeight: '700' },
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
  chipText: { fontSize: 13, fontWeight: '600' },
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
    fontWeight: '700',
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
});
