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

// Forums redirect target type
type ForumsRedirect = 'create' | 'join' | null;

/**
 * Welcome — The Mirror's single-page arrival moment.
 *
 * A confident, non-scrolling composition on standard mobile viewports.
 * The layout uses `justifyContent: 'space-between'` so the wordmark
 * block breathes at the top-third and the primary CTA is anchored to
 * the safe-area bottom, with forums / build marker footer beneath.
 *
 * Kept intentionally under one screen height on ≥ 360×640; on very
 * short viewports the KeyboardAvoidingView / SafeArea still absorbs
 * cleanly without visual collision.
 */
export default function Welcome() {
  const router = useRouter();
  const { setUser, setChart, user, hasCompletedOnboarding } = useAppStore();
  const { height } = useWindowDimensions();

  const isAuthenticated = !!user?.id;
  const hasExistingSession = isAuthenticated;

  const t = colorDark;

  const [showLogin, setShowLogin] = useState(false);
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [forumsRedirect, setForumsRedirect] = useState<ForumsRedirect>(null);

  const headline = {
    main: 'You almost did it again.',
    sub: 'You were about to decide—then stopped.\nYou noticed it—then moved past it.',
  };

  const handleBeginReflection = () => router.push('/onboarding');
  const handleShowMe = () => {
    if (isAuthenticated && hasCompletedOnboarding) router.replace('/(tabs)');
    else router.push('/onboarding');
  };
  const handleCreateForum = () => {
    if (hasExistingSession) router.push('/forums/create');
    else { setForumsRedirect('create'); setShowLogin(true); }
  };
  const handleJoinForum = () => {
    if (hasExistingSession) router.push('/forums/join');
    else { setForumsRedirect('join'); setShowLogin(true); }
  };

  const handleLogin = async () => {
    if (!email.trim()) { setError('Please enter your email'); return; }
    setIsLoading(true);
    setError('');
    try {
      const result = await loginUser(email.trim());
      if (result.success && result.user) {
        await setUser(result.user);
        if (result.chart) await setChart(result.chart);
        if (forumsRedirect === 'create') router.replace('/forums/create');
        else if (forumsRedirect === 'join') router.replace('/forums/join');
        else router.replace('/(tabs)');
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
          <View style={styles.loginBody}>
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
          </View>
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

      <View style={[styles.landingBody, { paddingVertical: verticalRoom }]}>
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

        {/* PRIMARY CTA + secondary auth row */}
        <View style={styles.ctaBlock}>
          <TouchableOpacity
            style={[
              styles.primaryButton,
              {
                backgroundColor: 'rgba(255, 255, 255, 0.08)',
                borderColor: 'rgba(255, 255, 255, 0.15)',
              },
            ]}
            onPress={handleShowMe}
            activeOpacity={0.7}
          >
            <Text style={[styles.primaryButtonText, { color: 'rgba(255, 255, 255, 0.9)' }]}>
              Show me
            </Text>
          </TouchableOpacity>

          <View style={styles.secondaryActionsRow}>
            <TouchableOpacity onPress={handleBeginReflection} activeOpacity={0.6} hitSlop={8}>
              <Text style={styles.secondaryActionText}>{"I\u2019m new here"}</Text>
            </TouchableOpacity>
            <Text style={styles.secondaryActionDivider}>·</Text>
            <TouchableOpacity
              onPress={() => setShowLogin(true)}
              activeOpacity={0.6}
              hitSlop={8}
              testID="welcome-sign-in-link"
              accessibilityLabel="Sign in"
              accessibilityRole="button"
            >
              <Text style={styles.secondaryActionText}>Sign in</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* FOOTER — forums quick-access + build marker */}
        <View style={styles.footerArea}>
          <View style={styles.forumsFooter}>
            <TouchableOpacity style={styles.forumLink} onPress={handleCreateForum} activeOpacity={0.5} hitSlop={4}>
              <Text style={styles.forumLinkText}>Create Forum</Text>
            </TouchableOpacity>
            <Text style={styles.forumDivider}>·</Text>
            <TouchableOpacity style={styles.forumLink} onPress={handleJoinForum} activeOpacity={0.5} hitSlop={4}>
              <Text style={styles.forumLinkText}>Join Forum</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.buildMarker}>build · {BUILD_ID}</Text>
        </View>
      </View>
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
    flex: 1,
    width: '100%',
    paddingHorizontal: space.xl,
    justifyContent: 'space-between',
    alignItems: 'center',
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
    gap: space.md,
  },
  primaryButton: {
    borderWidth: 1,
    paddingVertical: space.lg,
    paddingHorizontal: space['2xl'],
    borderRadius: radius.md,
    alignItems: 'center',
    width: '100%',
    minHeight: touchTarget.minSize,
    justifyContent: 'center',
  },
  primaryButtonText: {
    ...textRole.buttonPrimary,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  secondaryActionsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: space.sm,
    gap: space.md,
    minHeight: touchTarget.minSize,
  },
  secondaryActionText: {
    ...textRole.body,
    color: 'rgba(255, 255, 255, 0.55)',
  },
  secondaryActionDivider: {
    ...textRole.body,
    color: 'rgba(255, 255, 255, 0.3)',
  },

  // ── Footer ────────────────────────────────────────────────
  footerArea: {
    alignItems: 'center',
    gap: space.sm,
    paddingBottom: space.xs,
  },
  forumsFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    minHeight: touchTarget.minSize,
  },
  forumLink: {
    paddingVertical: space.xs,
    paddingHorizontal: space.sm,
  },
  forumLinkText: {
    ...textRole.body,
    color: 'rgba(255, 255, 255, 0.42)',
  },
  forumDivider: {
    ...textRole.body,
    color: 'rgba(255, 255, 255, 0.25)',
  },
  buildMarker: {
    fontFamily: fontFamily.text,
    fontSize: 11,
    fontVariant: ['tabular-nums'],
    color: 'rgba(255, 255, 255, 0.22)',
    letterSpacing: 0.3,
    marginTop: space.xs,
  },

  // ── Login form ────────────────────────────────────────────
  loginBody: {
    flex: 1,
    width: '100%',
    paddingHorizontal: space.xl,
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
