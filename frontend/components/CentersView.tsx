import React, { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import api from '../services/api';
import { InlineResonanceReflect } from './ResonanceReflectButtons';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface CenterData {
  center_name: string;
  display_name: string;
  defined: boolean;
  gates_present: number[];
  themes: string[];
  what_this_means: string;
  your_challenge: string;
  your_genius: string;
  practical_experiments: string[];
  remember: string;
}

interface CentersResponse {
  success: boolean;
  centers: CenterData[];
  summary?: {
    defined_count: number;
    undefined_count: number;
    definition_type: string;
  };
}

interface Props {
  userId: string;
}

// Export handle type for parent component to use
export interface CentersViewHandle {
  openCenter: (centerName: string) => void;
}

const CentersView = forwardRef<CentersViewHandle, Props>(({ userId }, ref) => {
  const { theme } = useTheme();
  const [centers, setCenters] = useState<CenterData[]>([]);
  const [summary, setSummary] = useState<{ defined_count: number; undefined_count: number } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCenter, setExpandedCenter] = useState<string | null>(null);
  
  // Parent accordion state - collapsed by default
  const [isAccordionExpanded, setIsAccordionExpanded] = useState(false);

  // Expose openCenter method to parent via ref
  useImperativeHandle(ref, () => ({
    openCenter: (centerName: string) => {
      // First, expand the main accordion
      if (!isAccordionExpanded) {
        LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
        setIsAccordionExpanded(true);
      }
      
      // Then expand the specific center - normalize the name for matching
      const normalizedName = centerName.toLowerCase().replace(/\s+/g, '').replace('/', '');
      const matchedCenter = centers.find(c => {
        const cn = c.center_name.toLowerCase().replace(/\s+/g, '').replace('/', '');
        const dn = c.display_name.toLowerCase().replace(/\s+/g, '').replace('/', '');
        return cn.includes(normalizedName) || normalizedName.includes(cn) ||
               dn.includes(normalizedName) || normalizedName.includes(dn) ||
               // Handle special cases
               (normalizedName === 'g' && (cn === 'gcenter' || cn === 'g center')) ||
               (normalizedName === 'heart' && (cn === 'ego' || cn.includes('heart'))) ||
               (normalizedName === 'solarplexus' && cn.includes('solar'));
      });
      
      if (matchedCenter) {
        LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
        setExpandedCenter(matchedCenter.center_name);
      }
    }
  }), [isAccordionExpanded, centers]);

  useEffect(() => {
    loadCenters();
  }, [userId]);

  const loadCenters = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<CentersResponse>(`/human-design/centers/${userId}`);
      if (response.data.success) {
        setCenters(response.data.centers);
        setSummary(response.data.summary || null);
      } else {
        setError('Unable to load centers data.');
      }
    } catch (err: any) {
      console.error('Centers load error:', err);
      setError('Unable to load centers right now.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCenter = (centerName: string) => {
    setExpandedCenter(expandedCenter === centerName ? null : centerName);
  };

  const renderCenterCard = (center: CenterData) => {
    const isExpanded = expandedCenter === center.center_name;
    const statusLabel = center.defined ? 'Defined' : 'Undefined';
    const statusColor = center.defined ? theme.accent : theme.textTertiary;

    return (
      <View
        key={center.center_name}
        style={[styles.centerCard, { backgroundColor: theme.surface, borderColor: theme.border }]}
      >
        {/* Header - always visible */}
        <TouchableOpacity
          style={styles.centerHeader}
          onPress={() => toggleCenter(center.center_name)}
          activeOpacity={0.7}
        >
          <View style={styles.centerHeaderLeft}>
            <Text style={[styles.centerName, { color: theme.text }]}>
              {center.display_name}
            </Text>
            <View style={styles.centerMeta}>
              <Text style={[styles.centerStatus, { color: statusColor }]}>
                {statusLabel}
              </Text>
              {center.gates_present.length > 0 && (
                <Text style={[styles.centerGates, { color: theme.textTertiary }]}>
                  • Gates {center.gates_present.join(', ')}
                </Text>
              )}
            </View>
          </View>
          <Text style={[styles.expandIcon, { color: theme.textTertiary }]}>
            {isExpanded ? '▾' : '▸'}
          </Text>
        </TouchableOpacity>

        {/* Themes row - always visible */}
        <View style={[styles.themesRow, { borderTopColor: theme.border }]}>
          {center.themes.map((themeText, idx) => (
            <Text key={idx} style={[styles.themeTag, { color: theme.textSecondary }]}>
              {themeText}
            </Text>
          ))}
        </View>

        {/* Expanded content */}
        {isExpanded && (
          <View style={[styles.expandedContent, { borderTopColor: theme.border }]}>
            {/* What This Means */}
            <View style={styles.sectionBlock}>
              <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
                What This Means
              </Text>
              <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
                {center.what_this_means}
              </Text>
            </View>

            {/* Your Challenge */}
            <View style={styles.sectionBlock}>
              <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
                Your Challenge
              </Text>
              <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
                {center.your_challenge}
              </Text>
            </View>

            {/* Your Genius */}
            <View style={styles.sectionBlock}>
              <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
                Your Genius
              </Text>
              <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>
                {center.your_genius}
              </Text>
            </View>

            {/* Practical Experiments */}
            <View style={styles.sectionBlock}>
              <Text style={[styles.sectionTitle, { color: theme.textTertiary }]}>
                Practical Experiments
              </Text>
              {center.practical_experiments.map((exp, idx) => (
                <View key={idx} style={styles.experimentRow}>
                  <Text style={[styles.experimentBullet, { color: theme.accent }]}>•</Text>
                  <Text style={[styles.experimentText, { color: theme.textSecondary }]}>
                    {exp}
                  </Text>
                </View>
              ))}
            </View>

            {/* Remember */}
            <View style={[styles.rememberBlock, { backgroundColor: 'rgba(255,255,255,0.02)', borderLeftColor: theme.accent }]}>
              <Text style={[styles.rememberLabel, { color: theme.textTertiary }]}>
                Remember
              </Text>
              <Text style={[styles.rememberText, { color: theme.text }]}>
                {center.remember}
              </Text>
            </View>

            {/* Reflect Button */}
            <View style={styles.reflectContainer}>
              <InlineResonanceReflect
                source={{
                  lens: 'human_design',
                  type: 'center',
                  name: center.display_name,
                  value: center.defined ? 'Defined' : 'Undefined',
                  id: `hd_center_${center.center_name.toLowerCase().replace(/\s+/g, '_')}`,
                }}
                prompt={center.what_this_means}
              />
            </View>
          </View>
        )}
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="small" color={theme.textTertiary} />
        <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
          Loading centers...
        </Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Parent Accordion Header - collapsed by default */}
      <TouchableOpacity
        style={[styles.accordionHeader, { backgroundColor: theme.surface, borderColor: theme.border }]}
        onPress={() => setIsAccordionExpanded(!isAccordionExpanded)}
        activeOpacity={0.7}
      >
        <View style={styles.accordionHeaderLeft}>
          <Text style={[styles.accordionTitle, { color: theme.text }]}>
            Centers
          </Text>
          {summary && (
            <Text style={[styles.accordionSubtitle, { color: theme.textTertiary }]}>
              {summary.defined_count} Defined • {summary.undefined_count} Undefined
            </Text>
          )}
        </View>
        <Text style={[styles.accordionChevron, { color: theme.textTertiary }]}>
          {isAccordionExpanded ? '▲' : '▼'}
        </Text>
      </TouchableOpacity>

      {/* Accordion Content - Only visible when expanded */}
      {isAccordionExpanded && (
        <View style={styles.accordionContent}>
          {/* Intro text */}
          <Text style={[styles.introText, { color: theme.textSecondary }]}>
            Your nine centers are like different rooms in a house—each with its own function.
            Defined centers have consistent energy; undefined centers take in energy from others.
          </Text>

          {/* Centers list */}
          <View style={styles.centersList}>
            {centers.map(center => renderCenterCard(center))}
          </View>
        </View>
      )}
    </View>
  );
});

