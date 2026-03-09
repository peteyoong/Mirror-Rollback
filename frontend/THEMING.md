# Dark Mode / Theming Guide

## Overview

This app uses a centralized theme system with React Context. All UI components must use dynamic theme colors - **never hardcode colors or use CSS-like patterns**.

## Architecture

```
/app/frontend/
├── constants/
│   └── theme.ts           # Light/dark theme token definitions
├── contexts/
│   └── ThemeContext.tsx   # ThemeProvider + useTheme hook
└── components/
    └── *.tsx              # Components consume theme via useTheme()
```

## Theme Tokens

Located in `/app/frontend/constants/theme.ts`:

```typescript
// Available color tokens
theme.background      // Main background (#0D0D0D dark, #FAF9F6 light)
theme.surface         // Card backgrounds
theme.surfaceLight    // Elevated surfaces
theme.text            // Primary text
theme.textSecondary   // Body text
theme.textTertiary    // Muted/label text
theme.accent          // Brand accent color
theme.border          // Border colors
theme.error           // Error states
```

## Usage Pattern

### ✅ CORRECT - Dynamic Theme Colors

```tsx
import { useTheme } from '../contexts/ThemeContext';

function MyComponent() {
  const { theme, isDark } = useTheme();
  
  return (
    <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <Text style={[styles.title, { color: theme.text }]}>Title</Text>
      <Text style={[styles.body, { color: theme.textSecondary }]}>Body text</Text>
      <Text style={[styles.label, { color: theme.textTertiary }]}>LABEL</Text>
    </View>
  );
}
```

### ❌ WRONG - Static Colors / "inherit"

```tsx
// NEVER DO THIS - "inherit" doesn't work in React Native
const styles = StyleSheet.create({
  title: {
    color: "inherit",        // ❌ BROKEN - renders as black/invisible
  },
  card: {
    backgroundColor: "#fff", // ❌ BROKEN - ignores dark mode
  },
});

// NEVER import Colors and use directly without theme override
import { Colors } from '../constants/colors';
<Text style={{ color: Colors.text }}>...</Text>  // ❌ Static, won't adapt
```

## Key Rules

### 1. Every Text Component Needs Inline Theme Color

```tsx
// ✅ Correct
<Text style={[styles.label, { color: theme.textTertiary }]}>Label</Text>

// ❌ Wrong - missing theme color override
<Text style={styles.label}>Label</Text>
```

### 2. Every Card/Container Needs Theme Background

```tsx
// ✅ Correct
<View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>

// ❌ Wrong - static background
<View style={styles.card}>
```

### 3. Icons Use Theme Colors

```tsx
// ✅ Correct
<Ionicons name="star" size={20} color={theme.textSecondary} />

// ❌ Wrong - hardcoded color
<Ionicons name="star" size={20} color="#666" />
```

### 4. StatusBar Adapts to Theme

```tsx
import { StatusBar } from 'expo-status-bar';
const { isDark } = useTheme();

<StatusBar style={isDark ? 'light' : 'dark'} />
```

## Stylesheet Pattern

Keep structure in StyleSheet, apply colors inline:

```tsx
const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    // NO color values here
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    // NO color values here
  },
});

// Apply colors in JSX
<View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
  <Text style={[styles.title, { color: theme.text }]}>...</Text>
</View>
```

## Developer Override (Testing)

In `/app/frontend/contexts/ThemeContext.tsx`:

```typescript
// Force a specific theme for testing (set to null for system preference)
const DEV_THEME_OVERRIDE: 'light' | 'dark' | null = 'dark';
```

## Component Checklist

When creating/modifying components, verify:

- [ ] `useTheme()` is imported and called
- [ ] All `<Text>` have `{ color: theme.X }` inline style
- [ ] All card/container `<View>` have `{ backgroundColor: theme.X }` 
- [ ] All borders use `{ borderColor: theme.border }`
- [ ] All icons use `color={theme.X}`
- [ ] No hardcoded hex colors in JSX
- [ ] No `color: "inherit"` in StyleSheet

## Files Using Theme System

### Fully Migrated
- `app/(tabs)/index.tsx` - Home/Mirror
- `app/(tabs)/life.tsx` - Life tab
- `app/(tabs)/journal.tsx` - Journal tab
- `app/(tabs)/lenses.tsx` - Lenses list
- `app/(tabs)/_layout.tsx` - Tab bar
- `app/lenses/[lens].tsx` - Lens detail modal
- `app/welcome.tsx` - Login screen
- `components/EnneagramLensView.tsx`
- `components/HumanDesignLensView.tsx`
- `components/AstrologyLensView.tsx`
- `components/NumerologyLensView.tsx`
- `components/LifeContextView.tsx`
- `components/MirrorChat.tsx`

## Common Mistakes to Avoid

1. **Forgetting nested components** - Parent may be themed but child Text still needs color
2. **Using `Colors.X` directly** - Always use `theme.X` from hook instead
3. **Adding colors to StyleSheet** - Keep them inline with theme values
4. **Missing accordion/section content** - Expanded content needs theme too
5. **Modal backgrounds** - Must explicitly set `backgroundColor: theme.surface`

---

*Last updated: March 2026*
*Theme system introduced during dark mode migration*
