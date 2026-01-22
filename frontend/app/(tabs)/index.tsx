import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import ReflectionCard from '../../components/ReflectionCard';
import ChatBot from '../../components/ChatBot';
import { getDailyReflection } from '../../services/api';
import { format } from 'date-fns';

export default function MirrorScreen() {
  const { user, dailyReflection, setDailyReflection } = useAppStore();
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadReflection();
  }, []);

  const loadReflection = async (forceRefresh = false) => {
    if (!user) return;

    if (forceRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError('');

    try {
      const reflection = await getDailyReflection(user.id);
      setDailyReflection(reflection);
    } catch (err: any) {
      console.error('Load reflection error:', err);
      setError('Unable to load today\'s reflection. Pull to try again.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = () => {
    loadReflection(true);
  };

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.centered}>
          <Text style={styles.errorText}>No user found</Text>
        </View>
      </SafeAreaView>
    );
  }

  const today = format(new Date(), 'EEEE, MMMM d');

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.textSecondary}
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.greeting}>
            {user.name ? `Hello, ${user.name}` : 'Hello'}
          </Text>
          <Text style={styles.date}>{today}</Text>
        </View>

        {/* Loading State */}
        {isLoading && (
          <View style={styles.centered}>
            <ActivityIndicator size="large" color={Colors.textSecondary} />
            <Text style={styles.loadingText}>Preparing your reflection...</Text>
          </View>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity style={styles.retryButton} onPress={() => loadReflection()}>
              <Text style={styles.retryText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Reflection Card */}
        {dailyReflection && !isLoading && (
          <View style={styles.reflectionContainer}>
            <ReflectionCard
              insight={dailyReflection.insight}
              question={dailyReflection.question}
              perspective={dailyReflection.perspective}
            />
          </View>
        )}

        {/* Optional Journaling Prompt */}
        {dailyReflection && !isLoading && (
          <View style={styles.journalPrompt}>
            <Text style={styles.journalPromptText}>
              If this resonates, consider journaling your thoughts.
            </Text>
          </View>
        )}

        <View style={styles.spacer} />
      </ScrollView>

      {/* Persistent Chatbot */}
      <ChatBot userId={user.id} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 100,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 60,
  },
  header: {
    marginBottom: 32,
  },
  greeting: {
    fontSize: 28,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 4,
  },
  date: {
    fontSize: 14,
    color: Colors.textTertiary,
  },
  loadingText: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 16,
  },
  errorContainer: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 24,
    alignItems: 'center',
  },
  errorText: {
    fontSize: 14,
    color: Colors.error,
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: Colors.surfaceLight,
    borderRadius: 8,
    paddingHorizontal: 24,
    paddingVertical: 12,
  },
  retryText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
  },
  reflectionContainer: {
    marginBottom: 24,
  },
  journalPrompt: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 20,
    marginHorizontal: 16,
  },
  journalPromptText: {
    fontSize: 14,
    color: Colors.textTertiary,
    textAlign: 'center',
    fontStyle: 'italic',
  },
  spacer: {
    height: 60,
  },
});