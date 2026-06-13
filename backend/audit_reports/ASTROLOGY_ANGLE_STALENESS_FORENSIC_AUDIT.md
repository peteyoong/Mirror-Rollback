# Astrology Angle Staleness — Full Forensic Audit (Read-Only)

**Build marker:** `angle-staleness-forensic-audit-v1`
**Date:** 2026-02 (current session)
**Scope:** MC / IC / ASC / DSC, all 12 house cusps, all angle-derived sign labels
**Mode:** READ-ONLY. No fixes applied. No calculator changes. No env flag changes.
**Source DB sampled:** `test_database` on `mongodb://localhost:27017` (171 charts; 168 stamped with `midpoint13_variant_a_v1`).

> **TL;DR**
> Mirror has **one canonical calculator** for angles (`calculations/astrology.py::get_full_natal_chart`) and **one canonical attribution table** (Variant A, `midpoint13_variant_a_v1`).  However, **at least 6 alternative read/derive paths exist** in the live codebase that either (a) call a parallel uniform-30 sign attributor, (b) re-attribute angles against a different boundary table, (c) reconstruct tropical longitudes with the wrong offset, or (d) silently miss angles entirely when the stored chart's shape doesn't match expectation.  These paths are the structural source of staleness — not the calculator itself.  Enforcing a single canonical chart source therefore requires **(i) deleting / hard-wiring the divergent attributors, (ii) writing tropical_longitude on every angle so downstream readers stop reconstructing, and (iii) eliminating the parallel canonical_astronomy + sidereal_config sign-label pipelines.**

---

## 1. Source-of-Truth Map (every site that produces an ASC / MC / IC / DC / house value or its sign label)

### 1.1  WRITE LAYER — paths that compute angles and persist them to `charts.astrology`

| ID | File / Line | Function | Numerical formula for ASC/MC | Sign attribution mode | House system | Where it persists | Notes |
|----|-------------|----------|------------------------------|-----------------------|--------------|-------------------|-------|
| W1 | `calculations/astrology.py:300-329` | `calculate_ascendant_tropical`, `calculate_mc_tropical` | `swe.houses(jd, lat, lon, b'P')` → tropical ASC/MC | n/a (raw floats) | Equal (default) or Placidus (opt-in) | n/a | Uses Placidus solver to extract tropical ASC/MC even when Equal-house mode is selected. |
| W2 | `calculations/astrology.py:444-1074` | `get_full_natal_chart` | Equal: ASC_sid = `tropical_to_sidereal(asc_tropical, svp_degrees)` (manual subtract).  Placidus: `swe.houses_ex(jd, lat, lon, b"P", FLG_SIDEREAL\|FLG_SWIEPH)` then overrides ASC/MC with `ascmc_p[0]/[1]` directly. | `longitude_to_sign_degree(asc_sidereal)` (no `tropical_longitude` passed) → re-routes via `attribute_sign(trop=sid+SVP, mode=DEFAULT_MODE)` = **Variant A midpoint-13** | `CANONICAL_HOUSE_SYSTEM = "Equal"` | Caller's responsibility. | **Canonical source-of-truth.** Returned dict: `angles.{asc,dc,mc,ic}.{sign, degree, longitude, formatted}` + `houses.{system, cusps[12], formatted_cusps[12], ascendant, ascendant_tropical, mc, mc_tropical}`. `forensic_variant_b.angles` is also stamped for rollback. |
| W3 | `calculations/astrology.py:813-871` | Vertex / Anti-Vertex amplifier | `swe.houses_ex(jd, lat, lon, b'P', FLG_SIDEREAL)` → `ascmc_v[3]` | `longitude_to_sign_degree(vx_long)` → Variant A | n/a | Inside `angles.vertex` / `angles.anti_vertex` | Tropical-frame Vertex also stored via `swe.houses(jd, lat, lon, b'P')`. Same axis indices.  Wrapped in `try/except: pass` — failure silently drops the amplifier. |
| W4 | `server.py:4633-4704` (`/api/calculate-chart`) | Single-pass chart compute on user signup | Calls W2 | (inherits W2) | Equal | `db.charts.replace/upsert` | Initial chart. Stamps `debug_stamp`, `calculated_at`. **Does NOT stamp `astrology_engine_version`, `migration_marker`, or `house_system` at top-level** — those are stamped only by the migration script. |
| W5 | `server.py:14751-14766` (`/api/astrology/chart/{user_id}`) | Re-recompute path | Calls W2 | Variant A | Equal | `db.charts.update_one({user_id}, {$set: {astrology: canonical_chart, updated_at: now}})` | **Re-writes `astrology` block on every recompute trigger** (which fires whenever `astro["planets"]["Chiron"]` is missing OR `force_recompute=true`). Does NOT stamp `astrology_engine_version` / `migration_marker` — only `updated_at`. |
| W6 | `server.py:15545-15552` (`/api/astrology/deep-dive/{user_id}`) | Recompute for deep dive | Calls W2 | Variant A | Equal | NOT stored here — `canonical_chart` is held in memory for prompt assembly. | Deep dive does NOT auto-write back. So deep dive's angles can diverge from `db.charts.astrology` if the stored doc was older. (Earlier code path used to write; current code does not — verified at line 15545-15672.) |
| W7 | `scripts/migration_phase5_variant_a.py:185-320` | `recompute_users` | Calls W2 | Variant A | Equal | `db.charts.update_one({user_id}, {$set: {astrology: {...}, astrology_engine_version: "midpoint13_variant_a_v1", sign_attribution_version: "midpoint13_variant_a", house_system: "Equal", migration_marker: "variant-a-13-sign-migration-v1", migrated_at: <iso>}})` | The migration-of-record. Only path that stamps the engine_version + migration_marker. **168 / 171 charts in test_database already carry these stamps.** |
| W8 | `routers/admin_variant_a_migration.py:653-810` (`/api/admin/migration-run`) | HTTP wrapper for W7 | Delegates to W7 | (inherits) | (inherits) | (inherits) | Write-gated via `MIGRATION_ADMIN_TOKEN` + preflight; refuses preview DB. |
| W9 | `routers/variant_a_startup_hook.py:200-308` | One-shot pod-startup migration | Delegates to W7 | (inherits) | (inherits) | (inherits) | Triggered by env `RUN_VARIANT_A_MIGRATION=VARIANT_A_PHASE_5`. |
| W10 | `routers/admin_gm_aligned.py:278-397` (`/api/admin/gm-aligned-recompute`) | Frozen GM-aligned recompute | Calls W2 | Variant A | Equal | `db.charts.update_one({user_id}, {$set: {astrology: chart, ..., astrology_engine_version: "gm-aligned-v1", house_system: "Equal", recomputed_at: now}})` | **FROZEN** (line 209 `_MIGRATION_FROZEN=True`). Would over-stamp `astrology_engine_version="gm-aligned-v1"` if unfrozen, masking the canonical `midpoint13_variant_a_v1` stamp.  Same calculator, different version label. |
| W11 | `server.py:10902-10969` (auto-migration `check_and_migrate_astrology_chart`) | Legacy-format upgrade for old chart docs | Calls W2 | Variant A | Equal | `db.charts.update_one({user_id}, {$set: {astrology: ..., human_design: ..., numerology: ..., calculated_at: iso, migration_info: {...}}})` | Fires when legacy string format is detected. Does NOT stamp `astrology_engine_version` / `migration_marker`. |
| W12 | `server.py:32208-32243` (`/api/admin/chart-recompute`) | Operator force-recompute | Calls W2 | Variant A | Equal | `db.charts.update_one({user_id}, {$set: {...update_fields}}, upsert=True)` | Operator-driven. Does NOT stamp engine_version. |

