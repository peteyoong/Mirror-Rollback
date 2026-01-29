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
import DateTimePicker from '@react-native-community/datetimepicker';

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
  const { user, updateUser } = useAuth();
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
  
  // Birth Details Modal state
  const [birthDetailsModalVisible, setBirthDetailsModalVisible] = useState(false);
  const [birthDate, setBirthDate] = useState<Date>(new Date(1990, 0, 1, 12, 0));
  const [showBirthDatePicker, setShowBirthDatePicker] = useState(false);
  const [showBirthTimePicker, setShowBirthTimePicker] = useState(false);
  const [birthTzOffset, setBirthTzOffset] = useState('480');
  const [birthLat, setBirthLat] = useState('');
  const [birthLon, setBirthLon] = useState('');
  const [savingBirthDetails, setSavingBirthDetails] = useState(false);
  const [autoComputeAfterSave, setAutoComputeAfterSave] = useState(false);
  
  // Debug state (POC) - Detailed status tracking
  const [debugExpanded, setDebugExpanded] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{ success: boolean; message: string; response?: string } | null>(null);
  const [computeStatus, setComputeStatus] = useState<{ success: boolean; message: string; response?: string } | null>(null);
  const [runningCompute, setRunningCompute] = useState(false);
  const [showBirthDataForm, setShowBirthDataForm] = useState(false);
  const [birthFormData, setBirthFormData] = useState({
    birth_datetime_local: '',
    tz_offset_minutes: '480',
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
      setComputeStatus({ 
        success: false, 
        message: 'Birth fields missing from user record', 
        response: 'N/A - No birth data available to send to compute endpoint' 
      });
      return;
    }
    
    setRunningCompute(true);
    setComputeStatus(null);
    
    const requestPayload = {
      birth_datetime_local: userBirthData.birth_datetime_local,
      tz_offset_minutes: userBirthData.tz_offset_minutes,
      latitude: userBirthData.latitude,
      longitude: userBirthData.longitude,
      ayanamsa: 'FAGAN_BRADLEY',
    };
    
    try {
      const response = await api.post('/computed-profile/astrology', requestPayload);
      
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
        const positions = response.data.profile.positions;
        setComputeStatus({ 
          success: true, 
          message: 'Compute successful!',
          response: `Sun: ${positions?.sun?.formatted || 'N/A'}, Moon: ${positions?.moon?.formatted || 'N/A'}, Asc: ${positions?.ascendant?.formatted || 'N/A'}`
        });
      } else {
        setComputeStatus({ 
          success: false, 
          message: 'Compute returned no profile data',
          response: JSON.stringify(response.data, null, 2)
        });
      }
    } catch (error: any) {
      const errMsg = error.response?.data?.detail || error.message || 'Unknown error';
      const fullResponse = error.response?.data 
        ? JSON.stringify(error.response.data, null, 2) 
        : error.message || 'No response body';
      setComputeStatus({ 
        success: false, 
        message: `Compute failed: ${errMsg}`,
        response: fullResponse
      });
    } finally {
      setRunningCompute(false);
    }
  };

  // Save birth data to user record AND run compute
  const saveBirthData = async () => {
    if (!birthFormData.birth_datetime_local || !birthFormData.latitude || !birthFormData.longitude) {
      setSaveStatus({ success: false, message: 'Validation failed', response: 'Please fill in all birth data fields (datetime, latitude, longitude).' });
      return;
    }
    
    setSavingBirthData(true);
    setSaveStatus(null);
    setComputeStatus(null);
    
    const savePayload = {
      birth_datetime_local: birthFormData.birth_datetime_local,
      tz_offset_minutes: parseInt(birthFormData.tz_offset_minutes, 10),
      latitude: parseFloat(birthFormData.latitude),
      longitude: parseFloat(birthFormData.longitude),
    };
    
    try {
      // Step 1: Save birth data to user record
      const saveResponse = await api.post('/user/birth-data', savePayload);
      
      if (!saveResponse.data.success) {
        setSaveStatus({ 
          success: false, 
          message: 'Save returned success=false',
          response: JSON.stringify(saveResponse.data, null, 2)
        });
        return;
      }
      
      const savedBirthData = saveResponse.data.birth_data;
      setSaveStatus({ 
        success: true, 
        message: 'Birth data saved to database',
        response: JSON.stringify(savedBirthData, null, 2)
      });
      
      // Update user context with birth data immediately
      let updatedUser = user ? {
        ...user,
        birth_data: savedBirthData,
      } : null;
      
      if (updatedUser) {
        updateUser(updatedUser);
      }
      
      // Step 2: Run sidereal compute
      const computePayload = {
        birth_datetime_local: savedBirthData.birth_datetime_local,
        tz_offset_minutes: savedBirthData.tz_offset_minutes,
        latitude: savedBirthData.latitude,
        longitude: savedBirthData.longitude,
        ayanamsa: 'FAGAN_BRADLEY',
      };
      
      try {
        const computeResponse = await api.post('/computed-profile/astrology', computePayload);
        
        if (computeResponse.data.has_profile && computeResponse.data.profile) {
          // Update user context with computed profile
          const computedAstrology = {
            ayanamsa: computeResponse.data.profile.ayanamsa,
            positions: computeResponse.data.profile.positions,
            birth_datetime_local: savedBirthData.birth_datetime_local,
            latitude: savedBirthData.latitude,
            longitude: savedBirthData.longitude,
            computed_at: new Date().toISOString(),
          };
          
          if (updatedUser) {
            updatedUser = {
              ...updatedUser,
              computed_profile: {
                ...updatedUser.computed_profile,
                astrology: computedAstrology,
              },
            };
            updateUser(updatedUser);
          }
          
          const positions = computeResponse.data.profile.positions;
          setComputeStatus({ 
            success: true, 
            message: 'Compute successful!',
            response: `Sun: ${positions?.sun?.formatted || 'N/A'}, Moon: ${positions?.moon?.formatted || 'N/A'}, Asc: ${positions?.ascendant?.formatted || 'N/A'}`
          });
          setShowBirthDataForm(false);
        } else {
          setComputeStatus({ 
            success: false, 
            message: 'Compute returned no profile data',
            response: JSON.stringify(computeResponse.data, null, 2)
          });
        }
      } catch (computeError: any) {
        const computeErrMsg = computeError.response?.data?.detail || computeError.message || 'Unknown compute error';
        const fullResponse = computeError.response?.data 
          ? JSON.stringify(computeError.response.data, null, 2) 
          : computeError.message || 'No response body';
        setComputeStatus({ 
          success: false, 
          message: `Compute failed: ${computeErrMsg}`,
          response: fullResponse
        });
      }
      
    } catch (error: any) {
      const errMsg = error.response?.data?.detail || error.message || 'Unknown error';
      setComputeStatus({ success: false, message: `Failed to save birth data: ${errMsg}` });
    } finally {
      setSavingBirthData(false);
    }
  };

  // Open birth details modal with existing data if available
  const openBirthDetailsModal = () => {
    if (userBirthData) {
      // Pre-populate from existing data
      try {
        const existingDate = new Date(userBirthData.birth_datetime_local);
        setBirthDate(existingDate);
      } catch {
        setBirthDate(new Date(1990, 0, 1, 12, 0));
      }
      setBirthTzOffset(String(userBirthData.tz_offset_minutes || 480));
      setBirthLat(String(userBirthData.latitude || ''));
      setBirthLon(String(userBirthData.longitude || ''));
    } else {
      // Reset to defaults
      setBirthDate(new Date(1990, 0, 1, 12, 0));
      setBirthTzOffset('480');
      setBirthLat('');
      setBirthLon('');
    }
    setBirthDetailsModalVisible(true);
  };

  // Common locations for quick selection
  const QUICK_LOCATIONS = [
    { name: 'New York, USA', lat: 40.7128, lon: -74.0060 },
    { name: 'Los Angeles, USA', lat: 34.0522, lon: -118.2437 },
    { name: 'London, UK', lat: 51.5074, lon: -0.1278 },
    { name: 'Sydney, Australia', lat: -33.8688, lon: 151.2093 },
    { name: 'Mumbai, India', lat: 19.0760, lon: 72.8777 },
    { name: 'Tokyo, Japan', lat: 35.6762, lon: 139.6503 },
  ];

  // Save birth details and optionally run compute
  const saveBirthDetailsAndCompute = async () => {
    if (!birthLat || !birthLon) {
      Alert.alert('Missing Location', 'Please enter latitude and longitude or select a city.');
      return;
    }
    
    setSavingBirthDetails(true);
    try {
      const birthDatetimeISO = birthDate.toISOString();
      
      const response = await api.post('/user/birth-data', {
        birth_datetime_local: birthDatetimeISO,
        tz_offset_minutes: parseInt(birthTzOffset, 10),
        latitude: parseFloat(birthLat),
        longitude: parseFloat(birthLon),
      });
      
      if (response.data.success && user) {
        const updatedBirthData = response.data.birth_data;
        
        // Update user context with birth data
        let updatedUser = {
          ...user,
          birth_data: updatedBirthData,
        };
        
        // Now run compute automatically
        try {
          const computeResponse = await api.post('/computed-profile/astrology', {
            birth_datetime_local: updatedBirthData.birth_datetime_local,
            tz_offset_minutes: updatedBirthData.tz_offset_minutes,
            latitude: updatedBirthData.latitude,
            longitude: updatedBirthData.longitude,
            ayanamsa: 'FAGAN_BRADLEY',
          });
          
          if (computeResponse.data.has_profile && computeResponse.data.profile) {
            // Update user with computed profile
            updatedUser = {
              ...updatedUser,
              computed_profile: {
                ...updatedUser.computed_profile,
                astrology: {
                  ayanamsa: computeResponse.data.profile.ayanamsa,
                  positions: computeResponse.data.profile.positions,
                  birth_datetime_local: updatedBirthData.birth_datetime_local,
                  latitude: updatedBirthData.latitude,
                  longitude: updatedBirthData.longitude,
                  computed_at: new Date().toISOString(),
                },
              },
            };
            setComputeStatus({ success: true, message: 'Profile computed successfully!' });
          }
        } catch (computeErr: any) {
          console.error('Auto-compute failed:', computeErr);
          setComputeStatus({ success: false, message: 'Birth data saved but compute failed.' });
        }
        
        updateUser(updatedUser);
        setBirthDetailsModalVisible(false);
        
        // Navigate to Astrology lens and show deep dive
        const astrologyLens = lenses.find(l => l.id === 'true-sidereal-astrology');
        if (astrologyLens) {
          openLensDetail('true-sidereal-astrology');
          setTimeout(() => setViewMode('deepdive'), 500);
        }
        
        Alert.alert('Success', 'Birth details saved and sidereal profile computed!');
      }
    } catch (error: any) {
      Alert.alert('Error', 'Failed to save birth details.');
    } finally {
      setSavingBirthDetails(false);
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
        <TouchableOpacity 
          style={styles.headerIconButton}
          onPress={openBirthDetailsModal}
        >
          <Ionicons name="person-circle-outline" size={28} color={COLORS.primary} />
        </TouchableOpacity>
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

                      {/* DEBUG SECTION (POC) - Only for Astrology */}
                      {selectedLens.id === 'true-sidereal-astrology' && (
                        <View style={styles.debugContainer}>
                          <TouchableOpacity 
                            style={styles.debugHeader}
                            onPress={() => setDebugExpanded(!debugExpanded)}
                          >
                            <Text style={styles.debugHeaderText}>Debug (POC)</Text>
                            <Ionicons 
                              name={debugExpanded ? 'chevron-up' : 'chevron-down'} 
                              size={18} 
                              color="#888"
                            />
                          </TouchableOpacity>
                          
                          {debugExpanded && (
                            <View style={styles.debugContent}>
                              {/* Birth Data Fields */}
                              <Text style={styles.debugSubtitle}>Stored Birth Fields (raw):</Text>
                              {userBirthData ? (
                                <View style={styles.debugCodeBlock}>
                                  <Text style={styles.debugCode}>birth_datetime_local: {userBirthData.birth_datetime_local}</Text>
                                  <Text style={styles.debugCode}>tz_offset_minutes: {userBirthData.tz_offset_minutes}</Text>
                                  <Text style={styles.debugCode}>latitude: {userBirthData.latitude}</Text>
                                  <Text style={styles.debugCode}>longitude: {userBirthData.longitude}</Text>
                                </View>
                              ) : (
                                <View style={styles.debugWarning}>
                                  <Ionicons name="warning" size={16} color="#D97706" />
                                  <Text style={styles.debugWarningText}>Birth fields missing from user record</Text>
                                </View>
                              )}
                              
                              {/* Computed Profile Status */}
                              <Text style={styles.debugSubtitle}>computed_profile exists:</Text>
                              <Text style={[styles.debugCode, { color: userAstrologyProfile ? '#10B981' : '#EF4444' }]}>
                                {userAstrologyProfile ? 'true' : 'false'}
                              </Text>
                              
                              {/* Compute Endpoint */}
                              <Text style={styles.debugSubtitle}>Compute Endpoint:</Text>
                              <Text style={styles.debugCode}>/api/computed-profile/astrology (POST)</Text>
                              
                              {/* Last Compute Status */}
                              {computeStatus && (
                                <>
                                  <Text style={styles.debugSubtitle}>Last Compute Status:</Text>
                                  <View style={[styles.debugStatusBadge, { backgroundColor: computeStatus.success ? '#D1FAE5' : '#FEE2E2' }]}>
                                    <Text style={[styles.debugStatusText, { color: computeStatus.success ? '#065F46' : '#991B1B' }]}>
                                      {computeStatus.success ? '✓ ' : '✗ '}{computeStatus.message}
                                    </Text>
                                  </View>
                                </>
                              )}
                              
                              {/* Run Compute Button */}
                              {userBirthData ? (
                                <TouchableOpacity 
                                  style={[styles.debugButton, runningCompute && styles.debugButtonDisabled]}
                                  onPress={runSiderealCompute}
                                  disabled={runningCompute}
                                >
                                  {runningCompute ? (
                                    <ActivityIndicator size="small" color="#FFF" />
                                  ) : (
                                    <Text style={styles.debugButtonText}>Run Sidereal Compute Now</Text>
                                  )}
                                </TouchableOpacity>
                              ) : (
                                <TouchableOpacity 
                                  style={styles.debugButtonSecondary}
                                  onPress={() => setShowBirthDataForm(true)}
                                >
                                  <Text style={styles.debugButtonSecondaryText}>Add/Edit Birth Details</Text>
                                </TouchableOpacity>
                              )}
                              
                              {/* Birth Data Form */}
                              {showBirthDataForm && (
                                <View style={styles.debugForm}>
                                  <Text style={styles.debugFormTitle}>Enter Birth Data</Text>
                                  <Text style={styles.debugFormSubtitle}>
                                    Data will be saved to your user record and compute will run automatically.
                                  </Text>
                                  
                                  <Text style={styles.debugFormLabel}>Birth DateTime (ISO format)</Text>
                                  <TextInput
                                    style={styles.debugFormInput}
                                    value={birthFormData.birth_datetime_local}
                                    onChangeText={(v) => setBirthFormData({...birthFormData, birth_datetime_local: v})}
                                    placeholder="1990-05-15T10:30:00"
                                    placeholderTextColor="#999"
                                  />
                                  
                                  <Text style={styles.debugFormLabel}>TZ Offset (minutes from UTC)</Text>
                                  <TextInput
                                    style={styles.debugFormInput}
                                    value={birthFormData.tz_offset_minutes}
                                    onChangeText={(v) => setBirthFormData({...birthFormData, tz_offset_minutes: v})}
                                    placeholder="480"
                                    placeholderTextColor="#999"
                                    keyboardType="numeric"
                                  />
                                  <Text style={styles.debugFormHint}>e.g., -300 (EST), -420 (PDT), 0 (UTC), 330 (IST), 480 (PST)</Text>
                                  
                                  <Text style={styles.debugFormLabel}>Latitude</Text>
                                  <TextInput
                                    style={styles.debugFormInput}
                                    value={birthFormData.latitude}
                                    onChangeText={(v) => setBirthFormData({...birthFormData, latitude: v})}
                                    placeholder="40.7128"
                                    placeholderTextColor="#999"
                                    keyboardType="decimal-pad"
                                  />
                                  
                                  <Text style={styles.debugFormLabel}>Longitude</Text>
                                  <TextInput
                                    style={styles.debugFormInput}
                                    value={birthFormData.longitude}
                                    onChangeText={(v) => setBirthFormData({...birthFormData, longitude: v})}
                                    placeholder="-74.0060"
                                    placeholderTextColor="#999"
                                    keyboardType="decimal-pad"
                                  />
                                  
                                  <View style={styles.debugFormButtons}>
                                    <TouchableOpacity 
                                      style={styles.debugButtonSecondary}
                                      onPress={() => {
                                        setShowBirthDataForm(false);
                                        setComputeStatus(null);
                                      }}
                                    >
                                      <Text style={styles.debugButtonSecondaryText}>Cancel</Text>
                                    </TouchableOpacity>
                                    <TouchableOpacity 
                                      style={[styles.debugButton, savingBirthData && styles.debugButtonDisabled]}
                                      onPress={saveBirthData}
                                      disabled={savingBirthData}
                                    >
                                      {savingBirthData ? (
                                        <ActivityIndicator size="small" color="#FFF" />
                                      ) : (
                                        <Text style={styles.debugButtonText}>Save & Compute</Text>
                                      )}
                                    </TouchableOpacity>
                                  </View>
                                </View>
                              )}
                            </View>
                          )}
                        </View>
                      )}

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

      {/* Birth Details Modal */}
      <Modal
        visible={birthDetailsModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setBirthDetailsModalVisible(false)}
      >
        <SafeAreaView style={styles.birthDetailsModal}>
          <View style={styles.birthDetailsHeader}>
            <TouchableOpacity onPress={() => setBirthDetailsModalVisible(false)}>
              <Ionicons name="close" size={28} color={COLORS.primary} />
            </TouchableOpacity>
            <Text style={styles.birthDetailsTitle}>Birth Details</Text>
            <View style={{ width: 28 }} />
          </View>

          <ScrollView style={styles.birthDetailsContent} showsVerticalScrollIndicator={false}>
            <Text style={styles.birthDetailsSubtitle}>
              Enter your birth details to compute your True Sidereal profile
            </Text>

            {/* Date Selection */}
            <View style={styles.birthDetailsField}>
              <Text style={styles.birthDetailsLabel}>Birth Date</Text>
              <TouchableOpacity 
                style={styles.birthDetailsInput} 
                onPress={() => setShowBirthDatePicker(true)}
              >
                <Text style={styles.birthDetailsInputText}>
                  {birthDate.toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </Text>
                <Ionicons name="calendar-outline" size={20} color={COLORS.secondary} />
              </TouchableOpacity>
            </View>

            {/* Time Selection */}
            <View style={styles.birthDetailsField}>
              <Text style={styles.birthDetailsLabel}>Birth Time</Text>
              <TouchableOpacity 
                style={styles.birthDetailsInput} 
                onPress={() => setShowBirthTimePicker(true)}
              >
                <Text style={styles.birthDetailsInputText}>
                  {birthDate.toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </Text>
                <Ionicons name="time-outline" size={20} color={COLORS.secondary} />
              </TouchableOpacity>
            </View>

            {/* Timezone Offset */}
            <View style={styles.birthDetailsField}>
              <Text style={styles.birthDetailsLabel}>Timezone Offset (minutes from UTC)</Text>
              <TextInput
                style={styles.birthDetailsTextInput}
                value={birthTzOffset}
                onChangeText={setBirthTzOffset}
                placeholder="480 (for PST)"
                placeholderTextColor="#999"
                keyboardType="numeric"
              />
              <Text style={styles.birthDetailsHint}>
                Examples: -300 (EST), -420 (PDT), 0 (UTC), 330 (IST), 480 (PST)
              </Text>
            </View>

            {/* Quick Location Selection */}
            <View style={styles.birthDetailsField}>
              <Text style={styles.birthDetailsLabel}>Birth Location</Text>
              <Text style={styles.birthDetailsHint}>Select a city or enter coordinates manually</Text>
              <View style={styles.quickLocationGrid}>
                {QUICK_LOCATIONS.map((loc) => (
                  <TouchableOpacity
                    key={loc.name}
                    style={[
                      styles.quickLocationChip,
                      birthLat === String(loc.lat) && birthLon === String(loc.lon) && styles.quickLocationChipSelected
                    ]}
                    onPress={() => {
                      setBirthLat(String(loc.lat));
                      setBirthLon(String(loc.lon));
                    }}
                  >
                    <Text style={[
                      styles.quickLocationChipText,
                      birthLat === String(loc.lat) && birthLon === String(loc.lon) && styles.quickLocationChipTextSelected
                    ]}>{loc.name}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Manual Coordinates */}
            <View style={styles.birthDetailsRow}>
              <View style={[styles.birthDetailsField, { flex: 1, marginRight: SPACING.sm }]}>
                <Text style={styles.birthDetailsLabel}>Latitude</Text>
                <TextInput
                  style={styles.birthDetailsTextInput}
                  value={birthLat}
                  onChangeText={setBirthLat}
                  placeholder="40.7128"
                  placeholderTextColor="#999"
                  keyboardType="decimal-pad"
                />
              </View>
              <View style={[styles.birthDetailsField, { flex: 1, marginLeft: SPACING.sm }]}>
                <Text style={styles.birthDetailsLabel}>Longitude</Text>
                <TextInput
                  style={styles.birthDetailsTextInput}
                  value={birthLon}
                  onChangeText={setBirthLon}
                  placeholder="-74.0060"
                  placeholderTextColor="#999"
                  keyboardType="decimal-pad"
                />
              </View>
            </View>

            {/* Current Status */}
            {userBirthData && (
              <View style={styles.currentBirthDataBox}>
                <Text style={styles.currentBirthDataTitle}>Currently Saved:</Text>
                <Text style={styles.currentBirthDataText}>
                  {new Date(userBirthData.birth_datetime_local).toLocaleString()}
                </Text>
                <Text style={styles.currentBirthDataText}>
                  Lat: {userBirthData.latitude}, Lon: {userBirthData.longitude}
                </Text>
              </View>
            )}

            {/* Save Button */}
            <TouchableOpacity
              style={[styles.birthDetailsSaveButton, savingBirthDetails && styles.birthDetailsSaveButtonDisabled]}
              onPress={saveBirthDetailsAndCompute}
              disabled={savingBirthDetails}
            >
              {savingBirthDetails ? (
                <ActivityIndicator color={COLORS.white} />
              ) : (
                <>
                  <Ionicons name="calculator-outline" size={20} color={COLORS.white} />
                  <Text style={styles.birthDetailsSaveButtonText}>Save & Compute Sidereal Profile</Text>
                </>
              )}
            </TouchableOpacity>
          </ScrollView>

          {/* Date/Time Pickers */}
          {showBirthDatePicker && (
            <DateTimePicker
              value={birthDate}
              mode="date"
              display={Platform.OS === 'ios' ? 'spinner' : 'default'}
              onChange={(event, selectedDate) => {
                setShowBirthDatePicker(false);
                if (selectedDate) {
                  const newDate = new Date(birthDate);
                  newDate.setFullYear(selectedDate.getFullYear());
                  newDate.setMonth(selectedDate.getMonth());
                  newDate.setDate(selectedDate.getDate());
                  setBirthDate(newDate);
                }
              }}
              maximumDate={new Date()}
              minimumDate={new Date(1900, 0, 1)}
            />
          )}
          {showBirthTimePicker && (
            <DateTimePicker
              value={birthDate}
              mode="time"
              display={Platform.OS === 'ios' ? 'spinner' : 'default'}
              onChange={(event, selectedTime) => {
                setShowBirthTimePicker(false);
                if (selectedTime) {
                  const newDate = new Date(birthDate);
                  newDate.setHours(selectedTime.getHours());
                  newDate.setMinutes(selectedTime.getMinutes());
                  setBirthDate(newDate);
                }
              }}
            />
          )}
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
  // Header Icon Button
  headerIconButton: {
    padding: SPACING.xs,
  },
  // Birth Details Modal Styles
  birthDetailsModal: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  birthDetailsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  birthDetailsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.primary,
  },
  birthDetailsContent: {
    flex: 1,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.lg,
  },
  birthDetailsSubtitle: {
    fontSize: 15,
    color: COLORS.secondary,
    marginBottom: SPACING.xl,
    lineHeight: 22,
  },
  birthDetailsField: {
    marginBottom: SPACING.lg,
  },
  birthDetailsLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.primary,
    marginBottom: SPACING.xs,
  },
  birthDetailsInput: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  birthDetailsInputText: {
    fontSize: 16,
    color: COLORS.primary,
  },
  birthDetailsTextInput: {
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
    fontSize: 16,
    color: COLORS.primary,
  },
  birthDetailsHint: {
    fontSize: 12,
    color: COLORS.secondary,
    marginTop: SPACING.xs,
  },
  birthDetailsRow: {
    flexDirection: 'row',
    marginBottom: SPACING.lg,
  },
  quickLocationGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
    marginTop: SPACING.sm,
  },
  quickLocationChip: {
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  quickLocationChipSelected: {
    backgroundColor: '#F0FDF4',
    borderColor: COLORS.accent,
  },
  quickLocationChipText: {
    fontSize: 13,
    color: COLORS.primary,
  },
  quickLocationChipTextSelected: {
    color: COLORS.accent,
    fontWeight: '500',
  },
  currentBirthDataBox: {
    backgroundColor: '#F0FDF4',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: '#BBF7D0',
    marginBottom: SPACING.lg,
  },
  currentBirthDataTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#166534',
    marginBottom: SPACING.xs,
  },
  currentBirthDataText: {
    fontSize: 13,
    color: '#166534',
  },
  birthDetailsSaveButton: {
    backgroundColor: COLORS.accent,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: SPACING.sm,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.xxl,
  },
  birthDetailsSaveButtonDisabled: {
    opacity: 0.6,
  },
  birthDetailsSaveButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  // Debug Section Styles (POC)
  debugContainer: {
    backgroundColor: '#FEF3C7',
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.md,
    borderWidth: 1,
    borderColor: '#F59E0B',
  },
  debugHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: SPACING.md,
  },
  debugHeaderText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#92400E',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  debugContent: {
    paddingHorizontal: SPACING.md,
    paddingBottom: SPACING.md,
    borderTopWidth: 1,
    borderTopColor: '#FCD34D',
  },
  debugSubtitle: {
    fontSize: 11,
    fontWeight: '600',
    color: '#78350F',
    marginTop: SPACING.md,
    marginBottom: SPACING.xs,
    textTransform: 'uppercase',
  },
  debugCodeBlock: {
    backgroundColor: '#FFFBEB',
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  debugCode: {
    fontSize: 11,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    color: '#451A03',
    lineHeight: 18,
  },
  debugWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    backgroundColor: '#FEF3C7',
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
  },
  debugWarningText: {
    fontSize: 12,
    color: '#92400E',
    fontWeight: '500',
  },
  debugStatusBadge: {
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    marginTop: SPACING.xs,
  },
  debugStatusText: {
    fontSize: 12,
    fontWeight: '500',
  },
  debugButton: {
    backgroundColor: '#2563EB',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.sm,
    alignItems: 'center',
    marginTop: SPACING.md,
  },
  debugButtonDisabled: {
    opacity: 0.6,
  },
  debugButtonText: {
    color: '#FFF',
    fontSize: 13,
    fontWeight: '600',
  },
  debugButtonSecondary: {
    backgroundColor: '#F3F4F6',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.sm,
    alignItems: 'center',
    marginTop: SPACING.md,
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  debugButtonSecondaryText: {
    color: '#374151',
    fontSize: 13,
    fontWeight: '500',
  },
  debugForm: {
    marginTop: SPACING.md,
    padding: SPACING.md,
    backgroundColor: '#FFFBEB',
    borderRadius: BORDER_RADIUS.sm,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  debugFormTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#78350F',
    marginBottom: SPACING.xs,
  },
  debugFormSubtitle: {
    fontSize: 11,
    color: '#92400E',
    marginBottom: SPACING.md,
  },
  debugFormLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: '#78350F',
    marginTop: SPACING.sm,
    marginBottom: 4,
  },
  debugFormHint: {
    fontSize: 10,
    color: '#92400E',
    marginTop: 2,
    fontStyle: 'italic',
  },
  debugFormInput: {
    backgroundColor: '#FFF',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: BORDER_RADIUS.sm,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    fontSize: 13,
    color: '#1F2937',
  },
  debugFormButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: SPACING.sm,
    marginTop: SPACING.md,
  },
});
