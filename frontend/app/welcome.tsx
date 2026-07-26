import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  TextInput,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  useWindowDimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { useAppStore } from '../store';
import { loginUser } from '../services/api';
import { BUILD_ID } from '../constants/buildMarker';
import {
  colorDark,
  space,
  radius,
  textRole,
  fontFamily,
  fontSize,
  touchTarget,
} from '../theme/tokens';

/**
 * Welcome — The Mirror's single-page arrival moment.
 *
 * A quiet, centred composition: wordmark, headline, bridge line, and
 * exactly two actions — "I'm new here" (primary) and "Sign in" (ghost).
 */
export default function Welcome() {
  const router = useRouter();
  const { setUser, setChart } = useAppStore();
  const { height } = useWindowDimensions();

  const t = colorDark;

  const [showLogin, setShowLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const headline = {
    main: 'You almost did it again.',
    sub: 'You were about to decide—then stopped.\nYou noticed it—then moved past it.',
  };

  const handleBeginReflection = () => router.push('/onboarding');

  const handleLogin = async () => {
    if (!email.trim()) { setError('Please enter your email'); return; }
    setIsLoading(true);
    setError('');
    try {
      const result = await loginUser(email.trim());
      if (result.success && result.user) {
        await setUser(result.user);
        if (result.chart) await setChart(result.chart);
        router.replace('/(tabs)');
      } else {
        setError(result.detail || 'No account found with this email. Please create a new account.');
      }
    } catch (err: any) {
      const rawDetail = err.response?.data?.detail;
      const errorMsg = typeof rawDetail === 'string'
        ? rawDetail
        : (rawDetail?.message || err.message || 'Login failed. Please try again.');
      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  // Short-viewport threshold: below this, allow the KeyboardAvoidingView
  // to relax spacing so nothing collides.
  const isCompactHeight = height < 700;

  // ============================================================
  // LOGIN — same brand, tighter form
  // ============================================================
  if (showLogin) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: t.background }]}>
        <StatusBar style="light" />
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <ScrollView
            contentContainerStyle={styles.loginBody}
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
            bounces={false}
          >
            <View style={styles.loginBrand}>
              <Text style={styles.brandSeparator}>—</Text>
              <Text style={[styles.brandText, { color: t.onSurface }]}>The Mirror</Text>
              <Text style={styles.brandSeparator}>—</Text>
            </View>

            <View style={styles.loginContainer}>
              <Text style={[styles.loginTitle, { color: t.onSurface }]}>Welcome back</Text>
              <Text style={[styles.loginSubtitle, { color: t.onSurfaceSecondary }]}>
                Enter the email you used to save your reflection space.
              </Text>

              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: t.surfaceSecondary,
                    borderColor: t.border,
                    color: t.onSurface,
                  },
                ]}
                value={email}
                onChangeText={(text) => { setEmail(text); setError(''); }}
                placeholder="your@email.com"
                placeholderTextColor={t.onSurfaceTertiary}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                editable={!isLoading}
              />

              {error ? (
                <View style={[styles.errorContainer, { backgroundColor: t.error + '20' }]}>
                  <Text style={[styles.errorText, { color: t.error }]}>{error}</Text>
                </View>
              ) : null}

              <TouchableOpacity
                style={[
                  styles.primaryButton,
                  { backgroundColor: t.buttonPrimaryBg, borderColor: t.border },
                  isLoading && styles.buttonDisabled,
                ]}
                onPress={handleLogin}
                disabled={isLoading}
                activeOpacity={0.8}
              >
                {isLoading ? (
                  <ActivityIndicator size="small" color={t.buttonPrimaryText} />
                ) : (
                  <Text style={[styles.primaryButtonText, { color: t.buttonPrimaryText }]}>Enter</Text>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.textButton}
                onPress={() => { setShowLogin(false); setEmail(''); setError(''); }}
                disabled={isLoading}
                activeOpacity={0.8}
              >
                <Text style={[styles.textButtonText, { color: t.onSurfaceTertiary }]}>Back</Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // ============================================================
  // LANDING — single confident page (non-scrolling by default)
  // Uses justifyContent: 'space-between' so wordmark breathes at the
  // top-third and CTA anchors to the safe-area bottom above the
  // forums footer.  No ScrollView — the layout is designed to fit on
  // 360×640 and up; on shorter viewports paddings shrink instead.
  // ============================================================
  const verticalRoom = isCompactHeight ? space.md : space.xl;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: t.background }]}>
      <StatusBar style="light" />

      <ScrollView
        style={styles.container}
        contentContainerStyle={[styles.landingBody, { paddingVertical: verticalRoom }]}
        showsVerticalScrollIndicator={false}
        bounces={false}
      >
        {/* HERO — brand + headline + subtext + bridge */}
        <View style={styles.hero}>
          <View style={styles.brandContainer}>
            <Text style={styles.brandSeparator}>—</Text>
            <Text style={[styles.brandText, { color: t.onSurface }]}>The Mirror</Text>
            <Text style={styles.brandSeparator}>—</Text>
          </View>

          <Text style={[styles.headline, { color: t.onSurface, marginTop: isCompactHeight ? space.lg : space.xl }]}>
            {headline.main}
          </Text>

          <Text style={[styles.subtext, { color: t.onSurfaceSecondary, marginTop: space.lg }]}>
            {headline.sub}
          </Text>

          <Text style={[styles.bridgeLine, { color: t.onSurfaceTertiary, marginTop: isCompactHeight ? space.lg : space.xl }]}>
            {"This isn\u2019t about who you are.\nIt\u2019s about what\u2019s happening right now."}
          </Text>
        </View>

        {/* ACTIONS — exactly two, quiet and centred */}
        <View style={styles.ctaBlock}>
          <Text style={styles.ornament}>—  ◇  —</Text>

          <TouchableOpacity
            style={styles.primaryButton}
            onPress={handleBeginReflection}
            activeOpacity={0.7}
            testID="welcome-new-here-button"
            accessibilityRole="button"
          >
            <Text style={styles.primaryButtonText}>{"I\u2019m new here"}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.ghostButton}
            onPress={() => setShowLogin(true)}
            activeOpacity={0.6}
            testID="welcome-sign-in-link"
            accessibilityLabel="Sign in"
            accessibilityRole="button"
          >
            <Text style={styles.ghostButtonText}>Sign in</Text>
          </TouchableOpacity>
        </View>

        {/* FOOTER — build marker only */}
        <View style={styles.footerArea}>
          <Text style={styles.buildMarker}>build · {BUILD_ID}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    width: '100%',
  },
  keyboardView: {
    flex: 1,
    width: '100%',
  },

  // ── Landing single-page layout ──────────────────────────────
  landingBody: {
    flexGrow: 1,
    width: '100%',
    paddingHorizontal: space.xl,
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: space.xl,
  },
  hero: {
    width: '100%',
    alignItems: 'center',
    marginTop: space['2xl'],
  },
  brandContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.md,
  },
  brandText: {
    fontFamily: fontFamily.display,
    fontSize: fontSize['2xl'],
    fontWeight: '400',
    letterSpacing: 2.5,
    textAlign: 'center',
  },
  brandSeparator: {
    fontFamily: fontFamily.display,
    fontSize: fontSize['2xl'],
    fontWeight: '400',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  headline: {
    ...textRole.h1,
    textAlign: 'center',
    paddingHorizontal: space.sm,
  },
  subtext: {
    ...textRole.bodyLg,
    textAlign: 'center',
  },
  bridgeLine: {
    ...textRole.body,
    textAlign: 'center',
    fontStyle: 'italic',
  },

  // ── CTA block ──────────────────────────────────────────────
  ctaBlock: {
    width: '100%',
    maxWidth: 320,
    alignItems: 'center',
    gap: space.lg,
  },
  ornament: {
    fontFamily: fontFamily.display,
    fontSize: fontSize.base,
    color: 'rgba(198, 168, 124, 0.45)',
    letterSpacing: 6,
    marginBottom: space.xs,
  },
  primaryButton: {
    width: '100%',
    borderWidth: 1,
    borderColor: 'rgba(198, 168, 124, 0.35)',
    backgroundColor: 'rgba(198, 168, 124, 0.08)',
    paddingVertical: space.lg,
    paddingHorizontal: space['2xl'],
    borderRadius: radius.md,
    alignItems: 'center',
    minHeight: touchTarget.minSize + 8,
    justifyContent: 'center',
  },
  primaryButtonText: {
    ...textRole.buttonPrimary,
    color: '#E8DCC8',
    letterSpacing: 0.6,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  ghostButton: {
    width: '100%',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    borderRadius: radius.md,
    paddingVertical: space.md + 2,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: touchTarget.minSize,
  },
  ghostButtonText: {
    ...textRole.buttonSecondary,
    color: 'rgba(255, 255, 255, 0.65)',
    letterSpacing: 0.4,
  },

  // ── Footer ────────────────────────────────────────────────
  footerArea: {
    alignItems: 'center',
    paddingBottom: space.xs,
  },
  buildMarker: {
    fontFamily: fontFamily.text,
    fontSize: 11,
    fontVariant: ['tabular-nums'],
    color: 'rgba(255, 255, 255, 0.18)',
    letterSpacing: 0.3,
  },

  // ── Login form ────────────────────────────────────────────
  loginBody: {
    flexGrow: 1,
    width: '100%',
    paddingHorizontal: space.xl,
    paddingVertical: space['2xl'],
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginBrand: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.md,
    marginBottom: space['3xl'],
  },
  loginContainer: {
    width: '100%',
    maxWidth: 340,
    alignItems: 'center',
  },
  loginTitle: {
    ...textRole.h2,
    marginBottom: space.md,
  },
  loginSubtitle: {
    ...textRole.body,
    textAlign: 'center',
    marginBottom: space.xl,
  },
  input: {
    width: '100%',
    borderRadius: radius.md,
    padding: space.lg,
    fontFamily: fontFamily.text,
    fontSize: fontSize.lg,
    fontWeight: '400',
    borderWidth: 1,
    marginBottom: space.lg,
    minHeight: touchTarget.minSize + 8,
  },
  errorContainer: {
    width: '100%',
    borderRadius: radius.sm,
    padding: space.md,
    marginBottom: space.lg,
  },
  errorText: {
    ...textRole.body,
    textAlign: 'center',
  },
  textButton: {
    paddingVertical: space.md,
    alignItems: 'center',
    minHeight: touchTarget.minSize,
    justifyContent: 'center',
  },
  textButtonText: {
    ...textRole.body,
  },
});
