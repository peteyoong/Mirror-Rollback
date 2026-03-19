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
      
      {/* 2. Life - Contextual translation of patterns */}
      <Tabs.Screen
        name="life"
        options={{
          title: 'Life',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 22, color }}>❧</Text>
          ),
        }}
      />
      
      {/* 3. Journal - User inputs and reflections */}
      <Tabs.Screen
        name="journal"
        options={{
          title: 'Journal',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 22, color }}>☰</Text>
          ),
        }}
      />
      
      {/* 4. Patterns - Pattern engine with Weekly/Timeline sub-views */}
      <Tabs.Screen
        name="patterns"
        options={{
          title: 'Patterns',
          tabBarIcon: ({ color }) => (
            <Text style={{ fontSize: 22, color }}>⬡</Text>
          ),
          // Note: unmountOnBlur removed - it causes issues on some platforms
          // Scroll reset is handled within the component via useFocusEffect
        }}
      />
      
      {/* 5. Lenses - Framework explanations */}
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
