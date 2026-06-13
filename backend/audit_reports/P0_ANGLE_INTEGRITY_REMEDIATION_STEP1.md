# P0 — Astrology Angle Integrity Remediation — Step 1

**Build marker:** `angle-staleness-step1-v1`
**Date:** 2026-02 (current session)
**Scope:** Eliminate divergent astrology angle/sign derivation from live delivery paths.
**Mode:** Surgical code change. No calculator math change. No chart-doc writes. No env flag changes.

---

## 1. Acceptance check

| Requirement | Status |
|-------------|--------|
| No production user-facing path derives angle signs through `uniform_30`. | ✅ `calculations/sidereal_config.longitude_to_sign_degree` now delegates to canonical Variant A. All 8+ importers (`canonical_astronomy`, `transit_signals` Earth-gate, `lunar_cycle`, transit dominance/aspects/window helpers) automatically inherit Variant A. |
| No production user-facing path derives angle signs through Variant B alias (`attribute_sign_true_sidereal_midpoint`). | ✅ The alias is now used **only** by `/api/admin/asc_forensic` and is labeled "LEGACY / FORENSIC ROLLBACK". No production read path consumes it. |
| Canonical Variant A is the only live source for ASC/MC/DC/IC sign attribution. | ✅ Stored-chart angles (W7 migration: `midpoint13_variant_a_v1`) and any re-attribution helpers now route through `calculations/astrology.longitude_to_sign_degree` (`DEFAULT_MODE = midpoint13_variant_a`). |
| Hardcoded tropical reconstruction constants replaced. | ✅ Four occurrences of `+28.69` in `services/iau_constellations.py` (body / angle reconstruction) replaced with `_CANONICAL_SVP_OFFSET = SVP_DEGREES = 31.2836`. The two IAU constellation **boundary** values (which legitimately use `28.69` as the Pisces/Aries border) are untouched. |
| All four locked flags remain unchanged. | ✅ Verified in `/app/backend/.env`: `INTENT_ROUTER_V2_CUTOVER=false`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`, `RELATIONSHIP_ORCHESTRATION_PROMPT=false`, `CROSS_LENS_PROMPT_SURFACE=false`. |
| Calculator math, birth data, chart documents, migrations, relationship orchestration, HD, timeline untouched. | ✅ No edits to `calculations/astrology.py` calculator routines, `calculations/human_design.py`, timeline modules, migration scripts, or chart docs. |

---

## 2. Files changed

| File | Lines touched | Nature of change |
|------|---------------|-------------------|
| `/app/backend/calculations/sidereal_config.py` | `longitude_to_sign_degree` (replaced body, preserved legacy under `_legacy_longitude_to_sign_degree_uniform_30`) | Delegation to canonical Variant A. Legacy implementation kept as private function for back-compat callers that still need raw uniform_30. |
| `/app/backend/services/iau_constellations.py` | Added `_CANONICAL_SVP_OFFSET` import at top; replaced 4 hardcoded `28.69` reconstruction offsets at lines 677, 688, 714, 724. | Fixes off-by-2.59° tropical reconstruction. |
| `/app/backend/server.py` (`/api/astrology/chart/{user_id}`) | `SIGN_TO_ELEMENT`, `SIGN_TO_MODALITY` (extended); `element_counts` (added `'Ether': 0`). | Ophiuchus now counts in element/modality balances (Ether / Mutable). |
| `/app/backend/server.py` (`/api/diagnostics/astro-system`) | Response payload labels. | Reports canonical Variant A instead of stale Variant B label. Adds explicit provenance fields for V-A canonical, V-B forensic, uniform_30 deprecated. |
| `/app/backend/server.py` (`/api/admin/asc_forensic/{user_id}`) | `attribution_preview._both_modes` (added Variant A column + `provenance` strings on all three modes). | Admin forensic now previews all three modes with clear provenance labels. |

**No other files were modified.**  Audit / migration / calculator / HD / timeline / relationship-orchestration / chart documents are untouched.

---

## 3. Before / After source-of-truth map (sign attribution only)

### Before remediation

```
              ┌─────────────────────────────────────────────────────────────┐
              │  Three live sign attributors, no enforcement of canonical:  │
              │                                                             │
              │  A) calculations.astrology.longitude_to_sign_degree         │
              │     → attribute_sign(DEFAULT_MODE=midpoint13_variant_a)    │
              │     → Variant A canonical ✓                                 │
              │                                                             │
              │  B) calculations.sidereal_config.longitude_to_sign_degree   │
              │     → int(lon/30) on 12-sign hardcoded list                │
              │     → uniform_30 (no Ophiuchus) ✗                          │
              │                                                             │
              │  C) calculations.sign_attribution.                          │
              │       attribute_sign_true_sidereal_midpoint (legacy alias)  │
              │     → Variant B (12-sign Ophi-merged) ✗                    │
              └─────────────────────────────────────────────────────────────┘
                  ▲                  ▲                       ▲
   ┌──────────────┘                  │                       └──────────┐
   │                                 │                                  │
