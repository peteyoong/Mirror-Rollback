import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { api } from '../../src/services/api';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/constants/theme';
import { useAuth } from '../../src/context/AuthContext';

interface Lens {
  id: string;
  title: string;
  icon: string;
  summary: string;
  is_dynamic_framework?: boolean;
  dynamic_note?: string;
}

interface StructuredElement {
  label: string;
  description: string;
  patterns_to_observe: string;
}

interface LearnModule {
  id: number;
  title: string;
  subtitle: string;
  narrative: string;
  examples: string[];
  reflective_question: string;
  experiment: string;
}

interface AdvancedLens {
  title: string;
  description: string;
  note: string;
}

interface LearnOverTime {
  intro: string;
  modules: LearnModule[];
  advanced_lens?: AdvancedLens;
}

interface PersonalizedAstrologyInsights {
  has_personalization: boolean;
  sun_insight?: string;
  moon_insight?: string;
  ascendant_insight?: string;
  element_balance?: string;
  integration_question?: string;
  placements?: {
    sun: string;
    moon: string;
    ascendant: string;
  };
}

interface PersonalizedHDInsights {
  has_personalization: boolean;
  type_insight?: string;
  strategy_insight?: string;
  authority_insight?: string;
  integration_reflection?: string;
  not_self_awareness?: string;
  elements?: {
    type: string;
    strategy: string;
    authority: string;
    profile?: string;
  };
}

interface PersonalizedNumerologyInsights {
  has_personalization: boolean;
  life_path_insight?: string;
  expression_insight?: string;
  soul_urge_insight?: string;
  personal_year_insight?: string;
  integration_reflection?: string;
  elements?: {
    life_path: number;
    expression?: number;
    soul_urge?: number;
    personal_year?: number;
  };
}

interface HumanDesignProfile {
  has_profile: boolean;
  profile?: {
    type: string;
    strategy: string;
    authority: string;
    profile?: string;
    definition?: string;
    not_self_theme?: string;
    signature?: string;
  };
}

interface NumerologyProfile {
  has_profile: boolean;
  profile?: {
    life_path: number;
    expression?: number;
    soul_urge?: number;
    personality?: number;
    birthday?: number;
    personal_year?: number;
  };
}

interface LensDetail extends Lens {
  deep_dive: {
    description: string;
    key_concepts?: string[];
    reflection_themes?: string[];
    structured_elements?: {
      note: string;
      type?: StructuredElement;
      strategy?: StructuredElement;
      inner_authority?: StructuredElement;
      profile?: StructuredElement;
      definition?: StructuredElement;
      incarnation_cross?: StructuredElement;
      not_self_and_signature?: StructuredElement;
    };
    learn_over_time?: LearnOverTime;
    how_mirror_uses_this?: string;
    important_note?: string;
    invitation: string;
  };
  personalized_insights?: PersonalizedAstrologyInsights | PersonalizedHDInsights | PersonalizedNumerologyInsights;
}

interface ChatMessage {
  id: string;
  lens_key: string;
  role: 'user' | 'assistant';
  message_text: string;
  created_at: string;
}

interface AstrologyPosition {
  name: string;
  sign: string;
  degree: number;
  minutes: number;
  formatted: string;
}

