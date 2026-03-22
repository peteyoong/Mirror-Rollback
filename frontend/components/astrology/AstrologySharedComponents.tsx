// ============================================
// ASTROLOGY SHARED COMPONENTS
// Small reusable UI pieces
// ============================================

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

// Section Header Component
interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  theme: any;
}

export const AstrologySectionHeader: React.FC<SectionHeaderProps> = ({ 
  title, 
  subtitle, 
  theme 
}) => (
  <View style={styles.sectionHeader}>
    <Text style={[styles.sectionTitle, { color: theme.accent }]}>{title}</Text>
    {subtitle && (
      <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>{subtitle}</Text>
    )}
  </View>
);

// Collapsible Section Component
interface CollapsibleSectionProps {
  title: string;
  hint?: string;
  expanded: boolean;
  onToggle: () => void;
  theme: any;
  children: React.ReactNode;
}

export const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  hint,
  expanded,
  onToggle,
  theme,
  children
}) => (
  <TouchableOpacity
    style={[styles.collapsibleSection, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
    onPress={onToggle}
    activeOpacity={0.7}
  >
    <View style={styles.collapsibleHeader}>
      <Text style={[styles.collapsibleTitle, { color: theme.textSecondary }]}>{title}</Text>
      <Text style={[styles.collapsibleIcon, { color: theme.textTertiary }]}>
        {expanded ? '▴' : '▾'}
      </Text>
    </View>
    {!expanded && hint && (
      <Text style={[styles.collapsibleHint, { color: theme.textTertiary }]}>{hint}</Text>
    )}
    {expanded && (
      <View style={styles.collapsibleContent}>
        {children}
      </View>
    )}
  </TouchableOpacity>
);

// Context Line Component
interface ContextLineProps {
  text: string;
  color?: string;
  fontWeight?: 'normal' | '500' | 'bold';
  fontStyle?: 'normal' | 'italic';
  theme: any;
}

export const ContextLine: React.FC<ContextLineProps> = ({
  text,
  color,
  fontWeight = 'normal',
  fontStyle = 'normal',
  theme
}) => (
  <Text style={[
    styles.contextLine, 
    { 
      color: color || theme.textTertiary,
      fontWeight,
      fontStyle 
    }
  ]}>
    ↳ {text}
  </Text>
);

// Reflection Question Card
interface ReflectionCardProps {
  question: string;
  theme: any;
}

export const ReflectionCard: React.FC<ReflectionCardProps> = ({ question, theme }) => (
  <View style={[styles.reflectionCard, { backgroundColor: theme.accent + '08', borderColor: theme.accent + '20' }]}>
    <Text style={[styles.reflectionLabel, { color: theme.accent }]}>A QUESTION</Text>
    <Text style={[styles.reflectionText, { color: theme.text }]}>{question}</Text>
  </View>
);

// Insight Card Component
interface InsightCardProps {
  title: string;
  content: string;
  titleColor?: string;
  backgroundColor?: string;
  borderColor?: string;
  theme: any;
}

export const InsightCard: React.FC<InsightCardProps> = ({
  title,
  content,
  titleColor,
  backgroundColor,
  borderColor,
  theme
}) => (
  <View style={[
    styles.insightCard, 
    { 
      backgroundColor: backgroundColor || theme.surface, 
      borderColor: borderColor || theme.border 
    }
  ]}>
    <Text style={[styles.insightTitle, { color: titleColor || theme.textSecondary }]}>{title}</Text>
    <Text style={[styles.insightContent, { color: theme.text }]}>{content}</Text>
  </View>
);

// Pill/Chip Component
interface ChipProps {
  text: string;
  color?: string;
  backgroundColor?: string;
  theme: any;
}

export const Chip: React.FC<ChipProps> = ({ text, color, backgroundColor, theme }) => (
  <View style={[styles.chip, { backgroundColor: backgroundColor || theme.accent + '10' }]}>
    <Text style={[styles.chipText, { color: color || theme.accent }]}>{text}</Text>
  </View>
);

// Styles
const styles = StyleSheet.create({
  sectionHeader: {
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 12,
  },
  collapsibleSection: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 14,
    marginBottom: 4,
  },
  collapsibleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  collapsibleTitle: {
    fontSize: 13,
    fontWeight: '500',
  },
  collapsibleIcon: {
    fontSize: 11,
    marginLeft: 8,
  },
  collapsibleHint: {
    fontSize: 11,
    marginTop: 4,
  },
  collapsibleContent: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(0,0,0,0.08)',
  },
  contextLine: {
    fontSize: 12,
    lineHeight: 18,
  },
  reflectionCard: {
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    marginTop: 12,
  },
  reflectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  reflectionText: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  insightCard: {
    flex: 1,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 12,
  },
  insightTitle: {
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  insightContent: {
    fontSize: 13,
    lineHeight: 19,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 6,
    marginBottom: 6,
  },
  chipText: {
    fontSize: 11,
    fontWeight: '500',
  },
});
