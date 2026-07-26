import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';

// Enneagram type definitions
const ENNEAGRAM_TYPES = [
  { number: 1, name: 'Reformer', brief: 'Principled, purposeful, self-controlled' },
  { number: 2, name: 'Helper', brief: 'Generous, demonstrative, people-pleasing' },
  { number: 3, name: 'Achiever', brief: 'Adaptable, driven, image-conscious' },
  { number: 4, name: 'Individualist', brief: 'Expressive, dramatic, self-absorbed' },
  { number: 5, name: 'Investigator', brief: 'Perceptive, innovative, secretive' },
  { number: 6, name: 'Loyalist', brief: 'Engaging, responsible, anxious' },
  { number: 7, name: 'Enthusiast', brief: 'Spontaneous, versatile, scattered' },
  { number: 8, name: 'Challenger', brief: 'Self-confident, decisive, confrontational' },
  { number: 9, name: 'Peacemaker', brief: 'Receptive, reassuring, complacent' },
];

// Get adjacent wings for a type
const getWingOptions = (type: number): number[] => {
  if (type === 1) return [9, 2];
  if (type === 9) return [8, 1];
  return [type - 1, type + 1];
};

type Step = 'type' | 'wing';

export default function SelfDeclareEnneagramScreen() {
  const router = useRouter();
  const { user } = useAppStore();
  const [step, setStep] = useState<Step>('type');
  const [selectedType, setSelectedType] = useState<number | null>(null);
  const [selectedWing, setSelectedWing] = useState<number | 'none' | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleBack = () => {
    if (step === 'wing') {
      setStep('type');
      setSelectedWing(null);
    } else {
      router.back();
    }
  };

  const handleTypeSelect = (type: number) => {
    setSelectedType(type);
    setStep('wing');
  };

  const handleWingSelect = async (wing: number | 'none') => {
    setSelectedWing(wing);
    
    if (!user?.id || !selectedType) return;
    
    setIsSaving(true);
    setError(null);
    
    try {
      // Save self-declared result
      await api.post('/enneagram/self-declare', {
        user_id: user.id,
        enneagram_type: selectedType,
        enneagram_wing: wing === 'none' ? null : wing,
        source: 'self_declared'
      });
      
      // Navigate to the Enneagram lens view
      router.replace('/enneagram');
    } catch (err: any) {
      console.error('Error saving self-declared type:', err);
      setError('Failed to save your type. Please try again.');
      setIsSaving(false);
    }
  };

  const wingOptions = selectedType ? getWingOptions(selectedType) : [];

  // Type selection step
  if (step === 'type') {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Select Your Type</Text>
          <View style={styles.headerSpacer} />
        </View>
        
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <Text style={styles.stepTitle}>What's your core Enneagram type?</Text>
          <Text style={styles.stepSubtitle}>
            Select the type that most resonates with your fundamental patterns.
          </Text>
          
          <View style={styles.typeGrid}>
            {ENNEAGRAM_TYPES.map((type) => (
              <TouchableOpacity
                key={type.number}
                style={[
                  styles.typeCard,
                  selectedType === type.number && styles.typeCardSelected
                ]}
                onPress={() => handleTypeSelect(type.number)}
              >
                <View style={styles.typeNumber}>
                  <Text style={styles.typeNumberText}>{type.number}</Text>
                </View>
                <View style={styles.typeInfo}>
                  <Text style={styles.typeName}>{type.name}</Text>
                  <Text style={styles.typeBrief}>{type.brief}</Text>
                </View>
                <Ionicons 
                  name="chevron-forward" 
                  size={18} 
                  color={Colors.textTertiary} 
                />
              </TouchableOpacity>
            ))}
          </View>
          
          <View style={styles.noteCard}>
            <Ionicons name="information-circle-outline" size={18} color={Colors.textTertiary} />
            <Text style={styles.noteText}>
              Not sure of your type? You can always take the assessment instead.
            </Text>
          </View>
          
          <TouchableOpacity
            style={styles.assessmentLink}
            onPress={() => router.push('/enneagram/assessment')}
          >
            <Text style={styles.assessmentLinkText}>Take the assessment instead</Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Wing selection step
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Select Your Wing</Text>
        <View style={styles.headerSpacer} />
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.selectedTypeDisplay}>
          <Text style={styles.selectedTypeLabel}>Your type</Text>
          <Text style={styles.selectedTypeValue}>
            Type {selectedType} · {ENNEAGRAM_TYPES.find(t => t.number === selectedType)?.name}
          </Text>
        </View>
        
        <Text style={styles.stepTitle}>Do you have a dominant wing?</Text>
        <Text style={styles.stepSubtitle}>
          Wings are the adjacent types that color your expression. 
          Most people lean toward one wing, but some are balanced.
        </Text>
        
        {error && (
          <View style={styles.errorCard}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}
        
        <View style={styles.wingOptions}>
          {wingOptions.map((wingNum) => {
            const wingType = ENNEAGRAM_TYPES.find(t => t.number === wingNum);
            return (
              <TouchableOpacity
                key={wingNum}
                style={[
                  styles.wingCard,
                  selectedWing === wingNum && styles.wingCardSelected
                ]}
                onPress={() => handleWingSelect(wingNum)}
                disabled={isSaving}
              >
                <View style={styles.wingHeader}>
                  <Text style={styles.wingNumber}>Wing {wingNum}</Text>
                  <Text style={styles.wingName}>{wingType?.name}</Text>
                </View>
                <Text style={styles.wingDesc}>
                  {selectedType}w{wingNum} — {wingType?.brief}
                </Text>
              </TouchableOpacity>
            );
          })}
          
          <TouchableOpacity
            style={[
              styles.wingCard,
              styles.wingCardNone,
              selectedWing === 'none' && styles.wingCardSelected
            ]}
            onPress={() => handleWingSelect('none')}
            disabled={isSaving}
          >
            <View style={styles.wingHeader}>
              <Text style={styles.wingNumber}>Balanced / Unknown</Text>
            </View>
            <Text style={styles.wingDesc}>
              I don't have a clear dominant wing, or I'm not sure yet.
            </Text>
          </TouchableOpacity>
        </View>
        
        {isSaving && (
          <View style={styles.savingOverlay}>
            <ActivityIndicator size="small" color={Colors.text} />
            <Text style={styles.savingText}>Saving your type...</Text>
          </View>
        )}
        
        <View style={styles.bottomSpacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  backButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '500',
    color: Colors.text,
  },
  headerSpacer: {
    width: 32,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 40,
  },
  
  // Step content
  stepTitle: {
    fontSize: 22,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 14,
  },
  stepSubtitle: {
    fontSize: 17,
    lineHeight: 30,
    color: Colors.textSecondary,
    marginBottom: 24,
  },
  
  // Type selection
  typeGrid: {
    gap: 10,
    marginBottom: 24,
  },
  typeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  typeCardSelected: {
    borderColor: Colors.text,
    borderWidth: 1,
  },
  typeNumber: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.background,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  typeNumberText: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.text,
  },
  typeInfo: {
    flex: 1,
  },
  typeName: {
    fontSize: 17,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 2,
  },
  typeBrief: {
    fontSize: 14,
    color: Colors.textTertiary,
  },
  
  // Note
  noteCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 8,
    padding: 14,
    marginBottom: 16,
  },
  noteText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 32,
    color: Colors.textTertiary,
  },
  
  // Assessment link
  assessmentLink: {
    alignSelf: 'center',
    padding: 12,
  },
  assessmentLinkText: {
    fontSize: 16,
    color: Colors.textTertiary,
    textDecorationLine: 'underline',
  },
  
  // Selected type display
  selectedTypeDisplay: {
    alignItems: 'center',
    marginBottom: 24,
    paddingVertical: 16,
    backgroundColor: Colors.surface,
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  selectedTypeLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textTertiary,
    letterSpacing: 0.5,
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  selectedTypeValue: {
    fontSize: 22,
    fontWeight: '500',
    color: Colors.text,
  },
  
  // Wing options
  wingOptions: {
    gap: 12,
  },
  wingCard: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  wingCardSelected: {
    borderColor: Colors.text,
    borderWidth: 1,
  },
  wingCardNone: {
    borderStyle: 'dashed',
  },
  wingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  wingNumber: {
    fontSize: 17,
    fontWeight: '500',
    color: Colors.text,
  },
  wingName: {
    fontSize: 17,
    color: Colors.textSecondary,
  },
  wingDesc: {
    fontSize: 16,
    lineHeight: 32,
    color: Colors.textTertiary,
  },
  
  // Error
  errorCard: {
    backgroundColor: 'rgba(255,100,100,0.1)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 16,
    color: '#ff6b6b',
    textAlign: 'center',
  },
  
  // Saving
  savingOverlay: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 24,
  },
  savingText: {
    fontSize: 16,
    color: Colors.textSecondary,
  },
  
  bottomSpacer: {
    height: 40,
  },
});
