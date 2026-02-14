import React from 'react';
import { View, Text } from 'react-native';

export default function MirrorV2() {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a2e' }}>
      <Text style={{ color: 'red', fontSize: 24, fontWeight: 'bold' }}>MIRROR V2 SAFE SCREEN</Text>
      <Text style={{ color: 'white', fontSize: 14, marginTop: 10 }}>No hooks, no store, no effects</Text>
    </View>
  );
}
