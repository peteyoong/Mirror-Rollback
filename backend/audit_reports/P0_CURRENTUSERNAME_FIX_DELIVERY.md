# P0 Fix Report — `currentUserName` ReferenceError

**Date:** 2026-06-14
**Status:** ✅ Applied, built, deployed bundle verified, smoke-test passed.

---

## 1. Change Applied (one line, one token)

```diff
File: /app/frontend/app/forums/mappings.tsx
Line: 929

- const nameA = currentUserName || 'You';
+ const nameA = user?.name || 'You';
```

`user` is already destructured from `useAppStore()` at line 29 (top of
`ForumMappingsScreen`) and is guaranteed in scope inside
`renderDetailModal()`. The `|| 'You'` fallback is preserved exactly.

## 2. Constraints Honored

| Constraint                                          | Status |
| --------------------------------------------------- | :----: |
| BaZi math unchanged                                 | ✅ (zero backend / engine touches) |
| Backend unchanged                                   | ✅ |
| API payload unchanged                               | ✅ |
| `RelationshipInsightV2Card.tsx` unchanged           | ✅ (verified — no edits) |
| Feature flags unchanged                             | ✅ (all 5 flags including `RELATIONSHIP_FIELD_V2_PROMPT=false`) |
| No DB writes                                        | ✅ |
| No migrations                                       | ✅ |

## 3. Build

```
$ yarn build:deploy
... Exported: dist
... Done in 9.44s.

Old bundle: entry-b3cdf036630b6f659f0a728a5bb5b997.js  (3,976,097 b)
NEW bundle: entry-c14a85ea4f24e0d01884b9236c1aa051.js  (3,976,089 b)
Δ        : 8 bytes smaller (consistent with the source line being
            shorter after the rename: `currentUserName`(15) → `user?.name`(10))
```

## 4. Bundle Verification

### 4.1 Offending identifier removed

```
grep -oc "currentUserName"  entry-c14a85ea4f24e0d01884b9236c1aa051.js
0           ← was 1 in the previous bundle
```

### 4.2 Patched call-site shape

```
@2778198 in new bundle:
  "...'',j=o.animal_b||'',S=o.animal_relation||'unknown',
       b=w?.name||'You',_=F?.member_name||'Them',..."
                ↑
       minified user?.name (was currentUserName before)
```

### 4.3 Required Evidence-Layer-V2 markers all present

| Marker                                  | Encoded form in bundle               | Occurrences | Expected |
| --------------------------------------- | ------------------------------------ | :---------: | :------: |
| `bazi-evidence-layer-v2`                | unchanged                            | **1**       | 1        |
| `ELEMENTAL DYNAMICS — Evidence`         | `ELEMENTAL DYNAMICS \u2014 Evidence` | **4**       | 4 (2 per renderer × 2 renderers) |
| `1 · ELEMENTAL STRUCTURE`               | `1 \xb7 ELEMENTAL STRUCTURE`         | **2**       | 2        |
| `2 · WHAT STRENGTHENS THE FLOW`         | `2 \xb7 WHAT STRENGTHENS THE FLOW`   | **2**       | 2        |
| `3 · GROWTH TRIGGER`                    | `3 \xb7 GROWTH TRIGGER`              | **2**       | 2        |
| `4 · SHADOW SIGNAL`                     | `4 \xb7 SHADOW SIGNAL`               | **2**       | 2        |

All section markers ship in both renderers (forum-mappings + V2 card)
exactly as before the bug fix.

## 5. Live Smoke Test — Mel detail modal

Replayed the user's repro steps with a Playwright session seeded as Pete:

| Step                                                 | Result                                   |
| ---------------------------------------------------- | ---------------------------------------- |
| 1. Open `/forums/mappings?forumId=Pete & Mel`        | HTTP 200, "Computing connections…" → list |
| 2. Tap Mel in member list                            | Modal mounts cleanly                     |
| 3. Modal renders                                     | "Mel · What happens between you" + full body |
| 4. Sections from BELOW the previously-crashing line  | All render (`WHAT LIVES BETWEEN YOU`, `Emotional reach`, `Building together`, `GIFT OF THIS CONNECTION`) — proves JS execution flowed past line 929 |
| 5. "Pete" appears in visible content                 | 4× (Direction-of-Flow rows now use `user?.name`) |
| 6. `Can't find variable: currentUserName`            | **0 occurrences** in DOM                 |
| 7. React Error Boundary visible                       | **No** — `crash_visible: false`          |
| 8. JS `pageerror` events captured                     | **No ReferenceError** captured            |

Screenshot shows the modal open with the Wisdom-Mode narrative and the
subsequent "WHAT LIVES BETWEEN YOU" / GIFT cards rendering — content
that lives **after** the previously-fatal line in the render tree.

## 6. Combined Test Suite — Unchanged, Still Green

```
Slice 1 (resolver unit):            9/9   PASS
Slice 2 (Ask Mirror wiring):        7/7   PASS
Slice 2.5 (replay validation):      6/6   PASS
Slice 3 (prompt gate):             12/12  PASS
Variant-A / Ophiuchus suite:       31/31  PASS
```

The patch is a renderer-only one-token change; no backend / Python
tests were affected.

## 7. Side-Effect Audit

```
$ git-equivalent diff   (against the prior tree)
   1 file changed,  1 insertion (+),  1 deletion (-)
   /app/frontend/app/forums/mappings.tsx

$ frontend ref count:
   currentUserName  : 0  (was 1)
   user?.name       : referenced in 5 sites in this file
                      (lines 40, 43, 46, 295, 929) ← canonical pattern
```

No other file touched. Backend bundle/runtime untouched.

## 8. Deploy Posture

- New bundle `entry-c14a85ea4f24e0d01884b9236c1aa051.js` ready in
  `/app/backend/web_dist/_expo/static/js/web/`.
- Flag state unchanged: `RELATIONSHIP_FIELD_V2_PROMPT=false` and all
  four pre-existing flags still in their committed values.
- Atlas access remains blocked pending IP whitelist — all verification
  ran against `localhost`.

P0 fix is complete. Stopping per directive.