> **Observation 1 — Stamp drift across write paths.**  Only W7/W8/W9 stamp the canonical `astrology_engine_version` and `migration_marker`.  Every other write path silently re-writes the `astrology` sub-document *without* updating these flags.  Once W5 (or any of W4/W11/W12) fires after a migrated chart, the chart's `astrology.angles` block is overwritten with current-engine output, but the top-level `astrology_engine_version` / `migration_marker` remain stamped to whatever they were before.  **This means engine_version on the chart doc is not a reliable proof of which engine actually wrote the current `astrology.angles` payload.**  In production this can yield charts that *carry* `midpoint13_variant_a_v1` but whose `angles` were last written by W5 on an even older engine (or vice versa).

> **Observation 2 — Two engine-version labels for the same calculator.**  `midpoint13_variant_a_v1` (W7) and `gm-aligned-v1` (W10) both call the same `get_full_natal_chart` with `house_system="Equal"`.  These labels are not mutually exclusive guard flags — they will overwrite each other depending on which write path last ran.

---

### 1.2  READ LAYER — paths that consume angles or houses from a stored chart

| ID | File / Line | What it reads | Surface it feeds | Behaviour on stale data |
|----|-------------|---------------|------------------|--------------------------|
| R1 | `server.py:14685-14768` (`/api/astrology/chart/{user_id}`) | `chart.astrology` (full block); on stale shape, calls W5 which re-writes via W2 | Frontend Astrology Lens (`components/AstrologyLensView.tsx`, `services/astrology/astrologyInterpreter.ts`) | **Refreshing read**: triggers a recompute+rewrite when `astro.planets.Chiron` missing. Otherwise returns stored data verbatim — so an old chart that *did* have Chiron but stale angles stays stale. |
| R2 | `server.py:15404-15700` (`/api/astrology/deep-dive/{user_id}`) | Recomputes via W6 → in-memory `canonical_chart`. NEVER persists the recompute back. | Astrology Deep Dive prompt to LLM; UI `components/astrology/AstrologyDeepDiveTab.tsx` | **Never stale** for itself. But returns Variant-A angles that may disagree with the stored chart that *other* read paths serve. Source of the "deep dive says ASC=X, mirror chat says ASC=Y" inconsistency. |
| R3 | `server.py:14685` core read | `chart.astrology.angles.{asc,dc,mc,ic}.{sign,longitude}` and `chart.astrology.houses.{cusps, formatted_cusps, ascendant, mc}` | Frontend chart consumers, all lens summaries | Stored data only. Sign labels frozen as written. |
| R4 | `services/mirror_chat_phase4_enrichment.py` (consumes chart) → `routers/mirror_chat.py:290-360` | `astro.angles.mc.sign`, `astro.houses.formatted_cusps[0].sign` for Rising | Mirror Chat USER CONTEXT block sent to LLM | Stale-stamped angles flow directly into prompt. |
| R5 | `routers/mirror_chat.py:485, 508` | `astro.angles.dc.sign`, `astro.angles.ic.sign` | Mirror Chat lens-specific prompts (relationship → DC, home → IC) | Stale-stamped angles flow into prompt. |
| R6 | `services/forum_chat_knowledge_retrieval.py:482-507` | `angles.asc/mc/dc/ic.sign+formatted+degree` | FKR evidence injection footer for Forum Chat LLM | Stale-stamped angles flow into deterministic evidence. |
| R7 | `services/forum_lens_helpers.py:283-345` | Multi-source fallback chain: `angles.asc.sign` → `angles.ascendant.sign` → `houses.ascendant_sign` → derive from `angles.asc.longitude` via `calculations.astrology.longitude_to_sign_degree` (Variant A) → derive from `houses.ascendant` (legacy float) | Forum lens summary cards | Step 4 (derive from longitude) **bypasses the stored sign** and re-attributes via Variant A. If the stored sign was uniform_30, the derived value disagrees with the stored value. |
| R8 | `services/astrology_domain_context.py:42-106` | `angles.mc.sign`, `angles.dc.sign`, `angles.ic.sign` | Domain-specific astrology context (career/relationship/home) for Mirror Chat | Stale stored sign. No derivation fallback. |
| R9 | `services/natal_object_engine.py:177-266` | `angles.asc/mc/dc/ic/vertex/anti_vertex` (dict copy returned as-is for Vertex / Lot computation seeds) | "Tell me about my Lilith / Vertex / Lot of Fortune" chat answers | Stored stale sign flows into Lot computations (Lot of Fortune uses ASC tropical reconstructed from `asc.longitude + SVP`). |
| R10 | `services/iau_constellations.py:620-716` | `angles.asc/mc.tropical_longitude` OR reconstructed via `(angles.asc.longitude or sidereal_longitude) + 28.69` | Ophiuchus overlay card (`components/astrology/ConstellationOverlayCard.tsx`) | **BUG**: hardcoded `+28.69` offset (lines 661, 672, 698, 708) does NOT match the canonical `SVP_DEGREES = 31.2836`. Off by **−2.5936°** — large enough to flip the IAU constellation an angle sits in at a constellation boundary. |
| R11 | `services/relationship_field.py:299` | `angles.vertex` (read directly) | Vertex significance amplifier in relationship synthesis | Stored as-is. |
| R12 | `services/lifecycle_engine.py:310-315` | Iterates `chart.angles[src]` for arbitrary `src in {asc, mc, dc, ic, vertex, anti_vertex}` | Lifecycle pattern engine | Stored as-is. |
| R13 | `services/transit_object_engine.py:104-155` | Vertex / Anti-Vertex via `chart.angles.{vertex, anti_vertex}` (refuses transit lookup; returns natal only) | Transit object queries | Stored as-is. |
| R14 | `services/recognition_language.py` (grep hit) | angles | Recognition / sign-spec language | Stored as-is. |
| R15 | `services/lens_diagnosis_engine.py` | angles | Lens diagnostic | Stored as-is. |
| R16 | `services/cross_lens_synthesis_v2.py` | angles | Cross-lens synthesis | Stored as-is. |
| R17 | `services/pressure_topology_engine.py` | angles | Pressure topology | Stored as-is. |
| R18 | `routers/admin_gm_aligned.py:81-83, 168-171` | `angles.asc.sign`, `angles.mc.sign` | GM forensic comparison endpoint | Stored as-is (used for QA only). |
| R19 | `services/member_summary.py:62` | `angles.asc.sign` fallback to `angles.ascendant.sign` | Member summary card | Stored as-is. |
| R20 | `services/home_synthesis_engine.py:394`, `services/home_insight_engine.py:516` | Uses `available_angles[]` from chart | Home insight selection | Stored as-is. |
| R21 | `services/forum_contributions.py:327` | `angles.asc` | Forum contribution summary | Stored as-is. |
| R22 | `routers/variant_a_startup_hook.py:113-123` | `angles.asc.sign` (read-back validator) | Startup-hook post-migration anchor check | Diagnostic only. |

