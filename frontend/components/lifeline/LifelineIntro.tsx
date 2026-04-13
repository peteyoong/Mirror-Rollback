/**
 * LifelineIntro Component
 * 
 * Emotional hook screen that explains why entering life events matters.
 * Includes a Pattern Teaser card to create curiosity before users begin.
 * Connects Mirror's lenses (astrology, Human Design, BaZi) with lived experience.
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';

interface LifelineIntroProps {
  onComplete: () => void;
  onImport?: () => void;
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function LifelineIntro({ onComplete, onImport }: LifelineIntroProps) {
  const { theme } = useTheme();
  const router = useRouter();
  
  // Staggered fade-in animations
  const line1Opacity = useRef(new Animated.Value(0)).current;
  const line2Opacity = useRef(new Animated.Value(0)).current;
  const line3Opacity = useRef(new Animated.Value(0)).current;
  const teaserOpacity = useRef(new Animated.Value(0)).current;
  const actionsOpacity = useRef(new Animated.Value(0)).current;
  
  useEffect(() => {
    // Staggered animation sequence for reflective feel
    Animated.stagger(350, [
      Animated.timing(line1Opacity, {
        toValue: 1,
        duration: 500,
        useNativeDriver: false,
      }),
      Animated.timing(line2Opacity, {
        toValue: 1,
        duration: 500,
        useNativeDriver: false,
      }),
      Animated.timing(line3Opacity, {
        toValue: 1,
        duration: 500,
        useNativeDriver: false,
      }),
      Animated.timing(teaserOpacity, {
        toValue: 1,
        duration: 600,
        useNativeDriver: false,
      }),
      Animated.timing(actionsOpacity, {
        toValue: 1,
        duration: 400,
        useNativeDriver: false,
      }),
    ]).start();
  }, []);
  
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Main Emotional Hook - Three Lines */}
        <View style={styles.hookContainer}>
          <Animated.Text 
            style={[
              styles.hookLine, 
              { color: theme.text, opacity: line1Opacity }
            ]}
          >
            Your chart shows potential.
          </Animated.Text>
          
          <Animated.Text 
            style={[
              styles.hookLine, 
              { color: theme.text, opacity: line2Opacity }
            ]}
          >
            Your life reveals the pattern.
          </Animated.Text>
          
          <Animated.Text 
            style={[
              styles.hookLine, 
              { color: theme.text, opacity: line3Opacity }
            ]}
          >
            Your decisions show the path you chose.
          </Animated.Text>
        </View>
        
        {/* Pattern Teaser Card */}
        <Animated.View 
          style={[
            styles.teaserCard, 
            { 
              backgroundColor: `${theme.accent}08`,
              borderColor: `${theme.accent}30`,
              opacity: teaserOpacity,
            }
          ]}
        >
          <Text style={[styles.teaserTitle, { color: theme.text }]}>
            A pattern may already exist in your life
          </Text>
          
          <Text style={[styles.teaserBody, { color: theme.textSecondary }]}>
            Many lives move through cycles such as:
          </Text>
          
          {/* Pattern Arc Visual */}
          <View style={styles.patternArc}>
            <View style={[styles.arcNode, { backgroundColor: `${theme.accent}15`, borderColor: theme.accent }]}>
              <Text style={[styles.arcNodeText, { color: theme.accent }]}>Momentum</Text>
            </View>
            <View style={[styles.arcConnector, { backgroundColor: `${theme.accent}40` }]} />
            <View style={[styles.arcNode, { backgroundColor: `${theme.accent}15`, borderColor: theme.accent }]}>
              <Text style={[styles.arcNodeText, { color: theme.accent }]}>Pressure</Text>
            </View>
            <View style={[styles.arcConnector, { backgroundColor: `${theme.accent}40` }]} />
            <View style={[styles.arcNode, { backgroundColor: `${theme.accent}15`, borderColor: theme.accent }]}>
              <Text style={[styles.arcNodeText, { color: theme.accent }]}>Reinvention</Text>
            </View>
          </View>
          
          <View style={styles.teaserDescriptions}>
            <Text style={[styles.teaserDescription, { color: theme.textSecondary }]}>
              Starting something.
            </Text>
            <Text style={[styles.teaserDescription, { color: theme.textSecondary }]}>
              Facing resistance.
            </Text>
            <Text style={[styles.teaserDescription, { color: theme.textSecondary }]}>
              Changing direction.
            </Text>
          </View>
          
          <Text style={[styles.teaserCta, { color: theme.textSecondary }]}>
            Your timeline may already contain a pattern like this.{'\n'}
            Add five turning points to begin revealing it.
          </Text>
        </Animated.View>
      </ScrollView>
      
      {/* Actions */}
      <Animated.View style={[styles.actionsContainer, { opacity: actionsOpacity }]}>
        <TouchableOpacity
          style={[styles.primaryButton, { backgroundColor: theme.accent }]}
          onPress={onComplete}
          activeOpacity={0.8}
        >
          <Text style={styles.primaryButtonText}>Start My Lifeline</Text>
        </TouchableOpacity>
        
        {onImport && (
          <TouchableOpacity
            style={[styles.secondaryButton, { borderColor: theme.border }]}
            onPress={() => router.push('/lifeline-upload')}
            activeOpacity={0.7}
          >
            <Text style={[styles.secondaryButtonText, { color: theme.text }]}>
              Import a Lifeline
            </Text>
          </TouchableOpacity>
        )}
        
        <Text style={[styles.importHint, { color: theme.textTertiary }]}>
          PowerPoint, spreadsheet, PDF, or image
        </Text>
      </Animated.View>
    </SafeAreaView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 28,
    paddingTop: 40,
    paddingBottom: 20,
  },
  
  // Emotional Hook - Three Main Lines
  hookContainer: {
    marginBottom: 32,
  },
  hookLine: {
    fontSize: 24,
    fontWeight: '500',
    lineHeight: 30,
    textAlign: 'center',
    marginBottom: 16,
    letterSpacing: -0.3,
  },
  
  // Pattern Teaser Card
  teaserCard: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 24,
    marginBottom: 16,
  },
  teaserTitle: {
    fontSize: 17,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 16,
  },
  teaserBody: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
  },
  
  // Pattern Arc Visual
  patternArc: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    paddingHorizontal: 4,
  },
  arcNode: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 16,
    borderWidth: 1,
  },
  arcNodeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  arcConnector: {
    width: 16,
    height: 2,
    marginHorizontal: 2,
  },
  
  // Teaser descriptions
  teaserDescriptions: {
    marginBottom: 16,
  },
  teaserDescription: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
  },
  teaserCta: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
    fontStyle: 'italic',
  },
  
  // Actions
  actionsContainer: {
    paddingHorizontal: 28,
    paddingBottom: 32,
    gap: 12,
  },
  primaryButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 17,
    fontWeight: '600',
  },
  secondaryButton: {
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  importHint: {
    fontSize: 12,
    textAlign: 'center',
    marginTop: 4,
  },
});
