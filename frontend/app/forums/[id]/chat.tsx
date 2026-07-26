/**
 * /forums/[id]/chat — Talk to the room
 * ====================================
 *
 * Build marker: forum-conversational-field-v1
 *
 * Quiet, full-screen surface that lets a member talk WITH the field
 * of a forum.  The actual chat logic lives in ForumMirrorChat — this
 * file is just a thin route wrapper.
 */
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '../../../contexts/ThemeContext';
import { useAppStore } from '../../../store';
import ForumMirrorChat from '../../../components/ForumMirrorChat';
import { BUILD_ID } from '../../../constants/buildMarker';

export default function ForumMirrorChatScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const forumId = String(params.id || '');
  const { user } = useAppStore();

  if (!user?.id) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.center}>
          <Text style={{ color: theme.textTertiary, fontStyle: 'italic' }}>
            Sign in to talk to the room.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!forumId) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <View style={styles.center}>
          <Text style={{ color: theme.textTertiary, fontStyle: 'italic' }}>
            No room id.
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.background }]}
      edges={['top']}
    >
      {/* Quiet header — no chrome, no dashboard pill. */}
      <View style={[styles.header, { borderBottomColor: theme.border }]}>
        <TouchableOpacity
          onPress={() => router.back()}
          hitSlop={10}
          accessibilityRole="button"
          accessibilityLabel="Back"
          style={styles.backBtn}
        >
          <Ionicons name="chevron-back" size={22} color={theme.text} />
        </TouchableOpacity>
        <View style={styles.titleWrap}>
          <Text style={[styles.kicker, { color: theme.textTertiary }]}>
            With the room
          </Text>
          <Text style={[styles.title, { color: theme.text }]}>
            Talk to the field
          </Text>
        </View>
        <View style={styles.backBtn} />
      </View>

      <View style={{ flex: 1 }}>
        <ForumMirrorChat userId={String(user.id)} forumId={forumId} />
      </View>

      <Text style={[styles.buildBadge, { color: theme.textTertiary }]}>
        {BUILD_ID}
      </Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  backBtn: { width: 38, height: 38, alignItems: 'center', justifyContent: 'center' },
  titleWrap: { flex: 1, alignItems: 'center' },
  kicker: {
    fontSize: 10.5,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    fontWeight: '500',
  },
  title: {
    fontSize: 16,
    fontWeight: '500',
    letterSpacing: -0.2,
    marginTop: 1,
  },
  buildBadge: {
    position: 'absolute',
    bottom: Platform.OS === 'ios' ? 4 : 2,
    right: 12,
    fontSize: 9,
    fontStyle: 'italic',
    opacity: 0.5,
  },
});
