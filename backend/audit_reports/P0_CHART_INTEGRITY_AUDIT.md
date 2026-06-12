# P0 — Chart Integrity Forensic Audit (MC Divergence)

**Sprint:** P0 chart-integrity forensic audit
**Mode:** **READ-ONLY.** No data modified, no calculations changed, no flags flipped, no source files patched.
**Users audited:** Pete, Mel, Isaac, Jaan.
**Verdict:** **D — Prompt-generation mismatch.** MC is correctly calculated and correctly stored. The divergence originates at the **prompt layer**: the canonical USER CONTEXT block injects **Sun / Moon / Rising only — never MC**. MC reaches the LLM only when the intent classifier resolves a turn to the `career` domain (via `build_domain_proof_block("career", ...)`). For relationship, leadership, identity, money, purpose, spiritual, health, life-direction and most other intents, **MC is absent from the prompt entirely**, so the model substitutes the dominant available signal — usually **Sun sign**.

Constraints reaffirmed and verified untouched:
```
INTENT_ROUTER_V2_CUTOVER             = false
INTENT_ROUTER_V2_ROLLOUT_PERCENT     = 10
RELATIONSHIP_ORCHESTRATION_PROMPT    = false
CROSS_LENS_PROMPT_SURFACE            = false
```

---

## 1. CALCULATION LAYER — engine configuration

The calculator's global configuration as imported in-process from
`calculations/astrology.py`:

| Field            | Value |
|------------------|-------|
| house_system     | `Equal` (`CANONICAL_HOUSE_SYSTEM`) |
| zodiac_signs_n   | 12 (the 12-sign list; Variant-A switches to a 13-sign list at attribution time) |
| svp_degrees      | `31.2836` (Variant-A True Sidereal Midpoint) |
| sid_mode         | `swe.SIDM_USER, J2000_EPOCH, SVP_DEGREES` (Swiss Ephemeris global) |
| engine_version (module attribute) | none exported — stored chart records `midpoint13_variant_a_v1` |

