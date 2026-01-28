import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { format } from 'date-fns';
import { api } from '../../src/services/api';
import { useAuth } from '../../src/context/AuthContext';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/constants/theme';

interface DailyReflection {
  id: string;
  user_id: string;
  date_key: string;
  todays_insight: string;
  reflect_on: string;
  another_perspective: string;
  closing_line: string;
  created_at: string;
}

function getTodayDateKey(): string {
  // Get local date in YYYY-MM-DD format
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function Mirror() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const [reflection, setReflection] = useState<DailyReflection | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const fetchReflection = useCallback(async () => {
    try {
      const dateKey = getTodayDateKey();
      const response = await api.post('/reflection/today', { date_key: dateKey });
      setReflection(response.data);
    } catch (error) {
      console.error('Failed to fetch reflection:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchReflection();
  }, [fetchReflection]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchReflection();
  };

  const handleRegenerate = async () => {
    if (regenerating) return;
    
    setRegenerating(true);
    try {
      const dateKey = getTodayDateKey();
      const response = await api.post('/reflection/regenerate', { date_key: dateKey });
      setReflection(response.data);
    } catch (error) {
      console.error('Failed to regenerate reflection:', error);
      if (Platform.OS !== 'web') {
        Alert.alert('Error', 'Failed to regenerate reflection');
      }
    } finally {
      setRegenerating(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/welcome');
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={COLORS.accent} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Good {getTimeOfDay()}, {user?.name?.split(' ')[0]}</Text>
          <Text style={styles.date}>{format(new Date(), 'EEEE, MMMM d')}</Text>
        </View>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
          <Ionicons name="log-out-outline" size={24} color={COLORS.secondary} />
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={COLORS.accent}
          />
        }
      >
        {reflection && (
          <View style={styles.card}>
            {/* Regenerate button */}
            <View style={styles.cardHeader}>
              <TouchableOpacity 
                onPress={handleRegenerate} 
                style={styles.regenerateButton}
                disabled={regenerating}
              >
                {regenerating ? (
                  <ActivityIndicator size="small" color={COLORS.secondary} />
                ) : (
                  <Ionicons name="refresh-outline" size={20} color={COLORS.secondary} />
                )}
              </TouchableOpacity>
            </View>

            <View style={styles.section}>
              <Text style={styles.sectionLabel}>Today's Insight</Text>
              <Text style={styles.insight}>{reflection.todays_insight}</Text>
            </View>

            <View style={styles.divider} />

            <View style={styles.section}>
              <Text style={styles.sectionLabel}>Reflect On</Text>
              <Text style={styles.reflectionQuestion}>{reflection.reflect_on}</Text>
            </View>

            <View style={styles.divider} />

            <View style={styles.section}>
              <Text style={styles.sectionLabel}>Another Perspective</Text>
              <Text style={styles.perspective}>{reflection.another_perspective}</Text>
            </View>

            <View style={styles.closingSection}>
              <Text style={styles.closingLine}>{reflection.closing_line}</Text>
              <TouchableOpacity
                style={styles.journalButton}
                onPress={() => router.push({
                  pathname: '/(main)/new-entry',
                  params: { reflectOn: reflection.reflect_on }
                })}
              >
                <Ionicons name="create-outline" size={20} color={COLORS.accent} />
                <Text style={styles.journalButtonText}>Open Journal</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function getTimeOfDay(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'morning';
  if (hour < 17) return 'afternoon';
  return 'evening';
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '300',
    color: COLORS.primary,
  },
  date: {
    fontSize: 14,
    color: COLORS.secondary,
    marginTop: SPACING.xs,
  },
  logoutButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: SPACING.lg,
    paddingBottom: SPACING.xxl,
  },
  card: {
    backgroundColor: COLORS.white,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginBottom: SPACING.sm,
  },
  regenerateButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  section: {
    paddingVertical: SPACING.md,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.accent,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: SPACING.sm,
  },
  insight: {
    fontSize: 20,
    fontWeight: '300',
    color: COLORS.primary,
    lineHeight: 30,
  },
  reflectionQuestion: {
    fontSize: 18,
    color: COLORS.primary,
    lineHeight: 28,
    fontStyle: 'italic',
  },
  perspective: {
    fontSize: 16,
    color: COLORS.secondary,
    lineHeight: 26,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginVertical: SPACING.sm,
  },
  closingSection: {
    paddingTop: SPACING.lg,
    alignItems: 'center',
  },
  closingLine: {
    fontSize: 14,
    color: COLORS.secondary,
    textAlign: 'center',
    marginBottom: SPACING.md,
  },
  journalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.accent,
    gap: SPACING.sm,
  },
  journalButtonText: {
    color: COLORS.accent,
    fontSize: 14,
    fontWeight: '500',
  },
});
