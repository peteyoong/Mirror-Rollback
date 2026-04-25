import React, { useEffect, useState } from 'react';
import {
  Modal,
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  TouchableWithoutFeedback,
  Keyboard,
  Animated,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { saveReflection } from '../services/api';

/**
 * ReflectModal — lightweight thought capture from the Life tab.
 *
 * Reflections are intentionally SEPARATE from Lifeline events:
 *   - Reflect = thinking (fast, low friction, captures what's coming up)
 *   - Lifeline = reality  (intentional, real events only)
 *
 * Rendered as a centered modal on web and a bottom sheet feel on mobile.
 */

interface Props {
  visible: boolean;
  onClose: () => void;
  userId: string;
  domain: 'self' | 'work' | 'relationships';
  phaseLabel?: string | null;
  patternHint?: string | null;
  onSaved?: () => void;
  /** Source tag for analytics + DB filtering (e.g. "life_reflect", "ask_reflect"). */
  source?: string;
  /** Optional pre-filled text (used when reflecting on an answer). */
  initialText?: string;
  /** Optional override for the prompt heading shown above the input. */
  promptOverride?: string | null;
}

const PROMPTS: string[] = [
  "What's happening for you right now?",
  "What did this bring up?",
  "Where do you see this showing up?",
];

export default function ReflectModal({
  visible,
  onClose,
  userId,
  domain,
  phaseLabel,
  patternHint,
  onSaved,
  source,
  initialText,
  promptOverride,
}: Props) {
  const { theme } = useTheme();
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedFlash, setSavedFlash] = useState(false);
  const [promptIdx] = useState(() => Math.floor(Math.random() * PROMPTS.length));
  const flash = React.useRef(new Animated.Value(0)).current;

  // Reset state when modal opens / closes
  useEffect(() => {
    if (visible) {
      setText(initialText || '');
      setError(null);
      setSaving(false);
      setSavedFlash(false);
    }
  }, [visible, initialText]);

  const handleSave = async () => {
    const trimmed = text.trim();
    if (!trimmed) {
      setError('Add a few words first.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await saveReflection({
        user_id:      userId,
        text:         trimmed,
        domain,
        source:       source || 'life_reflect',
        phase_label:  phaseLabel || null,
        pattern_hint: patternHint || null,
      });
      setSavedFlash(true);
      Animated.sequence([
        Animated.timing(flash, { toValue: 1, duration: 180, useNativeDriver: true }),
        Animated.delay(700),
        Animated.timing(flash, { toValue: 0, duration: 180, useNativeDriver: true }),
      ]).start(() => {
        if (onSaved) onSaved();
        onClose();
      });
    } catch (e: unknown) {
      const msg = e && typeof e === 'object' && 'message' in e ? String((e as { message?: string }).message) : 'Could not save. Please try again.';
      setError(msg);
      setSaving(false);
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <TouchableWithoutFeedback onPress={onClose}>
        <View style={styles.backdrop}>
          <TouchableWithoutFeedback onPress={() => Keyboard.dismiss()}>
            <KeyboardAvoidingView
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              style={styles.kavWrap}
            >
              <View
                style={[
                  styles.sheet,
                  {
                    backgroundColor: theme.background,
                    borderColor: theme.border,
                  },
                ]}
              >
                <Text style={[styles.title, { color: theme.text }]}>
                  Capture what&apos;s coming up
                </Text>

                <Text style={[styles.prompt, { color: theme.textTertiary }]}>
                  {promptOverride || PROMPTS[promptIdx]}
                </Text>

                <TextInput
                  style={[
                    styles.input,
                    {
                      color: theme.text,
                      backgroundColor: theme.surface,
                      borderColor: theme.border,
                    },
                  ]}
                  placeholder="Type a thought, observation, or question..."
                  placeholderTextColor={theme.textTertiary}
                  multiline
                  numberOfLines={6}
                  textAlignVertical="top"
                  value={text}
                  onChangeText={(v) => {
                    setText(v);
                    if (error) setError(null);
                  }}
                  autoFocus
                  maxLength={4000}
                  editable={!saving}
                />

                {!!error && (
                  <Text style={[styles.error, { color: theme.error || '#C04848' }]}>
                    {error}
                  </Text>
                )}

                <View style={styles.actions}>
                  <Pressable
                    onPress={onClose}
                    disabled={saving}
                    style={({ pressed }) => [
                      styles.cancelBtn,
                      { opacity: pressed ? 0.6 : 1 },
                    ]}
                    hitSlop={8}
                  >
                    <Text style={[styles.cancelText, { color: theme.textTertiary }]}>
                      Cancel
                    </Text>
                  </Pressable>

                  <Pressable
                    onPress={handleSave}
                    disabled={saving || !text.trim()}
                    style={({ pressed }) => [
                      styles.saveBtn,
                      {
                        backgroundColor: text.trim() ? theme.text : theme.textTertiary,
                        opacity: pressed ? 0.85 : 1,
                      },
                    ]}
                  >
                    {saving ? (
                      <ActivityIndicator
                        size="small"
                        color={theme.background}
                      />
                    ) : (
                      <Text
                        style={[styles.saveText, { color: theme.background }]}
                      >
                        Save Reflection
                      </Text>
                    )}
                  </Pressable>
                </View>

                {savedFlash && (
                  <Animated.View
                    style={[
                      styles.savedFlash,
                      {
                        opacity: flash,
                        backgroundColor: theme.surface,
                        borderColor: theme.border,
                      },
                    ]}
                    pointerEvents="none"
                  >
                    <Text style={[styles.savedFlashText, { color: theme.text }]}>
                      Saved
                    </Text>
                  </Animated.View>
                )}
              </View>
            </KeyboardAvoidingView>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.55)',
    justifyContent: 'flex-end',
  },
  kavWrap: {
    width: '100%',
  },
  sheet: {
    width: '100%',
    paddingHorizontal: 20,
    paddingTop: 22,
    paddingBottom: 28,
    borderTopLeftRadius: 18,
    borderTopRightRadius: 18,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderLeftWidth: StyleSheet.hairlineWidth,
    borderRightWidth: StyleSheet.hairlineWidth,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 6,
  },
  prompt: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 14,
  },
  input: {
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    minHeight: 120,
    fontSize: 15,
    lineHeight: 21,
  },
  error: {
    fontSize: 13,
    marginTop: 10,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginTop: 18,
    gap: 12,
  },
  cancelBtn: {
    paddingVertical: 10,
    paddingHorizontal: 14,
  },
  cancelText: {
    fontSize: 14,
    fontWeight: '500',
  },
  saveBtn: {
    paddingVertical: 12,
    paddingHorizontal: 22,
    borderRadius: 24,
    minWidth: 150,
    alignItems: 'center',
  },
  saveText: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  savedFlash: {
    position: 'absolute',
    top: 22,
    right: 20,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  savedFlashText: {
    fontSize: 12,
    fontWeight: '600',
  },
});
