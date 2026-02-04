import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { Ionicons } from '@expo/vector-icons';
import { getEnneagramResult } from '../../services/api';
import * as Clipboard from 'expo-clipboard';

// Check if we're in development mode
const IS_DEV = process.env.NODE_ENV !== 'production' || __DEV__;

// Type motivation labels
const TYPE_MOTIVATIONS: { [key: number]: string } = {
  1: 'integrity and high standards',
  2: 'being needed and connection through helping',
  3: 'value through success and achievement',
  4: 'identity, meaning, and emotional depth',
  5: 'competence, resources, and understanding',
  6: 'security, trust, and reliability',
  7: 'freedom, possibility, and stimulation',
  8: 'autonomy, control, and strength',
  9: 'peace, harmony, and inner stability',
};

// Type names
const TYPE_NAMES: { [key: number]: string } = {
  1: 'The Perfectionist',
  2: 'The Helper',
  3: 'The Achiever',
  4: 'The Individualist',
  5: 'The Investigator',
  6: 'The Loyalist',
  7: 'The Enthusiast',
  8: 'The Challenger',
  9: 'The Peacemaker',
};

interface EnneagramResult {
  inferred_core: number;
  inferred_wing: number | 'balanced';
  confidence: number;
  confidence_tier: string;
  is_close: boolean;
  top_candidates: { type: number; probability: number }[];
  state_calibration?: {
    energy_state: string;
    life_context: string;
    answer_frame: string;
  };
  created_at?: string;
}

