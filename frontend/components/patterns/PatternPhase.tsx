/**
 * PatternPhase Component
 * 
 * Displays the current detected phase within a pattern arc.
 * Helps users understand where they may be in a recurring pattern cycle.
 * 
 * Design: Calm, observational, non-predictive
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

// =============================================================================
// TYPES
// =============================================================================

export interface PatternPhaseData {
  phase: string;
  display: string;
  description: string;
  confidence: number;
  sequence_labels: string[];
}

interface PatternPhaseProps {
  phase: PatternPhaseData;
}

// =============================================================================
// PHASE INDICATOR COMPONENT
// =============================================================================

interface PhaseIndicatorProps {
  phases: string[];
  currentPhase: string;
  theme: any;
}

function PhaseIndicator({ phases, currentPhase, theme }: PhaseIndicatorProps) {
  // Find current phase index
  const currentIndex = phases.findIndex(
    p => p.toLowerCase().includes(currentPhase.toLowerCase()) || 
        currentPhase.toLowerCase().includes(p.toLowerCase())
  );
  
  return (
    <View style={styles.phaseIndicator}>
      {phases.map((phase, index) => {
        const isActive = index === currentIndex;
        const isPast = index < currentIndex;
        
        return (
          <View key={index} style={styles.phaseStep}>
            <View 
              style={[
                styles.phaseDot,
                isActive && styles.phaseDotActive,
                isPast && styles.phaseDotPast,
                { borderColor: isActive ? '#10B981' : isPast ? theme.textSecondary : theme.border },
              ]} 
            >
              {isActive && <View style={styles.phaseDotInner} />}
            </View>
            <Text 
              style={[
                styles.phaseLabel,
                isActive && styles.phaseLabelActive,
                { color: isActive ? '#10B981' : theme.textSecondary },
              ]}
            >
              {phase}
            </Text>
            {index < phases.length - 1 && (
              <View 
                style={[
                  styles.phaseLine, 
                  { backgroundColor: isPast ? theme.textSecondary : theme.border }
                ]} 
              />
            )}
          </View>
        );
      })}
    </View>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function PatternPhase({ phase }: PatternPhaseProps) {
  const { theme } = useTheme();
  
  if (!phase || !phase.display) {
    return null;
  }
  
  return (
    <View style={styles.container}>
      {/* Phase Indicator */}
      {phase.sequence_labels && phase.sequence_labels.length > 0 && (
        <PhaseIndicator 
          phases={phase.sequence_labels}
          currentPhase={phase.phase}
          theme={theme}
        />
      )}
      
      {/* Current Phase */}
      <View style={[styles.phaseCard, { backgroundColor: 'rgba(16, 185, 129, 0.06)', borderColor: 'rgba(16, 185, 129, 0.2)' }]}>
        <Text style={[styles.phaseDisplay, { color: '#10B981' }]}>
          {phase.display}
        </Text>
        <Text style={[styles.phaseDescription, { color: theme.textSecondary }]}>
          {phase.description}
        </Text>
      </View>
      
      {/* Confidence indicator */}
      {phase.confidence && (
        <View style={styles.confidenceContainer}>
          <View style={[styles.confidenceBar, { backgroundColor: theme.border }]}>
            <View 
              style={[
                styles.confidenceFill, 
                { width: `${phase.confidence * 100}%`, backgroundColor: '#10B981' }
              ]} 
            />
          </View>
          <Text style={[styles.confidenceText, { color: theme.textTertiary }]}>
            Signal strength: {Math.round(phase.confidence * 100)}%
          </Text>
        </View>
      )}
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    gap: 16,
  },
  phaseIndicator: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
    marginBottom: 8,
  },
  phaseStep: {
    alignItems: 'center',
    flex: 1,
    position: 'relative',
  },
  phaseDot: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'transparent',
  },
  phaseDotActive: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
  },
  phaseDotPast: {
    backgroundColor: 'rgba(100, 100, 100, 0.15)',
  },
  phaseDotInner: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#10B981',
  },
  phaseLabel: {
    marginTop: 6,
    fontSize: 11,
    fontWeight: '600',
    textAlign: 'center',
  },
  phaseLabelActive: {
    fontWeight: '700',
  },
  phaseLine: {
    position: 'absolute',
    top: 9,
    left: '60%',
    right: '-40%',
    height: 2,
    zIndex: -1,
  },
  phaseCard: {
    padding: 16,
    borderRadius: 10,
    borderWidth: 1,
  },
  phaseDisplay: {
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 8,
  },
  phaseDescription: {
    fontSize: 14,
    lineHeight: 21,
  },
  confidenceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  confidenceBar: {
    flex: 1,
    height: 4,
    borderRadius: 2,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    borderRadius: 2,
  },
  confidenceText: {
    fontSize: 11,
    fontWeight: '500',
  },
});
