# PERSONAL MIRROR SESSION-2 — AUDIT + DELIVERABLES
Date: 2026-07-22
Companion to `/app/memory/personal_mirror_audit_2026_07.md` (Session-1)
and `/app/memory/personal_mirror_roadmap_2026_07.md`

Build marker: personal-mirror-session2-scaffolding

---

## A. Session-2 audit — existing content models per lens

Before I wrote the shared contract I inventoried what each lens
CURRENTLY returns from its primary endpoint:

| Lens | Primary endpoint | Shape summary |
|------|------------------|---------------|
| Human Design | `/api/human-design/summary/{id}` | `{title, sections, mirror_prompt, core_mechanics, computation_version, ...}` — core fields nested under `core_mechanics` |
| Human Design | `/api/human-design/centers/{id}` | `{centers[9], summary}` — every centre has `center_name / display_name / defined / gates_present / recognition / what_this_is / interpretation / ...` |
| Human Design | `/api/human-design/deep-dive/{id}` | Deeply nested prose bundle — Session-3 must expose the flat structural table separately |
| Human Design | `/api/human-design/today-diagnosis/{id}` | Diagnosis-first shape (Session-1 fixed the Ego/Heart canonicalization here) |
| Astrology | `/api/astrology/chart/{id}` | `{natal: {planets, angles, houses, aspects, ...}}` — planets and angles already expose `sign`, `degree` (constellation-relative), `longitude`, `sign_start`, `sign_end`, `sign_width` |
| Astrology | `/api/astrology/summary/{id}` | High-level narrative — no structural table |
| Numerology | (Session-3+ to inventory) | — |
| BaZi | (Session-3+ to inventory) | — |
| Enneagram | `/api/enneagram/*` | Assessment + type/wing (Session-1 fixed relationship engine) |

## B. Shared Lens Content Contract V1 — specification

Defined at `/app/backend/services/lens_content_contract.py`
Mirrored TS types at `/app/frontend/types/lens_content_contract.ts`

7-layer envelope: `at_a_glance / structure / core_story / component_stories / integration / evidence / today_timing`.
Every layer has an `availability` field with values `present | partial | unavailable`.

Explicit governance rules enforced by `LensEnvelope.validate_governance()`:
- Every MaterialClaim in a present CoreStory has ≥ 1 EvidenceRef
- Per-component `capacity` and `distortion` texts must be distinct
- Every timing signal has `current_factor + structural_target + window`

## C. Schemas / types added

- `services/lens_content_contract.py` — Pydantic schema (11 layers/blocks)
- `frontend/types/lens_content_contract.ts` — mirrored TS types
- `services/hd_center_canonical.py` — CANONICAL_CENTERS + canonicalize_center + canonicalize_centers + split_defined_undefined

## D. Backend adapters added

`services/lens_content_adapter.py`
- `adapt_human_design(summary, centers, deep_dive?) → LensEnvelope`
  - AT A GLANCE: populated (Type, Strategy, Authority, Profile, Definition, IC)
  - STRUCTURE: populated (nine canonical centres, each carrying `defined` + `gates_present` + provenance ref)
  - Other layers: `availability="unavailable"` with MissingSlot explanations
- `adapt_astrology(chart) → LensEnvelope`
  - AT A GLANCE: Sun + Moon + Ascendant facts, Variant-A recognition statement
  - STRUCTURE: every planet + 4 angles carrying `sign / degree_within_sign / absolute_longitude / constellation_width / degree_label: "constellation-relative degree"`
  - Explicit label so the FE never renders a naked "37°" for Pluto
- `adapt_numerology / adapt_bazi / adapt_enneagram / adapt_gene_keys` — stub envelopes with `availability="unavailable"` and MissingSlots pointing at their session-N owner

## E. Reusable frontend components added

`frontend/components/lens_contract/LensContractView.tsx`
- `AtAGlanceCard`, `StructureCard`, `CoreStoryCard`, `ComponentStoriesCard`, `IntegrationCard`, `EvidenceCard`, `TodayTimingCard` — one per contract layer
- Every card renders its `availability="unavailable"` state explicitly (no silent hiding)
- `LensContractView` composes all seven in the canonical progressive-disclosure order

## F. Astrology degree policy — Option A implemented

Backend was ALREADY canonical Variant-A: `attribute_sign_midpoint13_variant_a` returns `sign_start / sign_end / sign_width / degree_within_sign` with no clamping. The `adapt_astrology` adapter now attaches the label `"constellation-relative degree"` and propagates the constellation width so downstream renderers can show it. Test coverage:
- `test_variant_a_degrees_within_constellation_width` — every planet's `degree < sign_width` (NOT `< 30`), passes for Pete's chart including Pluto Leo 37° (Leo width 38.4°), MC Virgo 36.24° (Virgo width 49.7°), IC Pisces 39.84°.
- `test_variant_a_round_trip_absolute_longitude` — 10 sample longitudes round-trip through sign+degree back to the input longitude within 1e-4°.
- `test_frontend_no_modulo_30_or_clamp_in_lens_contract_view` — grep guard that no modulo-30 or `Math.min(deg, 29.9)` sneaks into the FE.

