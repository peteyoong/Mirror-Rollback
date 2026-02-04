import React, { useEffect, useState } from 'react';
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
import { getEnneagramResult } from '../../services/api';

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
}

// Enneagram Lens Intro Screen
// Shows summary if user has result, otherwise shows intro with assessment CTA
export default function EnneagramIntro() {
  const router = useRouter();
  const { user } = useAppStore();
  const [result, setResult] = useState<EnneagramResult | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchResult = async () => {
      if (!user?.id) {
        setLoading(false);
        return;
      }
      
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
  
  const handleStartAssessment = () => {
    router.push('/enneagram/assessment');
  };
  
  const handleViewResults = () => {
    router.push('/enneagram/results');
  };
  
  const handleBack = () => {
    router.back();
  };
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="dark" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.text} />
        </View>
      </SafeAreaView>
    );
  }
  
  // User has a result - show summary card + view results
  if (result) {
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
          <TouchableOpacity onPress={handleBack} style={styles.closeButton}>
            <Ionicons name="close" size={24} color={Colors.text} />
          </TouchableOpacity>
          <View style={styles.headerCenter}>
            <Ionicons name="git-branch-outline" size={20} color={Colors.text} />
            <Text style={styles.headerTitle}>Enneagram</Text>
          </View>
          <View style={styles.headerSpacer} />
        </View>
        
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Result Summary Card */}
          <View style={styles.resultSummaryCard}>
            <View style={styles.resultBadge}>
              <Text style={styles.resultBadgeText}>{result.inferred_core}</Text>
            </View>
            <Text style={styles.resultTitle}>
              Type {result.inferred_core} with {wingDisplay}
            </Text>
            <Text style={styles.resultSubtitle}>
              {TYPE_NAMES[result.inferred_core]}
            </Text>
            <View style={[
              styles.confidencePill,
              result.confidence_tier === 'high' && styles.confidenceHigh,
              result.confidence_tier === 'medium' && styles.confidenceMedium,
              result.confidence_tier === 'low' && styles.confidenceLow,
            ]}>
              <Text style={styles.confidencePillText}>
                Confidence: {confidenceLabel}
              </Text>
            </View>
            
            <TouchableOpacity style={styles.viewResultsButton} onPress={handleViewResults}>
              <Text style={styles.viewResultsText}>View Full Results</Text>
              <Ionicons name="arrow-forward" size={16} color={Colors.text} />
            </TouchableOpacity>
          </View>
          
          {/* Placeholder for lens content */}
          <View style={styles.lensPlaceholder}>
            <Ionicons name="construct-outline" size={32} color={Colors.textTertiary} />
            <Text style={styles.lensPlaceholderTitle}>Lens Content Coming Soon</Text>
            <Text style={styles.lensPlaceholderText}>
              Daily insights and deep dives for your Enneagram type will be available here.
            </Text>
          </View>
          
          {/* Retake Option */}
          <TouchableOpacity 
            style={styles.retakeButton}
            onPress={handleStartAssessment}
          >
            <Ionicons name="refresh-outline" size={18} color={Colors.textSecondary} />
            <Text style={styles.retakeText}>Retake Assessment</Text>
          </TouchableOpacity>
          
          <View style={styles.bottomSpacer} />
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // User has no result - show intro screen
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.closeButton}>
          <Ionicons name="close" size={24} color={Colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Ionicons name="git-branch-outline" size={20} color={Colors.text} />
          <Text style={styles.headerTitle}>Enneagram</Text>
        </View>
        <View style={styles.headerSpacer} />
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Hero Section */}
        <View style={styles.heroSection}>
          <View style={styles.iconContainer}>
            <Ionicons name="git-branch-outline" size={40} color={Colors.text} />
          </View>
          <Text style={styles.title}>Enneagram</Text>
          <Text style={styles.subtitle}>
            A framework for understanding core motivations,
            fears, and growth patterns.
          </Text>
        </View>
        
        {/* Info Cards */}
        <View style={styles.infoSection}>
          <View style={styles.infoCard}>
            <View style={styles.infoRow}>
              <Ionicons name="checkmark-circle-outline" size={18} color={Colors.textSecondary} />
              <Text style={styles.infoLabel}>Helps with</Text>
            </View>
            <Text style={styles.infoText}>
              Understanding why you do what you do, identifying blind spots, 
              and recognizing patterns in relationships and stress.
            </Text>
          </View>
          
          <View style={styles.infoCard}>
            <View style={styles.infoRow}>
              <Ionicons name="close-circle-outline" size={18} color={Colors.textTertiary} />
              <Text style={styles.infoLabel}>Does not</Text>
            </View>
            <Text style={styles.infoText}>
              Put you in a box, predict behavior, or replace self-observation. 
              It&apos;s a lens for reflection — not a label.
            </Text>
          </View>
        </View>
        
        {/* Assessment Info */}
        <View style={styles.assessmentSection}>
          <Text style={styles.assessmentTitle}>How it works</Text>
          <Text style={styles.assessmentDescription}>
            The Enneagram assessment takes 10–12 minutes and consists of three sections:
          </Text>
          
          <View style={styles.sectionsList}>
            <View style={styles.sectionItem}>
              <View style={styles.sectionNumber}>
                <Text style={styles.sectionNumberText}>1</Text>
              </View>
              <View style={styles.sectionContent}>
                <Text style={styles.sectionItemTitle}>Core Motivation</Text>
                <Text style={styles.sectionItemDesc}>Identify your fundamental patterns</Text>
              </View>
            </View>
            
            <View style={styles.sectionItem}>
              <View style={styles.sectionNumber}>
                <Text style={styles.sectionNumberText}>2</Text>
              </View>
              <View style={styles.sectionContent}>
                <Text style={styles.sectionItemTitle}>Disambiguation</Text>
                <Text style={styles.sectionItemDesc}>Clarify between similar patterns</Text>
              </View>
            </View>
            
            <View style={styles.sectionItem}>
              <View style={styles.sectionNumber}>
                <Text style={styles.sectionNumberText}>3</Text>
              </View>
              <View style={styles.sectionContent}>
                <Text style={styles.sectionItemTitle}>Wing Resolution</Text>
                <Text style={styles.sectionItemDesc}>Refine how your type expresses itself</Text>
              </View>
            </View>
          </View>
        </View>
        
        {/* Note */}
        <View style={styles.noteSection}>
          <Text style={styles.noteText}>
            Answer based on what feels most fundamental to you — not how you&apos;ve been lately. 
            There are no right or wrong answers.
          </Text>
        </View>
        
        {/* CTA Button */}
        <TouchableOpacity 
          style={styles.ctaButton}
          onPress={handleStartAssessment}
        >
          <Text style={styles.ctaButtonText}>Start Enneagram Assessment</Text>
          <Ionicons name="arrow-forward" size={18} color={Colors.background} />
        </TouchableOpacity>
        
        {/* Spacer for safe area */}
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
  headerCenter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  headerSpacer: {
    width: 32,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 40,
  },
  
  // Result Summary (when user has result)
  resultSummaryCard: {
    backgroundColor: Colors.surface,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    marginBottom: 20,
  },
  resultBadge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.text,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  resultBadgeText: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.background,
  },
  resultTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
  },
  resultSubtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    marginBottom: 12,
  },
  confidencePill: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: Colors.border,
    marginBottom: 16,
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
  confidencePillText: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.text,
  },
  viewResultsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
  },
  viewResultsText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },
  
  // Lens Placeholder
  lensPlaceholder: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    marginBottom: 20,
  },
  lensPlaceholderTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    marginTop: 12,
    marginBottom: 8,
  },
  lensPlaceholderText: {
    fontSize: 14,
    lineHeight: 20,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  
  // Retake
  retakeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
  },
  retakeText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  
  // Hero
  heroSection: {
    alignItems: 'center',
    marginBottom: 32,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  title: {
    fontSize: 28,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: 16,
  },
  
  // Info Cards
  infoSection: {
    gap: 12,
    marginBottom: 32,
  },
  infoCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  infoLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  infoText: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textTertiary,
    marginLeft: 26,
  },
  
  // Assessment Section
  assessmentSection: {
    marginBottom: 24,
  },
  assessmentTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  assessmentDescription: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 20,
  },
  sectionsList: {
    gap: 12,
  },
  sectionItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 16,
  },
  sectionNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.surface,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sectionNumberText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.text,
  },
  sectionContent: {
    flex: 1,
  },
  sectionItemTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 2,
  },
  sectionItemDesc: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  
  // Note
  noteSection: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  noteText: {
    fontSize: 14,
    lineHeight: 21,
    color: Colors.textSecondary,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  
  // CTA
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  ctaButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.background,
  },
  
  bottomSpacer: {
    height: 20,
  },
});
