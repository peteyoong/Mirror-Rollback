# PLACEMENTS TAB — FORWARD-BUILD DELIVERY REPORT

**Date:** 2026-06-13
**Workspace:** `hd-incarnation-fix` (workspace MONGO = `mongodb://localhost:27017` / `test_database`)
**Scope:** Forward-build the previously-shipped Placements tab in Astrology Lens. Additive only. No calculator / backend / migration / flag changes.
**User constraint correction acknowledged:** Per screenshot evidence, the Placements tab **was previously live** on the deployed app — so this is treated as **artifact-drift / sibling-workspace recovery**, not a "never existed" condition. The forensic of yesterday's audit stands as a *workspace-state* observation only.

---

## 1. What changed

| File | Action | Lines |
|---|---|---:|
| `frontend/components/astrology/AstrologyPlacementsTab.tsx` | **CREATED** | new — 339 lines |
| `frontend/components/AstrologyLensView.tsx` | **EDITED** (3 surgical edits) | +30 / −0 |
| `backend/web_dist/_expo/static/js/web/entry-*.js` | **REGENERATED** (was `entry-a840aeeb…js` → now `entry-7145ec4a…js`) | full rebuild |

No other files touched. Calculators, backend services, env vars, feature flags untouched.

### 1.1 `AstrologyLensView.tsx` — three surgical edits

1. **Import** the new tab (with build marker in comment):
   ```ts
   import AstrologyPlacementsTab from './astrology/AstrologyPlacementsTab'; // MARKER: placements-tab-v1
   ```
2. **Extend the `activeTab` union** from 4 values to 5:
   ```ts
   const [activeTab, setActiveTab] = useState<
     'at_a_glance' | 'placements' | 'today' | 'deep_dive' | 'timeline'
   >('at_a_glance');
   ```
3. **Insert tab button** between *At a Glance* and *Today* (matches screenshot order) + **add render branch** that switches to deep-dive on per-card "Open deep dive" tap by reusing the existing `expandedCards` state and `setActiveTab('deep_dive')`. No new state, no new endpoint.

### 1.2 `AstrologyPlacementsTab.tsx` — feature spec implemented

| Section header (from screenshot) | Placements rendered |
|---|---|
| `CORE IDENTITY` | Sun · Moon · Rising (Ascendant) |
| `PERSONAL PLANETS` | Mercury · Venus · Mars |
| `SOCIAL PLANETS` | Jupiter · Saturn |
| `OUTER PLANETS` | Uranus · Neptune · Pluto |
| `NODES & POINTS` | North Node · South Node · Chiron |
| `ANGLES` | MC · IC · DC (Ascendant lives in Core Identity per screenshot) |
| `HOUSE CUSPS` | All 12 cusps from `fullChartData.natal.houses.cusps`, when present |

Each placement card renders:
* Glyph icon (`☉ ☽ ↑ ☿ ♀ ♂ ♃ ♄ ♅ ♆ ♇ ☊ ☋ ⚷ MC IC DC`)
* Name (with "Rising (Ascendant)" display-name for `asc`, matching screenshot)
* Meta line: **`Sign · House N · DD.DD°`** (House omitted for angles; `℞ Retrograde` appended when `retrograde === true`)
* **Italic trait pair** keyed off sign — Variant A canonical, 13 signs **including Ophiuchus** (`Healing · truth-seeking`). Two-word descriptors match screenshot tone (e.g., Pisces → `Imaginative · empathic`, Aries → `Initiating · direct`, Sagittarius → `Expansive · truth-seeking`).
* **"Open deep dive"** link → routes the user to the existing **Deep Dive** tab with the corresponding card pre-expanded (uses the existing `expandedCards: Set<string>` state, no new state machinery).

### 1.3 Data plane — read-only, no new endpoints

