/**
 * Accordion - Collapsible section component for structured content
 * 
 * Supports both CONTROLLED and UNCONTROLLED modes:
 * - Controlled: Pass `expanded` and `onToggle` props (for single-expand groups)
 * - Uncontrolled: Use `defaultExpanded` (for standalone accordions)
 * 
 * Features:
 * - Smooth LayoutAnimation on expand/collapse
 * - Chevron rotation indicator
 * - Subtitle/teaser support
 * - Accessibility (aria-expanded, button role)
 * - Large touch targets
 */

import React, { useState, useCallback, useMemo } from 'react';
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

// Custom animation config for smoother transitions
const ACCORDION_ANIMATION = {
  duration: 250,
  create: {
    type: LayoutAnimation.Types.easeInEaseOut,
    property: LayoutAnimation.Properties.opacity,
  },
  update: {
    type: LayoutAnimation.Types.easeInEaseOut,
  },
  delete: {
    type: LayoutAnimation.Types.easeInEaseOut,
    property: LayoutAnimation.Properties.opacity,
  },
};

interface AccordionProps {
  /** Section ID for controlled mode */
  id?: string;
  /** Section title */
  title: string;
  /** Optional subtitle/teaser shown below title */
  subtitle?: string;
  /** Content to show when expanded */
  children: React.ReactNode;
  /** Default expanded state (uncontrolled mode) */
  defaultExpanded?: boolean;
  /** Controlled expanded state */
  expanded?: boolean;
  /** Called when toggle is requested */
  onToggle?: (expanded: boolean, id?: string) => void;
  /** Container style override */
  style?: object;
  /** Header style override */
  headerStyle?: object;
  /** Content style override */
  contentStyle?: object;
  /** Test ID for automation */
  testID?: string;
}

/**
 * Accordion component for collapsible content sections.
 * 
 * UNCONTROLLED Usage (standalone):
 *   <Accordion title="Section" defaultExpanded>
 *     <Text>Content</Text>
 *   </Accordion>
 * 
 * CONTROLLED Usage (single-expand group):
 *   <Accordion 
 *     id="section1"
 *     title="Section"
 *     expanded={openId === 'section1'}
 *     onToggle={(_, id) => setOpenId(openId === id ? null : id)}
 *   >
 *     <Text>Content</Text>
 *   </Accordion>
 */
export function Accordion({
  id,
  title,
  subtitle,
  children,
  defaultExpanded = false,
  expanded: controlledExpanded,
  onToggle,
  style,
  headerStyle,
  contentStyle,
  testID,
}: AccordionProps) {
  // Internal state for uncontrolled mode
  const [internalExpanded, setInternalExpanded] = useState(defaultExpanded);
  
  // Determine if we're in controlled mode
  const isControlled = controlledExpanded !== undefined;
  const isExpanded = isControlled ? controlledExpanded : internalExpanded;

  const handleToggle = useCallback(() => {
    // Animate the layout change for smooth expand/collapse
    LayoutAnimation.configureNext(ACCORDION_ANIMATION);
    
    if (isControlled) {
      // Controlled mode: delegate to parent
      onToggle?.(!isExpanded, id);
    } else {
      // Uncontrolled mode: manage internal state
      const newState = !internalExpanded;
      setInternalExpanded(newState);
      onToggle?.(newState, id);
    }
  }, [isControlled, isExpanded, internalExpanded, onToggle, id]);

  // Memoize the content to prevent unnecessary re-renders
  const contentView = useMemo(() => {
    if (!isExpanded) return null;
    return (
      <View style={[styles.content, contentStyle]}>
        {children}
      </View>
    );
  }, [isExpanded, children, contentStyle]);

  return (
    <View style={[styles.container, isExpanded && styles.containerExpanded, style]} testID={testID}>
      <TouchableOpacity
        style={[styles.header, headerStyle]}
        onPress={handleToggle}
        activeOpacity={0.6}
        accessibilityRole="button"
        accessibilityState={{ expanded: isExpanded }}
        accessibilityLabel={`${title}${subtitle ? `, ${subtitle}` : ''}. ${isExpanded ? 'Collapse' : 'Expand'}`}
        accessibilityHint={isExpanded ? 'Double tap to collapse' : 'Double tap to expand'}
      >
        <View style={styles.headerContent}>
          <Text style={[styles.title, isExpanded && styles.titleExpanded]}>{title}</Text>
          {subtitle && (
            <Text style={styles.subtitle} numberOfLines={1}>
              {subtitle}
            </Text>
          )}
        </View>
        <View style={[styles.chevronContainer, isExpanded && styles.chevronExpanded]}>
          <Ionicons
            name={isExpanded ? 'chevron-up' : 'chevron-down'}
            size={20}
            color={isExpanded ? Colors.accent : Colors.textSecondary}
          />
        </View>
      </TouchableOpacity>
      
      {contentView}
    </View>
  );
}

/**
 * AccordionGroup - Container for single-expand accordion behavior
 * 
 * Usage:
 *   const [openId, setOpenId] = useState<string | null>('section1');
 *   
 *   <AccordionGroup>
 *     <Accordion 
 *       id="section1" 
 *       expanded={openId === 'section1'}
 *       onToggle={(_, id) => setOpenId(openId === id ? null : id)}
 *     />
 *   </AccordionGroup>
 */
interface AccordionGroupProps {
  children: React.ReactNode;
  style?: object;
}

export function AccordionGroup({ children, style }: AccordionGroupProps) {
  return <View style={[styles.group, style]}>{children}</View>;
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 12,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
  },
  containerExpanded: {
    borderColor: Colors.accent + '40', // 25% opacity accent
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
    paddingHorizontal: 16,
    minHeight: 60, // Larger touch target
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
  titleExpanded: {
    color: Colors.accent,
  },
  subtitle: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginTop: 3,
    fontStyle: 'italic',
    lineHeight: 18,
  },
  chevronContainer: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
    backgroundColor: 'transparent',
  },
  chevronExpanded: {
    backgroundColor: Colors.accent + '15', // 10% opacity accent
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    paddingTop: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: Colors.border,
  },
  group: {
    // Group container styling
  },
});

export default Accordion;
