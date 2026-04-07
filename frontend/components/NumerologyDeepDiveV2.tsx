/**
 * NumerologyDeepDiveV2.tsx
 * ========================
 * 
 * Upgraded Deep Dive aligned with Summary V2 architecture.
 * Uses the same hybrid numerology system (Pythagorean + Lo Shu).
 * 
 * Structure:
 * A. Pattern headline - Short, strong, numerology-specific
 * B. Why this pattern forms - Tied to computed numbers
 * C. How it shows up - Behavioral, real-life
 * D. What it costs - Where it breaks down
 * E. What needs to be built - Missing-number logic
 * F. Unified footer - Resonate + Reflect
 * 
 * COMPUTE ≠ SURFACED ≠ INTERPRETED
 */

import React, { useState, useEffect } from 'react';
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
  pattern_interrupt?: {
    trigger_conditions: string[];
    default_behavior: string[];
    interrupt_actions: string[];
    why_this_works: string;
    primary_driver: string;
    mechanism: string;
  };
}

interface Props {
  userId: string;
  onOpenChat: () => void;
  existingName?: string | null;
  onNameUpdated?: () => void;
}

// =============================================================================
// PATTERN CONTENT GENERATORS (Numerology-Specific)
// =============================================================================

// Life Path specific headlines and behaviors
const LIFE_PATH_PATTERNS: Record<number, {
  headline: string;
  why_forms: string;
  how_shows_up: string[];
  what_costs: string[];
  overuse_risk: string;
}> = {
  1: {
    headline: "The pattern of leading before consensus",
    why_forms: "Life Path 1 creates an instinct to initiate. You see direction before others do and move toward it—often alone.",
    how_shows_up: [
      "Starting projects before getting buy-in",
      "Making decisions while others are still deliberating",
      "Feeling frustrated when progress depends on collective agreement",
      "Taking charge in ambiguous situations without waiting",
    ],
    what_costs: [
      "People feel bypassed rather than included",
      "You carry more than your share because asking feels slow",
      "Collaboration becomes harder the more you lead alone",
    ],
    overuse_risk: "Independence becomes isolation. Strength becomes rigidity.",
  },
  2: {
    headline: "The pattern of sensing what isn't said",
    why_forms: "Life Path 2 creates an instinct to feel the field before acting. You register subtle dynamics others miss.",
    how_shows_up: [
      "Knowing when something is off before anyone says it",
      "Adjusting your tone based on unspoken signals",
      "Absorbing tension from the room without realizing",
      "Hesitating to act until harmony feels possible",
    ],
    what_costs: [
      "Your own needs get deprioritized for the group",
      "Over-accommodation masks your actual position",
      "You may know the truth but not voice it",
    ],
    overuse_risk: "Sensitivity becomes over-absorption. Peace-keeping becomes erasure.",
  },
  3: {
    headline: "The pattern of processing through expression",
    why_forms: "Life Path 3 creates an instinct to externalize inner experience. You know what you think by saying it.",
    how_shows_up: [
      "Talking through problems rather than sitting with them",
      "Using humor or storytelling to navigate tension",
      "Needing creative output to feel grounded",
      "Struggling with unexpressed emotion",
    ],
    what_costs: [
      "Words come faster than consideration",
      "Depth gets sacrificed for engagement",
      "Others may feel performed at rather than with",
    ],
    overuse_risk: "Expression becomes noise. Sharing becomes avoiding.",
  },
  4: {
    headline: "The pattern of building what lasts",
    why_forms: "Life Path 4 creates an instinct to construct stable foundations. You value what endures over what excites.",
    how_shows_up: [
      "Needing structure before you can move forward",
      "Feeling unsettled in unpredictable environments",
      "Repeating processes that have worked before",
      "Valuing effort and consistency over shortcuts",
    ],
    what_costs: [
      "Rigidity when flexibility is needed",
      "Resentment toward those who don't follow the plan",
      "Difficulty releasing systems that no longer serve",
    ],
    overuse_risk: "Stability becomes stagnation. Process becomes prison.",
  },
  5: {
    headline: "The pattern of seeking the next frontier",
    why_forms: "Life Path 5 creates an instinct for motion and variety. Routine signals stagnation to your system.",
    how_shows_up: [
      "Restlessness in stable environments",
      "Changing direction when things start working",
      "Craving novelty even when satisfied",
      "Difficulty sustaining what you've built",
    ],
    what_costs: [
      "Consistency suffers under the need for change",
      "Others may feel you're never fully there",
      "Depth gets sacrificed for breadth",
    ],
    overuse_risk: "Freedom becomes avoidance. Motion becomes running.",
  },
  6: {
    headline: "The pattern of taking responsibility uninvited",
    why_forms: "Life Path 6 creates an instinct to care for what's broken. You see what needs fixing and move toward it.",
    how_shows_up: [
      "Carrying burdens others didn't ask you to carry",
      "Feeling guilty when you prioritize yourself",
      "Attracting people who need help",
      "Believing your value comes from usefulness",
    ],
    what_costs: [
      "Your needs get delayed indefinitely",
      "Resentment builds when care isn't returned",
      "Others never learn to carry their own weight",
    ],
    overuse_risk: "Care becomes control. Giving becomes debt.",
  },
  7: {
    headline: "The pattern of knowing before proving",
    why_forms: "Life Path 7 creates an instinct to understand before committing. You need to see the logic beneath the surface.",
    how_shows_up: [
      "Analyzing situations others accept at face value",
      "Needing solitude to process",
      "Trusting internal logic over external validation",
      "Feeling disconnected from surface-level conversation",
    ],
    what_costs: [
      "Paralysis when analysis never ends",
      "Others feel judged or kept at distance",
      "Connection suffers when you can't articulate what you know",
    ],
    overuse_risk: "Insight becomes isolation. Knowing becomes withholding.",
  },
  8: {
    headline: "The pattern of tracking results and power",
    why_forms: "Life Path 8 creates an instinct to measure impact. You see how resources and influence flow.",
    how_shows_up: [
      "Evaluating situations by outcome potential",
      "Sensing power dynamics others miss",
      "Pushing for concrete results over abstract progress",
      "Feeling restless when achievement stalls",
    ],
    what_costs: [
      "Relationships become transactions",
      "Worth gets tied to external markers",
      "Vulnerability feels like weakness",
    ],
    overuse_risk: "Ambition becomes obsession. Strength becomes hardness.",
  },
  9: {
    headline: "The pattern of seeing the larger arc",
    why_forms: "Life Path 9 creates an instinct for completion and meaning. You sense how things end before they begin.",
    how_shows_up: [
      "Feeling called to let go of what others cling to",
      "Seeing cycles where others see straight lines",
      "Struggling with attachment to outcomes",
      "Carrying a sense of unfinished purpose",
    ],
    what_costs: [
      "The present gets lost in service to meaning",
      "Others may feel you're already elsewhere",
      "Endings become premature when patience runs out",
    ],
    overuse_risk: "Wisdom becomes detachment. Release becomes abandonment.",
  },
  11: {
    headline: "The pattern of receiving before it arrives",
    why_forms: "Life Path 11 carries the sensitivity of 2 amplified. You catch signals before they become visible.",
    how_shows_up: [
      "Knowing things you can't explain knowing",
      "Feeling overwhelmed by emotional environments",
      "Seeing potential others haven't imagined",
      "Struggling to ground vision into action",
    ],
    what_costs: [
      "High sensitivity creates high exhaustion",
      "Others don't see what you're responding to",
      "Visionary insight without practical traction",
    ],
    overuse_risk: "Intuition becomes anxiety. Vision becomes paralysis.",
  },
  22: {
    headline: "The pattern of building what others can't see yet",
    why_forms: "Life Path 22 carries the builder instinct of 4 at scale. You think in structures that span years.",
    how_shows_up: [
      "Thinking in long arcs while others plan quarters",
      "Feeling frustrated by small-scope execution",
      "Carrying responsibility for things not yet built",
      "Struggling when vision outpaces resources",
    ],
    what_costs: [
      "The gap between vision and reality creates chronic tension",
      "Others may feel you're impractical or demanding",
      "Patience gets tested when the timeline is decades",
    ],
    overuse_risk: "Ambition becomes burden. Building becomes compulsion.",
  },
  33: {
    headline: "The pattern of holding space for healing",
    why_forms: "Life Path 33 carries the care instinct of 6 at spiritual depth. You absorb what others carry.",
    how_shows_up: [
      "People confide in you without knowing why",
      "Feeling responsible for collective emotional weight",
      "Struggling to separate your needs from others'",
      "Sensing wounds before they're spoken",
    ],
    what_costs: [
      "Your own healing gets neglected",
      "Compassion fatigue without boundaries",
      "Others may lean on you without reciprocating",
    ],
    overuse_risk: "Healing becomes self-sacrifice. Compassion becomes depletion.",
  },
};

