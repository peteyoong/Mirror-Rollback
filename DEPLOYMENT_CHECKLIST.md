# Pre-Production Deployment Checklist

## Build Information
- **Date**: March 9, 2026
- **Branch**: main (dark mode migration complete)
- **Theme Mode**: System preference (DEV_THEME_OVERRIDE = null)

---

## 1. Native Build Validation (REQUIRES USER ACTION)

### Build Steps
```bash
# Create new native build via EAS
eas build --platform ios --profile preview

# Or for production
eas build --platform ios --profile production
```

### Required Native Tests
| Test | Screen | Expected Result |
|------|--------|-----------------|
| Onboarding birth time | Onboarding | DateTimePicker opens, user can select time |
| Journal input | Journal tab | Tap input, keyboard opens, can type, can save |
| Mirror chat | Home → Continue with Mirror | Send message, receive response, both visible |
| Enneagram lens | Lenses → Enneagram → View Summary | All 3 tabs render, all text readable |
| Human Design lens | Lenses → Human Design → View Summary | All 3 tabs render, all text readable |
| Astrology lens | Lenses → Astrology → View Summary | All 3 tabs render, all text readable |
| Numerology lens | Lenses → Numerology → View Summary | All 3 tabs render, all text readable |
| Dark mode auto | System Settings → Dark mode | App theme switches automatically |
| Light mode auto | System Settings → Light mode | App theme switches automatically |

### Known Issue (From Previous Fork)
- **Onboarding birth time input** may be unclickable on native builds
- If this occurs, investigate modal/overlay z-index in onboarding flow

---

## 2. Release Sanity Checks

### Backend Health ✅
- All API endpoints returning 200 OK
- No errors in backend.err.log (except LiteLLM info logs)
- LLM integration working (gpt-5.2)

### Frontend Health ✅
- Metro bundler running
- No runtime errors in expo.out.log
- Console warnings (non-blocking): deprecated `shadow*` props, `pointerEvents`

### Navigation ✅
- Tab bar working (Mirror, Life, Journal, Lenses)
- Lens detail modals open/close correctly
- Back navigation works

### Loading States ✅
- No stuck loading states observed
- Lens content loads within 8-15 seconds

### Blank Screens ✅
- No blank screens in any flow
- All text readable in dark mode

---

## 3. Theme Configuration

### Current State
```typescript
// /app/frontend/contexts/ThemeContext.tsx
const DEV_THEME_OVERRIDE: ThemeMode | null = null; // PRODUCTION MODE
```

### Theme Behavior
- **System preference**: App follows iOS/Android dark mode setting
- **Manual override**: Users can set via stored preference (future feature)
- **Fallback**: Light theme if system preference unavailable

### Tested Modes
- [x] Dark mode forced (DEV_THEME_OVERRIDE = 'dark')
- [ ] Light mode forced (needs visual verification)
- [ ] System switching (needs device testing)

---

## 4. Rollback Safety

### Files Changed in This Session

#### Theme Infrastructure (NEW)
- `/app/frontend/constants/theme.ts` - Light/dark theme tokens
- `/app/frontend/contexts/ThemeContext.tsx` - ThemeProvider + useTheme hook
- `/app/frontend/THEMING.md` - Documentation

#### Modified for Dark Mode
| File | Changes |
|------|---------|
| `app/_layout.tsx` | Wrapped in ThemeProvider |
| `app/(tabs)/_layout.tsx` | Themed tab bar |
| `app/(tabs)/index.tsx` | Themed home screen |
| `app/(tabs)/life.tsx` | Themed + useTheme hook |
| `app/(tabs)/journal.tsx` | Themed + fixed input clickability |
| `app/(tabs)/lenses.tsx` | Themed lens cards |
| `app/lenses/[lens].tsx` | Themed header + added Enneagram routing |
| `app/welcome.tsx` | Themed login screen |
| `components/EnneagramLensView.tsx` | Full theme migration |
| `components/HumanDesignLensView.tsx` | Full theme migration |
| `components/AstrologyLensView.tsx` | Full theme migration |
| `components/NumerologyLensView.tsx` | Full theme migration |
| `components/LifeContextView.tsx` | Themed containers |

### Rollback Procedure
If regressions occur after deployment:

1. **Quick fix**: Set `DEV_THEME_OVERRIDE = 'light'` to force light mode
2. **Full rollback**: Revert to previous commit before dark mode migration
3. **Partial rollback**: Remove theme imports and restore `Colors.X` usage

### Git Commands
```bash
# Tag current working state
git tag -a v1.0-dark-mode -m "Dark mode migration complete"

# View recent commits
git log --oneline -20

# Rollback to specific commit
git revert <commit-hash>
```

---

## 5. Post-Deployment Monitoring

### Watch For
- User reports of invisible text
- Theme not switching on system change
- Lens pages blank or partially rendered
- Journal input not responding
- Mirror chat not returning responses

### Debug Commands
```bash
# Check backend logs
tail -f /var/log/supervisor/backend.out.log

# Check expo logs  
tail -f /var/log/supervisor/expo.out.log

# Check for errors
grep -i error /var/log/supervisor/*.log
```

---

## Sign-Off

- [ ] Native build tested on iPhone
- [ ] Onboarding birth time input verified
- [ ] Journal input verified
- [ ] Mirror chat verified
- [ ] All 4 lenses verified in dark mode
- [ ] System theme switching verified
- [ ] No blocking issues found

**Approved for deployment**: _______________

**Date**: _______________