interface AstrologyProfile {
  has_profile: boolean;
  profile?: {
    positions: {
      ascendant: AstrologyPosition;
      sun: AstrologyPosition;
      moon: AstrologyPosition;
    };
    ayanamsa: string;
    location_name?: string;
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

type ViewMode = 'summary' | 'snapshot' | 'deepdive';

export default function Lenses() {
  const { user } = useAuth();
  const [lenses, setLenses] = useState<Lens[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedLens, setSelectedLens] = useState<LensDetail | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('summary');
  const [snapshot, setSnapshot] = useState<string | null>(null);
  const [loadingSnapshot, setLoadingSnapshot] = useState(false);
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const chatScrollRef = useRef<ScrollView>(null);
  
  // Module expansion state
  const [expandedModuleId, setExpandedModuleId] = useState<number | null>(null);
  
  // Debug state (POC)
  const [debugExpanded, setDebugExpanded] = useState(false);
  const [computeStatus, setComputeStatus] = useState<{ success: boolean; message: string } | null>(null);
  const [runningCompute, setRunningCompute] = useState(false);
  const [showBirthDataForm, setShowBirthDataForm] = useState(false);
  const [birthFormData, setBirthFormData] = useState({
    birth_datetime_local: '',
    tz_offset_minutes: '-300',
    latitude: '',
    longitude: '',
  });
  const [savingBirthData, setSavingBirthData] = useState(false);
  
  // Computed profile from user context (primary source)
  const userAstrologyProfile = user?.computed_profile?.astrology;
  const userBirthData = user?.birth_data;
  
  // Astrology computed profile state (fallback for separate fetch if needed)
  const [astrologyProfile, setAstrologyProfile] = useState<AstrologyProfile | null>(null);
  const [loadingAstrologyProfile, setLoadingAstrologyProfile] = useState(false);
  
  // Human Design profile state
  const [hdProfile, setHdProfile] = useState<HumanDesignProfile | null>(null);
  const [loadingHdProfile, setLoadingHdProfile] = useState(false);

  // Numerology profile state
  const [numerologyProfile, setNumerologyProfile] = useState<NumerologyProfile | null>(null);
  const [loadingNumerologyProfile, setLoadingNumerologyProfile] = useState(false);

  // Run sidereal compute and update user context
  const runSiderealCompute = async () => {
    if (!userBirthData) {
      setComputeStatus({ success: false, message: 'Birth fields missing from user record' });
      return;
    }
    
    setRunningCompute(true);
    setComputeStatus(null);
    
    try {
      const response = await api.post('/computed-profile/astrology', {
        birth_datetime_local: userBirthData.birth_datetime_local,
        tz_offset_minutes: userBirthData.tz_offset_minutes,
        latitude: userBirthData.latitude,
        longitude: userBirthData.longitude,
        ayanamsa: 'FAGAN_BRADLEY',
      });
      
      if (response.data.has_profile && response.data.profile) {
        // Update user context with new computed profile
        if (user) {
          const updatedUser = {
            ...user,
            computed_profile: {
              ...user.computed_profile,
              astrology: {
                ayanamsa: response.data.profile.ayanamsa,
                positions: response.data.profile.positions,
                birth_datetime_local: userBirthData.birth_datetime_local,
                latitude: userBirthData.latitude,
                longitude: userBirthData.longitude,
                computed_at: new Date().toISOString(),
              },
            },
          };
          updateUser(updatedUser);
        }
        setComputeStatus({ success: true, message: 'Compute successful! Profile updated.' });
      } else {
        setComputeStatus({ success: false, message: 'Compute returned no profile data' });
      }
    } catch (error: any) {
      const errMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setComputeStatus({ success: false, message: `Compute failed: ${errMsg}` });
    } finally {
      setRunningCompute(false);
    }
  };

  // Save birth data to user record
  const saveBirthData = async () => {
    if (!birthFormData.birth_datetime_local || !birthFormData.latitude || !birthFormData.longitude) {
      Alert.alert('Missing Fields', 'Please fill in all birth data fields.');
      return;
    }
    
    setSavingBirthData(true);
    try {
      const response = await api.post('/user/birth-data', {
        birth_datetime_local: birthFormData.birth_datetime_local,
        tz_offset_minutes: parseInt(birthFormData.tz_offset_minutes, 10),
        latitude: parseFloat(birthFormData.latitude),
        longitude: parseFloat(birthFormData.longitude),
      });
      
      if (response.data.success && user) {
        const updatedUser = {
          ...user,
          birth_data: response.data.birth_data,
        };
        updateUser(updatedUser);
        setShowBirthDataForm(false);
        Alert.alert('Success', 'Birth data saved! You can now run compute.');
      }
    } catch (error: any) {
      Alert.alert('Error', 'Failed to save birth data.');
    } finally {
      setSavingBirthData(false);
    }
  };

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

  const fetchSnapshot = async (lensId: string) => {
    setLoadingSnapshot(true);
    try {
      const response = await api.get(`/lenses/${lensId}/snapshot`);
      setSnapshot(response.data.snapshot);
    } catch (error) {
      console.error('Failed to fetch snapshot:', error);
      setSnapshot('Unable to load personalized snapshot.');
    } finally {
      setLoadingSnapshot(false);
    }
  };

  const fetchChatHistory = async (lensId: string) => {
    setLoadingChat(true);
    try {
      const response = await api.get(`/lenses/${lensId}/chat`);
      setChatMessages(response.data);
    } catch (error) {
      console.error('Failed to fetch chat history:', error);
    } finally {
      setLoadingChat(false);
    }
  };

  const fetchAstrologyProfile = async () => {
    setLoadingAstrologyProfile(true);
    try {
      const response = await api.get('/computed-profile/astrology');
      setAstrologyProfile(response.data);
    } catch (error) {
      console.error('Failed to fetch astrology profile:', error);
      setAstrologyProfile({ has_profile: false });
    } finally {
      setLoadingAstrologyProfile(false);
    }
  };

  const fetchHdProfile = async () => {
    setLoadingHdProfile(true);
    try {
      const response = await api.get('/computed-profile/human-design');
      setHdProfile(response.data);
    } catch (error) {
      console.error('Failed to fetch HD profile:', error);
      setHdProfile({ has_profile: false });
    } finally {
      setLoadingHdProfile(false);
    }
  };

  const fetchNumerologyProfile = async () => {
    setLoadingNumerologyProfile(true);
    try {
      const response = await api.get('/computed-profile/numerology');
      setNumerologyProfile(response.data);
    } catch (error) {
      console.error('Failed to fetch numerology profile:', error);
      setNumerologyProfile({ has_profile: false });
    } finally {
      setLoadingNumerologyProfile(false);
    }
  };

  const openLensDetail = async (lensId: string) => {
    setLoadingDetail(true);
    setModalVisible(true);
    setViewMode('summary');
    setSnapshot(null);
    setChatMessages([]);
    setChatInput('');
    setAstrologyProfile(null);
    setHdProfile(null);
    setNumerologyProfile(null);
    try {
      const response = await api.get(`/lenses/${lensId}`);
      setSelectedLens(response.data);
      // Fetch chat history in background
      fetchChatHistory(lensId);
      // Fetch astrology profile if this is the astrology lens
      if (lensId === 'true-sidereal-astrology') {
        fetchAstrologyProfile();
      }
      // Fetch HD profile if this is the human design lens
      if (lensId === 'human-design') {
        fetchHdProfile();
      }
      // Fetch numerology profile if this is the numerology lens
      if (lensId === 'numerology') {
        fetchNumerologyProfile();
      }
    } catch (error) {
      console.error('Failed to fetch lens detail:', error);
    } finally {
      setLoadingDetail(false);
    }
  };

  const closeModal = () => {
    setModalVisible(false);
    setSelectedLens(null);
    setViewMode('summary');
    setSnapshot(null);
    setChatMessages([]);
    setChatInput('');
    setExpandedModuleId(null);
    setAstrologyProfile(null);
    setHdProfile(null);
    setNumerologyProfile(null);
  };

  const handleViewSnapshot = () => {
    if (selectedLens && !snapshot) {
      fetchSnapshot(selectedLens.id);
    }
    setViewMode('snapshot');
  };

  const handleViewDeepDive = () => {
    if (selectedLens && chatMessages.length === 0) {
      fetchChatHistory(selectedLens.id);
    }
    setViewMode('deepdive');
  };

  const askAboutModule = (moduleTitle: string, moduleId: number) => {
    const question = `Help me understand Module ${moduleId}: ${moduleTitle} with examples from work and relationships.`;
    setChatInput(question);
    // Scroll to chat section after a short delay
    setTimeout(() => {
      chatScrollRef.current?.scrollToEnd({ animated: true });
    }, 200);
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || !selectedLens || sendingMessage) return;
    
    const message = chatInput.trim();
    setChatInput('');
    setSendingMessage(true);
    
    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      lens_key: selectedLens.id,
      role: 'user',
      message_text: message,
      created_at: new Date().toISOString(),
    };
    setChatMessages(prev => [...prev, tempUserMsg]);
    
    // Scroll to bottom
    setTimeout(() => {
      chatScrollRef.current?.scrollToEnd({ animated: true });
    }, 100);
    
    try {
      const response = await api.post(`/lenses/${selectedLens.id}/chat`, { message });
      // Replace temp message with actual messages
      setChatMessages(prev => {
        const filtered = prev.filter(m => m.id !== tempUserMsg.id);
        return [...filtered, ...response.data];
      });
      // Scroll to bottom again
      setTimeout(() => {
        chatScrollRef.current?.scrollToEnd({ animated: true });
      }, 100);
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove temp message on error
      setChatMessages(prev => prev.filter(m => m.id !== tempUserMsg.id));
      if (Platform.OS !== 'web') {
        Alert.alert('Error', 'Failed to send message. Please try again.');
      }
    } finally {
      setSendingMessage(false);
    }
  };

  const clearChatHistory = async () => {
    if (!selectedLens) return;
    
    const doClear = async () => {
      try {
        await api.delete(`/lenses/${selectedLens.id}/chat`);
        setChatMessages([]);
      } catch (error) {
        console.error('Failed to clear chat:', error);
      }
    };
    
    if (Platform.OS !== 'web') {
      Alert.alert(
        'Clear Chat',
        'Are you sure you want to clear this conversation?',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Clear', style: 'destructive', onPress: doClear }
        ]
      );
    } else {
      doClear();
    }
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

  const renderStructuredElement = (element: StructuredElement) => (
    <View style={styles.structuredElement}>
      <Text style={styles.structuredLabel}>{element.label}</Text>
      <Text style={styles.structuredDescription}>{element.description}</Text>
      <View style={styles.patternsBox}>
        <Text style={styles.patternsLabel}>Patterns to observe:</Text>
        <Text style={styles.patternsText}>{element.patterns_to_observe}</Text>
      </View>
    </View>
  );

