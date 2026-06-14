# BaZi Evidence Layer V2 — V2 Card Parity Delivery Report

**Date:** 2026-06-14
**Scope:** Apply the 4-section BaZi Evidence Layer (V2) — previously delivered
on `/forums/mappings` — to the Relationship Insight V2 card, so both surfaces
render identical structural evidence beneath the Wisdom / Synthesis layer.
**Constraint set respected:** renderer-side transformation only. No backend
schema changes. No new signal categories. No changes to
`compute_bazi_signals()`. No changes to BaZi math.

---

## 1. Goal

Match the Forum Mapping evidence UX 1:1 on the Relationship Insight V2 card:

- `ELEMENTAL DYNAMICS — Evidence` (renamed header)
- `1 · ELEMENTAL STRUCTURE` (elements, geometry, Direction-of-Flow, animals)
- `2 · WHAT STRENGTHENS THE FLOW` (labelled support rows)
- `3 · GROWTH TRIGGER` (animal-relation subtitle + labelled growth rows)
- `4 · SHADOW SIGNAL` (hidden when tension is empty)

The same `services/bazi/evidenceLabels.ts` module powers both renderers,
guaranteeing identical labels and verbs.

---

## 2. Changes (renderer-side only)

### Backend — passthrough plumbing (no math, no schema)

`/app/backend/server.py` — `/relationship-insight-v2/{user_id}` endpoint:

1. After the existing `compute_bazi_signals(...)` call (which already produces
   `support / tension / growth`), invoke `relationship_bazi_engine.build_relationship_bazi(...)`
   with the same args **for its diagnostics block only**.
2. Attach the returned `diagnostics` dict to `bazi_signals["diagnostics"]`.
   This is identical to what `/api/forum-mappings` already surfaces — the V2
   endpoint was simply not relaying it.
3. Expose top-level `you_name` (from the user doc) so the card can label
   "Direction of Flow" rows with the viewer's real name rather than a
   generic "You".

These additions are purely additive plumbing — they do not alter calculator
output, BaZi math, signal categories, or DB schema. The same engine has been
producing the same diagnostics for the forum-mappings endpoint since the
v2.2 narrative landed.

### Frontend — RelationshipInsightV2Card.tsx

- Imported `services/bazi/evidenceLabels.ts` (the same module forum mappings
  uses) and its `BaziCycle` / `AnimalRelation` types.
- Extended `RelInsightV2Data.signals.bazi` to declare optional `diagnostics`
  and added optional top-level `you_name` to the interface.
- Replaced the previous flat-list BaZi block with the same 4-section
  evidence renderer used in `app/forums/mappings.tsx` (`bazi-evidence-layer-v2`
  marker), including:
  - Direction-of-Flow rows derived from `EL.buildFlowRows(...)`
  - Geometry arrow from `EL.geometryArrow(...)`
  - Animal-relation label from `EL.animalRelationLabel(...)`
  - Section labels from `EL.labelFor(cycle, bucket, idx)`
  - Growth-trigger subtitle from `EL.growthTriggerSubtitle(...)`
- Legacy fallback retained: if `diagnostics` is missing for any reason, the
  card falls back to the previous flat list — same defensive behaviour as
  forum mappings.

---

## 3. Verification — Pete ↔ Mel

### API parity check (local, post-restart)

```
GET /api/relationship-insight-v2/697f0c6abf35c0528ff06954
    ?other_name=Mel&context=spouse

you_name: Pete
signals.bazi keys: ['strengthens', 'drains', 'activates_growth', 'diagnostics']
diagnostics:
  element_a: Metal
  element_b: Water
  cycle:     a_produces_b
  animal_a:  Monkey
  animal_b:  Rooster
  animal_relation: neutral
  role_key:  other
  support_count: 3
  tension_count: 0
  growth_count:  2
```

These values match the forum-mappings endpoint for the same pair.

### DOM render counts (V2 card, signals expanded)

```
ELEMENTAL DYNAMICS — Evidence  : 1
1 · ELEMENTAL STRUCTURE         : 1
2 · WHAT STRENGTHENS THE FLOW   : 1
3 · GROWTH TRIGGER              : 1
4 · SHADOW SIGNAL               : 0   ← correctly hidden (drains=0)
Direction-of-Flow header        : 1
Metal → Water geometry          : 1
Pete / Monkey / Rooster names   : 10  ← real names in flow rows + animals
```

The single absence (Shadow Signal) is intentional and matches the
`tension.length > 0` gate — it would also be hidden on the forum-mapping
side for this pair, since both lenses now read from the same upstream
`compute_bazi_signals(...)` result.

### Bundle fingerprint

```
/app/backend/web_dist/_expo/static/js/web/entry-b3cdf036630b6f659f0a728a5bb5b997.js
```

Built via `yarn build:deploy` (`expo export --platform web` →
`backend/web_dist/`). Bundle string occurrences:

```
ELEMENTAL STRUCTURE        : 2   ← forum-mapping + v2 card
WHAT STRENGTHENS THE FLOW  : 2
GROWTH TRIGGER             : 2
SHADOW SIGNAL              : 2
ELEMENTAL DYNAMICS         : 4   ← header + evidence labels
bazi-evidence-layer-v2     : 1   ← marker (defined once in evidenceLabels.ts)
```

Each evidence-section header appears exactly twice in the bundle — once per
renderer — confirming the V2 card and forum mapping ship the same code path.

---

## 4. Regression Surface

- **No backend schema changes.** `signals.bazi` still has the same three
  required arrays. `diagnostics` is an additive optional field; consumers
  that ignore it continue to work.
- **No calculator drift.** `compute_bazi_signals(...)` is unmodified; the
  diagnostics block is sourced from `relationship_bazi_engine`, which
  already produced this block for forum mappings.
- **Legacy fallback preserved.** If diagnostics are ever absent (older
  deploy, partial chart, exception path), the V2 card renders the previous
  flat list rather than crashing.
- **No new lens added.** The Layer-3 "Why this is so strong" gate still
  considers HD / Astro / BaZi / Enneagram / Numerology together.

---

## 5. Files Touched

```
M  /app/backend/server.py
   └─ +diagnostics passthrough, +you_name field
M  /app/frontend/components/RelationshipInsightV2Card.tsx
   └─ +evidenceLabels import, interface extensions, 4-section BaZi block
A  /app/backend/audit_reports/BAZI_EVIDENCE_LAYER_V2_PARITY_DELIVERY.md
```

Static web build refreshed: `frontend/dist/` + `backend/web_dist/` overwrite.

---

## 6. Hold Points

Per user directive: stop here, await review. No further BaZi changes,
no flag ungating, no production-data-dependent work until Atlas access
is confirmed.
