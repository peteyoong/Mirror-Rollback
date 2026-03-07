import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';
import { 
  formatSequenceExplanation, 
  getArcDescription, 
  getGateTheme,
  SEQUENCE_ROLES 
} from '../utils/humanDesignContext';

interface HumanDesignSection {
  label: string;
  body: string;
}

// Gene Keys sequence position
interface GeneKeyPosition {
  gate: number;
  line: number;
  source_planet: string;
  source_chart: 'personality' | 'design';
  // Optional UI-layer fields (not from compute)
  theme_label?: string;
  reflection_prompt?: string;
}

// Gene Keys data structure
interface GeneKeysData {
  gene_keys_version: string;
  purpose_arc: {
    lifes_work: GeneKeyPosition;
    evolution: GeneKeyPosition;
    radiance: GeneKeyPosition;
    purpose: GeneKeyPosition;
  };
  love_arc: {
    attraction: GeneKeyPosition;
    iq: GeneKeyPosition;
    eq: GeneKeyPosition;
    sq: GeneKeyPosition;
    core_wound: GeneKeyPosition;
  };
  prosperity_arc: {
    brand: GeneKeyPosition;
    culture: GeneKeyPosition;
    vocation: GeneKeyPosition;
    pearl: GeneKeyPosition;
  };
}

interface HumanDesignData {
  title: string;
  sections: HumanDesignSection[];
  mirror_prompt: string;
  core_mechanics?: {
    type: string;
    strategy: string;
    authority: string;
    profile?: string;
    definition?: string;
    incarnation_cross?: string;
    incarnation_cross_gates?: string;
  };
  // Gene Keys sequences (deterministic compute)
  gene_keys?: GeneKeysData | null;
  date?: string;
  // Version fields from backend (frozen compute)
  computation_version?: string;
  astronomy_version?: string;
  human_design_version?: string;
  // Debug fields from API
  debug_stamp?: {
    fallback_used?: boolean;
    source?: string;
    timestamp?: string;
    cached?: boolean;
  };
}

interface Props {
  userId: string;
  onOpenChat: () => void;
}

type TabType = 'summary' | 'today' | 'deep_dive';

