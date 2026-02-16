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
          tabBarActiveTintColor: Colors.accent,
          tabBarInactiveTintColor: Colors.textTertiary,
          tabBarHideOnKeyboard: true,
          tabBarStyle: {
            backgroundColor: Colors.surface,
            borderTopColor: Colors.border,
            borderTopWidth: 1,
            height: 60,
            paddingBottom: Spacing.xs,
            paddingTop: Spacing.xs,
          },
          headerStyle: {
            backgroundColor: Colors.background,
          },
          headerTintColor: Colors.text,
          headerShadowVisible: false,
          lazy: false,
          unmountOnBlur: false,
        }}
      >
        {/* Mirror tab - using placeholder or real component */}
        <Tabs.Screen
          name="mirror-v2"
          options={{
            title: 'Mirror',
            tabBarIcon: ({ color, size }) => (
              <Ionicons name="moon-outline" size={size} color={color} />
            ),
            headerShown: false,
          }}
        />
        {/* Hide the old index screen */}
        <Tabs.Screen
          name="index"
          options={{
            href: null,
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
      </Tabs>
    </View>
  );
}