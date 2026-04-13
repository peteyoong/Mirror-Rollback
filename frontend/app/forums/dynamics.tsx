import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { getForumDynamicsContext, ForumDynamicsContext } from '../../services/api';

// Reflective descriptions for each section
const REFLECTIVE_TEXTS = {
  hdTypes: "A mix of different energy types may create a rhythm where some members initiate, others sustain momentum, and others help guide or reflect the group.",
  enneagram: "When people approach challenges from different motivational patterns, the group may naturally explore problems from multiple angles.",
  astrology: "Different elemental emphases may shape how members respond to challenges — some through action, others through reflection, structure, or emotional insight.",
  patterns: "Shared themes sometimes surface repeatedly across a group, creating space for members to explore similar challenges from different perspectives.",
  authority: "This mix may influence how decisions are explored — some members needing time for emotional clarity, others responding quickly in the moment."
};

export default function ForumDynamicsScreen() {
  const { theme } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { forumId } = useLocalSearchParams();

  const [dynamics, setDynamics] = useState<ForumDynamicsContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.id && forumId) {
      fetchDynamics();
    }
  }, [user?.id, forumId]);

  const fetchDynamics = async () => {
    if (!user?.id || !forumId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await getForumDynamicsContext(forumId as string, user.id);
      setDynamics(response.context);
    } catch (err: any) {
      console.error('[ForumDynamics] Error:', err);
      setError('Unable to load forum dynamics. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    router.back();
  };

  const handleExplorePair = () => {
    router.push({ pathname: '/forums/pairwise', params: { forumId } });
  };

  // Helper to render distribution as a list
  const renderDistribution = (
    distribution: Record<string, number> | Record<number, number>,
    labelPrefix: string = ''
  ) => {
    const entries = Object.entries(distribution).sort((a, b) => Number(b[1]) - Number(a[1]));
    if (entries.length === 0) return null;

    return (
      <View style={styles.distributionList}>
        {entries.map(([key, count]) => (
          <View key={key} style={styles.distributionItem}>
            <Text style={[styles.distributionLabel, { color: theme.text }]}>
              {labelPrefix}{key}
            </Text>
            <View style={[styles.distributionBadge, { backgroundColor: theme.accent + '20' }]}>
              <Text style={[styles.distributionCount, { color: theme.accent }]}>{count}</Text>
            </View>
          </View>
        ))}
      </View>
    );
  };

  // Helper to render pattern domains
  const renderPatternDomains = (domains: { domain: string; count: number }[]) => {
    if (!domains || domains.length === 0) return null;

    return (
      <View style={styles.distributionList}>
        {domains.slice(0, 5).map((item) => (
          <View key={item.domain} style={styles.distributionItem}>
            <Text style={[styles.distributionLabel, { color: theme.text }]}>
              {item.domain}
            </Text>
            <Text style={[styles.distributionMeta, { color: theme.textTertiary }]}>
              {item.count} {item.count === 1 ? 'member' : 'members'}
            </Text>
          </View>
        ))}
      </View>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity onPress={handleBack} style={styles.backButton}>
          <Text style={[styles.backText, { color: theme.accent }]}>← Back</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => router.replace('/(tabs)')} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }} style={{ padding: 8 }}>
          <Ionicons name="home-outline" size={22} color={theme.text} />
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content} 
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Title */}
        <View style={styles.titleSection}>
          <Text style={[styles.title, { color: theme.text }]}>Dynamics of This Circle</Text>
          <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
            A view of the patterns and diversity within this group
          </Text>
        </View>

        {/* Explore Pair Button */}
        {dynamics && dynamics.member_count > 1 && (
          <TouchableOpacity
            style={[styles.explorePairButton, { backgroundColor: theme.accent + '15', borderColor: theme.accent + '40' }]}
            onPress={handleExplorePair}
          >
            <Text style={[styles.explorePairText, { color: theme.accent }]}>
              Explore Member Pair
            </Text>
            <Text style={[styles.explorePairArrow, { color: theme.accent }]}>→</Text>
          </TouchableOpacity>
        )}

        {/* Content */}
        {loading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.accent} />
            <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
              Loading dynamics...
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Text style={[styles.errorText, { color: theme.error }]}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryButton, { backgroundColor: theme.accent + '20' }]}
              onPress={fetchDynamics}
            >
              <Text style={[styles.retryButtonText, { color: theme.accent }]}>Try Again</Text>
            </TouchableOpacity>
          </View>
        ) : dynamics ? (
          <View style={styles.sectionsContainer}>
            {/* Section 1: Human Design Energy Mix */}
            {Object.keys(dynamics.hd_type_distribution).length > 0 && (
              <View style={[styles.section, { backgroundColor: theme.surface }]}>
                <Text style={[styles.sectionTitle, { color: theme.text }]}>
                  Human Design Energy Mix
                </Text>
                {renderDistribution(dynamics.hd_type_distribution)}
                <Text style={[styles.reflectiveText, { color: theme.textSecondary }]}>
                  {REFLECTIVE_TEXTS.hdTypes}
                </Text>
              </View>
            )}

            {/* Section 2: Enneagram Diversity */}
            {Object.keys(dynamics.enneagram_distribution).length > 0 && (
              <View style={[styles.section, { backgroundColor: theme.surface }]}>
                <Text style={[styles.sectionTitle, { color: theme.text }]}>
                  Enneagram Diversity
                </Text>
                {renderDistribution(dynamics.enneagram_distribution, 'Type ')}
                <Text style={[styles.reflectiveText, { color: theme.textSecondary }]}>
                  {REFLECTIVE_TEXTS.enneagram}
                </Text>
              </View>
            )}

            {/* Section 3: Astrology Element Balance */}
            {Object.keys(dynamics.astrology_elements).length > 0 && (
              <View style={[styles.section, { backgroundColor: theme.surface }]}>
                <Text style={[styles.sectionTitle, { color: theme.text }]}>
                  Astrology Element Balance
                </Text>
                {renderDistribution(dynamics.astrology_elements)}
                <Text style={[styles.reflectiveText, { color: theme.textSecondary }]}>
                  {REFLECTIVE_TEXTS.astrology}
                </Text>
              </View>
            )}

            {/* Section 4: Pattern Landscape */}
            {dynamics.active_pattern_domains.length > 0 && (
              <View style={[styles.section, { backgroundColor: theme.surface }]}>
                <Text style={[styles.sectionTitle, { color: theme.text }]}>
                  Pattern Landscape
                </Text>
                {renderPatternDomains(dynamics.active_pattern_domains)}
                <Text style={[styles.reflectiveText, { color: theme.textSecondary }]}>
                  {REFLECTIVE_TEXTS.patterns}
                </Text>
              </View>
            )}

            {/* Section 5: Authority Mix */}
            {Object.keys(dynamics.hd_authority_distribution).length > 0 && (
              <View style={[styles.section, { backgroundColor: theme.surface }]}>
                <Text style={[styles.sectionTitle, { color: theme.text }]}>
                  Authority Mix
                </Text>
                {renderDistribution(dynamics.hd_authority_distribution)}
                <Text style={[styles.reflectiveText, { color: theme.textSecondary }]}>
                  {REFLECTIVE_TEXTS.authority}
                </Text>
              </View>
            )}

            {/* Member count note */}
            <View style={styles.memberCountNote}>
              <Text style={[styles.memberCountText, { color: theme.textTertiary }]}>
                Based on {dynamics.member_count} {dynamics.member_count === 1 ? 'member' : 'members'} in this circle
              </Text>
            </View>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backButton: {
    paddingVertical: 4,
  },
  backText: {
    fontSize: 16,
    fontWeight: '500',
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  titleSection: {
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 14,
  },
  subtitle: {
    fontSize: 17,
    lineHeight: 26,
  },
  explorePairButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 20,
  },
  explorePairText: {
    fontSize: 17,
    fontWeight: '600',
  },
  explorePairArrow: {
    fontSize: 16,
    fontWeight: '600',
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 17,
    marginTop: 16,
  },
  errorContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  errorText: {
    fontSize: 17,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 17,
    fontWeight: '600',
  },
  sectionsContainer: {
    gap: 16,
  },
  section: {
    padding: 20,
    borderRadius: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
  },
  distributionList: {
    gap: 10,
    marginBottom: 16,
  },
  distributionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  distributionLabel: {
    fontSize: 17,
    flex: 1,
  },
  distributionBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  distributionCount: {
    fontSize: 16,
    fontWeight: '600',
  },
  distributionMeta: {
    fontSize: 16,
  },
  reflectiveText: {
    fontSize: 16,
    lineHeight: 26,
    fontStyle: 'italic',
  },
  memberCountNote: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  memberCountText: {
    fontSize: 14,
    fontStyle: 'italic',
  },
});
