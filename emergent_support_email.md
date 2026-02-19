# Email to Emergent Support

**To:** support@emergent.sh  
**Subject:** Deployed App Shows Old Content - Cache Not Updating After Multiple Deploys (Job: EMT-7d68fd)

---

Hi Emergent Support Team,

I'm experiencing a critical issue where my **deployed app shows old/incorrect content** while the **preview shows the correct content**. I've attempted to redeploy over 20 times but the deployed version never updates.

## App Details
- **App Name:** cache-buster-21
- **Job ID:** EMT-7d68fd
- **Deployed:** Visible in my Emergent Home → Deployed Apps

## The Problem

| Environment | What It Shows | Status |
|-------------|---------------|--------|
| Preview Web URL (`cache-buster-21.preview.emergentagent.com`) | Type 7w8, HIGH confidence | ✅ Correct |
| Preview in Expo Go (via Emergent chat QR code) | Type 7w8, HIGH confidence | ✅ Correct |
| **Deployed App** (via "Live" button / deployed QR code) | Type 7 balanced wings, LOW confidence | ❌ Wrong (OLD) |

The deployed version is showing **Enneagram results from an old build** that was fixed weeks ago. The preview correctly shows the updated results, but no matter how many times I redeploy, the live/deployed version continues showing stale content.

## What I've Tried
1. Clicked "Deploy" / "Deploy Now" over 20 times
2. Cleared Expo Go app cache on my phone
3. Force quit and reopened Expo Go
4. Rebuilt the web assets with new build IDs multiple times
5. Restarted all backend services
6. Added cache-busting headers to all responses
7. Cleared Metro bundler cache

None of these resolved the issue for the **deployed** version.

## Technical Details

**Confirmed working:**
- Database contains correct data (verified via direct MongoDB query)
- API endpoint `/api/enneagram/results/{user_id}` returns correct data: `inferred_core: 7, inferred_wing: 8, confidence_tier: "high"`
- Preview web URL displays correct results
- Preview Expo Go displays correct results
- Current build ID: `deploy_20260219_031458`

**The issue:**
The deployed Expo bundle appears to be served from a cached version in Emergent's infrastructure that predates my fixes. The bundle being served to users who scan the deployed QR code contains old JavaScript code that displays incorrect UI.

## Request

Could you please:
1. **Purge the deployment cache** for app `cache-buster-21`
2. **Force a fresh Expo bundle build** from the current preview code
3. **Investigate** why redeploying doesn't update the deployed bundle

This is blocking me from sharing the app with external testers, as they see incorrect information.

## Screenshots Available

I have screenshots showing:
- Preview displaying correct results (Type 7w8 HIGH)
- Deployed version displaying wrong results (Type 7 balanced LOW)
- The Emergent deployed apps screen showing the app

Happy to provide these if helpful.

## Workaround Needed

If the cache cannot be cleared immediately, is there an alternative way to share an always-on URL with testers? The preview URL works correctly but goes to sleep after inactivity.

Thank you for your help resolving this urgently.

Best regards,
[Your Name]

---

**Attachments to include:**
1. Screenshot of Preview showing Type 7w8 HIGH (correct)
2. Screenshot of Deployed version showing Type 7 balanced LOW (wrong)
3. Screenshot of Emergent Deployed Apps screen showing cache-buster-21
