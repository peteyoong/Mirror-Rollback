import { Tabs } from 'expo-router';
import { Text, Platform, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../contexts/ThemeContext';
import SessionRestoreWrapper from '../../components/SessionRestoreWrapper';

// Build marker — temporary visible flag to confirm the tab-bar fix is
// actually running on the user's device. Remove after verification.
const NAV_FIX_MARKER = 'Nav fix v2';

export default function TabLayout() {
  const { theme } = useTheme();
  const insets = useSafeAreaInsets();

  // Bottom padding for the tab bar.
  // On mobile web (Safari / Expo Go web preview), the viewport often does
  // NOT report a `bottom` inset even though Safari's bottom chrome covers
  // the last ~30-50px. We therefore add a generous web baseline so labels
  // are never clipped by the browser bar.
  let bottomPadding: number;
  if (Platform.OS === 'web') {
    // Web preview: protect against Safari bottom bar + Expo shell overlay.
    bottomPadding = Math.max(insets.bottom, 20);
  } else if (Platform.OS === 'ios') {
    // iOS native: use the actual home-indicator inset, with a floor.
    bottomPadding = insets.bottom > 0 ? insets.bottom : 8;
  } else {
    // Android: gesture bar + a small buffer.
    bottomPadding = Math.max(insets.bottom, 12);
  }

  // Total tab bar height — base 60 for icon + label + top padding, plus
  // the safe-area bottom padding.
  const tabBarHeight = 60 + bottomPadding;

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
            paddingTop: 8,
          },
          // Explicit label style — readable across iPhone preview, Safari
          // bottom bar, and Expo shell. Font 12px with generous line-height
          // so descenders aren't clipped.
          tabBarLabelStyle: {
            fontSize: 12,
            fontWeight: '500',
            lineHeight: 16,
            marginTop: 2,
            marginBottom: 0,
            paddingBottom: 2,
            includeFontPadding: false,
          },
          tabBarIconStyle: {
            marginTop: 0,
          },
          tabBarItemStyle: {
            paddingVertical: 2,
          },
          headerStyle: {
            backgroundColor: theme.background,
          },
          headerTintColor: theme.text,
          headerShadowVisible: false,
        }}
      >
        {/* 1. Mirror */}
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

        {/* 2. Life */}
        <Tabs.Screen
          name="life"
          options={{
            title: 'Life',
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 22 }}>❧</Text>
            ),
          }}
        />

        {/* 3. Reflect */}
        <Tabs.Screen
          name="reflect"
          options={{
            title: 'Reflect',
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 22 }}>◇</Text>
            ),
          }}
        />

        {/* Hidden: patterns */}
        <Tabs.Screen
          name="patterns"
          options={{
            href: null,
          }}
        />

        {/* 4. Lenses */}
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

      {/* =============================================================
          TEMPORARY BUILD MARKER — proves the new tab layout is deployed
          on the user's device. Remove after visual verification.
          ============================================================= */}
      <View
        pointerEvents="none"
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: tabBarHeight + 2,
          alignItems: 'center',
          zIndex: 9999,
        }}
      >
        <View
          style={{
            backgroundColor: 'rgba(255, 180, 0, 0.92)',
            paddingHorizontal: 10,
            paddingVertical: 3,
            borderRadius: 8,
          }}
        >
          <Text
            style={{
              fontSize: 10,
              fontWeight: '700',
              color: '#000',
              letterSpacing: 0.4,
            }}
          >
            {NAV_FIX_MARKER}
          </Text>
        </View>
      </View>
    </SessionRestoreWrapper>
  );
}
