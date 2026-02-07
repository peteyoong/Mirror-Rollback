import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import { getLifeContext, LifeContextResponse, LifeContextType } from '../services/api';

interface Props {
  userId: string;
  initialContext?: LifeContextType;
}

const CONTEXT_CONFIG = {
  relationships: {
    icon: 'heart-outline' as const,
    label: 'Relationships',
    description: 'How you connect',
  },
  work: {
    icon: 'briefcase-outline' as const,
    label: 'Work',
    description: 'How you create',
  },
  self: {
    icon: 'person-outline' as const,
    label: 'Self',
    description: 'How you grow',
  },
};

const SECTION_ICONS: Record<string, keyof typeof Ionicons.glyphMap> = {
  'Overview': 'compass-outline',
  'Today': 'sunny-outline',
  'Explore': 'search-outline',
  'Reflect': 'create-outline',
};

export default function LifeContextView({ userId, initialContext = 'relationships' }: Props) {
  const [activeContext, setActiveContext] = useState<LifeContextType>(initialContext);
  const [data, setData] = useState<LifeContextResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>('Overview');

  useEffect(() => {
    loadContextData();
  }, [activeContext, userId]);

  const loadContextData = async (forceRefresh = false) => {
    if (forceRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const response = await getLifeContext(userId, activeContext);
      setData(response);
      setExpandedSection('Overview'); // Reset to Overview on context change
    } catch (err: any) {
      console.error(`Life Context ${activeContext} error:`, err);
      setError('Unable to load this context right now.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    loadContextData(true);
  };

  const renderContextTabs = () => (
    <View style={styles.contextTabsContainer}>
      {(Object.keys(CONTEXT_CONFIG) as LifeContextType[]).map((ctx) => {
        const config = CONTEXT_CONFIG[ctx];
        const isActive = activeContext === ctx;
        return (
          <TouchableOpacity
            key={ctx}
            style={[styles.contextTab, isActive && styles.contextTabActive]}
            onPress={() => setActiveContext(ctx)}
            activeOpacity={0.7}
          >
            <Ionicons
              name={config.icon}
              size={20}
              color={isActive ? Colors.text : Colors.textTertiary}
            />
            <Text style={[styles.contextTabLabel, isActive && styles.contextTabLabelActive]}>
              {config.label}
            </Text>
            {isActive && <View style={styles.contextTabIndicator} />}
          </TouchableOpacity>
        );
      })}
    </View>
  );

  const renderSection = (section: { label: string; body: string }, index: number) => {
    const isExpanded = expandedSection === section.label;
    const icon = SECTION_ICONS[section.label] || 'ellipse-outline';

    return (
      <View key={section.label} style={styles.sectionContainer}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => setExpandedSection(isExpanded ? null : section.label)}
          activeOpacity={0.7}
        >
          <View style={styles.sectionHeaderLeft}>
            <Ionicons name={icon} size={18} color={Colors.accent} />
            <Text style={styles.sectionLabel}>{section.label}</Text>
          </View>
          <Ionicons
            name={isExpanded ? 'chevron-up' : 'chevron-down'}
            size={18}
            color={Colors.textTertiary}
          />
        </TouchableOpacity>
        {isExpanded && (
          <View style={styles.sectionContent}>
            <Text style={styles.sectionBody}>{section.body}</Text>
          </View>
        )}
      </View>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.textTertiary} />
        <Text style={styles.loadingText}>Generating your Life context...</Text>
        <Text style={styles.loadingSubtext}>This may take a moment</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle-outline" size={48} color={Colors.textTertiary} />
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => loadContextData()}>
          <Text style={styles.retryButtonText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {renderContextTabs()}

      <ScrollView
        style={styles.scrollContainer}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.textTertiary}
          />
        }
      >
        {/* Context Header */}
        <View style={styles.headerContainer}>
          <Text style={styles.title}>{data?.title || 'Life'}</Text>
          <Text style={styles.contextDescription}>
            {CONTEXT_CONFIG[activeContext].description}
          </Text>
        </View>

        {/* Sections */}
        <View style={styles.sectionsContainer}>
          {data?.sections.map((section, index) => renderSection(section, index))}
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            This isn't a rule. It's a pattern you can notice and work with.
          </Text>
        </View>
      </ScrollView>
    </View>
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
    padding: 40,
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginTop: 8,
  },
  loadingSubtext: {
    fontSize: 13,
    color: Colors.textTertiary,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    gap: 16,
  },
  errorText: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 24,
    backgroundColor: Colors.surface,
    borderRadius: 8,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  retryButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
  },
  contextTabsContainer: {
    flexDirection: 'row',
    backgroundColor: Colors.surface,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: Colors.border,
  },
  contextTab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
    borderRadius: 8,
    position: 'relative',
  },
  contextTabActive: {
    backgroundColor: Colors.background,
  },
  contextTabLabel: {
    fontSize: 12,
    fontWeight: '500',
    color: Colors.textTertiary,
    marginTop: 4,
  },
  contextTabLabelActive: {
    color: Colors.text,
  },
  contextTabIndicator: {
    position: 'absolute',
    bottom: 0,
    left: '25%',
    right: '25%',
    height: 2,
    backgroundColor: Colors.accent,
    borderRadius: 1,
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 40,
  },
  headerContainer: {
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
    letterSpacing: -0.3,
    marginBottom: 8,
  },
  contextDescription: {
    fontSize: 14,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  sectionsContainer: {
    gap: 12,
  },
  sectionContainer: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  sectionLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
  },
  sectionContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 0,
  },
  sectionBody: {
    fontSize: 15,
    lineHeight: 24,
    color: Colors.textSecondary,
  },
  footer: {
    marginTop: 32,
    paddingTop: 24,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  footerText: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
    fontStyle: 'italic',
    lineHeight: 20,
  },
});
