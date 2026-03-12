import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import { useForumContext, PrefilledSource } from '../contexts/ForumContext';

interface ForumContextBannerProps {
  showReflectButton?: boolean;
  onReflect?: () => void;
}

export function ForumContextBanner({ showReflectButton = false, onReflect }: ForumContextBannerProps) {
  const { theme } = useTheme();
  const { isInForumContext, forumId, forumName, clearForumContext } = useForumContext();
  const router = useRouter();

  if (!isInForumContext) return null;

  const handleBackToForum = () => {
    router.push(`/forums/${forumId}`);
  };

  const handleExitForumMode = () => {
    clearForumContext();
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.accent + '15', borderBottomColor: theme.border }]}>
      <View style={styles.leftSection}>
        <TouchableOpacity onPress={handleBackToForum} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Back to {forumName || 'Forum'}</Text>
        </TouchableOpacity>
      </View>
      
      <View style={styles.rightSection}>
        {showReflectButton && onReflect && (
          <TouchableOpacity 
            onPress={onReflect} 
            style={[styles.reflectButton, { backgroundColor: theme.accent }]}
          >
            <Text style={[styles.reflectButtonText, { color: theme.buttonPrimaryText }]}>
              Reflect in Forum
            </Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity onPress={handleExitForumMode} style={styles.exitButton}>
          <Text style={[styles.exitText, { color: theme.textTertiary }]}>Exit</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// Component for individual insight items with "Reflect in Forum" option
interface ForumReflectButtonProps {
  insightId: string;
  insightName: string;
  insightValue: string;
  lens: 'human-design' | 'enneagram' | 'daily-insight';
  theme: string;
  strength: string;
  challenge: string;
  guidance: string;
}

export function ForumReflectButton({
  insightId,
  insightName,
  insightValue,
  lens,
  theme: insightTheme,
  strength,
  challenge,
  guidance,
}: ForumReflectButtonProps) {
  const { theme } = useTheme();
  const router = useRouter();
  const { isInForumContext, forumId, setPrefilledSource } = useForumContext();

  if (!isInForumContext) return null;

  const handleReflect = () => {
    // Set the prefilled source
    const source: PrefilledSource = {
      sourceType: 'mirror',
      lens,
      insightId,
      insightName,
      insightValue,
      theme: insightTheme,
      strength,
      challenge,
      guidance,
    };
    setPrefilledSource(source);
    
    // Navigate to exercise with prefilled flag
    router.push(`/forums/exercise?forumId=${forumId}&prefilled=true`);
  };

  return (
    <TouchableOpacity 
      onPress={handleReflect} 
      style={[styles.insightReflectButton, { borderColor: theme.accent }]}
    >
      <Text style={[styles.insightReflectText, { color: theme.accent }]}>
        Reflect in Forum
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  leftSection: {
    flex: 1,
  },
  rightSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  backButton: {
    paddingVertical: 4,
  },
  backText: {
    fontSize: 14,
    fontWeight: '500',
  },
  reflectButton: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 8,
  },
  reflectButtonText: {
    fontSize: 13,
    fontWeight: '600',
  },
  exitButton: {
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  exitText: {
    fontSize: 13,
  },
  // For insight-level button
  insightReflectButton: {
    marginTop: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  insightReflectText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
