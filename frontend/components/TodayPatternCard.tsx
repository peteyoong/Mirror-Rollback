/**
 * TodayPatternCard
 * Home screen keystone - Cross-Lens Synthesis
 * Shows title + 3 lines that feel like immediate recognition
 * 
 * Structure:
 * - Line 1: What you're feeling / doing
 * - Line 2: The tension / contradiction  
 * - Line 3: The pattern (recognition layer)
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
      
      {/* Divider */}
      <View style={[styles.divider, { backgroundColor: theme.border }]} />
      
      {/* CTA */}
      <TouchableOpacity
        style={styles.ctaContainer}
        onPress={handleReflect}
        activeOpacity={0.7}
      >
        <Text style={[styles.ctaIcon, { color: theme.textTertiary }]}>☐</Text>
        <Text style={[styles.ctaText, { color: theme.text }]}>Reflect</Text>
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
  divider: {
    height: 1,
    marginVertical: 14,
  },
  ctaContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  ctaIcon: {
    fontSize: 16,
  },
  ctaText: {
    fontSize: 14,
    fontWeight: '500',
  },
});
