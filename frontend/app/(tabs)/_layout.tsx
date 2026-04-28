import { Tabs } from 'expo-router';
import { Text, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../contexts/ThemeContext';
import SessionRestoreWrapper from '../../components/SessionRestoreWrapper';

export default function TabLayout() {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  // Bottom padding for the tab bar:
  //  * iOS with home indicator (insets.bottom > 0) — use the inset directly
  //  * iOS without home indicator — small padding (6)
  //  * Android — slight padding to avoid hugging the gesture bar
  //  * Web — small default so labels don't hug the Safari bottom bar
  const bottomPadding =
    insets.bottom > 0 ? insets.bottom : Platform.OS === 'android' ? 10 : 6;

  // Overall tab bar height — base 56 for icon + label, plus safe-area bottom.
  const tabBarHeight = 56 + bottomPadding;

  return (
    <SessionRestoreWrapper>
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: theme.tabActive,
          tabBarInactiveTintColor: theme.tabInactive,
          tabBarStyle: {
            backgroundColor: theme.surface,
            borderTopColor: theme.border,
            borderTopWidth: 1,
            height: tabBarHeight,
            paddingBottom: bottomPadding,
            paddingTop: 6,
          },
          // Explicit label style — readable across iPhone preview, Safari
          // bottom bar, and Expo shell. 11px is the RN default — we bump
          // to 12 and ensure proper line height so nothing gets clipped.
          tabBarLabelStyle: {
            fontSize: 12,
            fontWeight: '500',
            lineHeight: 14,
            marginTop: 2,
            marginBottom: 0,
            includeFontPadding: false,
          },
          tabBarIconStyle: {
            marginTop: 2,
          },
          tabBarItemStyle: {
            paddingTop: 4,
          },
          // Keep inactive labels readable (do not fade too much).
          // Default tint already handles this via `tabInactive` color.
          headerStyle: {
            backgroundColor: theme.background,
          },
          headerTintColor: theme.text,
          headerShadowVisible: false,
        }}
      >
        {/* 1. Mirror - Default landing screen */}
        <Tabs.Screen
          name="index"
          options={{
            title: 'Mirror',
            headerShown: false,
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 22 }}>☽</Text>
            ),
          }}
        />

        {/* 2. Life - Lifeline & long-term patterns */}
        <Tabs.Screen
          name="life"
          options={{
            title: 'Life',
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 22 }}>❧</Text>
            ),
          }}
        />

        {/* 3. Reflect - Journal & Mirror tabs (renamed from Journal) */}
        <Tabs.Screen
          name="reflect"
          options={{
            title: 'Reflect',
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 22 }}>◇</Text>
            ),
          }}
        />

        {/* Patterns tab REMOVED - Patterns V1 now lives on Home as "Today's Pattern" */}
        {/* Hide patterns route from tab bar but keep file for potential dev use */}
        <Tabs.Screen
          name="patterns"
          options={{
            href: null,
          }}
        />

        {/* 4. Lenses - Framework explanations */}
        <Tabs.Screen
          name="lenses"
          options={{
            title: 'Lenses',
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 22 }}>◉</Text>
            ),
          }}
        />
      </Tabs>
    </SessionRestoreWrapper>
  );
}