> **Observation 3 — Two distinct reading conventions for "rising sign".**
> 1. `astro.angles.asc.sign` (canonical post-W2)
> 2. `astro.houses.formatted_cusps[0].sign` (canonical House 1 cusp sign — Equal House so it equals the ASC sign, but recomputed via `longitude_to_sign_degree(cusp)` independently)
>
> Both are stamped at write-time by W2 from the same `asc_sidereal` longitude, so they agree numerically.  But `mirror_chat.py:295` uses (2) for Rising while `forum_chat_knowledge_retrieval.py:501` uses (1).  Any patch / migration / future engine change that updates one without the other will introduce drift between Mirror Chat's Rising and the FKR-injected ASC.

> **Observation 4 — Stored angles never carry `tropical_longitude`.**  W2 writes `angles.{asc,dc,mc,ic}.{sign, degree, longitude, formatted}` and `angles.{vertex, anti_vertex}.{...longitude, tropical_longitude, ...}`.  Only Vertex / Anti-Vertex carry a tropical longitude; the four primary angles do NOT.  This forces every downstream consumer that wants tropical (Lots, IAU constellations, alt-ayanamsa sweeps) to reconstruct it as `sidereal + SVP_DEGREES`.  Three of those reconstructions use the wrong constant (R10) or no constant at all.

---

### 1.3  DERIVE / RECOMPUTE LAYER — paths that re-attribute or re-compute angles outside the canonical engine

