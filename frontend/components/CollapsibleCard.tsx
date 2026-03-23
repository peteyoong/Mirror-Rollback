// ============================================
// COLLAPSIBLE CARD COMPONENT
// ============================================
// Reusable card with expand/collapse functionality
// For reducing scroll fatigue and progressive disclosure

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Animated,
  StyleSheet,
  LayoutAnimation,
  Platform,
  UIManager,
} from 'react-native';
import { useTheme } from '../contexts/ThemeContext';

// Enable LayoutAnimation for Android
if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

export interface CollapsibleCardProps {
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  accentColor?: string;
  // Badge for counts like "9 centers" or "22 gates"
  badge?: string;
  // Children rendered when expanded
  children: React.ReactNode;
  // Lazy render - only mount children when first expanded
  lazyRender?: boolean;
  // Callback when toggle state changes
  onToggle?: (isOpen: boolean) => void;
  // Custom styling
  containerStyle?: object;
  // Priority indicator (for sorting/highlighting)
  priority?: 'high' | 'medium' | 'low';
}

export const CollapsibleCard: React.FC<CollapsibleCardProps> = ({
  title,
  subtitle,
  defaultOpen = false,
  accentColor,
  badge,
  children,
  lazyRender = true,
  onToggle,
  containerStyle,
  priority,
}) => {
  const { theme } = useTheme();
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [hasBeenOpened, setHasBeenOpened] = useState(defaultOpen);
  const rotateAnim = useRef(new Animated.Value(defaultOpen ? 1 : 0)).current;

  // Determine accent color
  const cardAccent = accentColor || theme.accent;
  
  // Priority-based left border
  const borderColor = priority === 'high' 
    ? theme.accent 
    : priority === 'medium' 
      ? theme.textSecondary 
      : theme.border;

  useEffect(() => {
    Animated.timing(rotateAnim, {
      toValue: isOpen ? 1 : 0,
      duration: 200,
      useNativeDriver: true,
    }).start();
  }, [isOpen]);

  const toggleExpand = () => {
    // Configure smooth layout animation
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    
    const newState = !isOpen;
    setIsOpen(newState);
    
    // Track if it's been opened (for lazy rendering)
    if (newState && !hasBeenOpened) {
      setHasBeenOpened(true);
    }
    
    // Notify parent
    onToggle?.(newState);
  };

  const chevronRotation = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '180deg'],
  });

  // Lazy render: only render content after first open
  const shouldRenderContent = lazyRender ? hasBeenOpened : true;

  return (
    <View 
      style={[
        styles.container, 
        { 
          backgroundColor: theme.surface, 
          borderColor: theme.border,
          borderLeftColor: borderColor,
        },
        containerStyle
      ]}
    >
      {/* Header - Always Visible */}
      <TouchableOpacity 
        style={styles.header}
        onPress={toggleExpand}
        activeOpacity={0.7}
      >
        <View style={styles.headerLeft}>
          <View style={styles.titleRow}>
            <Text style={[styles.title, { color: theme.text }]}>
              {title}
            </Text>
            {badge && (
              <View style={[styles.badge, { backgroundColor: theme.background }]}>
                <Text style={[styles.badgeText, { color: theme.textSecondary }]}>
                  {badge}
                </Text>
              </View>
            )}
          </View>
          {subtitle && (
            <Text style={[styles.subtitle, { color: theme.textTertiary }]}>
              {subtitle}
            </Text>
          )}
        </View>
        
        {/* Chevron */}
        <Animated.View style={{ transform: [{ rotate: chevronRotation }] }}>
          <Text style={[styles.chevron, { color: theme.textSecondary }]}>
            ▼
          </Text>
        </Animated.View>
      </TouchableOpacity>

      {/* Content - Expandable */}
      {isOpen && shouldRenderContent && (
        <View style={[styles.content, { borderTopColor: theme.border }]}>
          {children}
        </View>
      )}
    </View>
  );
};

// ============================================
// NESTED COLLAPSIBLE (for sub-items)
// ============================================
// Lighter weight version for nested items like individual centers/gates

export interface NestedCollapsibleProps {
  title: string;
  subtitle?: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  lazyRender?: boolean;
  // Status indicator
  status?: 'defined' | 'undefined' | 'active' | 'dormant';
}

