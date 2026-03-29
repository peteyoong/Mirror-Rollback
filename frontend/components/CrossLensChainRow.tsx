import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

/**
 * CrossLensChainRow (V2: Specific Pattern Linking)
 * 
 * A subtle, quiet chaining row that connects the SAME pattern across lenses.
 * 
 * V2 UPGRADE:
 * - References the actual pattern, not just generic continuity
 * - User should feel "This is the SAME thing" not just "these pages are connected"
 * - Accepts pattern context for specific linking phrases
 * 
 * STYLE:
 * - Small text
 * - Low visual weight
 * - Tappable with subtle chevron
 * - No big cards
 * - Feels like connective tissue
 */

// Pattern scene types that can be linked
type PatternScene = 
  | 'urgency' 
  | 'hesitation' 
  | 'overcommitment' 
  | 'avoidance' 
  | 'control' 
  | 'validation' 
  | 'isolation' 
  | 'intensity'
  | 'general';

interface CrossLensChainRowProps {
  // Current lens context
  currentLens: 'numerology' | 'astrology' | 'bazi' | 'home';
  
  // V2: Pattern-specific context
  patternScene?: PatternScene;
  patternKey?: string;  // e.g., "life_path_1", "sun_aries"
  
  // V2: Backend-derived linking phrase (preferred when available)
  linkingPhrase?: string;
  
  // V2: Core pattern text for context extraction
  corePattern?: string;
  
  // Optional: Custom message override (fallback)
  customMessage?: string;
  
  // Optional: Secondary line for extra clarity
  secondaryLine?: string;
  
  // Navigation target (defaults to home)
  navigateTo?: string;
  
  // Optional: Pattern ID for deep linking
  patternId?: string;
  
  // Hide if not useful
  hide?: boolean;
}

// V2: Specific pattern-based linking phrases
const PATTERN_LINKING_PHRASES: Record<PatternScene, string[]> = {
  urgency: [
    "Same pressure to close too early",
    "Same pattern of pushing before clarity",
    "This urgency is showing up here too",
    "Same rush to decide",
  ],
  hesitation: [
    "Same hesitation, different angle",
    "Same thing keeps not landing",
    "This holding pattern again",
    "Same pause before moving",
  ],
  overcommitment: [
    "Same pattern of taking on too much",
    "Same overextension showing here",
    "This spreading thin again",
  ],
  avoidance: [
    "Same thing you've been circling",
    "Same unresolved part showing up here",
    "This avoidance pattern again",
  ],
  control: [
    "Same need to manage everything",
    "Same grip showing here",
    "This control pattern repeating",
  ],
  validation: [
    "Same need to be seen",
    "Same search for acknowledgment",
    "This validation loop again",
  ],
  isolation: [
    "Same pulling back",
    "Same retreat pattern here",
    "This withdrawal showing up again",
  ],
  intensity: [
    "Same intensity pattern",
    "Same full-on approach here",
    "This all-or-nothing again",
  ],
  general: [
    "This is the same loop",
    "Same pattern, different lens",
    "You've seen this already",
    "This keeps showing up",
  ],
};

// V2: Extract pattern scene from core pattern text
function extractPatternScene(corePattern?: string): PatternScene {
  if (!corePattern) return 'general';
  
  const text = corePattern.toLowerCase();
  
  if (text.includes('wait') || text.includes('rush') || text.includes('fast') || text.includes('move')) {
    return 'urgency';
  }
  if (text.includes('hesitat') || text.includes('pause') || text.includes('hold') || text.includes('stuck')) {
    return 'hesitation';
  }
  if (text.includes('too much') || text.includes('overcommit') || text.includes('spread') || text.includes('exhaust')) {
    return 'overcommitment';
  }
  if (text.includes('avoid') || text.includes('circle') || text.includes('escape') || text.includes('run')) {
    return 'avoidance';
  }
  if (text.includes('control') || text.includes('manage') || text.includes('grip') || text.includes('fix')) {
    return 'control';
  }
  if (text.includes('seen') || text.includes('acknowledge') || text.includes('recogni') || text.includes('valid')) {
    return 'validation';
  }
  if (text.includes('alone') || text.includes('withdraw') || text.includes('retreat') || text.includes('pull back')) {
    return 'isolation';
  }
  if (text.includes('intense') || text.includes('all or') || text.includes('full')) {
    return 'intensity';
  }
  
  return 'general';
}

