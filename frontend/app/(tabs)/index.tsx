import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import api from '../../services/api';

interface MirrorReflection {
  reflection: string;
  generated_at: string;
  is_first_visit: boolean;
}

export default function MirrorScreen() {
  const { user } = useAppStore();
  const [reflection, setReflection] = useState<MirrorReflection | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (user) {
      loadReflection();
    }
  }, [user]);

  const loadReflection = async (forceRefresh = false) => {
    if (!user) return;

    if (forceRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const response = await api.get(`/mirror/home/${user.id}`);
      setReflection(response.data);
    } catch (err: any) {
      console.error('Load reflection error:', err);
      // Use fallback
      setReflection({
        reflection: "Something in you brought you here today. That's worth noticing.",
        generated_at: new Date().toISOString(),
        is_first_visit: false,
      });
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
        <StatusBar style="dark" />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={Colors.textTertiary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.textTertiary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* Spacer for breathing room */}
        <View style={styles.topSpacer} />

        {/* Greeting - minimal */}
        <View style={styles.greetingContainer}>
          <Text style={styles.greeting}>
            {user.name || 'Welcome'}
          </Text>
        </View>

        {/* Loading State */}
        {isLoading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color={Colors.textTertiary} />
          </View>
        )}

        {/* The Reflection - the emotional keystone */}
        {reflection && !isLoading && (
          <View style={styles.reflectionContainer}>
            <Text style={styles.reflectionText}>
              {reflection.reflection}
            </Text>
          </View>
        )}

        {/* Gentle footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Pull down to receive a new reflection
          </Text>
        </View>

        <View style={styles.bottomSpacer} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 28,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  topSpacer: {
    height: 80,
  },
  greetingContainer: {
    marginBottom: 48,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '500',
    color: Colors.text,
    letterSpacing: -0.3,
  },
  loadingContainer: {
    paddingVertical: 60,
    alignItems: 'center',
  },
  reflectionContainer: {
    paddingVertical: 20,
  },
  reflectionText: {
    fontSize: 19,
    lineHeight: 32,
    color: Colors.text,
    fontWeight: '400',
    letterSpacing: 0.1,
  },
  footer: {
    marginTop: 'auto',
    paddingTop: 40,
    paddingBottom: 20,
  },
  footerText: {
    fontSize: 12,
    color: Colors.textTertiary,
    textAlign: 'center',
    opacity: 0.6,
  },
  bottomSpacer: {
    height: 40,
  },
});
