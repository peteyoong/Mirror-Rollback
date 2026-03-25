/**
 * TodayPatternCard
 * Home screen keystone - Cross-Lens Synthesis
 * Shows title + 3 lines that feel like immediate recognition
 * + contextual follow-through line based on dominant source
 * 
 * Structure:
 * - Line 1: What you're feeling / doing
 * - Line 2: The tension / contradiction  
 * - Line 3: The pattern (recognition layer)
 * - Follow-through: Contextual bridge to relevant lens
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import api from '../services/api';

interface TodayPatternData {
  title: string;
  lines: string[];
  confidence: number;
  sources: string[];
  date: string;
  cached: boolean;
  follow_through?: string;
  follow_through_route?: string;
}

interface TodayPatternCardProps {
  userId: string;
  theme: any;
  onReflect?: () => void;
}

export default function TodayPatternCard({ userId, theme, onReflect }: TodayPatternCardProps) {
  const router = useRouter();
  const [data, setData] = useState<TodayPatternData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    const fetchPattern = async () => {
      try {
        setIsLoading(true);
        const response = await api.get(`/today-pattern/${userId}`);
        setData(response.data);
        setError(null);
      } catch (err) {
        console.error('[TodayPatternCard] Error:', err);
        setError('Could not load pattern');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPattern();
  }, [userId]);

  const handleReflect = () => {
    if (onReflect) {
      onReflect();
    } else {
      router.push('/(tabs)/reflect?view=mirror');
    }
  };

  const handleFollowThrough = () => {
    if (!data?.follow_through_route) return;
    
    switch (data.follow_through_route) {
      case 'reflect':
        router.push('/(tabs)/reflect');
        break;
      case 'human_design':
        router.push('/lenses/human-design');
        break;
      case 'astrology':
        router.push('/lenses/astrology?tab=today');
        break;
      case 'enneagram':
        router.push('/lenses/enneagram');
        break;
      default:
        break;
    }
  };

  // Don't render if no data
  if (!isLoading && (!data || !data.lines || data.lines.length === 0)) {
    return null;
  }

  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.surface, borderColor: theme.accent + '30' }]}>
      {/* Label */}
      <Text style={[styles.label, { color: theme.textTertiary }]}>TODAY'S PATTERN</Text>
      
      {/* Title */}
      <Text style={[styles.title, { color: theme.text }]}>
        {data?.title}
      </Text>
      
      {/* Three lines */}
      <View style={styles.linesContainer}>
        {data?.lines.map((line, index) => (
          <Text 
            key={index} 
            style={[
              styles.line, 
              { color: index === 2 ? theme.text : theme.textSecondary },
              index === 2 && styles.lastLine
            ]}
          >
            {line}
          </Text>
        ))}
      </View>
      
      {/* Follow-through line - tappable bridge to relevant lens */}
      {data?.follow_through && (
        <TouchableOpacity
          style={styles.followThroughContainer}
          onPress={handleFollowThrough}
          activeOpacity={0.7}
          disabled={!data.follow_through_route}
        >
          <Text style={[styles.followThrough, { color: theme.textTertiary }]}>
            {data.follow_through}
            {data.follow_through_route && ' →'}
          </Text>
        </TouchableOpacity>
      )}
      
      {/* Divider */}
      <View style={[styles.divider, { backgroundColor: theme.border }]} />
      
      {/* CTA - Clear action */}
      <TouchableOpacity
        style={styles.ctaContainer}
        onPress={handleReflect}
        activeOpacity={0.7}
      >
        <Text style={[styles.ctaText, { color: theme.text }]}>Write about this</Text>
        <Text style={[styles.ctaArrow, { color: theme.textTertiary }]}>→</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    marginBottom: 12,
  },
  label: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 24,
    marginBottom: 14,
  },
  linesContainer: {
    gap: 8,
  },
  line: {
    fontSize: 15,
    lineHeight: 22,
  },
  lastLine: {
    fontStyle: 'italic',
  },
  followThroughContainer: {
    marginTop: 12,
    paddingTop: 10,
  },
  followThrough: {
    fontSize: 13,
    lineHeight: 18,
    fontStyle: 'italic',
  },
  divider: {
    height: 1,
    marginVertical: 14,
  },
  ctaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '500',
  },
  ctaArrow: {
    fontSize: 16,
    fontWeight: '400',
  },
});