* **Primary source:** `fullChartData.natal.planets`, `.nodes`, `.angles`, `.houses.cusps` — already fetched by `AstrologyLensView.loadFullChartData()` via existing `GET /api/astrology/chart/{userId}`.
* **Fallback:** when `fullChartData` is null, falls back to the 3-placement summary from the existing `CorePlacements` prop. Cards still render (sign-only); a small footnote explains "Showing a partial summary."
* **No backend changes.** No new collections. No write paths. No migrations. No calculator deltas.

---

## 2. Build & deploy verification

### 2.1 Build
```bash
cd /app/frontend && yarn build:deploy   # → npx expo export --platform web && wipe + cp into backend/web_dist
```
Output: `Exported: dist  Done in 8.14s.`
**Exit code 0.** No type errors, no Metro bundling errors.

### 2.2 New bundle artifact
| Field | Value |
|---|---|
| Path | `/app/backend/web_dist/_expo/static/js/web/entry-7145ec4af389f79a1da9f6afa8b44f7c.js` |
| Size | **3,960,066 bytes** (was 3,936,149 — delta **+23,917 bytes ≈ +23 KB**, well within the predicted 10–25 KB envelope) |
| MD5 | `27e055f1ea1abc0e3330ae35593f18a0` |
| mtime | 2026-06-13 14:30 UTC |
| Old bundle wiped? | ✅ `rm -rf ../backend/web_dist/*` ran before `cp` — only the new bundle remains |

### 2.3 Forensic marker verification (bundle grep)

| Marker | Hits in new bundle | Why it matters |
|---|---:|---|
| **`placements-tab-v1`** | **1** | Build marker for future regression audits |
| **`AstrologyPlacementsTab`** | **1** | Component-name marker for future grep |
| `"Placements"` (tab label) | 1 | Tab visible |
| `"Your complete natal map"` (subtitle) | 1 | Screenshot copy match |
| `"CORE IDENTITY"` | 1 | Section header match |
| `"PERSONAL PLANETS"` | 1 | Section header match |
| `"Rising (Ascendant)"` | 1 | Asc display-name match |
| `Ophiuchus` | 9 | Variant A canonical sign retained |
| Tab labels in bundle | `At a Glance`, `Placements`, `Today`, `Deep Dive`, `Timeline` | Correct 5-tab order |

> **Note on the markers:** the comment-only `// MARKER: placements-tab-v1` did **not** survive Metro's minification (comments are stripped). The fix used was to embed both markers as **live const references** (`const BUILD_MARKER = 'placements-tab-v1'`) and reference them on the rendered ScrollView's `testID` / `accessibilityLabel`. They now survive minification permanently — future forensic bundle-greps will land on them.

### 2.4 Backend health endpoint
```json
GET /api/health → debug & build
{
  "build": {
    "deployed_bundle": {
      "timestamp": "2026-06-13 14:30:14 UTC",
      "hash": "5ae9551bb335",
      "name": "entry-7145ec4af389f79a1da9f6afa8b44f7c.js",
      "size_kb": 3867.3
    },
    "validation": {
      "is_current": true,
      "errors": [],
      "stale_files_count": 0
    }
  }
}
```
**`validation.is_current = true`** — the deployment guard no longer flags `STALE DEPLOYMENT`. Static `backend/web_dist` is in sync with source.

### 2.5 Smoke check (preview pod)

* `GET http://localhost:3000/` → 200 (Expo dev server)
* `GET http://localhost:8001/` → 200, serves new bundle filename
* Astrology lens route loads with header "True Sidereal Astrology" and the proper loading shell. (The screenshotting browser is unauthenticated so the chart fetch sits in its loading state; tab order and Placements visibility require an authenticated session to verify visually. Bundle-level confirmation is given by §2.3.)

---

## 3. Preserved invariants (audit checklist)

