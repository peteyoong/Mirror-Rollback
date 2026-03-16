import React, { useState } from 'react';
import { TouchableOpacity, Text, StyleSheet, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useForumContext } from '../contexts/ForumContext';
import { UniversalReflectionModal, ReflectionSource } from './UniversalReflectionModal';

interface UniversalReflectButtonProps {
  source: ReflectionSource;
  prompt?: string;  // Optional guidance/prompt text
  compact?: boolean;
  label?: string;   // Custom label (default: "Reflect")
  style?: object;
}

export function UniversalReflectButton({
  source,
  prompt,
  compact = false,
  label = 'Reflect',
  style,
}: UniversalReflectButtonProps) {
  const { theme } = useTheme();
  const { isInForumContext, forumId, forumName } = useForumContext();
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <TouchableOpacity
        style={[
          compact ? styles.compactButton : styles.button,
          { borderColor: theme.border },
          style,
        ]}
        onPress={() => setShowModal(true)}
        activeOpacity={0.7}
      >
        <Ionicons 
          name="create-outline" 
          size={compact ? 14 : 16} 
          color={theme.textSecondary} 
        />
        <Text style={[
          compact ? styles.compactButtonText : styles.buttonText,
          { color: theme.textSecondary }
        ]}>
          {label}
        </Text>
      </TouchableOpacity>

      <UniversalReflectionModal
        visible={showModal}
        onClose={() => setShowModal(false)}
        source={source}
        initialPrompt={prompt}
        activeForumId={isInForumContext ? forumId || undefined : undefined}
        activeForumName={isInForumContext ? forumName || undefined : undefined}
      />
    </>
  );
}

// Inline Reflect button for cards (sits at the bottom of content)
export function InlineReflectButton({
  source,
  prompt,
}: {
  source: ReflectionSource;
  prompt?: string;
}) {
  const { theme } = useTheme();
  const { isInForumContext, forumId, forumName } = useForumContext();
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <TouchableOpacity
        style={[styles.inlineButton, { backgroundColor: theme.background, borderColor: theme.border }]}
        onPress={() => setShowModal(true)}
        activeOpacity={0.7}
      >
        <View style={styles.inlineContent}>
          <Ionicons name="create-outline" size={16} color={theme.accent} />
          <Text style={[styles.inlineText, { color: theme.accent }]}>Reflect</Text>
        </View>
      </TouchableOpacity>

      <UniversalReflectionModal
        visible={showModal}
        onClose={() => setShowModal(false)}
        source={source}
        initialPrompt={prompt}
        activeForumId={isInForumContext ? forumId || undefined : undefined}
        activeForumName={isInForumContext ? forumName || undefined : undefined}
      />
    </>
  );
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  compactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  compactButtonText: {
    fontSize: 13,
    fontWeight: '500',
  },
  inlineButton: {
    marginTop: 16,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    alignSelf: 'flex-start',
  },
  inlineContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  inlineText: {
    fontSize: 14,
    fontWeight: '500',
  },
});

export default UniversalReflectButton;
