import { Tabs } from 'expo-router';
import { Text } from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import SessionRestoreWrapper from '../../components/SessionRestoreWrapper';

export default function TabLayout() {
  const { theme } = useTheme();
  
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
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
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
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 22, color }}>☽</Text>
          ),
        }}
      />
      
      {/* 2. Life - Lifeline & long-term patterns */}
      <Tabs.Screen
        name="life"
        options={{
          title: 'Life',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 22, color }}>❧</Text>
          ),
        }}
      />
      
      {/* 3. Reflect - Journal & Mirror tabs (renamed from Journal) */}
      <Tabs.Screen
        name="reflect"
        options={{
          title: 'Reflect',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 22, color }}>◇</Text>
          ),
        }}
      />
      
      {/* Patterns tab REMOVED - Patterns V1 now lives on Home as "Today's Pattern" */}
      {/* Hide patterns route from tab bar but keep file for potential dev use */}
      <Tabs.Screen
        name="patterns"
        options={{
          href: null, // This removes it from tab bar
        }}
      />
      
      {/* 4. Lenses - Framework explanations */}
      <Tabs.Screen
        name="lenses"
        options={{
          title: 'Lenses',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 22, color }}>◉</Text>
          ),
        }}
      />
      
    </Tabs>
    </SessionRestoreWrapper>
  );
}
