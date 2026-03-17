/**
 * LifelineEventCard
 * 
 * Displays a single lifeline event in the timeline.
 * Designed to be reusable in both Life Lens and Forum contexts.
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { useTheme } from '../../contexts/ThemeContext';
import { ResonanceMarker, ResonanceModal, ChartResonance } from './ChartResonance';

export interface LifelineEvent {
  id: string;
  title: string;
  description?: string;
  year?: number;
  age?: number;
  category?: string;
  emotional_tone?: 'positive' | 'negative' | 'mixed' | 'neutral';
  impact_score?: number;
  // TASK 59: New separate scales for valence and significance
  emotional_valence?: number;  // 1-10: 1=very difficult, 5=mixed, 10=very positive
  significance_score?: number; // 1-10: 1=very low, 5=meaningful, 10=life-changing
  tags?: string[];
  privacy_level?: 'private' | 'shareable';
  created_at?: string;
  updated_at?: string;
}

interface Props {
  event: LifelineEvent;
  onPress?: (event: LifelineEvent) => void;
  onEdit?: (event: LifelineEvent) => void;
  onDelete?: (eventId: string) => Promise<void>;
  isCompact?: boolean;
  resonances?: ChartResonance[];
}

const CATEGORY_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  'Family': 'people-outline',
  'Relationships': 'heart-outline',
  'Career': 'briefcase-outline',
  'Health': 'fitness-outline',
  'Money': 'wallet-outline',
  'Spirituality': 'sparkles-outline',
  'Turning Point': 'git-branch-outline',
  'Loss': 'cloud-outline',
  'Achievement': 'trophy-outline',
  'Move': 'airplane-outline',
  'Identity': 'person-outline',
};

const TONE_COLORS = {
  positive: '#4CAF50',
  negative: '#E57373',
  mixed: '#FFB74D',
  neutral: '#90A4AE',
};

/**
 * Clean malformed event text that has numeric parsing artifacts.
 * Examples: "0 Transitioned to Australia", "2 -4 0 Parents divorced", "1970 2 -4 0 Parents divorced"
 * 
 * This function handles various patterns from import parsing:
 * - Leading single digits: "0 Started..."
 * - Year-like prefixes: "1970 2 -4 0 Parents..."
 * - Multiple numeric chunks: "2 -4 0 Something..."
 */
function cleanDisplayText(text: string): string {
  if (!text) return '';
  
  let cleaned = text;
  
  // Pattern 1: Remove leading year-like numbers (4 digits) followed by garbage
  // "1970 2 -4 0 Parents divorced" -> "Parents divorced"
  cleaned = cleaned.replace(/^\d{4}\s+[\d\s\-]+(?=[A-Za-z])/, '').trim();
  
  // Pattern 2: Remove leading numeric patterns like "0 ", "2 -4 0 ", etc.
  // "0 Started direct selling" -> "Started direct selling"
  cleaned = cleaned.replace(/^[\d\s\-]+(?=\s*[A-Za-z])/, '').trim();
  
  // Pattern 3: Remove isolated leading numbers or dashes at start
  // "-4 0 Something" -> "Something"
  cleaned = cleaned.replace(/^[-\d\s]+(?=[A-Za-z])/, '').trim();
  
  // If we cleaned too much and the result is empty, return original
  if (!cleaned) return text;
  
  // Capitalize first letter if it was lowercased after cleaning
  if (cleaned[0] && cleaned[0].match(/[a-z]/)) {
    cleaned = cleaned[0].toUpperCase() + cleaned.slice(1);
  }
  
  return cleaned;
}

// Alias for backward compatibility
const cleanDisplayTitle = cleanDisplayText;

