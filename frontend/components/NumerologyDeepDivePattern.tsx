/**
 * NumerologyDeepDivePattern.tsx
 * 
 * Pattern System content for the Deep Dive tab in NumerologyLensView.
 * This component renders the Lo Shu grid and pattern sections without outer chrome.
 * 
 * Used inside NumerologyLensView's Deep Dive tab to maintain the shared lens architecture.
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
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
  has_name_numbers: boolean;
  system_explanation: string;
  lo_shu_template: number[][];
  lo_shu_counts: { [key: string]: number };
  lo_shu_display: string[][];
  present_numbers: { [key: string]: number };
  missing_numbers: number[];
  core_pattern: string;
  how_this_shows_up: string[];
  where_this_misfires: string[];
  where_this_costs_you: {
    energy_cost: string;
    relationship_cost: string;
    trust_cost: string;
  };
  balance_today: string;
  internal_tensions: { a: string; b: string; description: string }[];
  mirror_moment: string;
}

interface Props {
  userId: string;
  onOpenChat: () => void;
  existingName?: string | null;
  onNameUpdated?: () => void;
}

// =============================================================================
// COLORS
// =============================================================================

const COLORS = {
  accent: '#9B8AC4',
  accentLight: 'rgba(155, 138, 196, 0.12)',
  accentMedium: 'rgba(155, 138, 196, 0.25)',
  lessEmphasis: 'rgba(156, 163, 175, 0.4)',
  lessEmphasisText: '#9CA3AF',
  tensionGold: '#D4A574',
  tensionBg: 'rgba(212, 165, 116, 0.08)',
  // New action-relevant colors
  misfireRed: '#E57373',
  misfireBg: 'rgba(229, 115, 115, 0.08)',
  costOrange: '#FFB74D',
  costBg: 'rgba(255, 183, 77, 0.08)',
  balanceGreen: '#81C784',
  balanceBg: 'rgba(129, 199, 132, 0.08)',
};

// =============================================================================
// LO SHU GRID COMPONENT
// =============================================================================

interface LoShuGridProps {
  loShuDisplay: string[][];
  loShuTemplate: number[][];
  presentNumbers: { [key: string]: number };
  missingNumbers: number[];
  theme: any;
}

function LoShuGrid({ loShuDisplay, loShuTemplate, presentNumbers, missingNumbers, theme }: LoShuGridProps) {
  return (
    <View style={styles.loShuContainer}>
      <Text style={[styles.sectionTitle, { color: theme.text }]}>ENERGY MAP</Text>
      <Text style={[styles.sectionSubtitle, { color: theme.textTertiary }]}>
        Lo Shu Grid from your birth date
      </Text>
      
      <View style={[styles.gridContainer, { borderColor: theme.border }]}>
        {loShuDisplay.map((row, rowIdx) => (
          <View key={rowIdx} style={styles.gridRow}>
            {row.map((cellDisplay, colIdx) => {
              const templateNum = loShuTemplate[rowIdx][colIdx];
              const isMissing = cellDisplay === '—';
              const count = presentNumbers[templateNum.toString()] || 0;
              
              return (
                <View
                  key={`${rowIdx}-${colIdx}`}
                  style={[
                    styles.gridCell,
                    { borderColor: theme.border },
                    isMissing && { backgroundColor: 'rgba(156, 163, 175, 0.08)' },
                    !isMissing && { backgroundColor: COLORS.accentLight },
                  ]}
                >
                  <Text style={[
                    styles.gridCellText,
                    { color: isMissing ? COLORS.lessEmphasisText : theme.text },
                    count > 1 && styles.gridCellMultiple
                  ]}>
                    {cellDisplay}
                  </Text>
                  <Text style={[styles.gridCellLabel, { color: theme.textTertiary }]}>
                    {templateNum}
                  </Text>
                </View>
              );
            })}
          </View>
        ))}
      </View>

      <View style={styles.gridLegend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: COLORS.accent }]} />
          <Text style={[styles.legendText, { color: theme.textSecondary }]}>
            Active: {Object.entries(presentNumbers).filter(([_, c]) => c > 0).map(([n, c]) => c > 1 ? `${n}×${c}` : n).join(', ') || 'None'}
          </Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: COLORS.lessEmphasisText }]} />
          <Text style={[styles.legendText, { color: theme.textSecondary }]}>
            Less emphasized: {missingNumbers.length > 0 ? missingNumbers.join(', ') : 'None'}
          </Text>
        </View>
      </View>
    </View>
  );
}

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function NumerologyDeepDivePattern({ userId, onOpenChat, existingName, onNameUpdated }: Props) {
  const { theme } = useTheme();
  
  const [data, setData] = useState<NumerologyPatternData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Name modal state
  const [showNameModal, setShowNameModal] = useState(false);
  const [nameInput, setNameInput] = useState(existingName || '');
  const [isSavingName, setIsSavingName] = useState(false);

  useEffect(() => {
    loadPatternData();
  }, [userId]);

  useEffect(() => {
    setNameInput(existingName || '');
  }, [existingName]);

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
      setShowNameModal(false);
      loadPatternData();
      onNameUpdated?.();
    } catch (err) {
      console.error('[NumerologyPattern] Save name error:', err);
    } finally {
      setIsSavingName(false);
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Building your pattern system...
        </Text>
      </View>
    );
  }

  // Error state with fallback message
  if (error || !data) {
    return (
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
    );
  }

  return (
    <View style={styles.container}>
      {/* System Explanation Banner */}
      <View style={[styles.systemBanner, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Ionicons name="information-circle-outline" size={16} color={theme.textTertiary} />
        <Text style={[styles.systemBannerText, { color: theme.textSecondary }]}>
          {data.system_explanation || "Your core pattern comes from your birth date. Your name adds an identity layer on top of it."}
        </Text>
      </View>

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

      {/* Energy Map */}
      <LoShuGrid
        loShuDisplay={data.lo_shu_display}
        loShuTemplate={data.lo_shu_template}
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

      {/* WHERE THIS MISFIRES - New action-relevant section */}
      {data.where_this_misfires && data.where_this_misfires.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: COLORS.misfireRed }]}>WHERE THIS MISFIRES</Text>
          <View style={[styles.bulletList, { backgroundColor: COLORS.misfireBg, borderColor: COLORS.misfireRed }]}>
            {data.where_this_misfires.map((item, index) => (
              <View key={index} style={styles.bulletItem}>
                <View style={[styles.bulletDot, { backgroundColor: COLORS.misfireRed }]} />
                <Text style={[styles.bulletText, { color: theme.textSecondary }]}>{item}</Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* WHERE THIS COSTS YOU - New action-relevant section */}
      {data.where_this_costs_you && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: COLORS.costOrange }]}>WHERE THIS COSTS YOU</Text>
          <View style={[styles.costsCard, { backgroundColor: COLORS.costBg, borderColor: COLORS.costOrange }]}>
            <View style={styles.costItem}>
              <Text style={[styles.costLabel, { color: COLORS.costOrange }]}>ENERGY</Text>
              <Text style={[styles.costText, { color: theme.textSecondary }]}>{data.where_this_costs_you.energy_cost}</Text>
            </View>
            <View style={styles.costItem}>
              <Text style={[styles.costLabel, { color: COLORS.costOrange }]}>RELATIONSHIPS</Text>
              <Text style={[styles.costText, { color: theme.textSecondary }]}>{data.where_this_costs_you.relationship_cost}</Text>
            </View>
            <View style={styles.costItem}>
              <Text style={[styles.costLabel, { color: COLORS.costOrange }]}>TRUST</Text>
              <Text style={[styles.costText, { color: theme.textSecondary }]}>{data.where_this_costs_you.trust_cost}</Text>
            </View>
          </View>
        </View>
      )}

      {/* ONE WAY TO BALANCE TODAY - New action section */}
      {data.balance_today && (
        <View style={[styles.balanceSection, { backgroundColor: COLORS.balanceBg, borderColor: COLORS.balanceGreen }]}>
          <Text style={[styles.balanceLabel, { color: COLORS.balanceGreen }]}>ONE WAY TO BALANCE TODAY</Text>
          <Text style={[styles.balanceText, { color: theme.text }]}>
            {data.balance_today}
          </Text>
        </View>
      )}

      {/* Tensions to Notice */}
      {data.internal_tensions && data.internal_tensions.length > 0 && (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>TENSIONS TO NOTICE</Text>
          <View style={styles.tensionList}>
            {data.internal_tensions.map((tension, index) => (
              <View 
                key={index} 
                style={[styles.tensionCard, { backgroundColor: COLORS.tensionBg, borderColor: COLORS.tensionGold }]}
              >
                <View style={styles.tensionHeader}>
                  <Text style={[styles.tensionA, { color: theme.text }]}>{tension.a}</Text>
                  <Text style={[styles.tensionVs, { color: COLORS.tensionGold }]}>vs</Text>
                  <Text style={[styles.tensionB, { color: theme.text }]}>{tension.b}</Text>
                </View>
                <Text style={[styles.tensionDescription, { color: theme.textSecondary }]}>
                  {tension.description}
                </Text>
              </View>
            ))}
          </View>
        </View>
      )}

      {/* Reflection */}
      <View style={[styles.reflectionSection, { backgroundColor: theme.surface, borderLeftColor: COLORS.accent }]}>
        <Text style={[styles.reflectionLabel, { color: theme.textTertiary }]}>REFLECTION</Text>
        <Text style={[styles.reflectionText, { color: theme.text }]}>
          {data.mirror_moment}
        </Text>
      </View>

      {/* Edit birth name link */}
      {!existingName && (
        <TouchableOpacity
          style={[styles.addNameButton, { borderColor: COLORS.accent }]}
          onPress={() => setShowNameModal(true)}
        >
          <Ionicons name="add-circle-outline" size={18} color={COLORS.accent} />
          <Text style={[styles.addNameButtonText, { color: COLORS.accent }]}>
            Add birth name for identity layer
          </Text>
        </TouchableOpacity>
      )}

      {/* Explore with Mirror CTA */}
      <TouchableOpacity
        style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
        onPress={onOpenChat}
      >
        <Ionicons name="chatbubble-outline" size={18} color={theme.background} />
        <Text style={[styles.askMirrorText, { color: theme.background }]}>
          Explore this pattern with Mirror
        </Text>
      </TouchableOpacity>

      {/* Positioning Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        A lens for noticing patterns, not a statement of identity. Use it or leave it.
      </Text>

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
              Your Full Birth Name
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
                  <Text style={styles.modalPrimaryButtonText}>Unlock</Text>
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
    paddingTop: 8,
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
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

  // System Banner
  systemBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
    borderWidth: 1,
  },
  systemBannerText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
  },

  // Core Numbers Strip
  coreNumbersStrip: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 14,
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
    fontSize: 22,
    fontWeight: '700',
  },
  coreNumberDivider: {
    width: 1,
    marginHorizontal: 8,
  },

  // Lo Shu Grid
  loShuContainer: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 11,
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
    width: 72,
    height: 60,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
    position: 'relative',
  },
  gridCellText: {
    fontSize: 20,
    fontWeight: '700',
  },
  gridCellMultiple: {
    fontSize: 14,
    letterSpacing: 4,
  },
  gridCellLabel: {
    position: 'absolute',
    bottom: 3,
    right: 5,
    fontSize: 8,
    opacity: 0.5,
  },
  gridLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    flexWrap: 'wrap',
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  legendDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  legendText: {
    fontSize: 11,
  },

  // Core Pattern
  corePatternSection: {
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
    padding: 14,
    marginBottom: 20,
  },
  corePatternLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  corePatternText: {
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 22,
  },

  // Sections
  section: {
    marginBottom: 20,
  },
  bulletList: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    gap: 10,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  bulletDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    marginTop: 7,
  },
  bulletText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 20,
  },

  // Tension
  tensionList: {
    gap: 10,
  },
  tensionCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 12,
  },
  tensionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginBottom: 6,
  },
  tensionA: {
    fontSize: 13,
    fontWeight: '600',
  },
  tensionVs: {
    fontSize: 11,
    fontWeight: '700',
  },
  tensionB: {
    fontSize: 13,
    fontWeight: '600',
  },
  tensionDescription: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
  },

  // Costs Card
  costsCard: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 14,
    gap: 14,
  },
  costItem: {
    gap: 4,
  },
  costLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  costText: {
    fontSize: 13,
    lineHeight: 19,
  },

  // Balance Section
  balanceSection: {
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
    padding: 14,
    marginBottom: 20,
  },
  balanceLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  balanceText: {
    fontSize: 14,
    lineHeight: 21,
    fontWeight: '500',
  },

  // Reflection
  reflectionSection: {
    borderRadius: 12,
    borderLeftWidth: 4,
    padding: 14,
    marginBottom: 16,
  },
  reflectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  reflectionText: {
    fontSize: 14,
    lineHeight: 21,
    fontStyle: 'italic',
  },

  // Add Name Button
  addNameButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 12,
    marginBottom: 12,
  },
  addNameButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Ask Mirror
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderRadius: 12,
    paddingVertical: 14,
    marginBottom: 12,
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
    marginBottom: 16,
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
