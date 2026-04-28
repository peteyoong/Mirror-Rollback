import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { Ionicons } from '@expo/vector-icons';
import { InlineResonanceReflect } from './ResonanceReflectButtons';
import axios from 'axios';
import Constants from 'expo-constants';
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';
import { 
  getStableUserId, 
  getStableUserIdSync,
  assertUserIdStable, 
  maskUserId,
  getDebugUserIdInfo 
} from '../utils/stableUserId';
// Import NumerologyPatternView for Deep Dive tab
import NumerologyDeepDivePattern from './NumerologyDeepDivePattern';
// Import new V2 components
import NumerologySummaryV2 from './NumerologySummaryV2';
import NumerologyDeepDiveV2 from './NumerologyDeepDiveV2';

// === V1-SAFE DEV FALLBACK FOR BACKEND URL ===
// Web preview proxy /api is unreliable, so we need a direct backend URL fallback
const DEV_BACKEND_FALLBACK = 'http://localhost:8001'; // Direct backend in dev

function getBackendBaseUrl(): string {
  // For web: ALWAYS use relative URLs so API calls go to same origin
  // This works for both preview and deployed domains
  if (Platform.OS === 'web') {
    return '';
  }
  
  // For native: try EXPO_PUBLIC_BACKEND_URL from env
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.length > 0) {
    return envUrl;
  }
  
  // Try expo-constants extra config
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
  if (extraUrl && typeof extraUrl === 'string' && extraUrl.length > 0) {
    return extraUrl;
  }
  
  // Native fallback
  return DEV_BACKEND_FALLBACK;
}

// Resolved backend base URL (computed once)
const BACKEND_BASE_URL = getBackendBaseUrl();
if (__DEV__) {
  console.log('[NumerologyLensView] BACKEND_BASE_URL resolved to:', BACKEND_BASE_URL || '(relative)')
}

interface NumerologySection {
  label: string;
  body: string;
}

interface NumerologyCycles {
  personal_day: number;
  personal_month: number;
  personal_year: number;
}

interface CoreNumbers {
  life_path: number | string;
  expression: number | string;
  soul_urge: number | string;
}

interface NumerologyData {
  title: string;
  sections: NumerologySection[];
  mirror_prompt: string;
  unlock_prompt?: string | null;
  unlock_required?: boolean;
  core_numbers?: CoreNumbers;
  cycles?: NumerologyCycles;
  date?: string;
  full_birth_name?: string | null;
  // Debug fields from API
  debug_stamp?: {
    fallback_used?: boolean;
    source?: string;
    timestamp?: string;
    cached?: boolean;
  };
}

// Profile data from GET /api/profile/{user_id}
interface UserProfile {
  user_id: string;
  preferred_name: string | null;
  numerology_full_name: string | null;
  updated_at: string | null;
  exists?: boolean;
}

interface Props {
  userId: string;
  onOpenChat: () => void;
}

type TabType = 'summary' | 'today' | 'deep_dive';

