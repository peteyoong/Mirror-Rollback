/**
 * TodayPanel.tsx
 * 
 * Reusable component for the standardized Today tab layout across all lenses.
 * Provides consistent structure: Tone → What to Notice → Small Experiment → Reflect
 * 
 * Sections are conditionally rendered - if a prop is not provided, that section is omitted.
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';

export interface TodayPanelProps {
  // Date display
  date?: string;
  
  // Tone section (supports text or bullets)
  toneText?: string;
  toneBullets?: string[];
  toneSecondary?: string; // For "Background tone" merge
  
  // What to Notice section (bullets preferred)
  noticeBullets?: string[];
  noticeText?: string; // Fallback for paragraph format
  
  // Small Experiment section
  experimentText?: string;
  
  // Reflect section
  reflectQuestion?: string;
  onSaveToJournal?: () => void;
  
  // Optional header for cycles (Numerology)
  cyclesHeader?: React.ReactNode;
}

const TodayPanel: React.FC<TodayPanelProps> = ({
  date,
  toneText,
  toneBullets,
  toneSecondary,
  noticeBullets,
  noticeText,
  experimentText,
  reflectQuestion,
  onSaveToJournal,
  cyclesHeader,
}) => {
  // Check if we have tone content
  const hasTone = toneText || (toneBullets && toneBullets.length > 0);
  
  // Check if we have notice content
  const hasNotice = noticeText || (noticeBullets && noticeBullets.length > 0);
  
  // Check if we have experiment content
  const hasExperiment = experimentText && experimentText.trim().length > 0;
  
  // Check if we have reflect content
  const hasReflect = reflectQuestion && reflectQuestion.trim().length > 0;

  return (
    <View style={styles.container}>
      {/* Date Label */}
      {date && (
        <Text style={styles.dateLabel}>{date}</Text>
      )}
      
      {/* Cycles Header (Numerology only) */}
      {cyclesHeader}
      
      {/* TONE SECTION */}
      {hasTone && (
        <View style={styles.sectionCard}>
          <Text style={styles.sectionHeading}>Tone</Text>
          
          {/* Text format */}
          {toneText && (
            <Text style={styles.sectionBody}>{toneText}</Text>
          )}
          
          {/* Bullets format */}
          {toneBullets && toneBullets.length > 0 && (
            <View style={styles.bulletList}>
              {toneBullets.map((bullet, index) => (
                <View key={index} style={styles.bulletItem}>
                  <Text style={styles.bulletDot}>•</Text>
                  <Text style={styles.bulletText}>{bullet}</Text>
                </View>
              ))}
            </View>
          )}
          
          {/* Secondary tone (merged "Background tone") */}
          {toneSecondary && (
            <Text style={styles.toneSecondary}>{toneSecondary}</Text>
          )}
        </View>
      )}
      
      {/* WHAT TO NOTICE SECTION */}
      {hasNotice && (
        <View style={styles.sectionCard}>
          <Text style={styles.sectionHeading}>What to Notice</Text>
          
          {/* Bullets format (preferred) */}
          {noticeBullets && noticeBullets.length > 0 && (
            <View style={styles.bulletList}>
              {noticeBullets.map((bullet, index) => (
                <View key={index} style={styles.bulletItem}>
                  <Text style={styles.bulletDot}>•</Text>
                  <Text style={styles.bulletText}>{bullet}</Text>
                </View>
              ))}
            </View>
          )}
          
          {/* Text fallback */}
          {noticeText && !noticeBullets?.length && (
            <Text style={styles.sectionBody}>{noticeText}</Text>
          )}
        </View>
      )}
      
      {/* SMALL EXPERIMENT SECTION */}
      {hasExperiment && (
        <View style={styles.sectionCard}>
          <Text style={styles.sectionHeading}>Small Experiment</Text>
          <Text style={styles.sectionBody}>{experimentText}</Text>
        </View>
      )}
      
      {/* REFLECT SECTION */}
      {hasReflect && (
        <View style={styles.reflectCard}>
          <Text style={styles.reflectHeading}>Reflect</Text>
          <Text style={styles.reflectQuestion}>{reflectQuestion}</Text>
          
          {onSaveToJournal && (
            <TouchableOpacity
              style={styles.journalCTA}
              onPress={onSaveToJournal}
            >
              <Ionicons name="create-outline" size={16} color={Colors.accent} />
              <Text style={styles.journalCTAText}>Save to Journal</Text>
            </TouchableOpacity>
          )}
        </View>
      )}
    </View>
  );
};

export default TodayPanel;

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  dateLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 16,
  },
  // Section Card (Tone, What to Notice, Small Experiment)
  sectionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  sectionHeading: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  sectionBody: {
    fontSize: 15,
    lineHeight: 23,
    color: Colors.text,
  },
  // Bullet list styling
  bulletList: {
    gap: 8,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  bulletDot: {
    fontSize: 15,
    color: Colors.accent,
    marginRight: 10,
    marginTop: 1,
  },
  bulletText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
    flex: 1,
  },
  // Secondary tone (merged background tone)
  toneSecondary: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textSecondary,
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
    fontStyle: 'italic',
  },
  // Reflect Card (special styling)
  reflectCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 18,
    marginTop: 4,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: Colors.accent,
  },
  reflectHeading: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  reflectQuestion: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.text,
    fontStyle: 'italic',
  },
  // Journal CTA
  journalCTA: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  journalCTAText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.accent,
  },
});