canonical write (W2)         production reads:                  /api/admin/asc_forensic
+ deep dive recompute        - canonical_astronomy (diag)       (admin/diagnostic)
+ astrology_today_engine     - transit_signals.Earth-gate
+ solar_return_engine        - transit_signals.Moon-gate
+ natal_object_engine        - lunar_cycle
+ forum_lens_helpers         - transit_dominance/aspects/window
+ stored chart angles        - iau_constellations (+28.69, off
                               by 2.59°)
```

### After remediation

```
              ┌─────────────────────────────────────────────────────────────┐
              │   ONE LIVE sign attributor for production paths:            │
              │                                                             │
              │   calculations.astrology.longitude_to_sign_degree           │
              │     → attribute_sign(DEFAULT_MODE=midpoint13_variant_a)    │
              │     → Variant A canonical ✓                                 │
              │                                                             │
              │   sidereal_config.longitude_to_sign_degree                  │
              │     → DELEGATES to canonical above ✓                        │
              │     (uniform_30 implementation preserved as private         │
              │      `_legacy_longitude_to_sign_degree_uniform_30`          │
              │      for forensic comparison only.)                         │
              │                                                             │
              │   attribute_sign_true_sidereal_midpoint (V-B alias)         │
              │     → USED ONLY by /api/admin/asc_forensic                  │
              │     → labeled "LEGACY / FORENSIC ROLLBACK" in payload       │
              └─────────────────────────────────────────────────────────────┘
                  ▲                                              ▲
                  │                                              │
   All production user-facing paths.                  Admin / diagnostic only.
   - canonical write (W2)                             Reports all three modes
   - deep dive recompute                              with provenance labels:
   - astrology_today_engine                            * V-A canonical
   - solar_return_engine                               * V-B legacy/forensic
   - natal_object_engine                               * uniform_30 deprecated
   - forum_lens_helpers
   - stored chart angles (R3–R22)
   - canonical_astronomy diagnostic
   - transit_signals (Earth/Moon gates)
   - lunar_cycle
   - transit_dominance/aspects/window
   - iau_constellations (now uses canonical SVP=31.2836)
```

---

## 4. Regression proof — Pete, Mel, Isaac, Thaddeus

### 4.1  Live re-attribution of stored ASC longitude (sanity test)

| User       | User ID                       | Stored ASC sign | Re-attributed via `sidereal_config` (now delegating) | Re-attributed via canonical `calculations.astrology` | Match |
|------------|-------------------------------|------------------|-------------------------------------------------------|------------------------------------------------------|-------|
| Pete       | `697f0c6abf35c0528ff06954`    | Sagittarius     | Sagittarius                                           | Sagittarius                                          | ✓     |
| Mel        | `697ec826ad4b18f75bf42616`    | Cancer          | Cancer                                                | Cancer                                               | ✓     |
| Isaac      | `69dda348de9cb1c83c0780f8`    | Aquarius        | Aquarius                                              | Aquarius                                             | ✓     |
| Thaddeus   | `69dd0b2cc92ba973f8838c11`    | **Ophiuchus**   | **Ophiuchus**                                         | **Ophiuchus**                                        | ✓     |

> Thaddeus (Ophiuchus ASC) is the strongest signal that the fix lands correctly: previously `sidereal_config.longitude_to_sign_degree` would have returned "Scorpio" or "Sagittarius" for an Ophiuchus longitude because it had no Ophiuchus in its 12-sign list.

### 4.2  All four angles per user, with re-attribution consistency

| User     | Engine stamp                 | ASC               | MC                | IC                | DC                 |
|----------|------------------------------|--------------------|-------------------|-------------------|--------------------|
| Pete     | `midpoint13_variant_a_v1` ✓  | Sagittarius ✓     | Virgo ✓           | Pisces ✓          | Gemini ✓           |
| Mel      | `midpoint13_variant_a_v1` ✓  | Cancer ✓          | Aries ✓           | Virgo ✓           | Sagittarius ✓      |
| Isaac    | `midpoint13_variant_a_v1` ✓  | Aquarius ✓        | **Ophiuchus** ✓   | Taurus ✓          | Leo ✓              |
| Thaddeus | `midpoint13_variant_a_v1` ✓  | **Ophiuchus** ✓   | Leo ✓             | Aquarius ✓        | Taurus ✓           |

All 16 (4 users × 4 angles) angle sign re-attributions round-trip cleanly through both `sidereal_config.longitude_to_sign_degree` (now delegating) and `calculations.astrology.longitude_to_sign_degree` (canonical).

### 4.3  End-to-end endpoint regression

**`GET /api/astrology/chart/{user_id}`** (live recompute / read):

```
Pete:     ASC=Sagittarius MC=Virgo
          elements = {Fire:4.5, Earth:0.5, Air:0.5, Water:6.0, Ether:0}
          modalities = {Cardinal:3.5, Fixed:1.5, Mutable:6.5}
