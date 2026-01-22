import { useEffect, useState } from 'react';
import { Slot } from 'expo-router';
import { View, ActivityIndicator } from 'react-native';
import { useAppStore } from '../store';
import { Colors } from '../constants/colors';

export default function RootLayout() {
  const { loadPersistedData } = useAppStore();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Load persisted data on app start
    loadPersistedData().then(() => {
      setIsReady(true);
    });
  }, []);

  if (!isReady) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.background }}>
        <ActivityIndicator size="large" color={Colors.textSecondary} />
      </View>
    );
  }

  return <Slot />;
}