// Missing number deep dive content
const MISSING_NUMBER_DEEP_DIVE: Record<number, {
  what_must_be_built: string;
  how_to_build: string[];
  watch_for: string;
}> = {
  1: {
    what_must_be_built: "The capacity to initiate without external permission",
    how_to_build: [
      "Practice starting before you feel ready",
      "Notice when you defer to others unnecessarily",
      "Build confidence through small self-directed actions",
    ],
    watch_for: "Waiting for validation that won't arrive",
  },
  2: {
    what_must_be_built: "The capacity to translate inner knowing to others",
    how_to_build: [
      "Practice naming what you sense before assuming others see it",
      "Ask clarifying questions instead of assuming alignment",
      "Build bridges between your insight and others' understanding",
    ],
    watch_for: "Assuming connection without confirming it",
  },
  3: {
    what_must_be_built: "The capacity to express what you hold inside",
    how_to_build: [
      "Practice saying things before you've perfected them",
      "Find outlets for creative expression—any form",
      "Notice when you're holding back to avoid judgment",
    ],
    watch_for: "Insight that never makes it into words",
  },
  4: {
    what_must_be_built: "The capacity to sustain what you start",
    how_to_build: [
      "Build small daily routines and stick to them",
      "Practice finishing before starting something new",
      "Create structures that support long-term goals",
    ],
    watch_for: "Enthusiasm that fades when effort is required",
  },
  5: {
    what_must_be_built: "The capacity to adapt when plans fail",
    how_to_build: [
      "Practice changing direction without catastrophizing",
      "Build flexibility into your commitments",
      "Notice when rigidity creates unnecessary friction",
    ],
    watch_for: "Clinging to the plan when reality has shifted",
  },
  6: {
    what_must_be_built: "The capacity to care without owning outcomes",
    how_to_build: [
      "Practice offering help without attachment to acceptance",
      "Build awareness of when care becomes control",
      "Notice when you take responsibility that isn't yours",
    ],
    watch_for: "Helping that becomes obligation",
  },
  7: {
    what_must_be_built: "The capacity for deep reflection before action",
    how_to_build: [
      "Build space for solitude into your week",
      "Practice sitting with questions before seeking answers",
      "Notice when surface engagement replaces real understanding",
    ],
    watch_for: "Acting before you've understood",
  },
  8: {
    what_must_be_built: "The capacity to track and leverage resources",
    how_to_build: [
      "Practice measuring progress in concrete terms",
      "Build awareness of how power flows in your environment",
      "Notice when you avoid the material dimension",
    ],
    watch_for: "Ignoring results until consequences arrive",
  },
  9: {
    what_must_be_built: "The capacity to release what's complete",
    how_to_build: [
      "Practice letting go before you're forced to",
      "Build rituals for endings and transitions",
      "Notice when you're holding onto what's already over",
    ],
    watch_for: "Dragging the past into the present",
  },
};

