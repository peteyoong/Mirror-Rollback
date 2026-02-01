import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../constants/colors';
import { format } from 'date-fns';

interface JournalEntryItemProps {
  content: string;
  created_at: string;
  themes?: string[];
}

export default function JournalEntryItem({
  content,
  created_at,
  themes = [],
}: JournalEntryItemProps) {
  const formattedDate = format(new Date(created_at), 'MMM d, yyyy');

  return (
    <View style={styles.container}>
      <Text style={styles.date}>{formattedDate}</Text>
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
  date: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 8,
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