/**
 * NarrativeFlowView V1.0
 * 
 * SHARED COMPONENT for displaying 5-part Narrative Flow.
 * Used by:
 * - Forum Live Field (forums/[id].tsx) 
 * - Relationship Narrative Flow (RelationshipInsightCard.tsx)
 * 
 * 5-PART STRUCTURE:
 * 1. FIELD STATE - Awareness (what's happening)
 * 2. YOUR POSITION - Responsibility (where you stand)
 * 3. TRAJECTORY - Tension (if nothing changes)
 * 4. STORY - Meaning (what this tends to become)
 * 5. THE MOVE - Possibility (subtle action opening)
 * 
 * CONTEXT MODES:
 * - "forum": Field-first language ("the space", "the room")
 * - "relationship": Intimate language ("between you", "this connection")
 * 
 * UI PRINCIPLES:
 * - One continuous narrative flow, not separate cards
 * - Subtle dividers between sections
 * - Story is expandable (doesn't overpower present-moment read)
 * - "The Move" is highlighted with accent
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Platform,
} from 'react-native';

export interface NarrativeFlowData {
  // Core sections
  field_state: string;
  your_position: string | null;
  your_position_type?: string;
  trajectory: string | null;
  trajectory_type?: string;
  trajectory_severity?: 'low' | 'moderate' | 'high' | 'positive';
  story: string;
  the_move: string | null;
  
  // Metadata
  field_temperature: 'warm' | 'cool' | 'charged' | 'still' | 'quiet' | 'present';
  is_breakthrough?: boolean;
  other_name?: string;
}

interface NarrativeFlowViewProps {
  data: NarrativeFlowData;
  mode: 'forum' | 'relationship';
  theme: {
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    textTertiary: string;
    accent: string;
    border: string;
  };
  onStoryPress?: () => void;
  showExpandedStory?: boolean;
}

const TEMPERATURE_EMOJI: Record<string, string> = {
  warm: '🔥',
  charged: '⚡',
  still: '🌊',
  cool: '❄️',
  quiet: '🌙',
  present: '✦',
};

const NarrativeFlowView: React.FC<NarrativeFlowViewProps> = ({
  data,
  mode,
  theme,
  onStoryPress,
  showExpandedStory = false,
}) => {
  const [storyExpanded, setStoryExpanded] = useState(showExpandedStory);
  
  // Mode-specific styling
  const isRelationship = mode === 'relationship';
  
  // Relationship mode: more intimate, tighter, warmer
  const containerStyle = isRelationship ? {
    paddingHorizontal: 16,
    paddingVertical: 20,
  } : {
    paddingHorizontal: 12,
    paddingVertical: 16,
  };
  
  // Section labels based on mode
  const positionLabel = isRelationship ? 'where you stand' : 'your position';
  const trajectoryLabel = isRelationship ? 'if this continues' : 'if nothing changes';
  const storyLabel = isRelationship 
    ? `what this connection tends to become` 
    : 'what this space tends to become';
  
  const getTrajectoryColor = (severity?: string) => {
    if (severity === 'positive') return '#10B981';
    if (severity === 'moderate' || severity === 'high') return '#F59200';
    return theme.textSecondary;
  };

  const handleStoryPress = () => {
    if (onStoryPress) {
      onStoryPress();
    } else {
      setStoryExpanded(!storyExpanded);
    }
  };
  
  // Truncate story for collapsed view
  const truncatedStory = data.story.length > 120 && !storyExpanded
    ? data.story.substring(0, 120).trim() + '...'
    : data.story;

  return (
    <View style={[
      styles.container, 
      { backgroundColor: theme.surface },
      containerStyle,
    ]}>
      
      {/* === SECTION 1: FIELD STATE (Awareness) === */}
      <View style={styles.section}>
        {/* Header with temperature */}
        <View style={styles.fieldHeader}>
          <Text style={styles.fieldEmoji}>
            {TEMPERATURE_EMOJI[data.field_temperature] || '✦'}
          </Text>
          <Text style={[styles.fieldTemp, { color: theme.textSecondary }]}>
            {data.field_temperature}
          </Text>
        </View>
        
        <Text style={[
          styles.fieldText, 
          { color: theme.text },
          isRelationship && styles.fieldTextRelationship,
        ]}>
          {data.field_state}
        </Text>
      </View>
      
      {/* Subtle divider */}
      <View style={[styles.divider, { backgroundColor: theme.border + '30' }]} />
      
      {/* === SECTION 2: YOUR POSITION (Responsibility) === */}
      {data.your_position && (
        <>
          <View style={styles.section}>
            <Text style={[
              styles.sectionHint, 
              { color: isRelationship ? theme.accent : theme.accent }
            ]}>
              {positionLabel}
            </Text>
            <Text style={[
              styles.positionText, 
              { color: theme.text },
              isRelationship && styles.positionTextRelationship,
            ]}>
              {data.your_position}
            </Text>
          </View>
          
          <View style={[styles.divider, { backgroundColor: theme.border + '30' }]} />
        </>
      )}
      
      {/* === SECTION 3: TRAJECTORY (Tension) === */}
      {data.trajectory && (
        <>
          <View style={styles.section}>
            <Text style={[
              styles.sectionHint, 
              { color: getTrajectoryColor(data.trajectory_severity) }
            ]}>
              {trajectoryLabel}
            </Text>
            <Text style={[
              styles.trajectoryText, 
              { color: theme.text },
              isRelationship && styles.trajectoryTextRelationship,
            ]}>
              {data.trajectory}
            </Text>
          </View>
          
          <View style={[styles.divider, { backgroundColor: theme.border + '30' }]} />
        </>
      )}
      
      {/* === SECTION 4: STORY (Meaning - What this tends to become) === */}
      <TouchableOpacity 
        style={styles.section}
        onPress={handleStoryPress}
        activeOpacity={0.8}
      >
        <Text style={[styles.sectionHint, { color: theme.textSecondary }]}>
          {storyLabel}
        </Text>
        <Text style={[
          styles.storyText, 
          { color: theme.text },
          isRelationship && styles.storyTextRelationship,
        ]}>
          {truncatedStory}
        </Text>
        {data.story.length > 120 && (
          <Text style={[styles.storyToggle, { color: theme.accent }]}>
            {storyExpanded ? 'Show less' : 'Read more →'}
          </Text>
        )}
      </TouchableOpacity>
      
      {/* === SECTION 5: THE MOVE (Possibility) === */}
      {data.the_move && (
        <>
          <View style={[
            styles.moveDivider, 
            { backgroundColor: theme.accent + '20' }
          ]} />
          
          <View style={[
            styles.moveSection,
            isRelationship && styles.moveSectionRelationship,
          ]}>
            <Text style={[styles.moveHint, { color: theme.accent }]}>✦</Text>
            <Text style={[
              styles.moveText, 
              { color: theme.text },
              isRelationship && styles.moveTextRelationship,
            ]}>
              {data.the_move}
            </Text>
          </View>
        </>
      )}
      
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.06,
        shadowRadius: 8,
      },
      android: {
        elevation: 2,
      },
    }),
  },
  
  // Section base
  section: {
    paddingVertical: 12,
  },
  
  // Field State (Section 1)
  fieldHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  fieldEmoji: {
    fontSize: 16,
  },
  fieldTemp: {
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 0.5,
    textTransform: 'lowercase',
  },
  fieldText: {
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '500',
  },
  fieldTextRelationship: {
    fontSize: 17,
    lineHeight: 26,
    fontWeight: '600',
  },
  
  // Dividers
  divider: {
    height: 1,
    marginVertical: 4,
  },
  moveDivider: {
    height: 2,
    marginVertical: 8,
  },
  
  // Section hints
  sectionHint: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'lowercase',
    marginBottom: 6,
  },
  
  // Your Position (Section 2)
  positionText: {
    fontSize: 15,
    lineHeight: 23,
  },
  positionTextRelationship: {
    fontSize: 16,
    lineHeight: 25,
  },
  
  // Trajectory (Section 3)
  trajectoryText: {
    fontSize: 15,
    lineHeight: 23,
  },
  trajectoryTextRelationship: {
    fontSize: 16,
    lineHeight: 25,
  },
  
  // Story (Section 4)
  storyText: {
    fontSize: 14,
    lineHeight: 22,
    opacity: 0.9,
  },
  storyTextRelationship: {
    fontSize: 15,
    lineHeight: 24,
  },
  storyToggle: {
    fontSize: 13,
    fontWeight: '500',
    marginTop: 8,
  },
  
  // The Move (Section 5)
  moveSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    paddingVertical: 12,
  },
  moveSectionRelationship: {
    paddingVertical: 14,
    paddingHorizontal: 4,
  },
  moveHint: {
    fontSize: 14,
    marginTop: 2,
  },
  moveText: {
    flex: 1,
    fontSize: 15,
    lineHeight: 23,
    fontWeight: '500',
  },
  moveTextRelationship: {
    fontSize: 16,
    lineHeight: 25,
    fontWeight: '600',
  },
});

export default NarrativeFlowView;