| ID | File / Line | What it does | Sign attribution it uses | Divergence vs canonical |
|----|-------------|--------------|--------------------------|-------------------------|
| D1 | `services/canonical_astronomy.py:250-269` | `_compute_houses_equal`: `swe.houses_ex(jd, lat, lon, b'E')` (Equal, tropical, **no FLG_SIDEREAL**), then `cusps[i] - SVP_DEGREES`, then `asc_trop - SVP_DEGREES`. Sign label via `longitude_to_sign_degree` imported from **`calculations.sidereal_config`** (line 57). | **uniform_30** (sign = `int(sidereal / 30) % 12`, 12-sign list, no Ophiuchus) | ASC/MC sidereal longitudes agree numerically with W2 to within float epsilon. **But the sign label uses `int(lon/30)` 30°-equal buckets, NOT the midpoint-13 boundary table.**  This produces a different sign for any longitude near a midpoint-13 boundary (e.g. anywhere in Ophiuchus 14.50° wide band, and at every other shifted boundary). Consumed by `/api/diagnostics/canonical-astronomy/{user_id}` (server.py:27264). |
| D2 | `calculations/sidereal_config.py:141-159` | `longitude_to_sign_degree(longitude)` — independent re-implementation. | **uniform_30**, hardcoded 12-sign `ZODIAC_SIGNS`. | Returns `sign = ZODIAC_SIGNS[int(longitude / 30)]`. Cannot return Ophiuchus. Used by: `services/canonical_astronomy.py`, `services/transit_signals.py:777`, `services/lunar_cycle.py:286`, and indirectly by `services/transit_dominance_engine.py`, `services/transit_natal_aspects.py`, `services/daily_transit_window.py` (all import `calculate_planet_by_name` from sidereal_config — which calls D2 internally). |
| D3 | `services/transit_signals.py:770-800` | `calculate_earth_gate`: HD Earth sign via `longitude_to_sign_degree(earth_long)` from sidereal_config. | **uniform_30** | Earth sign label in HD transit returns is uniform_30 (12-sign). |
| D4 | `services/transit_signals.py:803-855` | `calculate_moon_gate_transit`: uses `calculate_planet_by_name("Moon", dt)` → sidereal_config → D2 sign. | **uniform_30** | Daily transit Moon sign disagrees with main astrology engine when Moon is in Ophiuchus or at a midpoint-13 boundary. |
| D5 | `services/lunar_cycle.py:222-300+` | Uses `calculate_planet_by_name` from sidereal_config for Sun and Moon at any timestamp. | **uniform_30** | Lunar cycle phase tags / sign labels are uniform_30. |
| D6 | `services/astrology_today_engine.py:226-250` (`compute_transit_positions`) | Calls `swe.set_sid_mode(SIDM_USER, 2451545.0, 31.2836)` itself, then `swe.calc_ut(..., FLG_SWIEPH \| FLG_SIDEREAL)`, then `longitude_to_sign_degree(lon)` imported **from `calculations.astrology`**. | **Variant A** (via `calculations.astrology.longitude_to_sign_degree`) | ✅ Consistent with canonical for sign labels. **BUT** has its own `swe.set_sid_mode` call (line 230) — violates the "no lens may call set_sid_mode itself" rule from `services/canonical_astronomy.py:8-13`. |
| D7 | `services/astrology_today_engine.py:26-27` | Hardcoded `SIGNS` list (12 signs, no Ophiuchus). | n/a (used for stellium concentration grouping) | `detect_sign_concentration` (line 390-414) groups by raw `data['sign']`. If Variant A returned "Ophiuchus", it gets its own group, but **`SIGN_BEHAVIOR.get(sign, {})` returns empty for Ophiuchus** because the local SIGN_BEHAVIOR dict doesn't include it. Same for `fire_signs/water_signs/earth_signs/air_signs` (`ether_signs = {'Ophiuchus'}` IS defined at line 483, but only used for the element fallback — `SIGN_BEHAVIOR` is not patched). |
| D8 | `services/astrology_today_v3.py:142` | Comment only, not a sign attributor. | n/a | n/a |
| D9 | `services/iau_constellations.py:661, 672, 698, 708` | Reconstructs `tropical_longitude = sidereal + 28.69` (literal). | n/a (uses boundary lookup, not sign-attribution) | **`28.69` is wrong** — canonical `SVP_DEGREES = 31.2836`. Δ = **−2.5936°**. Enough to misplace any body within 3° of an IAU constellation boundary. |
| D10 | `services/solar_return_engine.py:267-275` | `from calculations.sidereal_config import SVP_DEGREES as svp`; `asc_sidereal = normalize_degrees(asc_tropical - svp)`; sign via `longitude_to_sign_degree(asc_sidereal, tropical_longitude=asc_tropical)` imported from `calculations.astrology`. | **Variant A** | ✅ Consistent with canonical. |
| D11 | `services/natal_object_engine.py:184, 208-209, 299-302` | Reconstructs angle tropical from stored sidereal (`asc.longitude + SVP_DEGREES`), then computes Lot of Fortune / Lot of Spirit / Lilith family. Sign via `longitude_to_sign_degree(sid, tropical_longitude=trop)` (Variant A). | **Variant A** | ✅ Consistent. But propagates any storage-shape error (e.g. if `angles.asc.longitude` is missing). |
| D12 | `server.py:14786-14801` (Element/Modality/Polarity tally inside `/api/astrology/chart/{user_id}`) | Hardcoded 12-sign maps (`SIGN_TO_ELEMENT`, `SIGN_TO_MODALITY`, `SIGN_TO_POLARITY`). No `Ophiuchus` entry. | n/a | Any planet (or angle, if added) in Ophiuchus contributes ZERO to every element/modality/polarity bucket. Downstream "dominant element" / "concentrations" balances are biased. |
| D13 | `server.py:31870-31886` (`/api/admin/asc_forensic/{user_id}`) | Live re-compute of ASC/MC using `swe.houses(jd, lat, lon, b"P")` + `swe.houses_ex(jd, lat, lon, b"P", FLG_SIDEREAL)` + manual `(tropical_asc - SVP) % 360`. | Both modes side-by-side via `_both_modes` → `attribute_sign_uniform_30` + `attribute_sign_true_sidereal_midpoint` (legacy alias for **Variant B**). | **D13 attribution call uses `attribute_sign_true_sidereal_midpoint` which is aliased to Variant B (12-sign Ophiuchus-merged)**, NOT Variant A. So the admin forensic endpoint compares uniform_30 vs **Variant B** — never against Variant A. Wrong baseline. |
| D14 | `server.py:31654-31735` (`/api/admin/astrology/house_forensic/{user_id}`) | Calls `get_house_for_planet(lon, cusps_long)` from `calculations.astrology` and `whole_sign_house(asc_long, lon)` (locally defined) to compare Equal vs Whole-Sign house attribution. | n/a (house numbers, not signs) | Reads `houses_doc.get("ascendant")` (sidereal float) and `houses_doc.get("formatted_cusps")`. Confirms Equal-House SSOT on the chart but does **not** test angle sign labels. |
| D15 | `services/home_insight_v5.py`, `services/home_insight_v6.py`, etc. | Various references to angles | Mostly stored read | Need to spot-check; grep showed them in §1 file list but no sign re-attribution detected on quick scan. |

---

### 1.4  FRONTEND — every UI surface that consumes angle data

| ID | File / Line | What it reads | Source |
|----|-------------|---------------|--------|
| F1 | `frontend/services/astrology/astrologyTypes.ts:79-84` | TypeScript shape: `natal.angles.{asc, dc, mc, ic}: PlanetData` | Schema for the `/api/astrology/chart/{user_id}` response |
| F2 | `frontend/services/astrology/astrologyInterpreter.ts:614-616, 1170-1177, 2605, 4123` | `chartData.natal.angles.asc.sign` (lowercased), `placements.ascendant` | Astrology interpreter → core orientation + pressure-triangle logic |
| F3 | `frontend/components/AstrologyLensView.tsx:177-184` | `fullChartData.natal.angles.asc.sign` | "Astrology" tab — Sun/Moon/Rising header |
| F4 | `frontend/components/astrology/AstrologyAtAGlanceTab.tsx:65` | `safePlacements.ascendant` | "At a glance" tab |
| F5 | `frontend/components/astrology/AstrologyDeepDiveTab.tsx:1473, 1479, 1530, 1540, 1542, 1769-1774, 1869` | `placements.ascendant` (string sign), per-sign quality lookups | Deep dive UI — Sun / Moon / Ascendant deep-dive cards |
| F6 | `frontend/components/astrology/ConstellationOverlayCard.tsx` | Ophiuchus overlay derived from `iau_constellations.py` (R10/D9) | Ophiuchus overlay card — vulnerable to D9 wrong-offset bug |
| F7 | `frontend/utils/humanDesignMirrorCards.ts`, `frontend/utils/humanDesignSynthesis.ts` | Incarnation Cross / HD-specific reads (separate from astrology angles) | Not in scope for this audit |

