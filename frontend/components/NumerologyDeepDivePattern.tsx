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
import CrossLensChainRow from './CrossLensChainRow';

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
  // V1 Mirror Layers
  continuation?: string;
  echo?: string;
  cross_link?: string;
  memory?: {
    memory_line: string;
    recurrence_count: number;
    last_seen_at: string;
    memory_state: string;
  } | null;
  genius?: string;
  // Original fields
  core_pattern: string;
  how_this_shows_up: string[];
  how_this_shows_up_today: string[];
  when_this_gets_triggered: string[];
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
  // Action-relevant colors
  misfireRed: '#E57373',
  misfireBg: 'rgba(229, 115, 115, 0.08)',
  costOrange: '#FFB74D',
  costBg: 'rgba(255, 183, 77, 0.08)',
  balanceGreen: '#81C784',
  balanceBg: 'rgba(129, 199, 132, 0.08)',
  // Time-aware colors
  todayBlue: '#64B5F6',
  todayBg: 'rgba(100, 181, 246, 0.08)',
  triggerPurple: '#BA68C8',
  triggerBg: 'rgba(186, 104, 200, 0.08)',
  // Identity layer
  identityGold: '#FFD54F',
  identityBg: 'rgba(255, 213, 79, 0.08)',
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
  
  // Premium V1: Collapsible states for proof sections
  const [showLoShu, setShowLoShu] = useState(false);
  const [showIdentity, setShowIdentity] = useState(false);
  const [showTensions, setShowTensions] = useState(false);

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
      {/* ========== PREMIUM V1 STRUCTURE ========== */}
      
      {/* 1. CONTINUATION (whisper) */}
      {data.continuation && (
        <Text style={[styles.continuation, { color: theme.textTertiary }]}>
          {data.continuation}
        </Text>
      )}
      
      {/* Life Path Number - Minimal display */}
      <View style={styles.lifePathBadge}>
        <Text style={[styles.lifePathLabel, { color: theme.textTertiary }]}>Life Path</Text>
        <Text style={[styles.lifePathNumber, { color: theme.text }]}>{data.life_path}</Text>
      </View>
      
      {/* 2. CORE TRUTH (hero) */}
      <View style={styles.heroSection}>
        <View style={[styles.heroAccent, { backgroundColor: COLORS.accent }]} />
        <Text style={[styles.heroText, { color: theme.text }]}>
          {data.core_pattern}
        </Text>
      </View>
      
      {/* 3. ECHO (quick reinforcement) */}
      {data.echo && (
        <Text style={[styles.echoText, { color: theme.textSecondary }]}>
          {data.echo}
        </Text>
      )}
      
      {/* 4. CROSS LINK (subtle connection) */}
      <CrossLensChainRow 
        currentLens="numerology"
        corePattern={data.core_pattern}
        patternKey={`life_path_${data.life_path}`}
        linkingPhrase={data.cross_link || undefined}
      />
      
      {/* 5. HOW THIS SHOWS UP */}
      {data.how_this_shows_up_today && data.how_this_shows_up_today.length > 0 && (
        <View style={styles.premiumSection}>
          <Text style={[styles.premiumSectionTitle, { color: theme.textSecondary }]}>How this shows up</Text>
          <View style={styles.premiumBulletList}>
            {data.how_this_shows_up_today.map((item, index) => (
              <View key={index} style={styles.premiumBulletItem}>
                <View style={[styles.premiumBulletDot, { backgroundColor: COLORS.accent, opacity: 0.4 }]} />
                <Text style={[styles.premiumBulletText, { color: theme.text }]}>{item}</Text>
              </View>
            ))}
          </View>
        </View>
      )}
      
      {/* 6. WHEN THIS BACKFIRES */}
      {data.where_this_misfires && data.where_this_misfires.length > 0 && (
        <View style={styles.premiumSection}>
          <Text style={[styles.premiumSectionTitle, { color: theme.textSecondary }]}>When this backfires</Text>
          <View style={styles.premiumBulletList}>
            {data.where_this_misfires.map((item, index) => (
              <View key={index} style={styles.premiumBulletItem}>
                <View style={[styles.premiumBulletDot, { backgroundColor: COLORS.misfireRed, opacity: 0.5 }]} />
                <Text style={[styles.premiumBulletText, { color: theme.text }]}>{item}</Text>
              </View>
            ))}
          </View>
        </View>
      )}
      
      {/* 7. GENIUS (integrated, subtle accent) */}
      {data.genius && (
        <View style={styles.geniusSection}>
          <View style={[styles.geniusAccentBar, { backgroundColor: COLORS.accent, opacity: 0.3 }]} />
          <Text style={[styles.geniusText, { color: theme.text }]}>
            {data.genius}
          </Text>
        </View>
      )}
      
      {/* 8. WHAT THIS COSTS */}
      {data.where_this_costs_you && (
        <View style={styles.costsSection}>
          <Text style={[styles.premiumSectionTitle, { color: theme.textSecondary }]}>What this costs</Text>
          <View style={styles.costsList}>
            <View style={styles.costRow}>
              <Text style={[styles.costLabel, { color: theme.textTertiary }]}>Energy</Text>
              <Text style={[styles.costValue, { color: theme.text }]}>{data.where_this_costs_you.energy_cost}</Text>
            </View>
            <View style={styles.costRow}>
              <Text style={[styles.costLabel, { color: theme.textTertiary }]}>Relationships</Text>
              <Text style={[styles.costValue, { color: theme.text }]}>{data.where_this_costs_you.relationship_cost}</Text>
            </View>
            <View style={styles.costRow}>
              <Text style={[styles.costLabel, { color: theme.textTertiary }]}>Trust</Text>
              <Text style={[styles.costValue, { color: theme.text }]}>{data.where_this_costs_you.trust_cost}</Text>
            </View>
          </View>
        </View>
      )}
      
      {/* 9. ONE SHIFT (pause moment) */}
      {data.balance_today && (
        <View style={styles.shiftSection}>
          <View style={[styles.shiftAccent, { backgroundColor: COLORS.balanceGreen, opacity: 0.2 }]} />
          <Text style={[styles.shiftLabel, { color: COLORS.balanceGreen }]}>One shift</Text>
          <Text style={[styles.shiftText, { color: theme.text }]}>
            {data.balance_today}
          </Text>
        </View>
      )}
      
      {/* 10. PROOF / DETAILS (collapsible) */}
      <View style={styles.proofSection}>
        {/* Energy Map Collapsible */}
        <TouchableOpacity 
          style={styles.collapsibleHeader}
          onPress={() => setShowLoShu(!showLoShu)}
          activeOpacity={0.7}
        >
          <Text style={[styles.collapsibleTitle, { color: theme.textSecondary }]}>Your energy map</Text>
          <Ionicons 
            name={showLoShu ? "chevron-up" : "chevron-down"} 
            size={20} 
            color={theme.textTertiary} 
          />
        </TouchableOpacity>
        {showLoShu && (
          <View style={styles.collapsibleContent}>
            <LoShuGrid
              loShuDisplay={data.lo_shu_display}
              loShuTemplate={data.lo_shu_template}
              presentNumbers={data.present_numbers}
              missingNumbers={data.missing_numbers}
              theme={theme}
            />
          </View>
        )}
        
        {/* Identity Layer Collapsible (if name exists) */}
        {data.has_name_numbers && (
          <>
            <TouchableOpacity 
              style={styles.collapsibleHeader}
              onPress={() => setShowIdentity(!showIdentity)}
              activeOpacity={0.7}
            >
              <Text style={[styles.collapsibleTitle, { color: theme.textSecondary }]}>Your identity numbers</Text>
              <Ionicons 
                name={showIdentity ? "chevron-up" : "chevron-down"} 
                size={20} 
                color={theme.textTertiary} 
              />
            </TouchableOpacity>
            {showIdentity && (
              <View style={styles.collapsibleContent}>
                <View style={styles.identityRow}>
                  <View style={styles.identityItem}>
                    <Text style={[styles.identityLabel, { color: theme.textTertiary }]}>Expression</Text>
                    <Text style={[styles.identityValue, { color: theme.text }]}>{data.expression}</Text>
                    <Text style={[styles.identityDesc, { color: theme.textTertiary }]}>how you show up</Text>
                  </View>
                  <View style={styles.identityItem}>
                    <Text style={[styles.identityLabel, { color: theme.textTertiary }]}>Soul Urge</Text>
                    <Text style={[styles.identityValue, { color: theme.text }]}>{data.soul_urge}</Text>
                    <Text style={[styles.identityDesc, { color: theme.textTertiary }]}>what you crave</Text>
                  </View>
                  {data.personality && (
                    <View style={styles.identityItem}>
                      <Text style={[styles.identityLabel, { color: theme.textTertiary }]}>Personality</Text>
                      <Text style={[styles.identityValue, { color: theme.text }]}>{data.personality}</Text>
                      <Text style={[styles.identityDesc, { color: theme.textTertiary }]}>first impression</Text>
                    </View>
                  )}
                </View>
              </View>
            )}
          </>
        )}
        
        {/* Tensions Collapsible */}
        {data.internal_tensions && data.internal_tensions.length > 0 && (
          <>
            <TouchableOpacity 
              style={styles.collapsibleHeader}
              onPress={() => setShowTensions(!showTensions)}
              activeOpacity={0.7}
            >
              <Text style={[styles.collapsibleTitle, { color: theme.textSecondary }]}>Tensions to notice</Text>
              <Ionicons 
                name={showTensions ? "chevron-up" : "chevron-down"} 
                size={20} 
                color={theme.textTertiary} 
              />
            </TouchableOpacity>
            {showTensions && (
              <View style={styles.collapsibleContent}>
                {data.internal_tensions.map((tension, index) => (
                  <View key={index} style={styles.tensionItem}>
                    <Text style={[styles.tensionPair, { color: theme.text }]}>
                      {tension.a} <Text style={{ color: theme.textTertiary }}>vs</Text> {tension.b}
                    </Text>
                    <Text style={[styles.tensionDesc, { color: theme.textSecondary }]}>{tension.description}</Text>
                  </View>
                ))}
              </View>
            )}
          </>
        )}
      </View>
      
      {/* Edit birth name link */}
      {!existingName && (
        <TouchableOpacity
          style={styles.addNameLink}
          onPress={() => setShowNameModal(true)}
        >
          <Ionicons name="add-circle-outline" size={16} color={theme.textTertiary} />
          <Text style={[styles.addNameLinkText, { color: theme.textTertiary }]}>
            Add birth name for identity layer
          </Text>
        </TouchableOpacity>
      )}
      
      {/* Explore with Mirror CTA */}
      <TouchableOpacity
        style={[styles.exploreCTA, { backgroundColor: theme.text }]}
        onPress={onOpenChat}
      >
        <Ionicons name="chatbubble-outline" size={18} color={theme.background} />
        <Text style={[styles.exploreCTAText, { color: theme.background }]}>
          Explore this pattern
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
    paddingHorizontal: 16,
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  retryText: {
    fontSize: 16,
    fontWeight: '500',
  },

  // =============================================================================
  // PREMIUM V1 STYLES
  // =============================================================================

  // 1. Continuation (whisper)
  continuation: {
    fontSize: 16,
    opacity: 0.6,
    marginBottom: 24,
    fontStyle: 'italic',
  },

  // Life Path Badge (minimal)
  lifePathBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  lifePathLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  lifePathNumber: {
    fontSize: 22,
    fontWeight: '700',
  },

  // 2. Hero Section (Core Truth)
  heroSection: {
    marginBottom: 20,
    paddingTop: 40,
    paddingBottom: 40,
  },
  heroAccent: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: 32,
    height: 3,
    borderRadius: 2,
  },
  heroText: {
    fontSize: 22,
    fontWeight: '600',
    lineHeight: 32,
  },

  // 3. Echo (reinforcement)
  echoText: {
    fontSize: 16,
    marginBottom: 16,
    opacity: 0.7,
  },

  // 5-6. Premium Section (bullet lists)
  premiumSection: {
    marginBottom: 28,
  },
  premiumSectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.3,
    marginBottom: 16,
    textTransform: 'lowercase',
  },
  premiumBulletList: {
    gap: 10,
  },
  premiumBulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  premiumBulletDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    marginTop: 7,
  },
  premiumBulletText: {
    flex: 1,
    fontSize: 17,
    lineHeight: 30,
  },

  // 7. Genius (subtle accent)
  geniusSection: {
    paddingLeft: 16,
    marginBottom: 28,
    position: 'relative',
  },
  geniusAccentBar: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 3,
    borderRadius: 2,
  },
  geniusText: {
    fontSize: 17,
    lineHeight: 31,
    fontWeight: '500',
  },

  // 8. Costs Section
  costsSection: {
    marginBottom: 28,
  },
  costsList: {
    gap: 12,
  },
  costRow: {
    gap: 4,
  },
  costValue: {
    fontSize: 16,
    lineHeight: 32,
  },

  // 9. Shift Section (pause moment)
  shiftSection: {
    paddingTop: 32,
    paddingBottom: 32,
    marginBottom: 28,
    position: 'relative',
  },
  shiftAccent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 2,
    borderRadius: 1,
  },
  shiftLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: 14,
  },
  shiftText: {
    fontSize: 16,
    fontWeight: '500',
    lineHeight: 32,
  },

  // 10. Proof Section (collapsibles)
  proofSection: {
    marginTop: 16,
    marginBottom: 24,
  },
  collapsibleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: 'rgba(128, 128, 128, 0.2)',
  },
  collapsibleTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  collapsibleContent: {
    paddingVertical: 16,
  },

  // Identity Row (in collapsible)
  identityRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 8,
  },
  identityItem: {
    alignItems: 'center',
    flex: 1,
  },
  identityLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  identityValue: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 2,
  },
  identityDesc: {
    fontSize: 14,
    fontStyle: 'italic',
  },

  // Tension Items (in collapsible)
  tensionItem: {
    marginBottom: 16,
  },
  tensionPair: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  tensionDesc: {
    fontSize: 16,
    lineHeight: 32,
  },

  // Add Name Link
  addNameLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingVertical: 12,
  },
  addNameLinkText: {
    fontSize: 16,
  },

  // Explore CTA
  exploreCTA: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 8,
    marginBottom: 24,
  },
  exploreCTAText: {
    fontSize: 17,
    fontWeight: '600',
  },

  // =============================================================================
  // LEGACY STYLES (kept for modal compatibility)
  // =============================================================================

  // System Banner (now hidden but kept for reference)
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
    fontSize: 14,
    lineHeight: 31,
  },

  // Layer Headers (Core vs Identity)
  layerHeader: {
    borderLeftWidth: 3,
    paddingLeft: 12,
    marginBottom: 16,
  },
  layerLabel: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
  },
  layerSubLabel: {
    fontSize: 14,
    marginTop: 2,
  },

  // Core Numbers Strip
  coreNumbersStrip: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 14,
    marginBottom: 20,
    borderWidth: 1,
    justifyContent: 'center',
  },
  coreNumberItem: {
    flex: 1,
    alignItems: 'center',
  },
  coreNumberLabel: {
    fontSize: 14,
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

  // Identity Numbers Strip (Name-based)
  identityNumbersStrip: {
    flexDirection: 'row',
    borderRadius: 12,
    padding: 14,
    marginBottom: 20,
    borderWidth: 1,
  },
  identityNumberItem: {
    flex: 1,
    alignItems: 'center',
  },
  identityNumberLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  identityNumberValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  identityNumberDesc: {
    fontSize: 9,
    marginTop: 2,
    fontStyle: 'italic',
  },
  identityNumberDivider: {
    width: 1,
    marginHorizontal: 8,
    opacity: 0.3,
  },

  // Lo Shu Grid
  loShuContainer: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 14,
    marginBottom: 16,
  },
  sectionSubtitleWarning: {
    fontSize: 14,
    marginBottom: 14,
    fontStyle: 'italic',
  },
  gridContainer: {
    borderWidth: 2,
    borderRadius: 12,
    overflow: 'hidden',
    alignSelf: 'center',
    marginBottom: 16,
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
    fontSize: 24,
    fontWeight: '700',
  },
  gridCellMultiple: {
    fontSize: 16,
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
    fontSize: 14,
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
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  corePatternText: {
    fontSize: 17,
    fontWeight: '600',
    lineHeight: 30,
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
    fontSize: 16,
    lineHeight: 32,
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
    fontSize: 16,
    fontWeight: '600',
  },
  tensionVs: {
    fontSize: 14,
    fontWeight: '700',
  },
  tensionB: {
    fontSize: 16,
    fontWeight: '600',
  },
  tensionDescription: {
    fontSize: 14,
    lineHeight: 31,
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
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  costText: {
    fontSize: 16,
    lineHeight: 32,
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
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  balanceText: {
    fontSize: 16,
    lineHeight: 30,
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
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
    marginBottom: 6,
  },
  reflectionText: {
    fontSize: 16,
    lineHeight: 30,
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
    marginBottom: 16,
  },
  addNameButtonText: {
    fontSize: 16,
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
    marginBottom: 16,
  },
  askMirrorText: {
    fontSize: 17,
    fontWeight: '600',
  },

  // Footer
  footer: {
    fontSize: 14,
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
    fontSize: 16,
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
    fontSize: 17,
    fontWeight: '500',
  },
  modalPrimaryButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 12,
  },
  modalPrimaryButtonText: {
    fontSize: 17,
    fontWeight: '600',
    color: '#fff',
  },
});