| Constraint | Status |
|---|:---:|
| Calculators (sidereal_config, canonical_astronomy, IAU constellations) unchanged | ✅ no edits |
| Astrology math / SVP / Variant A engine unchanged | ✅ confirmed `/api/diagnostics/astro-system` still reports `midpoint13_variant_a_v1`, SVP 31.2836, runtime_guard active |
| Human Design generation unchanged | ✅ no edits |
| Birth-data / timeline / forum logic unchanged | ✅ no edits |
| `INTENT_ROUTER_V2_CUTOVER` | still `false` ✅ |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT` | still `10` ✅ |
| `RELATIONSHIP_ORCHESTRATION_PROMPT` | still `false` ✅ |
| `CROSS_LENS_PROMPT_SURFACE` | still `false` ✅ |
| Backend code | no changes ✅ |
| New collections / migrations | none ✅ |
| Existing tabs (At a Glance, Today, Deep Dive, Timeline) | preserved — unchanged behavior ✅ |
| `EXPO_PACKAGER_PROXY_URL` / `EXPO_PACKAGER_HOSTNAME` / `MONGO_URL` | untouched ✅ |

---

## 4. Known follow-ups (not part of this delivery)

1. **Publish the rebuilt bundle to the live deployed environment.** The Atlas-backed deployed app at `https://mirror-lens-fixes-r-1779710763.emergent.host` is still serving `entry-a840aeeb…js` (the old bundle, last-modified 2026-05-31). To make Placements visible in production, you must hit **Publish** in the Emergent dashboard to roll the new `backend/web_dist` content forward. This delivery prepared the artifact; only you can authorize the publish.
2. **Authenticated UI screenshot.** Visual confirmation of card layout vs. your reference screenshot is best done as a follow-up against an authenticated session (e.g., Pete = `pete@pulsifi.me`). Happy to run that next if you want.
3. **Trait-pair tuning.** The `SIGN_TRAITS` table includes a working two-word pair per sign (matching your screenshot for Pisces/Aries/Sagittarius). The other 10 signs use defensible defaults — feel free to override if you want copy parity with the prior deployment's exact phrasing.
4. **House cusp tap-through.** The "HOUSE CUSPS" card currently renders read-only rows. If you want per-house deep-dive routing, that's a small follow-up.

---

## 5. Reproducibility (for future forensic audits)

```bash
# 1. Bundle marker check
NEW=$(find /app/backend/web_dist/_expo/static/js/web -name 'entry-*.js')
for m in "placements-tab-v1" "AstrologyPlacementsTab" \
         "Your complete natal map" "CORE IDENTITY" \
         "PERSONAL PLANETS" "Rising (Ascendant)"; do
  printf '%-30s %d\n' "$m" "$(grep -oc "$m" "$NEW")"
done

# 2. Backend self-report of current bundle
curl -s http://localhost:8001/api/health \
  | jq '{name:.build.deployed_bundle.name,
         current:.build.validation.is_current}'

# 3. Source file presence (counter to yesterday's forensic)
ls /app/frontend/components/astrology/AstrologyPlacementsTab.tsx
grep -c "placements-tab-v1" /app/frontend/components/astrology/AstrologyPlacementsTab.tsx   # → ≥1
```

---

## 6. One-paragraph bottom line

The Placements tab has been **forward-built and embedded into the workspace bundle** as `entry-7145ec4af389f79a1da9f6afa8b44f7c.js` (MD5 `27e055f1ea1abc0e3330ae35593f18a0`, +23 KB). The 5-tab order in the bundle now reads **At a Glance · Placements · Today · Deep Dive · Timeline**, matching your screenshot. All forensic markers (`placements-tab-v1`, `AstrologyPlacementsTab`, `CORE IDENTITY`, `Rising (Ascendant)`, `Your complete natal map`) are runtime-embedded so they will survive future minified-bundle audits. Calculators, backend, math, flags, and DB topology are all untouched. The deployed `emergent.host` app is still on the **old** bundle until you hit **Publish** in the Emergent dashboard — the new artifact is staged and ready in `/app/backend/web_dist/` and the preview/workspace backend already serves it.

**Next step on your side:** click *Publish* on Emergent to roll the new bundle to the live deployed URL — or tell me whether to run an authenticated screenshot verification first.