// =============================================================================
// COMPONENT
// =============================================================================

export default function NumerologyDeepDiveV2({ userId, onOpenChat, existingName, onNameUpdated }: Props) {
  const { theme } = useTheme();
  const [data, setData] = useState<NumerologyCompute | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['pattern']));
  const [showNameModal, setShowNameModal] = useState(false);
  const [nameInput, setNameInput] = useState('');
  const [isSavingName, setIsSavingName] = useState(false);

  // Fetch compute data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await api.get(`/numerology/compute/${userId}`);
        setData(response.data);
      } catch (err: any) {
        console.error('[NumerologyDeepDiveV2] Error:', err);
        setError(err.response?.data?.detail || 'Failed to load pattern data');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [userId]);

  useEffect(() => {
    setNameInput(existingName || '');
  }, [existingName]);

  const handleSaveName = async () => {
    if (!nameInput.trim()) return;
    
    setIsSavingName(true);
    try {
      await api.post(`/numerology/unlock-name/${userId}`, {
        full_birth_name: nameInput.trim()
      });
      setShowNameModal(false);
      // Re-fetch data
      const response = await api.get(`/numerology/compute/${userId}`);
      setData(response.data);
      onNameUpdated?.();
    } catch (err) {
      console.error('[NumerologyDeepDiveV2] Save name error:', err);
    } finally {
      setIsSavingName(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
  };

  // Get pattern content based on life path
  const getPatternContent = () => {
    if (!data) return null;
    const lifePath = data.pythagorean.life_path;
    return LIFE_PATH_PATTERNS[lifePath] || LIFE_PATH_PATTERNS[lifePath % 9 || 9];
  };

  // =============================================================================
  // RENDER SECTIONS
  // =============================================================================

  const renderPatternHeadline = () => {
    const content = getPatternContent();
    if (!content) return null;

    return (
      <View style={[styles.card, styles.headlineCard, { backgroundColor: theme.surface, borderColor: theme.accent + '40' }]}>
        <View style={styles.lifePathBadge}>
          <Text style={[styles.lifePathLabel, { color: theme.textTertiary }]}>Life Path</Text>
          <Text style={[styles.lifePathNumber, { color: theme.accent }]}>{data?.pythagorean.life_path}</Text>
        </View>
        <Text style={[styles.headline, { color: theme.text }]}>{content.headline}</Text>
      </View>
    );
  };

  const renderWhyThisPatternForms = () => {
    const content = getPatternContent();
    if (!content || !data) return null;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('why')}
        >
          <Text style={[styles.sectionTitle, { color: theme.text }]}>WHY THIS PATTERN FORMS</Text>
          <Ionicons
            name={expandedSections.has('why') ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {expandedSections.has('why') && (
          <View style={styles.sectionContent}>
            <Text style={[styles.bodyText, { color: theme.textSecondary }]}>{content.why_forms}</Text>

            {/* Number contributions */}
            <View style={styles.numberContributions}>
              <View style={styles.contributionItem}>
                <Text style={[styles.contributionLabel, { color: theme.textTertiary }]}>Life Path {data.pythagorean.life_path}</Text>
                <Text style={[styles.contributionValue, { color: theme.text }]}>Core operating pattern</Text>
              </View>
              
              {data.pythagorean.expression && (
                <View style={styles.contributionItem}>
                  <Text style={[styles.contributionLabel, { color: theme.textTertiary }]}>Expression {data.pythagorean.expression}</Text>
                  <Text style={[styles.contributionValue, { color: theme.text }]}>How you present to others</Text>
                </View>
              )}
              
              {data.pythagorean.soul_urge && (
                <View style={styles.contributionItem}>
                  <Text style={[styles.contributionLabel, { color: theme.textTertiary }]}>Soul Urge {data.pythagorean.soul_urge}</Text>
                  <Text style={[styles.contributionValue, { color: theme.text }]}>What you internally crave</Text>
                </View>
              )}

              {data.lo_shu.missing_numbers.length > 0 && (
                <View style={styles.contributionItem}>
                  <Text style={[styles.contributionLabel, { color: theme.textTertiary }]}>
                    Not naturally available: {data.lo_shu.missing_numbers.slice(0, 3).join(', ')}
                  </Text>
                  <Text style={[styles.contributionValue, { color: theme.text }]}>Energies that require conscious effort</Text>
                </View>
              )}
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderHowItShowsUp = () => {
    const content = getPatternContent();
    if (!content) return null;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('shows')}
        >
          <Text style={[styles.sectionTitle, { color: theme.text }]}>HOW IT SHOWS UP</Text>
          <Ionicons
            name={expandedSections.has('shows') ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {expandedSections.has('shows') && (
          <View style={styles.sectionContent}>
            {content.how_shows_up.map((item, index) => (
              <View key={index} style={styles.bulletItem}>
                <View style={[styles.bullet, { backgroundColor: theme.accent }]} />
                <Text style={[styles.bulletText, { color: theme.text }]}>{item}</Text>
              </View>
            ))}
          </View>
        )}
      </View>
    );
  };

  const renderPatternInterrupt = () => {
    if (!data?.pattern_interrupt) return null;

    const { trigger_conditions, default_behavior, interrupt_actions, why_this_works, mechanism } = data.pattern_interrupt;

    return (
      <View style={[styles.card, styles.interruptCard, { backgroundColor: theme.surface, borderColor: theme.accent + '40' }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('interrupt')}
        >
          <View style={styles.interruptHeader}>
            <Ionicons name="flash" size={16} color={theme.accent} />
            <Text style={[styles.sectionTitle, { color: theme.text, marginLeft: 8 }]}>WHEN THIS PATTERN TRIGGERS</Text>
          </View>
          <Ionicons
            name={expandedSections.has('interrupt') ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {expandedSections.has('interrupt') && (
          <View style={styles.sectionContent}>
            {/* Trigger Conditions */}
            <View style={styles.interruptSection}>
              <Text style={[styles.interruptLabel, { color: theme.textTertiary }]}>TRIGGER CONDITIONS</Text>
              {trigger_conditions.map((trigger, index) => (
                <View key={index} style={styles.bulletItem}>
                  <View style={[styles.bullet, { backgroundColor: theme.accent }]} />
                  <Text style={[styles.bulletText, { color: theme.text }]}>{trigger}</Text>
                </View>
              ))}
            </View>

            {/* Default Behavior */}
            <View style={styles.interruptSection}>
              <Text style={[styles.interruptLabel, { color: theme.textTertiary }]}>DEFAULT BEHAVIOR</Text>
              {default_behavior.map((behavior, index) => (
                <View key={index} style={styles.bulletItem}>
                  <View style={[styles.bullet, { backgroundColor: '#FFB74D' }]} />
                  <Text style={[styles.bulletText, { color: theme.textSecondary }]}>{behavior}</Text>
                </View>
              ))}
            </View>

            {/* THE INTERRUPT - Key Block */}
            <View style={[styles.interruptBlock, { backgroundColor: theme.accent + '10', borderColor: theme.accent + '30' }]}>
              <View style={styles.interruptBlockHeader}>
                <Ionicons name="hand-left" size={18} color={theme.accent} />
                <Text style={[styles.interruptBlockTitle, { color: theme.accent }]}>THE INTERRUPT</Text>
              </View>
              <Text style={[styles.interruptBlockSubtitle, { color: theme.textSecondary }]}>
                Under 30 seconds • In the moment
              </Text>
              {interrupt_actions.map((action, index) => (
                <View key={index} style={styles.interruptAction}>
                  <Text style={[styles.interruptActionNumber, { color: theme.accent }]}>{index + 1}</Text>
                  <Text style={[styles.interruptActionText, { color: theme.text }]}>{action}</Text>
                </View>
              ))}
            </View>

            {/* WHY THIS WORKS */}
            <View style={styles.whyWorksSection}>
              <Text style={[styles.whyWorksLabel, { color: theme.textTertiary }]}>WHY THIS WORKS</Text>
              <Text style={[styles.whyWorksText, { color: theme.textSecondary }]}>{why_this_works}</Text>
              <View style={styles.mechanismBadge}>
                <Text style={[styles.mechanismText, { color: theme.textTertiary }]}>
                  Addressing: {mechanism}
                </Text>
              </View>
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderWhatItCosts = () => {
    const content = getPatternContent();
    if (!content) return null;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('costs')}
        >
          <Text style={[styles.sectionTitle, { color: theme.text }]}>WHAT IT COSTS</Text>
          <Ionicons
            name={expandedSections.has('costs') ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {expandedSections.has('costs') && (
          <View style={styles.sectionContent}>
            {content.what_costs.map((item, index) => (
              <View key={index} style={styles.bulletItem}>
                <View style={[styles.bullet, { backgroundColor: '#E57373' }]} />
                <Text style={[styles.bulletText, { color: theme.text }]}>{item}</Text>
              </View>
            ))}

            <View style={[styles.warningBox, { backgroundColor: 'rgba(229, 115, 115, 0.08)', borderColor: 'rgba(229, 115, 115, 0.2)' }]}>
              <Text style={[styles.warningLabel, { color: '#E57373' }]}>OVERUSE RISK</Text>
              <Text style={[styles.warningText, { color: theme.text }]}>{content.overuse_risk}</Text>
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderWhatNeedsToBeBuilt = () => {
    if (!data || data.lo_shu.missing_numbers.length === 0) return null;

    // Get content for top 2 missing numbers
    const missingToShow = data.lo_shu.missing_numbers.slice(0, 2);

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('build')}
        >
          <Text style={[styles.sectionTitle, { color: theme.text }]}>WHAT NEEDS TO BE BUILT</Text>
          <Ionicons
            name={expandedSections.has('build') ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {expandedSections.has('build') && (
          <View style={styles.sectionContent}>
            <Text style={[styles.helperText, { color: theme.textSecondary }]}>
              These numbers are absent from your birth date. The energies they represent don't come automatically—they must be developed through conscious effort.
            </Text>

            {missingToShow.map((num) => {
              const content = MISSING_NUMBER_DEEP_DIVE[num];
              if (!content) return null;

              return (
                <View key={num} style={[styles.buildItem, { borderColor: theme.border }]}>
                  <View style={styles.buildHeader}>
                    <View style={[styles.missingBadge, { backgroundColor: theme.accent + '20' }]}>
                      <Text style={[styles.missingNumber, { color: theme.accent }]}>{num}</Text>
                    </View>
                    <Text style={[styles.buildTitle, { color: theme.text }]}>{content.what_must_be_built}</Text>
                  </View>

                  <Text style={[styles.buildSubtitle, { color: theme.textTertiary }]}>How to build it:</Text>
                  {content.how_to_build.map((item, index) => (
                    <View key={index} style={styles.buildBulletItem}>
                      <Text style={[styles.buildBulletText, { color: theme.textSecondary }]}>• {item}</Text>
                    </View>
                  ))}

                  <View style={[styles.watchForBox, { backgroundColor: theme.background }]}>
                    <Text style={[styles.watchForLabel, { color: theme.textTertiary }]}>Watch for:</Text>
                    <Text style={[styles.watchForText, { color: theme.text }]}>{content.watch_for}</Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </View>
    );
  };

  const renderLoShuGrid = () => {
    if (!data) return null;

    const { grid, missing_numbers, present_numbers, digit_counts } = data.lo_shu;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('loshu')}
        >
          <Text style={[styles.sectionTitle, { color: theme.text }]}>ENERGY MAP (Lo Shu Grid)</Text>
          <Ionicons
            name={expandedSections.has('loshu') ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {expandedSections.has('loshu') && (
          <View style={styles.sectionContent}>
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

            <View style={styles.gridLegend}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: theme.accent }]} />
                <Text style={[styles.legendText, { color: theme.textSecondary }]}>Naturally present: {present_numbers.join(', ')}</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: theme.textTertiary }]} />
                <Text style={[styles.legendText, { color: theme.textSecondary }]}>Not naturally available: {missing_numbers.join(', ')}</Text>
              </View>
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderComputationBasis = () => {
    if (!data) return null;

    return (
      <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection('computation')}
        >
          <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>What this is based on</Text>
          <Ionicons
            name={expandedSections.has('computation') ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={theme.textTertiary}
          />
        </TouchableOpacity>

        {expandedSections.has('computation') && (
          <View style={styles.sectionContent}>
            <Text style={[styles.computationNote, { color: theme.textTertiary }]}>
              This is a hybrid numerology lens combining two systems:
            </Text>
            <View style={styles.computationItem}>
              <Text style={[styles.computationLabel, { color: theme.text }]}>Pythagorean (Western)</Text>
              <Text style={[styles.computationValue, { color: theme.textSecondary }]}>
                Full name → letter-to-number mapping → Expression, Soul Urge, Personality
              </Text>
            </View>
            <View style={styles.computationItem}>
              <Text style={[styles.computationLabel, { color: theme.text }]}>Lo Shu Grid (birth-date distribution)</Text>
              <Text style={[styles.computationValue, { color: theme.textSecondary }]}>
                Birth date digits → Energy Map (naturally present / not naturally available)
              </Text>
            </View>

            {data.input.full_name && (
              <View style={styles.inputDisplay}>
                <Text style={[styles.inputLabel, { color: theme.textTertiary }]}>Name used:</Text>
                <Text style={[styles.inputValue, { color: theme.text }]}>{data.input.full_name}</Text>
              </View>
            )}
            <View style={styles.inputDisplay}>
              <Text style={[styles.inputLabel, { color: theme.textTertiary }]}>Birth date:</Text>
              <Text style={[styles.inputValue, { color: theme.text }]}>{data.input.birth_date}</Text>
            </View>
          </View>
        )}
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
          Building your pattern system...
        </Text>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={[styles.errorContainer, { backgroundColor: theme.background }]}>
        <Ionicons name="alert-circle-outline" size={32} color={theme.textTertiary} />
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error || 'Unable to load pattern data'}</Text>
        <TouchableOpacity
          style={[styles.retryButton, { backgroundColor: theme.surface }]}
          onPress={() => {
            setError(null);
            setIsLoading(true);
            api.get(`/numerology/compute/${userId}`)
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
      {/* A. Pattern Headline */}
      {renderPatternHeadline()}

      {/* B. Why This Pattern Forms */}
      {renderWhyThisPatternForms()}

      {/* C. How It Shows Up */}
      {renderHowItShowsUp()}

      {/* NEW: When This Pattern Triggers - Pattern Interrupt Layer */}
      {renderPatternInterrupt()}

      {/* D. What It Costs */}
      {renderWhatItCosts()}

      {/* E. What Needs To Be Built */}
      {renderWhatNeedsToBeBuilt()}

      {/* Energy Map (Lo Shu) */}
      {renderLoShuGrid()}

      {/* Computation Basis */}
      {renderComputationBasis()}

      {/* Unified Footer */}
      <InsightCardFooter
        source={{
          lens: 'numerology',
          type: 'deep_dive',
          name: `Life Path ${data.pythagorean.life_path} Pattern`,
          value: getPatternContent()?.headline || '',
          id: `numerology_deep_dive_${userId}`,
        }}
        patternSignature={`numerology_deep_dive_${userId}`}
        context="numerology_deep_dive"
        prompt={getPatternContent()?.headline || 'Reflect on this pattern'}
        showBorder={true}
        borderColor={theme.border}
      />

      {/* Add Name Link */}
      {!data.input.full_name && (
        <TouchableOpacity
          style={[styles.addNameLink, { borderColor: theme.border }]}
          onPress={() => setShowNameModal(true)}
        >
          <Ionicons name="add-circle-outline" size={16} color={theme.textTertiary} />
          <Text style={[styles.addNameText, { color: theme.textTertiary }]}>
            Add birth name for identity numbers
          </Text>
        </TouchableOpacity>
      )}

      {/* Secondary Action: Ask about pattern */}
      <TouchableOpacity
        style={[styles.secondaryAction, { backgroundColor: theme.surfaceLight, borderColor: theme.border }]}
        onPress={onOpenChat}
      >
        <Ionicons name="chatbubble-outline" size={18} color={theme.textSecondary} />
        <Text style={[styles.secondaryActionText, { color: theme.textSecondary }]}>
          Ask about this pattern
        </Text>
      </TouchableOpacity>

      {/* Footer */}
      <Text style={[styles.footer, { color: theme.textTertiary }]}>
        Pattern notation, not identity. A lens for noticing, not a truth to follow.
      </Text>

      {/* Name Modal - Fixed for mobile web */}
      <Modal
        visible={showNameModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowNameModal(false)}
        statusBarTranslucent={true}
      >
        {/* Overlay backdrop - tappable to close */}
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={() => setShowNameModal(false)}
        >
          {/* Prevent touches on modal content from closing */}
          <TouchableOpacity 
            activeOpacity={1} 
            onPress={(e) => e.stopPropagation()}
            style={{ width: '100%' }}
          >
            <KeyboardAvoidingView
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
              style={styles.keyboardAvoidingContainer}
            >
              <View style={[styles.modalContainer, { backgroundColor: theme.surface }]}>
                <TouchableOpacity
                  style={styles.modalCloseButton}
                  onPress={() => setShowNameModal(false)}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                  <Ionicons name="close" size={24} color={theme.textSecondary} />
                </TouchableOpacity>

                {/* Scrollable content area */}
                <ScrollView 
                  style={styles.modalScrollContent}
                  contentContainerStyle={styles.modalScrollContentContainer}
                  showsVerticalScrollIndicator={false}
                  keyboardShouldPersistTaps="handled"
                  bounces={false}
                >
                  <Text style={[styles.modalTitle, { color: theme.text }]}>
                    Your Full Birth Name
                  </Text>
                  <Text style={[styles.modalSubtitle, { color: theme.textTertiary }]}>
                    As given at birth — used for Pythagorean calculation
                  </Text>

                  <TextInput
                    style={[styles.nameInput, { color: theme.text, borderColor: theme.border, backgroundColor: theme.background }]}
                    placeholder="e.g., John Michael Smith"
                    placeholderTextColor={theme.textTertiary}
                    value={nameInput}
                    onChangeText={setNameInput}
                    autoCapitalize="words"
                    autoCorrect={false}
                    autoFocus={Platform.OS !== 'web'}
                    returnKeyType="done"
                    blurOnSubmit={true}
                    onSubmitEditing={handleSaveName}
                  />
                </ScrollView>

                {/* STICKY ACTION BUTTONS - Always visible at bottom */}
                <View style={[styles.modalActionsSticky, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>
                  <TouchableOpacity
                    style={[styles.modalSecondaryButton, { backgroundColor: theme.background }]}
                    onPress={() => setShowNameModal(false)}
                  >
                    <Text style={[styles.modalSecondaryButtonText, { color: theme.text }]}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.modalPrimaryButton, { backgroundColor: theme.accent }]}
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
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>
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
    gap: 12,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
    padding: 40,
  },
  loadingText: {
    fontSize: 14,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
    padding: 40,
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
    overflow: 'hidden',
  },
  headlineCard: {
    padding: 20,
    borderLeftWidth: 3,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  sectionContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 12,
  },

  // Headline
  lifePathBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  lifePathLabel: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  lifePathNumber: {
    fontSize: 24,
    fontWeight: '700',
  },
  headline: {
    fontSize: 18,
    fontWeight: '600',
    lineHeight: 26,
  },

  // Body
  bodyText: {
    fontSize: 14,
    lineHeight: 22,
  },
  helperText: {
    fontSize: 13,
    lineHeight: 20,
  },

  // Bullets
  bulletItem: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 8,
  },
  bullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
  },
  bulletText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 22,
  },

  // Number contributions
  numberContributions: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
    gap: 10,
  },
  contributionItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  contributionLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  contributionValue: {
    fontSize: 12,
    flex: 1,
    textAlign: 'right',
    marginLeft: 16,
  },

  // Warning box
  warningBox: {
    marginTop: 12,
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
  },
  warningLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  warningText: {
    fontSize: 13,
    lineHeight: 20,
  },

  // Build section
  buildItem: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
  },
  buildHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  missingBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  missingNumber: {
    fontSize: 16,
    fontWeight: '700',
  },
  buildTitle: {
    flex: 1,
    fontSize: 14,
    fontWeight: '500',
    lineHeight: 20,
  },
  buildSubtitle: {
    fontSize: 11,
    fontWeight: '600',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  buildBulletItem: {
    marginBottom: 6,
  },
  buildBulletText: {
    fontSize: 13,
    lineHeight: 20,
  },
  watchForBox: {
    marginTop: 12,
    padding: 10,
    borderRadius: 6,
  },
  watchForLabel: {
    fontSize: 10,
    fontWeight: '600',
    marginBottom: 4,
  },
  watchForText: {
    fontSize: 13,
    lineHeight: 18,
  },

  // Grid
  gridContainer: {
    alignItems: 'center',
    marginBottom: 12,
  },
  gridRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  gridCell: {
    width: 56,
    height: 56,
    borderRadius: 8,
    borderWidth: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  gridNumber: {
    fontSize: 22,
    fontWeight: '700',
  },
  gridCount: {
    fontSize: 10,
    marginTop: 2,
  },
  gridEmpty: {
    fontSize: 18,
  },
  gridLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 24,
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

  // Computation
  computationNote: {
    fontSize: 12,
    marginBottom: 12,
    fontStyle: 'italic',
  },
  computationItem: {
    marginBottom: 12,
  },
  computationLabel: {
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 4,
  },
  computationValue: {
    fontSize: 12,
    lineHeight: 18,
  },
  inputDisplay: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 8,
  },
  inputLabel: {
    fontSize: 12,
  },
  inputValue: {
    fontSize: 12,
    fontWeight: '500',
  },

  // Add name
  addNameLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderWidth: 1,
    borderRadius: 8,
    borderStyle: 'dashed',
  },
  addNameText: {
    fontSize: 13,
  },

  // Secondary action
  secondaryAction: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1,
  },
  secondaryActionText: {
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

  // Modal - Fixed for mobile web
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'flex-end',
  },
  keyboardAvoidingContainer: {
    width: '100%',
    maxHeight: '90%',
  },
  modalContainer: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 24,
    paddingHorizontal: 24,
    paddingBottom: 24,
    maxHeight: '100%',
    minHeight: 280,
  },
  modalScrollContent: {
    flexGrow: 0,
    flexShrink: 1,
    maxHeight: 180,
  },
  modalScrollContentContainer: {
    paddingBottom: 16,
  },
  modalCloseButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    padding: 8,
    zIndex: 1,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 8,
    marginTop: 8,
  },
  modalSubtitle: {
    fontSize: 14,
    marginBottom: 24,
  },
  nameInput: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 14,
    fontSize: 16,
    marginBottom: 24,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalActionsSticky: {
    flexDirection: 'row',
    gap: 12,
    paddingTop: 16,
    borderTopWidth: 1,
    marginTop: 8,
  },
  modalSecondaryButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  modalSecondaryButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  modalPrimaryButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 48,
  },
  modalPrimaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },

  // Pattern Interrupt Styles
  interruptCard: {
    borderLeftWidth: 3,
  },
  interruptHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  interruptSection: {
    marginBottom: 16,
  },
  interruptLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 10,
  },
  interruptBlock: {
    padding: 16,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 16,
  },
  interruptBlockHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  interruptBlockTitle: {
    fontSize: 13,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  interruptBlockSubtitle: {
    fontSize: 11,
    marginBottom: 14,
  },
  interruptAction: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 10,
  },
  interruptActionNumber: {
    fontSize: 14,
    fontWeight: '700',
    width: 20,
  },
  interruptActionText: {
    flex: 1,
    fontSize: 14,
    lineHeight: 21,
  },
  whyWorksSection: {
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(128, 128, 128, 0.2)',
  },
  whyWorksLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  whyWorksText: {
    fontSize: 13,
    lineHeight: 20,
    marginBottom: 8,
  },
  mechanismBadge: {
    marginTop: 4,
  },
  mechanismText: {
    fontSize: 11,
    fontStyle: 'italic',
  },
});
