import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { useTheme } from '../../contexts/ThemeContext';
import { useAppStore } from '../../store';
import LifeContextView from '../../components/LifeContextView';
import LifelineIntro from '../../components/lifeline/LifelineIntro';
import LifelineGuidedFlow from '../../components/lifeline/LifelineGuidedFlow';
import api from '../../services/api';

const TARGET_MOMENTS = 5;

export default function LifeScreen() {
  const { user } = useAppStore();
  const { theme, isDark } = useTheme();
  const router = useRouter();
  
  const [loading, setLoading] = useState(true);
  const [eventCount, setEventCount] = useState<number | null>(null);
  const [showIntro, setShowIntro] = useState(false);
  const [showGuidedFlow, setShowGuidedFlow] = useState(false);
  const [introCompleted, setIntroCompleted] = useState(false);

  useEffect(() => {
    if (user?.id) {
      checkLifelineStatus();
    }
  }, [user?.id]);

  const checkLifelineStatus = async () => {
    if (!user?.id) return;
    
    setLoading(true);
    try {
      const response = await api.get(`/lifeline/${user.id}`);
      const count = response.data?.event_count || 0;
      setEventCount(count);
      
      // Decision logic:
      // - 0 events + hasn't seen intro: show intro
      // - 0 events + intro completed: show guided flow
      // - 1-4 events: show guided flow (resume)
      // - 5+ events: show main lifeline view
      
      if (count === 0 && !introCompleted) {
        setShowIntro(true);
      } else if (count < TARGET_MOMENTS && introCompleted) {
        setShowGuidedFlow(true);
      } else if (count > 0 && count < TARGET_MOMENTS) {
        // User has some events but returned - show guided flow to continue
        setShowGuidedFlow(true);
      }
    } catch (err) {
      console.error('[Life] Failed to check lifeline status:', err);
      setEventCount(0);
      // If error, show intro for new users
      if (!introCompleted) {
        setShowIntro(true);
      }
    } finally {
      setLoading(false);
    }
  };

  // Called when user taps "Start My Lifeline" from intro
  const handleIntroComplete = () => {
    setShowIntro(false);
    setIntroCompleted(true);
    setShowGuidedFlow(true);
  };

  const handleImport = () => {
    setShowIntro(false);
    setIntroCompleted(true);
    // Router will handle navigation to import screen
  };

  // Called when guided flow reaches 5 moments
  const handleGuidedFlowComplete = () => {
    setShowGuidedFlow(false);
    // Navigate to Pattern Reveal / Pattern Lens
    router.push('/pattern-lens');
  };

  // Called when user exits guided flow early
  const handleGuidedFlowExit = () => {
    setShowGuidedFlow(false);
    // Refresh the event count
    checkLifelineStatus();
  };

  if (!user?.id) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.accent} />
        </View>
      </SafeAreaView>
    );
  }

  if (loading) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={theme.accent} />
          <Text style={[styles.loadingText, { color: theme.textSecondary }]}>
            Loading your lifeline...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  // Show intro flow for first-time users with 0 events
  if (showIntro) {
    return (
      <>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <LifelineIntro 
          onComplete={handleIntroComplete}
          onImport={handleImport}
        />
      </>
    );
  }

  // Show guided flow for users with < 5 events
  if (showGuidedFlow) {
    return (
      <>
        <StatusBar style={isDark ? 'light' : 'dark'} />
        <LifelineGuidedFlow
          initialCount={eventCount || 0}
          onComplete={handleGuidedFlowComplete}
          onExit={handleGuidedFlowExit}
        />
      </>
    );
  }

  // Show main lifeline view for users with 5+ events
  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]} edges={['top']}>
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <LifeContextView 
        userId={user.id} 
        onEventCountChange={(count) => setEventCount(count)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 15,
  },
});
