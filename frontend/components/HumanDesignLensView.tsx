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

  // Render a single Gene Key sphere position
  const renderGeneKeySphere = (name: string, position: GeneKeyPosition) => {
    const chartLabel = position.source_chart === 'personality' ? 'Conscious' : 'Unconscious';
    return (
      <View key={name} style={styles.gkSphereItem}>
        <Text style={styles.gkSphereName}>{formatSphereName(name)}</Text>
        <View style={styles.gkSphereDetails}>
          <Text style={styles.gkGateLine}>
            Gate {position.gate}.{position.line}
          </Text>
          <Text style={styles.gkSource}>
            {position.source_planet} ({chartLabel})
          </Text>
        </View>
      </View>
    );
  };

  // Format sphere name from snake_case to Title Case
  const formatSphereName = (name: string): string => {
    return name
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Render Gene Keys Arc card
  const renderGeneKeysArc = (
    arcName: string, 
    arcData: Record<string, GeneKeyPosition> | undefined,
    icon: keyof typeof Ionicons.glyphMap
  ) => {
    if (!arcData) return null;
    
    return (
      <View style={styles.gkArcCard}>
        <View style={styles.gkArcHeader}>
          <Ionicons name={icon} size={18} color={Colors.accent} />
          <Text style={styles.gkArcTitle}>{arcName}</Text>
        </View>
        <View style={styles.gkArcContent}>
          {Object.entries(arcData).map(([name, position]) => 
            renderGeneKeySphere(name, position)
          )}
        </View>
      </View>
    );
  };

  // Render all Gene Keys sequences
  const renderGeneKeys = () => {
    if (!data?.gene_keys) return null;
    
    const gk = data.gene_keys;
    
    return (
      <View style={styles.gkContainer}>
        <Text style={styles.gkSectionTitle}>GENE KEYS SEQUENCES</Text>
        {renderGeneKeysArc('Purpose Arc', gk.purpose_arc, 'compass-outline')}
        {renderGeneKeysArc('Love Arc', gk.love_arc, 'heart-outline')}
        {renderGeneKeysArc('Prosperity Arc', gk.prosperity_arc, 'diamond-outline')}
        {isDebugEnabled() && (
          <Text style={styles.gkVersion}>v: {gk.gene_keys_version}</Text>
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
  // Gene Keys styles
  gkContainer: {
    marginTop: 24,
    marginBottom: 16,
  },
  gkSectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1.5,
    marginBottom: 16,
  },
  gkArcCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.05)',
  },
  gkArcHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.08)',
  },
  gkArcTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  gkArcContent: {
    gap: 8,
  },
  gkSphereItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 6,
  },
  gkSphereName: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  gkSphereDetails: {
    alignItems: 'flex-end',
  },
  gkGateLine: {
    fontSize: 14,
    color: Colors.text,
    fontWeight: '600',
  },
  gkSource: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 2,
  },
  gkVersion: {
    fontSize: 10,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 8,
    fontFamily: 'monospace',
  },
});
