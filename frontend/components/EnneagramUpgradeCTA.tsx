import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Colors } from '../constants/colors';
import { EnneagramCTACopy } from '../utils/enneagramGateLogic';
import { 
  emitEnneagramGateCTAClicked, 
  EnneagramGateCTAVariant, 
  EnneagramGateSurface 
} from '../utils/analytics';

interface Props {
  ctaCopy: EnneagramCTACopy;
  // Analytics props
  surface: EnneagramGateSurface;
  ctaVariant: EnneagramGateCTAVariant;
  assessmentDepth: string | null;
  confidenceTier: string | null;
  resultAgeDays: number | null;
  hasSavedSession?: boolean;
  // Custom handler
  onPress?: () => void;
  testID?: string;
}

/**
 * Enneagram Upgrade CTA Component
 * ================================
 * A reusable CTA banner for suggesting assessment upgrades.
 * 
 * Features:
 * - Primary variant: More prominent styling
 * - Secondary variant: Subtle styling
 * - Never blocks content (always dismissable)
 * - Mirror-safe copy (no coaching language)
 * - Analytics: emits enneagram_gate_cta_clicked on press
 */
export default function EnneagramUpgradeCTA({ 
  ctaCopy, 
  surface,
  ctaVariant,
  assessmentDepth,
  confidenceTier,
  resultAgeDays,
  hasSavedSession = false,
  onPress, 
  testID 
}: Props) {
  const router = useRouter();
  
  const handlePress = () => {
    // Emit analytics event
    emitEnneagramGateCTAClicked({
      variant: ctaVariant,
      surface,
      assessment_depth: assessmentDepth,
      confidence_tier: confidenceTier,
      result_age_days: resultAgeDays,
      action: 'start_assessment',
      has_saved_session: hasSavedSession,
    });
    
    if (onPress) {
      onPress();
    } else {
      // Default action: navigate to assessment
      router.push('/enneagram/assessment');
    }
  };
  
  const isPrimary = ctaCopy.variant === 'primary';
  
  return (
    <View 
      style={[
        styles.container,
        isPrimary ? styles.containerPrimary : styles.containerSecondary
      ]}
      testID={testID}
    >
      <Text style={[
        styles.title,
        isPrimary ? styles.titlePrimary : styles.titleSecondary
      ]}>
        {ctaCopy.title}
      </Text>
      
      <Text style={[
        styles.body,
        isPrimary ? styles.bodyPrimary : styles.bodySecondary
      ]}>
        {ctaCopy.body}
      </Text>
      
      <TouchableOpacity
        style={[
          styles.button,
          isPrimary ? styles.buttonPrimary : styles.buttonSecondary
        ]}
        onPress={handlePress}
        activeOpacity={0.8}
      >
        <Text style={[
          styles.buttonText,
          isPrimary ? styles.buttonTextPrimary : styles.buttonTextSecondary
        ]}>
          {ctaCopy.button_text}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  containerPrimary: {
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.text,
  },
  containerSecondary: {
    backgroundColor: Colors.surfaceLight,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  
  title: {
    fontWeight: '600',
    marginBottom: 8,
  },
  titlePrimary: {
    fontSize: 17,
    color: Colors.text,
  },
  titleSecondary: {
    fontSize: 15,
    color: Colors.textSecondary,
  },
  
  body: {
    lineHeight: 20,
    marginBottom: 12,
  },
  bodyPrimary: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  bodySecondary: {
    fontSize: 13,
    color: Colors.textTertiary,
  },
  
  button: {
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignSelf: 'flex-start',
  },
  buttonPrimary: {
    backgroundColor: Colors.text,
  },
  buttonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: Colors.textSecondary,
  },
  
  buttonText: {
    fontWeight: '500',
  },
  buttonTextPrimary: {
    fontSize: 14,
    color: Colors.background,
  },
  buttonTextSecondary: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
});
