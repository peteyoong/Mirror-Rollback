import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

/**
 * CrossLensChainRow (V1)
 * 
 * A subtle, quiet chaining row that connects patterns across lenses.
 * 
 * GOAL: Make Mirror feel like one connected intelligence, not separate feature pages.
 * 
 * User should feel:
 * - "this is the same thing"
 * - "I'm seeing it from another angle"
 * - "the app is connecting the dots for me"
 * 
 * STYLE:
 * - Small text
 * - Low visual weight
 * - Optional chevron or inline arrow
 * - No big cards
 * - No competing borders
 * - Feels like connective tissue, not another content block
 */

interface CrossLensChainRowProps {
  // Current lens context
  currentLens: 'numerology' | 'astrology' | 'bazi' | 'home';
  
  // Optional: Pattern showing elsewhere
  showsInHome?: boolean;
  showsInOtherLens?: string; // e.g., "astrology", "numerology"
  
  // Optional: Custom message override
  customMessage?: string;
  
  // Optional: Secondary line for extra clarity
  secondaryLine?: string;
  
  // Navigation target (defaults to home)
  navigateTo?: string;
  
  // Hide if not useful
  hide?: boolean;
}

const CHAIN_MESSAGES = {
  toHome: [
    "Also showing up in your Home today",
    "This pattern is active on Home",
    "Visible on Home right now",
  ],
  fromAngle: [
    "Seen from another angle",
    "Same pattern, different view",
    "Another perspective on this",
  ],
  elsewhere: [
    "This pattern shows up elsewhere too",
    "Showing up in more than one place",
    "Connected across your profile",
  ],
};

const SECONDARY_LINES = [
  "Same pattern. Different proof.",
  "This is showing up in more than one place.",
  "The same signal, just louder here.",
];

export default function CrossLensChainRow({
  currentLens,
  showsInHome = true,
  showsInOtherLens,
  customMessage,
  secondaryLine,
  navigateTo = '/(tabs)',
  hide = false,
}: CrossLensChainRowProps) {
  const router = useRouter();
  
  if (hide) return null;
  
  // Determine message
  let message = customMessage;
  if (!message) {
    if (showsInHome && currentLens !== 'home') {
      message = CHAIN_MESSAGES.toHome[Math.floor(Math.random() * CHAIN_MESSAGES.toHome.length)];
    } else if (showsInOtherLens) {
      message = CHAIN_MESSAGES.fromAngle[Math.floor(Math.random() * CHAIN_MESSAGES.fromAngle.length)];
    } else {
      message = CHAIN_MESSAGES.elsewhere[Math.floor(Math.random() * CHAIN_MESSAGES.elsewhere.length)];
    }
  }
  
  // Determine navigation label
  const navLabel = showsInHome ? 'Home' : showsInOtherLens ? showsInOtherLens : 'explore';
  
  const handlePress = () => {
    if (navigateTo) {
      router.push(navigateTo as any);
    }
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
 * Minimal variant - even more subtle
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
