import React, { useState, useEffect } from 'react';
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
import api from '../services/api';
import DebugFooter, { SectionDebug, isDebugEnabled } from './DebugFooter';

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
  
  // Unlock flow state
  const [unlockModalVisible, setUnlockModalVisible] = useState(false);
  const [unlockStep, setUnlockStep] = useState<'consent' | 'input' | 'success'>('consent');
  const [fullBirthName, setFullBirthName] = useState('');
  const [isUnlocking, setIsUnlocking] = useState(false);
  const [unlockError, setUnlockError] = useState<string | null>(null);

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
          <Text style={styles.sectionBody}>{section.body}</Text>
        )}
      </View>
    );
  };

  const renderUnlockPrompt = () => {
    // If unlock is not required, show the full name if available
    if (!data?.unlock_required && data?.full_birth_name) {
      return (
        <View style={styles.fullNameCard}>
          <Ionicons name="person-outline" size={18} color={Colors.textSecondary} />
          <View style={styles.fullNameTextContainer}>
            <Text style={styles.fullNameLabel}>Full Birth Name</Text>
            <Text style={styles.fullNameValue}>{data.full_birth_name}</Text>
          </View>
        </View>
      );
    }
    
    // If unlock is required, show a prominent button
    if (data?.unlock_required || data?.unlock_prompt) {
      return (
        <TouchableOpacity 
          style={styles.unlockButton}
          onPress={() => {
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
    }
    
    return null;
  };

  // Handle unlock flow
  const handleUnlockSubmit = async () => {
    if (!fullBirthName.trim()) {
      setUnlockError('Please enter your full birth name');
      return;
    }

    setIsUnlocking(true);
    setUnlockError(null);

    try {
      await api.post(`/numerology/unlock-name/${userId}`, {
        full_birth_name: fullBirthName.trim()
      });
      
      setUnlockStep('success');
      
      // Refresh data after a short delay
      setTimeout(() => {
        loadTabData(activeTab);
      }, 2000);
      
    } catch (err: any) {
      console.error('Unlock error:', err);
      setUnlockError('Something went wrong. Please try again.');
    } finally {
      setIsUnlocking(false);
    }
  };

  const closeUnlockModal = () => {
    setUnlockModalVisible(false);
    setUnlockStep('consent');
    setFullBirthName('');
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
                  value={fullBirthName}
                  onChangeText={setFullBirthName}
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

            {/* Unlock Prompt (if name-based numbers locked) */}
            {renderUnlockPrompt()}

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
});
