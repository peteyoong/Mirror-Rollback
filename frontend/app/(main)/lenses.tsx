import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Modal,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/services/api';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/constants/theme';

interface Lens {
  id: string;
  title: string;
  icon: string;
  summary: string;
}

interface LensDetail extends Lens {
  deep_dive: {
    description: string;
    key_concepts?: string[];
    reflection_themes?: string[];
    practices?: string[];
    invitation: string;
  };
}

const ICON_MAP: Record<string, keyof typeof Ionicons.glyphMap> = {
  eye: 'eye-outline',
  body: 'body-outline',
  heart: 'heart-outline',
  search: 'search-outline',
  time: 'time-outline',
  planet: 'planet-outline',
  calculator: 'calculator-outline',
  layers: 'layers-outline',
};

export default function Lenses() {
  const [lenses, setLenses] = useState<Lens[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedLens, setSelectedLens] = useState<LensDetail | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [showDeepDive, setShowDeepDive] = useState(false);

  const fetchLenses = useCallback(async () => {
    try {
      const response = await api.get('/lenses');
      setLenses(response.data);
    } catch (error) {
      console.error('Failed to fetch lenses:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchLenses();
  }, [fetchLenses]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchLenses();
  };

  const openLensDetail = async (lensId: string) => {
    setLoadingDetail(true);
    setModalVisible(true);
    setShowDeepDive(false);
    try {
      const response = await api.get(`/lenses/${lensId}`);
      setSelectedLens(response.data);
    } catch (error) {
      console.error('Failed to fetch lens detail:', error);
    } finally {
      setLoadingDetail(false);
    }
  };

  const closeModal = () => {
    setModalVisible(false);
    setSelectedLens(null);
    setShowDeepDive(false);
  };

  const renderLensCard = ({ item }: { item: Lens }) => (
    <TouchableOpacity
      style={styles.lensCard}
      onPress={() => openLensDetail(item.id)}
    >
      <View style={styles.lensIconContainer}>
        <Ionicons
          name={ICON_MAP[item.icon] || 'ellipse-outline'}
          size={28}
          color={COLORS.accent}
        />
      </View>
      <View style={styles.lensContent}>
        <Text style={styles.lensTitle}>{item.title}</Text>
        <Text style={styles.lensSummary} numberOfLines={2}>
          {item.summary}
        </Text>
      </View>
      <Ionicons name="chevron-forward" size={20} color={COLORS.border} />
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.accent} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Lenses</Text>
      </View>

      <View style={styles.introContainer}>
        <Text style={styles.introText}>
          Lenses are optional perspectives to explore—not definitions of who you are.
        </Text>
      </View>

      <FlatList
        data={lenses}
        keyExtractor={(item) => item.id}
        renderItem={renderLensCard}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={COLORS.accent}
          />
        }
      />

      <Modal
        visible={modalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={closeModal}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={closeModal} style={styles.modalCloseButton}>
              <Ionicons name="close" size={24} color={COLORS.primary} />
            </TouchableOpacity>
            {selectedLens && (
              <View style={styles.modalTitleContainer}>
                <Ionicons
                  name={ICON_MAP[selectedLens.icon] || 'ellipse-outline'}
                  size={24}
                  color={COLORS.accent}
                />
                <Text style={styles.modalTitle}>{selectedLens.title}</Text>
              </View>
            )}
            <View style={{ width: 44 }} />
          </View>

          {loadingDetail ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={COLORS.accent} />
            </View>
          ) : selectedLens ? (
            <ScrollView
              contentContainerStyle={styles.modalContent}
              showsVerticalScrollIndicator={false}
            >
              {!showDeepDive ? (
                // Summary View
                <View>
                  <Text style={styles.summaryLabel}>Summary</Text>
                  <Text style={styles.summaryText}>{selectedLens.summary}</Text>

                  <TouchableOpacity
                    style={styles.deepDiveButton}
                    onPress={() => setShowDeepDive(true)}
                  >
                    <Text style={styles.deepDiveButtonText}>Explore Deeper</Text>
                    <Ionicons name="arrow-forward" size={18} color={COLORS.accent} />
                  </TouchableOpacity>
                </View>
              ) : (
                // Deep Dive View
                <View>
                  <TouchableOpacity
                    style={styles.backToSummary}
                    onPress={() => setShowDeepDive(false)}
                  >
                    <Ionicons name="arrow-back" size={18} color={COLORS.secondary} />
                    <Text style={styles.backToSummaryText}>Back to summary</Text>
                  </TouchableOpacity>

                  <Text style={styles.deepDiveLabel}>Deep Dive</Text>
                  <Text style={styles.deepDiveDescription}>
                    {selectedLens.deep_dive.description}
                  </Text>

                  {/* Key Concepts */}
                  {selectedLens.deep_dive.key_concepts && selectedLens.deep_dive.key_concepts.length > 0 && (
                    <View style={styles.practicesContainer}>
                      <Text style={styles.practicesLabel}>Key Concepts</Text>
                      {selectedLens.deep_dive.key_concepts.map((concept, index) => (
                        <View key={index} style={styles.practiceItem}>
                          <View style={styles.practiceBullet} />
                          <Text style={styles.practiceText}>{concept}</Text>
                        </View>
                      ))}
                    </View>
                  )}

                  {/* Reflection Themes */}
                  {selectedLens.deep_dive.reflection_themes && selectedLens.deep_dive.reflection_themes.length > 0 && (
                    <View style={styles.reflectionThemesContainer}>
                      <Text style={styles.practicesLabel}>Reflection Themes</Text>
                      {selectedLens.deep_dive.reflection_themes.map((theme, index) => (
                        <View key={index} style={styles.themeItem}>
                          <Text style={styles.themeText}>{theme}</Text>
                        </View>
                      ))}
                    </View>
                  )}

                  {/* Legacy Practices (for backward compatibility) */}
                  {selectedLens.deep_dive.practices && selectedLens.deep_dive.practices.length > 0 && (
                    <View style={styles.practicesContainer}>
                      <Text style={styles.practicesLabel}>Practices</Text>
                      {selectedLens.deep_dive.practices.map((practice, index) => (
                        <View key={index} style={styles.practiceItem}>
                          <View style={styles.practiceBullet} />
                          <Text style={styles.practiceText}>{practice}</Text>
                        </View>
                      ))}
                    </View>
                  )}

                  <View style={styles.invitationContainer}>
                    <Text style={styles.invitationLabel}>An Invitation</Text>
                    <Text style={styles.invitationText}>
                      {selectedLens.deep_dive.invitation}
                    </Text>
                  </View>
                </View>
              )}
            </ScrollView>
          ) : null}
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
  },
  title: {
    fontSize: 28,
    fontWeight: '300',
    color: COLORS.primary,
  },
  introContainer: {
    paddingHorizontal: SPACING.lg,
    paddingBottom: SPACING.md,
  },
  introText: {
    fontSize: 14,
    color: COLORS.secondary,
    lineHeight: 22,
  },
  listContent: {
    padding: SPACING.lg,
    paddingTop: SPACING.sm,
    paddingBottom: SPACING.xxl,
  },
  lensCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.03,
    shadowRadius: 4,
    elevation: 1,
  },
  lensIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#F5F8F3',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  lensContent: {
    flex: 1,
  },
  lensTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.primary,
    marginBottom: SPACING.xs,
  },
  lensSummary: {
    fontSize: 14,
    color: COLORS.secondary,
    lineHeight: 20,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  modalCloseButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
  },
  modalTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '500',
    color: COLORS.primary,
  },
  modalContent: {
    padding: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  summaryLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.accent,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: SPACING.md,
  },
  summaryText: {
    fontSize: 18,
    color: COLORS.primary,
    lineHeight: 28,
  },
  deepDiveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: SPACING.xxl,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.accent,
    gap: SPACING.sm,
  },
  deepDiveButtonText: {
    color: COLORS.accent,
    fontSize: 16,
    fontWeight: '500',
  },
  backToSummary: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SPACING.lg,
    gap: SPACING.xs,
  },
  backToSummaryText: {
    color: COLORS.secondary,
    fontSize: 14,
  },
  deepDiveLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.accent,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: SPACING.md,
  },
  deepDiveDescription: {
    fontSize: 16,
    color: COLORS.primary,
    lineHeight: 26,
  },
  practicesContainer: {
    marginTop: SPACING.xl,
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
  },
  practicesLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  practiceItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SPACING.sm,
  },
  practiceBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.accent,
    marginTop: 8,
    marginRight: SPACING.sm,
  },
  practiceText: {
    flex: 1,
    fontSize: 15,
    color: COLORS.secondary,
    lineHeight: 22,
  },
  reflectionThemesContainer: {
    marginTop: SPACING.xl,
    backgroundColor: '#F9F9F7',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
  },
  themeItem: {
    marginBottom: SPACING.md,
    paddingLeft: SPACING.sm,
    borderLeftWidth: 2,
    borderLeftColor: COLORS.accentLight,
  },
  themeText: {
    fontSize: 15,
    color: COLORS.primary,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  invitationContainer: {
    marginTop: SPACING.xl,
    padding: SPACING.lg,
    backgroundColor: '#F5F8F3',
    borderRadius: BORDER_RADIUS.md,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
  },
  invitationLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.accent,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: SPACING.sm,
  },
  invitationText: {
    fontSize: 16,
    color: COLORS.primary,
    lineHeight: 26,
    fontStyle: 'italic',
  },
});
