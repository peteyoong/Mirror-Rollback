/**
 * LifelineAddMenu
 * 
 * Action sheet / bottom sheet for adding content to Lifeline.
 * Provides multiple entry points:
 * - Add moment manually
 * - Import spreadsheet
 * - Import PowerPoint
 * - View imported sources
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Modal,
  Pressable,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../../contexts/ThemeContext';
import { useRouter } from 'expo-router';

interface Props {
  visible: boolean;
  onClose: () => void;
  onAddManually: () => void;
  onViewSources: () => void;
  hasImportedSources?: boolean;
  importedSourceCount?: number;
}

interface MenuOption {
  id: string;
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle: string;
  onPress: () => void;
  comingSoon?: boolean;
  badge?: string | number;
}

export default function LifelineAddMenu({
  visible,
  onClose,
  onAddManually,
  onViewSources,
  hasImportedSources = false,
  importedSourceCount = 0,
}: Props) {
  const { theme, isDark } = useTheme();
  const router = useRouter();

  const handleImportSpreadsheet = () => {
    onClose();
    router.push('/lifeline-upload');
  };

  const handleImportPowerPoint = () => {
    onClose();
    router.push({
      pathname: '/lifeline-upload',
      params: { preferredType: 'pptx' },
    });
  };

  const menuOptions: MenuOption[] = [
    {
      id: 'manual',
      icon: 'create-outline',
      title: 'Add moment manually',
      subtitle: 'Write about a memory that shaped you',
      onPress: () => {
        onClose();
        onAddManually();
      },
    },
    {
      id: 'spreadsheet',
      icon: 'document-text-outline',
      title: 'Import spreadsheet',
      subtitle: 'Excel or CSV with your life events',
      onPress: handleImportSpreadsheet,
    },
    {
      id: 'pptx',
      icon: 'easel-outline',
      title: 'Import PowerPoint',
      subtitle: 'Slides from a lifeline deck',
      onPress: handleImportPowerPoint,
    },
    {
      id: 'sources',
      icon: 'layers-outline',
      title: 'View imported sources',
      subtitle: hasImportedSources 
        ? `${importedSourceCount} source${importedSourceCount !== 1 ? 's' : ''} imported`
        : 'See what you\'ve imported',
      onPress: () => {
        onClose();
        onViewSources();
      },
      badge: importedSourceCount > 0 ? importedSourceCount : undefined,
    },
    {
      id: 'pdf',
      icon: 'document-outline',
      title: 'Import PDF',
      subtitle: 'Extract moments from documents',
      onPress: () => {},
      comingSoon: true,
    },
    {
      id: 'image',
      icon: 'image-outline',
      title: 'Import from image',
      subtitle: 'OCR text from photos',
      onPress: () => {},
      comingSoon: true,
    },
  ];

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <Pressable style={styles.backdrop} onPress={onClose}>
        <View style={styles.backdropInner} />
      </Pressable>
      
      <View style={styles.sheetContainer} pointerEvents="box-none">
        <View style={[styles.sheet, { backgroundColor: theme.surface }]}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.handle} />
            <Text style={[styles.title, { color: theme.text }]}>
              Add to Lifeline
            </Text>
            <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
              Import moments from multiple sources. We'll review and merge them into your timeline.
            </Text>
          </View>

          {/* Menu Options */}
          <View style={styles.optionsContainer}>
            {menuOptions.map((option, index) => (
              <TouchableOpacity
                key={option.id}
                style={[
                  styles.option,
                  { borderBottomColor: theme.border },
                  index === menuOptions.length - 1 && styles.lastOption,
                  option.comingSoon && styles.optionDisabled,
                ]}
                onPress={option.onPress}
                disabled={option.comingSoon}
                activeOpacity={0.7}
              >
                <View style={[
                  styles.iconContainer,
                  { backgroundColor: option.comingSoon ? theme.border : theme.accent + '15' }
                ]}>
                  <Ionicons
                    name={option.icon}
                    size={22}
                    color={option.comingSoon ? theme.textTertiary : theme.accent}
                  />
                </View>
                
                <View style={styles.optionContent}>
                  <View style={styles.optionTitleRow}>
                    <Text style={[
                      styles.optionTitle,
                      { color: option.comingSoon ? theme.textTertiary : theme.text }
                    ]}>
                      {option.title}
                    </Text>
                    {option.comingSoon && (
                      <View style={[styles.comingSoonBadge, { backgroundColor: theme.border }]}>
                        <Text style={[styles.comingSoonText, { color: theme.textTertiary }]}>
                          Coming soon
                        </Text>
                      </View>
                    )}
                    {option.badge && (
                      <View style={[styles.badge, { backgroundColor: theme.accent }]}>
                        <Text style={styles.badgeText}>{option.badge}</Text>
                      </View>
                    )}
                  </View>
                  <Text style={[
                    styles.optionSubtitle,
                    { color: option.comingSoon ? theme.textTertiary : theme.textSecondary }
                  ]}>
                    {option.subtitle}
                  </Text>
                </View>
                
                {!option.comingSoon && (
                  <Ionicons
                    name="chevron-forward"
                    size={18}
                    color={theme.textTertiary}
                  />
                )}
              </TouchableOpacity>
            ))}
          </View>

          {/* Cancel Button */}
          <TouchableOpacity
            style={[styles.cancelButton, { backgroundColor: theme.background }]}
            onPress={onClose}
          >
            <Text style={[styles.cancelText, { color: theme.text }]}>Cancel</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
  },
  backdropInner: {
    flex: 1,
  },
  sheetContainer: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'flex-end',
  },
  sheet: {
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingBottom: Platform.OS === 'ios' ? 34 : 20,
    maxHeight: '85%',
  },
  header: {
    alignItems: 'center',
    paddingTop: 12,
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  handle: {
    width: 36,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(128, 128, 128, 0.3)',
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    letterSpacing: -0.3,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: 20,
  },
  optionsContainer: {
    paddingHorizontal: 16,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 4,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  lastOption: {
    borderBottomWidth: 0,
  },
  optionDisabled: {
    opacity: 0.6,
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  optionContent: {
    flex: 1,
  },
  optionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '500',
  },
  optionSubtitle: {
    fontSize: 13,
    marginTop: 2,
  },
  comingSoonBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  comingSoonText: {
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  badge: {
    minWidth: 20,
    height: 20,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  cancelButton: {
    marginHorizontal: 16,
    marginTop: 12,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  cancelText: {
    fontSize: 16,
    fontWeight: '500',
  },
});
