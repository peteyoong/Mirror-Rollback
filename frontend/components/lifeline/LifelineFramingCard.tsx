/**
 * LifelineFramingCard
 * 
 * Smart collapsible framing card that explains the purpose of Lifeline.
 * - Expanded by default for users with < 10 moments
 * - Collapsed by default for users with 10+ moments
 * - Never fully hidden - always shows a teaser in collapsed state
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ScrollView,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { LinearGradient } from 'expo-linear-gradient';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface Props {
  onAddMoment: () => void;
  eventCount: number;
  birthYear?: number;
  currentYear?: number;
}

export default function LifelineFramingCard({ 
  onAddMoment, 
  eventCount,
  birthYear,
  currentYear = new Date().getFullYear(),
}: Props) {
  const { theme, isDark } = useTheme();
  const [showExample, setShowExample] = useState(false);
  
  // Determine default expanded state based on event count and data density
  const yearsOfData = birthYear ? currentYear - birthYear : 0;
  const eventDensity = yearsOfData > 0 ? eventCount / yearsOfData : 0;
  const isLowDataUser = eventCount < 10 || eventDensity < 0.2;
  
  const [isExpanded, setIsExpanded] = useState(isLowDataUser);
  
  // Update expanded state when event count changes significantly
  useEffect(() => {
    if (eventCount < 10) {
      setIsExpanded(true);
    }
  }, [eventCount]);
  
  const toggleExpanded = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setIsExpanded(!isExpanded);
  };
  
  const ctaText = eventCount === 0 ? "Add your first moment" : "Add another moment";
  
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
        
        {/* Header - always visible */}
        <TouchableOpacity 
          style={styles.headerRow}
          onPress={toggleExpanded}
          activeOpacity={0.7}
        >
          <View style={styles.headerContent}>
            <Text style={[styles.eyebrow, { color: theme.textSecondary }]}>
              THE MOMENTS THAT SHAPED YOU
            </Text>
            {!isExpanded && (
              <Text style={[styles.teaserText, { color: theme.textSecondary }]}>
                Big life moments often shape how we respond, protect, and grow.
              </Text>
            )}
          </View>
          <View style={styles.expandControl}>
            <Text style={[styles.expandText, { color: theme.textTertiary }]}>
              {isExpanded ? 'Collapse' : 'Why this matters'}
            </Text>
            <Ionicons 
              name={isExpanded ? 'chevron-up' : 'chevron-down'} 
              size={20} 
              color={theme.textTertiary} 
            />
          </View>
        </TouchableOpacity>
        
        {/* Expanded content */}
        {isExpanded && (
          <View style={styles.expandedContent}>
            <Text style={[styles.bodyText, { color: theme.text }]}>
              Some moments stay with you long after they've passed.
            </Text>
            
            <Text style={[styles.bodyText, { color: theme.text }]}>
              Not because they were big, but because they meant something.
            </Text>
            
            <Text style={[styles.bodyText, { color: theme.text }]}>
              These moments shape how you open, how you protect, how you move through life — often without you realising it.
            </Text>
            
            <Text style={[styles.bodyText, { color: theme.text }]}>
              Reflecting on them can be powerful on its own.
            </Text>
            
            <Text style={[styles.bodyText, styles.lastParagraph, { color: theme.text }]}>
              Here, Mirror helps you trace those moments, and begin to see the patterns they may have created.
            </Text>
            
            {/* Micro line */}
            <Text style={[styles.microLine, { color: theme.textTertiary }]}>
              Start anywhere. It doesn't have to be perfect.
            </Text>
            
            {/* CTA Button */}
            <TouchableOpacity
              style={[styles.ctaButton, { backgroundColor: theme.accent }]}
              onPress={onAddMoment}
              activeOpacity={0.8}
            >
              <Ionicons name="add-circle-outline" size={18} color="#FFFFFF" />
              <Text style={styles.ctaText}>{ctaText}</Text>
            </TouchableOpacity>
            
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
        )}
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
    marginBottom: 16,
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    padding: 16,
  },
  headerContent: {
    flex: 1,
    marginRight: 12,
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  teaserText: {
    fontSize: 14,
    lineHeight: 20,
    marginTop: 4,
  },
  expandControl: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  expandText: {
    fontSize: 12,
  },
  expandedContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 23,
    marginBottom: 10,
  },
  lastParagraph: {
    marginBottom: 14,
  },
  microLine: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 16,
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
    fontWeight: '600',
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
    marginTop: 12,
    paddingTop: 12,
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
    fontWeight: '600',
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
    fontWeight: '600',
  },
  exampleCategory: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  exampleCategoryText: {
    fontSize: 11,
    fontWeight: '600',
  },
  exampleTitle: {
    fontSize: 16,
    fontWeight: '600',
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
    fontWeight: '600',
    color: '#FFFFFF',
  },
});
