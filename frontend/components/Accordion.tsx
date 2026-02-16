/**
 * Accordion - Collapsible section component for structured content
 * 
 * Used in Deep Dive views to create scannable, modular content.
 * Supports:
 * - Header with title and optional subtitle
 * - Chevron indicator for expand/collapse state
 * - Animated height transition (optional)
 * - Mirror-safe styling
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../constants/colors';

// Enable LayoutAnimation on Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface AccordionProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  onToggle?: (expanded: boolean) => void;
  style?: object;
  headerStyle?: object;
  contentStyle?: object;
  testID?: string;
}

/**
 * Accordion component for collapsible content sections.
 * 
 * Usage:
 *   <Accordion title="Core Strategy" subtitle="Your primary pattern" defaultExpanded>
 *     <Text>Content here...</Text>
 *   </Accordion>
 */
export function Accordion({
  title,
  subtitle,
  children,
  defaultExpanded = false,
  onToggle,
  style,
  headerStyle,
  contentStyle,
  testID,
}: AccordionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const handleToggle = useCallback(() => {
    // Animate the layout change for smooth expand/collapse
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    
    const newState = !expanded;
    setExpanded(newState);
    onToggle?.(newState);
  }, [expanded, onToggle]);

  return (
    <View style={[styles.container, style]} testID={testID}>
      <TouchableOpacity
        style={[styles.header, headerStyle]}
        onPress={handleToggle}
        activeOpacity={0.7}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
        accessibilityLabel={`${title}${subtitle ? `, ${subtitle}` : ''}`}
      >
        <View style={styles.headerContent}>
          <Text style={styles.title}>{title}</Text>
          {subtitle && (
            <Text style={styles.subtitle} numberOfLines={1}>
              {subtitle}
            </Text>
          )}
        </View>
        <View style={styles.chevronContainer}>
          <Ionicons
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={20}
            color={Colors.textSecondary}
          />
        </View>
      </TouchableOpacity>
      
      {expanded && (
        <View style={[styles.content, contentStyle]}>
          {children}
        </View>
      )}
    </View>
  );
}

/**
 * AccordionGroup - Manages multiple accordions with optional single-expand behavior
 */
interface AccordionGroupProps {
  children: React.ReactNode;
  singleExpand?: boolean; // Only one accordion open at a time
}

export function AccordionGroup({ children, singleExpand = false }: AccordionGroupProps) {
  // For now, just render children - can add single-expand logic later
  return <View style={styles.group}>{children}</View>;
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    minHeight: 56,
  },
  headerContent: {
    flex: 1,
    marginRight: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
    letterSpacing: 0.2,
  },
  subtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 2,
    fontStyle: 'italic',
  },
  chevronContainer: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 0,
  },
  group: {
    // Group container styling
  },
});

export default Accordion;
