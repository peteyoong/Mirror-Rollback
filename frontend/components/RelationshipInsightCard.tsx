/**
 * RelationshipInsightCard V2.0
 * 
 * NOW: 5-part Relationship Narrative Flow
 * Uses the same structure as Forum Live Field, adapted for 1:1 dynamics.
 * 
 * 5-PART STRUCTURE (strict order):
 * 1. FIELD STATE - What's happening between you two
 * 2. YOUR POSITION - Where you stand in this dynamic
 * 3. TRAJECTORY - What happens if nothing changes
 * 4. STORY - What this connection tends to become
 * 5. THE MOVE - Subtle action opening
 * 
 * DESIGN PRINCIPLES:
 * - More intimate than Forum (tighter, warmer, more immediate)
 * - Uses "between you", "this connection" language
 * - Story is expandable, doesn't overpower present-moment read
 * - Other person's name is prominent ("Between you and Sarah")
 * 
 * TONE: Intimate, calm, clear, slightly premium, not clinical
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Platform,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import NarrativeFlowView, { NarrativeFlowData } from './NarrativeFlowView';
import { getRelationshipNarrativeFlow, RelationshipNarrativeFlowResponse } from '../services/api';

interface RelationshipInsightCardProps {
  userId: string;
  otherName: string;
  relationshipContext?: string;
  theme: {
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    textTertiary: string;
    accent: string;
    border: string;
  };
  onClose?: () => void;
}

const RelationshipInsightCard: React.FC<RelationshipInsightCardProps> = ({
  userId,
  otherName,
  relationshipContext = '',
  theme,
  onClose,
}) => {
  const [data, setData] = useState<RelationshipNarrativeFlowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNarrativeFlow();
  }, [userId, otherName, relationshipContext]);

  const loadNarrativeFlow = async () => {
    console.log('[RelationshipInsight] Loading narrative flow for:', { userId, otherName, relationshipContext });
    
    if (!userId || !otherName) {
      console.log('[RelationshipInsight] Missing userId or otherName');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await getRelationshipNarrativeFlow(
        userId,
        otherName,
        relationshipContext
      );
      
      console.log('[RelationshipInsight] Response:', response);
      setData(response);
    } catch (err: any) {
      console.error('[RelationshipInsight] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading what's between you...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !data || !data.success) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to read this dynamic'}
        </Text>
        <TouchableOpacity onPress={loadNarrativeFlow}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Transform API response to NarrativeFlowData
  const narrativeData: NarrativeFlowData = {
    field_state: data.field_state,
    your_position: data.your_position,
    your_position_type: data.your_position_type,
    trajectory: data.trajectory,
    trajectory_type: data.trajectory_type,
    trajectory_severity: data.trajectory_severity,
    story: data.story,
    the_move: data.the_move,
    field_temperature: data.field_temperature,
    is_breakthrough: data.is_breakthrough,
    other_name: data.other_name,
  };

  return (
    <ScrollView 
      style={[styles.container, { backgroundColor: theme.background }]}
      contentContainerStyle={styles.scrollContent}
      showsVerticalScrollIndicator={false}
    >
      {/* Header with name and close button */}
      <View style={styles.header}>
        {onClose && (
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Ionicons name="close" size={24} color={theme.textSecondary} />
          </TouchableOpacity>
        )}
        
        <Text style={[styles.otherName, { color: theme.text }]}>
          {data.other_name}
        </Text>
        
        {/* Intimate connection subtitle */}
        <Text style={[styles.connectionSubtitle, { color: theme.textTertiary }]}>
          Between you and {data.other_name}
        </Text>
      </View>

      {/* Main Narrative Flow */}
      <NarrativeFlowView
        data={narrativeData}
        mode="relationship"
        theme={theme}
      />

      {/* Signal confidence indicator (subtle) */}
      {data.signal_confidence === 'low' && (
        <View style={[styles.signalNote, { backgroundColor: theme.surface }]}>
          <Text style={[styles.signalNoteText, { color: theme.textTertiary }]}>
            ✦ More signal will deepen this reading over time
          </Text>
        </View>
      )}

      {/* Breakthrough indicator */}
      {data.is_breakthrough && (
        <View style={[styles.breakthroughNote, { backgroundColor: theme.accent + '10' }]}>
          <Text style={[styles.breakthroughText, { color: theme.accent }]}>
            ✦ Something is shifting in this connection
          </Text>
        </View>
      )}

      <View style={styles.bottomPadding} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    borderRadius: 20,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.08,
        shadowRadius: 16,
      },
      android: {
        elevation: 4,
      },
    }),
  },
  scrollContent: {
    padding: 20,
  },
  loadingContainer: {
    padding: 48,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    fontStyle: 'italic',
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
    padding: 32,
  },
  retryText: {
    fontSize: 14,
    textAlign: 'center',
    fontWeight: '600',
  },
  
  // Header
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  closeButton: {
    position: 'absolute',
    top: 0,
    right: 0,
    padding: 8,
  },
  otherName: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.5,
    marginBottom: 6,
  },
  connectionSubtitle: {
    fontSize: 13,
    fontStyle: 'italic',
    letterSpacing: 0.3,
  },

  // Signal confidence note
  signalNote: {
    marginTop: 16,
    padding: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  signalNoteText: {
    fontSize: 12,
    fontStyle: 'italic',
  },

  // Breakthrough indicator
  breakthroughNote: {
    marginTop: 16,
    padding: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  breakthroughText: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.3,
  },

  bottomPadding: {
    height: 32,
  },
});

export default RelationshipInsightCard;
