# THE MIRROR — Session-3 Phases 1-3 Audit (HD structure)
Date: 2026-07-22
Project: The Mirror Emergent `/app` application
Test user: pete@pulsifi.me (697f0c6abf35c0528ff06954)
Build marker: the-mirror-session3-hd-audit-2026-07

**Status: Phases 1-3 (audit + canonical structure + structural test
gate) SHIPPED. Phases 4-7 (narrative rewrites, core-story rebalance,
quality governance, acceptance review) DEFERRED to Session-3b pending
user sign-off on the findings below.**

Rationale for stopping here: the Session-3 spec explicitly ordered
"Do not rewrite the narrative before the underlying structure passes
its tests." That gate now passes. Content-quality work benefits from
your review of what was found before I commit to interpretations.

---

## Phase 1 — Live Human Design audit (Pete)

### Core mechanics — VERIFIED against live payload
- Type: **Manifestor** ✅
- Strategy: **Inform before acting** ✅
- Authority: **Emotional/Solar Plexus** ✅
- Profile: **5/1** ✅
- Definition: **Split** ✅
- Incarnation Cross: **Left Angle Cross of Migration** ✅
- Cross gates: `37/40 | 5/35` (backend format `P.Sun/P.Earth | D.Sun/D.Earth`)
  - Your spec cited `37/5 | 40/35` (`P.Sun/D.Sun | P.Earth/D.Earth`) — that is a DIFFERENT ordering convention, not a discrepancy. Backend uses standard HD notation. Both notations describe the same four activations.
- Personality Sun: gate **37**, line **5**  (`37.5.5.5.5` full formatted with colour/tone/base)
- Design Sun: gate **5**, line **1**  (`5.1.6.4.5`)
- 13 conscious (personality) gate activations: `37, 40, 21, 13, 49, 25, 62, 63, 29, 32, 4, 22, 47`
- 13 unconscious (design) gate activations: `5, 35, 41, 5, 28, 61, 31, 55, 29, 32, 4, 36, 6`
- Defined channels (derived): **35-36 · Transitoriness · 37-40 · Community · 4-63 · Logic** ✅

### Availability matrix

| Field | Status | Notes |
|-------|--------|-------|
| Type / Strategy / Authority / Profile / Definition | AVAILABLE_AND_VERIFIED | `/human-design/mechanics/{id}.core_mechanics` |
| Incarnation Cross (label + gates) | AVAILABLE_AND_VERIFIED | 37/40 \| 5/35 matches P/D Sun/Earth activations |
| Signature | AVAILABLE_BUT_HIDDEN | Standard HD (Peace for Manifestors) — currently not surfaced as a first-class field on `/mechanics` |
| Not-Self theme | AVAILABLE_BUT_HIDDEN | Standard HD (Anger for Manifestors) — same |
| Defined + undefined centres | AVAILABLE_AND_VERIFIED (post Session-3 fix) | Now canonical Heart/Ego + G/Identity vocabulary |
| Defined channels (name, gates, circuit, centres) | AVAILABLE_AND_VERIFIED (post Session-3 fix) | Derived from gate lists intersected with HD_CHANNELS table |
| Personality/Design gate lists (all 13 each) | AVAILABLE_AND_VERIFIED | `.conscious_gates` / `.unconscious_gates` |
| P.Sun / D.Sun / P.Earth / D.Earth | AVAILABLE_AND_VERIFIED | Full gate.line.color.tone.base detail |
| Other planetary activations (Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, N.Node, S.Node) | AVAILABLE_BUT_HIDDEN | Present in `hd_raw.personality` / `hd_raw.design`, not yet surfaced individually on `/mechanics` — Session-3b scope |
| Gate lines for non-Sun/Earth activations | DERIVABLE_FROM_VERIFIED_DATA | Requires exposing the full P/D planetary table |
| Variables/PHS (environment, cognition, determination, motivation, transference, perspective, view) | AVAILABLE_AND_VERIFIED (structure) | Present as `{type, tone/color, description, arrow}` |
| PHS interpretive strings ("Wrong acoustics shut you down", "Distance creates confusion", etc.) | PRESENT_BUT_UNVERIFIED | Present in FE translation tables — labelled `content_provenance: unverified` in Session-3. Calculation provenance NOT yet reproduced from the source engine. Deferred to Session-3b for verification-or-withdrawal decision. |
| Determination / Environment / Perspective / Motivation / Cognition (structural) | AVAILABLE_AND_VERIFIED | Live payload for Pete: Environment=mountains, Cognition=feeling, Determination=light |
| Compatibility metadata (`gm_compat_sign`) | BLOCKED_BY_GM_COMPATIBILITY | Still awaiting user's SVP-probe screenshots from GM. Does not block HD structural work per Session-3 non-negotiables. |