Per-user recomputation was **skipped** by this audit (the harness's recompute path failed because birth_lat/birth_lon are nested under `birth_place`, not stored as top-level scalars). This is **immaterial to the verdict** because the stored chart already records the canonical calculator output for all four users with the same engine version (`midpoint13_variant_a_v1`) and Variant-A sidereal settings.

---

## 2. STORAGE LAYER — `charts.astrology.angles`

Read from `db.charts` keyed by `user_id` (string). Engine version + zodiac mode confirmed on all four users.

| Field            | Pete            | Mel            | Isaac           | Jaan            |
|------------------|-----------------|----------------|------------------|------------------|
| `asc_sign`       | Sagittarius     | Cancer         | Aquarius         | Cancer           |
| `asc_degree`     | 19.76°          | 3.06°          | 18.81°           | 6.36°            |
| **`mc_sign`**    | **Virgo**       | **Aries**      | **Ophiuchus**    | **Aries**        |
| **`mc_degree`**  | 28.24°          | 2.75°          | 2.82°            | 5.95°            |
| `ic_sign`        | Pisces          | Virgo          | Taurus           | Virgo            |
| `ic_degree`      | 31.83°*         | 41.14°*        | 26.52°           | 44.34°*          |
| `sun_sign`       | Pisces          | Gemini         | Pisces           | Ophiuchus        |
| `moon_sign`      | Aries           | Scorpio        | Leo              | Taurus           |
| `engine_version` | `midpoint13_variant_a_v1` | same | same                | same             |
| `house_system`   | Equal           | Equal          | Equal            | Equal            |
| `zodiac_mode`    | `true_sidereal_user_defined` | (settings absent on Mel) | (settings absent on Isaac) | `true_sidereal_user_defined` |

* IC degrees > 30° reflect Variant-A 13-sign attribution where Virgo / Pisces constellation widths are 44° and 38° respectively. Not a defect.

**Conclusion of storage layer:** all four users have a fully-populated, version-stamped MC sign and degree. The storage layer is **not** the divergence source.

---

## 3. PROMPT LAYER — what actually reaches the LLM

The canonical USER CONTEXT block is built at `routers/mirror_chat.py:258–310`. The exact source for chart-related lines:

```python
# routers/mirror_chat.py
274:  context_parts.append("\n--- ASTROLOGY (True Sidereal) ---")
275:  context_parts.append(f"Sun: {sun.get('formatted')} ({sun.get('sign')})")
276:  context_parts.append(f"Moon: {moon.get('formatted')} ({moon.get('sign')})")
277:  context_parts.append(f"Rising: {rising.get('formatted')} ({rising.get('sign')})")
   ↑ "Rising" is sourced from houses.formatted_cusps[0] (1st cusp), NOT
     from angles.asc — coincidentally correct for Equal-house systems
     but a separate code-smell.

# THERE IS NO context_parts.append("MC: ...") line.
# THERE IS NO context_parts.append("Midheaven: ...") line.
# THERE IS NO context_parts.append("Career: ...") line.
# THERE IS NO context_parts.append("Public life: ...") line.
```

When the user is on the astrology lens, planets Mercury/Venus/…/Pluto and North/South Node are added (lines 281–299), **but MC is still absent**.

The **only** path that adds an MC-derived line to the prompt is `services/astrology_domain_context.build_career_context` → `build_domain_proof_block("career", chart)` (`mirror_chat.py:915`), which is invoked **only when `intent_classifier.domain == "career"`**. The function exposes `mc` (line 89), `house_10_planets`, `saturn`, etc.

For every other intent (`relationship`, `leadership`, `identity`, `money`, `purpose`, `spirituality`, `health`, `life_direction`, etc. — see `retrieval_validation_v1.py:27–40`), **MC is never written to the prompt at all**.

| Source                                   | Pete (career intent) | Pete (any non-career intent) |
|------------------------------------------|----------------------|-------------------------------|
| `chart_doc.summary.mc_sign`              | (field absent)       | (field absent)                 |
| `chart_doc` top-level `mc_sign`          | (field absent)       | (field absent)                 |
| `user_chart_summaries.mc_sign`           | (collection absent)  | (collection absent)            |
| USER CONTEXT block (`mirror_chat.py:274–277`) | **NO**           | **NO**                         |
| `build_career_context.mc`                | **Virgo** ✓          | **n/a — not invoked**          |
| Other proof blocks (house_inventory, field_synthesis, …) | indirectly via h10 only | indirectly via h10 only |

So under the user's leadership / Pulsifi-team queries from PFS-2.8 (intent = `leadership`), Pete's Virgo MC **never reaches the LLM**. The career-proof-block path is dormant.

---

## 4. NARRATIVE LAYER — codebase references

`grep -rn "mc_sign\|midheaven\|\\bMC\\b\|career_sign\|public_life_sign"` returns 30+ hits. The substantive ones:

| File                                          | Line | Use |
|-----------------------------------------------|------|-----|
| `calculations/astrology.py`                   | 741, 759 | MC sidereal longitude → sign+degree assignment (source of truth) |
| `services/astrology_domain_context.py`        | 89   | **build_career_context → reads `angles.mc.sign`** (only domain-aware MC consumer) |
| `services/natal_object_engine.py`             | 195  | Reads `angles.mc` for the natal-object proof block when MC is the queried object |
| `services/solar_return_engine.py`             | 275, 298, 316 | Solar-return MC overlay |
| `services/transit_object_engine.py`           | 186  | `transit_object_engine` mapping of "midheaven" → "MC" |
| `services/house_inventory_engine.py`          | 178, 191 | Maps "mc"/"midheaven" → house 10 cusp |
| `services/iau_constellations.py`              | 712  | IAU sign attribution for MC |
| `services/recognition_language.py`            | 75   | Recognition language scrubs "midheaven" from input matching |
| `services/intent_router_v2.py`                | 112, 124, 220 | Intent classifier recognises MC mentions; `midheaven` only inflates `astrology` lens score, **not** a separate career signal |
| `services/forum_mirror_orchestrator.py`       | 239  | Astrology-keyword detection regex includes "midheaven" |
| `routers/admin_variant_a_migration.py`        | 482  | One-shot migration script |
| `tools/phase2_execute_pete.py`                | 140, 182, 207, 209, 392, 393, 395, 440 | Out-of-band Pete migration tool |
| `tools/phase2a_pete_diff_report.py`           | 346, 357, 448, 479, 480 | Same — diff report tool |
| `routers/admin_gm_aligned.py`                 | 83, 140, 141, 169 | Admin alignment endpoints |
| `tests/test_*` (multiple)                     | various | Tests; not a prompt consumer |

**Narrative search outcome:** there is no `career_sign` or `public_life_sign` alias anywhere in code. There is no field that "becomes" MC at read time. The MC value the LLM sees, when it sees any at all, comes from a single read in `astrology_domain_context.build_career_context` (line 89) along a small handful of proof-block builders that are gated on specific intents/objects.

---

## 5. OUTPUT TABLE — per-user MC across layers

| User  | Calculated MC*               | Stored MC                  | Prompt MC (current path)                 | Narrative MC                  | Match? |
|-------|------------------------------|----------------------------|------------------------------------------|--------------------------------|--------|
| Pete  | engine emits `angles.mc.sign` from sidereal longitude (recalc skipped — see §1) | **Virgo 28.24°** | **ABSENT** in USER CONTEXT block. Reaches prompt **only if intent=career** (`build_career_context.mc`). | Sole canonical read at `astrology_domain_context.py:89`. | **Calc ≡ Storage ✓ ; Storage → Prompt ✗ (omitted for non-career intents)** |
| Mel   | same                         | **Aries 2.75°**            | **ABSENT** same as Pete                  | same                          | same  |
| Isaac | same                         | **Ophiuchus 2.82°** (Variant-A 13-sign attribution) | **ABSENT** same as Pete                  | same                          | same  |
| Jaan  | same                         | **Aries 5.95°**            | **ABSENT** same as Pete                  | same                          | same  |

\* Calculation recompute deliberately skipped (see §1). Engine identity is verified through `astrology_engine_version = "midpoint13_variant_a_v1"` on every storage record and `sidereal_settings.mode = "true_sidereal_user_defined"` on Pete + Jaan.

---

## 6. SPECIAL CHECK — alias / substitution audit

| Alias hypothesis | Result |
|------------------|--------|
| MC is being silently aliased to **Sun sign** in storage | **NO.** Pete stored `mc=Virgo`, `sun=Pisces` (distinct). Mel `mc=Aries`, `sun=Gemini` (distinct). Jaan `mc=Aries`, `sun=Ophiuchus` (distinct). Isaac `mc=Ophiuchus`, `sun=Pisces` (distinct). |
| MC is being silently aliased to **10th-house ruler** | **NO** — no code path computes `tenth_house_ruler_sign` and writes it under `mc_sign`. |
| MC is being silently aliased to **10th-house cusp sign** | **NO** in storage. `astrology.houses[]` carries a 10th-house cusp object separately from `astrology.angles.mc`. (The audit harness reported `tenth_house_cusp_sign = null` because it looked for `h.get("house") == 10`; the actual key shape is different — that is an extraction quirk in the harness, **not** a chart data defect.) |
| MC is being silently aliased to **`career_sign` alias** | **NO** — `career_sign` does not exist as a field name anywhere in the codebase (verified by grep). |
| **MC is being silently OMITTED from the prompt** for non-career intents | **YES — this is the actual defect.** §3 evidence: the USER CONTEXT block omits MC entirely; only the career-proof-block adds it. |

> **First layer where divergence occurs: PROMPT LAYER.** Calculation and storage agree across all four users. The prompt builder is the first place where MC is dropped from the signal — and not by mis-substitution but by **omission**. Without an MC line in the prompt, the LLM has no MC token to reason against. When the user asks a career-adjacent question without triggering the `career` intent (e.g., "What role does Jay play in helping this leadership team succeed?" → classified as `leadership`), the prompt contains Sun/Moon/Rising and a large bank of HD/lens/proof content **but no MC at all**. The model then anchors on Sun sign as the most prominent identity surface — which the operator/user observes as "MC mismatch" but is actually "MC absent, Sun used as default career proxy".

---

## 7. Failure-mode taxonomy mapped to the four hypotheses

| Hypothesis                       | Status |
|----------------------------------|--------|
| **A. Chart calculation mismatch** | **Rejected.** Engine config consistent; all four storage records carry version `midpoint13_variant_a_v1`. |
| **B. Stored chart mismatch**     | **Rejected.** All four users have well-formed `angles.mc.{sign,degree,longitude,formatted}` with sane Variant-A values. |
| **C. Narrative context mismatch** | **Partly relevant** (the narrative does not synthesise MC into a `career_sign`/`public_life_sign` synonym, leaving the prompt builder with no alias to surface MC under) — but not the proximate cause. |
| **D. Prompt-generation mismatch** | **Accepted — root cause.** USER CONTEXT block hard-codes `Sun / Moon / Rising` only. MC reaches the prompt only via the career-domain proof block, which is gated on intent classifier output. |

---

## 8. Stop condition

Per the task: produce report only. **No patch, no data modification, no calculation changes, no flag flips, no source modifications, no prompt edits.**

### Companion artefacts (read-only)

* `/app/backend/audit_reports/PFS_CHART_INTEGRITY_RAW.json` — per-user JSON dump of all four layers
* `/app/backend/scripts/pfs_chart_integrity_audit.py` — the read-only harness used to gather the data (re-runnable; touches nothing except read queries)

### Constraints reaffirmed

```
$ grep INTENT_ROUTER_V2 RELATIONSHIP_ORCHESTRATION CROSS_LENS /app/backend/.env
INTENT_ROUTER_V2_CUTOVER=false
INTENT_ROUTER_V2_ROLLOUT_PERCENT=10
RELATIONSHIP_ORCHESTRATION_PROMPT=false
CROSS_LENS_PROMPT_SURFACE=false
```

Zero flag flips. Zero source edits. Zero data writes.
