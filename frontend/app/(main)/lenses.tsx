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
  const [birthModalError, setBirthModalError] = useState<{ type: 'save' | 'compute'; message: string; response?: string } | null>(null);
  const [savedUserId, setSavedUserId] = useState<string | null>(null);
  const [locationManuallyEdited, setLocationManuallyEdited] = useState(false);
  const [showManualLocationEntry, setShowManualLocationEntry] = useState(false);
  
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
  
  // Computed profile from user context (SINGLE SOURCE OF TRUTH)
  // All astrology data comes from the persisted user record only
  const userAstrologyProfile = user?.computed_profile?.astrology;
  const userBirthData = user?.birth_data;
  
  // Human Design profile state (separate collection - not yet unified)
  const [hdProfile, setHdProfile] = useState<HumanDesignProfile | null>(null);
  const [loadingHdProfile, setLoadingHdProfile] = useState(false);

  // Numerology profile state (separate collection - not yet unified)
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
      const fullResponse = error.response?.data 
        ? JSON.stringify(error.response.data, null, 2) 
        : error.message || 'No response body';
      setSaveStatus({ 
        success: false, 
        message: `Failed to save birth data: ${errMsg}`,
        response: fullResponse
      });
    } finally {
      setSavingBirthData(false);
    }
  };

  // Open birth details modal with existing data if available
  const openBirthDetailsModal = () => {
    // Clear any previous errors and state
    setBirthModalError(null);
    setSavedUserId(null);
    setLocationManuallyEdited(false);
    setShowManualLocationEntry(false);
    setSelectedCountry('');
    setSelectedCity('');
    setShowCountryPicker(false);
    setShowCityPicker(false);
    
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
      
      // Try to find matching country/city from existing coordinates
      const lat = userBirthData.latitude;
      const lon = userBirthData.longitude;
      if (lat && lon) {
        let found = false;
        for (const [country, cities] of Object.entries(CITY_DATABASE)) {
          const matchingCity = cities.find(c => 
            Math.abs(c.lat - lat) < 0.1 && Math.abs(c.lon - lon) < 0.1
          );
          if (matchingCity) {
            setSelectedCountry(country);
            setSelectedCity(matchingCity.city);
            found = true;
            break;
          }
        }
        // If no matching city found, show manual entry mode
        if (!found) {
          setShowManualLocationEntry(true);
          setLocationManuallyEdited(true);
        }
      }
    } else {
      // Reset to defaults
      setBirthDate(new Date(1990, 0, 1, 12, 0));
      setBirthTzOffset('480');
      setBirthLat('');
      setBirthLon('');
    }
    setBirthDetailsModalVisible(true);
  };
  
  // Handle manual lat/lon edits - prevent chips from overriding
  const handleLatChange = (value: string) => {
    setBirthLat(value);
    setLocationManuallyEdited(true);
  };
  
  const handleLonChange = (value: string) => {
    setBirthLon(value);
    setLocationManuallyEdited(true);
  };
  
  // Handle chip selection - only update if user explicitly taps
  const handleCitySelect = (lat: number, lon: number) => {
    setBirthLat(String(lat));
    setBirthLon(String(lon));
    setLocationManuallyEdited(false); // Reset since user chose a preset
  };

  // Location search state (OpenStreetMap Nominatim)
  const [locationSearch, setLocationSearch] = useState('');
  const [locationSuggestions, setLocationSuggestions] = useState<Array<{
    display_name: string;
    lat: string;
    lon: string;
    place_id: number;
  }>>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  const searchTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  
  // Search for locations using OpenStreetMap Nominatim API
  const searchLocation = async (query: string) => {
    if (query.length < 3) {
      setLocationSuggestions([]);
      return;
    }
    
    setIsSearching(true);
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=8`,
        {
          headers: {
            'Accept': 'application/json',
            'User-Agent': 'ProjectMirror/1.0'
          }
        }
      );
      const data = await response.json();
      setLocationSuggestions(data);
    } catch (error) {
      console.error('Location search failed:', error);
      setLocationSuggestions([]);
    } finally {
      setIsSearching(false);
    }
  };
  
  // Debounced search handler
  const handleLocationSearchChange = (text: string) => {
    setLocationSearch(text);
    
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    
    // Debounce search by 500ms
    searchTimeoutRef.current = setTimeout(() => {
      searchLocation(text);
    }, 500);
  };
  
  // Calculate timezone offset from longitude (approximate)
  const calculateTimezoneFromLon = (longitude: number): number => {
    // Each 15 degrees of longitude = 1 hour (60 minutes)
    // This is approximate but works for most cases
    return Math.round(longitude / 15) * 60;
  };
  
  // Handle location selection from suggestions
  const handleLocationSelect = (location: { display_name: string; lat: string; lon: string }) => {
    const lat = parseFloat(location.lat);
    const lon = parseFloat(location.lon);
    const tzOffset = calculateTimezoneFromLon(lon);
    
    setSelectedLocation(location.display_name);
    setBirthLat(location.lat);
    setBirthLon(location.lon);
    setBirthTzOffset(String(tzOffset));
    setLocationSearch('');
    setLocationSuggestions([]);
    setLocationManuallyEdited(false);
    setShowManualLocationEntry(false);
  };
  
  // Format timezone for display
  const formatTimezone = (minutes: number): string => {
    const hours = Math.floor(Math.abs(minutes) / 60);
    const mins = Math.abs(minutes) % 60;
    const sign = minutes >= 0 ? '+' : '-';
    return `UTC${sign}${hours}${mins > 0 ? ':' + String(mins).padStart(2, '0') : ''}`;
  };

  // Save birth details and optionally run compute
  const saveBirthDetailsAndCompute = async () => {
    if (!birthLat || !birthLon) {
      setBirthModalError({ type: 'save', message: 'Missing location', response: 'Please enter latitude and longitude or select a city.' });
      return;
    }
    
    setSavingBirthDetails(true);
    setBirthModalError(null);
    
    try {
      const birthDatetimeISO = birthDate.toISOString();
      
      // Step 1: Save birth data to user record
      const saveResponse = await api.post('/user/birth-data', {
        birth_datetime_local: birthDatetimeISO,
        tz_offset_minutes: parseInt(birthTzOffset, 10),
        latitude: parseFloat(birthLat),
        longitude: parseFloat(birthLon),
      });
      
      if (!saveResponse.data.success) {
        setBirthModalError({ 
          type: 'save', 
          message: 'Failed to save birth data',
          response: JSON.stringify(saveResponse.data, null, 2)
        });
        return;
      }
      
      const savedBirthData = saveResponse.data.birth_data;
      const userId = saveResponse.data.user_id || user?.id;
      
      // Show saved user_id for debug
      setSavedUserId(userId);
      
      // Update user context with birth data immediately
      let updatedUser = user ? {
        ...user,
        birth_data: savedBirthData,
      } : null;
      
      if (updatedUser) {
        updateUser(updatedUser);
      }
      
      // Update save status for debug panel
      setSaveStatus({ success: true, message: 'Birth data saved to user record' });
      
      // Step 2: Run sidereal compute
      try {
        const computeResponse = await api.post('/computed-profile/astrology', {
          birth_datetime_local: savedBirthData.birth_datetime_local,
          tz_offset_minutes: savedBirthData.tz_offset_minutes,
          latitude: savedBirthData.latitude,
          longitude: savedBirthData.longitude,
          ayanamsa: 'FAGAN_BRADLEY',
        });
        
        if (computeResponse.data.has_profile && computeResponse.data.profile) {
          // Update user with computed profile
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
          
          // Also update debug panel status
          setComputeStatus({ success: true, message: 'Profile computed successfully!' });
          
          // Don't close modal immediately - let user see success state
          // User can manually close after seeing confirmation
          
          Alert.alert('Success', 'Birth details saved and sidereal profile computed!');
        } else {
          setBirthModalError({ 
            type: 'compute', 
            message: 'Compute returned no profile data',
            response: JSON.stringify(computeResponse.data, null, 2)
          });
        }
      } catch (computeErr: any) {
        const errMsg = computeErr.response?.data?.detail || computeErr.message || 'Unknown compute error';
        const fullResponse = computeErr.response?.data 
          ? JSON.stringify(computeErr.response.data, null, 2) 
          : computeErr.message || 'No response body';
        setBirthModalError({ 
          type: 'compute', 
          message: `Compute failed: ${errMsg}`,
          response: fullResponse
        });
        setComputeStatus({ success: false, message: 'Birth data saved but compute failed.' });
      }
      
    } catch (error: any) {
      const errMsg = error.response?.data?.detail || error.message || 'Unknown error';
      const fullResponse = error.response?.data 
        ? JSON.stringify(error.response.data, null, 2) 
        : error.message || 'No response body';
      setBirthModalError({ 
        type: 'save', 
        message: `Failed to save: ${errMsg}`,
        response: fullResponse
      });
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

  // NOTE: fetchAstrologyProfile removed - astrology data comes from user context only
  // This ensures single source of truth from user.computed_profile.astrology

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
    // Reset status for new lens view
    setSaveStatus(null);
    setComputeStatus(null);
    setHdProfile(null);
    setNumerologyProfile(null);
    try {
      const response = await api.get(`/lenses/${lensId}`);
      setSelectedLens(response.data);
      // Fetch chat history in background
      fetchChatHistory(lensId);
      // NOTE: Astrology profile comes from user context (userAstrologyProfile)
      // No separate fetch needed - single source of truth
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
    setSaveStatus(null);
    setComputeStatus(null);
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
                              {/* Section 1: Stored Birth Fields (raw) */}
                              <View style={styles.debugSection}>
                                <Text style={styles.debugSectionTitle}>1. Stored Birth Fields (raw from user record)</Text>
                                {userBirthData ? (
                                  <View style={styles.debugCodeBlock}>
                                    <Text style={styles.debugCode}>birth_datetime_local: {userBirthData.birth_datetime_local}</Text>
                                    <Text style={styles.debugCode}>tz_offset_minutes: {userBirthData.tz_offset_minutes}</Text>
                                    <Text style={styles.debugCode}>latitude: {userBirthData.latitude}</Text>
                                    <Text style={styles.debugCode}>longitude: {userBirthData.longitude}</Text>
                                    {userBirthData.updated_at && (
                                      <Text style={styles.debugCodeMuted}>updated_at: {userBirthData.updated_at}</Text>
                                    )}
                                  </View>
                                ) : (
                                  <View style={styles.debugWarning}>
                                    <Ionicons name="warning" size={16} color="#D97706" />
                                    <Text style={styles.debugWarningText}>No birth fields stored in user record</Text>
                                  </View>
                                )}
                              </View>
                              
                              {/* Section 2: Computed Profile Status */}
                              <View style={styles.debugSection}>
                                <Text style={styles.debugSectionTitle}>2. Computed Profile State</Text>
                                <View style={styles.debugCodeBlock}>
                                  <Text style={styles.debugCode}>
                                    computed_profile.astrology exists: {' '}
                                    <Text style={{ color: userAstrologyProfile ? '#10B981' : '#EF4444', fontWeight: '600' }}>
                                      {userAstrologyProfile ? 'TRUE' : 'FALSE'}
                                    </Text>
                                  </Text>
                                  {userAstrologyProfile && (
                                    <>
                                      <Text style={styles.debugCode}>ayanamsa: {userAstrologyProfile.ayanamsa}</Text>
                                      <Text style={styles.debugCode}>computed_at: {userAstrologyProfile.computed_at}</Text>
                                    </>
                                  )}
                                </View>
                              </View>
                              
                              {/* Section 3: Last Save Status - Reflects persisted truth */}
                              <View style={styles.debugSection}>
                                <Text style={styles.debugSectionTitle}>3. Birth Data Save Status</Text>
                                {/* Priority: 1) Recent action status, 2) Persisted state from user record */}
                                {saveStatus ? (
                                  <View style={styles.debugFullStatus}>
                                    <View style={[styles.debugStatusBadge, { backgroundColor: saveStatus.success ? '#D1FAE5' : '#FEE2E2' }]}>
                                      <Text style={[styles.debugStatusText, { color: saveStatus.success ? '#065F46' : '#991B1B' }]}>
                                        {saveStatus.success ? '✓ SUCCESS' : '✗ FAILED'}: {saveStatus.message}
                                      </Text>
                                    </View>
                                    {saveStatus.response && (
                                      <View style={styles.debugErrorBlock}>
                                        <Text style={styles.debugErrorLabel}>Full API Response:</Text>
                                        <ScrollView style={styles.debugErrorScroll} nestedScrollEnabled>
                                          <Text style={styles.debugErrorText}>{saveStatus.response}</Text>
                                        </ScrollView>
                                      </View>
                                    )}
                                  </View>
                                ) : userBirthData ? (
                                  <View style={styles.debugFullStatus}>
                                    <View style={[styles.debugStatusBadge, { backgroundColor: '#D1FAE5' }]}>
                                      <Text style={[styles.debugStatusText, { color: '#065F46' }]}>
                                        ✓ PERSISTED: Birth data exists in user record
                                      </Text>
                                    </View>
                                    <Text style={styles.debugPersistedNote}>
                                      (Loaded from GET /api/auth/me)
                                    </Text>
                                  </View>
                                ) : (
                                  <View style={styles.debugFullStatus}>
                                    <View style={[styles.debugStatusBadge, { backgroundColor: '#FEF3C7' }]}>
                                      <Text style={[styles.debugStatusText, { color: '#92400E' }]}>
                                        ⚠ NOT SAVED: No birth data in user record
                                      </Text>
                                    </View>
                                  </View>
                                )}
                              </View>
                              
                              {/* Section 4: Last Compute Status - Reflects persisted truth */}
                              <View style={styles.debugSection}>
                                <Text style={styles.debugSectionTitle}>4. Astrology Compute Status</Text>
                                {/* Priority: 1) Recent action status, 2) Persisted state from user record */}
                                {computeStatus ? (
                                  <View style={styles.debugFullStatus}>
                                    <View style={[styles.debugStatusBadge, { backgroundColor: computeStatus.success ? '#D1FAE5' : '#FEE2E2' }]}>
                                      <Text style={[styles.debugStatusText, { color: computeStatus.success ? '#065F46' : '#991B1B' }]}>
                                        {computeStatus.success ? '✓ SUCCESS' : '✗ FAILED'}: {computeStatus.message}
                                      </Text>
                                    </View>
                                    {computeStatus.response && (
                                      <View style={styles.debugErrorBlock}>
                                        <Text style={styles.debugErrorLabel}>Full API Response:</Text>
                                        <ScrollView style={styles.debugErrorScroll} nestedScrollEnabled>
                                          <Text style={styles.debugErrorText}>{computeStatus.response}</Text>
                                        </ScrollView>
                                      </View>
                                    )}
                                  </View>
                                ) : userAstrologyProfile?.positions ? (
                                  <View style={styles.debugFullStatus}>
                                    <View style={[styles.debugStatusBadge, { backgroundColor: '#D1FAE5' }]}>
                                      <Text style={[styles.debugStatusText, { color: '#065F46' }]}>
                                        ✓ PERSISTED: Compute successful - profile exists
                                      </Text>
                                    </View>
                                    <Text style={styles.debugPersistedNote}>
                                      (Loaded from user.computed_profile.astrology)
                                    </Text>
                                  </View>
                                ) : userBirthData ? (
                                  <View style={styles.debugFullStatus}>
                                    <View style={[styles.debugStatusBadge, { backgroundColor: '#FEF3C7' }]}>
                                      <Text style={[styles.debugStatusText, { color: '#92400E' }]}>
                                        ⚠ PENDING: Birth data saved but not yet computed
                                      </Text>
                                    </View>
                                  </View>
                                ) : (
                                  <View style={styles.debugFullStatus}>
                                    <View style={[styles.debugStatusBadge, { backgroundColor: '#F3F4F6' }]}>
                                      <Text style={[styles.debugStatusText, { color: '#6B7280' }]}>
                                        — BLOCKED: Cannot compute without birth data
                                      </Text>
                                    </View>
                                  </View>
                                )}
                              </View>
                              
                              {/* Section 5: API Endpoints Reference */}
                              <View style={styles.debugSection}>
                                <Text style={styles.debugSectionTitle}>5. API Endpoints</Text>
                                <View style={styles.debugCodeBlock}>
                                  <Text style={styles.debugCode}>Save: POST /api/user/birth-data</Text>
                                  <Text style={styles.debugCode}>Compute: POST /api/computed-profile/astrology</Text>
                                  <Text style={styles.debugCode}>Read: GET /api/auth/me</Text>
                                </View>
                              </View>
                              
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
                                  onPress={openBirthDetailsModal}
                                >
                                  <Text style={styles.debugButtonSecondaryText}>Add/Edit Birth Details</Text>
                                </TouchableOpacity>
                              )}
                              
                              {/* Always show Edit button when birth data exists */}
                              {userBirthData && (
                                <TouchableOpacity 
                                  style={[styles.debugButtonSecondary, { marginTop: SPACING.sm }]}
                                  onPress={openBirthDetailsModal}
                                >
                                  <Text style={styles.debugButtonSecondaryText}>Edit Birth Details</Text>
                                </TouchableOpacity>
                              )}
                            </View>
                          )}
                        </View>
                      )}

                      {/* Your Sidereal Profile - SINGLE SOURCE OF TRUTH from user.computed_profile.astrology */}
                      {selectedLens.id === 'true-sidereal-astrology' && (
                        <View style={styles.siderealProfileContainer}>
                          <Text style={styles.siderealProfileTitle}>Your Sidereal Profile</Text>
                          {userAstrologyProfile?.positions ? (
                            <View style={styles.siderealProfileContent}>
                              <View style={styles.siderealProfileGrid}>
                                <View style={styles.siderealProfileItem}>
                                  <Text style={styles.siderealProfileLabel}>Sun</Text>
                                  <Text style={styles.siderealProfileSign}>
                                    {userAstrologyProfile.positions.sun?.sign}
                                  </Text>
                                  <Text style={styles.siderealProfileDegree}>
                                    {userAstrologyProfile.positions.sun?.degree}°
                                    {userAstrologyProfile.positions.sun?.minutes}'
                                  </Text>
                                </View>
                                <View style={styles.siderealProfileItem}>
                                  <Text style={styles.siderealProfileLabel}>Moon</Text>
                                  <Text style={styles.siderealProfileSign}>
                                    {userAstrologyProfile.positions.moon?.sign}
                                  </Text>
                                  <Text style={styles.siderealProfileDegree}>
                                    {userAstrologyProfile.positions.moon?.degree}°
                                    {userAstrologyProfile.positions.moon?.minutes}'
                                  </Text>
                                </View>
                                <View style={styles.siderealProfileItem}>
                                  <Text style={styles.siderealProfileLabel}>Ascendant</Text>
                                  <Text style={styles.siderealProfileSign}>
                                    {userAstrologyProfile.positions.ascendant?.sign}
                                  </Text>
                                  <Text style={styles.siderealProfileDegree}>
                                    {userAstrologyProfile.positions.ascendant?.degree}°
                                    {userAstrologyProfile.positions.ascendant?.minutes}'
                                  </Text>
                                </View>
                              </View>
                              <Text style={styles.siderealProfileAyanamsa}>
                                {(userAstrologyProfile.ayanamsa || 'FAGAN_BRADLEY').replace('_', '-')} ayanamsa
                              </Text>
                              <Text style={styles.siderealProfileSource}>
                                Source: user.computed_profile.astrology (persisted)
                              </Text>
                              {/* Action buttons when profile exists */}
                              <View style={styles.siderealProfileActions}>
                                <TouchableOpacity 
                                  style={styles.siderealProfileActionSecondary}
                                  onPress={openBirthDetailsModal}
                                >
                                  <Ionicons name="create-outline" size={16} color={COLORS.accent} />
                                  <Text style={styles.siderealProfileActionSecondaryText}>Edit Birth Details</Text>
                                </TouchableOpacity>
                                <TouchableOpacity 
                                  style={[styles.siderealProfileActionPrimary, runningCompute && { opacity: 0.6 }]}
                                  onPress={runSiderealCompute}
                                  disabled={runningCompute}
                                >
                                  {runningCompute ? (
                                    <ActivityIndicator size="small" color={COLORS.white} />
                                  ) : (
                                    <>
                                      <Ionicons name="refresh" size={16} color={COLORS.white} />
                                      <Text style={styles.siderealProfileActionPrimaryText}>Recompute</Text>
                                    </>
                                  )}
                                </TouchableOpacity>
                              </View>
                            </View>
                          ) : userBirthData ? (
                            /* State: Birth data exists but not computed */
                            <View style={styles.siderealProfileEmpty}>
                              <Ionicons name="hourglass-outline" size={32} color={COLORS.accent} style={{ marginBottom: SPACING.sm }} />
                              <Text style={styles.siderealProfileEmptyText}>
                                Birth data saved — ready to compute
                              </Text>
                              <Text style={styles.siderealProfileEmptyHint}>
                                Run computation to see your sidereal placements
                              </Text>
                              <View style={styles.siderealProfileActions}>
                                <TouchableOpacity 
                                  style={styles.siderealProfileActionSecondary}
                                  onPress={openBirthDetailsModal}
                                >
                                  <Ionicons name="create-outline" size={16} color={COLORS.accent} />
                                  <Text style={styles.siderealProfileActionSecondaryText}>Edit Birth Details</Text>
                                </TouchableOpacity>
                                <TouchableOpacity 
                                  style={[styles.siderealProfileActionPrimary, runningCompute && { opacity: 0.6 }]}
                                  onPress={runSiderealCompute}
                                  disabled={runningCompute}
                                >
                                  {runningCompute ? (
                                    <ActivityIndicator size="small" color={COLORS.white} />
                                  ) : (
                                    <>
                                      <Ionicons name="calculator-outline" size={16} color={COLORS.white} />
                                      <Text style={styles.siderealProfileActionPrimaryText}>Run Sidereal Compute Now</Text>
                                    </>
                                  )}
                                </TouchableOpacity>
                              </View>
                            </View>
                          ) : (
                            /* State: No birth data */
                            <View style={styles.siderealProfileEmpty}>
                              <Ionicons name="planet-outline" size={32} color={COLORS.secondary} style={{ marginBottom: SPACING.sm }} />
                              <Text style={styles.siderealProfileEmptyText}>
                                No birth data in user record
                              </Text>
                              <Text style={styles.siderealProfileEmptyHint}>
                                Add your birth details to compute your sidereal placements
                              </Text>
                              <TouchableOpacity 
                                style={styles.siderealProfileCTA}
                                onPress={openBirthDetailsModal}
                              >
                                <Ionicons name="add-circle-outline" size={18} color={COLORS.white} />
                                <Text style={styles.siderealProfileCTAText}>Add Birth Details</Text>
                              </TouchableOpacity>
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
                    {/* SINGLE SOURCE OF TRUTH: Reads directly from user.computed_profile.astrology */}
                    {selectedLens?.id === 'true-sidereal-astrology' && (
                      <View style={styles.computedProfileBlock}>
                        <Text style={styles.computedProfileBlockTitle}>Your Sidereal Profile (Computed)</Text>
                        {userAstrologyProfile?.positions ? (
                          <View style={styles.computedProfileBlockContent}>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Sun:</Text>
                              <Text style={styles.computedProfileValue}>
                                {userAstrologyProfile.positions.sun?.formatted || `${userAstrologyProfile.positions.sun?.sign} ${userAstrologyProfile.positions.sun?.degree}°${userAstrologyProfile.positions.sun?.minutes}'`}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Moon:</Text>
                              <Text style={styles.computedProfileValue}>
                                {userAstrologyProfile.positions.moon?.formatted || `${userAstrologyProfile.positions.moon?.sign} ${userAstrologyProfile.positions.moon?.degree}°${userAstrologyProfile.positions.moon?.minutes}'`}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Ascendant:</Text>
                              <Text style={styles.computedProfileValue}>
                                {userAstrologyProfile.positions.ascendant?.formatted || `${userAstrologyProfile.positions.ascendant?.sign} ${userAstrologyProfile.positions.ascendant?.degree}°${userAstrologyProfile.positions.ascendant?.minutes}'`}
                              </Text>
                            </View>
                            <View style={styles.computedProfileRow}>
                              <Text style={styles.computedProfileLabel}>Ayanamsa:</Text>
                              <Text style={styles.computedProfileValue}>
                                {userAstrologyProfile.ayanamsa?.replace('_', '-') || 'FAGAN-BRADLEY'}
                              </Text>
                            </View>
                            <Text style={styles.computedProfileSource}>Source: user.computed_profile.astrology</Text>
                          </View>
                        ) : (
                          <View style={styles.computedProfileBlockEmpty}>
                            <Ionicons name="planet-outline" size={24} color={COLORS.secondary} />
                            <Text style={styles.computedProfileEmptyText}>
                              {userBirthData ? 'Birth data saved but not computed' : 'No profile computed yet'}
                            </Text>
                            <TouchableOpacity 
                              style={styles.computedProfileCTA}
                              onPress={openBirthDetailsModal}
                            >
                              <Text style={styles.computedProfileCTAText}>
                                {userBirthData ? 'Run Compute' : 'Add Birth Details'}
                              </Text>
                            </TouchableOpacity>
                          </View>
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

          <ScrollView 
            style={styles.birthDetailsContent} 
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
          >
            <Text style={styles.birthDetailsSubtitle}>
              Enter your birth details to compute your True Sidereal profile
            </Text>

            {/* Date Selection - Platform specific */}
            <View style={styles.birthDetailsField}>
              <Text style={styles.birthDetailsLabel}>Birth Date</Text>
              {Platform.OS === 'web' ? (
                /* Web: Use native HTML date input */
                <View style={styles.birthDetailsInput}>
                  <TextInput
                    style={[styles.birthDetailsTextInput, { flex: 1, borderWidth: 0 }]}
                    value={`${birthDate.getFullYear()}-${String(birthDate.getMonth() + 1).padStart(2, '0')}-${String(birthDate.getDate()).padStart(2, '0')}`}
                    onChangeText={(text) => {
                      const parts = text.split('-');
                      if (parts.length === 3) {
                        const newDate = new Date(birthDate);
                        newDate.setFullYear(parseInt(parts[0]) || 1990);
                        newDate.setMonth((parseInt(parts[1]) || 1) - 1);
                        newDate.setDate(parseInt(parts[2]) || 1);
                        setBirthDate(newDate);
                      }
                    }}
                    placeholder="YYYY-MM-DD"
                    placeholderTextColor="#999"
                  />
                  <Ionicons name="calendar-outline" size={20} color={COLORS.secondary} />
                </View>
              ) : (
                /* Native: Use TouchableOpacity to open picker */
                <TouchableOpacity 
                  style={styles.birthDetailsInput} 
                  onPress={() => setShowBirthDatePicker(true)}
                  activeOpacity={0.7}
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
              )}
            </View>

            {/* Time Selection - Platform specific */}
            <View style={styles.birthDetailsField}>
              <Text style={styles.birthDetailsLabel}>Birth Time</Text>
              {Platform.OS === 'web' ? (
                /* Web: Use native HTML time input */
                <View style={styles.birthDetailsInput}>
                  <TextInput
                    style={[styles.birthDetailsTextInput, { flex: 1, borderWidth: 0 }]}
                    value={`${String(birthDate.getHours()).padStart(2, '0')}:${String(birthDate.getMinutes()).padStart(2, '0')}`}
                    onChangeText={(text) => {
                      const parts = text.split(':');
                      if (parts.length === 2) {
                        const newDate = new Date(birthDate);
                        newDate.setHours(parseInt(parts[0]) || 0);
                        newDate.setMinutes(parseInt(parts[1]) || 0);
                        setBirthDate(newDate);
                      }
                    }}
                    placeholder="HH:MM"
                    placeholderTextColor="#999"
                  />
                  <Ionicons name="time-outline" size={20} color={COLORS.secondary} />
                </View>
              ) : (
                /* Native: Use TouchableOpacity to open picker */
                <TouchableOpacity 
                  style={styles.birthDetailsInput} 
                  onPress={() => setShowBirthTimePicker(true)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.birthDetailsInputText}>
                    {birthDate.toLocaleTimeString('en-US', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </Text>
                  <Ionicons name="time-outline" size={20} color={COLORS.secondary} />
                </TouchableOpacity>
              )}
            </View>

            {/* Birth Location - Country → City Picker */}
            <View style={styles.birthDetailsField}>
              <Text style={styles.birthDetailsLabel}>Birth Country</Text>
              <TouchableOpacity 
                style={styles.birthDetailsInput} 
                onPress={() => setShowCountryPicker(!showCountryPicker)}
                activeOpacity={0.7}
              >
                <Text style={[styles.birthDetailsInputText, !selectedCountry && { color: '#999' }]}>
                  {selectedCountry || 'Select Country...'}
                </Text>
                <Ionicons name={showCountryPicker ? "chevron-up" : "chevron-down"} size={20} color={COLORS.secondary} />
              </TouchableOpacity>
              
              {/* Country Dropdown */}
              {showCountryPicker && (
                <View style={styles.pickerDropdown}>
                  <ScrollView style={styles.pickerScrollView} nestedScrollEnabled>
                    {countries.map((country) => (
                      <TouchableOpacity
                        key={country}
                        style={[
                          styles.pickerOption,
                          selectedCountry === country && styles.pickerOptionSelected
                        ]}
                        onPress={() => {
                          setSelectedCountry(country);
                          setSelectedCity('');
                          setBirthLat('');
                          setBirthLon('');
                          setBirthTzOffset('');
                          setShowCountryPicker(false);
                        }}
                      >
                        <Text style={[
                          styles.pickerOptionText,
                          selectedCountry === country && styles.pickerOptionTextSelected
                        ]}>{country}</Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>
                </View>
              )}
            </View>

            {/* City Picker - Only show when country is selected */}
            {selectedCountry && (
              <View style={styles.birthDetailsField}>
                <Text style={styles.birthDetailsLabel}>Birth City</Text>
                <TouchableOpacity 
                  style={styles.birthDetailsInput} 
                  onPress={() => setShowCityPicker(!showCityPicker)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.birthDetailsInputText, !selectedCity && { color: '#999' }]}>
                    {selectedCity || 'Select City...'}
                  </Text>
                  <Ionicons name={showCityPicker ? "chevron-up" : "chevron-down"} size={20} color={COLORS.secondary} />
                </TouchableOpacity>
                
                {/* City Dropdown */}
                {showCityPicker && (
                  <View style={styles.pickerDropdown}>
                    <ScrollView style={styles.pickerScrollView} nestedScrollEnabled>
                      {citiesForCountry.map((cityData) => (
                        <TouchableOpacity
                          key={cityData.city}
                          style={[
                            styles.pickerOption,
                            selectedCity === cityData.city && styles.pickerOptionSelected
                          ]}
                          onPress={() => handleCitySelection(cityData)}
                        >
                          <View style={styles.pickerCityOption}>
                            <Text style={[
                              styles.pickerOptionText,
                              selectedCity === cityData.city && styles.pickerOptionTextSelected
                            ]}>{cityData.city}</Text>
                            <Text style={styles.pickerCityTz}>{formatTimezone(cityData.tz)}</Text>
                          </View>
                        </TouchableOpacity>
                      ))}
                    </ScrollView>
                  </View>
                )}
              </View>
            )}

            {/* Can't find my city? - Manual Entry Toggle */}
            {!showManualLocationEntry ? (
              <TouchableOpacity 
                style={styles.cantFindCityButton}
                onPress={() => {
                  setShowManualLocationEntry(true);
                  setSelectedCountry('');
                  setSelectedCity('');
                  setLocationManuallyEdited(true);
                }}
              >
                <Ionicons name="help-circle-outline" size={18} color={COLORS.accent} />
                <Text style={styles.cantFindCityText}>Can't find my city? Enter manually</Text>
              </TouchableOpacity>
            ) : (
              /* Manual Entry Section */
              <View style={styles.manualEntrySection}>
                <View style={styles.manualEntryHeader}>
                  <Text style={styles.manualEntryTitle}>Manual Location Entry</Text>
                  <TouchableOpacity 
                    onPress={() => {
                      setShowManualLocationEntry(false);
                      setLocationManuallyEdited(false);
                      setBirthLat('');
                      setBirthLon('');
                      setBirthTzOffset('480');
                    }}
                  >
                    <Text style={styles.manualEntrySwitchBack}>← Back to city picker</Text>
                  </TouchableOpacity>
                </View>
                
                {/* Manual Coordinates */}
                <View style={styles.birthDetailsRow}>
                  <View style={[styles.birthDetailsField, { flex: 1, marginRight: SPACING.sm }]}>
                    <Text style={styles.birthDetailsLabel}>Latitude</Text>
                    <TextInput
                      style={styles.birthDetailsTextInput}
                      value={birthLat}
                      onChangeText={(v) => {
                        setBirthLat(v);
                        setLocationManuallyEdited(true);
                      }}
                      placeholder="e.g., 40.7128"
                      placeholderTextColor="#999"
                      keyboardType="decimal-pad"
                    />
                  </View>
                  <View style={[styles.birthDetailsField, { flex: 1, marginLeft: SPACING.sm }]}>
                    <Text style={styles.birthDetailsLabel}>Longitude</Text>
                    <TextInput
                      style={styles.birthDetailsTextInput}
                      value={birthLon}
                      onChangeText={(v) => {
                        setBirthLon(v);
                        setLocationManuallyEdited(true);
                      }}
                      placeholder="e.g., -74.0060"
                      placeholderTextColor="#999"
                      keyboardType="decimal-pad"
                    />
                  </View>
                </View>
                
                {/* Manual Timezone */}
                <View style={styles.birthDetailsField}>
                  <Text style={styles.birthDetailsLabel}>Timezone (UTC offset in minutes)</Text>
                  <TextInput
                    style={styles.birthDetailsTextInput}
                    value={birthTzOffset}
                    onChangeText={setBirthTzOffset}
                    placeholder="e.g., -300 for EST"
                    placeholderTextColor="#999"
                    keyboardType="numeric"
                  />
                  <Text style={styles.birthDetailsHint}>
                    Common: -300 (EST), -480 (PST), 0 (UTC), 330 (IST), 540 (JST)
                  </Text>
                </View>
                
                {birthTzOffset && (
                  <View style={styles.manualTzDisplay}>
                    <Text style={styles.manualTzLabel}>Selected timezone:</Text>
                    <Text style={styles.manualTzValue}>{formatTimezone(parseInt(birthTzOffset) || 0)}</Text>
                  </View>
                )}
              </View>
            )}

            {/* Auto-generated Timezone Display - Only for city picker mode */}
            {!showManualLocationEntry && selectedCity && birthTzOffset && (
              <View style={styles.autoTimezoneBox}>
                <View style={styles.autoTimezoneRow}>
                  <Ionicons name="time-outline" size={18} color="#059669" />
                  <Text style={styles.autoTimezoneLabel}>Timezone (auto-detected):</Text>
                </View>
                <Text style={styles.autoTimezoneValue}>{formatTimezone(parseInt(birthTzOffset))}</Text>
                <Text style={styles.autoTimezoneHint}>
                  Based on {selectedCity}, {selectedCountry}
                </Text>
              </View>
            )}

            {/* Coordinates Display - Only for city picker mode */}
            {!showManualLocationEntry && (birthLat && birthLon) && (
              <View style={styles.coordinatesDisplay}>
                <Text style={styles.coordinatesLabel}>Coordinates (auto-filled):</Text>
                <Text style={styles.coordinatesValue}>
                  {parseFloat(birthLat).toFixed(4)}°, {parseFloat(birthLon).toFixed(4)}°
                </Text>
              </View>
            )}

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

            {/* Inline Error Display */}
            {birthModalError && (
              <View style={styles.birthModalErrorBox}>
                <View style={styles.birthModalErrorHeader}>
                  <Ionicons name="alert-circle" size={18} color="#DC2626" />
                  <Text style={styles.birthModalErrorTitle}>
                    {birthModalError.type === 'save' ? 'Save Failed' : 'Compute Failed'}
                  </Text>
                </View>
                <Text style={styles.birthModalErrorMessage}>{birthModalError.message}</Text>
                {birthModalError.response && (
                  <Text style={styles.birthModalErrorResponse} numberOfLines={5}>
                    {birthModalError.response}
                  </Text>
                )}
                <TouchableOpacity 
                  style={styles.birthModalErrorDismiss}
                  onPress={() => setBirthModalError(null)}
                >
                  <Text style={styles.birthModalErrorDismissText}>Dismiss</Text>
                </TouchableOpacity>
              </View>
            )}

            {/* Save Button */}
            <TouchableOpacity
              style={[
                styles.birthDetailsSaveButton, 
                savingBirthDetails && styles.birthDetailsSaveButtonDisabled,
                (!birthLat || !birthLon) && styles.birthDetailsSaveButtonDisabled
              ]}
              onPress={saveBirthDetailsAndCompute}
              disabled={savingBirthDetails || !birthLat || !birthLon}
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
            
            {/* Validation hint */}
            {(!birthLat || !birthLon) && (
              <Text style={styles.birthDetailsValidationHint}>
                ⚠️ Please enter birth location (latitude and longitude) to save
              </Text>
            )}
            
            {/* Debug line showing saved user_id */}
            {savedUserId && (
              <View style={styles.birthDetailsSavedDebug}>
                <Ionicons name="checkmark-circle" size={16} color="#10B981" />
                <Text style={styles.birthDetailsSavedDebugText}>
                  Saved user_id: {savedUserId}
                </Text>
              </View>
            )}
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
    alignItems: 'center',
    paddingVertical: SPACING.md,
    gap: SPACING.sm,
  },
  computedProfileEmptyText: {
    fontSize: 13,
    color: COLORS.secondary,
    fontStyle: 'italic',
    textAlign: 'center',
  },
  computedProfileSource: {
    fontSize: 9,
    color: '#10B981',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginTop: SPACING.sm,
    textAlign: 'center',
  },
  computedProfileCTA: {
    backgroundColor: COLORS.accent,
    paddingVertical: SPACING.xs,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.sm,
    marginTop: SPACING.xs,
  },
  computedProfileCTAText: {
    color: COLORS.white,
    fontSize: 12,
    fontWeight: '600',
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
  siderealProfileSource: {
    fontSize: 10,
    color: '#10B981',
    textAlign: 'center',
    marginTop: SPACING.xs,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  siderealProfileEmpty: {
    alignItems: 'center',
    paddingVertical: SPACING.lg,
  },
  siderealProfileEmptyText: {
    fontSize: 15,
    color: COLORS.secondary,
    fontWeight: '500',
    textAlign: 'center',
  },
  siderealProfileEmptyHint: {
    fontSize: 13,
    color: COLORS.secondary,
    opacity: 0.7,
    marginTop: 4,
    textAlign: 'center',
    paddingHorizontal: SPACING.md,
  },
  siderealProfileCTA: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.accent,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.md,
    gap: SPACING.xs,
  },
  siderealProfileCTAText: {
    color: COLORS.white,
    fontSize: 14,
    fontWeight: '600',
  },
  siderealProfileActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: SPACING.sm,
    marginTop: SPACING.md,
    flexWrap: 'wrap',
  },
  siderealProfileActionPrimary: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.accent,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    gap: SPACING.xs,
  },
  siderealProfileActionPrimaryText: {
    color: COLORS.white,
    fontSize: 13,
    fontWeight: '600',
  },
  siderealProfileActionSecondary: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'transparent',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.accent,
    gap: SPACING.xs,
  },
  siderealProfileActionSecondaryText: {
    color: COLORS.accent,
    fontSize: 13,
    fontWeight: '600',
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
  // Birth Modal Error Styles
  birthModalErrorBox: {
    backgroundColor: '#FEF2F2',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: '#FECACA',
    marginBottom: SPACING.lg,
  },
  birthModalErrorHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginBottom: SPACING.xs,
  },
  birthModalErrorTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#DC2626',
  },
  birthModalErrorMessage: {
    fontSize: 13,
    color: '#991B1B',
    marginBottom: SPACING.xs,
  },
  birthModalErrorResponse: {
    fontSize: 11,
    color: '#7F1D1D',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    backgroundColor: '#FEE2E2',
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    marginTop: SPACING.xs,
  },
  birthModalErrorDismiss: {
    marginTop: SPACING.sm,
    alignSelf: 'flex-end',
  },
  birthModalErrorDismissText: {
    fontSize: 12,
    color: '#DC2626',
    fontWeight: '500',
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
  birthDetailsValidationHint: {
    fontSize: 12,
    color: '#DC2626',
    textAlign: 'center',
    marginTop: SPACING.sm,
  },
  birthDetailsManualNote: {
    fontSize: 11,
    color: COLORS.accent,
    marginTop: SPACING.xs,
    fontStyle: 'italic',
  },
  birthDetailsSavedDebug: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: SPACING.md,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    backgroundColor: '#ECFDF5',
    borderRadius: BORDER_RADIUS.sm,
    gap: SPACING.xs,
  },
  birthDetailsSavedDebugText: {
    fontSize: 11,
    color: '#065F46',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  // Country/City Picker Styles
  pickerDropdown: {
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: BORDER_RADIUS.md,
    marginTop: SPACING.xs,
    maxHeight: 200,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 3,
      },
      web: {
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      },
    }),
  },
  pickerScrollView: {
    maxHeight: 200,
  },
  pickerOption: {
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  pickerOptionSelected: {
    backgroundColor: '#EBF5FF',
  },
  pickerOptionText: {
    fontSize: 14,
    color: COLORS.primary,
  },
  pickerOptionTextSelected: {
    color: COLORS.accent,
    fontWeight: '600',
  },
  pickerCityOption: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  pickerCityTz: {
    fontSize: 12,
    color: COLORS.secondary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  autoTimezoneBox: {
    backgroundColor: '#ECFDF5',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.md,
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  autoTimezoneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.xs,
    marginBottom: 4,
  },
  autoTimezoneLabel: {
    fontSize: 12,
    color: '#065F46',
    fontWeight: '500',
  },
  autoTimezoneValue: {
    fontSize: 18,
    color: '#059669',
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  autoTimezoneHint: {
    fontSize: 11,
    color: '#10B981',
    marginTop: 4,
    fontStyle: 'italic',
  },
  coordinatesDisplay: {
    backgroundColor: '#F3F4F6',
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    marginBottom: SPACING.md,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  coordinatesLabel: {
    fontSize: 11,
    color: COLORS.secondary,
  },
  coordinatesValue: {
    fontSize: 12,
    color: COLORS.primary,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    fontWeight: '500',
  },
  // Can't find my city / Manual Entry Styles
  cantFindCityButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: SPACING.md,
    gap: SPACING.xs,
  },
  cantFindCityText: {
    fontSize: 14,
    color: COLORS.accent,
    fontWeight: '500',
  },
  manualEntrySection: {
    backgroundColor: '#F9FAFB',
    padding: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    marginBottom: SPACING.md,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  manualEntryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.md,
  },
  manualEntryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.primary,
  },
  manualEntrySwitchBack: {
    fontSize: 12,
    color: COLORS.accent,
  },
  manualTzDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#EBF5FF',
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    marginTop: SPACING.sm,
  },
  manualTzLabel: {
    fontSize: 12,
    color: COLORS.secondary,
  },
  manualTzValue: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.accent,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
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
  debugStatusContainer: {
    marginTop: SPACING.xs,
  },
  debugResponseText: {
    fontSize: 10,
    color: '#6B7280',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginTop: 4,
    backgroundColor: '#F9FAFB',
    padding: 6,
    borderRadius: 4,
    overflow: 'hidden',
  },
  debugNoStatus: {
    fontSize: 11,
    color: '#9CA3AF',
    fontStyle: 'italic',
  },
  debugSection: {
    marginBottom: SPACING.md,
    paddingBottom: SPACING.md,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  debugSectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: SPACING.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  debugCodeMuted: {
    fontSize: 11,
    color: '#9CA3AF',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
  debugFullStatus: {
    marginTop: SPACING.xs,
  },
  debugErrorBlock: {
    marginTop: SPACING.sm,
    backgroundColor: '#FEF2F2',
    borderRadius: BORDER_RADIUS.sm,
    padding: SPACING.sm,
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  debugErrorLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#991B1B',
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  debugErrorScroll: {
    maxHeight: 120,
  },
  debugErrorText: {
    fontSize: 10,
    color: '#7F1D1D',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    lineHeight: 14,
  },
  debugPersistedNote: {
    fontSize: 10,
    color: '#059669',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginTop: 4,
    fontStyle: 'italic',
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
