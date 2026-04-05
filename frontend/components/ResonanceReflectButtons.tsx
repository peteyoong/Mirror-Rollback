import React, { useState, useRef, useEffect } from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  View,
  Animated,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { useForumContext } from '../contexts/ForumContext';
import { UniversalReflectionModal, ReflectionSource } from './UniversalReflectionModal';
import api from '../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface ResonanceReflectButtonsProps {
  source: ReflectionSource;
  patternSignature?: string;  // Pattern identifier for resonance tracking
  context?: string;           // Context (home, forum, lens, etc.)
  prompt?: string;            // Optional guidance/prompt for Reflect
  compact?: boolean;
  showReflectOnly?: boolean;  // Hide resonance button
  onResonance?: () => void;   // Callback after resonance
  onReflect?: () => void;     // Callback when reflect opens
}

interface ResonanceData {
  user_id: string;
  pattern_signature: string;
  context: string;
  timestamp: string;
  resonance: boolean;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export function ResonanceReflectButtons({
  source,
  patternSignature,
  context = 'home',
  prompt,
  compact = false,
  showReflectOnly = false,
  onResonance,
  onReflect,
}: ResonanceReflectButtonsProps) {
  const { theme } = useTheme();
  const { isInForumContext, forumId, forumName } = useForumContext();
  
  // State
  const [hasResonated, setHasResonated] = useState(false);
  const [showReflectModal, setShowReflectModal] = useState(false);
  const [showReflectHint, setShowReflectHint] = useState(false);
  
  // Animation values
  const resonanceGlow = useRef(new Animated.Value(0)).current;
  const resonanceScale = useRef(new Animated.Value(1)).current;
  const reflectHintOpacity = useRef(new Animated.Value(0)).current;

  // ==========================================================================
  // RESONANCE HANDLER
  // ==========================================================================
  
  const handleResonance = async () => {
    if (hasResonated) return;
    
    // Immediate UI feedback
    setHasResonated(true);
    
    // Animate glow + scale
    Animated.parallel([
      Animated.sequence([
        Animated.timing(resonanceScale, {
          toValue: 1.1,
          duration: 150,
          useNativeDriver: true,
        }),
        Animated.timing(resonanceScale, {
          toValue: 1,
          duration: 150,
          useNativeDriver: true,
        }),
      ]),
      Animated.sequence([
        Animated.timing(resonanceGlow, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.timing(resonanceGlow, {
          toValue: 0,
          duration: 500,
          useNativeDriver: true,
        }),
      ]),
    ]).start();
    
    // Show "Want to explore this more?" hint after delay
    setTimeout(() => {
      setShowReflectHint(true);
      Animated.timing(reflectHintOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }).start();
    }, 800);
    
    // Store resonance data (fire and forget)
    try {
      await api.post('/api/resonance/track', {
        pattern_signature: patternSignature || source.id || 'unknown',
        context: context,
        source_type: source.type,
        source_id: source.id,
        resonance: true,
      });
    } catch (error) {
      console.log('[Resonance] Failed to track:', error);
      // Don't show error to user - this is non-blocking
    }
    
    // Callback
    onResonance?.();
  };

  // ==========================================================================
  // REFLECT HANDLER
  // ==========================================================================
  
  const handleReflect = () => {
    setShowReflectModal(true);
    onReflect?.();
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================
  
  const glowStyle = {
    opacity: resonanceGlow.interpolate({
      inputRange: [0, 1],
      outputRange: [0, 0.3],
    }),
  };

  return (
    <>
      <View style={[styles.container, compact && styles.containerCompact]}>
        {/* Resonance Button */}
        {!showReflectOnly && (
          <Animated.View style={{ transform: [{ scale: resonanceScale }] }}>
            <TouchableOpacity
              style={[
                styles.resonanceButton,
                compact && styles.resonanceButtonCompact,
                { 
                  backgroundColor: hasResonated ? theme.accent + '15' : theme.surface,
                  borderColor: hasResonated ? theme.accent + '40' : theme.border,
                },
              ]}
              onPress={handleResonance}
              activeOpacity={0.7}
              disabled={hasResonated}
            >
              {/* Glow overlay */}
              <Animated.View 
                style={[
                  StyleSheet.absoluteFill, 
                  styles.glowOverlay,
                  { backgroundColor: theme.accent },
                  glowStyle,
                ]} 
              />
              
              <Text style={[
                styles.resonanceText,
                compact && styles.resonanceTextCompact,
                { color: hasResonated ? theme.accent : theme.textSecondary }
              ]}>
                {hasResonated ? '✨ Got it' : '✨ That resonates'}
              </Text>
            </TouchableOpacity>
          </Animated.View>
        )}

        {/* Reflect Button */}
        <TouchableOpacity
          style={[
            styles.reflectButton,
            compact && styles.reflectButtonCompact,
            { 
              backgroundColor: theme.surface,
              borderColor: theme.border,
            },
            hasResonated && styles.reflectButtonHighlighted,
            hasResonated && { borderColor: theme.accent + '60' },
          ]}
          onPress={handleReflect}
          activeOpacity={0.7}
        >
          <Ionicons 
            name="create-outline" 
            size={compact ? 14 : 16} 
            color={hasResonated ? theme.accent : theme.textSecondary} 
          />
          <Text style={[
            styles.reflectText,
            compact && styles.reflectTextCompact,
            { color: hasResonated ? theme.accent : theme.textSecondary }
          ]}>
            Reflect
          </Text>
        </TouchableOpacity>
      </View>

      {/* "Want to explore more?" hint - shows after resonance */}
      {showReflectHint && !showReflectOnly && (
        <Animated.View style={[styles.reflectHint, { opacity: reflectHintOpacity }]}>
          <Text style={[styles.reflectHintText, { color: theme.textTertiary }]}>
            Want to explore this more?
          </Text>
        </Animated.View>
      )}

      {/* Reflect Modal */}
      <UniversalReflectionModal
        visible={showReflectModal}
        onClose={() => setShowReflectModal(false)}
        source={source}
        initialPrompt={prompt}
        activeForumId={isInForumContext ? forumId || undefined : undefined}
        activeForumName={isInForumContext ? forumName || undefined : undefined}
      />
    </>
  );
}

// =============================================================================
// INLINE VERSION (for cards)
// =============================================================================

export function InlineResonanceReflect({
  source,
  patternSignature,
  context = 'card',
  prompt,
}: {
  source: ReflectionSource;
  patternSignature?: string;
  context?: string;
  prompt?: string;
}) {
  const { theme } = useTheme();
  const { isInForumContext, forumId, forumName } = useForumContext();
  
  const [hasResonated, setHasResonated] = useState(false);
  const [showReflectModal, setShowReflectModal] = useState(false);
  const [showHint, setShowHint] = useState(false);
  
  const glowAnim = useRef(new Animated.Value(0)).current;
  const hintOpacity = useRef(new Animated.Value(0)).current;

  const handleResonance = async () => {
    if (hasResonated) return;
    setHasResonated(true);
    
    // Glow animation
    Animated.sequence([
      Animated.timing(glowAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(glowAnim, {
        toValue: 0,
        duration: 400,
        useNativeDriver: true,
      }),
    ]).start();
    
    // Show hint after delay
    setTimeout(() => {
      setShowHint(true);
      Animated.timing(hintOpacity, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }, 600);
    
    // Track resonance
    try {
      await api.post('/api/resonance/track', {
        pattern_signature: patternSignature || source.id || 'unknown',
        context,
        source_type: source.type,
        source_id: source.id,
        resonance: true,
      });
    } catch (e) {
      // Silent fail
    }
  };

  return (
    <>
      <View style={styles.inlineContainer}>
        {/* Resonance */}
        <TouchableOpacity
          style={[
            styles.inlineResonance,
            { 
              backgroundColor: hasResonated ? theme.accent + '12' : theme.background,
              borderColor: hasResonated ? theme.accent + '30' : theme.border,
            }
          ]}
          onPress={handleResonance}
          activeOpacity={0.7}
          disabled={hasResonated}
        >
          <Text style={[
            styles.inlineResonanceText,
            { color: hasResonated ? theme.accent : theme.textSecondary }
          ]}>
            {hasResonated ? '✨ Got it' : '✨ That resonates'}
          </Text>
        </TouchableOpacity>

        {/* Reflect */}
        <TouchableOpacity
          style={[
            styles.inlineReflect,
            { 
              backgroundColor: theme.background,
              borderColor: hasResonated ? theme.accent + '40' : theme.border,
            }
          ]}
          onPress={() => setShowReflectModal(true)}
          activeOpacity={0.7}
        >
          <Ionicons 
            name="create-outline" 
            size={16} 
            color={hasResonated ? theme.accent : theme.textSecondary} 
          />
          <Text style={[
            styles.inlineReflectText,
            { color: hasResonated ? theme.accent : theme.textSecondary }
          ]}>
            Reflect
          </Text>
        </TouchableOpacity>
      </View>

      {/* Hint */}
      {showHint && (
        <Animated.View style={{ opacity: hintOpacity, marginTop: 8 }}>
          <Text style={[styles.hintText, { color: theme.textTertiary }]}>
            Want to explore this more?
          </Text>
        </Animated.View>
      )}

      <UniversalReflectionModal
        visible={showReflectModal}
        onClose={() => setShowReflectModal(false)}
        source={source}
        initialPrompt={prompt}
        activeForumId={isInForumContext ? forumId || undefined : undefined}
        activeForumName={isInForumContext ? forumName || undefined : undefined}
      />
    </>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  // Main container
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 16,
  },
  containerCompact: {
    gap: 8,
    marginTop: 12,
  },

  // Resonance button
  resonanceButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    overflow: 'hidden',
  },
  resonanceButtonCompact: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
  },
  resonanceText: {
    fontSize: 14,
    fontWeight: '500',
  },
  resonanceTextCompact: {
    fontSize: 13,
  },
  glowOverlay: {
    borderRadius: 8,
  },

  // Reflect button
  reflectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
  },
  reflectButtonCompact: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    gap: 4,
  },
  reflectButtonHighlighted: {
    borderWidth: 1.5,
  },
  reflectText: {
    fontSize: 14,
    fontWeight: '500',
  },
  reflectTextCompact: {
    fontSize: 13,
  },

  // Reflect hint
  reflectHint: {
    marginTop: 8,
    marginLeft: 4,
  },
  reflectHintText: {
    fontSize: 12,
    fontStyle: 'italic',
  },

  // Inline version
  inlineContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginTop: 16,
  },
  inlineResonance: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  inlineResonanceText: {
    fontSize: 14,
    fontWeight: '500',
  },
  inlineReflect: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
  },
  inlineReflectText: {
    fontSize: 14,
    fontWeight: '500',
  },
  hintText: {
    fontSize: 12,
    fontStyle: 'italic',
  },
});

export default ResonanceReflectButtons;