// V2: Generate specific linking phrase
function generateLinkingPhrase(
  patternScene: PatternScene,
  linkingPhrase?: string,
  customMessage?: string
): string {
  // Prefer backend-derived phrase
  if (linkingPhrase) return linkingPhrase;
  
  // Use custom message if provided
  if (customMessage) return customMessage;
  
  // Generate from pattern scene
  const phrases = PATTERN_LINKING_PHRASES[patternScene] || PATTERN_LINKING_PHRASES.general;
  return phrases[Math.floor(Math.random() * phrases.length)];
}

export default function CrossLensChainRow({
  currentLens,
  patternScene,
  patternKey,
  linkingPhrase,
  corePattern,
  customMessage,
  secondaryLine,
  navigateTo = '/(tabs)',
  patternId,
  hide = false,
}: CrossLensChainRowProps) {
  const router = useRouter();
  
  if (hide) return null;
  
  // V2: Determine pattern scene from context
  const effectiveScene = patternScene || extractPatternScene(corePattern);
  
  // V2: Generate specific linking phrase
  const message = generateLinkingPhrase(effectiveScene, linkingPhrase, customMessage);
  
  // V2: Build navigation target (deep link if pattern ID available)
  const buildNavTarget = (): string => {
    if (patternId) {
      // Deep link to specific pattern on Home
      return `/(tabs)?pattern=${patternId}`;
    }
    return navigateTo;
  };
  
  const handlePress = () => {
    const target = buildNavTarget();
    router.push(target as any);
  };
  
  return (
    <TouchableOpacity 
      style={styles.container} 
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <View style={styles.row}>
        <Ionicons 
          name="git-branch-outline" 
          size={14} 
          color="#8E8E93" 
          style={styles.icon}
        />
        <Text style={styles.message}>{message}</Text>
        <Ionicons 
          name="chevron-forward" 
          size={14} 
          color="#8E8E93" 
          style={styles.chevron}
        />
      </View>
      
      {secondaryLine && (
        <Text style={styles.secondary}>{secondaryLine}</Text>
      )}
    </TouchableOpacity>
  );
}

/**
 * Minimal variant - even more subtle, for inline use
 */
export function CrossLensChainRowMinimal({
  message = "Same pattern. Different lens.",
  onPress,
}: {
  message?: string;
  onPress?: () => void;
}) {
  return (
    <TouchableOpacity 
      style={styles.minimalContainer} 
      onPress={onPress}
      activeOpacity={0.7}
      disabled={!onPress}
    >
      <Text style={styles.minimalText}>{message}</Text>
      {onPress && (
        <Ionicons 
          name="arrow-forward" 
          size={12} 
          color="#8E8E93" 
          style={styles.minimalArrow}
        />
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginVertical: 8,
    marginHorizontal: 16,
    backgroundColor: 'rgba(142, 142, 147, 0.08)',
    borderRadius: 8,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  icon: {
    marginRight: 8,
    opacity: 0.7,
  },
  message: {
    flex: 1,
    fontSize: 13,
    color: '#8E8E93',
    fontWeight: '400',
  },
  chevron: {
    marginLeft: 4,
    opacity: 0.5,
  },
  secondary: {
    fontSize: 12,
    color: '#8E8E93',
    opacity: 0.7,
    marginTop: 4,
    marginLeft: 22, // Align with message text
  },
  // Minimal variant
  minimalContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    marginVertical: 4,
  },
  minimalText: {
    fontSize: 12,
    color: '#8E8E93',
    fontWeight: '400',
    fontStyle: 'italic',
  },
  minimalArrow: {
    marginLeft: 4,
    opacity: 0.5,
  },
});
