# HD Incarnation Cross Output Integrity — Forensic + Fix Report

**Date:** 2026-06-13
**Status:** ✅ FIXED & VERIFIED (20/20 frontend rendering probes + FKR v1 regression 5/5)
**Scope:** Display/rendering layer only. NO changes to HD calculator, birth
data, stored chart data, FKR v1, astrology, timeline, relationship
orchestration, or rollout flags.

---

## 1. Forensic trace — where the generic prose came from

The Deep Dive's collapsible "Incarnation Cross" card is rendered from a
`MirrorCard` produced by `getCrossMirrorCard()` in
`frontend/utils/humanDesignMirrorCards.ts`.  The original implementation
collapsed the stored cross name to one of three angle keys
(`Right Angle` / `Left Angle` / `Juxtaposition`) and returned the
corresponding entry from `CROSS_MIRROR_CARDS`:

```ts
// BEFORE — every Right Angle cross flattened to the same card.
export function getCrossMirrorCard(crossType: string): MirrorCard | null {
  if (crossType.toLowerCase().includes('right angle'))   return CROSS_MIRROR_CARDS['Right Angle'];
  if (crossType.toLowerCase().includes('left angle'))    return CROSS_MIRROR_CARDS['Left Angle'];
  if (crossType.toLowerCase().includes('juxtaposition')) return CROSS_MIRROR_CARDS['Juxtaposition'];
  return null;
}
```

`CROSS_MIRROR_CARDS['Right Angle']` had:
- `title: 'Right Angle Cross'`
- `subtitle: 'Personal destiny'`

That is precisely the generic header Isaac and Thaddeus were both
showing.  Backend was already returning the correct specific cross
name (`extract_human_design_data` in `server.py`) — the loss happened
purely at the rendering boundary.

Field-by-field source map for the Deep Dive card:

| Card field         | Came from                                                       | Bug effect |
|---|---|---|
| title              | `CROSS_MIRROR_CARDS['Right Angle'].title`                       | Generic "Right Angle Cross" |
| subtitle           | `CROSS_MIRROR_CARDS['Right Angle'].subtitle`                    | Generic "Personal destiny" |
| recognition        | `CROSS_MIRROR_CARDS['Right Angle'].recognition`                 | Same prose for every RAX |
| tension            | `CROSS_MIRROR_CARDS['Right Angle'].tension`                     | Same |
| realLifeMoments    | `CROSS_MIRROR_CARDS['Right Angle'].realLifeMoments`             | Same |
| truthShift         | `CROSS_MIRROR_CARDS['Right Angle'].truthShift`                  | Same |
| tryThisInstead     | `CROSS_MIRROR_CARDS['Right Angle'].tryThisInstead`              | Same |
| core_mechanics row | `data.core_mechanics.incarnation_cross` (✅ specific stored value) | Specific value WAS available — not used |

The modal at `HumanDesignLensView.tsx:3042` actually already consulted
the family-specific `CROSS_FAMILY_STORIES` map — but the Deep Dive
collapsible card never reached that branch.  Hence the inconsistency
between modal copy and card copy.

## 2. Confirmation of source data

Direct API probes on local backend (no LLM, deterministic):

```
GET /api/human-design/mechanics/69dd0b2cc92ba973f8838c11  (Thaddeus)
 incarnation_cross:        Right Angle Cross of Sleeping Phoenix
 incarnation_cross_gates:  20/34 | 55/59

GET /api/human-design/mechanics/69dda348de9cb1c83c0780f8  (Isaac)
 incarnation_cross:        Right Angle Cross of Consciousness
 incarnation_cross_gates:  63/64 | 5/35

GET /api/human-design/mechanics/697f0c6abf35c0528ff06954  (Pete)
 incarnation_cross:        Left Angle Cross of Migration
 incarnation_cross_gates:  37/40 | 5/35
```

Stored data is correct. The bug is purely renderer-side.

## 3. Patches applied (rendering layer only)