// Add display name for debugging
CentersView.displayName = 'CentersView';

export default CentersView;

const styles = StyleSheet.create({
  container: {
    marginTop: 16,
    marginBottom: 16,
  },
  // Parent Accordion
  accordionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
  },
  accordionHeaderLeft: {
    flex: 1,
  },
  accordionTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  accordionSubtitle: {
    fontSize: 14,
    marginTop: 2,
  },
  accordionChevron: {
    fontSize: 14,
  },
  accordionContent: {
    marginTop: 8,
    paddingTop: 12,
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
    gap: 8,
  },
  loadingText: {
    fontSize: 16,
  },
  errorContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  
  // Old styles (kept for reference)
  sectionHeader: {
    marginBottom: 16,
  },
  sectionHeaderTitle: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 1.5,
    marginBottom: 4,
  },
  sectionHeaderMeta: {
    fontSize: 14,
  },
  
  // Intro
  introText: {
    fontSize: 16,
    lineHeight: 28,
    marginBottom: 16,
  },
  
  // Centers list
  centersList: {
    gap: 12,
  },
  
  // Center card
  centerCard: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    overflow: 'hidden',
  },
  
  // Center header
  centerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
  },
  centerHeaderLeft: {
    flex: 1,
  },
  centerName: {
    fontSize: 17,
    fontWeight: '500',
    marginBottom: 4,
  },
  centerMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  centerStatus: {
    fontSize: 14,
    fontWeight: '500',
  },
  centerGates: {
    fontSize: 14,
    marginLeft: 8,
  },
  expandIcon: {
    fontSize: 16,
    marginLeft: 8,
  },
  
  // Themes row
  themesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderTopWidth: StyleSheet.hairlineWidth,
    gap: 8,
  },
  themeTag: {
    fontSize: 14,
    fontStyle: 'italic',
  },
  
  // Expanded content
  expandedContent: {
    padding: 14,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  
  // Section blocks
  sectionBlock: {
    marginBottom: 18,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  sectionBody: {
    fontSize: 16,
    lineHeight: 26,
  },
  
  // Experiments
  experimentRow: {
    flexDirection: 'row',
    marginBottom: 14,
  },
  experimentBullet: {
    fontSize: 16,
    marginRight: 8,
    marginTop: 1,
  },
  experimentText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 28,
  },
  
  // Remember block
  rememberBlock: {
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 2,
    marginTop: 4,
  },
  rememberLabel: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  rememberText: {
    fontSize: 16,
    lineHeight: 28,
    fontStyle: 'italic',
  },
  
  // Reflect button container
  reflectContainer: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
  },
});