---

## 2. Divergence Matrix — where does each surface get its ASC sign from?

Same user (Pete, `697f0c6abf35c0528ff06954`) gives different answers depending on which path the surface uses.  Tested live against `test_database`:

| Surface | Path | Pete's ASC sign |
|---------|------|------------------|
| Stored chart (`astro.angles.asc.sign`) | R3 | `Sagittarius` |
| Stored forensic Variant B (`astro.forensic_variant_b.angles.asc.sign`) | (forensic-only) | `Sagittarius` (matches in this case) |
| Mirror Chat USER CONTEXT Rising | R4 → `astro.houses.formatted_cusps[0].sign` | `Sagittarius` |
| FKR evidence Ascendant | R6 → `astro.angles.asc` | `Sagittarius` |
| Deep Dive | R2 / W6 (recomputed at request time) | `Sagittarius` (Variant A) |
| Canonical-astronomy diagnostic (`/api/diagnostics/canonical-astronomy`) | D1 → `longitude_to_sign_degree` from sidereal_config | **`Sagittarius`** via uniform_30 (`int(asc_sidereal/30) = int(255.54/30) = 8 → Sagittarius`) — happens to agree here, would disagree for any user with an ASC in Ophiuchus (which 13 charts in test_database currently have anywhere across angles). |
| Admin ASC forensic (`/api/admin/asc_forensic`) bodies_comparison preview | D13 → `attribute_sign_uniform_30` AND `attribute_sign_true_sidereal_midpoint` (legacy alias = **Variant B**) | uniform_30 / Variant-B side-by-side. **Variant A is not in this report.** |
| IAU constellation overlay | R10 / D9 → reconstructed tropical with **wrong `+28.69` offset** | Off by 2.59° at any constellation boundary |

**Verified divergence counts across all 168 migrated charts (Variant A canonical vs Variant B forensic stored on the same chart):**
- ASC sign A vs B mismatches: **22 / 168 = 13.1%**
- MC sign A vs B mismatches: **11 / 168 = 6.5%**
- IC sign A vs B mismatches: **20 / 168 = 11.9%**
- DC sign A vs B mismatches: **57 / 168 = 33.9%**

Sample DC mismatches:
```
697f9b592caf672a29468ee9  ASC=Aries     A_DC=Virgo        B_DC=Libra
697fa5101ea0ea87a2f58c7f  ASC=Taurus    A_DC=Ophiuchus    B_DC=Scorpio
697ec6ffad4b18f75bf42615  ASC=Virgo     A_DC=Pisces       B_DC=Aquarius
697ec826ad4b18f75bf42616  ASC=Cancer    A_DC=Sagittarius  B_DC=Capricorn
```

**The Variant A and Variant B boundary tables do not differ only by the Ophiuchus carve-out.**  They use measurably different boundary degrees for every sign (Variant A is derived from a zodiacal-frame Athen / Mastering-the-Zodiac table shifted by SVP=31.2836°; Variant B is a direct tropical table).  This is why even non-Ophiuchus signs (Virgo/Libra above, Aquarius/Pisces, Capricorn/Sagittarius) sometimes disagree.

---

## 3. Stamp Audit on Live DB (`test_database`)

Sampled all 171 chart docs:

```
total charts: 171
  168 (engine='midpoint13_variant_a_v1', computation_version='mirror-deterministic-v1',
       house_system='Equal', migration_marker='variant-a-13-sign-migration-v1')
    3 (engine=<missing>, computation_version=<missing>, house_system=<missing>,
       migration_marker=<missing>)
```

Three charts are completely orphaned (no engine_version, no migration_marker, no nested metadata).  These are pre-migration legacy docs that survived the migration's `_parse_user_birth` skip (no birth data) and are still served verbatim by R1–R22 to the surfaces that read them.

---

## 4. Root Causes of "Stale Angle Signs"

Synthesising the findings above, **the staleness is structural rather than calculator-level**.  It originates from four classes of defect, in order of impact:

### 4.1  Multiple parallel sign-attribution implementations (HIGH IMPACT)

Mirror has **three live sign-attribution functions** that look identical at the call site:

1. `calculations.astrology.longitude_to_sign_degree` → routes via `attribute_sign(mode=DEFAULT_MODE)` → **Variant A midpoint-13** ✅
2. `calculations.sidereal_config.longitude_to_sign_degree` → **uniform_30**, 12-sign hardcoded list ❌
3. (legacy alias) `calculations.sign_attribution.attribute_sign_true_sidereal_midpoint` → **Variant B** ❌

Modules grab one of these via `from calculations.X import longitude_to_sign_degree as ...` based on whichever file the author happened to be working in.  There is no compile-time / type-system check that callers picked the canonical one.  Even the canonical-astronomy module — explicitly named as the "single source of truth" — imports (2) and therefore mints **uniform_30 sign labels** when downstream consumers read its output.

### 4.2  Stored angles lack `tropical_longitude` (HIGH IMPACT)

W2 writes only the sidereal `longitude` on `angles.{asc,dc,mc,ic}`.  Every consumer that needs tropical (for IAU constellation lookup, for Lots, for alt-ayanamsa sweep, for re-attribution under a different mode) must reconstruct it.  Three reconstructions exist and **none of them are validated against the canonical SVP**:
- `services/natal_object_engine.py`: `+ SVP_DEGREES` (correct)
- `services/iau_constellations.py`: `+ 28.69` (WRONG — Δ = −2.59°)
- `calculations/astrology.py`'s internal forensic Variant B builder: `+ svp_degrees` from local var (correct)