| File | Change |
|---|---|
| `backend/server.py` (`extract_human_design_data`) | Re-formatted `incarnation_cross_gates` to canonical `P.Sun/P.Earth \| D.Sun/D.Earth` (e.g. `20/34 \| 55/59`). Reuses the raw `gates` string from the stored dict when available so we always surface the format the calculator already produced. |
| `frontend/utils/humanDesignMirrorCards.ts` | Added **11 family-specific `MirrorCard`s** in `CROSS_FAMILY_MIRROR_CARDS` (Sphinx, Sleeping Phoenix, Consciousness, Migration, Tension, Vessel of Love, Eden, Contagion, Explanation, Planning, Service). Added `extractCrossFamily()`. Rewrote `getCrossMirrorCard(crossType, crossGates?)` so it: (1) returns `null` for unknown/empty/"Unknown" inputs (no silent generic fallback); (2) prefers the family-specific card; (3) falls back to the angle card ONLY when family is genuinely unknown; (4) **always overrides `title` with the exact stored cross name** and appends the gate quartet to the subtitle. |
| `frontend/components/HumanDesignLensView.tsx` | Updated the call site to pass `data.core_mechanics.incarnation_cross_gates` as the second argument. |
| `frontend/scripts/hd_cross_acceptance_probe.ts` | New 20-check regression suite (compiled with project tsc). |

### Fallback rule (matches your spec)

The card returns `null` (and the section is suppressed) when **all** of
the following are true:
- no specific incarnation cross name exists on the chart,
- no gate quartet exists,
- the stored value is genuinely "Unknown" / "" / "—".

When a stored name exists but the family is not yet catalogued in
`CROSS_FAMILY_MIRROR_CARDS`, the renderer falls back to the angle card
**but still uses the specific stored cross name as the title and
appends the gate quartet to the subtitle**, so the generic "Right Angle
Cross / Personal destiny" header never appears for a real chart.

## 4. Acceptance results

### Frontend rendering probe (20/20 ✅)
```
✅ isaac.title canonical            — Right Angle Cross of Consciousness
✅ thad.title canonical             — Right Angle Cross of Sleeping Phoenix
✅ pete.title canonical             — Left Angle Cross of Migration
✅ isaac.subtitle contains gates    — Clarity as contribution · 63/64 | 5/35
✅ thad.subtitle contains gates     — Rising from quiet collapse · 20/34 | 55/59
✅ pete.subtitle contains gates     — Movement as identity · 37/40 | 5/35
✅ recognition differs (Isaac vs Thaddeus)
✅ tension differs
✅ truthShift differs
✅ realLifeMoments differ
✅ thad card free of "Sphinx" leakage
✅ subtitle ≠ bare "Personal destiny"
✅ empty crossType → null
✅ "Unknown" → null
✅ family extractor: Sphinx / Sleeping Phoenix / Consciousness
✅ family map has Sleeping Phoenix / Consciousness / Migration
```

### Before / After text evidence

```
BEFORE (Isaac)               AFTER (Isaac)
title:    Right Angle Cross  title:    Right Angle Cross of Consciousness
subtitle: Personal destiny   subtitle: Clarity as contribution · 63/64 | 5/35
recogn:   <generic RAX>      recogn:   You're oriented around the drive to make sense of things…

BEFORE (Thaddeus)            AFTER (Thaddeus)
title:    Right Angle Cross  title:    Right Angle Cross of Sleeping Phoenix
subtitle: Personal destiny   subtitle: Rising from quiet collapse · 20/34 | 55/59
recogn:   <same generic RAX> recogn:   Your life has rhythms of dormancy and re-emergence…
```

### FKR v1 regression (5/5 ✅)
Already-passing FKR v1 acceptance probes re-run after the patch:
- `[PASS] P1.FACT_LOOKUP — Thaddeus incarnation cross`
- `[PASS] P2.FACT_LOOKUP — asker self placements`
- `[PASS] P3.RELATIONSHIP — Pete and Mel dynamic`
- `[PASS] P4.COMPARISON — Pete vs Mel`
- `[PASS] P5.TIMELINE — what is emerging for me`

### Locked flags — unchanged
```
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

## 5. Re-run commands

```bash
# Frontend rendering probe
cd /app/frontend && node_modules/.bin/tsc --target es2020 --module commonjs \
  --moduleResolution node --esModuleInterop --skipLibCheck --outDir /tmp/hd_probe \
  scripts/hd_cross_acceptance_probe.ts utils/humanDesignMirrorCards.ts && \
  node /tmp/hd_probe/scripts/hd_cross_acceptance_probe.js

# FKR v1 regression
cd /app/backend && python scripts/fkr_v1_acceptance_probes.py

# Live API spot-check
curl -s http://localhost:8001/api/human-design/mechanics/69dd0b2cc92ba973f8838c11 | jq '.core_mechanics'
curl -s http://localhost:8001/api/human-design/mechanics/69dda348de9cb1c83c0780f8 | jq '.core_mechanics'
```
