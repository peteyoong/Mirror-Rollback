/**
 * NumerologyPatternView.tsx
 * 
 * COMPLETE REWRITE for Task: Transform Numerology into Pattern System
 * 
 * Replaces descriptive personality text with diagnostic pattern recognition.
 * 
 * Sections:
 * 1. Energy Map (Lo Shu Grid)
 * 2. Core Pattern (sharp, confronting insight)
 * 3. How This Shows Up (real behavioral patterns)
 * 4. Internal Tension (X vs Y conflicts)
 * 5. Mirror Moment (precise reflection questions)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface NumerologyPatternData {
  life_path: number;
  expression: number | null;
  soul_urge: number | null;
  personality: number | null;
  birth_date: string;
  lo_shu_grid: number[][];
  present_numbers: { [key: string]: number };
  missing_numbers: number[];
  core_pattern: string;
  how_this_shows_up: string[];
  internal_tensions: { a: string; b: string; description: string }[];
  mirror_moment: string;
}

interface Props {
  userId: string;
  onOpenChat: () => void;
}

// =============================================================================
// COLORS
// =============================================================================

const COLORS = {
  accent: '#9B8AC4',
  accentLight: 'rgba(155, 138, 196, 0.15)',
  missing: '#EF4444',
  missingBg: 'rgba(239, 68, 68, 0.1)',
  present: '#10B981',
  presentBg: 'rgba(16, 185, 129, 0.1)',
  tension: '#F59E0B',
  tensionBg: 'rgba(245, 158, 11, 0.1)',
};

// =============================================================================
// LO SHU GRID COMPONENT
// =============================================================================

interface LoShuGridProps {
  grid: number[][];
  presentNumbers: { [key: string]: number };
  missingNumbers: number[];
  theme: any;
}

function LoShuGrid({ grid, presentNumbers, missingNumbers, theme }: LoShuGridProps) {
  // Lo Shu grid positions: 
  // [4, 9, 2]
  // [3, 5, 7]
  // [8, 1, 6]
  const gridOrder = [[4, 9, 2], [3, 5, 7], [8, 1, 6]];
  
  const getCellDisplay = (num: number) => {
    const count = presentNumbers[num.toString()] || 0;
    if (count === 0) {
      return { display: '—', isMissing: true, count: 0 };
    }
    return { 
      display: count > 1 ? `${num}`.repeat(count).split('').join(' ') : num.toString(),
      isMissing: false,
      count 
    };
  };

  return (
    <View style={styles.loShuContainer}>
      <Text style={[styles.sectionTitle, { color: theme.text }]}>ENERGY MAP</Text>
      <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>
        Lo Shu Grid from your birth date
      </Text>
      
      {/* Grid */}
      <View style={[styles.gridContainer, { borderColor: theme.border }]}>
        {gridOrder.map((row, rowIdx) => (
          <View key={rowIdx} style={styles.gridRow}>
            {row.map((num, colIdx) => {
              const cell = getCellDisplay(num);
              return (
                <View
                  key={`${rowIdx}-${colIdx}`}
                  style={[
                    styles.gridCell,
                    { borderColor: theme.border },
                    cell.isMissing && { backgroundColor: COLORS.missingBg },
                  ]}
                >
                  <Text style={[
                    styles.gridCellText,
                    { color: cell.isMissing ? COLORS.missing : theme.text },
                    cell.count > 1 && styles.gridCellMultiple
                  ]}>
                    {cell.display}
                  </Text>
                  <Text style={[styles.gridCellLabel, { color: theme.textTertiary }]}>
                    {num}
                  </Text>
                </View>
              );
            })}
          </View>
        ))}
      </View>

      {/* Legend */}
      <View style={styles.gridLegend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: COLORS.present }]} />
          <Text style={[styles.legendText, { color: theme.textSecondary }]}>
            Present: {Object.entries(presentNumbers).filter(([_, c]) => c > 0).map(([n, c]) => c > 1 ? `${n}×${c}` : n).join(', ') || 'None'}
          </Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: COLORS.missing }]} />
          <Text style={[styles.legendText, { color: theme.textSecondary }]}>
            Missing: {missingNumbers.length > 0 ? missingNumbers.join(', ') : 'None'}
          </Text>
        </View>
      </View>
    </View>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function NumerologyPatternView({ userId, onOpenChat }: Props) {
  const { theme } = useTheme();
  
  const [data, setData] = useState<NumerologyPatternData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Name modal state
  const [showNameModal, setShowNameModal] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [isSavingName, setIsSavingName] = useState(false);
  const [existingName, setExistingName] = useState<string | null>(null);

  useEffect(() => {
    loadPatternData();
    loadProfile();
  }, [userId]);

  const loadProfile = async () => {
    try {
      const response = await api.get(`/profile/${userId}`);
      if (response.data?.numerology_full_name) {
        setExistingName(response.data.numerology_full_name);
        setNameInput(response.data.numerology_full_name);
      }
    } catch (err) {
      console.log('[NumerologyPattern] Profile load error:', err);
    }
  };

  const loadPatternData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/numerology/pattern/${userId}`);
      setData(response.data);
    } catch (err: any) {
      console.error('[NumerologyPattern] Load error:', err);
      setError('Unable to load pattern data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveName = async () => {
    if (!nameInput.trim()) return;
    
    setIsSavingName(true);
    try {
      await api.post(`/numerology/unlock-name/${userId}`, {
        full_birth_name: nameInput.trim()
      });
      setExistingName(nameInput.trim());
      setShowNameModal(false);
      loadPatternData(); // Reload with new data
    } catch (err) {
      console.error('[NumerologyPattern] Save name error:', err);
    } finally {
      setIsSavingName(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Building your pattern system...
          </Text>
        </View>
      </View>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <View style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.errorContainer}>
          <Ionicons name="alert-circle-outline" size={32} color={theme.textTertiary} />
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>
            {error || 'Unable to load pattern data'}
          </Text>
          <TouchableOpacity
            style={[styles.retryButton, { backgroundColor: theme.surface }]}
            onPress={loadPatternData}
          >
            <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <Text style={[styles.mainTitle, { color: theme.text }]}>
          Numerology Pattern System
        </Text>
        <Text style={[styles.mainSubtitle, { color: theme.textTertiary }]}>
          Diagnostic view of your numeric signature
        </Text>

        {/* Core Numbers Strip */}
        <View style={[styles.coreNumbersStrip, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <View style={styles.coreNumberItem}>
            <Text style={[styles.coreNumberLabel, { color: theme.textTertiary }]}>Life Path</Text>
            <Text style={[styles.coreNumberValue, { color: theme.text }]}>{data.life_path}</Text>
          </View>
          <View style={[styles.coreNumberDivider, { backgroundColor: theme.border }]} />
          <View style={styles.coreNumberItem}>
            <Text style={[styles.coreNumberLabel, { color: theme.textTertiary }]}>Expression</Text>
            <Text style={[styles.coreNumberValue, { color: data.expression ? theme.text : theme.textTertiary }]}>
              {data.expression ?? '🔒'}
            </Text>
          </View>
          <View style={[styles.coreNumberDivider, { backgroundColor: theme.border }]} />
          <View style={styles.coreNumberItem}>
            <Text style={[styles.coreNumberLabel, { color: theme.textTertiary }]}>Soul Urge</Text>
            <Text style={[styles.coreNumberValue, { color: data.soul_urge ? theme.text : theme.textTertiary }]}>
              {data.soul_urge ?? '🔒'}
            </Text>
          </View>
        </View>

        {/* Energy Map (Lo Shu Grid) */}
        <LoShuGrid
          grid={data.lo_shu_grid}
          presentNumbers={data.present_numbers}
          missingNumbers={data.missing_numbers}
          theme={theme}
        />

        {/* Core Pattern */}
        <View style={[styles.corePatternSection, { backgroundColor: COLORS.accentLight, borderColor: COLORS.accent }]}>
          <Text style={[styles.corePatternLabel, { color: COLORS.accent }]}>CORE PATTERN</Text>
          <Text style={[styles.corePatternText, { color: theme.text }]}>
            {data.core_pattern}
          </Text>
        </View>

        {/* How This Shows Up */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>HOW THIS SHOWS UP</Text>
          <View style={[styles.bulletList, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            {data.how_this_shows_up.map((item, index) => (
              <View key={index} style={styles.bulletItem}>
                <View style={[styles.bulletDot, { backgroundColor: COLORS.accent }]} />
                <Text style={[styles.bulletText, { color: theme.textSecondary }]}>{item}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Internal Tension */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>INTERNAL TENSION</Text>
          <View style={styles.tensionList}>
            {data.internal_tensions.map((tension, index) => (
              <View 
                key={index} 
                style={[styles.tensionCard, { backgroundColor: COLORS.tensionBg, borderColor: COLORS.tension }]}
              >
                <View style={styles.tensionHeader}>
                  <Text style={[styles.tensionA, { color: theme.text }]}>{tension.a}</Text>
                  <Text style={[styles.tensionVs, { color: COLORS.tension }]}>vs</Text>
                  <Text style={[styles.tensionB, { color: theme.text }]}>{tension.b}</Text>
                </View>
                <Text style={[styles.tensionDescription, { color: theme.textSecondary }]}>
                  {tension.description}
                </Text>
              </View>
            ))}
          </View>
        </View>

        {/* Mirror Moment */}
        <View style={[styles.mirrorMomentSection, { backgroundColor: theme.surface, borderLeftColor: COLORS.accent }]}>
          <Text style={[styles.mirrorMomentLabel, { color: theme.textTertiary }]}>MIRROR MOMENT</Text>
          <Text style={[styles.mirrorMomentText, { color: theme.text }]}>
            {data.mirror_moment}
          </Text>
        </View>

        {/* Name Section */}
        {!existingName ? (
          <TouchableOpacity
            style={[styles.unlockButton, { backgroundColor: theme.accent }]}
            onPress={() => setShowNameModal(true)}
          >
            <Ionicons name="add-circle-outline" size={20} color={theme.background} />
            <View style={styles.unlockButtonText}>
              <Text style={[styles.unlockButtonTitle, { color: theme.background }]}>
                Add Full Birth Name
              </Text>
              <Text style={[styles.unlockButtonSubtitle, { color: theme.background, opacity: 0.7 }]}>
                Unlock Expression & Soul Urge patterns
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={18} color={theme.background} style={{ opacity: 0.5 }} />
          </TouchableOpacity>
        ) : (
          <View style={[styles.nameDisplay, { backgroundColor: theme.surface, borderColor: theme.border }]}>
            <Ionicons name="person-outline" size={16} color={theme.textSecondary} />
            <View style={styles.nameDisplayText}>
              <Text style={[styles.nameDisplayLabel, { color: theme.textTertiary }]}>Birth Name</Text>
              <Text style={[styles.nameDisplayValue, { color: theme.text }]}>{existingName}</Text>
            </View>
            <TouchableOpacity onPress={() => setShowNameModal(true)}>
              <Ionicons name="pencil-outline" size={16} color={COLORS.accent} />
            </TouchableOpacity>
          </View>
        )}

        {/* Ask Mirror */}
        <TouchableOpacity
          style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
          onPress={onOpenChat}
        >
          <Ionicons name="chatbubble-outline" size={18} color={theme.background} />
          <Text style={[styles.askMirrorText, { color: theme.background }]}>
            Explore this pattern with Mirror
          </Text>
        </TouchableOpacity>

        {/* Footer */}
        <Text style={[styles.footer, { color: theme.textTertiary }]}>
          A diagnostic lens—not a prediction system.
        </Text>
      </ScrollView>

      {/* Name Modal */}
      <Modal
        visible={showNameModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowNameModal(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalOverlay}
        >
          <View style={[styles.modalContainer, { backgroundColor: theme.surface }]}>
            <TouchableOpacity
              style={styles.modalCloseButton}
              onPress={() => setShowNameModal(false)}
            >
              <Ionicons name="close" size={24} color={theme.textSecondary} />
            </TouchableOpacity>

            <View style={styles.modalIconContainer}>
              <Ionicons name="person-outline" size={32} color={COLORS.accent} />
            </View>

            <Text style={[styles.modalTitle, { color: theme.text }]}>
              {existingName ? 'Edit Birth Name' : 'Your Full Birth Name'}
            </Text>
            <Text style={[styles.modalSubtitle, { color: theme.textTertiary }]}>
              As given at birth
            </Text>

            <TextInput
              style={[styles.nameInput, { color: theme.text, borderColor: theme.border }]}
              placeholder="e.g., John Michael Smith"
              placeholderTextColor={theme.textTertiary}
              value={nameInput}
              onChangeText={setNameInput}
              autoCapitalize="words"
              autoCorrect={false}
              autoFocus
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalSecondaryButton, { backgroundColor: theme.background }]}
                onPress={() => setShowNameModal(false)}
              >
                <Text style={[styles.modalSecondaryButtonText, { color: theme.text }]}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalPrimaryButton, { backgroundColor: COLORS.accent }]}
                onPress={handleSaveName}
                disabled={isSavingName}
              >
                {isSavingName ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={styles.modalPrimaryButtonText}>
                    {existingName ? 'Save' : 'Unlock'}
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
    padding: 20,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Header
  mainTitle: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 4,
  },
  mainSubtitle: {
    fontSize: 13,
    marginBottom: 20,
  },

  // Core Numbers Strip
  coreNumbersStrip: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
  },
  coreNumberItem: {
    flex: 1,
    alignItems: 'center',
  },
  coreNumberLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  coreNumberValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  coreNumberDivider: {
    width: 1,
    marginHorizontal: 8,
  },

  // Lo Shu Grid
  loShuContainer: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 12,
    marginBottom: 12,
  },
  gridContainer: {
    borderWidth: 2,
    borderRadius: 12,
    overflow: 'hidden',
    alignSelf: 'center',
    marginBottom: 12,
  },
  gridRow: {
    flexDirection: 'row',
  },
  gridCell: {
    width: 80,
    height: 70,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  gridCellText: {
    fontSize: 22,
    fontWeight: '700',
  },
  gridCellMultiple: {
    fontSize: 16,
    letterSpacing: 4,
  },
  gridCellLabel: {
    position: 'absolute',
    bottom: 4,
    right: 6,
    fontSize: 9,
    opacity: 0.5,
  },
  gridLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 12,
  },

  // Core Pattern
  corePatternSection: {
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
    padding: 16,
    marginBottom: 24,
  },
  corePatternLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 8,
  },
  corePatternText: {
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 24,
  },

  // Sections
  section: {
    marginBottom: 24,
  },
  bulletList: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
    gap: 12,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  bulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
  },
  bulletText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },

  // Tension
  tensionList: {
    gap: 12,
  },
  tensionCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
  },
  tensionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    marginBottom: 8,
  },
  tensionA: {
    fontSize: 14,
    fontWeight: '600',
  },
  tensionVs: {
    fontSize: 12,
    fontWeight: '700',
  },
  tensionB: {
    fontSize: 14,
    fontWeight: '600',
  },
  tensionDescription: {
    fontSize: 13,
    lineHeight: 19,
    textAlign: 'center',
  },

  // Mirror Moment
  mirrorMomentSection: {
    borderRadius: 12,
    borderLeftWidth: 4,
    padding: 16,
    marginBottom: 24,
  },
  mirrorMomentLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 8,
  },
  mirrorMomentText: {
    fontSize: 15,
    lineHeight: 23,
    fontStyle: 'italic',
  },

  // Unlock Button
  unlockButton: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    gap: 12,
  },
  unlockButtonText: {
    flex: 1,
  },
  unlockButtonTitle: {
    fontSize: 15,
    fontWeight: '600',
  },
  unlockButtonSubtitle: {
    fontSize: 12,
  },

  // Name Display
  nameDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    marginBottom: 16,
    gap: 12,
  },
  nameDisplayText: {
    flex: 1,
  },
  nameDisplayLabel: {
    fontSize: 10,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  nameDisplayValue: {
    fontSize: 14,
    fontWeight: '500',
    marginTop: 2,
  },

  // Ask Mirror
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 12,
    paddingVertical: 14,
    marginBottom: 16,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
  },

  // Footer
  footer: {
    fontSize: 12,
    textAlign: 'center',
    fontStyle: 'italic',
  },

  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  modalContainer: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    paddingBottom: 40,
  },
  modalCloseButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    zIndex: 1,
    padding: 8,
  },
  modalIconContainer: {
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
  },
  nameInput: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    marginBottom: 20,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalSecondaryButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 12,
  },
  modalSecondaryButtonText: {
    fontSize: 15,
    fontWeight: '500',
  },
  modalPrimaryButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 12,
  },
  modalPrimaryButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#fff',
  },
});
