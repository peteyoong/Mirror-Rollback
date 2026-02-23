/**
 * LensTabBar - Unified Tab Component for All Lens Views
 * ======================================================
 * 
 * A production-grade tab bar designed for mobile screens.
 * 
 * Features:
 * - Horizontal scrolling for 4+ tabs on small screens
 * - Pill-style active indicator (no underline)
 * - Single-line text with ellipsis (never wraps)
 * - Gold accent for active tab
 * - Dark theme consistent with Mirror app
 * 
 * Usage:
 * <LensTabBar
 *   tabs={[
 *     { key: 'overview', label: 'Overview' },
 *     { key: 'glance', label: 'At a Glance' },
 *     { key: 'today', label: 'Today' },
 *     { key: 'deep_dive', label: 'Deep Dive' },
 *   ]}
 *   activeTab="overview"
 *   onTabChange={(key) => setActiveTab(key)}
 * />
 */

import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { Colors } from '../constants/colors';

export interface LensTab {
  key: string;
  label: string;
  shortLabel?: string; // Optional (not used in scroll mode)
}

interface LensTabBarProps {
  tabs: LensTab[];
  activeTab: string;
  onTabChange: (key: string) => void;
}

export function LensTabBar({ tabs, activeTab, onTabChange }: LensTabBarProps) {
  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.tabsContent}
        style={styles.tabsScroll}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              style={[
                styles.tabButton,
                isActive && styles.tabButtonActive,
              ]}
              onPress={() => onTabChange(tab.key)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.tabLabel,
                  isActive && styles.tabLabelActive,
                ]}
                numberOfLines={1}
                ellipsizeMode="tail"
              >
                {tab.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  tabsScroll: {
    marginTop: 8,
    marginBottom: 10,
  },
  tabsContent: {
    paddingHorizontal: 14,
    gap: 10,
    alignItems: 'center',
  },
  tabButton: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    minHeight: 36,
    minWidth: 80,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabButtonActive: {
    backgroundColor: 'rgba(201, 169, 98, 0.16)', // Subtle gold pill
  },
  tabLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
  },
  tabLabelActive: {
    color: Colors.accent, // Gold (#C9A962)
  },
});

export default LensTabBar;