export default function EnneagramResults() {
  const router = useRouter();
  const { user } = useAppStore();
  const [result, setResult] = useState<EnneagramResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [showRetakeModal, setShowRetakeModal] = useState(false);
  
  useEffect(() => {
    const fetchResult = async () => {
      if (!user?.id) return;
      
      try {
        const response = await getEnneagramResult(user.id);
        if (response.has_result && response.result) {
          setResult(response.result);
        }
      } catch (error) {
        console.error('Error fetching Enneagram result:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchResult();
  }, [user?.id]);
  
  // Redirect if no user
  if (!user) {
    router.replace('/onboarding');
    return null;
  }
  
  const handleViewLens = () => {
    router.replace('/enneagram');
  };
  
  const handleRetakeConfirm = () => {
    setShowRetakeModal(false);
    router.replace('/enneagram/assessment');
  };
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.text} />
          <Text style={styles.loadingText}>Loading your results...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  if (!result) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.loadingContainer}>
          <Ionicons name="alert-circle-outline" size={48} color={Colors.textTertiary} />
          <Text style={styles.errorTitle}>No Results Found</Text>
          <Text style={styles.errorText}>
            It looks like you haven&apos;t completed the assessment yet.
          </Text>
          <TouchableOpacity
            style={styles.primaryButton}
            onPress={() => router.replace('/enneagram/assessment')}
          >
            <Text style={styles.primaryButtonText}>Take Assessment</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  const wingDisplay = result.inferred_wing === 'balanced' 
    ? 'Balanced Wings' 
    : `Wing ${result.inferred_wing}`;
  
  const confidenceLabel = result.confidence_tier === 'high' 
    ? 'High' 
    : result.confidence_tier === 'medium' 
      ? 'Medium' 
      : 'Low';
  
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.closeButton}>
          <Ionicons name="close" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Your Results</Text>
        <View style={styles.headerSpacer} />
      </View>
      
      <ScrollView contentContainerStyle={styles.content}>
        {/* Main Result Card */}
        <View style={styles.resultCard}>
          <Text style={styles.pageTitle}>Your Enneagram Profile</Text>
          
          {/* Type Badge */}
          <View style={styles.typeBadge}>
            <Text style={styles.typeNumber}>{result.inferred_core}</Text>
          </View>
          
          {/* Type Title */}
          <Text style={styles.typeTitle}>
            Type {result.inferred_core} with {wingDisplay}
          </Text>
          <Text style={styles.typeName}>
            {TYPE_NAMES[result.inferred_core]}
          </Text>
          
          {/* Confidence */}
          <View style={styles.confidenceRow}>
            <View style={[
              styles.confidenceBadge,
              result.confidence_tier === 'high' && styles.confidenceHigh,
              result.confidence_tier === 'medium' && styles.confidenceMedium,
              result.confidence_tier === 'low' && styles.confidenceLow,
            ]}>
              <Text style={styles.confidenceText}>
                Confidence: {confidenceLabel}
              </Text>
            </View>
          </View>
        </View>
        
        {/* Why Paragraph */}
        <View style={styles.whyCard}>
          <Text style={styles.whyTitle}>Why this type?</Text>
          <Text style={styles.whyText}>
            Your responses suggest that {TYPE_MOTIVATIONS[result.inferred_core]} are central to how you navigate the world. This core pattern shapes your decisions, relationships, and growth edges.
          </Text>
        </View>
        
        {/* Top Candidates */}
        <View style={styles.candidatesCard}>
          <Text style={styles.candidatesTitle}>Top Patterns</Text>
          {result.top_candidates.map((candidate, index) => (
            <View key={candidate.type} style={styles.candidateRow}>
              <View style={styles.candidateInfo}>
                <Text style={styles.candidateRank}>{index + 1}</Text>
                <Text style={styles.candidateType}>
                  Type {candidate.type} — {TYPE_NAMES[candidate.type]}
                </Text>
              </View>
              <Text style={styles.candidateProbability}>
                {Math.round(candidate.probability * 100)}%
              </Text>
            </View>
          ))}
        </View>
        
        {/* Close Call Notice */}
        {result.is_close && result.top_candidates.length >= 2 && (
          <View style={styles.closeCallCard}>
            <Ionicons name="information-circle-outline" size={18} color={Colors.textSecondary} />
            <Text style={styles.closeCallText}>
              Close call between Type {result.top_candidates[0].type} and Type {result.top_candidates[1].type} — your result may depend on context and development level.
            </Text>
          </View>
        )}
        
        {/* Action Buttons */}
        <View style={styles.actionsContainer}>
          <TouchableOpacity style={styles.primaryButton} onPress={handleViewLens}>
            <Text style={styles.primaryButtonText}>View Enneagram Lens</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.secondaryButton} 
            onPress={() => setShowRetakeModal(true)}
          >
            <Text style={styles.secondaryButtonText}>Retake Assessment</Text>
          </TouchableOpacity>
        </View>
        
        <View style={styles.bottomSpacer} />
      </ScrollView>
      
      {/* Retake Confirmation Modal */}
      <Modal
        visible={showRetakeModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowRetakeModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Retake Assessment?</Text>
            <Text style={styles.modalText}>
              This will replace your current results. The assessment takes about 10-12 minutes.
            </Text>
            <View style={styles.modalActions}>
              <TouchableOpacity 
                style={styles.modalCancelButton}
                onPress={() => setShowRetakeModal(false)}
              >
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.modalConfirmButton}
                onPress={handleRetakeConfirm}
              >
                <Text style={styles.modalConfirmText}>Retake</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  headerSpacer: {
    width: 32,
  },
  content: {
    padding: 24,
  },
  
  // Loading & Error
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
    color: Colors.textSecondary,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  
  // Result Card
  resultCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  pageTitle: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.textTertiary,
    marginBottom: 20,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  typeBadge: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  typeNumber: {
    fontSize: 32,
    fontWeight: '700',
    color: Colors.background,
  },
  typeTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
    textAlign: 'center',
  },
  typeName: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginBottom: 16,
  },
  confidenceRow: {
    flexDirection: 'row',
  },
  confidenceBadge: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: Colors.border,
  },
  confidenceHigh: {
    backgroundColor: '#D4EDDA',
  },
  confidenceMedium: {
    backgroundColor: '#FFF3CD',
  },
  confidenceLow: {
    backgroundColor: '#F8D7DA',
  },
  confidenceText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.text,
  },
  
  // Why Card
  whyCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  whyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  whyText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
  },
  
  // Candidates Card
  candidatesCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 16,
  },
  candidatesTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 16,
  },
  candidateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  candidateInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  candidateRank: {
    width: 24,
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textTertiary,
  },
  candidateType: {
    fontSize: 14,
    color: Colors.text,
    flex: 1,
  },
  candidateProbability: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  
  // Close Call Card
  closeCallCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 10,
    padding: 14,
    marginBottom: 24,
  },
  closeCallText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 19,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  
  // Actions
  actionsContainer: {
    gap: 12,
  },
  primaryButton: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  secondaryButton: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  
  bottomSpacer: {
    height: 20,
  },
  
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  modalContent: {
    backgroundColor: Colors.background,
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 340,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  modalText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 24,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalCancelButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  modalCancelText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },
  modalConfirmButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    backgroundColor: Colors.text,
    borderRadius: 10,
  },
  modalConfirmText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.background,
  },
});
