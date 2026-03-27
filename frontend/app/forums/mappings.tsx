import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Modal,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import { 
  getForumMemberMappings, 
  ForumMemberMapping,
  ChannelCompletion,
} from '../../services/api';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export default function ForumMappingsScreen() {
  const { theme, isDark } = useTheme();
  const { user } = useAppStore();
  const router = useRouter();
  const { forumId, forumName } = useLocalSearchParams();

  const [mappings, setMappings] = useState<ForumMemberMapping[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMember, setSelectedMember] = useState<ForumMemberMapping | null>(null);
  const [showWhyExpanded, setShowWhyExpanded] = useState(false);

  useEffect(() => {
    if (user?.id && forumId) {
      fetchMappings();
    }
  }, [user?.id, forumId]);

  const fetchMappings = async () => {
    if (!user?.id || !forumId) return;

    setLoading(true);
    setError(null);
    
    try {
      const response = await getForumMemberMappings(forumId as string, user.id);
      if (response.success) {
        setMappings(response.mappings);
      } else {
        setError(response.error || 'Failed to load mappings');
      }
    } catch (err) {
      console.error('[Mappings] Error:', err);
      setError('Unable to load member mappings');
    } finally {
      setLoading(false);
    }
  };

  const handleMemberPress = (mapping: ForumMemberMapping) => {
    setSelectedMember(mapping);
    setShowWhyExpanded(false);
  };

  const handleCloseModal = () => {
    setSelectedMember(null);
    setShowWhyExpanded(false);
  };

  // Render a single mapping row in the list
  const renderMappingRow = (mapping: ForumMemberMapping) => (
    <TouchableOpacity
      key={mapping.member_id}
      style={[styles.mappingRow, { backgroundColor: theme.surface, borderColor: theme.border }]}
      onPress={() => handleMemberPress(mapping)}
      activeOpacity={0.7}
    >
      <View style={styles.mappingContent}>
        {/* Member Name */}
        <Text style={[styles.memberName, { color: theme.text }]}>
          {mapping.member_name}
        </Text>
        
        {/* Headline - scannable in under 10 seconds */}
        <Text style={[styles.headline, { color: theme.textSecondary }]}>
          {mapping.headline}
        </Text>
        
        {/* Watch-out line - short, actionable */}
        <Text style={[styles.watchOut, { color: theme.textTertiary }]}>
          {mapping.what_to_watch.split('.')[0]}
        </Text>
      </View>
      
      <Ionicons name="chevron-forward" size={20} color={theme.textTertiary} />
    </TouchableOpacity>
  );

  // Render the detail modal
  const renderDetailModal = () => {
    if (!selectedMember) return null;

    return (
      <Modal
        visible={!!selectedMember}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={handleCloseModal}
      >
        <SafeAreaView style={[styles.modalContainer, { backgroundColor: theme.background }]}>
          {/* Header */}
          <View style={[styles.modalHeader, { borderBottomColor: theme.border }]}>
            <TouchableOpacity onPress={handleCloseModal} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={theme.text} />
            </TouchableOpacity>
            <View style={styles.modalTitleContainer}>
              <Text style={[styles.modalTitle, { color: theme.text }]}>
                {selectedMember.member_name}
              </Text>
              <Text style={[styles.modalSubtitle, { color: theme.textSecondary }]}>
                How they map to you
              </Text>
            </View>
            <View style={{ width: 40 }} />
          </View>

          <ScrollView 
            style={styles.modalScroll}
            contentContainerStyle={styles.modalContent}
            showsVerticalScrollIndicator={false}
          >
            {/* Section 1: What happens when you're together */}
            <View style={styles.section}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                What happens when you're together
              </Text>
              <Text style={[styles.sectionTitle, { color: theme.text }]}>
                {selectedMember.headline}
              </Text>
              <Text style={[styles.sectionText, { color: theme.textSecondary }]}>
                {selectedMember.description}
              </Text>
            </View>

            {/* Section 2: What works well */}
            <View style={[styles.section, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                What works well
              </Text>
              <Text style={[styles.sectionText, { color: theme.text }]}>
                {selectedMember.what_works}
              </Text>
            </View>

            {/* Section 3: What to watch */}
            <View style={[styles.section, { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                What to watch
              </Text>
              <Text style={[styles.sectionText, { color: theme.text }]}>
                {selectedMember.what_to_watch}
              </Text>
            </View>

            {/* Section 4: Why this happens (expandable) */}
            {selectedMember.why_this_happens.length > 0 && (
              <View style={styles.section}>
                <TouchableOpacity
                  style={styles.expandableHeader}
                  onPress={() => setShowWhyExpanded(!showWhyExpanded)}
                >
                  <Text style={[styles.sectionLabel, { color: theme.textTertiary }]}>
                    Why this happens
                  </Text>
                  <Ionicons
                    name={showWhyExpanded ? "chevron-up" : "chevron-down"}
                    size={20}
                    color={theme.textTertiary}
                  />
                </TouchableOpacity>

                {showWhyExpanded && (
                  <View style={styles.whyContent}>
                    {selectedMember.why_this_happens.map((channel, index) => (
                      <View 
                        key={channel.channel} 
                        style={[
                          styles.channelCard, 
                          { backgroundColor: theme.surface, borderColor: theme.border }
                        ]}
                      >
                        <View style={styles.channelGates}>
                          <View style={[styles.gateBox, { borderColor: theme.border }]}>
                            <Text style={[styles.gateLabel, { color: theme.textTertiary }]}>You</Text>
                            <Text style={[styles.gateNumber, { color: theme.text }]}>
                              Gate {channel.your_gate}
                            </Text>
                          </View>
                          <View style={styles.channelConnector}>
                            <View style={[styles.connectorLine, { backgroundColor: theme.border }]} />
                            <Text style={[styles.channelId, { color: theme.textSecondary }]}>
                              {channel.channel}
                            </Text>
                            <View style={[styles.connectorLine, { backgroundColor: theme.border }]} />
                          </View>
                          <View style={[styles.gateBox, { borderColor: theme.border }]}>
                            <Text style={[styles.gateLabel, { color: theme.textTertiary }]}>They</Text>
                            <Text style={[styles.gateNumber, { color: theme.text }]}>
                              Gate {channel.their_gate}
                            </Text>
                          </View>
                        </View>
                        <View style={styles.channelInfo}>
                          <Text style={[styles.channelName, { color: theme.text }]}>
                            Channel of {channel.name}
                          </Text>
                          <Text style={[styles.channelTheme, { color: theme.textSecondary }]}>
                            {channel.theme}
                          </Text>
                        </View>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            )}

            {/* Spacer for bottom */}
            <View style={{ height: 40 }} />
          </ScrollView>
        </SafeAreaView>
      </Modal>
    );
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity 
          onPress={() => router.back()} 
          style={styles.backButton}
        >
          <Ionicons name="arrow-back" size={24} color={theme.text} />
        </TouchableOpacity>
        <View style={styles.headerTitleContainer}>
          <Text style={[styles.headerTitle, { color: theme.text }]}>
            How they map to me
          </Text>
          {forumName && (
            <Text style={[styles.headerSubtitle, { color: theme.textTertiary }]}>
              {forumName}
            </Text>
          )}
        </View>
        <View style={{ width: 40 }} />
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.textSecondary} />
          <Text style={[styles.loadingText, { color: theme.textTertiary }]}>
            Computing connections...
          </Text>
        </View>
      ) : error ? (
        <View style={styles.centered}>
          <Ionicons name="alert-circle-outline" size={48} color={theme.textTertiary} />
          <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
          <TouchableOpacity 
            style={[styles.retryButton, { borderColor: theme.border }]}
            onPress={fetchMappings}
          >
            <Text style={[styles.retryText, { color: theme.text }]}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : mappings.length === 0 ? (
        <View style={styles.centered}>
          <Ionicons name="people-outline" size={48} color={theme.textTertiary} />
          <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
            No forum members to map
          </Text>
        </View>
      ) : (
        <ScrollView 
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Intro text */}
          <Text style={[styles.introText, { color: theme.textTertiary }]}>
            How each person in your forum energetically connects with you
          </Text>

          {/* Mappings list */}
          {mappings.map(renderMappingRow)}

          {/* Footer spacer */}
          <View style={{ height: 100 }} />
        </ScrollView>
      )}

      {/* Detail Modal */}
      {renderDetailModal()}
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
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  headerTitleContainer: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  headerSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  errorText: {
    marginTop: 12,
    fontSize: 14,
    textAlign: 'center',
  },
  emptyText: {
    marginTop: 12,
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 16,
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 20,
    borderWidth: 1,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  introText: {
    fontSize: 13,
    fontStyle: 'italic',
    marginBottom: 16,
    lineHeight: 18,
  },
  mappingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  mappingContent: {
    flex: 1,
    marginRight: 12,
  },
  memberName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  headline: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 4,
  },
  watchOut: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  // Modal styles
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  closeButton: {
    padding: 8,
  },
  modalTitleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  modalSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  modalScroll: {
    flex: 1,
  },
  modalContent: {
    padding: 20,
  },
  section: {
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    lineHeight: 24,
  },
  sectionText: {
    fontSize: 15,
    lineHeight: 22,
  },
  expandableHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  whyContent: {
    marginTop: 16,
  },
  channelCard: {
    padding: 16,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 12,
  },
  channelGates: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  gateBox: {
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    minWidth: 80,
  },
  gateLabel: {
    fontSize: 10,
    fontWeight: '500',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  gateNumber: {
    fontSize: 14,
    fontWeight: '600',
  },
  channelConnector: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  connectorLine: {
    height: 1,
    width: 12,
  },
  channelId: {
    fontSize: 11,
    fontWeight: '600',
    marginHorizontal: 4,
  },
  channelInfo: {
    alignItems: 'center',
  },
  channelName: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  channelTheme: {
    fontSize: 13,
    fontStyle: 'italic',
    textAlign: 'center',
    lineHeight: 18,
  },
});