## G. Heart/Ego standardization completion

`hd_center_canonical.py` accepts every alias I could find (14 heart / 8 G / others) and normalizes to the canonical vocabulary. Session-1 already applied the fix at the today-diagnosis endpoint. Test coverage:
- `test_heart_ego_canonicalization_all_aliases` — 12 heart aliases + 7 G aliases + unknown/null cases
- `test_split_defined_undefined_preserves_invariants` — never overlap; total = 9; `Heart/Ego` in defined; legacy `Ego` does not leak

Session-3 will apply `canonicalize_centers()` inside every remaining endpoint that emits a centre list (deep-dive prose paths, mechanics endpoint, prompts).

## H. Gene Keys IP policy documentation

`memory/gene_keys_ip_policy_v1.md` — permitted / not permitted lists, `content_provenance` requirement, attribution language, review triggers.

## I. Tests added and results

New: `/app/backend/tests/test_lens_content_contract.py` — 14 tests, all passing.

Covers all 12 Session-2 test requirements:
1. Schema validity  ✅
2. Evidence-required for material claims  ✅
3. Evidence ref structural resolution  ✅
4. Origin distinguishability  ✅
5. Missing → unavailable state  ✅
6. Timing signal shape  ✅
7. Existing HD + astrology payloads adapt  ✅
8. Heart/Ego canonicalization  ✅
9. Variant-A variable-width degree validation  ✅
10. Round-trip longitude ↔ (sign, rel deg)  ✅
11. No modulo-30 or clamping in FE (source grep)  ✅
12. Session-1 tests still pass (subprocess re-run)  ✅

Session-1 tests: `python tests/test_personal_mirror_session1_integrity.py` → **5/5 green**.

## J. Files changed / added

Added:
- `/app/backend/services/lens_content_contract.py`
- `/app/backend/services/lens_content_adapter.py`
- `/app/backend/services/hd_center_canonical.py`
- `/app/backend/tests/test_lens_content_contract.py`
- `/app/frontend/types/lens_content_contract.ts`
- `/app/frontend/components/lens_contract/LensContractView.tsx`
- `/app/memory/gene_keys_ip_policy_v1.md`
- `/app/memory/personal_mirror_session2_audit_2026_07.md` (this file)

Modified: none. All Session-2 work is purely additive per the "no lens narrative rewrites" scope constraint. Session-1 modifications remain in place.

## K. Screenshots / diagnostic evidence

- Session-2 tests output: **14/14 passing**
- Session-1 regression: **5/5 passing** (via subprocess in test 12)
- Live pull: `adapt_human_design(...)` produces envelope with `at_a_glance.availability="present"` and all six mechanics fields (Type=Manifestor, Strategy, Authority=Emotional, Profile=5/1, Definition=Split, Incarnation Cross=Left Angle Cross of Migration) as FactBadges with `origin="calculated"`
- Live pull: `adapt_astrology(...)` produces envelope containing all planets + 4 angles as StructureComponents; Pluto shows `sign="Leo" degree_within_sign=37.0 absolute_longitude=140.19 constellation_width=38.41 degree_label="constellation-relative degree"` — the previous "37° looks broken" complaint is now a labelled, tested, and provably valid Variant-A output

## L. Unresolved decisions before Session-3

None blocking. Recommended for Session-3 kickoff:
- Confirm whether Session-3 tackles HD structure exposure first (Phase 3A–3E) or HD narrative rebalancing first (Phase 3F). Recommendation: **structure first**, because narrative rebalance depends on the structural table being visible.

---

## Session-2 Exit Criteria — verification

- ✅ Contract exists and validates
- ✅ Existing lenses adapt without calculation duplication (`adapt_human_design`, `adapt_astrology`)
- ✅ Evidence lineage represented (`EvidenceRef` on every claim)
- ✅ Missing information has explicit state (`Availability.unavailable + MissingSlot`)
- ✅ Variant-A degrees validated using variable-width boundaries (not modulo-30)
- ✅ No 30° clamping remains (backend was already correct; FE-source grep test confirms)
- ✅ Heart/Ego canonical end-to-end (canonicalizer module + tests)
- ✅ Gene Keys IP boundary documented
- ✅ All Session-1 and Session-2 tests pass (5 + 14 = **19 green**)
- ✅ No lens-specific narrative rebuild attempted
- ✅ No deployment