export const NestedCollapsible: React.FC<NestedCollapsibleProps> = ({
  title,
  subtitle,
  defaultOpen = false,
  children,
  lazyRender = true,
  status,
}) => {
  const { theme } = useTheme();
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [hasBeenOpened, setHasBeenOpened] = useState(defaultOpen);
  const rotateAnim = useRef(new Animated.Value(defaultOpen ? 1 : 0)).current;

  // Status color mapping
  const statusColors = {
    defined: theme.accent,
    undefined: theme.textTertiary,
    active: theme.success || '#4CAF50',
    dormant: theme.textTertiary,
  };

  const statusColor = status ? statusColors[status] : theme.textSecondary;

  useEffect(() => {
    Animated.timing(rotateAnim, {
      toValue: isOpen ? 1 : 0,
      duration: 150,
      useNativeDriver: true,
    }).start();
  }, [isOpen]);

  const toggleExpand = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    
    const newState = !isOpen;
    setIsOpen(newState);
    
    if (newState && !hasBeenOpened) {
      setHasBeenOpened(true);
    }
  };

  const chevronRotation = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '90deg'],
  });

  const shouldRenderContent = lazyRender ? hasBeenOpened : true;

  return (
    <View style={[styles.nestedContainer, { borderColor: theme.border }]}>
      <TouchableOpacity 
        style={styles.nestedHeader}
        onPress={toggleExpand}
        activeOpacity={0.7}
      >
        <Animated.View style={{ transform: [{ rotate: chevronRotation }] }}>
          <Text style={[styles.nestedChevron, { color: theme.textTertiary }]}>
            ▶
          </Text>
        </Animated.View>
        
        <View style={styles.nestedTitleContainer}>
          <View style={styles.nestedTitleRow}>
            {status && (
              <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
            )}
            <Text style={[styles.nestedTitle, { color: theme.text }]}>
              {title}
            </Text>
          </View>
          {subtitle && (
            <Text style={[styles.nestedSubtitle, { color: theme.textTertiary }]}>
              {subtitle}
            </Text>
          )}
        </View>
      </TouchableOpacity>

      {isOpen && shouldRenderContent && (
        <View style={[styles.nestedContent, { borderLeftColor: statusColor }]}>
          {children}
        </View>
      )}
    </View>
  );
};

// ============================================
// SECTION HEADER (for grouping collapsibles)
// ============================================

export interface SectionHeaderProps {
  title: string;
  count?: number;
  icon?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  count,
  icon,
}) => {
  const { theme } = useTheme();

  return (
    <View style={[styles.sectionHeader, { borderBottomColor: theme.border }]}>
      {icon && <Text style={styles.sectionIcon}>{icon}</Text>}
      <Text style={[styles.sectionTitle, { color: theme.textSecondary }]}>
        {title}
      </Text>
      {count !== undefined && (
        <Text style={[styles.sectionCount, { color: theme.textTertiary }]}>
          ({count})
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  // Main Collapsible Card
  container: {
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 3,
    marginBottom: 12,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  headerLeft: {
    flex: 1,
    marginRight: 12,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '500',
  },
  subtitle: {
    fontSize: 13,
    marginTop: 4,
    lineHeight: 18,
  },
  chevron: {
    fontSize: 12,
  },
  content: {
    padding: 16,
    paddingTop: 0,
    borderTopWidth: 0,
  },

  // Nested Collapsible
  nestedContainer: {
    marginBottom: 8,
    borderRadius: 8,
    borderWidth: 1,
    overflow: 'hidden',
  },
  nestedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    paddingLeft: 8,
  },
  nestedChevron: {
    fontSize: 10,
    marginRight: 8,
  },
  nestedTitleContainer: {
    flex: 1,
  },
  nestedTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  nestedTitle: {
    fontSize: 14,
    fontWeight: '500',
  },
  nestedSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  nestedContent: {
    paddingHorizontal: 12,
    paddingBottom: 12,
    paddingTop: 4,
    marginLeft: 18,
    borderLeftWidth: 2,
  },

  // Section Header
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 4,
    marginBottom: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  sectionIcon: {
    fontSize: 14,
    marginRight: 8,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  sectionCount: {
    fontSize: 12,
    marginLeft: 4,
  },
});

export default CollapsibleCard;