  const renderChatMessage = (message: ChatMessage) => (
    <View
      key={message.id}
      style={[
        styles.chatMessage,
        message.role === 'user' ? styles.chatMessageUser : styles.chatMessageAssistant
      ]}
    >
      <Text style={[
        styles.chatMessageText,
        message.role === 'user' ? styles.chatMessageTextUser : styles.chatMessageTextAssistant
      ]}>
        {message.message_text}
      </Text>
    </View>
  );

  const renderModule = (module: LearnModule) => {
    const isExpanded = expandedModuleId === module.id;
    
    return (
      <View key={module.id} style={styles.moduleCard}>
        <TouchableOpacity
          style={styles.moduleHeader}
          onPress={() => setExpandedModuleId(isExpanded ? null : module.id)}
        >
          <View style={styles.moduleNumber}>
            <Text style={styles.moduleNumberText}>{module.id}</Text>
          </View>
          <View style={styles.moduleTitleContainer}>
            <Text style={styles.moduleTitle}>{module.title}</Text>
            <Text style={styles.moduleSubtitle}>{module.subtitle}</Text>
          </View>
          <Ionicons
            name={isExpanded ? 'chevron-up' : 'chevron-down'}
            size={20}
            color={COLORS.secondary}
          />
        </TouchableOpacity>
        
        {isExpanded && (
          <View style={styles.moduleContent}>
            <Text style={styles.moduleNarrative}>{module.narrative}</Text>
            
            <View style={styles.moduleExamples}>
              <Text style={styles.moduleExamplesLabel}>Examples</Text>
              {module.examples.map((example, idx) => (
                <View key={idx} style={styles.moduleExampleItem}>
                  <View style={styles.moduleExampleBullet} />
                  <Text style={styles.moduleExampleText}>{example}</Text>
                </View>
              ))}
            </View>
            
            <View style={styles.moduleReflection}>
              <Ionicons name="help-circle-outline" size={18} color={COLORS.accent} />
              <Text style={styles.moduleReflectionText}>{module.reflective_question}</Text>
            </View>
            
            <View style={styles.moduleExperiment}>
              <Ionicons name="flask-outline" size={18} color="#8B7355" />
              <View style={styles.moduleExperimentContent}>
                <Text style={styles.moduleExperimentLabel}>Optional Experiment</Text>
                <Text style={styles.moduleExperimentText}>{module.experiment}</Text>
              </View>
            </View>
            
            <TouchableOpacity
              style={styles.askModuleButton}
              onPress={() => askAboutModule(module.title, module.id)}
            >
              <Ionicons name="chatbubble-outline" size={18} color={COLORS.white} />
              <Text style={styles.askModuleButtonText}>Ask about this module</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    );
  };

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
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.modalKeyboard}
          >
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
              <View style={styles.modalBody}>
                {/* Navigation Tabs */}
                <View style={styles.tabContainer}>
                  <TouchableOpacity
                    style={[styles.tab, viewMode === 'summary' && styles.tabActive]}
                    onPress={() => setViewMode('summary')}
                  >
                    <Text style={[styles.tabText, viewMode === 'summary' && styles.tabTextActive]}>
                      Summary
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.tab, viewMode === 'snapshot' && styles.tabActive]}
                    onPress={handleViewSnapshot}
                  >
                    <Text style={[styles.tabText, viewMode === 'snapshot' && styles.tabTextActive]}>
                      Your Snapshot
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.tab, viewMode === 'deepdive' && styles.tabActive]}
                    onPress={handleViewDeepDive}
                  >
                    <Text style={[styles.tabText, viewMode === 'deepdive' && styles.tabTextActive]}>
                      Deep Dive
                    </Text>
                  </TouchableOpacity>
                </View>

                <ScrollView
                  style={styles.modalScroll}
                  contentContainerStyle={styles.modalContent}
                  showsVerticalScrollIndicator={false}
                  ref={viewMode === 'deepdive' ? chatScrollRef : undefined}
                >
                  {/* Summary View */}
                  {viewMode === 'summary' && (
                    <View>
                      <Text style={styles.sectionLabel}>Summary</Text>
                      <Text style={styles.summaryText}>{selectedLens.summary}</Text>

                      {selectedLens.is_dynamic_framework && selectedLens.dynamic_note && (
                        <View style={styles.dynamicNote}>
                          <Ionicons name="information-circle-outline" size={20} color={COLORS.accent} />
                          <Text style={styles.dynamicNoteText}>{selectedLens.dynamic_note}</Text>
                        </View>
                      )}
                    </View>
                  )}

                  {/* Snapshot View */}
                  {viewMode === 'snapshot' && (
                    <View>
                      <Text style={styles.sectionLabel}>Your Snapshot</Text>
                      {loadingSnapshot ? (
                        <View style={styles.snapshotLoading}>
                          <ActivityIndicator size="small" color={COLORS.accent} />
                          <Text style={styles.snapshotLoadingText}>Generating personalized insight...</Text>
                        </View>
                      ) : (
                        <View style={styles.snapshotContainer}>
                          <Text style={styles.snapshotText}>{snapshot}</Text>
                        </View>
                      )}
                      <Text style={styles.snapshotDisclaimer}>
                        This reflection is based on what you shared during onboarding. It offers patterns to consider, not fixed truths about who you are.
                      </Text>
                    </View>
                  )}

                  {/* Deep Dive View */}
                  {viewMode === 'deepdive' && (
                    <View>
                      <Text style={styles.sectionLabel}>Deep Dive</Text>

                      {/* Your Sidereal Profile - At the TOP, before any explanatory text */}
                      {selectedLens.id === 'true-sidereal-astrology' && (
                        <View style={styles.siderealProfileContainer}>
                          <Text style={styles.siderealProfileTitle}>Your Sidereal Profile</Text>
                          {loadingAstrologyProfile ? (
                            <ActivityIndicator size="small" color={COLORS.accent} style={{ marginVertical: SPACING.md }} />
                          ) : astrologyProfile?.has_profile && astrologyProfile.profile ? (
                            <View style={styles.siderealProfileContent}>
                              <View style={styles.siderealProfileGrid}>
                                <View style={styles.siderealProfileItem}>
                                  <Text style={styles.siderealProfileLabel}>Sun</Text>
                                  <Text style={styles.siderealProfileSign}>
                                    {astrologyProfile.profile.positions.sun.sign}
                                  </Text>
                                  <Text style={styles.siderealProfileDegree}>
                                    {astrologyProfile.profile.positions.sun.degree}°{astrologyProfile.profile.positions.sun.minutes}'
                                  </Text>
                                </View>
                                <View style={styles.siderealProfileItem}>
                                  <Text style={styles.siderealProfileLabel}>Moon</Text>
                                  <Text style={styles.siderealProfileSign}>
                                    {astrologyProfile.profile.positions.moon.sign}
                                  </Text>
                                  <Text style={styles.siderealProfileDegree}>
                                    {astrologyProfile.profile.positions.moon.degree}°{astrologyProfile.profile.positions.moon.minutes}'
                                  </Text>
                                </View>
                                <View style={styles.siderealProfileItem}>
                                  <Text style={styles.siderealProfileLabel}>Ascendant</Text>
                                  <Text style={styles.siderealProfileSign}>
                                    {astrologyProfile.profile.positions.ascendant.sign}
                                  </Text>
                                  <Text style={styles.siderealProfileDegree}>
                                    {astrologyProfile.profile.positions.ascendant.degree}°{astrologyProfile.profile.positions.ascendant.minutes}'
                                  </Text>
                                </View>
                              </View>
                              <Text style={styles.siderealProfileAyanamsa}>
                                {astrologyProfile.profile.ayanamsa.replace('_', '-')} ayanamsa
                              </Text>
                            </View>
                          ) : (
                            <View style={styles.siderealProfileEmpty}>
                              <Text style={styles.siderealProfileEmptyText}>
                                No birth data computed
                              </Text>
                              <Text style={styles.siderealProfileEmptyHint}>
                                Enter your birth details to see your sidereal placements
                              </Text>
                            </View>
                          )}
                        </View>
                      )}

                      {/* Personalized Insights - Only for Astrology with computed profile */}
                      {selectedLens.id === 'true-sidereal-astrology' && selectedLens.personalized_insights?.has_personalization && (
                        <View style={styles.personalizedInsightsContainer}>
                          <Text style={styles.personalizedInsightsTitle}>Your Chart at a Glance</Text>
                          
                          {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).sun_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}>☉ Sun</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).placements?.sun}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).sun_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).moon_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}>☽ Moon</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).placements?.moon}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).moon_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).ascendant_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}>↑ Rising</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).placements?.ascendant}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).ascendant_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).element_balance && (
                            <View style={styles.personalizedInsightBalance}>
                              <Text style={styles.personalizedInsightBalanceText}>
                                {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).element_balance}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).integration_question && (
                            <View style={styles.personalizedInsightQuestion}>
                              <Ionicons name="help-circle-outline" size={18} color={COLORS.accent} />
                              <Text style={styles.personalizedInsightQuestionText}>
                                {(selectedLens.personalized_insights as PersonalizedAstrologyInsights).integration_question}
                              </Text>
                            </View>
                          )}
                        </View>
                      )}

                      {/* Your Human Design Profile - At the TOP of HD Deep Dive */}
                      {selectedLens.id === 'human-design' && (
                        <View style={styles.siderealProfileContainer}>
                          <Text style={styles.siderealProfileTitle}>Your Human Design Profile</Text>
                          {loadingHdProfile ? (
                            <ActivityIndicator size="small" color={COLORS.accent} style={{ marginVertical: SPACING.md }} />
                          ) : hdProfile?.has_profile && hdProfile.profile ? (
                            <View style={styles.siderealProfileContent}>
                              <View style={styles.hdProfileGrid}>
                                <View style={styles.hdProfileItem}>
                                  <Text style={styles.hdProfileLabel}>Type</Text>
                                  <Text style={styles.hdProfileValue}>{hdProfile.profile.type}</Text>
                                </View>
                                <View style={styles.hdProfileItem}>
                                  <Text style={styles.hdProfileLabel}>Strategy</Text>
                                  <Text style={styles.hdProfileValue}>{hdProfile.profile.strategy}</Text>
                                </View>
                                <View style={styles.hdProfileItem}>
                                  <Text style={styles.hdProfileLabel}>Authority</Text>
                                  <Text style={styles.hdProfileValue}>{hdProfile.profile.authority}</Text>
                                </View>
                                {hdProfile.profile.profile && (
                                  <View style={styles.hdProfileItem}>
                                    <Text style={styles.hdProfileLabel}>Profile</Text>
                                    <Text style={styles.hdProfileValue}>{hdProfile.profile.profile}</Text>
                                  </View>
                                )}
                              </View>
                              {hdProfile.profile.signature && hdProfile.profile.not_self_theme && (
                                <Text style={styles.hdProfileSubtext}>
                                  {hdProfile.profile.signature} ↔ {hdProfile.profile.not_self_theme}
                                </Text>
                              )}
                            </View>
                          ) : (
                            <View style={styles.siderealProfileEmpty}>
                              <Text style={styles.siderealProfileEmptyText}>
                                No Human Design data entered
                              </Text>
                              <Text style={styles.siderealProfileEmptyHint}>
                                Enter your Human Design details to see personalized insights
                              </Text>
                            </View>
                          )}
                        </View>
                      )}

                      {/* Personalized Insights - Only for Human Design with profile */}
                      {selectedLens.id === 'human-design' && selectedLens.personalized_insights?.has_personalization && (
                        <View style={styles.personalizedInsightsContainer}>
                          <Text style={styles.personalizedInsightsTitle}>Your Design at a Glance</Text>
                          
                          {(selectedLens.personalized_insights as PersonalizedHDInsights).type_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}>⬡ Type</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedHDInsights).elements?.type}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedHDInsights).type_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedHDInsights).strategy_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}>→ Strategy</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedHDInsights).elements?.strategy}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedHDInsights).strategy_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedHDInsights).authority_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}>◈ Authority</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedHDInsights).elements?.authority}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedHDInsights).authority_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedHDInsights).not_self_awareness && (
                            <View style={styles.personalizedInsightBalance}>
                              <Text style={styles.personalizedInsightBalanceText}>
                                {(selectedLens.personalized_insights as PersonalizedHDInsights).not_self_awareness}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedHDInsights).integration_reflection && (
                            <View style={styles.personalizedInsightQuestion}>
                              <Ionicons name="flask-outline" size={18} color={COLORS.accent} />
                              <Text style={styles.personalizedInsightQuestionText}>
                                {(selectedLens.personalized_insights as PersonalizedHDInsights).integration_reflection}
                              </Text>
                            </View>
                          )}
                        </View>
                      )}

                      {/* Your Numerology Profile - At the TOP of Numerology Deep Dive */}
                      {selectedLens.id === 'numerology' && (
                        <View style={styles.siderealProfileContainer}>
                          <Text style={styles.siderealProfileTitle}>Your Numerology Profile</Text>
                          {loadingNumerologyProfile ? (
                            <ActivityIndicator size="small" color={COLORS.accent} style={{ marginVertical: SPACING.md }} />
                          ) : numerologyProfile?.has_profile && numerologyProfile.profile ? (
                            <View style={styles.siderealProfileContent}>
                              <View style={styles.hdProfileGrid}>
                                <View style={styles.hdProfileItem}>
                                  <Text style={styles.hdProfileLabel}>Life Path</Text>
                                  <Text style={styles.numerologyNumber}>{numerologyProfile.profile.life_path}</Text>
                                </View>
                                {numerologyProfile.profile.expression && (
                                  <View style={styles.hdProfileItem}>
                                    <Text style={styles.hdProfileLabel}>Expression</Text>
                                    <Text style={styles.numerologyNumber}>{numerologyProfile.profile.expression}</Text>
                                  </View>
                                )}
                                {numerologyProfile.profile.soul_urge && (
                                  <View style={styles.hdProfileItem}>
                                    <Text style={styles.hdProfileLabel}>Soul Urge</Text>
                                    <Text style={styles.numerologyNumber}>{numerologyProfile.profile.soul_urge}</Text>
                                  </View>
                                )}
                                {numerologyProfile.profile.personal_year && (
                                  <View style={styles.hdProfileItem}>
                                    <Text style={styles.hdProfileLabel}>Personal Year</Text>
                                    <Text style={styles.numerologyNumber}>{numerologyProfile.profile.personal_year}</Text>
                                  </View>
                                )}
                              </View>
                            </View>
                          ) : (
                            <View style={styles.siderealProfileEmpty}>
                              <Text style={styles.siderealProfileEmptyText}>
                                No numerology data entered
                              </Text>
                              <Text style={styles.siderealProfileEmptyHint}>
                                Enter your numerology numbers to see personalized insights
                              </Text>
                            </View>
                          )}
                        </View>
                      )}

                      {/* Personalized Insights - Only for Numerology with profile */}
                      {selectedLens.id === 'numerology' && selectedLens.personalized_insights?.has_personalization && (
                        <View style={styles.personalizedInsightsContainer}>
                          <Text style={styles.personalizedInsightsTitle}>Your Numbers at a Glance</Text>
                          
                          {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).life_path_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}># Life Path</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).elements?.life_path}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).life_path_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).expression_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}># Expression</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).elements?.expression}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).expression_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).soul_urge_insight && (
                            <View style={styles.personalizedInsightCard}>
                              <View style={styles.personalizedInsightHeader}>
                                <Text style={styles.personalizedInsightPlanet}># Soul Urge</Text>
                                <Text style={styles.personalizedInsightSign}>
                                  {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).elements?.soul_urge}
                                </Text>
                              </View>
                              <Text style={styles.personalizedInsightText}>
                                {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).soul_urge_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).personal_year_insight && (
                            <View style={styles.personalizedInsightBalance}>
                              <Text style={styles.personalizedInsightBalanceText}>
                                {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).personal_year_insight}
                              </Text>
                            </View>
                          )}
                          
                          {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).integration_reflection && (
                            <View style={styles.personalizedInsightQuestion}>
                              <Ionicons name="eye-outline" size={18} color={COLORS.accent} />
                              <Text style={styles.personalizedInsightQuestionText}>
                                {(selectedLens.personalized_insights as PersonalizedNumerologyInsights).integration_reflection}
                              </Text>
                            </View>
                          )}
                        </View>
                      )}

                      <Text style={styles.deepDiveDescription}>
                        {selectedLens.deep_dive.description}
                      </Text>

                      {selectedLens.deep_dive.how_mirror_uses_this && (
                        <View style={styles.howMirrorUsesContainer}>
                          <Text style={styles.howMirrorUsesLabel}>How Project Mirror Uses This</Text>
                          <Text style={styles.howMirrorUsesText}>
                            {selectedLens.deep_dive.how_mirror_uses_this}
                          </Text>
                        </View>
                      )}

                      {selectedLens.deep_dive.structured_elements && (
                        <View style={styles.structuredContainer}>
                          {selectedLens.deep_dive.structured_elements.note && (
                            <View style={styles.structuredNote}>
                              <Text style={styles.structuredNoteText}>
                                {selectedLens.deep_dive.structured_elements.note}
                              </Text>
                            </View>
                          )}
                          {selectedLens.deep_dive.structured_elements.type && 
                            renderStructuredElement(selectedLens.deep_dive.structured_elements.type)}
                          {selectedLens.deep_dive.structured_elements.strategy && 
                            renderStructuredElement(selectedLens.deep_dive.structured_elements.strategy)}
                          {selectedLens.deep_dive.structured_elements.inner_authority && 
                            renderStructuredElement(selectedLens.deep_dive.structured_elements.inner_authority)}
                          {selectedLens.deep_dive.structured_elements.profile && 
                            renderStructuredElement(selectedLens.deep_dive.structured_elements.profile)}
                          {selectedLens.deep_dive.structured_elements.definition && 
                            renderStructuredElement(selectedLens.deep_dive.structured_elements.definition)}
                          {selectedLens.deep_dive.structured_elements.incarnation_cross && 
                            renderStructuredElement(selectedLens.deep_dive.structured_elements.incarnation_cross)}
                          {selectedLens.deep_dive.structured_elements.not_self_and_signature && 
                            renderStructuredElement(selectedLens.deep_dive.structured_elements.not_self_and_signature)}
                        </View>
                      )}

                      {selectedLens.deep_dive.key_concepts && selectedLens.deep_dive.key_concepts.length > 0 && (
                        <View style={styles.conceptsContainer}>
                          <Text style={styles.conceptsLabel}>Key Concepts</Text>
                          {selectedLens.deep_dive.key_concepts.map((concept, index) => (
                            <View key={index} style={styles.conceptItem}>
                              <View style={styles.conceptBullet} />
                              <Text style={styles.conceptText}>{concept}</Text>
                            </View>
                          ))}
                        </View>
                      )}

                      {selectedLens.deep_dive.important_note && (
                        <View style={styles.importantNote}>
                          <Text style={styles.importantNoteText}>
                            {selectedLens.deep_dive.important_note}
                          </Text>
                        </View>
                      )}

                      {/* Learn Over Time Section - Only for Human Design */}
                      {selectedLens.deep_dive.learn_over_time && (
                        <View style={styles.learnOverTimeContainer}>
                          <Text style={styles.learnOverTimeTitle}>Learn Over Time</Text>
                          <Text style={styles.learnOverTimeIntro}>
                            {selectedLens.deep_dive.learn_over_time.intro}
                          </Text>
                          
                          <View style={styles.modulesContainer}>
                            {selectedLens.deep_dive.learn_over_time.modules.map(renderModule)}
                          </View>
                          
                          {/* Optional Advanced Lens */}
                          {selectedLens.deep_dive.learn_over_time.advanced_lens && (
                            <View style={styles.advancedLensContainer}>
                              <Text style={styles.advancedLensTitle}>
                                {selectedLens.deep_dive.learn_over_time.advanced_lens.title}
                              </Text>
                              <Text style={styles.advancedLensDescription}>
                                {selectedLens.deep_dive.learn_over_time.advanced_lens.description}
                              </Text>
                              <Text style={styles.advancedLensNote}>
                                {selectedLens.deep_dive.learn_over_time.advanced_lens.note}
                              </Text>
                            </View>
                          )}
                        </View>
                      )}

                      {selectedLens.deep_dive.reflection_themes && selectedLens.deep_dive.reflection_themes.length > 0 && (
                        <View style={styles.reflectionThemesContainer}>
                          <Text style={styles.themesLabel}>Reflection Themes</Text>
                          {selectedLens.deep_dive.reflection_themes.map((theme, index) => (
                            <View key={index} style={styles.themeItem}>
                              <Text style={styles.themeText}>{theme}</Text>
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

                      {/* Chat Section */}
                      <View style={styles.chatSection}>
                        <View style={styles.chatHeader}>
                          <Text style={styles.chatTitle}>Ask About {selectedLens.title}</Text>
                          {chatMessages.length > 0 && (
                            <TouchableOpacity onPress={clearChatHistory} style={styles.clearChatButton}>
                              <Ionicons name="trash-outline" size={18} color={COLORS.secondary} />
                              <Text style={styles.clearChatText}>Clear</Text>
                            </TouchableOpacity>
                          )}
                        </View>

                        {/* Chat Messages */}
                        {loadingChat ? (
                          <View style={styles.chatLoading}>
                            <ActivityIndicator size="small" color={COLORS.accent} />
                          </View>
                        ) : chatMessages.length > 0 ? (
                          <View style={styles.chatMessages}>
                            {chatMessages.map(renderChatMessage)}
                          </View>
                        ) : (
                          <View style={styles.chatEmpty}>
                            <Text style={styles.chatEmptyText}>
                              Have questions about {selectedLens.title}? Ask below and I'll help you explore.
                            </Text>
                          </View>
                        )}

                        {sendingMessage && (
                          <View style={styles.chatTyping}>
                            <ActivityIndicator size="small" color={COLORS.accent} />
                            <Text style={styles.chatTypingText}>Thinking...</Text>
                          </View>
                        )}
                      </View>
                    </View>
                  )}
                </ScrollView>

                {/* Chat Input - Only show in Deep Dive */}
                {viewMode === 'deepdive' && (
                  <>
                    {/* Computed Profile Block - Above Chat for Astrology */}
                    {/* Reads directly from user.computed_profile.astrology */}
                    {selectedLens?.id === 'true-sidereal-astrology' && (
                      <View style={styles.computedProfileBlock}>
                        <Text style={styles.computedProfileBlockTitle}>Your Sidereal Profile (Computed)</Text>
                        {userAstrologyProfile ? (
                          <View style={styles.computedProfileBlockContent}>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Sun:</Text>
                              <Text style={styles.computedProfileValue}>
                                {userAstrologyProfile.positions?.sun?.formatted || 'N/A'}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Moon:</Text>
                              <Text style={styles.computedProfileValue}>
                                {userAstrologyProfile.positions?.moon?.formatted || 'N/A'}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Ascendant:</Text>
                              <Text style={styles.computedProfileValue}>
                                {userAstrologyProfile.positions?.ascendant?.formatted || 'N/A'}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Ayanamsa:</Text>
                              <Text style={styles.computedProfileValue}>
                                {userAstrologyProfile.ayanamsa?.replace('_', '-') || 'N/A'}
                              </Text>
                            </View>
                          </View>
                        ) : loadingAstrologyProfile ? (
                          <ActivityIndicator size="small" color={COLORS.accent} />
                        ) : astrologyProfile?.has_profile && astrologyProfile.profile?.positions ? (
                          <View style={styles.computedProfileBlockContent}>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Sun:</Text>
                              <Text style={styles.computedProfileValue}>
                                {astrologyProfile.profile.positions.sun?.formatted || 'N/A'}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Moon:</Text>
                              <Text style={styles.computedProfileValue}>
                                {astrologyProfile.profile.positions.moon?.formatted || 'N/A'}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Ascendant:</Text>
                              <Text style={styles.computedProfileValue}>
                                {astrologyProfile.profile.positions.ascendant?.formatted || 'N/A'}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Ayanamsa:</Text>
                              <Text style={styles.computedProfileValue}>
                                {astrologyProfile.profile.ayanamsa?.replace('_', '-') || 'N/A'}
                              </Text>
                            </View>
                          </View>
                        ) : (
                          <Text style={styles.computedProfileBlockEmpty}>
                            Sidereal profile not computed yet.
                          </Text>
                        )}
                      </View>
                    )}

                    {/* Computed Profile Block - Above Chat for Human Design */}
                    {selectedLens?.id === 'human-design' && (
                      <View style={styles.computedProfileBlock}>
                        <Text style={styles.computedProfileBlockTitle}>Your Human Design Profile</Text>
                        {loadingHdProfile ? (
                          <ActivityIndicator size="small" color={COLORS.accent} />
                        ) : hdProfile?.has_profile && hdProfile.profile ? (
                          <View style={styles.computedProfileBlockContent}>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Type:</Text>
                              <Text style={styles.computedProfileValue}>
                                {hdProfile.profile.type || 'N/A'}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Strategy:</Text>
                              <Text style={styles.computedProfileValue}>
                                {hdProfile.profile.strategy || 'N/A'}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Authority:</Text>
                              <Text style={styles.computedProfileValue}>
                                {hdProfile.profile.authority || 'N/A'}
                              </Text>
                            </View>
                            {hdProfile.profile.profile && (
                              <View style={styles.computedProfileRow}>
                                <Text style={styles.computedProfileLabel}>Profile:</Text>
                                <Text style={styles.computedProfileValue}>
                                  {hdProfile.profile.profile}
                                </Text>
                              </View>
                            )}
                          </View>
                        ) : (
                          <Text style={styles.computedProfileBlockEmpty}>
                            Human Design profile not entered yet.
                          </Text>
                        )}
                      </View>
                    )}

                    {/* Computed Profile Block - Above Chat for Numerology */}
                    {selectedLens?.id === 'numerology' && (
                      <View style={styles.computedProfileBlock}>
                        <Text style={styles.computedProfileBlockTitle}>Your Numerology Profile</Text>
                        {loadingNumerologyProfile ? (
                          <ActivityIndicator size="small" color={COLORS.accent} />
                        ) : numerologyProfile?.has_profile && numerologyProfile.profile ? (
                          <View style={styles.computedProfileBlockContent}>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Life Path:</Text>
                              <Text style={styles.computedProfileValue}>
                                {numerologyProfile.profile.life_path || 'N/A'}
                              </Text>
                            </View>
                            {numerologyProfile.profile.expression && (
                              <View style={styles.computedProfileRow}>
                                <Text style={styles.computedProfileLabel}>Expression:</Text>
                                <Text style={styles.computedProfileValue}>
                                  {numerologyProfile.profile.expression}
                                </Text>
                              </View>
                            )}
                            {numerologyProfile.profile.soul_urge && (
                              <View style={styles.computedProfileRow}>
                                <Text style={styles.computedProfileLabel}>Soul Urge:</Text>
                                <Text style={styles.computedProfileValue}>
                                  {numerologyProfile.profile.soul_urge}
                                </Text>
                              </View>
                            )}
                            {numerologyProfile.profile.personal_year && (
                              <View style={styles.computedProfileRow}>
                                <Text style={styles.computedProfileLabel}>Personal Year:</Text>
                                <Text style={styles.computedProfileValue}>
                                  {numerologyProfile.profile.personal_year}
                                </Text>
                              </View>
                            )}
                          </View>
                        ) : (
                          <Text style={styles.computedProfileBlockEmpty}>
                            Numerology profile not entered yet.
                          </Text>
                        )}
                      </View>
                    )}

                    <View style={styles.chatInputContainer}>
                      <TextInput
                        style={styles.chatInput}
                        value={chatInput}
                        onChangeText={setChatInput}
                        placeholder={
                          selectedLens?.id === 'true-sidereal-astrology'
                            ? "Ask about your sidereal profile, or how it shows up in your life…"
                            : selectedLens?.id === 'human-design'
                            ? "Ask about your Human Design, or how it shows up in your life…"
                            : selectedLens?.id === 'numerology'
                            ? "Ask about your numerology profile, or how it shows up in your life…"
                            : selectedLens?.id === 'levels-of-consciousness'
                            ? "Ask about a stage, or how it shows up in your experience…"
                            : "Ask a question…"
                        }
                        placeholderTextColor={COLORS.secondary}
                        multiline
                        maxLength={500}
                      />
                      <TouchableOpacity
                        style={[styles.chatSendButton, (!chatInput.trim() || sendingMessage) && styles.chatSendButtonDisabled]}
                        onPress={sendChatMessage}
                        disabled={!chatInput.trim() || sendingMessage}
                      >
                        <Ionicons name="send" size={20} color={COLORS.white} />
                      </TouchableOpacity>
                    </View>
                  </>
                )}
              </View>
            ) : null}
          </KeyboardAvoidingView>
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
  modalKeyboard: {
    flex: 1,
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
  modalBody: {
    flex: 1,
  },
  modalScroll: {
    flex: 1,
  },
  modalContent: {
    padding: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  tabContainer: {
    flexDirection: 'row',
    marginHorizontal: SPACING.lg,
    marginTop: SPACING.md,
    marginBottom: SPACING.sm,
    backgroundColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    padding: 4,
  },
  tab: {
    flex: 1,
    paddingVertical: SPACING.sm,
    alignItems: 'center',
    borderRadius: BORDER_RADIUS.sm,
  },
  tabActive: {
    backgroundColor: COLORS.white,
  },
  tabText: {
    fontSize: 12,
    color: COLORS.secondary,
    fontWeight: '500',
  },
  tabTextActive: {
    color: COLORS.accent,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.accent,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: SPACING.md,
  },
  summaryText: {
    fontSize: 17,
    color: COLORS.primary,
    lineHeight: 26,
  },
  dynamicNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F5F8F3',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.lg,
    gap: SPACING.sm,
  },
  dynamicNoteText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.secondary,
    lineHeight: 22,
  },
  snapshotLoading: {
    alignItems: 'center',
    paddingVertical: SPACING.xl,
  },
  snapshotLoadingText: {
    marginTop: SPACING.md,
    fontSize: 14,
    color: COLORS.secondary,
  },
  snapshotContainer: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
  },
  snapshotText: {
    fontSize: 16,
    color: COLORS.primary,
    lineHeight: 26,
  },
  snapshotDisclaimer: {
    fontSize: 12,
    color: COLORS.secondary,
    marginTop: SPACING.md,
    fontStyle: 'italic',
    lineHeight: 18,
  },
  deepDiveDescription: {
    fontSize: 16,
    color: COLORS.primary,
    lineHeight: 26,
    marginBottom: SPACING.lg,
  },
  howMirrorUsesContainer: {
    backgroundColor: '#F0F4ED',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
  },
  howMirrorUsesLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.accent,
    marginBottom: SPACING.sm,
  },
  howMirrorUsesText: {
    fontSize: 15,
    color: COLORS.primary,
    lineHeight: 24,
  },
  structuredContainer: {
    marginTop: SPACING.md,
  },
  structuredNote: {
    backgroundColor: '#FFF9E6',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.lg,
  },
  structuredNoteText: {
    fontSize: 14,
    color: '#8B7355',
    lineHeight: 20,
  },
  structuredElement: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    marginBottom: SPACING.md,
  },
  structuredLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.sm,
  },
  structuredDescription: {
    fontSize: 15,
    color: COLORS.secondary,
    lineHeight: 22,
    marginBottom: SPACING.md,
  },
  patternsBox: {
    backgroundColor: '#F5F8F3',
    borderRadius: BORDER_RADIUS.sm,
    padding: SPACING.md,
  },
  patternsLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.accent,
    marginBottom: SPACING.xs,
  },
  patternsText: {
    fontSize: 14,
    color: COLORS.secondary,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  conceptsContainer: {
    marginTop: SPACING.lg,
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
  },
  conceptsLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  conceptItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SPACING.sm,
  },
  conceptBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.accent,
    marginTop: 8,
    marginRight: SPACING.sm,
  },
  conceptText: {
    flex: 1,
    fontSize: 15,
    color: COLORS.secondary,
    lineHeight: 22,
  },
  importantNote: {
    backgroundColor: '#FFF5F5',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    marginTop: SPACING.lg,
    borderLeftWidth: 3,
    borderLeftColor: '#E8B4B4',
  },
  importantNoteText: {
    fontSize: 14,
    color: '#8B6B6B',
    lineHeight: 22,
  },
  reflectionThemesContainer: {
    marginTop: SPACING.lg,
    backgroundColor: '#F9F9F7',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
  },
  themesLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.md,
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
  // Chat Styles
  chatSection: {
    marginTop: SPACING.xl,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingTop: SPACING.lg,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  chatTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  clearChatButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  clearChatText: {
    fontSize: 14,
    color: COLORS.secondary,
  },
  chatLoading: {
    padding: SPACING.lg,
    alignItems: 'center',
  },
  chatMessages: {
    gap: SPACING.sm,
  },
  chatMessage: {
    maxWidth: '85%',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
  },
  chatMessageUser: {
    alignSelf: 'flex-end',
    backgroundColor: COLORS.accent,
  },
  chatMessageAssistant: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chatMessageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  chatMessageTextUser: {
    color: COLORS.white,
  },
  chatMessageTextAssistant: {
    color: COLORS.primary,
  },
  chatEmpty: {
    padding: SPACING.lg,
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderStyle: 'dashed',
  },
  chatEmptyText: {
    fontSize: 14,
    color: COLORS.secondary,
    textAlign: 'center',
    lineHeight: 20,
  },
  chatTyping: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    marginTop: SPACING.sm,
    padding: SPACING.sm,
  },
  chatTypingText: {
    fontSize: 14,
    color: COLORS.secondary,
    fontStyle: 'italic',
  },
  // Computed Profile Block (above chat input)
  computedProfileBlock: {
    backgroundColor: '#F8F9FA',
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
  },
  computedProfileBlockTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: SPACING.sm,
  },
  computedProfileBlockContent: {
    gap: 4,
  },
  computedProfileRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  computedProfileLabel: {
    fontSize: 13,
    color: COLORS.secondary,
    fontWeight: '500',
  },
  computedProfileValue: {
    fontSize: 13,
    color: COLORS.primary,
    fontWeight: '600',
  },
  computedProfileBlockEmpty: {
    fontSize: 13,
    color: COLORS.secondary,
    fontStyle: 'italic',
  },
  chatInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    backgroundColor: COLORS.background,
    gap: SPACING.sm,
  },
  chatInput: {
    flex: 1,
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: SPACING.md,
    paddingVertical: SPACING.sm,
    fontSize: 16,
    color: COLORS.primary,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chatSendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.accent,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chatSendButtonDisabled: {
    opacity: 0.5,
  },
  // Learn Over Time Module Styles
  learnOverTimeContainer: {
    marginTop: SPACING.xl,
    marginBottom: SPACING.lg,
  },
  learnOverTimeTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.sm,
  },
  learnOverTimeIntro: {
    fontSize: 15,
    color: COLORS.secondary,
    lineHeight: 22,
    marginBottom: SPACING.lg,
  },
  modulesContainer: {
    gap: SPACING.md,
  },
  moduleCard: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  moduleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: SPACING.md,
    gap: SPACING.md,
  },
  moduleNumber: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.accent,
    justifyContent: 'center',
    alignItems: 'center',
  },
  moduleNumberText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
  moduleTitleContainer: {
    flex: 1,
  },
  moduleTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
  },
  moduleSubtitle: {
    fontSize: 13,
    color: COLORS.secondary,
    marginTop: 2,
  },
  moduleContent: {
    padding: SPACING.md,
    paddingTop: 0,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    gap: SPACING.md,
  },
  moduleNarrative: {
    fontSize: 15,
    color: COLORS.primary,
    lineHeight: 24,
    marginTop: SPACING.md,
  },
  moduleExamples: {
    backgroundColor: '#F9F9F7',
    borderRadius: BORDER_RADIUS.sm,
    padding: SPACING.md,
  },
  moduleExamplesLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.accent,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: SPACING.sm,
  },
  moduleExampleItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: SPACING.sm,
  },
  moduleExampleBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.accent,
    marginTop: 7,
    marginRight: SPACING.sm,
  },
  moduleExampleText: {
    flex: 1,
    fontSize: 14,
    color: COLORS.secondary,
    lineHeight: 20,
  },
  moduleReflection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#F5F8F3',
    borderRadius: BORDER_RADIUS.sm,
    padding: SPACING.md,
    gap: SPACING.sm,
  },
  moduleReflectionText: {
    flex: 1,
    fontSize: 15,
    color: COLORS.primary,
    lineHeight: 22,
    fontStyle: 'italic',
  },
  moduleExperiment: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFF9E6',
    borderRadius: BORDER_RADIUS.sm,
    padding: SPACING.md,
    gap: SPACING.sm,
  },
  moduleExperimentContent: {
    flex: 1,
  },
  moduleExperimentLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#8B7355',
    marginBottom: 4,
  },
  moduleExperimentText: {
    fontSize: 14,
    color: '#6B5A45',
    lineHeight: 20,
  },
  askModuleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.accent,
    borderRadius: BORDER_RADIUS.md,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    gap: SPACING.sm,
    marginTop: SPACING.sm,
  },
  askModuleButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
  advancedLensContainer: {
    marginTop: SPACING.lg,
    backgroundColor: '#F5F5F5',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    borderLeftWidth: 3,
    borderLeftColor: '#9B9B9B',
  },
  advancedLensTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.secondary,
    marginBottom: SPACING.sm,
  },
  advancedLensDescription: {
    fontSize: 14,
    color: COLORS.secondary,
    lineHeight: 20,
    marginBottom: SPACING.sm,
  },
  advancedLensNote: {
    fontSize: 12,
    color: '#888',
    fontStyle: 'italic',
  },
  // Your Sidereal Profile Styles (Top of Deep Dive)
  siderealProfileContainer: {
    backgroundColor: '#F8F9FA',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    marginBottom: SPACING.lg,
    borderWidth: 1,
    borderColor: '#E8E8E8',
  },
  siderealProfileTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.secondary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: SPACING.md,
    textAlign: 'center',
  },
  siderealProfileContent: {
    alignItems: 'center',
  },
  siderealProfileGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: SPACING.md,
  },
  siderealProfileItem: {
    alignItems: 'center',
    flex: 1,
  },
  siderealProfileLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: COLORS.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  siderealProfileSign: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.primary,
  },
  siderealProfileDegree: {
    fontSize: 13,
    color: COLORS.secondary,
    marginTop: 2,
  },
  siderealProfileAyanamsa: {
    fontSize: 12,
    color: COLORS.secondary,
    textAlign: 'center',
    fontStyle: 'italic',
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
    width: '100%',
  },
  siderealProfileEmpty: {
    alignItems: 'center',
    paddingVertical: SPACING.md,
  },
  siderealProfileEmptyText: {
    fontSize: 15,
    color: COLORS.secondary,
  },
  siderealProfileEmptyHint: {
    fontSize: 13,
    color: COLORS.secondary,
    opacity: 0.7,
    marginTop: 4,
  },
  // Human Design Profile Styles
  hdProfileGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: SPACING.sm,
  },
  hdProfileItem: {
    alignItems: 'center',
    width: '50%',
    marginBottom: SPACING.md,
  },
  hdProfileLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: COLORS.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  hdProfileValue: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
    textAlign: 'center',
  },
  hdProfileSubtext: {
    fontSize: 12,
    color: COLORS.secondary,
    textAlign: 'center',
    fontStyle: 'italic',
    paddingTop: SPACING.sm,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
    width: '100%',
  },
  // Numerology Profile Styles
  numerologyNumber: {
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.primary,
    textAlign: 'center',
  },
  // Personalized Insights Styles
  personalizedInsightsContainer: {
    marginBottom: SPACING.lg,
  },
  personalizedInsightsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  personalizedInsightCard: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: SPACING.sm,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.accent,
  },
  personalizedInsightHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.xs,
  },
  personalizedInsightPlanet: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
  },
  personalizedInsightSign: {
    fontSize: 13,
    color: COLORS.accent,
    fontWeight: '500',
  },
  personalizedInsightText: {
    fontSize: 15,
    color: COLORS.secondary,
    lineHeight: 22,
  },
  personalizedInsightBalance: {
    backgroundColor: '#F5F8F3',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.sm,
  },
  personalizedInsightBalanceText: {
    fontSize: 14,
    color: COLORS.primary,
    lineHeight: 20,
    fontStyle: 'italic',
  },
  personalizedInsightQuestion: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFF9E6',
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginTop: SPACING.sm,
    gap: SPACING.sm,
  },
  personalizedInsightQuestionText: {
    flex: 1,
    fontSize: 14,
    color: '#6B5A45',
    lineHeight: 20,
  },
  // Legacy Your Details styles (can be removed if not used elsewhere)
  yourDetailsContainer: {
    marginTop: SPACING.lg,
    marginBottom: SPACING.md,
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.lg,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  yourDetailsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: SPACING.md,
  },
  yourDetailsContent: {
    gap: SPACING.md,
  },
  yourDetailsRow: {
    flexDirection: 'row',
    gap: SPACING.md,
  },
  yourDetailsItem: {
    flex: 1,
    backgroundColor: '#F9F9F7',
    borderRadius: BORDER_RADIUS.sm,
    padding: SPACING.md,
  },
  yourDetailsLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  yourDetailsValue: {
    fontSize: 18,
    fontWeight: '500',
    color: COLORS.primary,
  },
  yourDetailsAyanamsa: {
    marginTop: SPACING.sm,
    alignItems: 'center',
  },
  yourDetailsAyanamsaLabel: {
    fontSize: 12,
    color: COLORS.secondary,
    fontStyle: 'italic',
  },
  yourDetailsEmpty: {
    alignItems: 'center',
    paddingVertical: SPACING.lg,
  },
  yourDetailsEmptyText: {
    fontSize: 16,
    color: COLORS.secondary,
    marginTop: SPACING.sm,
  },
  yourDetailsEmptySubtext: {
    fontSize: 14,
    color: COLORS.secondary,
    textAlign: 'center',
    marginTop: SPACING.xs,
    opacity: 0.7,
  },
});