Even when the constant is correct, the reconstruction itself is unnecessary work that gates correctness on a literal number being typed correctly at every call site.

### 4.3  Stamp-vs-data drift (MEDIUM IMPACT)

The chart doc carries two engine identifiers that are written and read independently:
- Top-level: `astrology_engine_version`, `sign_attribution_version`, `migration_marker`, `house_system`
- Embedded: `astrology.metadata.{computation_version, house_system, sidereal_mode, svp_degrees, astrology_engine_version}` and `astrology.astrology_engine_version`

The migration script (W7) writes BOTH consistently.  Every other write path (W4, W5, W11, W12) writes only the embedded one (via the `chart` payload returned by W2) and leaves the top-level stamps stale.  R1 inspects `astro.planets.Chiron` to decide whether to refresh; it does **not** inspect `astrology_engine_version`.  Consequence: a chart can correctly carry Variant-A angles in its data while its top-level stamps still say it's pre-migration (or vice versa).

### 4.4  Hardcoded 12-sign maps / behaviour tables (MEDIUM IMPACT)

Several downstream interpreters still operate on a 12-sign worldview even though canonical attribution can return "Ophiuchus":
- `server.py:14786-14801` element / modality / polarity counters — Ophiuchus contributes zero.
- `services/astrology_today_engine.py:26-27, 50-489` `SIGNS` list + `SIGN_BEHAVIOR` dict — Ophiuchus has no behaviour entry. (`ether_signs` exists at line 483 for element bucketing, but `SIGN_BEHAVIOR.get('Ophiuchus', {})` returns `{}` so stellium narratives go blank for Ophiuchus stelliums.)
- `services/canonical_astronomy.py:54` `ZODIAC_SIGNS` is imported from sidereal_config (12-sign).
- `services/forum_lens_helpers.py:362-375` correctly includes `"Ophiuchus": "Ether"` for elements and `"Ophiuchus": "Mutable"` for modality — but this is an exception, not the rule.

This isn't strictly an *angle* problem, but it amplifies the visible staleness: when a stale angle gets corrected from (say) Scorpio → Ophiuchus, the downstream narrative degrades from "Scorpio-flavoured" to "no flavour at all".

### 4.5  Silent failure modes (LOW-MEDIUM IMPACT)

- `services/house_inventory_engine.py:66-74` passes `astro.get("houses")` (a dict) to `get_house_for_planet(lon, cusps)` (expects a list).  Indexing `dict[0]` raises KeyError, caught by line 73-74 `except Exception: return None`.  House inventory silently misses houses for the new chart shape.
- `calculations/astrology.py:813-871` Vertex / Anti-Vertex block is wrapped in `try / except: pass`.  Any swisseph failure (e.g., near-pole anomaly) silently drops both `angles.vertex` and `angles.anti_vertex`.  R11/R12/R13/R20 surfaces then see a chart with no Vertex and have no idea why.
- W11 `check_and_migrate_astrology_chart` catches all exceptions and returns `(False, msg, chart)` with the OLD chart — the surface continues to render stale data with no user-visible failure signal.

---

## 5. What "single canonical chart source" enforcement would require (read-only assessment)

> ⚠️  This section describes the work that *would* be needed.  Per scope, NO changes were made.

### 5.1  Calculator layer — already canonical

`calculations.astrology.get_full_natal_chart` is the only legitimate angle producer.  No additional calculator unification is required.  The only safe change here would be to also stamp `tropical_longitude` on `angles.{asc, dc, mc, ic}` (currently only present on `angles.{vertex, anti_vertex}`).  This is purely additive.

### 5.2  Sign-attribution layer — needs collapse