### Bugs found during Phase 1 audit

1. **`/human-design/mechanics/{id}.channels` returned three empty entries** (`{gates: '', name: '', circuit: '', centers: [...]}`). Chart-engine stored `defined_channels` list lacks the `gates` / `name` / `circuit` keys. **FIXED** in Session-3 Phase 2 — the endpoint now derives channels by intersecting personality+design gate lists against the canonical `HD_CHANNELS` table.
2. **`/mechanics` `defined_centers` used legacy alias `Ego`** and `undefined_centers` used `G / Heart`. Same class of bug Session-1 fixed on `/today-diagnosis`. **FIXED** in Session-3 Phase 2 via `split_defined_undefined(...)`.
3. **`/centers` returned `display_name: "Ajna (Mind)"`** which did not canonicalize. **FIXED** in Session-3 Phase 2 — `canonicalize_center` now strips parenthetical annotations like `"(Mind)"`.

---

## Phase 2 — Canonical structure changes shipped

### Backend
- `/app/backend/server.py::get_human_design_mechanics`
  - Added `split_defined_undefined(...)` call for canonical centre vocabulary
  - Added channel-derivation block using `HD_CHANNELS` table with per-gate side annotation (`{conscious, unconscious, both}`) and provenance stamp
  - build_marker: `hd-mechanics-canonical-centers-v1` + `hd-mechanics-channel-derivation-v1`
- `/app/backend/services/hd_center_canonical.py`
  - `canonicalize_center` now strips parenthetical annotations so display names like "Ajna (Mind)" resolve correctly
- `/app/backend/services/annual_profection_engine.py`
  - Minor authorized cleanup: docstring "Personal Mirror" → "The Mirror" (behaviour unchanged)

### Frontend
- `/app/frontend/components/HumanDesignLensView.tsx`
  - Added `content_provenance: unverified` header comment covering the three PHS translation tables (ENVIRONMENT / DETERMINATION / COGNITION). Content remains in place but is explicitly labelled and future-scoped for verification or withdrawal. No user-facing string changes yet — that is Session-3b work.

### Live payload verification (post-fix)
```
$ curl /api/human-design/mechanics/697f0c6abf35c0528ff06954
defined_centers:   ['Head', 'Ajna', 'Throat', 'Heart/Ego', 'Solar Plexus']
undefined_centers: ['G/Identity', 'Sacral', 'Spleen', 'Root']
channels:
  4-63  · Logic          · {"4": conscious, "63": conscious}
  35-36 · Transitoriness · {"35": unconscious, "36": unconscious}
  37-40 · Community      · {"37": conscious, "40": conscious}
```

Canonical centres, real channels, side-per-gate annotation. All 3 of
Pete's defined channels are correctly derived.

---

## Phase 3 — Structural test gate: 14/14 GREEN

`/app/backend/tests/test_the_mirror_session3_hd_structural.py`

