import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';

interface LensCardProps {
  name: string;
  description: string;
  helps_with: string;
  does_not: string;
}

export default function LensCard({
  name,
  description,
  helps_with,
  does_not,
}: LensCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>{name}</Text>
      <Text style={styles.description}>{description}</Text>

      <View style={styles.infoSection}>
        <View style={styles.infoRow}>
          <Ionicons name="checkmark-circle-outline" size={16} color={Colors.textSecondary} />
          <Text style={styles.infoLabel}>Helps with:</Text>
        </View>
        <Text style={styles.infoText}>{helps_with}</Text>
      </View>

      <View style={styles.infoSection}>
        <View style={styles.infoRow}>
          <Ionicons name="close-circle-outline" size={16} color={Colors.textTertiary} />
          <Text style={styles.infoLabel}>Does not:</Text>
        </View>
        <Text style={styles.infoText}>{does_not}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  description: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 16,
  },
  infoSection: {
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  infoLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginLeft: 6,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textTertiary,
    marginLeft: 22,
  },
});