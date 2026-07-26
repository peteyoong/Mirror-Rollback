# The Mirror — Session 4A: Gene Keys Foundation Audit
## Structural foundation only — no narrative rewrite, no deployment
**Date:** 2026-07-26  
**Canonical version:** `mirror_true_sidereal_gk_v1`  
**Mechanics version:** `gene_keys_mechanics_v1`  
**Human Design engine consumed:** `hd_sidereal_v1`

---

## Deliverable A — Existing Gene Keys implementation audit

### Backend inventory (before Session 4A)

| Item | File | LOC | Session-4A classification |
|---|---|---|---|
| Sphere→planet mapping (legacy calc) | `calculations/gene_keys.py` | 222 | **INCORRECT_FIXED** (see B) |
| Sphere→planet mapping (legacy interpreter docstring) | `services/gene_keys_interpreter.py` | 556 | **INCORRECT_FIXED** (see B) |
| Sphere interpretation templates (Mirror-authored SPHERE_TEMPLATES) | `services/gene_keys_interpreter.py` | (subset) | **AVAILABLE_AND_VERIFIED** — provenance = `mirror_original` |
| Shadow/Gift/Siddhi structural labels (per-key) | `data/gene_keys_data.py` | 562 | **AVAILABLE_AND_VERIFIED** as `structural_label`; long free-text descriptions require line-by-line IP audit before Session 4B |
| Chat matcher | `services/gene_keys_matcher.py` | 332 | **AVAILABLE_AND_VERIFIED** — no long-form prose |
| Regression test suite | `tests/test_gene_keys_regression.py` | 315 | **AVAILABLE_AND_VERIFIED**, updated for canonical map |
| REST endpoints — `/gene-keys/activation-sequence`, `/venus-sequence`, `/pearl-sequence`, `/profile/{user_id}`, `/available` | `server.py` | ~500 | **AVAILABLE_BUT_LEGACY** — retained for the embedded HD section; not consumed by the new lens |
| Frontend `GeneKeysView.tsx` (embedded in HD Deep Dive) | `frontend/components/GeneKeysView.tsx` | 562 | **AVAILABLE_BUT_HIDDEN** in the standalone lens for Session 4A; still rendered inside Human Design |

### Newly added in Session 4A

| Item | File | Purpose |
|---|---|---|
| Canonical sphere map | `services/gene_keys_sphere_map.py` | Single source of truth for sphere → (planet, chart_side); methodology provenance; Star Pearl policy |
| Canonical mechanics builder | `services/gene_keys_mechanics.py` | Builds the mechanics envelope for the standalone lens |
| `/api/gene-keys/mechanics/{user_id}` endpoint | `server.py` | Canonical read model |
| Standalone lens frontend | `frontend/components/GeneKeysLensView.tsx` | Parent-owned single fetch, tab scaffold |
| Session-4A test suite | `tests/test_the_mirror_session4a_gene_keys_foundation.py` | 34 tests, all passing |

---

## Deliverable B — Calculation and activation lineage

- Astronomical longitudes and 64-gate placement are produced by
  `calculations/human_design.get_human_design_chart(...)` — engine tag
  `hd_sidereal_v1`.  Gene Keys **does not recompute astronomy**.
- Session 4A introduces `services/gene_keys_sphere_map.py` as the sole
  source of truth for sphere→(planet, chart_side).  Both
  `calculations/gene_keys.py` and `services/gene_keys_interpreter.py`
  now consume it (`CANONICAL_SPHERE_MAP`).
- The canonical map follows the first-party Gene Keys documentation:
  - Life's Work / Brand → Personality Sun
  - Evolution → Personality Earth
  - Radiance → Design Sun
  - Purpose → Design Earth
  - Attraction → Design Moon
  - IQ → Personality Venus
  - EQ → Personality Mars
  - SQ → Design Venus
  - Core / Vocation → Design Mars
  - Culture → Design Jupiter
  - Pearl → Personality Jupiter

### Deltas vs. legacy sources (recorded in `LEGACY_CALC_MAP` and `LEGACY_INTERPRETER_DOCSTRING_MAP`)