export default function HumanDesignLensView({ userId, onOpenChat }: Props) {
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [data, setData] = useState<HumanDesignData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  
  // Gene Keys expansion state
  const [geneKeysExpanded, setGeneKeysExpanded] = useState(false);
  const [expandedArc, setExpandedArc] = useState<string | null>(null);
  
  // View mode toggle: 'everyday' or 'technical'
  const [sequenceViewMode, setSequenceViewMode] = useState<'everyday' | 'technical'>('everyday');
  
  // Debug: track raw API response length
  const [rawDataLength, setRawDataLength] = useState<number>(0);

  useEffect(() => {
    loadTabData(activeTab);
  }, [activeTab, userId]);

  const loadTabData = async (tab: TabType) => {
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = tab === 'today' 
        ? `/human-design/today/${userId}`
        : tab === 'deep_dive'
        ? `/human-design/deep-dive/${userId}`
        : `/human-design/summary/${userId}`;

      const response = await api.get(endpoint);
      setData(response.data);
      
      // Debug: Calculate raw data length for comparison
      if (isDebugEnabled() && response.data?.sections) {
        const totalChars = response.data.sections.reduce(
          (sum: number, s: HumanDesignSection) => sum + (s.body?.length || 0), 
          0
        );
        setRawDataLength(totalChars);
        console.log(`[DEBUG_MIRROR] HumanDesign ${tab}: API returned ${totalChars} chars across ${response.data.sections.length} sections`);
      }
    } catch (err: any) {
      console.error(`Human Design ${tab} error:`, err);
      setError('Unable to load this view right now.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, activeTab === 'summary' && styles.activeTabText]}>
          Summary
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'today' && styles.activeTab]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, activeTab === 'today' && styles.activeTabText]}>
          Today's Snapshot
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, activeTab === 'deep_dive' && styles.activeTabText]}>
          Deep Dive
        </Text>
      </TouchableOpacity>
    </View>
  );

  // Always render core mechanics for deep dive, even with fallback values
  const renderCoreMechanics = () => {
    // Default fallback if no data
    const mechanics = data?.core_mechanics || {
      type: 'Unknown',
      strategy: 'Unknown',
      authority: 'Unknown',
      profile: 'Unknown',
      definition: 'Unknown',
      incarnation_cross: 'Unknown',
      incarnation_cross_gates: null
    };

    // Helper to format unknown gracefully - DO NOT TRANSFORM canonical labels
    const formatMechanic = (value: string | undefined | null) => {
      if (!value || value === 'Unknown') return '—';
      // Display canonical label exactly as received from backend
      return value;
    };

    // Format incarnation cross - show the full name
    const formatCross = () => {
      if (!mechanics.incarnation_cross || mechanics.incarnation_cross === 'Unknown') {
        return '—';
      }
      // If it's a numbered cross like "Right Angle Cross of 37/40", extract just the type
      // If it's a named cross like "Right Angle Cross of Migration", show the full name
      const numbered = /\s*of\s*\d+\/\d+/;
      if (numbered.test(mechanics.incarnation_cross)) {
        // It's still numbered (old format) - just show the cross type
        return mechanics.incarnation_cross.replace(/\s*of\s*\d+\/\d+.*$/, '').trim();
      }
      // It's a named cross - show it fully (e.g., "Right Angle Cross of Migration")
      return mechanics.incarnation_cross;
    };

    const getCrossGates = () => {
      return mechanics.incarnation_cross_gates || '—';
    };

    return (
      <View style={styles.coreMechanicsCard}>
        <Text style={styles.coreMechanicsTitle}>CORE MECHANICS</Text>
        
        {/* Row 1: Type + Authority */}
        <View style={styles.mechanicsGrid}>
          <View style={styles.mechanicItem}>
            <Ionicons name="flash-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Type</Text>
            <Text style={styles.mechanicValue}>{formatMechanic(mechanics.type)}</Text>
          </View>
          <View style={styles.mechanicDivider} />
          <View style={styles.mechanicItem}>
            <Ionicons name="compass-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Authority</Text>
            <Text style={styles.mechanicValue}>{formatMechanic(mechanics.authority)}</Text>
          </View>
        </View>
        
        {/* Row 2: Profile + Definition */}
        <View style={[styles.mechanicsGrid, { marginTop: 16 }]}>
          <View style={styles.mechanicItem}>
            <Ionicons name="person-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Profile</Text>
            <Text style={styles.mechanicValue}>{mechanics.profile || '—'}</Text>
          </View>
          <View style={styles.mechanicDivider} />
          <View style={styles.mechanicItem}>
            <Ionicons name="layers-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Definition</Text>
            <Text style={styles.mechanicValue}>{formatMechanic(mechanics.definition)}</Text>
          </View>
        </View>
        
        {/* Row 3: Incarnation Cross */}
        <View style={[styles.mechanicsGrid, { marginTop: 16 }]}>
          <View style={[styles.mechanicItem, { flex: 1 }]}>
            <Ionicons name="git-branch-outline" size={16} color={Colors.accent} />
            <Text style={styles.mechanicLabel}>Incarnation Cross</Text>
            <Text style={[styles.mechanicValue, styles.mechanicValueSmall]}>{formatCross()}</Text>
            <Text style={styles.mechanicGates}>{getCrossGates()}</Text>
          </View>
        </View>
      </View>
    );
  };

  // Render version debug panel (only in dev mode)
  const renderVersionDebug = () => {
    if (!isDebugEnabled() || !data) return null;
    
    return (
      <View style={styles.versionDebugCard}>
        <Text style={styles.versionDebugTitle}>COMPUTE VERSIONS (DEV)</Text>
        <View style={styles.versionDebugRow}>
          <Text style={styles.versionDebugLabel}>computation:</Text>
          <Text style={styles.versionDebugValue}>{data.computation_version || '—'}</Text>
        </View>
        <View style={styles.versionDebugRow}>
          <Text style={styles.versionDebugLabel}>astronomy:</Text>
          <Text style={styles.versionDebugValue}>{data.astronomy_version || '—'}</Text>
        </View>
        <View style={styles.versionDebugRow}>
          <Text style={styles.versionDebugLabel}>human_design:</Text>
          <Text style={styles.versionDebugValue}>{data.human_design_version || '—'}</Text>
        </View>
      </View>
    );
  };

  // Render a single Gene Key sphere position with context
  const renderGeneKeySphere = (name: string, position: GeneKeyPosition) => {
    const chartLabel = position.source_chart === 'personality' ? 'Conscious' : 'Unconscious';
    const explanation = formatSequenceExplanation(name, position.gate, position.line);
    const gateTheme = getGateTheme(position.gate);
    
    // Technical view: show raw values prominently
    if (sequenceViewMode === 'technical') {
      return (
        <View key={name} style={styles.gkSphereItemTechnical}>
          <View style={styles.gkSphereLeft}>
            <Text style={styles.gkSphereName}>{explanation.title}</Text>
          </View>
          <View style={styles.gkSphereRight}>
            <Text style={styles.gkGateLine}>
              {position.gate}.{position.line}
            </Text>
            <Text style={styles.gkSource}>
              {position.source_planet} • {chartLabel}
            </Text>
          </View>
        </View>
      );
    }
    
    // Everyday language view: editorial, spacious layout
    return (
      <View key={name} style={styles.gkSphereItemExpanded}>
        {/* Sphere Title - emphasized */}
        <Text style={styles.gkSphereTitle}>{explanation.title}</Text>
        
        {/* Theme Label */}
        <Text style={styles.gkSphereTheme}>{explanation.themeLabel}</Text>
        
        {/* Description */}
        <Text style={styles.gkSphereDescription}>{explanation.description}</Text>
        
        {/* Reflection Prompt - visually separated */}
        {explanation.reflectionPrompt && (
          <View style={styles.gkReflectionContainer}>
            <View style={styles.gkReflectionDivider} />
            <Text style={styles.gkSpherePrompt}>{explanation.reflectionPrompt}</Text>
          </View>
        )}
        
        {/* Technical value - secondary, subtle */}
        <Text style={styles.gkSphereTechnical}>{explanation.technicalValue}</Text>
      </View>
    );
  };

  // Format sphere name from snake_case to Title Case
  const formatSphereName = (name: string): string => {
    // Special cases for better readability
    const specialNames: Record<string, string> = {
      'lifes_work': "Life's Work",
      'iq': 'IQ',
      'eq': 'EQ', 
      'sq': 'SQ',
      'core_wound': 'Core Wound',
    };
    if (specialNames[name]) return specialNames[name];
    
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Render view mode toggle
  const renderViewModeToggle = () => {
    return (
      <View style={styles.viewModeToggle}>
        <TouchableOpacity
          style={[
            styles.viewModeButton,
            sequenceViewMode === 'everyday' && styles.viewModeButtonActive
          ]}
          onPress={() => setSequenceViewMode('everyday')}
          activeOpacity={0.7}
        >
          <Text style={[
            styles.viewModeText,
            sequenceViewMode === 'everyday' && styles.viewModeTextActive
          ]}>Everyday language</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.viewModeButton,
            sequenceViewMode === 'technical' && styles.viewModeButtonActive
          ]}
          onPress={() => setSequenceViewMode('technical')}
          activeOpacity={0.7}
        >
          <Text style={[
            styles.viewModeText,
            sequenceViewMode === 'technical' && styles.viewModeTextActive
          ]}>Technical view</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Render Gene Keys Arc card with collapse/expand
  const renderGeneKeysArc = (
    arcName: string, 
    arcKey: string,
    arcData: Record<string, GeneKeyPosition> | undefined,
    icon: keyof typeof Ionicons.glyphMap,
    subtitle: string
  ) => {
    if (!arcData) return null;
    
    const isExpanded = expandedArc === arcKey;
    const sphereCount = Object.keys(arcData).length;
    const arcDescription = getArcDescription(arcKey);
    
    return (
      <View style={styles.gkArcCard}>
        <TouchableOpacity
          style={styles.gkArcHeader}
          onPress={() => setExpandedArc(isExpanded ? null : arcKey)}
          activeOpacity={0.7}
        >
          <View style={styles.gkArcHeaderLeft}>
            <Ionicons name={icon} size={18} color={Colors.accent} />
            <View>
              <Text style={styles.gkArcTitle}>{arcDescription.title || arcName}</Text>
              <Text style={styles.gkArcSubtitle}>
                {sequenceViewMode === 'everyday' ? arcDescription.description : subtitle}
              </Text>
            </View>
          </View>
          <View style={styles.gkArcHeaderRight}>
            <Text style={styles.gkArcCount}>{sphereCount} spheres</Text>
            <Ionicons
              name={isExpanded ? 'chevron-up' : 'chevron-down'}
              size={18}
              color={Colors.textTertiary}
            />
          </View>
        </TouchableOpacity>
        {isExpanded && (
          <View style={styles.gkArcContent}>
            {sequenceViewMode === 'everyday' && arcDescription.helperText && (
              <Text style={styles.gkArcHelper}>{arcDescription.helperText}</Text>
            )}
            {Object.entries(arcData).map(([name, position]) => 
              renderGeneKeySphere(name, position)
            )}
          </View>
        )}
      </View>
    );
  };

  // Render all Gene Keys sequences with section header
  const renderGeneKeys = () => {
    if (!data?.gene_keys) return null;
    
    const gk = data.gene_keys;
    
    return (
      <View style={styles.gkContainer}>
        {/* Section Divider */}
        <View style={styles.gkDivider}>
          <View style={styles.gkDividerLine} />
          <Text style={styles.gkDividerText}>YOUR SEQUENCES</Text>
          <View style={styles.gkDividerLine} />
        </View>
        
        {/* Helper Text */}
        <Text style={styles.gkHelperText}>
          These sequences are derived from your Human Design chart and translated here into everyday language.
        </Text>
        
        {/* View Mode Toggle */}
        {renderViewModeToggle()}
        
        {/* Section Header */}
        <TouchableOpacity
          style={styles.gkSectionHeader}
          onPress={() => setGeneKeysExpanded(!geneKeysExpanded)}
          activeOpacity={0.7}
        >
          <View style={styles.gkSectionHeaderLeft}>
            <Ionicons name="key-outline" size={20} color={Colors.accent} />
            <View>
              <Text style={styles.gkSectionTitle}>Explore Your Sequences</Text>
              <Text style={styles.gkSectionSubtitle}>
                {sequenceViewMode === 'everyday' 
                  ? 'Tap to see themes and meanings'
                  : 'Tap to see gate and line values'}
              </Text>
            </View>
          </View>
          <Ionicons
            name={geneKeysExpanded ? 'chevron-up' : 'chevron-down'}
            size={20}
            color={Colors.textTertiary}
          />
        </TouchableOpacity>
        
        {/* Arc Cards */}
        {geneKeysExpanded && (
          <View style={styles.gkArcsContainer}>
            {renderGeneKeysArc('Purpose', 'purpose', gk.purpose_arc, 'compass-outline', 'Your life direction')}
            {renderGeneKeysArc('Love', 'love', gk.love_arc, 'heart-outline', 'Relationships & relating')}
            {renderGeneKeysArc('Prosperity', 'prosperity', gk.prosperity_arc, 'diamond-outline', 'Abundance & vocation')}
            
            {isDebugEnabled() && (
              <Text style={styles.gkVersion}>v: {gk.gene_keys_version}</Text>
            )}
          </View>
        )}
      </View>
    );
  };

  const renderSection = (section: HumanDesignSection, index: number) => {
    const isExpanded = expandedSection === section.label || activeTab !== 'deep_dive';

    return (
      <View key={index} style={styles.sectionCard}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => {
            if (activeTab === 'deep_dive') {
              setExpandedSection(expandedSection === section.label ? null : section.label);
            }
          }}
          activeOpacity={activeTab === 'deep_dive' ? 0.7 : 1}
        >
          <Text style={styles.sectionLabel}>{section.label}</Text>
          {activeTab === 'deep_dive' && (
            <Ionicons
              name={isExpanded ? 'chevron-up' : 'chevron-down'}
              size={18}
              color={Colors.textTertiary}
            />
          )}
        </TouchableOpacity>
        {isExpanded && (
          <>
            <Text style={styles.sectionBody}>{section.body}</Text>
            {/* Debug: Show section-level metrics */}
            <SectionDebug label={section.label} body={section.body} index={index} />
          </>
        )}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {renderTabs()}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.textTertiary} />
            <Text style={styles.loadingText}>
              {activeTab === 'deep_dive' 
                ? 'Generating your personalized reading...\nThis may take 30-45 seconds'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={32} color={Colors.textTertiary} />
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => loadTabData(activeTab)}
            >
              <Text style={styles.retryText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : data ? (
          <>
            {/* Title */}
            <Text style={styles.title}>{data.title}</Text>

            {/* Date for Today tab */}
            {data.date && (
              <Text style={styles.dateLabel}>{data.date}</Text>
            )}

            {/* Core Mechanics Card (Summary and Deep Dive) */}
            {(activeTab === 'summary' || activeTab === 'deep_dive') && renderCoreMechanics()}

            {/* Expand Button (Deep Dive only) */}
            {activeTab === 'deep_dive' && (
              <TouchableOpacity
                style={styles.expandButton}
                onPress={() => setExpandedSection(expandedSection ? null : 'all')}
              >
                <Text style={styles.expandButtonText}>
                  {expandedSection ? 'Collapse sections' : 'Explore your mechanics'}
                </Text>
                <Ionicons
                  name={expandedSection ? 'contract-outline' : 'expand-outline'}
                  size={16}
                  color={Colors.accent}
                />
              </TouchableOpacity>
            )}

            {/* Sections */}
            {data.sections.map((section, index) => renderSection(section, index))}

            {/* Gene Keys Sequences (Deep Dive only) */}
            {activeTab === 'deep_dive' && renderGeneKeys()}

            {/* Mirror Prompt */}
            {data.mirror_prompt && (
              <View style={styles.mirrorPromptCard}>
                <Text style={styles.mirrorPromptLabel}>EXPERIMENT</Text>
                <Text style={styles.mirrorPromptText}>{data.mirror_prompt}</Text>
              </View>
            )}

            {/* Ask Mirror Button */}
            <TouchableOpacity
              style={styles.askMirrorButton}
              onPress={onOpenChat}
            >
              <Ionicons name="chatbubble-outline" size={18} color={Colors.surface} />
              <Text style={styles.askMirrorText}>Ask about this lens</Text>
            </TouchableOpacity>

            {/* Footer */}
            <Text style={styles.footer}>
              A lens for understanding energy patterns, not a definition of who you are.
            </Text>
            
            {/* Version Debug Panel - only shows when DEBUG_MIRROR is enabled */}
            {renderVersionDebug()}
            
            {/* Debug Footer - only shows when DEBUG_MIRROR is enabled */}
            {activeTab === 'deep_dive' && data.sections && (
              <DebugFooter 
                lens="Human Design"
                sections={data.sections}
                source={data.debug_stamp?.source}
                rawDataLength={rawDataLength}
                debugStamp={data.debug_stamp}
              />
            )}
          </>
        ) : null}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    backgroundColor: Colors.surface,
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: Colors.text,
  },
  tabText: {
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  activeTabText: {
    color: Colors.surface,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: Colors.textTertiary,
  },
  errorContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: Colors.surface,
    borderRadius: 8,
  },
  retryText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  title: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  dateLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginBottom: 20,
  },
  coreMechanicsCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  coreMechanicsTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    textAlign: 'center',
    marginBottom: 16,
  },
  mechanicsGrid: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mechanicItem: {
    alignItems: 'center',
    paddingHorizontal: 16,
    gap: 4,
  },
  mechanicLabel: {
    fontSize: 10,
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  mechanicValue: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
    textAlign: 'center',
  },
  mechanicValueSmall: {
    fontSize: 12,
    lineHeight: 16,
  },
  mechanicGates: {
    fontSize: 11,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: 2,
  },
  mechanicDivider: {
    width: 1,
    height: 40,
    backgroundColor: Colors.border,
  },
  expandButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    marginBottom: 16,
  },
  expandButtonText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  sectionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
    letterSpacing: 0.3,
    flex: 1,
  },
  sectionBody: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.text,
    marginTop: 12,
  },
  mirrorPromptCard: {
    backgroundColor: '#FDFCFA',
    borderRadius: 12,
    padding: 20,
    marginTop: 8,
    marginBottom: 20,
    borderLeftWidth: 3,
    borderLeftColor: Colors.accent,
  },
  mirrorPromptLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  mirrorPromptText: {
    fontSize: 16,
    lineHeight: 26,
    color: Colors.text,
    fontStyle: 'italic',
  },
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    backgroundColor: Colors.text,
    borderRadius: 12,
    marginBottom: 20,
  },
  askMirrorText: {
    fontSize: 15,
    color: Colors.surface,
    fontWeight: '500',
  },
  footer: {
    fontSize: 12,
    color: Colors.textTertiary,
    textAlign: 'center',
    fontStyle: 'italic',
    opacity: 0.7,
  },
  // Version Debug Panel styles (non-production)
  versionDebugCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 8,
    padding: 12,
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#2a2a4e',
  },
  versionDebugTitle: {
    fontSize: 10,
    fontWeight: '600',
    color: '#6a6a8a',
    letterSpacing: 1,
    marginBottom: 8,
  },
  versionDebugRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 2,
  },
  versionDebugLabel: {
    fontSize: 11,
    color: '#8a8aaa',
    fontFamily: 'monospace',
  },
  versionDebugValue: {
    fontSize: 11,
    color: '#aaaacc',
    fontFamily: 'monospace',
  },
  // Gene Keys styles - Improved UX
  gkContainer: {
    marginTop: 32,
    marginBottom: 16,
  },
  gkDivider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    gap: 12,
  },
  gkDividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  gkDividerText: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 2,
  },
  gkHelperText: {
    fontSize: 13,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 18,
    fontStyle: 'italic',
  },
  viewModeToggle: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 8,
    padding: 4,
    marginBottom: 16,
  },
  viewModeButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  viewModeButtonActive: {
    backgroundColor: Colors.accent,
  },
  viewModeText: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontWeight: '500',
  },
  viewModeTextActive: {
    color: Colors.surface,
  },
  gkSectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  gkSectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  gkSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  gkSectionSubtitle: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 2,
  },
  gkArcsContainer: {
    gap: 10,
  },
  gkArcCard: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 10,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  gkArcHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
    backgroundColor: 'rgba(255,255,255,0.02)',
  },
  gkArcHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  gkArcHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gkArcTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  gkArcSubtitle: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 1,
    maxWidth: 180,
  },
  gkArcCount: {
    fontSize: 11,
    color: Colors.textTertiary,
  },
  gkArcContent: {
    paddingHorizontal: 14,
    paddingBottom: 12,
    gap: 8,
  },
  gkArcHelper: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    marginBottom: 8,
    lineHeight: 16,
  },
  // Technical view sphere item (compact)
  gkSphereItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.04)',
  },
  gkSphereLeft: {
    flex: 1,
  },
  gkSphereRight: {
    alignItems: 'flex-end',
  },
  gkSphereName: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  gkThemeLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 2,
    fontStyle: 'italic',
  },
  gkGateLine: {
    fontSize: 15,
    color: Colors.text,
    fontWeight: '700',
    fontFamily: 'monospace',
  },
  gkSource: {
    fontSize: 10,
    color: Colors.textTertiary,
    marginTop: 2,
  },
  // Everyday language sphere item (expanded)
  gkSphereItemExpanded: {
    paddingVertical: 14,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.04)',
    backgroundColor: 'rgba(255,255,255,0.02)',
    borderRadius: 8,
    marginBottom: 8,
  },
  gkSphereHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  gkSphereTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  gkSphereTechnical: {
    fontSize: 11,
    color: Colors.textTertiary,
    fontFamily: 'monospace',
  },
  gkSphereTheme: {
    fontSize: 12,
    color: Colors.accent,
    fontWeight: '500',
    marginBottom: 6,
  },
  gkSphereDescription: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 18,
    marginBottom: 8,
  },
  gkSpherePrompt: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontStyle: 'italic',
    lineHeight: 16,
  },
  gkVersion: {
    fontSize: 10,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 12,
    fontFamily: 'monospace',
  },
});
