import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, Text } from 'react-native';
import { Colors } from '../../constants/colors';
import { Spacing } from '../../constants/spacing';

// STEP 5: MIRROR TAB PLACEHOLDER - No imports from mirror-v2
// If this crashes, the issue is in tabs/_layout or root layout, not Mirror code
const MirrorPlaceholder = () => (
  <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a1a' }}>
    <Text style={{ color: '#0f0', fontSize: 18, fontWeight: 'bold' }}>MIRROR TAB PLACEHOLDER</Text>
    <Text style={{ color: '#888', fontSize: 14, marginTop: 8 }}>No store, no effects, no imports</Text>
    <Text style={{ color: '#666', fontSize: 12, marginTop: 16 }}>If you see this, the tab can render.</Text>
  </View>
);

// Feature flag to use placeholder vs real mirror-v2
const USE_PLACEHOLDER = true; // Set to false to use real mirror-v2

export default function TabLayout() {
  return (
    <View style={{ flex: 1 }}>
      <Tabs
        screenOptions={{
          // Active/Inactive colors - improved contrast
          tabBarActiveTintColor: Colors.accent,
          tabBarInactiveTintColor: '#888888', // Brighter than textTertiary for better visibility
          tabBarHideOnKeyboard: true,
          
          // Tab bar container - more prominent
          tabBarStyle: {
            backgroundColor: '#1E2023', // Slightly lighter than page background for separation
            borderTopColor: 'rgba(255, 255, 255, 0.08)', // Subtle light border for definition
            borderTopWidth: 1,
            height: 72, // Increased height for better tap targets
            paddingBottom: Spacing.sm, // More bottom padding for safe area
            paddingTop: Spacing.xs,
            // Subtle shadow for depth
            shadowColor: '#000',
            shadowOffset: { width: 0, height: -2 },
            shadowOpacity: 0.15,
            shadowRadius: 8,
            elevation: 8,
          },
          
          // Tab item styling
          tabBarItemStyle: {
            paddingVertical: Spacing.xxs, // Comfortable tap area
          },
          
          // Label styling - more readable
          tabBarLabelStyle: {
            fontSize: 11, // Slightly larger for readability
            fontWeight: '600', // Semi-bold for better visibility
            marginTop: 2,
          },
          
          // Active indicator - subtle pill background
          tabBarActiveBackgroundColor: 'rgba(201, 169, 98, 0.12)', // Soft accent glow
          
          // Icon styling
          tabBarIconStyle: {
            marginTop: 4,
          },
          
          headerStyle: {
            backgroundColor: Colors.background,
          },
          headerTintColor: Colors.text,
          headerShadowVisible: false,
          headerShown: false, // Hide header by default for all tabs
          lazy: false,
          unmountOnBlur: false,
        }}
      >
        {/* Mirror tab - The real Home screen */}
        <Tabs.Screen
          name="index"
          options={{
            title: 'Mirror',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="moon-outline" size={size} color={color} />
            ),
            headerShown: false,
          }}
        />
        {/* Hide debug mirror-v2 screen from normal navigation */}
        <Tabs.Screen
          name="mirror-v2"
          options={{
            href: null, // Hide from tab bar
            headerShown: false,
          }}
        />
        <Tabs.Screen
          name="life"
          options={{
            title: 'Life',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="leaf-outline" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="journal"
          options={{
            title: 'Journal',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="book-outline" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="lenses"
          options={{
            title: 'Lenses',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="eye-outline" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="inbox"
          options={{
            title: 'Inbox',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="notifications-outline" size={size} color={color} />
            ),
          }}
        />
      </Tabs>
    </View>
  );
}