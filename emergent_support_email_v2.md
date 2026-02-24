# Support Request: Expo Go Live Build Not Updating

## Issue Summary
The **Expo Go "Live" deployment** is serving a cached/stale JavaScript bundle that does not reflect the current codebase or database. This persists even after multiple re-deployments.

## Concrete Evidence

### What the DATABASE contains (verified via direct MongoDB query):
```
User: pete@pulsifi.me
Enneagram Type: 7w8
Confidence Tier: HIGH (0.4946)
Last Updated: 2026-02-16
```

### What the PREVIEW URL shows (CORRECT):
- URL: https://personality-quiz-15.preview.emergentagent.com
- Displays: **Type 7w8 High** ✅

### What the EXPO GO LIVE app shows (WRONG):
- Accessed via: QR code from Emergent dashboard → "Live" button
- Displays: **Type 7 — balanced wings (6 & 8) Low** ❌

The "balanced wings (6 & 8)" text **does not exist anywhere in the current codebase**. This proves the Live Expo Go bundle is serving **old code from weeks ago**.

## What We've Already Tried
1. ❌ Multiple re-deployments with new BUILD_IDs
2. ❌ Clearing Expo Go app cache on device
3. ❌ Deploying with a "new database" (as previously suggested)
4. ❌ Force refresh mechanisms in code
5. ❌ Cache-control headers on backend

**None of these worked because the issue is in Emergent's deployment infrastructure, not our code.**

## Technical Root Cause
The Expo Go deployment pipeline appears to be caching the JavaScript bundle at the CDN/infrastructure level. When users scan the "Live" QR code, they receive a stale bundle that was built weeks ago, regardless of new deployments.

## Requested Action
Please **purge/invalidate the Expo Go bundle cache** for this deployment:
- **Deployment ID**: expo-bundle-issue
- **URL**: expo-bundle-issue.preview.emergentagent.com

Or provide instructions on how we can force the Live Expo Go deployment to serve the latest bundle.

## Verification Steps After Fix
1. Scan "Live" QR code in Expo Go
2. Login as pete@pulsifi.me
3. Navigate to Lenses → Enneagram
4. Should show: **Type 7w8 High** (not "balanced wings Low")

Thank you for your assistance.