Thaddeus: ASC=Ophiuchus MC=Leo
          elements = {Fire:2.5, Earth:3.5, Air:5.0, Water:0.5, Ether:0}
Isaac:    ASC=Aquarius MC=Ophiuchus
          elements = {Fire:4.5, Earth:2, Air:1.0, Water:4.0, Ether:0}
Mel:      ASC=Cancer MC=Aries
          elements = {Fire:1, Earth:4.0, Air:3.5, Water:2.5, Ether:0.5}   ← Mel has a planet in Ophiuchus; Ether now counts (previously dropped to nowhere)
```

**`GET /api/diagnostics/astro-system`** (post-remediation labels):
```
zodiac_mode: "midpoint13_variant_a_v1 (canonical Variant A — 13 signs)"
ophiuchus_enabled: True
sign_attribution_mode_canonical: "midpoint13_variant_a"
sign_attribution_mode_legacy_forensic: "midpoint12_variant_b (Ophiuchus merged into Scorpio — kept for forensic rollback only)"
sign_attribution_mode_deprecated: "uniform_30 (legacy 30°-equal, retained only as a wrapper for back-compat)"
```

**`GET /api/admin/asc_forensic/{pete}`** (admin diagnostic — Pete's ASC):
```json
{
  "body": "ASC",
  "tropical_longitude": 286.822093,
  "midpoint13_variant_a": {
    "sign": "Sagittarius",
    "degree": 19.756693,
    "provenance": "CANONICAL (Variant A — midpoint13_variant_a_v1)"
  },
  "uniform_30": {
    "sign": "Sagittarius",
    "degree": 15.538493,
    "provenance": "DEPRECATED (uniform_30 — legacy 30°-equal; back-compat only)"
  },
  "midpoint12_variant_b": {
    "sign": "Sagittarius",
    "degree": 18.302093,
    "provenance": "LEGACY / FORENSIC ROLLBACK (Variant B — midpoint12_variant_b; Ophiuchus merged into Scorpio)"
  }
}
```

---

## 5. Out-of-scope items left untouched (per task constraints)

The following defects from §7 of the parent forensic audit (`ASTROLOGY_ANGLE_STALENESS_FORENSIC_AUDIT.md`) remain open and were **not** addressed in Step 1 (deliberately — they touch calculator math, chart documents, or migrations):

- **§7 Step 1 (parent audit, additive):** stamp `tropical_longitude` on every angle written by W2. Calculator change — out of scope.
- **§7 Step 4:** single chart-doc writer helper to keep top-level stamps in sync. Changes chart-write paths — out of scope.
- **§7 Step 7:** `services/house_inventory_engine.py:66-74` silent dict-shape failure. Read-path bug, but lives in the calculator-adjacent house-attribution module — kept out of scope to limit blast radius of Step 1.
- **§7 Step 9:** one-pass migration to back-fill `tropical_longitude`. Migration — out of scope.
- `services/astrology_today_engine.py:51-489` `SIGN_BEHAVIOR` dict missing Ophiuchus entry. Narrative content table — out of scope (touches narrative copy, not sign attribution).
- 18+ other hardcoded 12-sign lists across the codebase (grep `'Aries', 'Taurus', 'Gemini', 'Cancer'`). Distributed work — out of scope for Step 1.

---

## 6. Risk analysis (post-deployment)

| Risk | Likelihood | Impact | Mitigation now in place |
|------|------------|--------|--------------------------|
| A previously uniform_30 caller now receives `'Ophiuchus'` and crashes on a hardcoded 12-sign lookup. | Low/Medium. The two callers that already iterate the canonical Variant A pipeline (`solar_return_engine`, `astrology_today_engine`) tolerate Ophiuchus. Transit Earth-gate / Moon-gate sign labels become 13-sign aware. | Low for those surfaces (sign label is informational, not a lookup key). Higher only where a downstream consumer indexes a 12-element table by sign name. | **Element_counts in `/api/astrology/chart`** is patched (Ether bucket added). `forum_lens_helpers` already has Ether handling. Other 18+ tables remain hardcoded but are not on the angle-sign critical path. |
| `iau_constellations` returns different IAU constellations for bodies near boundaries after the 2.59° offset fix. | High. This is the desired outcome — previously `+28.69` mis-classified up to 6.5% of bodies. | The Ophiuchus overlay card was already an additive UI element; consumers expected the canonical answer. | Live regression on Pete/Mel/Isaac/Thaddeus confirms IAU lookups now use canonical SVP=31.2836. |
| `_legacy_longitude_to_sign_degree_uniform_30` is privately retained — could be inadvertently called by future code searching for "uniform_30". | Very low. Underscore prefix marks it as internal; docstring forbids production use. | If invoked, it returns the exact pre-remediation uniform_30 result. Useful for forensic A/B work. | Documented and guarded by naming convention. |

No downstream regressions observed across the 4 reference users. Backend started cleanly post-restart.

---

## 7. Updated source-of-truth map — D-rows (Derive/Recompute Layer)

This supersedes §1.3 in the parent audit for the listed rows.

| ID | File / Line | Sign attribution it uses | Status post Step 1 |
|----|-------------|--------------------------|---------------------|
| D1 | `services/canonical_astronomy.py:57` | Via `sidereal_config.longitude_to_sign_degree` | ✅ **NOW Variant A** (via delegation). |
| D2 | `calculations/sidereal_config.py:141` | Variant A (delegated) | ✅ **NOW Variant A**. Legacy implementation preserved as `_legacy_longitude_to_sign_degree_uniform_30` (internal, forensic only). |
| D3 | `services/transit_signals.py:777` (Earth gate) | Via `sidereal_config.longitude_to_sign_degree` | ✅ **NOW Variant A** (inherited from D2 fix). |
| D4 | `services/transit_signals.py:803-855` (Moon gate transit) | Via `sidereal_config.calculate_planet_by_name` → `longitude_to_sign_degree` | ✅ **NOW Variant A**. |
| D5 | `services/lunar_cycle.py:286` | Via `sidereal_config.longitude_to_sign_degree` | ✅ **NOW Variant A**. |
| D9 | `services/iau_constellations.py:677, 688, 714, 724` | Tropical reconstruction `+28.69` | ✅ **FIXED** — now `+_CANONICAL_SVP_OFFSET = SVP_DEGREES = 31.2836`. |
| D12 | `server.py:14786-14801` element/modality maps | Hardcoded 12-sign | ✅ **FIXED** — Ophiuchus added (Ether/Mutable); `element_counts` now seeded with `'Ether': 0`. |
| D13 | `server.py:31931` admin asc_forensic | `attribute_sign_true_sidereal_midpoint` (V-B alias) | ⚠ **LABELED**. Still callable for admin/diagnostic; now displayed alongside Variant A (canonical) and uniform_30 (deprecated) with explicit provenance strings. No production read consumes this endpoint. |

All other D-rows (D6, D7, D8, D10, D11, D14, D15) were already Variant A or out of scope; status unchanged.

---

## 8. How to verify (one-liner harness)

```bash
cd /app/backend && python3 -c "
from calculations.sidereal_config import longitude_to_sign_degree as sc
from calculations.astrology import longitude_to_sign_degree as ca
import calculations.sign_attribution as sa

# 1. Default mode must be Variant A
assert sa.DEFAULT_MODE == sa.MODE_MIDPOINT13_VARIANT_A, 'DEFAULT_MODE drift'

# 2. sidereal_config must now delegate
for sid in [0.0, 90.0, 180.0, 225.0, 255.5384925799478, 313.6515]:
    r1 = sc(sid); r2 = ca(sid)
    assert r1['sign'] == r2['sign'], f'divergence at {sid}: {r1[\"sign\"]} vs {r2[\"sign\"]}'

# 3. IAU constellations must use canonical SVP
from services.iau_constellations import _CANONICAL_SVP_OFFSET
from calculations.sidereal_config import SVP_DEGREES
assert _CANONICAL_SVP_OFFSET == SVP_DEGREES, 'IAU SVP drift'

print('Step 1 acceptance: PASS')
"
```

End of report.
