import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors } from '../constants/colors';
import { format } from 'date-fns';
import { Ionicons } from '@expo/vector-icons';

interface JournalEntryItemProps {
  content: string;
  created_at: string;
  themes?: string[];
  onReflect?: (content: string) => void;
}

export default function JournalEntryItem({
  content,
  created_at,
  themes = [],
  onReflect,
}: JournalEntryItemProps) {
  const formattedDate = format(new Date(created_at), 'MMM d, yyyy');

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.date}>{formattedDate}</Text>
        {onReflect && (
          <TouchableOpacity 
            style={styles.reflectButton}
            onPress={() => onReflect(content)}
          >
            <Ionicons name="sparkles-outline" size={14} color={Colors.accent} />
            <Text style={styles.reflectButtonText}>Reflect with Mirror</Text>
          </TouchableOpacity>
        )}
      </View>
      <Text style={styles.content} numberOfLines={5}>
        {content}
      </Text>
      {themes.length > 0 && (
        <View style={styles.themesContainer}>
          {themes.map((theme, index) => (
            <View key={index} style={styles.themeTag}>
              <Text style={styles.themeText}>{theme}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  date: {
    fontSize: 12,
    color: Colors.textTertiary,
  },
  reflectButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: Colors.accent + '15',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 12,
  },
  reflectButtonText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.accent,
  },
  content: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  themesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 12,
  },
  themeTag: {
    backgroundColor: Colors.background,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 8,
    marginBottom: 8,
  },
  themeText: {
    fontSize: 11,
    color: Colors.textTertiary,
  },
});