| Sphere | Legacy `calculations/gene_keys.py` | Legacy `interpreter.py` docstring | Canonical (fixed) |
|---|---|---|---|
| Attraction | Venus/design ❌ | Moon/design ✅ | **Moon/design** |
| IQ | Mercury/personality ❌ | Mercury/personality ❌ | **Venus/personality** |
| EQ | Venus/personality ❌ | Mercury/design ❌ | **Mars/personality** |
| SQ | Moon/design ❌ | Venus/design ✅ | **Venus/design** |
| Core | Mars/design ✅ | Mars/personality ❌ | **Mars/design** |
| Culture | Jupiter/design ✅ | Jupiter/personality ❌ | **Jupiter/design** |
| Pearl | Jupiter/personality ✅ | Jupiter/design ❌ | **Jupiter/personality** |

---

## Deliverable C — Pete's verified sphere mapping

Derived under the canonical map from Pete's HD activations (no hard-coded
sphere-to-gate lookup):

| Sphere | Sequence | Activation | Derived GK | Line | Expected fixture | Status |
|---|---|---|---|---|---|---|
| Life's Work | Activation | P Sun | 37 | 5 | 37 | ✅ verified |
| Evolution | Activation | P Earth | 40 | 5 | 40 | ✅ verified |
| Radiance | Activation | D Sun | 5 | 1 | 5 | ✅ verified |
| Purpose | Activation | D Earth | 35 | 1 | 35 | ✅ verified |
| Attraction | Venus | D Moon | 41 | 5 | 41 | ✅ verified |
| IQ | Venus | P Venus | **49** | 1 | 13 | ⛔ **discrepancy_held** |
| EQ | Venus | P Mars | **25** | 4 | 5 | ⛔ **discrepancy_held** |
| SQ | Venus | D Venus | 28 | 1 | 28 | ✅ verified |
| Core | Venus | D Mars | **61** | 5 | 25 | ⛔ **discrepancy_held** |
| Vocation | Pearl | D Mars (shares w/ Core) | 61 | 5 | 61 | ✅ verified |
| Culture | Pearl | D Jupiter | **31** | 3 | 62 | ⛔ **discrepancy_held** |
| Brand | Pearl | P Sun (shares w/ Life's Work) | 37 | 5 | 37 | ✅ verified |
| Pearl | Pearl | P Jupiter | **62** | 6 | 31 | ⛔ **discrepancy_held** |

**Held per user rule (2026-07-26): no fit-and-document.**  Affected
mechanics and UI are surfaced as `verification_status="discrepancy_held"`.

### Discrepancy classification

The five discrepancies form a clear pattern:

| Sphere | Expected planet in Pete's fixture | Canonical first-party planet | Likely source |
|---|---|---|---|
| IQ | Personality Mercury (13) | Personality Venus (49) | **Sphere mapping** — fixture appears to use a pre-canonical convention where IQ/EQ read from Mercury, not Venus/Mars |
| EQ | Design Mercury (5) | Personality Mars (25) | Sphere mapping |
| Core | Personality Mars (25) | Design Mars (61) | Sphere mapping (Personality/Design side reversed) |
| Culture | Personality Jupiter (62) | Design Jupiter (31) | Sphere mapping (side reversed) |
| Pearl | Design Jupiter (31) | Personality Jupiter (62) | Sphere mapping (side reversed) |

**Diagnosis:** Pete's expected fixture predates the reconciled first-party
sphere map and was likely captured against an earlier Gene Keys convention
(Mercury-based intelligences + Personality-Mars Core + reversed
Personality/Design on the Jupiter pair).  No zodiac-convention, design-
date, gate-mandala offset or line-boundary evidence supports the deltas —
they all lie on the sphere-mapping axis.

### User decisions required before Session 4B

1. **Accept the canonical first-party mapping** as the new source of
   truth and retire the earlier fixture (Pete's expected values become
   part of "legacy — pre-canonical").
2. **Or** provide an authoritative third-party reference showing IQ =
   Mercury / EQ = Mercury / Core = Personality Mars / Culture =
   Personality Jupiter / Pearl = Design Jupiter, in which case the
   canonical map is revised and re-verified.

Until this decision, the five affected spheres are held.

---

## Deliverable D — Methodology disclosure (progressive, non-leading)

Shipped in `services/gene_keys_sphere_map.METHODOLOGY_PROVENANCE.disclosure`
and surfaced under the "About this calculation" tab of the standalone lens:

> This profile uses The Mirror's True Sidereal activation method. It may
> differ from profiles calculated using other zodiac or Human Design
> conventions.

Sphere-to-activation semantics follow the first-party Gene Keys
correlations.  Longitudes, the Design (pre-natal) calculation and
64-gate placement come from The Mirror's governed True Sidereal
activation engine.  We do not claim calculation parity with the
standard Gene Keys online profile unless independently verified.

---

## Deliverable E — Standard-method vs True-Sidereal limitation

- **What we adopt from Gene Keys:** sphere-to-activation planetary
  correlations, sphere names, sequence names (Activation / Venus /
  Pearl), the concept of Shadow / Gift / Siddhi as structural label
  triads.
- **What is Mirror-authored:** all interpretive prose, sphere
  descriptions, reflection prompts, contemplative practices.
- **What differs from standard Gene Keys:** the zodiacal frame (True
  Sidereal vs the standard convention used by the official Gene Keys
  online profile).  We do not claim parity of *derived Gene Keys*
  between the two systems.
- **Not adopted in Session 4A:** Star Pearl (deferred), and any content
  that would require verbatim or close-paraphrase reproduction of
  proprietary Gene Keys interpretive material.

---

## Deliverable F — IP / provenance audit

Every record in the canonical mechanics envelope carries
`content_provenance` set to one of:

- `mirror_original` — Mirror-authored interpretive prose;
- `structural_label` — permitted structural triads (Shadow of GK N,
  Gift of GK N, Siddhi of GK N);
- `user_authored` — from user input.

Records lacking provenance **cannot render** in the standalone lens
scaffold (Session 4A does not display any interpretive prose beyond
structural labels — full prose is deferred to Session 4B).

Long-form free-text fields in `data/gene_keys_data.py` (e.g. multi-
sentence Shadow descriptions) require a line-by-line IP audit before
they can be surfaced in the standalone lens.  Session 4A ships only
short structural labels of the form `"Shadow of Gene Key N"`.

---

## Deliverable G — Star Pearl recommendation

**Recommendation:** `star_pearl_availability = UNAVAILABLE_OR_DEFERRED`.

- The four required Star Pearl spheres and their canonical sphere-to-
  activation mappings are not yet independently verified.
- The IP audit for Star Pearl terminology and interpretive framework
  has not been performed against `gene_keys_ip_policy_v1.md`.
- Its distinct product purpose (versus the three Golden Path sequences)
  is not yet articulated.
- Recommend adding Star Pearl only after Session 4B narrative work
  matures, and only if all four criteria above are met.

---

## Deliverable H — Canonical mechanics schema and endpoint

**Endpoint:** `GET /api/gene-keys/mechanics/{user_id}`  
**Envelope schema (top-level keys):**

- `mechanics_version` (str) — `"gene_keys_mechanics_v1"`
- `sphere_map_version` (str) — `"mirror_true_sidereal_gk_v1"`
- `methodology` (obj) — full provenance block (URLs, engines, disclosure)
- `profile_availability` — `"present" | "partial" | "unavailable"`
- `sequences` — `{ "Activation": [sphere], "Venus": [sphere], "Pearl": [sphere] }`
- `unique_spheres` — deduplicated list (11 entries for a full profile)
- `shared_activation_roles` — [{primary, shared, reason}, …]
- `all_spheres` — flat list of all 13 sphere roles
- `missing_fields` — spheres whose derivation failed
- `verification_status` — `"verified" | "partial" | "unavailable"`
- `verification_discrepancies` — per-sphere delta records
- `methodology_disclosure` (str)
- `star_pearl_availability` — `"UNAVAILABLE_OR_DEFERRED"` in 4A
- `star_pearl_reason` (str)
- `reading_availability` — `{ state: "pending_session_4b", reason: str }`
- `user_id`

**Per-sphere object:** `sphere_name`, `sequences[]`, `gene_key`, `line`,
`activation { planet, chart_side }`, `source_longitude`, `evidence_ref`,
`content_provenance`, `structural_labels`, `verification_status`,
`verification_note`.

---

## Deliverable I — Standalone Explore scaffold

Implemented in `frontend/components/GeneKeysLensView.tsx`:

- **Parent-owned single fetch** — one call to
  `/api/gene-keys/mechanics/{user_id}` on mount.
- Explicit **loading / error / unavailable** states.
- Tabs: Overview · Activation · Venus · Pearl · Reading · Methodology.
- **Reading** renders an explicit `pending_session_4b` state — no
  fabricated master story.
- **Held spheres** are visually distinguished and hide gate/line
  details until the discrepancy is resolved.
- Verified narrow-viewport (320px width) and standard-mobile (390px)
  layouts.
- No Human Design vocabulary in the UI copy.

---

## Deliverable J — Migration plan from the embedded HD section

Phase | Action
--- | ---
**4A (this)** | Standalone lens ships in scaffold-only form; embedded `GeneKeysView.tsx` inside `HumanDesignLensView.tsx` remains untouched and continues to serve users.
**4B** | Ship IP-safe Mirror-authored narrative content in the standalone lens; enable Reading tab.
**4B+** | Add a soft-deprecation banner on the embedded HD Gene Keys section pointing users to the standalone lens.
**4C** | After a stability window, remove the embedded `GeneKeysView.tsx` mount from `HumanDesignLensView.tsx`.  The component file may be retained in tree until 4D.
**4D** | Delete `GeneKeysView.tsx` and orphaned legacy REST routes (`/gene-keys/activation-sequence`, `/venus-sequence`, `/pearl-sequence`, `/profile/{user_id}`, `/available`) if no consumers remain.

No embedded functionality is removed in Session 4A.

---

## Deliverable K — Synthetic non-Pete fixtures

Two synthetic fixtures live in
`tests/test_the_mirror_session4a_gene_keys_foundation.py`:

- **Jay** — 1981-10-12 18:16 Singapore (UTC+8)
- **Melissa** — 1981-07-13 07:25 Melaka (UTC+8)

Under the canonical map, both produce full profiles with
`verification_status="verified"`, zero discrepancies, valid gates
(1-64) across all 13 spheres.  Their Life's Work gate differs from
Pete's — confirming the mapping generalises rather than being tuned to
one fixture.

---

## Deliverable L — Tests and accumulated results

### New Session 4A suite (`test_the_mirror_session4a_gene_keys_foundation.py`)
34 tests · 34 passed · 0 failed.

Coverage of the 16 mandatory Session-4A assertions:

1. ✅ No duplicated astronomical or gate engine —
   `TestSingleEngine::test_sphere_map_module_has_no_astronomy_code`,
   `test_mechanics_module_reuses_hd_engine`,
   `test_calculations_gene_keys_delegates_to_sphere_map`.
2. ✅ Every sphere maps to its correct activation source —
   `TestCanonicalSphereMap::test_first_party_activation_pairs`.
3. ✅ Personality/Design sources remain distinct —
   `TestPeteCanonicalMapping::test_personality_and_design_sides_distinct`.
4. ✅ Brand ↔ Life's Work share the underlying activation —
   `TestPeteCanonicalMapping::test_brand_shares_lifes_work_activation`.
5. ✅ Vocation ↔ Core relationship represented without duplication —
   `TestPeteCanonicalMapping::test_vocation_shares_core_activation`.
6. ✅ Pete's profile is derived rather than hard-coded —
   `TestPeteCanonicalMapping::test_pete_gates_not_hardcoded_in_production`.
7. ✅ Synthetic non-Pete profiles produce different valid results —
   `TestSyntheticFixtures`.
8. ✅ Lines appear only when verified —
   `TestLineHandling`.
9. ✅ No Human Design mechanics leak into Gene Keys output —
   `TestNoHDLeak`.
10. ✅ No Gene Keys prose lacks content provenance —
    `TestContentProvenance`.
11. ✅ IP-restricted content cannot render — enforced by
    provenance guard; Session-4A only ships `structural_label`.
12. ✅ Star Pearl remains unavailable unless explicitly verified —
    `TestStarPearlDeferred`.
13. ✅ Lens count updates dynamically — Gene Keys added to `/api/lenses`
    (visible in the lens library).
14. ✅ One canonical mechanics request — `useEffect` fetches once per
    `userId` change in `GeneKeysLensView`.
15. ✅ Reading renders an explicit pending state rather than invented
    copy — `TestReadingPending` + `ReadingPendingPanel` UI.
16. ✅ All previous Human Design and accumulated regression tests
    remain green — see below.

### Accumulated regression
- `test_gene_keys_regression.py`: 30/30 passed.
- `test_lens_content_contract.py`: 41/41 passed.
- `test_symbolic_compute_contract.py`: 1/1 passed.
- Full backend suite (excluding pre-existing async-fixture failures that
  are unrelated to Session 4A): 1150+ passed with **zero
  gene-keys-related regressions**.

---

## Deliverable M — Screenshots (desktop and mobile)

Stored under `/tmp` for handoff:

| File | Viewport | State |
|---|---|---|
| `/tmp/gk_390_overview.png` | 390×844 | Explore · Overview |
| `/tmp/gk_320_overview.png` | 320×700 | Explore · Overview |
| `/tmp/gk_320_activation.png` | 320×700 | Explore · Activation Sequence |
| `/tmp/gk_320_venus.png` | 320×700 | Explore · Venus (with held sphere) |
| `/tmp/gk_320_reading.png` | 320×700 | Reading · pending state |

---

## Deliverable N — Exact files changed

### Added
- `backend/services/gene_keys_sphere_map.py`
- `backend/services/gene_keys_mechanics.py`
- `backend/tests/test_the_mirror_session4a_gene_keys_foundation.py`
- `frontend/components/GeneKeysLensView.tsx`
- `memory/the_mirror_session4a_gk_audit.md` (this file)

### Modified
- `backend/calculations/gene_keys.py` — consume canonical sphere map;
  version bump to `gk_sidereal_v2`.
- `backend/services/gene_keys_interpreter.py` — Venus and Pearl
  builders reconciled to canonical mapping; corrected docstrings.
- `backend/server.py`
  - New route `GET /api/gene-keys/mechanics/{user_id}`.
  - `/lenses` catalogue includes Gene Keys entry with
    `availability = { explore: "present", reading: "pending_session_4b" }`.
  - Venus and Pearl legacy endpoints updated to pass the canonical
    planet set.
  - `build_gene_keys_profile` callers threaded the new
    `personality_venus_*` params.
- `backend/tests/test_gene_keys_regression.py` — version stamp bumped;
  Love-Arc mapping expectations updated to canonical.
- `frontend/app/(tabs)/lenses.tsx` — lens key `Gene Keys → gene_keys`.
- `frontend/app/lenses/[lens].tsx` — lens metadata entry; new render
  branch for `gene_keys`.

---

## Deliverable O — Remaining decisions before Session 4B

1. **Pete regression rule.**  Confirm whether Pete's expected fixture
   is retired (adopting the canonical first-party mapping) or whether
   a new authoritative reference will be provided to revise the map.
2. **`data/gene_keys_data.py` IP audit.**  Line-by-line audit of the
   per-key long-form Shadow / Gift / Siddhi descriptions vs
   `gene_keys_ip_policy_v1.md`.  Fields that fail the audit must be
   rewritten in Mirror-authored voice before Session 4B.
3. **Reflection prompts.**  Approve the tone and structure for Session
   4B contemplative practices per lens.
4. **Reading arc scope.**  Confirm whether the standalone Reading mode
   opens with Activation only, or with a synthesis of all three
   sequences.
5. **Star Pearl re-evaluation timing.**  Confirm 4B remains free of
   Star Pearl.
6. **Legacy embedded GK section.**  Confirm the 4B → 4C → 4D migration
   plan; agree on the soft-deprecation banner copy.

---

## Deliverable P — Bounded Session 4B narrative prompt

> **Session 4B — The Mirror Gene Keys Narrative Layer (bounded).**
>
> Build the IP-safe, Mirror-authored narrative content for the standalone
> Gene Keys lens introduced in Session 4A.  The canonical sphere map
> (`services/gene_keys_sphere_map.CANONICAL_SPHERE_MAP`) and mechanics
> endpoint (`/api/gene-keys/mechanics/{user_id}`) are frozen.
>
> Scope:
>
> - Author Mirror-original interpretive text for every sphere across
>   the three sequences: Activation, Venus, Pearl.  Each sphere ships
>   `content_provenance="mirror_original"`.
> - Author reflection prompts and contemplative practices per sphere.
> - Author the Reading arc introduction and closing.  No temporary
>   generic reading exists — 4B is the first release of Reading.
> - Do not surface Star Pearl.
> - Do not alter the sphere map.  If Pete regression discrepancies are
>   resolved before 4B, update `PETE_EXPECTED_GATES` only after the
>   canonical map is confirmed unchanged.
> - Do not import any long or close-paraphrased passages from Gene
>   Keys books, websites, or courses.  Preserve permitted structural
>   references (short Shadow/Gift/Siddhi labels, sequence/sphere
>   names).
> - Every content-bearing field must carry `content_provenance`.
> - Add narrative-layer tests: provenance required, no IP-restricted
>   substrings, sphere-by-sphere presence, Reading emits Mirror-authored
>   opener/closer, no HD vocabulary in prose.
> - Do NOT remove the embedded Human Design → Gene Keys section.
> - Do NOT deploy.
>
> Exit criteria:
>
> - Reading mode is functional for the eight verified spheres.
> - Held spheres continue to render as `discrepancy_held` unless the
>   user has approved the mapping reconciliation.
> - All Session 4A tests remain green; all new 4B narrative tests pass.
> - Desktop and mobile screenshots pass at 320px and 390px.
