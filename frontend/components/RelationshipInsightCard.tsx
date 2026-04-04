/**
 * RelationshipInsightCard V1.0
 * 
 * A 1:1 dynamic reflection that helps the user understand:
 * - What is happening between them
 * - What they need to shift in themselves
 * 
 * 6-SECTION STRUCTURE:
 * 1. Essence - What they are / how they move
 * 2. Friction - Where it clashes with you
 * 3. Tension - What happens between you
 * 4. Your Shift - What YOU need to adjust (MOST IMPORTANT)
 * 5. Gift - Why this person matters
 * 6. Try This - ONE specific action
 * 
 * VISUAL HIERARCHY:
 * 1. Title / dynamic
 * 2. Your Shift (EMPHASIZED)
 * 3. Tension
 * 4. Gift
 * 5. Essence / Friction
 * 6. Try This
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
import api from '../services/api';

interface RelationshipInsightData {
  success: boolean;
  version: string;
  other_name: string;
  relationship_type: string;
  essence: string;
  friction: string;
  tension: string;
  your_shift: string;
  gift: string;
  why_this_connection: string;  // NEW: Why this connection exists
  try_this: string;
  dynamic: {
    user_type: string;
    other_type: string;
    user_quality: string;
    other_quality: string;
  };
}

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
  const [data, setData] = useState<RelationshipInsightData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInsight();
  }, [userId, otherName, relationshipContext]);

  const loadInsight = async () => {
    console.log('[RelationshipInsight] Loading insight for:', { userId, otherName, relationshipContext });
    
    if (!userId || !otherName) {
      console.log('[RelationshipInsight] Missing userId or otherName');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        other_name: otherName,
        context: relationshipContext,
      });

      const url = `/relationship-insight/${userId}?${params}`;
      console.log('[RelationshipInsight] Calling API:', url);
      
      const response = await api.get(url);
      console.log('[RelationshipInsight] Response:', response.data);
      setData(response.data);
    } catch (err: any) {
      console.error('[RelationshipInsight] Error:', err);
      setError(err.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  // Split multi-line text into array
  const splitLines = (text: string): string[] => {
    return text.split('\n').filter(line => line.trim());
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Reading the dynamic...
          </Text>
        </View>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface }]}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>
          {error || 'Unable to load insight'}
        </Text>
        <TouchableOpacity onPress={loadInsight}>
          <Text style={[styles.retryText, { color: theme.accent }]}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView 
      style={[styles.container, { backgroundColor: theme.surface }]}
      showsVerticalScrollIndicator={false}
    >
      {/* Header */}
      <View style={styles.header}>
        {onClose && (
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Ionicons name="close" size={24} color={theme.textSecondary} />
          </TouchableOpacity>
        )}
        
        <Text style={[styles.otherName, { color: theme.text }]}>
          {data.other_name}
        </Text>
        
        <View style={styles.dynamicBadge}>
          <Text style={[styles.dynamicText, { color: theme.textTertiary }]}>
            {data.dynamic.user_quality} ↔ {data.dynamic.other_quality}
          </Text>
        </View>
      </View>

      {/* YOUR SHIFT - Most emphasized */}
      <View style={[styles.shiftSection, { borderColor: theme.accent }]}>
        <Text style={[styles.shiftLabel, { color: theme.accent }]}>
          YOUR SHIFT
        </Text>
        <View style={styles.shiftContent}>
          {splitLines(data.your_shift).map((line, idx) => (
            <Text 
              key={idx} 
              style={[styles.shiftLine, { color: theme.text }]}
            >
              {line}
            </Text>
          ))}
        </View>
      </View>

      {/* TENSION */}
      <View style={styles.section}>
        <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
          TENSION
        </Text>
        {splitLines(data.tension).map((line, idx) => (
          <Text 
            key={idx} 
            style={[styles.sectionText, { color: theme.text }]}
          >
            {line}
          </Text>
        ))}
      </View>

      {/* GIFT */}
      <View style={[styles.giftSection, { backgroundColor: theme.accent + '08' }]}>
        <Text style={[styles.giftLabel, { color: theme.accent }]}>
          GIFT
        </Text>
        {splitLines(data.gift).map((line, idx) => (
          <Text 
            key={idx} 
            style={[styles.giftText, { color: theme.text }]}
          >
            {line}
          </Text>
        ))}
      </View>

      {/* WHY THIS CONNECTION EXISTS (NEW) */}
      {data.why_this_connection && (
        <View style={[styles.whyConnectionSection, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Text style={[styles.whyConnectionLabel, { color: theme.textTertiary }]}>
            WHY THIS CONNECTION EXISTS
          </Text>
          {splitLines(data.why_this_connection).map((line, idx) => (
            <Text 
              key={idx} 
              style={[styles.whyConnectionText, { color: theme.text }]}
            >
              {line}
            </Text>
          ))}
        </View>
      )}

      {/* ESSENCE + FRICTION (compact) */}
      <View style={styles.contextSection}>
        <View style={styles.contextBlock}>
          <Text style={[styles.contextLabel, { color: theme.textTertiary }]}>
            ESSENCE
          </Text>
          <Text style={[styles.contextText, { color: theme.textSecondary }]}>
            {data.essence}
          </Text>
        </View>
        
        <View style={[styles.contextDivider, { backgroundColor: theme.border }]} />
        
        <View style={styles.contextBlock}>
          <Text style={[styles.contextLabel, { color: theme.textTertiary }]}>
            FRICTION
          </Text>
          {splitLines(data.friction).map((line, idx) => (
            <Text 
              key={idx} 
              style={[styles.contextText, { color: theme.textSecondary }]}
            >
              {line}
            </Text>
          ))}
        </View>
      </View>

      {/* TRY THIS - Action block */}
      <View style={[styles.tryThisSection, { backgroundColor: theme.background, borderColor: theme.border }]}>
        <View style={styles.tryThisHeader}>
          <Ionicons name="arrow-forward-circle" size={18} color={theme.accent} />
          <Text style={[styles.tryThisLabel, { color: theme.accent }]}>
            TRY THIS
          </Text>
        </View>
        <Text style={[styles.tryThisText, { color: theme.text }]}>
          {data.try_this}
        </Text>
      </View>

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
    padding: 24,
    paddingBottom: 16,
    alignItems: 'center',
  },
  closeButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    padding: 8,
  },
  otherName: {
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.5,
    marginBottom: 8,
  },
  dynamicBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  dynamicText: {
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 0.5,
  },

  // YOUR SHIFT - Primary emphasis
  shiftSection: {
    marginHorizontal: 20,
    marginBottom: 24,
    padding: 20,
    borderLeftWidth: 3,
    borderRadius: 2,
  },
  shiftLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.5,
    marginBottom: 12,
  },
  shiftContent: {
    gap: 8,
  },
  shiftLine: {
    fontSize: 17,
    fontWeight: '500',
    lineHeight: 26,
    letterSpacing: -0.2,
  },

  // Standard section
  section: {
    marginHorizontal: 20,
    marginBottom: 24,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 10,
  },
  sectionText: {
    fontSize: 15,
    lineHeight: 24,
    marginBottom: 4,
  },

  // GIFT section
  giftSection: {
    marginHorizontal: 20,
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
  },
  giftLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 10,
  },
  giftText: {
    fontSize: 15,
    lineHeight: 24,
    fontStyle: 'italic',
    marginBottom: 4,
  },

  // WHY THIS CONNECTION EXISTS section
  whyConnectionSection: {
    marginHorizontal: 20,
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  whyConnectionLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1,
    marginBottom: 12,
  },
  whyConnectionText: {
    fontSize: 15,
    lineHeight: 24,
    marginBottom: 4,
  },

  // Context section (Essence + Friction)
  contextSection: {
    marginHorizontal: 20,
    marginBottom: 24,
  },
  contextBlock: {
    marginBottom: 16,
  },
  contextDivider: {
    height: 1,
    marginVertical: 8,
    opacity: 0.5,
  },
  contextLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  contextText: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 2,
  },

  // TRY THIS section
  tryThisSection: {
    marginHorizontal: 20,
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  tryThisHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  tryThisLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 1.2,
  },
  tryThisText: {
    fontSize: 15,
    lineHeight: 24,
    fontWeight: '500',
  },

  bottomPadding: {
    height: 32,
  },
});

export default RelationshipInsightCard;
