/**
 * LensTabBar - Unified Tab Component for All Lens Views
 * ======================================================
 * 
 * A production-grade tab bar designed for mobile screens.
 * 
 * Features:
 * - Single-line tabs with even distribution
 * - Text truncation with ellipsis for long labels
 * - Responsive label shortening for small screens
 * - Gold accent underline on active tab
 * - Works with 3-4 tabs without overflow
 * 
 * Usage:
 * <LensTabBar
 *   tabs={[
 *     { key: 'overview', label: 'Overview' },
 *     { key: 'glance', label: 'At a Glance', shortLabel: 'Glance' },
 *     { key: 'today', label: 'Today' },
 *     { key: 'deep_dive', label: 'Deep Dive' },
 *   ]}
 *   activeTab="overview"
 *   onTabChange={(key) => setActiveTab(key)}
 * />
 */

import React, { useMemo } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  useWindowDimensions,
} from 'react-native';
import { Colors } from '../constants/colors';

export interface LensTab {
  key: string;
  label: string;
  shortLabel?: string; // Optional short label for small screens
}

interface LensTabBarProps {
  tabs: LensTab[];
  activeTab: string;
  onTabChange: (key: string) => void;
}

// Threshold for using short labels (small phone screens)
const SMALL_SCREEN_WIDTH = 380;

export function LensTabBar({ tabs, activeTab, onTabChange }: LensTabBarProps) {
  const { width } = useWindowDimensions();
  const useShortLabels = width < SMALL_SCREEN_WIDTH;

  // Memoize tab labels based on screen width
  const displayTabs = useMemo(() => {
    return tabs.map(tab => ({
      ...tab,
      displayLabel: useShortLabels && tab.shortLabel ? tab.shortLabel : tab.label,
    }));
  }, [tabs, useShortLabels]);

  return (
    <View style={styles.container}>
      <View style={styles.tabRow}>
        {displayTabs.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <TouchableOpacity
              key={tab.key}
              style={styles.tabButton}
              onPress={() => onTabChange(tab.key)}
              activeOpacity={0.7}
            >
              <View style={styles.tabContent}>
                <Text
                  style={[
                    styles.tabLabel,
                    isActive && styles.tabLabelActive,
                  ]}
                  numberOfLines={1}
                  ellipsizeMode="tail"
                >
                  {tab.displayLabel}
                </Text>
              </View>
              {/* Active indicator - gold underline */}
              <View
                style={[
                  styles.indicator,
                  isActive && styles.indicatorActive,
                ]}
              />
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  tabRow: {
    flexDirection: 'row',
    width: '100%',
  },
  tabButton: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 4,
    minWidth: 0, // Critical: allows flex shrink to work properly
  },
  tabContent: {
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 0, // Allow text to truncate
    width: '100%',
    paddingHorizontal: 2,
  },
  tabLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  tabLabelActive: {
    color: Colors.text,
  },
  indicator: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 2,
    backgroundColor: 'transparent',
  },
  indicatorActive: {
    backgroundColor: Colors.accent, // Gold accent
  },
});

export default LensTabBar;
