import React, { useState, useEffect, useCallback, useMemo } from 'react';
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
import { Colors } from '../constants/colors';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import Constants from 'expo-constants';
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';

// === V1-SAFE DEV FALLBACK FOR BACKEND URL ===
// Web preview proxy /api is unreliable, so we need a direct backend URL fallback
const DEV_BACKEND_FALLBACK = 'http://localhost:8001'; // Direct backend in dev

function getBackendBaseUrl(): string {
  // 1. Try EXPO_PUBLIC_BACKEND_URL from env (works for all builds)
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl && typeof envUrl === 'string' && envUrl.length > 0) {
    if (__DEV__) {
      console.log('[NumerologyLensView] Using EXPO_PUBLIC_BACKEND_URL:', envUrl);
    }
    return envUrl;
  }
  
  // 2. Try expo-constants extra config
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
  if (extraUrl && typeof extraUrl === 'string' && extraUrl.length > 0) {
    if (__DEV__) {
      console.log('[NumerologyLensView] Using Constants extra URL:', extraUrl);
    }
    return extraUrl;
  }
  
  // 3. For web platform, check if we're in dev/preview mode
  if (Platform.OS === 'web') {
    // Check if hostname indicates local dev or preview environment
    const hostname = typeof window !== 'undefined' ? window.location.hostname : '';
    const isLocalDev = hostname === 'localhost' || hostname === '127.0.0.1';
    const isPreview = hostname.includes('preview') || hostname.includes('emergent');
    
    if (isLocalDev || isPreview) {
      // Use direct backend URL to bypass unreliable proxy
      if (__DEV__) {
        console.log('[NumerologyLensView] Using DEV_BACKEND_FALLBACK:', DEV_BACKEND_FALLBACK);
      }
      return DEV_BACKEND_FALLBACK;
    }
    // Production web: use relative URL (proxy should work)
    return '';
  }
  
  // 4. Native fallback
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
  
  // Modal-only transient state (for input flow, not persistence)
  const [unlockModalVisible, setUnlockModalVisible] = useState(false);
  const [unlockStep, setUnlockStep] = useState<'consent' | 'input' | 'success'>('consent');
  const [modalInputName, setModalInputName] = useState(''); // Transient input only
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [unlockError, setUnlockError] = useState<string | null>(null);
  
  // Debug: track raw API response length
  const [rawDataLength, setRawDataLength] = useState<number>(0);

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
    loadTabData(activeTab);
  }, [activeTab, userId]);

  const loadTabData = async (tab: TabType) => {
    setIsLoading(true);
    setError(null);

    try {
      const endpoint = tab === 'today' 
        ? `/numerology/today/${userId}`
        : tab === 'deep_dive'
        ? `/numerology/deep-dive/${userId}`
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
      <View style={styles.coreNumbersCard}>
        <Text style={styles.coreNumbersTitle}>LIFE PATH • EXPRESSION • SOUL URGE</Text>
        <View style={styles.coreNumbersRow}>
          <View style={styles.numberItem}>
            <Text style={styles.numberLabel}>Life Path</Text>
            <Text style={styles.numberValue}>{formatNumber(numbers.life_path)}</Text>
          </View>
          <View style={styles.numberDivider} />
          <View style={styles.numberItem}>
            <Text style={styles.numberLabel}>Expression</Text>
            <Text style={[
              styles.numberValue, 
              isLocked(numbers.expression) && styles.lockedNumber
            ]}>
              {formatNumber(numbers.expression)}
            </Text>
          </View>
          <View style={styles.numberDivider} />
          <View style={styles.numberItem}>
            <Text style={styles.numberLabel}>Soul Urge</Text>
            <Text style={[
              styles.numberValue, 
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
      <View style={styles.cyclesCard}>
        <View style={styles.cyclesRow}>
          <View style={styles.cycleItem}>
            <Text style={styles.cycleLabel}>Day</Text>
            <Text style={styles.cycleNumber}>{personal_day}</Text>
          </View>
          <View style={styles.cycleDivider} />
          <View style={styles.cycleItem}>
            <Text style={styles.cycleLabel}>Month</Text>
            <Text style={styles.cycleNumber}>{personal_month}</Text>
          </View>
          <View style={styles.cycleDivider} />
          <View style={styles.cycleItem}>
            <Text style={styles.cycleLabel}>Year</Text>
            <Text style={styles.cycleNumber}>{personal_year}</Text>
          </View>
        </View>
      </View>
    );
  };

  const renderSection = (section: NumerologySection, index: number) => {
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

  // === RENDER NAME CARD OR CTA ===
  // Driven SOLELY by profile.numerology_full_name from server
  const renderNameSection = () => {
    // Still loading profile - show nothing yet
    if (profileLoading) {
      return null;
    }
    
    // Name EXISTS in server profile → Show name with Edit button
    if (profile?.numerology_full_name) {
      return (
        <View style={styles.fullNameCard}>
          <Ionicons name="person-outline" size={18} color={Colors.textSecondary} />
          <View style={styles.fullNameTextContainer}>
            <Text style={styles.fullNameLabel}>Full Birth Name</Text>
            <Text style={styles.fullNameValue}>{profile.numerology_full_name}</Text>
          </View>
          <TouchableOpacity 
            style={styles.editNameButton}
            onPress={() => {
              // Pre-fill modal with existing name for editing
              setModalInputName(profile.numerology_full_name || '');
              setUnlockStep('input');
              setUnlockModalVisible(true);
            }}
          >
            <Ionicons name="pencil-outline" size={16} color={Colors.accent} />
          </TouchableOpacity>
        </View>
      );
    }
    
    // Name ABSENT → Show CTA button to add name
    return (
      <TouchableOpacity 
        style={styles.unlockButton}
        onPress={() => {
          setModalInputName(''); // Start fresh
          setUnlockStep('consent');
          setUnlockModalVisible(true);
        }}
        activeOpacity={0.8}
      >
        <View style={styles.unlockButtonContent}>
          <Ionicons name="add-circle-outline" size={22} color={Colors.surface} />
          <View style={styles.unlockButtonText}>
            <Text style={styles.unlockButtonTitle}>Add Full Birth Name</Text>
            <Text style={styles.unlockButtonSubtitle}>Unlock Expression, Soul Urge & Personality numbers</Text>
          </View>
        </View>
        <Ionicons name="chevron-forward" size={20} color="rgba(255, 255, 255, 0.5)" />
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
        console.log('[DEBUG_MIRROR] Saving name via:', unlockUrl);
      }
      
      // POST to save the name
      const saveResponse = await axios.post(unlockUrl, {
        full_birth_name: nameToSave
      }, { timeout: 15000 });
      
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Name save response:', saveResponse.data);
      }
      
      // === READ-AFTER-WRITE: Immediately re-fetch profile to confirm persistence ===
      const profileResponse = await axios.get(profileUrl, { timeout: 10000 });
      const updatedProfile: UserProfile = profileResponse.data;
      
      if (isDebugEnabled()) {
        console.log('[DEBUG_MIRROR] Read-after-write verification:', {
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
      
      // Update local profile state with server-confirmed data
      setProfile(updatedProfile);
      
      // Show success step
      setUnlockStep('success');
      
      // Refresh tab data after a short delay to show updated numbers
      setTimeout(() => {
        loadTabData(activeTab);
      }, 1500);
      
    } catch (err: any) {
      console.error('[PROFILE] Save error:', err);
      setUnlockError('Something went wrong. Please try again.');
    } finally {
      setIsUnlocking(false);
    }
  };

  const closeUnlockModal = () => {
    setUnlockModalVisible(false);
    setUnlockStep('consent');
    setModalInputName(''); // Clear transient input
    setUnlockError(null);
  };

  // Render the unlock modal
  const renderUnlockModal = () => (
    <Modal
      visible={unlockModalVisible}
      animationType="slide"
      transparent={true}
      onRequestClose={closeUnlockModal}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.modalOverlay}
      >
        <View style={styles.unlockModalContainer}>
          {/* Close button */}
          <TouchableOpacity 
            style={styles.modalCloseButton}
            onPress={closeUnlockModal}
          >
            <Ionicons name="close" size={24} color={Colors.textSecondary} />
          </TouchableOpacity>

          {unlockStep === 'consent' && (
            <>
              <View style={styles.modalIconContainer}>
                <Ionicons name="key-outline" size={32} color={Colors.accent} />
              </View>
              <Text style={styles.modalTitle}>Deeper Numerology</Text>
              <Text style={styles.modalSubtitle}>This is optional</Text>
              
              <View style={styles.modalBody}>
                <Text style={styles.modalText}>
                  If you'd like, you can add your full birth name to unlock additional symbolic themes:
                </Text>
                
                <View style={styles.bulletList}>
                  <Text style={styles.bulletItem}>• Expression — how you tend to operate outwardly</Text>
                  <Text style={styles.bulletItem}>• Soul Urge — your inner motivation</Text>
                  <Text style={styles.bulletItem}>• Personality — first impressions you tend to create</Text>
                </View>
                
                <Text style={styles.modalNote}>
                  Your name is used only for numerology calculations. You can continue without this — everything else remains fully available.
                </Text>
              </View>

              <View style={styles.modalActions}>
                <TouchableOpacity 
                  style={styles.modalSecondaryButton}
                  onPress={closeUnlockModal}
                >
                  <Text style={styles.modalSecondaryButtonText}>Maybe later</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={styles.modalPrimaryButton}
                  onPress={() => setUnlockStep('input')}
                >
                  <Text style={styles.modalPrimaryButtonText}>Add my name</Text>
                </TouchableOpacity>
              </View>
            </>
          )}

          {unlockStep === 'input' && (
            <>
              <View style={styles.modalIconContainer}>
                <Ionicons name="person-outline" size={32} color={Colors.accent} />
              </View>
              <Text style={styles.modalTitle}>Your Full Birth Name</Text>
              <Text style={styles.modalSubtitle}>As given at birth</Text>
              
              <View style={styles.modalBody}>
                <Text style={styles.modalText}>
                  Please enter your name exactly as it appears on your birth certificate.
                </Text>
                
                <TextInput
                  style={styles.nameInput}
                  placeholder="Full birth name"
                  placeholderTextColor={Colors.textTertiary}
                  value={modalInputName}
                  onChangeText={setModalInputName}
                  autoCapitalize="words"
                  autoCorrect={false}
                />
                
                {unlockError && (
                  <Text style={styles.unlockErrorText}>{unlockError}</Text>
                )}
                
                <Text style={styles.privacyNote}>
                  Your name is stored securely and used only for these calculations.
                </Text>
              </View>

              <View style={styles.modalActions}>
                <TouchableOpacity 
                  style={styles.modalSecondaryButton}
                  onPress={() => setUnlockStep('consent')}
                >
                  <Text style={styles.modalSecondaryButtonText}>Back</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                  style={[styles.modalPrimaryButton, isUnlocking && styles.disabledButton]}
                  onPress={handleUnlockSubmit}
                  disabled={isUnlocking}
                >
                  {isUnlocking ? (
                    <ActivityIndicator size="small" color={Colors.surface} />
                  ) : (
                    <Text style={styles.modalPrimaryButtonText}>Unlock</Text>
                  )}
                </TouchableOpacity>
              </View>
            </>
          )}

          {unlockStep === 'success' && (
            <>
              <View style={styles.modalIconContainer}>
                <Ionicons name="checkmark-circle" size={48} color={Colors.accent} />
              </View>
              <Text style={styles.modalTitle}>Unlocked</Text>
              <Text style={styles.modalSubtitle}>Deeper numerology is now available</Text>
              
              <View style={styles.modalBody}>
                <Text style={styles.modalText}>
                  Your Expression, Soul Urge, and Personality numbers have been calculated. The view will refresh momentarily.
                </Text>
              </View>

              <TouchableOpacity 
                style={styles.modalPrimaryButton}
                onPress={closeUnlockModal}
              >
                <Text style={styles.modalPrimaryButtonText}>Continue</Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );

  return (
    <View style={styles.container}>
      {/* Backend Unreachable Banner - visible when DEBUG_MIRROR is on and health check failed */}
      {isDebugEnabled() && backendHealthOk === false && (
        <View style={styles.healthBanner}>
          <Ionicons name="warning" size={16} color="#fff" />
          <Text style={styles.healthBannerText}>Backend unreachable</Text>
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
            {/* Still show core numbers on Deep Dive even with error */}
            {activeTab === 'deep_dive' && renderCoreNumbers()}
          </View>
        ) : data ? (
          <>
            {/* Title */}
            <Text style={styles.title}>{data.title}</Text>

            {/* Date for Today's Snapshot tab only */}
            {activeTab === 'today' && data.date && (
              <Text style={styles.dateLabel}>{data.date}</Text>
            )}

            {/* Cycles Card (Today only) */}
            {renderCycles()}

            {/* Core Numbers Card (Deep Dive only) */}
            {activeTab === 'deep_dive' && renderCoreNumbers()}

            {/* Expand Button (Deep Dive only) */}
            {activeTab === 'deep_dive' && (
              <TouchableOpacity
                style={styles.expandButton}
                onPress={() => setExpandedSection(expandedSection ? null : 'all')}
              >
                <Text style={styles.expandButtonText}>
                  {expandedSection ? 'Collapse sections' : 'Explore your numbers'}
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

            {/* Mirror Prompt */}
            {data.mirror_prompt && (
              <View style={styles.mirrorPromptCard}>
                <Text style={styles.mirrorPromptLabel}>
                  {activeTab === 'today' ? 'REFLECT' : activeTab === 'deep_dive' ? 'MIRROR MOMENT' : 'REFLECT'}
                </Text>
                <Text style={styles.mirrorPromptText}>{data.mirror_prompt}</Text>
              </View>
            )}

            {/* Name Section - driven by profile.numerology_full_name */}
            {renderNameSection()}

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
              A lens for noticing patterns, not a prediction of outcomes.
            </Text>
            
            {/* Debug Footer - only shows when DEBUG_MIRROR is enabled */}
            {activeTab === 'deep_dive' && data.sections && (
              <DebugFooter 
                lens="Numerology"
                sections={data.sections}
                source={data.debug_stamp?.source}
                rawDataLength={rawDataLength}
                debugStamp={data.debug_stamp}
                extraDebug={{
                  backend_base_url: BACKEND_BASE_URL || '(relative)',
                  backend_health_ok: backendHealthOk === null ? 'checking...' : backendHealthOk ? 'YES' : 'NO',
                  profile_loaded: profile ? 'YES' : 'NO',
                  numerology_full_name: profile?.numerology_full_name || '(none)',
                  profile_updated_at: profile?.updated_at || '(never)'
                }}
              />
            )}
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
    marginBottom: 16,
  },
  // Core Numbers Card
  coreNumbersCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.surfaceLight,
  },
  coreNumbersTitle: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.textTertiary,
    letterSpacing: 1,
    textAlign: 'center',
    marginBottom: 12,
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
    fontSize: 10,
    color: Colors.textTertiary,
    marginBottom: 4,
  },
  numberValue: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
  },
  lockedNumber: {
    opacity: 0.5,
  },
  numberDivider: {
    width: 1,
    height: 30,
    backgroundColor: Colors.surfaceLight,
  },
  // Cycles Card
  cyclesCard: {
    backgroundColor: Colors.surface,
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
    fontSize: 10,
    color: Colors.textTertiary,
    marginBottom: 4,
  },
  cycleNumber: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.accent,
  },
  cycleDivider: {
    width: 1,
    height: 24,
    backgroundColor: Colors.surfaceLight,
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
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  // Section Card
  sectionCard: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.text,
    flex: 1,
  },
  sectionBody: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginTop: 12,
  },
  // Mirror Prompt
  mirrorPromptCard: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
    marginBottom: 16,
  },
  mirrorPromptLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.accent,
    letterSpacing: 1,
    marginBottom: 8,
  },
  mirrorPromptText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.text,
    fontStyle: 'italic',
  },
  // Unlock Prompt
  unlockCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.accent,
    borderStyle: 'dashed',
  },
  unlockText: {
    flex: 1,
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  unlockTextContainer: {
    flex: 1,
  },
  unlockCta: {
    fontSize: 12,
    color: Colors.accent,
    marginTop: 4,
    fontWeight: '500',
  },
  // Ask Mirror Button
  askMirrorButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 14,
    marginTop: 8,
  },
  askMirrorText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.surface,
  },
  // Footer
  footer: {
    fontSize: 12,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 20,
    fontStyle: 'italic',
  },
  // Unlock Modal Styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  unlockModalContainer: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    paddingBottom: 40,
    maxHeight: '85%',
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
    color: Colors.text,
    textAlign: 'center',
    marginBottom: 4,
  },
  modalSubtitle: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginBottom: 20,
  },
  modalBody: {
    marginBottom: 24,
  },
  modalText: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 16,
  },
  bulletList: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  bulletItem: {
    fontSize: 14,
    lineHeight: 22,
    color: Colors.text,
    marginBottom: 8,
  },
  modalNote: {
    fontSize: 13,
    lineHeight: 20,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  modalSecondaryButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 12,
    backgroundColor: Colors.surface,
  },
  modalSecondaryButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: Colors.textSecondary,
  },
  modalPrimaryButton: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderRadius: 12,
    backgroundColor: Colors.text,
  },
  modalPrimaryButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.surface,
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
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
    minHeight: 52,
  },
  unlockErrorText: {
    fontSize: 13,
    color: '#e74c3c',
    marginBottom: 12,
  },
  privacyNote: {
    fontSize: 12,
    color: Colors.textTertiary,
    fontStyle: 'italic',
  },
  // Unlock Button Styles (prominent BLACK button)
  unlockButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Colors.text,
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
    fontSize: 15,
    fontWeight: '600',
    color: Colors.surface,
    marginBottom: 2,
  },
  unlockButtonSubtitle: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  // Full Name Display (when entered)
  fullNameCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: Colors.surfaceLight,
  },
  fullNameTextContainer: {
    flex: 1,
  },
  fullNameLabel: {
    fontSize: 12,
    color: Colors.textTertiary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  fullNameValue: {
    fontSize: 15,
    color: Colors.text,
    fontWeight: '500',
  },
  editNameButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: Colors.surfaceLight,
  },
});