export default function NumerologyLensView({ userId, onOpenChat }: Props) {
  // Theme support
  const { theme, isDark } = useTheme();
  
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [data, setData] = useState<NumerologyData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  
  // === CANONICAL PROFILE STATE (single source of truth) ===
  // This is the ONLY state for the user's numerology name - driven entirely by server
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  
  // === BACKEND HEALTH CHECK STATE ===
  const [backendHealthOk, setBackendHealthOk] = useState<boolean | null>(null); // null = not checked yet
  
  // === USER ID STABILITY CHECK STATE (DEBUG_MIRROR only) ===
  const [stableUserId, setStableUserIdState] = useState<string | null>(null);
  const [userIdChanged, setUserIdChanged] = useState<boolean>(false);
  const [userIdDebugInfo, setUserIdDebugInfo] = useState<any>(null);
  
  // === MODAL STATE ===
  // Explicit mode: 'add' = no name exists, 'edit' = editing existing name
  type ModalMode = 'add' | 'edit';
  const [unlockModalVisible, setUnlockModalVisible] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>('add');
  const [unlockStep, setUnlockStep] = useState<'consent' | 'input' | 'success'>('consent');
  const [modalInputName, setModalInputName] = useState(''); // Transient input only
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [unlockError, setUnlockError] = useState<string | null>(null);
  
  // Debug: track raw API response length
  const [rawDataLength, setRawDataLength] = useState<number>(0);
  
  // Debug: track if TextInput was rendered
  const [inputRendered, setInputRendered] = useState(false);

  // === USER ID STABILITY CHECK using centralized utility ===
  useEffect(() => {
    const checkUserIdStability = async () => {
      try {
        // Get the stable user ID from centralized utility
        const stableId = await getStableUserId();
        setStableUserIdState(stableId);
        
        // Check if prop userId matches stable ID
        if (stableId !== userId) {
          setUserIdChanged(true);
          if (isDebugEnabled()) {
            console.log('[DEBUG_MIRROR] ⚠️ PROP USER ID DIFFERS FROM STABLE ID!', {
              prop_id: maskUserId(userId),
              stable_id: maskUserId(stableId)
            });
          }
        } else {
          setUserIdChanged(false);
          if (isDebugEnabled()) {
            console.log('[DEBUG_MIRROR] ✓ User ID matches stable ID:', maskUserId(userId));
          }
        }
        
        // Run assertion check
        const isStable = await assertUserIdStable();
        if (!isStable && isDebugEnabled()) {
          console.error('[DEBUG_MIRROR] ❌ User ID stability assertion FAILED');
        }
        
        // Get debug info for DebugFooter
        if (isDebugEnabled()) {
          const debugInfo = await getDebugUserIdInfo();
          setUserIdDebugInfo(debugInfo);
        }
      } catch (err) {
        console.error('[DEBUG_MIRROR] User ID stability check failed:', err);
      }
    };
    
    checkUserIdStability();
  }, [userId]);

  // === BACKEND HEALTH CHECK (DEBUG_MIRROR only) ===
  useEffect(() => {
    if (!isDebugEnabled()) return;
    
    const checkHealth = async () => {
      try {
        const healthUrl = BACKEND_BASE_URL 
          ? `${BACKEND_BASE_URL}/api/health`
          : `/api/health`;
        
        console.log('[DEBUG_MIRROR] Checking backend health:', healthUrl);
        
        const response = await axios.get(healthUrl, { timeout: 5000 });
        const isOk = response.data?.ok === true && response.data?.service === 'backend';
        
        setBackendHealthOk(isOk);
        console.log('[DEBUG_MIRROR] Backend health check:', isOk ? '✅ OK' : '❌ FAILED', response.data);
      } catch (err) {
        console.error('[DEBUG_MIRROR] Backend health check failed:', err);
        setBackendHealthOk(false);
      }
    };
    
    checkHealth();
  }, []); // Run once on mount

  // === PROFILE HYDRATION FROM SERVER ===
  // Fetch profile from GET /api/profile/{user_id} - this is the canonical source
  // Uses direct backend URL to bypass unreliable web preview proxy
  const hydrateProfile = useCallback(async () => {
    setProfileLoading(true);
    try {
      const profileUrl = BACKEND_BASE_URL 
        ? `${BACKEND_BASE_URL}/api/profile/${userId}`
        : `/api/profile/${userId}`;
      
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Fetching profile from:', profileUrl);
      }
      
      const response = await axios.get(profileUrl, { timeout: 10000 });
      const serverProfile: UserProfile = response.data;
      setProfile(serverProfile);
      
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Profile hydrated from server:', {
          user_id: userId,
          numerology_full_name: serverProfile.numerology_full_name,
          updated_at: serverProfile.updated_at,
          exists: serverProfile.exists,
          backend_base_url: BACKEND_BASE_URL || '(relative)'
        });
      }
    } catch (err) {
      console.error('[PROFILE] Failed to hydrate profile:', err);
      // Set empty profile on error - UI will show CTA
      setProfile({ user_id: userId, preferred_name: null, numerology_full_name: null, updated_at: null, exists: false });
    } finally {
      setProfileLoading(false);
    }
  }, [userId]);

  // Initial profile hydration on mount
  useEffect(() => {
    hydrateProfile();
  }, [hydrateProfile]);

  useEffect(() => {
    // Deep Dive tab uses NumerologyDeepDivePattern which has its own data fetching
    // Only load data for Summary and Today tabs
    if (activeTab !== 'deep_dive') {
      loadTabData(activeTab);
    } else {
      // Reset loading state for Deep Dive since component handles it
      setIsLoading(false);
      setError(null);
    }
  }, [activeTab, userId]);

  const loadTabData = async (tab: TabType) => {
    // Skip API call for Deep Dive - it uses NumerologyDeepDivePattern's own fetch
    if (tab === 'deep_dive') {
      setIsLoading(false);
      return;
    }
    
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = tab === 'today' 
        ? `/numerology/today/${userId}`
        : `/numerology/summary/${userId}`;

      const response = await api.get(endpoint);
      setData(response.data);
      
      // Debug: Calculate raw data length for comparison
      if (isDebugEnabled() && response.data?.sections) {
        const totalChars = response.data.sections.reduce(
          (sum: number, s: NumerologySection) => sum + (s.body?.length || 0), 
          0
        );
        setRawDataLength(totalChars);
        console.log(`[DEBUG_MIRROR] Numerology ${tab}: API returned ${totalChars} chars across ${response.data.sections.length} sections`);
      }
    } catch (err: any) {
      console.error(`Numerology ${tab} error:`, err);
      setError('Unable to load this view right now.');
    } finally {
      setIsLoading(false);
    }
  };

  const renderTabs = () => (
    <View style={[styles.tabContainer, { borderBottomColor: theme.border }]}>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'summary' && styles.activeTab]}
        onPress={() => setActiveTab('summary')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'summary' && { color: theme.text }]}>
          Summary
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'today' && styles.activeTab]}
        onPress={() => setActiveTab('today')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'today' && { color: theme.text }]}>
          Today&apos;s Snapshot
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === 'deep_dive' && styles.activeTab]}
        onPress={() => setActiveTab('deep_dive')}
      >
        <Text style={[styles.tabText, { color: theme.textTertiary }, activeTab === 'deep_dive' && { color: theme.text }]}>
          Deep Dive
        </Text>
      </TouchableOpacity>
    </View>
  );

  // Core Numbers Card (for Deep Dive)
  const renderCoreNumbers = () => {
    const numbers = data?.core_numbers || {
      life_path: 'Unknown',
      expression: 'locked',
      soul_urge: 'locked'
    };

    const formatNumber = (value: number | string | null | undefined) => {
      if (value === null || value === undefined) return '🔒';
      if (value === 'locked') return '🔒';
      if (value === 'Unknown') return '—';
      
      // Handle master numbers - display as "11/2", "22/4", "33/6"
      const num = typeof value === 'string' ? parseInt(value, 10) : value;
      if (num === 11) return '11/2';
      if (num === 22) return '22/4';
      if (num === 33) return '33/6';
      
      return value.toString();
    };

    const isLocked = (value: number | string | null | undefined) => 
      value === 'locked' || value === null || value === undefined;

    return (
      <View style={[styles.coreNumbersCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <Text style={[styles.coreNumbersTitle, { color: theme.textTertiary }]}>LIFE PATH • EXPRESSION • SOUL URGE</Text>
        <View style={styles.coreNumbersRow}>
          <View style={styles.numberItem}>
            <Text style={[styles.numberLabel, { color: theme.textTertiary }]}>Life Path</Text>
            <Text style={[styles.numberValue, { color: theme.text }]}>{formatNumber(numbers.life_path)}</Text>
          </View>
          <View style={[styles.numberDivider, { backgroundColor: theme.border }]} />
          <View style={styles.numberItem}>
            <Text style={[styles.numberLabel, { color: theme.textTertiary }]}>Expression</Text>
            <Text style={[
              styles.numberValue, 
              { color: theme.text },
              isLocked(numbers.expression) && styles.lockedNumber
            ]}>
              {formatNumber(numbers.expression)}
            </Text>
          </View>
          <View style={[styles.numberDivider, { backgroundColor: theme.border }]} />
          <View style={styles.numberItem}>
            <Text style={[styles.numberLabel, { color: theme.textTertiary }]}>Soul Urge</Text>
            <Text style={[
              styles.numberValue, 
              { color: theme.text },
              isLocked(numbers.soul_urge) && styles.lockedNumber
            ]}>
              {formatNumber(numbers.soul_urge)}
            </Text>
          </View>
        </View>
      </View>
    );
  };

  // Cycles Display (for Today's Snapshot)
  const renderCycles = () => {
    if (activeTab !== 'today' || !data?.cycles) return null;

    const { personal_day, personal_month, personal_year } = data.cycles;

    return (
      <View style={[styles.cyclesCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <View style={styles.cyclesRow}>
          <View style={styles.cycleItem}>
            <Text style={[styles.cycleLabel, { color: theme.textTertiary }]}>Day</Text>
            <Text style={[styles.cycleNumber, { color: theme.text }]}>{personal_day}</Text>
          </View>
          <View style={[styles.cycleDivider, { backgroundColor: theme.border }]} />
          <View style={styles.cycleItem}>
            <Text style={[styles.cycleLabel, { color: theme.textTertiary }]}>Month</Text>
            <Text style={[styles.cycleNumber, { color: theme.text }]}>{personal_month}</Text>
          </View>
          <View style={[styles.cycleDivider, { backgroundColor: theme.border }]} />
          <View style={styles.cycleItem}>
            <Text style={[styles.cycleLabel, { color: theme.textTertiary }]}>Year</Text>
            <Text style={[styles.cycleNumber, { color: theme.text }]}>{personal_year}</Text>
          </View>
        </View>
      </View>
    );
  };

  const renderSection = (section: NumerologySection, index: number) => {
    const isExpanded = expandedSection === section.label || activeTab !== 'deep_dive';

    return (
      <View key={index} style={[styles.sectionCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => {
            if (activeTab === 'deep_dive') {
              setExpandedSection(expandedSection === section.label ? null : section.label);
            }
          }}
          activeOpacity={activeTab === 'deep_dive' ? 0.7 : 1}
        >
          <Text style={[styles.sectionLabel, { color: theme.text }]}>{section.label}</Text>
          {activeTab === 'deep_dive' && (
            <Ionicons
              name={isExpanded ? 'chevron-up' : 'chevron-down'}
              size={20}
              color={theme.textTertiary}
            />
          )}
        </TouchableOpacity>
        {isExpanded && (
          <>
            <Text style={[styles.sectionBody, { color: theme.textSecondary }]}>{section.body}</Text>
            {/* Debug: Show section-level metrics */}
            <SectionDebug label={section.label} body={section.body} index={index} />
            {/* Reflect Button */}
            <InlineResonanceReflect
              source={{
                lens: 'numerology',
                type: section.label.toLowerCase().replace(/\s+/g, '_'),
                name: section.label,
                id: `numerology_${section.label.toLowerCase().replace(/\s+/g, '_')}`,
              }}
              prompt={`Reflect on ${section.label}: ${section.body.slice(0, 100)}...`}
            />
          </>
        )}
      </View>
    );
  };

  // === OPEN MODAL HANDLER ===
  // Determines mode based on latest profile.numerology_full_name
  // If profile is loading, defaults to 'add' mode
  const openUnlockModal = useCallback(() => {
    // Determine mode from latest profile state
    const hasName = profile?.numerology_full_name && profile.numerology_full_name.length > 0;
    const mode: 'add' | 'edit' = hasName ? 'edit' : 'add';
    
    // Set modal state
    setModalMode(mode);
    setModalInputName(hasName ? (profile?.numerology_full_name || '') : '');
    setUnlockStep('input'); // Always go directly to input - never show info-only step
    setInputRendered(false); // Reset debug flag
    setUnlockError(null);
    setUnlockModalVisible(true);
    
    if (isDebugEnabled()) {
      console.log('[DEBUG_MIRROR] Opening modal:', {
        mode,
        profile_loading: profileLoading,
        has_name: hasName,
        prefill_name: hasName ? maskUserId(profile?.numerology_full_name || '') : '(empty)'
      });
    }
  }, [profile, profileLoading]);

  // === RENDER NAME CARD OR CTA ===
  // Driven SOLELY by profile.numerology_full_name from server
  const renderNameSection = () => {
    // Still loading profile - show CTA that opens in 'add' mode
    if (profileLoading) {
      return (
        <TouchableOpacity 
          style={[styles.unlockButton, { backgroundColor: theme.accent }]}
          onPress={openUnlockModal}
          activeOpacity={0.8}
        >
          <View style={styles.unlockButtonContent}>
            <Ionicons name="add-circle-outline" size={22} color={theme.background} />
            <View style={styles.unlockButtonText}>
              <Text style={[styles.unlockButtonTitle, { color: theme.background }]}>Add Full Birth Name</Text>
              <Text style={[styles.unlockButtonSubtitle, { color: theme.background, opacity: 0.7 }]}>Loading profile...</Text>
            </View>
          </View>
          <Ionicons name="chevron-forward" size={20} color={theme.background} style={{ opacity: 0.5 }} />
        </TouchableOpacity>
      );
    }
    
    // Name EXISTS in server profile → Show name with Edit button
    if (profile?.numerology_full_name) {
      return (
        <View style={[styles.fullNameCard, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <Ionicons name="person-outline" size={18} color={theme.textSecondary} />
          <View style={styles.fullNameTextContainer}>
            <Text style={[styles.fullNameLabel, { color: theme.textTertiary }]}>Full Birth Name</Text>
            <Text style={[styles.fullNameValue, { color: theme.text }]}>{profile.numerology_full_name}</Text>
          </View>
          <TouchableOpacity 
            style={styles.editNameButton}
            onPress={openUnlockModal}
          >
            <Ionicons name="pencil-outline" size={16} color={theme.accent} />
          </TouchableOpacity>
        </View>
      );
    }
    
    // Name ABSENT → Show CTA button to add name
    return (
      <TouchableOpacity 
        style={[styles.unlockButton, { backgroundColor: theme.accent }]}
        onPress={openUnlockModal}
        activeOpacity={0.8}
      >
        <View style={styles.unlockButtonContent}>
          <Ionicons name="add-circle-outline" size={22} color={theme.background} />
          <View style={styles.unlockButtonText}>
            <Text style={[styles.unlockButtonTitle, { color: theme.background }]}>Add Full Birth Name</Text>
            <Text style={[styles.unlockButtonSubtitle, { color: theme.background, opacity: 0.7 }]}>Unlock Expression, Soul Urge & Personality numbers</Text>
          </View>
        </View>
        <Ionicons name="chevron-forward" size={20} color={theme.background} style={{ opacity: 0.5 }} />
      </TouchableOpacity>
    );
  };

  // === HANDLE NAME SAVE WITH READ-AFTER-WRITE ===
  // Uses direct backend URL to bypass unreliable web preview proxy
  const handleUnlockSubmit = async () => {
    const nameToSave = modalInputName.trim();
    
    if (!nameToSave) {
      setUnlockError('Please enter your full birth name');
      return;
    }

    setIsUnlocking(true);
    setUnlockError(null);

    try {
      // Build URLs with backend base URL
      const unlockUrl = BACKEND_BASE_URL 
        ? `${BACKEND_BASE_URL}/api/numerology/unlock-name/${userId}`
        : `/api/numerology/unlock-name/${userId}`;
      const profileUrl = BACKEND_BASE_URL 
        ? `${BACKEND_BASE_URL}/api/profile/${userId}`
        : `/api/profile/${userId}`;
      
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Step 1: POST unlock-name to:', unlockUrl);
      }
      
      // === STEP 1: POST to save the name ===
      const saveResponse = await axios.post(unlockUrl, {
        full_birth_name: nameToSave
      }, { timeout: 15000 });
      
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Step 1 complete. Response:', saveResponse.data);
      }
      
      // === STEP 2: GET profile to confirm persistence ===
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Step 2: GET profile from:', profileUrl);
      }
      
      const profileResponse = await axios.get(profileUrl, { timeout: 10000 });
      const updatedProfile: UserProfile = profileResponse.data;
      
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Step 2 complete. Profile:', {
          saved_name: nameToSave,
          server_name: updatedProfile.numerology_full_name,
          match: updatedProfile.numerology_full_name === nameToSave
        });
      }
      
      // Verify the write succeeded
      if (updatedProfile.numerology_full_name !== nameToSave) {
        console.error('[PROFILE] Read-after-write mismatch!', {
          expected: nameToSave,
          got: updatedProfile.numerology_full_name
        });
        setUnlockError('Save may have failed. Please try again.');
        setIsUnlocking(false);
        return;
      }
      
      // === STEP 3: setProfile with GET response ===
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Step 3: setProfile with confirmed data');
      }
      setProfile(updatedProfile);
      
      // === STEP 4: Close modal (only after GET completes) ===
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Step 4: Closing modal');
      }
      setIsUnlocking(false);
      setUnlockModalVisible(false);
      setUnlockStep('input'); // Reset for next open
      setModalInputName(''); // Clear input
      setUnlockError(null);
      
      // Refresh tab data to show updated numbers
      loadTabData(activeTab);
      
    } catch (err: any) {
      console.error('[PROFILE] Save error:', err);
      setUnlockError('Something went wrong. Please try again.');
      setIsUnlocking(false);
    }
  };

  const closeUnlockModal = () => {
    setUnlockModalVisible(false);
    setUnlockStep('input'); // Default to input step for next open
    setModalMode('add'); // Reset mode
    setModalInputName(''); // Clear transient input
    setUnlockError(null);
    setInputRendered(false);
  };

  // Render the unlock modal - ALWAYS shows TextInput when in 'input' step
  // Fixed for mobile web: proper keyboard handling, safe areas, and sticky action buttons
  const renderUnlockModal = () => {
    // Log when modal renders
    if (isDebugEnabled() && unlockModalVisible) {
      console.log('[DEBUG_MIRROR] Modal rendering:', {
        visible: unlockModalVisible,
        mode: modalMode,
        step: unlockStep,
        inputRendered: inputRendered
      });
    }
    
    return (
      <Modal
        visible={unlockModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={closeUnlockModal}
        statusBarTranslucent={true}
      >
        {/* Overlay backdrop - tappable to close */}
        <TouchableOpacity 
          style={styles.modalOverlay}
          activeOpacity={1}
          onPress={closeUnlockModal}
        >
          {/* Prevent touches on modal content from closing */}
          <TouchableOpacity 
            activeOpacity={1} 
            onPress={(e) => e.stopPropagation()}
            style={{ width: '100%' }}
          >
            <KeyboardAvoidingView 
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
              style={styles.keyboardAvoidingContainer}
            >
              <View style={[styles.unlockModalContainer, { backgroundColor: theme.surface }]}>
                {/* Close button */}
                <TouchableOpacity 
                  style={styles.modalCloseButton}
                  onPress={closeUnlockModal}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                  <Ionicons name="close" size={24} color={theme.textSecondary} />
                </TouchableOpacity>

                {/* INPUT STEP - Always show TextInput for add/edit */}
                {unlockStep === 'input' && (
                  <>
                    {/* Scrollable content area */}
                    <ScrollView 
                      style={styles.modalScrollContent}
                      contentContainerStyle={styles.modalScrollContentContainer}
                      showsVerticalScrollIndicator={false}
                      keyboardShouldPersistTaps="handled"
                      bounces={false}
                    >
                      <View style={styles.modalIconContainer}>
                        <Ionicons name="person-outline" size={32} color={theme.accent} />
                      </View>
                      <Text style={[styles.modalTitle, { color: theme.text }]}>
                        {modalMode === 'edit' ? 'Edit Your Name' : 'Your Full Birth Name'}
                      </Text>
                      <Text style={[styles.modalSubtitle, { color: theme.textSecondary }]}>
                        {modalMode === 'edit' ? 'Update your birth name' : 'As given at birth'}
                      </Text>
                      
                      <View style={styles.modalBody}>
                        <Text style={[styles.modalText, { color: theme.textSecondary }]}>
                          {modalMode === 'edit' 
                            ? 'Update the name used for numerology calculations.'
                            : 'Enter your full birth name to unlock Expression, Soul Urge, and Personality numbers.'
                          }
                        </Text>
                        
                        {/* TEXTINPUT - Always rendered when step === 'input' */}
                        {(() => {
                          // Log when TextInput mounts
                          if (!inputRendered) {
                            console.log('[DEBUG_MIRROR] 📝 TextInput MOUNTING - mode:', modalMode);
                            // Use setTimeout to avoid state update during render
                            setTimeout(() => setInputRendered(true), 0);
                          }
                          return (
                            <TextInput
                              style={[styles.nameInput, { borderColor: theme.border }]}
                              placeholder="e.g., John Michael Smith"
                              placeholderTextColor={theme.textTertiary}
                              value={modalInputName}
                              onChangeText={(text) => {
                                // Preserve the full text including spaces
                                setModalInputName(text);
                              }}
                              autoCapitalize="words"
                              autoCorrect={false}
                              autoFocus={Platform.OS !== 'web'}
                              multiline={false}
                              returnKeyType="done"
                              blurOnSubmit={true}
                              onSubmitEditing={handleUnlockSubmit}
                              maxLength={100}
                              textContentType="name"
                            />
                          );
                        })()}
                        
                        {unlockError && (
                          <Text style={styles.unlockErrorText}>{unlockError}</Text>
                        )}
                        
                        <Text style={[styles.privacyNote, { color: theme.textTertiary }]}>
                          Your name is stored securely and used only for these calculations.
                        </Text>
                      </View>
                    </ScrollView>

                    {/* STICKY ACTION BUTTONS - Always visible at bottom */}
                    <View style={[styles.modalActionsSticky, { backgroundColor: theme.surface, borderTopColor: theme.border }]}>
                      <TouchableOpacity 
                        style={[styles.modalSecondaryButton, { backgroundColor: theme.surfaceLight }]}
                        onPress={closeUnlockModal}
                      >
                        <Text style={[styles.modalSecondaryButtonText, { color: theme.text }]}>Cancel</Text>
                      </TouchableOpacity>
                      <TouchableOpacity 
                        style={[styles.modalPrimaryButton, { backgroundColor: theme.accent }, isUnlocking && styles.disabledButton]}
                        onPress={handleUnlockSubmit}
                        disabled={isUnlocking}
                      >
                        {isUnlocking ? (
                          <ActivityIndicator size="small" color="#FFFFFF" />
                        ) : (
                          <Text style={[styles.modalPrimaryButtonText, { color: '#FFFFFF' }]}>
                            {modalMode === 'edit' ? 'Save' : 'Unlock'}
                          </Text>
                        )}
                      </TouchableOpacity>
                    </View>
                    
                    {/* Debug info at bottom of modal */}
                    {isDebugEnabled() && (
                      <View style={styles.modalDebug}>
                        <Text style={[styles.modalDebugText, { color: theme.textTertiary }]}>
                          mode: {modalMode} | input_rendered: {inputRendered ? 'YES' : 'NO'}
                        </Text>
                      </View>
                    )}
                  </>
                )}
              </View>
            </KeyboardAvoidingView>
          </TouchableOpacity>
        </TouchableOpacity>
      </Modal>
    );
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.background }]}>
      {/* Backend Unreachable Banner - visible when DEBUG_MIRROR is on and health check failed */}
      {isDebugEnabled() && backendHealthOk === false && (
        <View style={styles.healthBanner}>
          <Ionicons name="warning" size={16} color="#fff" />
          <Text style={styles.healthBannerText}>Backend unreachable</Text>
        </View>
      )}
      
      {/* User ID Changed Banner - visible when DEBUG_MIRROR is on and user ID changed */}
      {isDebugEnabled() && userIdChanged && (
        <View style={styles.userIdChangedBanner}>
          <Ionicons name="swap-horizontal" size={16} color="#fff" />
          <Text style={styles.userIdChangedBannerText}>User ID changed — profile will appear empty</Text>
        </View>
      )}
      
      {renderTabs()}

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {isLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={theme.textTertiary} />
            <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
              {activeTab === 'deep_dive' 
                ? 'Generating your personalized reading...\nThis may take 30-45 seconds'
                : 'Loading...'}
            </Text>
          </View>
        ) : error ? (
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={32} color={theme.textTertiary} />
            <Text style={[styles.errorText, { color: theme.textSecondary }]}>{error}</Text>
            <TouchableOpacity
              style={[styles.retryButton, { backgroundColor: theme.surface }]}
              onPress={() => loadTabData(activeTab)}
            >
              <Text style={[styles.retryText, { color: theme.text }]}>Try Again</Text>
            </TouchableOpacity>
            {/* Still show core numbers on Deep Dive even with error */}
            {activeTab === 'deep_dive' && renderCoreNumbers()}
          </View>
        ) : activeTab === 'summary' ? (
          /* ===== SUMMARY TAB: Uses new V2 component with computed data ===== */
          <NumerologySummaryV2
            userId={userId}
            onOpenChat={onOpenChat}
            existingName={profile?.numerology_full_name}
            onAddName={openUnlockModal}
          />
        ) : activeTab === 'deep_dive' ? (
          /* ===== DEEP DIVE TAB: Uses new V2 component aligned with Summary ===== */
          <NumerologyDeepDiveV2
            userId={userId}
            onOpenChat={onOpenChat}
            existingName={profile?.numerology_full_name}
            onNameUpdated={hydrateProfile}
          />
        ) : data ? (
          /* ===== SUMMARY & TODAY TABS: Use API data with sections ===== */
          <>
            {/* Title */}
            <Text style={[styles.title, { color: theme.text }]}>{data.title}</Text>

            {/* Date for Today's Snapshot tab only */}
            {activeTab === 'today' && data.date && (
              <Text style={[styles.dateLabel, { color: theme.textTertiary }]}>{data.date}</Text>
            )}

            {/* Cycles Card (Today only) */}
            {renderCycles()}

            {/* Sections */}
            {data.sections.map((section, index) => renderSection(section, index))}

            {/* Mirror Prompt */}
            {data.mirror_prompt && (
              <View style={[styles.mirrorPromptCard, { backgroundColor: theme.surface, borderLeftColor: theme.accent }]}>
                <Text style={[styles.mirrorPromptLabel, { color: theme.textTertiary }]}>
                  {activeTab === 'today' ? 'REFLECT' : 'REFLECT'}
                </Text>
                <Text style={[styles.mirrorPromptText, { color: theme.text }]}>{data.mirror_prompt}</Text>
              </View>
            )}

            {/* Name Section - driven by profile.numerology_full_name */}
            {renderNameSection()}

            {/* Ask Mirror Button */}
            <TouchableOpacity
              style={[styles.askMirrorButton, { backgroundColor: theme.text }]}
              onPress={onOpenChat}
            >
              <Ionicons name="chatbubble-outline" size={18} color={theme.background} />
              <Text style={[styles.askMirrorText, { color: theme.background }]}>Ask about this lens</Text>
            </TouchableOpacity>

            {/* Footer */}
            <Text style={[styles.footer, { color: theme.textTertiary }]}>
              A lens for noticing patterns, not a prediction of outcomes.
            </Text>
          </>
        ) : null}
      </ScrollView>
      
      {/* Unlock Name Modal */}
      {renderUnlockModal()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "transparent",
  },
  healthBanner: {
    backgroundColor: '#D32F2F',
    paddingVertical: 8,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  healthBannerText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  userIdChangedBanner: {
    backgroundColor: '#FF9800',
    paddingVertical: 8,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  userIdChangedBannerText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
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
    backgroundColor: "transparent",
    alignItems: 'center',
  },
  activeTab: {
    backgroundColor: "transparent",
  },
  tabText: {
    fontSize: 16,
    fontWeight: '500',
    color: "inherit",
  },
  activeTabText: {
    color: "inherit",
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
    fontSize: 16,
    color: "inherit",
  },
  errorContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontSize: 16,
    color: "inherit",
    textAlign: 'center',
  },
  retryButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    backgroundColor: "transparent",
    borderRadius: 8,
  },
  retryText: {
    fontSize: 16,
    color: "inherit",
    fontWeight: '500',
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 14,
  },
  dateLabel: {
    fontSize: 14,
    color: "inherit",
    marginBottom: 16,
  },
  // Core Numbers Card
  coreNumbersCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "transparent",
  },
  coreNumbersTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 1,
    textAlign: 'center',
    marginBottom: 16,
  },
  coreNumbersRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  numberItem: {
    alignItems: 'center',
    flex: 1,
  },
  numberLabel: {
    fontSize: 14,
    color: "inherit",
    marginBottom: 4,
  },
  numberValue: {
    fontSize: 24,
    fontWeight: '600',
    color: "inherit",
  },
  lockedNumber: {
    opacity: 0.5,
  },
  numberDivider: {
    width: 1,
    height: 30,
    backgroundColor: "transparent",
  },
  // Cycles Card
  cyclesCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  cyclesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  cycleItem: {
    alignItems: 'center',
    flex: 1,
  },
  cycleLabel: {
    fontSize: 14,
    color: "inherit",
    marginBottom: 4,
  },
  cycleNumber: {
    fontSize: 24,
    fontWeight: '600',
    color: "inherit",
  },
  cycleDivider: {
    width: 1,
    height: 24,
    backgroundColor: "transparent",
  },
  // Expand Button
  expandButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    marginBottom: 16,
  },
  expandButtonText: {
    fontSize: 16,
    color: "inherit",
    fontWeight: '500',
  },
  // Section Card
  sectionCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionLabel: {
    fontSize: 17,
    fontWeight: '600',
    color: "inherit",
    flex: 1,
  },
  sectionBody: {
    fontSize: 16,
    lineHeight: 30,
    color: "inherit",
    marginTop: 12,
  },
  // Mirror Prompt
  mirrorPromptCard: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
    marginBottom: 16,
  },
  mirrorPromptLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: "inherit",
    letterSpacing: 1,
    marginBottom: 14,
  },
  mirrorPromptText: {
    fontSize: 17,
    lineHeight: 30,
    color: "inherit",
    fontStyle: 'italic',
  },
  // Unlock Prompt
  unlockCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "transparent",
    borderStyle: 'dashed',
  },
  unlockText: {
    flex: 1,
    fontSize: 16,
    color: "inherit",
    lineHeight: 32,
  },
  unlockTextContainer: {
    flex: 1,
  },
  unlockCta: {
    fontSize: 14,
    color: "inherit",
    marginTop: 4,
    fontWeight: '500',
  },
  // Ask Mirror Button
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: "transparent",
    borderRadius: 12,
    paddingVertical: 14,
    marginTop: 8,
  },
  askMirrorText: {
    fontSize: 17,
    fontWeight: '600',
    color: "inherit",
  },
  // Footer
  footer: {
    fontSize: 14,
    color: "inherit",
    textAlign: 'center',
    marginTop: 20,
    fontStyle: 'italic',
  },
  // Unlock Modal Styles - Fixed for mobile web
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  keyboardAvoidingContainer: {
    width: '100%',
    maxHeight: '90%',
  },
  unlockModalContainer: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 24,
    paddingHorizontal: 24,
    ...Platform.select({
      web: { paddingBottom: 24 },
      default: { paddingBottom: 40 },
    }),
    maxHeight: '100%',
    minHeight: 320,
  },
  modalScrollContent: {
    flexGrow: 0,
    flexShrink: 1,
    maxHeight: 280,
  },
  modalScrollContentContainer: {
    paddingBottom: 16,
  },
  modalCloseButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    zIndex: 1,
    padding: 8,
  },
  modalIconContainer: {
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: '600',
    color: "inherit",
    textAlign: 'center',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 16,
    color: "inherit",
    textAlign: 'center',
    marginBottom: 20,
  },
  modalBody: {
    marginBottom: 24,
  },
  modalText: {
    fontSize: 17,
    lineHeight: 30,
    color: "inherit",
    marginBottom: 16,
  },
  bulletList: {
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  bulletItem: {
    fontSize: 16,
    lineHeight: 30,
    color: "inherit",
    marginBottom: 14,
  },
  modalNote: {
    fontSize: 16,
    lineHeight: 32,
    color: "inherit",
    fontStyle: 'italic',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalActionsSticky: {
    flexDirection: 'row',
    gap: 12,
    paddingTop: 16,
    borderTopWidth: 1,
    marginTop: 8,
  },
  modalSecondaryButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    minHeight: 48,
  },
  modalSecondaryButtonText: {
    fontSize: 17,
    fontWeight: '500',
  },
  modalPrimaryButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
    minHeight: 48,
  },
  modalPrimaryButtonText: {
    fontSize: 17,
    fontWeight: '600',
  },
  disabledButton: {
    opacity: 0.6,
  },
  nameInput: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#000000',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    minHeight: 52,
  },
  unlockErrorText: {
    fontSize: 16,
    color: '#e74c3c',
    marginBottom: 16,
  },
  privacyNote: {
    fontSize: 14,
    color: "inherit",
    fontStyle: 'italic',
  },
  // Unlock Button Styles (prominent BLACK button)
  unlockButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 0,
  },
  unlockButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  unlockButtonText: {
    flex: 1,
  },
  unlockButtonTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: "inherit",
    marginBottom: 2,
  },
  unlockButtonSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  // Full Name Display (when entered)
  fullNameCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: "transparent",
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: "transparent",
  },
  fullNameTextContainer: {
    flex: 1,
  },
  fullNameLabel: {
    fontSize: 14,
    color: "inherit",
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  fullNameValue: {
    fontSize: 17,
    color: "inherit",
    fontWeight: '500',
  },
  editNameButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: "transparent",
  },
  modalDebug: {
    marginTop: 12,
    padding: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.05)',
    borderRadius: 6,
  },
  modalDebugText: {
    fontSize: 14,
    color: "inherit",
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
});
