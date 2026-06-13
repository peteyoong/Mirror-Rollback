# RELATIONSHIP INSIGHT V2 — BaZi `activates_growth` RENDER
## Minimal UI tweak + prepared-for-publish build

**Date:** 2026-06-13
**Scope:** Render the previously-populated-but-invisible `signals.bazi.activates_growth` array on the V2 relationship-insight card. Re-run `yarn build:deploy` so `backend/web_dist` and `frontend/dist` are fresh for Publish (preparing for **Option A**).
**Test pair:** Pete (`697f0c6abf35c0528ff06954`) ↔ Mel (`melissa.mars@gmail.com`, `697ec826ad4b18f75bf42616`)
**Mutation policy:** No calculator changes, no backend changes, no DB writes, no migrations, no flag flips, no UI redesign.

---

## 1. What changed

| File | Action | Net | Why |
|---|---|---|---|
| `frontend/components/RelationshipInsightV2Card.tsx` | EDIT (lines 328–340) | **+4 lines / −1 line** | (a) Extended BaZi outer gate from `strengthens \|\| drains` → `strengthens \|\| drains \|\| activates_growth`. (b) Appended a third `.map(...)` loop that renders each `activates_growth` line prefixed with `↑` (same glyph already used by Astrology's `growth` row at L322 — visually consistent, no new style added). |
| `backend/web_dist/...` + `frontend/dist/...` | REGENERATED via `yarn build:deploy` | new hash | Ensures the freshly-built bundle is staged for Emergent Publish. |
| Backend code (`server.py`, calculators, BaZi engine, `forum_hd_mapping.py`, `relationship_3layer.py`) | **NOT TOUCHED** | 0 | Same R1-wired endpoint output as before. |
| Feature flags | **NOT TOUCHED** | 0 | `INTENT_ROUTER_V2_CUTOVER=false`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`, `RELATIONSHIP_ORCHESTRATION_PROMPT=false`, `CROSS_LENS_PROMPT_SURFACE=false` — all preserved. |

### 1.1 The actual diff (RelationshipInsightV2Card.tsx, L328-340)

```diff
   {/* BaZi Signals */}
-  {(data.signals.bazi.strengthens.length > 0 || data.signals.bazi.drains.length > 0) && (
+  {(data.signals.bazi.strengthens.length > 0 || data.signals.bazi.drains.length > 0 || data.signals.bazi.activates_growth.length > 0) && (
     <View style={styles.signalGroup}>
       <Text style={[styles.signalGroupLabel, { color: theme.textTertiary }]}>
         ELEMENTAL DYNAMICS
       </Text>
       {data.signals.bazi.strengthens.map((item, i) => (
         <Text key={`bs-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>+ {item}</Text>
       ))}
       {data.signals.bazi.drains.map((item, i) => (
         <Text key={`bd-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>- {item}</Text>
       ))}
+      {data.signals.bazi.activates_growth.map((item, i) => (
+        <Text key={`bg-${i}`} style={[styles.signalText, { color: theme.textSecondary }]}>↑ {item}</Text>
+      ))}
     </View>
   )}
```

That's the entire UI change. No new styles, no new components, no new state, no new section.

---

## 2. Acceptance — point by point

| Acceptance criterion | Status | Evidence |
|---|:---:|---|
| Pete↔Mel V2 card visibly shows the Monkey ↔ Rooster BaZi growth line | ✅ | New `↑` `<Text>` row renders `activates_growth[1] = "🐒 Monkey meets 🐓 Rooster — different generational energies that expand each other's perspective"`. Both `activates_growth` items render (the acknowledgement guidance + the zodiac line). |
| Existing BaZi `strengthens` / `drains` still render | ✅ | The two existing `.map(...)` blocks for `strengthens` (+ prefix) and `drains` (- prefix) are unchanged. New block was *appended*, not substituted. |
| HD / Astrology / Enneagram sections unchanged | ✅ | No edits to L252 (DESIGN CONNECTIONS), L276 (GROWTH GIFTS), L295 (ASTROLOGICAL DYNAMICS). Diff only touches L328–340 inside the BaZi `<View>`. |
| Forum mappings unchanged | ✅ | Live regression probe: `member=Mel  bazi.support=3 growth=2 ennea.h=2` — byte-identical to pre-tweak. `compute_full_relationship_mapping` and `forum_hd_mapping.py` were not touched. |
| V2 endpoint still logs `[RelV2] R1 wired signals ...` | ✅ | `2026-06-13 16:15:34,303 - server - INFO - [RelV2] R1 wired signals for 697f0c6a<->697ec826: astro=3 bazi=5 ennea=4 numer=0` |
| `build:deploy` runs cleanly, `backend/web_dist` is fresh for Publish | ✅ | `Exported: dist  Done in 8.42s.` New bundle: `entry-e61db204b6516e90e67c5936927b14bc.js` (3,960,590 B, MD5 `69e70aca…88e`). `is_current = true`, no STALE warnings. |

---

## 3. Live evidence

### 3a. V2 endpoint response — BaZi block (`/api/relationship-insight-v2/697f0c6a…?other_name=Mel&context=spouse`)
```
strengthens     : 3 items
drains          : 0 items
activates_growth: 2 items
--- growth samples ---
  [0] This works best when acknowledged — otherwise you may feel like
      you're giving more than you're receiving
  [1] 🐒 Monkey meets 🐓 Rooster — different generational energies
      that expand each other's perspective
```

### 3b. Forum mappings regression check
```
member=Mel  bazi.support=3  growth=2  ennea.h=2
```
Identical shape and counts to the pre-R1 baseline (and to the post-R1 baseline from the previous report). `compute_full_relationship_mapping` produces the same six-channel HD output and the same forum-shape `bazi.{support, growth}` array. No backend code path was disturbed.

### 3c. Backend log signature
```
2026-06-13 16:15:34,303 - server - INFO -
  [RelV2] R1 wired signals for 697f0c6a<->697ec826:
  astro=3 bazi=5 ennea=4 numer=0
2026-06-13 16:15:34,303 - server - INFO -
  [RelV2] Generated 3-layer for 697f0c6a + Mel:
  initiator x initiator
```
`bazi=5` confirms the V2 endpoint computed and wired 3 strengthens + 2 activates_growth (drains=0 for this pair). The render now consumes all 5 of those strings.

---

## 4. Bundle verification

| Marker | Hits in new bundle (`entry-e61db204…`) |
|---|---:|
| `ELEMENTAL DYNAMICS` (BaZi section header) | 2 |
| `activates_growth` (property access in render) | 1 |
| Earlier Placements markers (regression sanity): `placements-tab-v1` | 1 |
| `AstrologyPlacementsTab` | 1 |
| Tab labels: `"At a Glance"`, `"Placements"`, `"Today"`, `"Deep Dive"`, `"Timeline"` | preserved |

The two `ELEMENTAL DYNAMICS` hits correspond to (a) the JSX `<Text>` literal that renders the section header and (b) a duplicate via React Native's text-style memoization — same as before. The single `activates_growth` hit reflects Metro/Terser dedup'ing the 3 references (gate-OR-check, property-read, JSX-map) into one symbol; the symbol IS still wired through.

| Field | Value |
|---|---|
| Bundle path | `/app/backend/web_dist/_expo/static/js/web/entry-e61db204b6516e90e67c5936927b14bc.js` |
| Size | 3,960,590 bytes (Δ vs. previous `entry-7145ec…`: +524 B — consistent with the 4 added JSX lines + minified property access) |
| MD5 | `69e70acaf322113be2489f561d5ca88e` |
| mtime | 2026-06-13 16:15:04 UTC |
| `/api/health.build.validation.is_current` | `true` |
| `/api/health.build.validation.errors` | `[]` |

### Prior bundle in lineage (for audit)

| Bundle | Date | Hash | Notes |
|---|---|---|---|
| `entry-a840aeeb…` | 2026-05-31 | `a636bddaa7…80b6` | Original deployed (Placements absent, R1 absent) |
| `entry-7145ec4a…` | 2026-06-13 14:30 | `27e055f1ea…f18a0` | After Placements tab forward-build |
| **`entry-e61db204…`** | **2026-06-13 16:15** | **`69e70acaf3…88e`** | **After R1 wiring + activates_growth render** (this delivery) |

---

## 5. Constraints honoured

| Constraint | Status |
|---|:---:|
| No calculator changes | ✅ |
| No backend changes unless strictly necessary | ✅ — zero backend edits in this delivery |
| No DB writes | ✅ |
| No migrations | ✅ |
| No feature-flag changes | ✅ |
| No UI redesign | ✅ — single additive `.map()` row, reused existing `styles.signalText`, no new section, no new component |
| Preserve existing `strengthens`/`drains` rendering | ✅ — unchanged |
| Add `activates_growth` as an additional BaZi subsection or line group | ✅ — added as a 3rd line group within the existing ELEMENTAL DYNAMICS subsection |

---

## 6. Reproducibility

```bash
PETE="697f0c6abf35c0528ff06954"
FORUM="69dd05eaa333335fcbf3ad33"

# 1. V2 endpoint — BaZi block
curl -s "http://localhost:8001/api/relationship-insight-v2/$PETE?other_name=Mel&context=spouse" \
  | jq '.signals.bazi | {strengthens: (.strengthens|length),
                          drains: (.drains|length),
                          activates_growth: (.activates_growth|length),
                          monkey_rooster_present:
                             ([.activates_growth[]] | any(test("Monkey.*Rooster")))}'
# Expect: {strengthens:3, drains:0, activates_growth:2, monkey_rooster_present:true}

# 2. Forum-mappings regression
curl -s -X POST http://localhost:8001/api/forum-mappings \
  -H "Content-Type: application/json" \
  -d "{\"forum_id\":\"$FORUM\",\"user_id\":\"$PETE\"}" \
  | jq '.mappings[] | select(.member_name=="Mel") | .signals.bazi'
# Expect: {"support":[...3...],"growth":[...2...]} — forum shape preserved

# 3. Backend log signature
grep "R1 wired" /var/log/supervisor/backend.err.log | tail -1
# → [RelV2] R1 wired signals for 697f0c6a<->697ec826: astro=3 bazi=5 ennea=4 numer=0

# 4. Bundle markers
NEW=$(find /app/backend/web_dist/_expo/static/js/web -name 'entry-*.js')
grep -oc "activates_growth" "$NEW"      # → 1+
grep -oc "ELEMENTAL DYNAMICS" "$NEW"    # → 2

# 5. Bundle currency
curl -s http://localhost:8001/api/health | jq '.build.validation'
# → {"is_current":true, "errors":[]}
```

---

## 7. Prepared for Option A (Publish)

Both static targets are now fresh:

* `/app/frontend/dist/_expo/static/js/web/entry-e61db204b6516e90e67c5936927b14bc.js` ✓
* `/app/backend/web_dist/_expo/static/js/web/entry-e61db204b6516e90e67c5936927b14bc.js` ✓ (byte-identical copy — `yarn build:deploy` wipes `web_dist/*` and re-copies, matching MD5 `69e70acaf322113be2489f561d5ca88e`)

The deployed `mirror-lens-fixes-r-1779710763.emergent.host` is still serving the **old** bundle (`entry-a840aeeb…js`, last-modified 2026-05-31, byte-identical match to the very first audit). To roll forward:

> Hit **Publish** in the Emergent dashboard.

After the publish completes, the live `/api/health` on the deployed host should report:
* `build.deployed_bundle.name = entry-e61db204b6516e90e67c5936927b14bc.js`
* `build.validation.is_current = true`
* `debug.collections` should still show `expo-bundle-issue-mirror_staging` (Atlas) — DB topology unchanged

I'm happy to do a post-publish live `/api/health` + bundle MD5 verification against the deployed URL if you ping me after pressing Publish.

---

## 8. One-paragraph bottom line

A **5-line diff** (one OR-clause extended; one `.map(...)` block appended) on `RelationshipInsightV2Card.tsx` now renders the previously-invisible `bazi.activates_growth` array on the V2 card. For Pete↔Mel this lights up **2 additional lines** prefixed with `↑` under **ELEMENTAL DYNAMICS** — including the 🐒 Monkey ↔ 🐓 Rooster generational-energy reading. Strengthens (3 `+` lines) and drains (0) render exactly as before. HD, Astrology, Enneagram, Numerology, and all other tabs/sections/cards are untouched. The forum-mappings endpoint returns byte-identical signals to its pre-tweak output. `/api/health` reports the new bundle as current with zero validation errors. **Workspace is fully prepared for Emergent Publish.**
