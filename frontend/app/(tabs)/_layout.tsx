import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../../constants/colors';
import { Spacing } from '../../constants/spacing';

// REMOVED SessionRestoreWrapper - session is already restored in root _layout.tsx
// Having it here caused duplicate restoreSession() calls and potential loops

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        // Active tab uses subtle accent color (muted brass)
        tabBarActiveTintColor: Colors.accent,
        tabBarInactiveTintColor: Colors.textTertiary,
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
        // CRITICAL: Prevent screens from unmounting on tab switch
        // This preserves chat state when switching tabs
        lazy: false,
        unmountOnBlur: false,
      }}
    >
      {/* Use mirror-v2 as the main Mirror tab (loop-proof) */}
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
          href: null,  // Hide from tab bar
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
  );
}