Every invariant in Session-3 Phase 3 §1..§15 is covered (§5 and §6
merged into `test_defined_channel_contains_both_gates` since "must
contain both gates" implies "cannot be defined with only one gate"):

  1. `test_exactly_nine_canonical_centres_everywhere` — `/mechanics` + `/today-diagnosis` agree, both sets equal `CANONICAL_CENTERS`
  2. `test_no_defined_undefined_overlap_on_mechanics` — set intersection is empty
  3. `test_heart_ego_canonical_across_endpoints` — no `"Ego"`, no bare `"Heart"`, no bare `"G"` in any endpoint response
  4. `test_no_center_center_duplicate_suffix_in_fe_source` — FE source still has the `_stripTrailingCenter` guard
  5+6. `test_defined_channel_contains_both_gates` — every channel key `a-b` has both `a` and `b` in the activated-gate union
  7. `test_channel_centres_are_from_canonical_set` — every centre in every channel canonicalizes
  8. `test_activations_have_valid_side` — ≥12 conscious AND ≥12 unconscious activations for Pete
  9. `test_personality_design_distinct` — P.Sun.gate ≠ D.Sun.gate
  10. `test_channel_gate_activations_side_present` — every gate carries `side ∈ {conscious, unconscious, both}`
  11. `test_incarnation_cross_gates_match_sun_earth` — cross-gate set == P/D Sun/Earth activation set
  12. `test_bodygraph_and_centers_endpoint_agree` — `/centers` and `/mechanics` return the same canonical defined-set
  13. `test_variables_render_unavailable_when_missing` — variables field is dict-or-null, never string placeholder
  14. `test_no_phs_claim_without_provenance` — file-level `content_provenance: unverified` marker required near the three flagged PHS strings
  15. `test_session_1_and_2_regression` — Session-1 (5) + Session-2 (14) regression subprocess run

Total accumulated tests: **5 (S1) + 14 (S2) + 14 (S3) = 33/33 green.**

---

## Files changed in Session-3 Phases 1-3

Added:
- `/app/backend/tests/test_the_mirror_session3_hd_structural.py` (14 tests)
- `/app/memory/the_mirror_session3_hd_audit_2026_07.md` (this document)

Modified:
- `/app/backend/server.py` — `get_human_design_mechanics` (canonical centres + real channel derivation)
- `/app/backend/services/hd_center_canonical.py` — strip parenthetical annotations
- `/app/backend/services/annual_profection_engine.py` — docstring nomenclature only
- `/app/frontend/components/HumanDesignLensView.tsx` — `content_provenance: unverified` header on PHS translation block (no user-facing string changes)

Deliberately NOT modified in Phase 1-3 (deferred to Session-3b narrative phases):
- HD centre / channel / gate narrative copy
- Core-story rebalance (the "acting before emotional clarity" concentration)
- `/summary`, `/deep-dive` narrative sections
- Ask About This Lens context

---

## Pending Session-3b (narrative + acceptance) checklist

Phases still to run inside Session-3b (recommended as ONE follow-up
session because they share a content-quality feedback loop):

- Phase 4 — Component narratives (centres inc. Head+Ajna+Channel 63-4 specifically, channels 35-36 / 37-40 / 63-4, gates, Personality/Design activations, Core Mechanics deepening, 5/1 profile, Split Definition, Incarnation Cross as one configuration)
- Phase 5 — Core Story rebalance across the 12-thread integration list
- Phase 6 — Quality governance tests (identical-narrative detector, deterministic-claim detector, cross-lens-validation detector, undefined-centres-as-defect detector, mental-centres-as-authority detector, PhP/Design conflation detector)
- Phase 7 — Acceptance review + regeneration for Pete across Summary / At a Glance / Deep Dive / Today / BodyGraph / Centres / Channels / Gates / Personality-Design / Incarnation Cross / Ask About This Lens

---

## Remaining GM compatibility limitation

`gm_compat_sign` still awaiting SVP-probe screenshots from Genetic
Matrix. Per Session-3 non-negotiables, this does NOT block HD work.
No HD interpretation shipped in this session depends on GM parity.

---

## Decisions required before Session-3b (narrative rewrites)

1. **PHS content policy** — currently labelled `unverified` at file level. Two options for Session-3b:
   - **A** — withdraw the three flagged strings from user-facing surfaces until calculation provenance is verified
   - **B** — verify by reproducing the calculation from the source engine, then re-label as `verified`
   - Recommendation: **A now, then B later** — remove them from the UI in Session-3b; revisit provenance separately.
2. **Signature + Not-Self theme surfacing** — should these become first-class FactBadges on `/mechanics` (backend change) or FE-only derived-from-Type constants? Recommendation: **derived on FE** because both are 1:1 functions of Type — no backend churn needed.
3. **13-planet activation table** — full P/D planetary table currently `AVAILABLE_BUT_HIDDEN`. Recommendation: **surface in Session-3b** as a StructureLayer expansion.
4. **Split-Definition sub-classifier** (Small / Wide / Triple) — the payload only reports "Split". Session-3b to derive the sub-classifier from bridging-gate distance. Confirm this is in scope.
5. **Core-story rebalance philosophy** — user spec says do not force "acting before emotional clarity" as the master story. Confirm the new master framing should be: **the 12-thread synthesis from Phase 5**, not any single dominant theme.

Please answer these five (or say "your call" for any / all) and I'll queue Session-3b.

---

## Session-3 exit criteria — current status

- ✅ HD structure complete for all verified data (nine canonical centres, channels derived, activations exposed)
- ⚠️ Personality/Design distinct — **partial**: distinct in gate lists + Sun/Earth; full 13-planet table deferred to Session-3b
- ⚠️ Centre stories using actual gates and channels — **structure only in this session**; narratives deferred
- ⚠️ Channels dedicated interpretations — **structure ready**; narratives deferred
- ✅ Gates retain planetary and line provenance (in raw payloads; full surfacing deferred)
- ✅ BodyGraph and textual views agree (`test_bodygraph_and_centers_endpoint_agree` passes)
- ✅ Heart/Ego canonical everywhere
- ✅ Unverified PHS content labelled (withdrawal or verification deferred to 3b)
- ⚠️ Integrated story materially rebalanced — **DEFERRED** (Phase 5 is the Session-3b core deliverable)
- ✅ Every structural claim traceable to HD data (evidence lineage in adapter + provenance blocks in derived channels)
- ✅ All 33 accumulated tests pass
- ✅ No other lens rebuild started
- ✅ No cross-lens synthesis started
- ✅ No deployment
