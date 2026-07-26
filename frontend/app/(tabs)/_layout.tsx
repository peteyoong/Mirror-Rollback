import { Tabs } from 'expo-router';
import { Text, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../contexts/ThemeContext';
import { fontFamily } from '../../theme/tokens';
import SessionRestoreWrapper from '../../components/SessionRestoreWrapper';

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
    bottomPadding = Math.max(insets.bottom, 20);
  } else if (Platform.OS === 'ios') {
    bottomPadding = insets.bottom > 0 ? insets.bottom : 8;
  } else {
    bottomPadding = Math.max(insets.bottom, 12);
  }

  // Total tab bar height — base 72 for icon (24px) + label (20px) + top
  // padding (12px) + margin (8px). Plus the safe-area bottom padding.
  // Calibrated so labels never clip in the Expo web preview where the
  // testing agent measured only ~7px of label height at the previous
  // base of 60.
  const tabBarHeight = 72 + bottomPadding;

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
            paddingTop: 10,
          },
          // Explicit label style — readable across iPhone preview, Safari
          // bottom bar, and Expo shell.
          tabBarLabelStyle: {
            fontSize: 12,
            fontWeight: '500',
            lineHeight: 16,
            marginTop: 4,
            marginBottom: 2,
            includeFontPadding: false,
          },
          tabBarIconStyle: {
            marginTop: 0,
            marginBottom: 0,
            height: 24,
            width: 32,
          },
          tabBarItemStyle: {
            paddingVertical: 0,
          },
          headerStyle: {
            backgroundColor: theme.background,
          },
          headerTitleStyle: {
            fontFamily: fontFamily.display,
            fontSize: 20,
            fontWeight: '400',
            letterSpacing: 0.4,
            color: theme.text,
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
              <Text style={{ fontSize: 20, color, lineHeight: 24, textAlign: 'center' }}>☽</Text>
            ),
          }}
        />

        {/* 2. Life */}
        <Tabs.Screen
          name="life"
          options={{
            title: 'Life',
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 24, textAlign: 'center' }}>❧</Text>
            ),
          }}
        />

        {/* 3. Reflect */}
        <Tabs.Screen
          name="reflect"
          options={{
            title: 'Reflect',
            headerShown: false,
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 24, textAlign: 'center' }}>◇</Text>
            ),
          }}
        />

        {/* Hidden: patterns route */}
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
            headerShown: false,
            tabBarIcon: ({ color }) => (
              <Text style={{ fontSize: 20, color, lineHeight: 24, textAlign: 'center' }}>◉</Text>
            ),
          }}
        />
      </Tabs>
    </SessionRestoreWrapper>
  );
}
