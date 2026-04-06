/**
 * NumerologySummaryV2.tsx
 * =======================
 * 
 * Upgraded Numerology Summary following Mirror doctrine:
 * COMPUTED ≠ SURFACED ≠ INTERPRETED
 * 
 * Structure:
 * 1. PATTERN SUMMARY (Mirror tone) - Top card
 * 2. YOUR PATTERN BLUEPRINT - Life Path, Expression, Soul Urge, Personality
 * 3. YOUR ENERGY MAP - Lo Shu Grid
 * 4. HOW THIS IS BUILT - Collapsible computation explanation
 * 5. HOW THIS PATTERN PLAYS OUT - Mirror synthesis
 * 6. TENSIONS TO NOTICE - Missing number behavioral mappings
 * 7. CTA - Unified InsightCardFooter
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../contexts/ThemeContext';
import { InsightCardFooter } from './InsightCardFooter';
import api from '../services/api';

// =============================================================================
// TYPES
// =============================================================================

interface NumerologyCompute {
  input: {
    full_name: string | null;
    birth_date: string;
  };
  pythagorean: {
    life_path: number;
    expression: number | null;
    soul_urge: number | null;
    personality: number | null;
    name_breakdown: Array<{ letter: string; value: number | null }> | null;
  };
  lo_shu: {
    digit_counts: Record<string, number>;
    grid: (number | null)[][];
    missing_numbers: number[];
    present_numbers: number[];
  };
  tensions: Array<{
    number: number;
    label: string;
    behavioral: string;
    tension: string;
  }>;
  synthesis: {
    lines: string[];
    summary: string;
  };
  computation_version: string;
  computed_at: string;
}

interface Props {
  userId: string;
  onOpenChat: () => void;
  existingName?: string | null;
  onAddName?: () => void;
}

// =============================================================================
// COMPONENT
// =============================================================================

export default function NumerologySummaryV2({ userId, onOpenChat, existingName, onAddName }: Props) {
  const { theme } = useTheme();
  const [data, setData] = useState<NumerologyCompute | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showComputation, setShowComputation] = useState(false);

  // Fetch compute data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await api.get(`/api/numerology/compute/${userId}`);
        setData(response.data);
      } catch (err: any) {
        console.error('[NumerologySummaryV2] Error:', err);
        setError(err.response?.data?.detail || 'Failed to load numerology data');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [userId]);

  // =============================================================================
  // RENDER HELPERS
  // =============================================================================

  const renderPatternSummary = () => {
    if (!data?.synthesis) return null;

    return (
      <View style={[styles.card, styles.summaryCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.cardLabel, { color: theme.textTertiary }]}>PATTERN SUMMARY</Text>
        {data.synthesis.lines.map((line, index) => (
          <Text key={index} style={[styles.summaryLine, { color: theme.text }]}>
            {line}
          </Text>
        ))}
        
        {/* Unified Footer */}
        <InsightCardFooter
          source={{
            lens: 'numerology',
            type: 'pattern_summary',
            name: 'Numerology Pattern Summary',
            value: data.synthesis.summary,
            id: `numerology_summary_${userId}`,
          }}
          patternSignature={`numerology_summary_${userId}`}
          context="numerology_summary"
          prompt={data.synthesis.lines[0] || 'Reflect on your numerology pattern'}
          showBorder={false}
        />
      </View>
    );
  };

  const renderPatternBlueprint = () => {
    if (!data?.pythagorean) return null;
    
    const { life_path, expression, soul_urge, personality } = data.pythagorean;
    const hasNameNumbers = expression !== null;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.cardLabel, { color: theme.textTertiary }]}>YOUR PATTERN BLUEPRINT</Text>
        <Text style={[styles.helperText, { color: theme.textSecondary }]}>
          These are derived from your name and birth date
        </Text>

        <View style={styles.blueprintGrid}>
          {/* Life Path - Always shown */}
          <View style={styles.blueprintItem}>
            <Text style={[styles.blueprintNumber, { color: theme.accent }]}>{life_path}</Text>
            <Text style={[styles.blueprintLabel, { color: theme.textSecondary }]}>Life Path</Text>
          </View>

          {/* Expression */}
          <View style={styles.blueprintItem}>
            <Text style={[styles.blueprintNumber, { color: hasNameNumbers ? theme.accent : theme.textTertiary }]}>
              {expression ?? '?'}
            </Text>
            <Text style={[styles.blueprintLabel, { color: theme.textSecondary }]}>Expression</Text>
          </View>

          {/* Soul Urge */}
          <View style={styles.blueprintItem}>
            <Text style={[styles.blueprintNumber, { color: hasNameNumbers ? theme.accent : theme.textTertiary }]}>
              {soul_urge ?? '?'}
            </Text>
            <Text style={[styles.blueprintLabel, { color: theme.textSecondary }]}>Soul Urge</Text>
          </View>

          {/* Personality */}
          <View style={styles.blueprintItem}>
            <Text style={[styles.blueprintNumber, { color: hasNameNumbers ? theme.accent : theme.textTertiary }]}>
              {personality ?? '?'}
            </Text>
            <Text style={[styles.blueprintLabel, { color: theme.textSecondary }]}>Personality</Text>
          </View>
        </View>

        {/* Add Name CTA if missing */}
        {!hasNameNumbers && onAddName && (
          <TouchableOpacity
            style={[styles.addNameButton, { borderColor: theme.accent }]}
            onPress={onAddName}
          >
            <Ionicons name="add-circle-outline" size={18} color={theme.accent} />
            <Text style={[styles.addNameText, { color: theme.accent }]}>Add birth name to unlock</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  const renderLoShuGrid = () => {
    if (!data?.lo_shu) return null;

    const { grid, missing_numbers, present_numbers, digit_counts } = data.lo_shu;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.cardLabel, { color: theme.textTertiary }]}>YOUR ENERGY MAP</Text>
        <Text style={[styles.helperText, { color: theme.textSecondary }]}>
          Lo Shu Grid — digit distribution from your birth date
        </Text>

        {/* Grid */}
        <View style={styles.gridContainer}>
          {grid.map((row, rowIndex) => (
            <View key={rowIndex} style={styles.gridRow}>
              {row.map((num, colIndex) => {
                const count = num ? digit_counts[String(num)] || 0 : 0;
                const isPresent = num !== null;
                
                return (
                  <View
                    key={colIndex}
                    style={[
                      styles.gridCell,
                      { 
                        backgroundColor: isPresent ? theme.accent + '15' : theme.surfaceLight,
                        borderColor: isPresent ? theme.accent + '40' : theme.border
                      }
                    ]}
                  >
                    {isPresent ? (
                      <>
                        <Text style={[styles.gridNumber, { color: theme.accent }]}>{num}</Text>
                        {count > 1 && (
                          <Text style={[styles.gridCount, { color: theme.textSecondary }]}>×{count}</Text>
                        )}
                      </>
                    ) : (
                      <Text style={[styles.gridEmpty, { color: theme.textTertiary }]}>—</Text>
                    )}
                  </View>
                );
              })}
            </View>
          ))}
        </View>

        {/* Missing Numbers */}
        {missing_numbers.length > 0 && (
          <View style={styles.missingSection}>
            <Text style={[styles.missingSectionLabel, { color: theme.textTertiary }]}>
              NOT NATURALLY AVAILABLE
            </Text>
            <Text style={[styles.missingNumbers, { color: theme.text }]}>
              {missing_numbers.join(', ')}
            </Text>
            <Text style={[styles.missingHelper, { color: theme.textSecondary }]}>
              These are patterns you tend to build through experience rather than start with.
            </Text>
          </View>
        )}

        {/* Present Numbers */}
        {present_numbers.length > 0 && (
          <View style={styles.presentSection}>
            <Text style={[styles.presentSectionLabel, { color: theme.textTertiary }]}>
              NATURALLY PRESENT
            </Text>
            <Text style={[styles.presentNumbers, { color: theme.accent }]}>
              {present_numbers.join(', ')}
            </Text>
          </View>
        )}
      </View>
    );
  };

  const renderHowThisIsBuilt = () => {
    if (!data) return null;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.collapsibleHeader}
          onPress={() => setShowComputation(!showComputation)}
        >
          <Text style={[styles.collapsibleLabel, { color: theme.textSecondary }]}>
            What this is based on
          </Text>
          <Ionicons
            name={showComputation ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {showComputation && (
          <View style={styles.computationContent}>
            <Text style={[styles.computationText, { color: theme.textSecondary }]}>
              <Text style={{ fontWeight: '600' }}>Birth date</Text> → digit distribution (Lo Shu Grid)
            </Text>
            <Text style={[styles.computationText, { color: theme.textSecondary }]}>
              <Text style={{ fontWeight: '600' }}>Full name</Text> → letter-to-number mapping (Pythagorean system)
            </Text>

            {/* Name Breakdown */}
            {data.pythagorean.name_breakdown && data.pythagorean.name_breakdown.length > 0 && (
              <View style={styles.nameBreakdown}>
                <Text style={[styles.breakdownLabel, { color: theme.textTertiary }]}>
                  NAME BREAKDOWN
                </Text>
                <View style={styles.breakdownGrid}>
                  {data.pythagorean.name_breakdown.map((item, index) => (
                    item.value !== null ? (
                      <View key={index} style={styles.breakdownItem}>
                        <Text style={[styles.breakdownLetter, { color: theme.text }]}>{item.letter}</Text>
                        <Text style={[styles.breakdownValue, { color: theme.accent }]}>{item.value}</Text>
                      </View>
                    ) : (
                      <View key={index} style={styles.breakdownSpace} />
                    )
                  ))}
                </View>
              </View>
            )}

            <Text style={[styles.computationNote, { color: theme.textTertiary }]}>
              Version: {data.computation_version}
            </Text>
          </View>
        )}
      </View>
    );
  };

  const renderTensions = () => {
    if (!data?.tensions || data.tensions.length === 0) return null;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.cardLabel, { color: theme.textTertiary }]}>TENSIONS TO NOTICE</Text>

        {data.tensions.map((tension, index) => (
          <View key={index} style={styles.tensionItem}>
            <View style={[styles.tensionBullet, { backgroundColor: theme.accent }]} />
            <View style={styles.tensionContent}>
              <Text style={[styles.tensionBehavioral, { color: theme.text }]}>
                {tension.behavioral}
              </Text>
              <Text style={[styles.tensionLabel, { color: theme.textTertiary }]}>
                ({tension.number} — {tension.label})
              </Text>
            </View>
          </View>
        ))}

        {/* Unified Footer */}
        <InsightCardFooter
          source={{
            lens: 'numerology',
            type: 'tensions',
            name: 'Numerology Tensions',
            value: data.tensions.map(t => t.behavioral).join('; '),
            id: `numerology_tensions_${userId}`,
          }}
          patternSignature={`numerology_tensions_${userId}`}
          context="numerology_tensions"
          prompt="Which of these tensions feels most present in your life right now?"
          showBorder={false}
        />
      </View>
    );
  };

  // =============================================================================
  // MAIN RENDER
  // =============================================================================

  if (isLoading) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.accent} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading your numerology pattern...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.errorContainer, { backgroundColor: theme.background }]}>
        <Ionicons name="alert-circle-outline" size={32} color={theme.textTertiary} />
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
        <TouchableOpacity
          style={[styles.retryButton, { backgroundColor: theme.surface }]}
          onPress={() => {
            setError(null);
            setIsLoading(true);
            // Re-fetch
            api.get(`/api/numerology/compute/${userId}`)
              .then(response => setData(response.data))
              .catch(err => setError(err.response?.data?.detail || 'Failed to load'))
              .finally(() => setIsLoading(false));
          }}
        >
          <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.background }]}
      contentContainerStyle={styles.contentContainer}
      showsVerticalScrollIndicator={false}
    >
      {/* 1. PATTERN SUMMARY */}
      {renderPatternSummary()}

      {/* 2. YOUR PATTERN BLUEPRINT */}
      {renderPatternBlueprint()}

      {/* 3. YOUR ENERGY MAP (Lo Shu Grid) */}
      {renderLoShuGrid()}

      {/* 4. HOW THIS IS BUILT (Collapsible) */}
      {renderHowThisIsBuilt()}

      {/* 5. TENSIONS TO NOTICE */}
      {renderTensions()}

      {/* Secondary Action: Ask Mirror */}
      <TouchableOpacity
        style={[styles.askMirrorButton, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
        onPress={onOpenChat}
      >
        <Ionicons name="chatbubble-outline" size={18} color={theme.textSecondary} />
        <Text style={[styles.askMirrorText, { color: theme.textSecondary }]}>
          Ask about your pattern
        </Text>
      </TouchableOpacity>

      {/* Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        Pattern notation, not prediction. A lens for noticing, not a truth to follow.
      </Text>
    </ScrollView>
  );
}

// =============================================================================
// STYLES
// =============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
    gap: 16,
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
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Cards
  card: {
    borderRadius: 12,
    borderWidth: 1,
    padding: 16,
  },
  summaryCard: {
    borderLeftWidth: 3,
  },
  cardLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  helperText: {
    fontSize: 12,
    marginBottom: 16,
    lineHeight: 18,
  },

  // Pattern Summary
  summaryLine: {
    fontSize: 15,
    lineHeight: 24,
    marginBottom: 8,
  },

  // Blueprint
  blueprintGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  blueprintItem: {
    alignItems: 'center',
    flex: 1,
  },
  blueprintNumber: {
    fontSize: 28,
    fontWeight: '700',
  },
  blueprintLabel: {
    fontSize: 11,
    marginTop: 4,
  },
  addNameButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderRadius: 8,
    borderStyle: 'dashed',
  },
  addNameText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Lo Shu Grid
  gridContainer: {
    alignItems: 'center',
    marginVertical: 16,
  },
  gridRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  gridCell: {
    width: 60,
    height: 60,
    borderRadius: 8,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  gridNumber: {
    fontSize: 24,
    fontWeight: '700',
  },
  gridCount: {
    fontSize: 10,
    marginTop: 2,
  },
  gridEmpty: {
    fontSize: 20,
  },
  missingSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
  },
  missingSectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  missingNumbers: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
  },
  missingHelper: {
    fontSize: 12,
    lineHeight: 18,
  },
  presentSection: {
    marginTop: 12,
  },
  presentSectionLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  presentNumbers: {
    fontSize: 16,
    fontWeight: '600',
  },

  // How This Is Built
  collapsibleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  collapsibleLabel: {
    fontSize: 13,
    fontWeight: '500',
  },
  computationContent: {
    marginTop: 16,
    gap: 8,
  },
  computationText: {
    fontSize: 13,
    lineHeight: 20,
  },
  computationNote: {
    fontSize: 10,
    marginTop: 12,
  },
  nameBreakdown: {
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
  },
  breakdownLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 8,
  },
  breakdownGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
  },
  breakdownItem: {
    alignItems: 'center',
    width: 28,
    paddingVertical: 4,
  },
  breakdownLetter: {
    fontSize: 12,
    fontWeight: '500',
  },
  breakdownValue: {
    fontSize: 10,
    marginTop: 2,
  },
  breakdownSpace: {
    width: 12,
  },

  // Tensions
  tensionItem: {
    flexDirection: 'row',
    marginBottom: 12,
    gap: 12,
  },
  tensionBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 6,
  },
  tensionContent: {
    flex: 1,
  },
  tensionBehavioral: {
    fontSize: 14,
    lineHeight: 22,
  },
  tensionLabel: {
    fontSize: 11,
    marginTop: 4,
  },

  // Ask Mirror
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1,
  },
  askMirrorText: {
    fontSize: 14,
    fontWeight: '500',
  },

  // Footer
  footer: {
    fontSize: 11,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 16,
  },
});
