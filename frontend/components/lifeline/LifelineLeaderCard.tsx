/**
 * LifelineLeaderCard
 * 
 * Emotionally engaging hero card at the top of the Lifeline page.
 * Establishes psychological safety and purpose before the timeline.
 * 
 * Design: Full-width, elevated card with soft gradient
 * Content: Purpose statement + clear CTA
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';

interface Props {
  onAddMoment: () => void;
  eventCount: number;
}

export default function LifelineLeaderCard({ onAddMoment, eventCount }: Props) {
  const { theme, isDark } = useTheme();
  const [showExample, setShowExample] = useState(false);
  
  // Don't show for users with 10+ events - they're established
  if (eventCount >= 10) {
    return null;
  }
  
  return (
    <>
      <View style={[
        styles.container,
        { 
          backgroundColor: theme.surface,
          borderColor: theme.border,
        }
      ]}>
        {/* Subtle gradient overlay */}
        <LinearGradient
          colors={isDark 
            ? ['rgba(255,255,255,0.02)', 'transparent']
            : ['rgba(0,0,0,0.01)', 'transparent']
          }
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.gradientOverlay}
        />
        
        {/* Title */}
        <Text style={[styles.title, { color: theme.textSecondary }]}>
          The Moments That Shaped You
        </Text>
        
        {/* Main body */}
        <Text style={[styles.bodyText, { color: theme.text }]}>
          Some moments stay with you — long after they've passed.
        </Text>
        
        <Text style={[styles.bodyText, { color: theme.text }]}>
          Not because they were big, but because they meant something.
        </Text>
        
        <Text style={[styles.bodyText, { color: theme.text }]}>
          These moments shape how you open, how you protect, how you move through life — often without you realising it.
        </Text>
        
        <Text style={[styles.bodyText, { color: theme.text }]}>
          Your story already holds the answers.
        </Text>
        
        <Text style={[styles.bodyText, styles.lastParagraph, { color: theme.text }]}>
          This is a space to trace those moments, and begin to understand the patterns they've created.
        </Text>
        
        {/* Micro line - psychological safety */}
        <Text style={[styles.microLine, { color: theme.textTertiary }]}>
          Start with one moment — it doesn't have to be perfect.
        </Text>
        
        {/* Primary CTA */}
        {eventCount === 0 && (
          <TouchableOpacity
            style={[styles.ctaButton, { backgroundColor: theme.accent }]}
            onPress={onAddMoment}
            activeOpacity={0.8}
          >
            <Ionicons name="add-circle-outline" size={18} color="#FFFFFF" />
            <Text style={styles.ctaText}>Add your first moment</Text>
          </TouchableOpacity>
        )}
        
        {/* Secondary action */}
        <TouchableOpacity
          style={styles.secondaryAction}
          onPress={() => setShowExample(true)}
          activeOpacity={0.7}
        >
          <Text style={[styles.secondaryText, { color: theme.textTertiary }]}>
            See an example
          </Text>
        </TouchableOpacity>
        
        {/* Safety line */}
        <Text style={[styles.safetyLine, { color: theme.textTertiary }]}>
          This is for you. You can go at your own pace.
        </Text>
      </View>
      
      {/* Example Modal */}
      <Modal
        visible={showExample}
        transparent
        animationType="fade"
        onRequestClose={() => setShowExample(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: theme.surface }]}>
            <View style={styles.modalHeader}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>Example Moment</Text>
              <TouchableOpacity onPress={() => setShowExample(false)}>
                <Ionicons name="close" size={24} color={theme.textSecondary} />
              </TouchableOpacity>
            </View>
            
            <ScrollView showsVerticalScrollIndicator={false}>
              {/* Example card */}
              <View style={[styles.exampleCard, { backgroundColor: theme.background, borderColor: theme.border }]}>
                <View style={styles.exampleHeader}>
                  <Text style={[styles.exampleYear, { color: theme.textSecondary }]}>2018</Text>
                  <View style={[styles.exampleCategory, { backgroundColor: `${theme.accent}20` }]}>
                    <Text style={[styles.exampleCategoryText, { color: theme.accent }]}>Relationship</Text>
                  </View>
                </View>
                <Text style={[styles.exampleTitle, { color: theme.text }]}>
                  The conversation that changed everything
                </Text>
                <Text style={[styles.exampleDescription, { color: theme.textSecondary }]}>
                  I finally told my parents about my career change. I'd been dreading it for months, but their reaction surprised me. For the first time, I felt like they saw me as an adult.
                </Text>
              </View>
              
              <Text style={[styles.exampleNote, { color: theme.textTertiary }]}>
                Notice: This isn't about dates or perfect details. It's about what the moment meant to you.
              </Text>
              
              <TouchableOpacity
                style={[styles.exampleCta, { backgroundColor: theme.accent }]}
                onPress={() => {
                  setShowExample(false);
                  onAddMoment();
                }}
              >
                <Text style={styles.exampleCtaText}>Add your own moment</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 20,
    marginBottom: 20,
    position: 'relative',
    overflow: 'hidden',
  },
  gradientOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  title: {
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 16,
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 24,
    marginBottom: 12,
  },
  lastParagraph: {
    marginBottom: 16,
  },
  microLine: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 20,
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginBottom: 12,
  },
  ctaText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#FFFFFF',
  },
  secondaryAction: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  secondaryText: {
    fontSize: 14,
    textDecorationLine: 'underline',
  },
  safetyLine: {
    fontSize: 12,
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(128,128,128,0.2)',
  },
  
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    borderRadius: 16,
    padding: 20,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '500',
  },
  exampleCard: {
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    padding: 16,
    marginBottom: 16,
  },
  exampleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  exampleYear: {
    fontSize: 14,
    fontWeight: '500',
  },
  exampleCategory: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  exampleCategoryText: {
    fontSize: 11,
    fontWeight: '500',
  },
  exampleTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 8,
  },
  exampleDescription: {
    fontSize: 14,
    lineHeight: 21,
  },
  exampleNote: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 19,
  },
  exampleCta: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  exampleCtaText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#FFFFFF',
  },
});
