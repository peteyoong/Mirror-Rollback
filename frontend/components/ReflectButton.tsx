/**
 * @deprecated This component has been replaced by UniversalReflectButton and UniversalReflectionModal.
 * Please use those components instead. This file will be removed in a future cleanup.
 * 
 * Migration guide:
 * - Import { InlineReflectButton } from './UniversalReflectButton'
 * - Replace <ReflectButton sourceLens="..." sourceName="..." .../>
 *   with <InlineReflectButton source={{ lens: "...", name: "...", type: "..." }} />
 */
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Modal, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { useTheme } from '../contexts/ThemeContext';
import { useForumContext, PrefilledSource } from '../contexts/ForumContext';

interface ReflectButtonProps {
  // Source identification
  sourceLens: 'human-design' | 'enneagram' | 'astrology' | 'numerology' | 'patterns';
  sourceType: string;  // e.g., 'type', 'authority', 'center_sacral', 'gate_1', or domain_id for patterns
  sourceName: string;  // Human-readable name e.g., 'Emotional Authority'
  sourceValue?: string; // The actual value e.g., 'Manifestor'
  
  // Guidance content for the reflection
  theme?: string;
  strength?: string;
  challenge?: string;
  guidance?: string;
  
  // Optional: compact mode for smaller cards
  compact?: boolean;
}