export default function LifelineEventCard({ event, onPress, onEdit, onDelete, isCompact = false, resonances = [] }: Props) {
  const { theme } = useTheme();
  const icon = CATEGORY_ICONS[event.category || ''] || 'ellipse-outline';
  const toneColor = TONE_COLORS[event.emotional_tone || 'neutral'];
  
  // Modal state for resonance
  const [showResonanceModal, setShowResonanceModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const hasResonance = resonances && resonances.length > 0;

  // Clean the title and description for display
  const displayTitle = cleanDisplayText(event.title);
  const displayDescription = event.description ? cleanDisplayText(event.description) : '';

  // Handle delete with confirmation
  const handleDelete = () => {
    if (!onDelete) return;
    
    Alert.alert(
      'Delete this moment from your Lifeline?',
      'This will also update related patterns and insights.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            setIsDeleting(true);
            try {
              await onDelete(event.id);
            } catch (err) {
              Alert.alert('Error', 'Failed to delete moment. Please try again.');
            } finally {
              setIsDeleting(false);
            }
          },
        },
      ]
    );
  };

  return (
    <>
      <TouchableOpacity
        style={[
          styles.container,
          { backgroundColor: theme.surface, borderColor: theme.border },
          isDeleting && { opacity: 0.5 }
        ]}
        onPress={() => onPress?.(event)}
        activeOpacity={0.7}
        disabled={!onPress || isDeleting}
      >
        {/* Year/Age indicator */}
        <View style={[styles.yearBadge, { backgroundColor: theme.background }]}>
          <Text style={[styles.yearText, { color: theme.text }]}>
            {event.year || (event.age ? `Age ${event.age}` : '—')}
          </Text>
          {/* Resonance marker below year */}
          {hasResonance && (
            <ResonanceMarker
              resonances={resonances}
              onPress={() => setShowResonanceModal(true)}
              size="small"
            />
          )}
        </View>

        {/* Timeline connector */}
        <View style={styles.timelineConnector}>
          <View style={[styles.timelineLine, { backgroundColor: theme.border }]} />
          <View style={[styles.timelineDot, { backgroundColor: toneColor }]} />
          <View style={[styles.timelineLine, { backgroundColor: theme.border }]} />
        </View>

        {/* Content */}
        <View style={styles.content}>
          <View style={styles.headerRow}>
            <View style={styles.headerLeft}>
              {event.category && (
                <View style={[styles.categoryBadge, { backgroundColor: `${theme.accent}15` }]}>
                  <Ionicons name={icon} size={12} color={theme.accent} />
                  <Text style={[styles.categoryText, { color: theme.accent }]}>
                    {event.category}
                  </Text>
                </View>
              )}
              {/* Inline resonance indicator */}
              {hasResonance && (
                <TouchableOpacity
                  style={styles.resonanceInline}
                  onPress={() => setShowResonanceModal(true)}
                >
                  <Text style={[styles.resonanceIcon, { color: '#9B8AC4' }]}>✧</Text>
                </TouchableOpacity>
              )}
            </View>
            {onEdit && (
              <TouchableOpacity
                style={styles.editButton}
                onPress={() => onEdit(event)}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              >
                <Ionicons name="pencil-outline" size={16} color={theme.textTertiary} />
              </TouchableOpacity>
            )}
            {onDelete && (
              <TouchableOpacity
                style={styles.deleteButton}
                onPress={handleDelete}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                disabled={isDeleting}
              >
                <Ionicons name="trash-outline" size={16} color={isDeleting ? theme.border : '#E57373'} />
              </TouchableOpacity>
            )}
          </View>

          <Text style={[styles.title, { color: theme.text }]} numberOfLines={2}>
            {displayTitle}
          </Text>

          {!isCompact && event.description && (
            <Text style={[styles.description, { color: theme.textSecondary }]} numberOfLines={3}>
              {event.description}
            </Text>
          )}

          {/* Impact indicator */}
          {event.impact_score && event.impact_score >= 7 && (
            <View style={styles.impactRow}>
              <View style={[styles.impactDot, { backgroundColor: toneColor }]} />
              <Text style={[styles.impactText, { color: theme.textTertiary }]}>
                High impact moment
              </Text>
            </View>
          )}

          {/* Tags */}
          {!isCompact && event.tags && event.tags.length > 0 && (
            <View style={styles.tagsRow}>
              {event.tags.slice(0, 3).map((tag, index) => (
                <View key={index} style={[styles.tag, { backgroundColor: theme.background }]}>
                  <Text style={[styles.tagText, { color: theme.textTertiary }]}>#{tag}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      </TouchableOpacity>
      
      {/* Resonance Modal */}
      {hasResonance && (
        <ResonanceModal
          resonance={resonances[0]}
          visible={showResonanceModal}
          onClose={() => setShowResonanceModal(false)}
        />
      )}
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    marginBottom: 12,
  },
  yearBadge: {
    width: 50,
    paddingVertical: 6,
    paddingHorizontal: 4,
    borderRadius: 6,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  yearText: {
    fontSize: 13,
    fontWeight: '600',
  },
  timelineConnector: {
    width: 20,
    alignItems: 'center',
    marginRight: 12,
  },
  timelineLine: {
    flex: 1,
    width: 2,
  },
  timelineDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginVertical: 4,
  },
  content: {
    flex: 1,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  categoryBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 12,
    gap: 4,
  },
  categoryText: {
    fontSize: 11,
    fontWeight: '500',
  },
  editButton: {
    padding: 4,
  },
  deleteButton: {
    padding: 4,
    marginLeft: 8,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
    marginBottom: 4,
  },
  description: {
    fontSize: 13,
    lineHeight: 19,
    marginBottom: 8,
  },
  impactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  impactDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  impactText: {
    fontSize: 11,
    fontStyle: 'italic',
  },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: 8,
  },
  tag: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 10,
  },
  tagText: {
    fontSize: 11,
  },
  resonanceInline: {
    padding: 4,
  },
  resonanceIcon: {
    fontSize: 14,
    fontWeight: '600',
  },
});