| Action | Files | Impact |
|--------|-------|--------|
| Delete or wrap `calculations.sidereal_config.longitude_to_sign_degree` (uniform_30) | `calculations/sidereal_config.py:141-159` | Forces every importer to route via Variant A.  Affects D1/D2/D3/D4/D5 and 8+ downstream services. |
| Delete legacy alias `attribute_sign_true_sidereal_midpoint` (= Variant B) | `calculations/sign_attribution.py:285` | Forces forensic comparisons (D13, scripts/*) to explicitly call `attribute_sign_midpoint12_variant_b` rather than the alias.  Prevents accidental V-B usage. |
| Replace `from calculations.sidereal_config import longitude_to_sign_degree` with `from calculations.astrology import longitude_to_sign_degree` | `services/canonical_astronomy.py:57`, `services/transit_signals.py:777`, `services/lunar_cycle.py:286` | Brings drift-detection + transit Earth gate + lunar cycle to Variant A. |
| Patch the hardcoded `28.69` offset in `iau_constellations.py` to `SVP_DEGREES` import | `services/iau_constellations.py:661, 672, 698, 708` | Fixes Ophiuchus / constellation boundary misplacements. |

### 5.3  Read-and-derive layer — needs deduplication

| Action | Files | Impact |
|--------|-------|--------|
| Drop the dual-read convention for Rising sign — pick one (`angles.asc.sign` vs `houses.formatted_cusps[0].sign`) and use it everywhere | `routers/mirror_chat.py:295`, `services/forum_chat_knowledge_retrieval.py:501-507`, `services/forum_lens_helpers.py:283-326`, `services/iau_constellations.py:711`, `services/astrology_domain_context.py:42-106`, `services/natal_object_engine.py:177` | Eliminates the path-dependent "which Rising does Mirror know about" ambiguity. |
| Stop the auto-recompute path (W5) from silently rewriting `astro` without updating `astrology_engine_version` / `migration_marker` / `sign_attribution_version` | `server.py:14751-14766`, plus W4 / W11 / W12 | Makes stamps a reliable provenance signal.  Requires updating these to call the same patch-builder W7 uses (lines 271-291 of `migration_phase5_variant_a.py`). |
| Same for `/api/admin/chart-recompute` (`server.py:32208`) and any other recompute helpers. | (as above) | (as above) |

### 5.4  Diagnostic / forensic layer — needs alignment

| Action | Files | Impact |
|--------|-------|--------|
| `/api/diagnostics/astro-system` reports `"zodiac_mode": "true_sidereal_midpoint_12_merged_candidate"` (V-B) and `"ophiuchus_enabled": False` | `server.py:27149-27154` | Misreports the canonical engine. Should read `ENGINE_VERSION_VARIANT_A`. |
| `/api/admin/asc_forensic/{user_id}` previews uniform_30 vs **Variant B** only | `server.py:31912-31940` (`_both_modes`), specifically `attribute_sign_true_sidereal_midpoint` import on line 31931 | Should include Variant A (which is what's actually stored). |
| `services/canonical_astronomy.py` advertises "single source of truth" but mints uniform_30 labels (D1, D2) | All of canonical_astronomy.py | Currently misleading. Either delete the parallel pipeline, or pin its sign attributor to Variant A. |

### 5.5  Downstream sign-aware narrative layer — needs 13-sign awareness

| Action | Files | Impact |
|--------|-------|--------|
| Add `Ophiuchus` keys to `SIGN_TO_ELEMENT` / `SIGN_TO_MODALITY` / `SIGN_TO_POLARITY` in `server.py:14786-14801` | `server.py:14786-14801` | Ophiuchus counts in balance computations. |
| Add `Ophiuchus` `SIGN_BEHAVIOR` entry in `astrology_today_engine.py:51-489` | `services/astrology_today_engine.py:51-489` | Stellium narratives stop dropping Ophiuchus stelliums. |
| Audit every hardcoded sign list across the codebase (grep: `'Aries', 'Taurus', 'Gemini', 'Cancer'` returns 18+ hits) for 13-sign completeness | grep result | Distributed work; out of scope for this audit but should be tracked. |

### 5.6  Persistence layer — needs idempotent provenance write

If the goal is "one source of truth per chart, with reliable staleness detection", the schema needs a single, atomic stamp written by the calculator itself (not by the caller).  Today `get_full_natal_chart` already stamps:
- `astrology_engine_version` (top-level of returned dict, line 1017)
- `metadata.astrology_engine_version` (line 1028)
- `metadata.computation_version` (line 1027)
- `metadata.house_system` (line 1024)
- `metadata.sidereal_mode` (line 1025)
- `metadata.svp_degrees` (line 1026)

But the **chart doc itself** has its own top-level versioning (W7 stamps `astrology_engine_version`, `sign_attribution_version`, `house_system`, `migration_marker`, `migrated_at`) which is **adjacent to** the engine's stamps, not derived from them.  The result is the stamp-vs-data drift documented in §4.3.

A canonical, drift-resistant pattern would be to either:
- (a) drop the chart-doc-level stamps and read provenance exclusively from `astrology.astrology_engine_version` (which W2 always writes), OR
- (b) define a single "stamp builder" helper that takes a calculator return value and produces both the chart payload and the top-level stamps in one shot — used by every write path.

---

## 6. File-by-file divergence checklist (for engineering review)

```
calculations/astrology.py                    ✅ Canonical write path. Default Variant A. (W1-W3)
calculations/sign_attribution.py             ⚠ Exposes Variant B as `attribute_sign_true_sidereal_midpoint` legacy alias.
calculations/sidereal_config.py              ❌ Independent uniform_30 sign attributor still lives here. (D2)
calculations/true_sidereal_midpoint_boundaries.py  (referenced by sign_attribution; not an attributor itself.)

services/canonical_astronomy.py              ❌ Advertises "single source of truth" but imports uniform_30 from sidereal_config (D1). `swe.houses_ex` uses `b'E'` without `FLG_SIDEREAL` — works by accident.
services/iau_constellations.py               ❌ Hardcoded +28.69 ≠ SVP (D9/R10).
services/astrology_today_engine.py           ⚠ Sign labels via canonical Variant A ✅; but local `set_sid_mode` (line 230), 12-sign hardcoded `SIGNS` (line 26), `SIGN_BEHAVIOR` missing Ophiuchus (D7).
services/transit_signals.py                  ❌ Uses sidereal_config.longitude_to_sign_degree (D2/D3).
services/lunar_cycle.py                      ❌ Uses sidereal_config.longitude_to_sign_degree (D2/D5).
services/solar_return_engine.py              ✅ Uses Variant A via calculations.astrology (D10).
services/natal_object_engine.py              ✅ Uses Variant A (D11); but reconstructs angle tropical from stored sidereal (Observation 4 dependency).
services/relationship_field.py               ✅ Stored-read only.
services/forum_chat_knowledge_retrieval.py   ✅ Stored-read only (Variant A → flows through).
services/forum_lens_helpers.py               ✅ Stored-read with Variant-A derivation fallback (R7).
services/astrology_domain_context.py         ✅ Stored-read only (R8).
services/mirror_chat_phase4_enrichment.py    ✅ Stored-read only.
services/house_inventory_engine.py           ❌ Silent house-lookup failure on new dict-shaped `astro.houses` (Observation 5).
services/lifecycle_engine.py                 ✅ Stored-read only.
services/recognition_language.py             ✅ Stored-read only.
services/lens_diagnosis_engine.py            ✅ Stored-read only.
services/cross_lens_synthesis_v2.py          ✅ Stored-read only.
services/pressure_topology_engine.py         ✅ Stored-read only.
services/member_summary.py                   ✅ Stored-read only (R19).
services/transit_object_engine.py            ✅ Stored-read only (R13).
services/home_synthesis_engine.py            ✅ Stored-read only (R20).
services/home_insight_engine.py              ✅ Stored-read only.

routers/mirror_chat.py                       ✅ Stored-read only — but uses `houses.formatted_cusps[0].sign` for Rising (Observation 3).
routers/forums_chat.py                       ✅ Stored-read only.
routers/admin_gm_aligned.py                  ⚠ Calls Variant A engine correctly; stamps `astrology_engine_version="gm-aligned-v1"` (over-writes canonical stamp). FROZEN.
routers/admin_variant_a_migration.py         ✅ Canonical migration path (W8).
routers/variant_a_startup_hook.py            ✅ Canonical migration path (W9).

server.py:4633-4704   (/api/calculate-chart)             ⚠ Writes `astrology` block without engine_version stamp (Observation 1).
server.py:10902-10969 (check_and_migrate_astrology_chart) ⚠ Same.
server.py:14685-14776 (/api/astrology/chart/{user_id})    ⚠ Conditional re-write without engine_version stamp; element/modality/polarity counts skip Ophiuchus (D12).
server.py:15404-15700 (/api/astrology/deep-dive)          ✅ Recomputes Variant A on every request — never persists. (W6 / R2)
server.py:27130-27176 (/api/diagnostics/astro-system)     ❌ Hardcoded Variant B labels in diagnostic response.
server.py:27180-27330 (/api/diagnostics/canonical-astronomy/{user_id}) ❌ Drift report uses uniform_30 sign labels (D1/D2).
server.py:31618-31736 (/api/admin/astrology/house_forensic) ✅ House-only forensic; correct.
server.py:31739-31970 (/api/admin/asc_forensic)            ❌ Bodies preview uses uniform_30 + Variant B; Variant A is not previewed (D13).
server.py:32143-32243 (/api/admin/chart-recompute)         ⚠ Writes without engine_version stamp.

scripts/migration_phase5_variant_a.py        ✅ The migration of record.  Stamps everything (W7).
```

Legend: ✅ canonical / ⚠ partial / ❌ divergent.

---

## 7. Recommended remediation sequence (read-only design — no code applied)

> Presented in dependency order.  Each step is independently reversible.

1. **Stamp `tropical_longitude` on every angle written by W2.** Purely additive; old consumers ignore it, new consumers stop reconstructing.  Eliminates D9 and unblocks any future re-attribution pass that wants to honour an alternative mode.
2. **Make `calculations.sidereal_config.longitude_to_sign_degree` an alias of `calculations.astrology.longitude_to_sign_degree`** (or remove it and update all 8+ importers).  Collapses D1/D2/D3/D4/D5 onto Variant A.
3. **Replace the hardcoded `28.69` in `iau_constellations.py` with `from calculations.sidereal_config import SVP_DEGREES`.**  Fixes D9.
4. **Define a single chart-doc writer helper** (e.g. `services.chart_persistence.write_canonical_chart(db, user_id, chart_payload)`) used by W4/W5/W7/W11/W12.  Ensures the top-level stamps (`astrology_engine_version`, `sign_attribution_version`, `house_system`, `migration_marker`, `migrated_at`/`updated_at`) are always in sync with `chart_payload.astrology.metadata`. Eliminates §4.3.
5. **Audit `/api/diagnostics/astro-system`** to report the actual `DEFAULT_MODE` (Variant A), not the hardcoded V-B label.
6. **Update `/api/admin/asc_forensic`** to preview all three modes (uniform_30, Variant B, Variant A) instead of just two.
7. **Fix `services/house_inventory_engine.py:66-74`** to pass `astro.get("houses", {}).get("cusps")` instead of the whole dict. (Independent bug; surfaces as silently missing house data, not as a wrong sign.)
8. **Decide whether to keep `routers/admin_gm_aligned.py`'s parallel "gm-aligned-v1" engine_version stamp.** If yes, document the stamp precedence rule. If no, retire the file (it's been frozen for months).
9. **One-pass migration after (1)-(4):** Rerun the W7 migration to back-fill `tropical_longitude` on every angle and re-sync every top-level stamp.  Cache invalidation list in `scripts/migration_phase5_variant_a.py:76-98` is already comprehensive.

None of these steps changes the canonical calculator or the canonical attribution table.  The angle math is correct; the staleness is purely in the delivery pipeline.

---

## 8. Out-of-scope items observed during the audit (recorded for future tickets)

- **HD vs astrology drift assertion** (`canonical_astronomy.assert_no_drift`) is invoked by `/api/diagnostics/canonical-astronomy/{user_id}` but compares **longitudes only**, not sign labels.  This is fine *if* downstream consumers only use longitudes.  In practice they use signs.  Drift-assertion could be extended to also assert sign-label equality post-Variant-A unification.
- **`forensic_variant_b` block on every chart** weighs ~0.5 KB per chart and is read by zero production paths.  Could be moved off-chart or dropped after stamp-consistency work in step 4.
- `astrology.calculations` exports `tropical_to_sidereal` with a `DeprecationWarning`.  Still imported by W2 (line 548).  Switching W2 to use SwissEph native sidereal mode for ASC/MC (`swe.houses_ex(jd, lat, lon, b'P', FLG_SIDEREAL)` for both Equal and Placidus paths) would remove the manual subtraction and the deprecation warning in one shot.
- **Three orphan charts** (no engine_version, no migration_marker) in `test_database` are still served by R1-R22.  These should be either deleted or re-keyed against their owning user and re-run through W7.

---

## 9. Summary

| Question | Answer |
|----------|--------|
| Is the canonical calculator producing correct Variant-A angles? | **Yes.** `calculations.astrology.get_full_natal_chart` writes Variant A signs and 13-sign-aware values on every angle. |
| Where does staleness come from then? | **Parallel attributors (uniform_30 in sidereal_config; V-B alias in sign_attribution), missing `tropical_longitude` on stored angles, hardcoded `28.69` in iau_constellations, stamp drift across non-migration write paths, and 12-sign-only narrative tables that drop Ophiuchus.** |
| Is the migrated DB safe today? | **Mostly.** 168/171 charts carry Variant A canonical stamps and data. 3 orphan charts have no stamps. **All 168 charts can have downstream readers (canonical_astronomy diagnostics, transit signals, lunar cycle, IAU overlay, admin forensic) silently disagree with the stored signs** because those readers re-attribute via uniform_30 or use the wrong tropical offset. |
| What would "one canonical source per chart" require? | **Step-1 through Step-9 in §7.**  No calculator change; only sign-attributor consolidation, persistence-stamp consolidation, and downstream 13-sign awareness. |

End of report.