export function ReflectButton({
  sourceLens,
  sourceType,
  sourceName,
  sourceValue,
  theme: insightTheme,
  strength,
  challenge,
  guidance,
  compact = false,
}: ReflectButtonProps) {
  const { theme } = useTheme();
  const router = useRouter();
  const { isInForumContext, forumId, forumName, setPrefilledSource } = useForumContext();
  const [showOptions, setShowOptions] = useState(false);

  // Helper function moved before usage
  const getLensDisplayName = (lens: string): string => {
    const names: Record<string, string> = {
      'human-design': 'Human Design',
      'enneagram': 'Enneagram',
      'astrology': 'Astrology',
      'numerology': 'Numerology',
      'patterns': 'Patterns',
    };
    return names[lens] || lens;
  };

  const handleReflect = () => {
    // If in forum context, show options
    // If not, go directly to private reflection
    if (isInForumContext) {
      setShowOptions(true);
    } else {
      handlePrivateReflection();
    }
  };

  const handlePrivateReflection = () => {
    setShowOptions(false);
    // Navigate to journal with prefilled source
    router.push({
      pathname: '/(tabs)/journal',
      params: {
        prefillPrompt: `Reflecting on ${sourceName}${sourceValue ? `: ${sourceValue}` : ''}`,
        journalSource: `${sourceLens}_${sourceType}`,
        category: getLensDisplayName(sourceLens),
        sourceLens,
        sourceType,
        sourceName,
        sourceValue: sourceValue || '',
      }
    });
  };

  const handleForumReflection = () => {
    setShowOptions(false);
    if (!forumId) return;
    
    // Set the prefilled source for forum reflection
    const source: PrefilledSource = {
      sourceType: 'mirror',
      lens: sourceLens === 'human-design' ? 'human-design' : 
            sourceLens === 'enneagram' ? 'enneagram' : 'daily-insight',
      insightId: sourceType,
      insightName: sourceName,
      insightValue: sourceValue || '',
      theme: insightTheme || `Reflecting on your ${sourceName}.`,
      strength: strength || 'What this offers when you honor it.',
      challenge: challenge || 'What happens when you override it.',
      guidance: guidance || 'Notice how this shows up in your life.',
    };
    setPrefilledSource(source);
    
    // Navigate to forum exercise with prefilled flag
    router.push(`/forums/exercise?forumId=${forumId}&prefilled=true`);
  };

  return (
    <>
      <TouchableOpacity
        style={[
          compact ? styles.compactButton : styles.button,
          { borderColor: theme.border }
        ]}
        onPress={handleReflect}
        activeOpacity={0.7}
      >
        <Text style={[
          compact ? styles.compactButtonText : styles.buttonText,
          { color: theme.textSecondary }
        ]}>
          Reflect
        </Text>
      </TouchableOpacity>

      {/* Options Modal */}
      <Modal
        visible={showOptions}
        transparent
        animationType="fade"
        onRequestClose={() => setShowOptions(false)}
      >
        <Pressable 
          style={styles.modalOverlay}
          onPress={() => setShowOptions(false)}
        >
          <Pressable 
            style={[styles.modalContent, { backgroundColor: theme.surface }]}
            onPress={(e) => e.stopPropagation()}
          >
            <Text style={[styles.modalTitle, { color: theme.text }]}>
              Reflect on {sourceName}
            </Text>
            {sourceValue && (
              <Text style={[styles.modalSubtitle, { color: theme.textSecondary }]}>
                {sourceValue}
              </Text>
            )}
            
            <View style={styles.optionsContainer}>
              {/* Forum Reflection - Primary when in forum context */}
              {isInForumContext && (
                <TouchableOpacity
                  style={[styles.optionPrimary, { backgroundColor: theme.buttonPrimaryBg }]}
                  onPress={handleForumReflection}
                >
                  <Text style={[styles.optionPrimaryText, { color: theme.buttonPrimaryText }]}>
                    Forum Reflection
                  </Text>
                  <Text style={[styles.optionHint, { color: theme.buttonPrimaryText, opacity: 0.8 }]}>
                    Share with {forumName}
                  </Text>
                </TouchableOpacity>
              )}
              
              {/* Private Reflection */}
              <TouchableOpacity
                style={[
                  isInForumContext ? styles.optionSecondary : styles.optionPrimary,
                  { 
                    backgroundColor: isInForumContext ? 'transparent' : theme.buttonPrimaryBg,
                    borderColor: theme.border,
                    borderWidth: isInForumContext ? 1 : 0,
                  }
                ]}
                onPress={handlePrivateReflection}
              >
                <Text style={[
                  isInForumContext ? styles.optionSecondaryText : styles.optionPrimaryText,
                  { color: isInForumContext ? theme.text : theme.buttonPrimaryText }
                ]}>
                  Private Reflection
                </Text>
                <Text style={[styles.optionHint, { color: theme.textTertiary }]}>
                  Save to your journal
                </Text>
              </TouchableOpacity>

              {/* Forum option when NOT in context - shown as secondary */}
              {!isInForumContext && (
                <TouchableOpacity
                  style={[styles.optionSecondary, { borderColor: theme.border }]}
                  onPress={() => {
                    setShowOptions(false);
                    router.push('/forums');
                  }}
                >
                  <Text style={[styles.optionSecondaryText, { color: theme.textSecondary }]}>
                    Reflect in a Forum
                  </Text>
                  <Text style={[styles.optionHint, { color: theme.textTertiary }]}>
                    Join or create a forum first
                  </Text>
                </TouchableOpacity>
              )}
            </View>

            <TouchableOpacity
              style={styles.cancelButton}
              onPress={() => setShowOptions(false)}
            >
              <Text style={[styles.cancelText, { color: theme.textTertiary }]}>
                Cancel
              </Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  button: {
    marginTop: 14,
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
    alignSelf: 'flex-start',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  compactButton: {
    marginTop: 10,
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 6,
    borderWidth: 1,
    alignItems: 'center',
    alignSelf: 'flex-start',
  },
  compactButtonText: {
    fontSize: 13,
    fontWeight: '500',
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    maxWidth: 340,
    borderRadius: 16,
    padding: 24,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
  },
  optionsContainer: {
    gap: 12,
  },
  optionPrimary: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    alignItems: 'center',
  },
  optionPrimaryText: {
    fontSize: 16,
    fontWeight: '600',
  },
  optionSecondary: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    alignItems: 'center',
  },
  optionSecondaryText: {
    fontSize: 15,
    fontWeight: '500',
  },
  optionHint: {
    fontSize: 12,
    marginTop: 2,
  },
  cancelButton: {
    marginTop: 16,
    paddingVertical: 10,
    alignItems: 'center',
  },
  cancelText: {
    fontSize: 14,
  },
});
