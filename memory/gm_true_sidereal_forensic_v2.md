# GM TRUE SIDEREAL FORENSIC V2 — Mirror Implementation Report
**Branch:** `gm-true-sidereal-forensic-v2`
**Date:** 2026-05-31
**Mode:** Read-only. NO chart calculation code modified. NO migration.
**Status of canonical default:** **REVERTED → Equal** (Placidus retained as optional).
**Status of recompute migration:** **FROZEN.** Confirm token rotated; endpoint refuses to write.

---

## STATUS — Immediate Actions Completed

| Action | Status | File |
|---|---|---|
| 1. Revert canonical house system → Equal | ✅ Done — `CANONICAL_HOUSE_SYSTEM = "Equal"` | `routers/admin_gm_aligned.py` |
| 2. Disable migration recompute | ✅ Done — `_MIGRATION_FROZEN = True`; token rotated to `__FROZEN__GM_FORENSIC_V2_PENDING__`; even with old token, endpoint returns `frozen: true` and does not write | `routers/admin_gm_aligned.py` |
| 3. Preserve IC variant fix, forensic endpoints, comparison tools, Placidus code path | ✅ All retained, untouched | `calculations/human_design.py`, `calculations/astrology.py`, `routers/admin_gm_aligned.py`, `scripts/gm_forensic_audit.py` |
| 4. New forensic branch for True Sidereal-M parity check | ✅ This document | `/app/memory/gm_true_sidereal_forensic_v2.md` |

Verified live:
- `GET /api/admin/gm-forensic-ana` now reports `"canonical_house_system": "Equal"`.
- `POST /api/admin/gm-aligned-recompute?dry_run=false&confirm=GM_PLACIDUS_RECOMPUTE_V1` returns `{"marker": "gm-aligned-recompute-FROZEN", "frozen": true, "will_write": false}`. Zero rows written.

---

## PHASE A — Mirror's exact algorithm (verbatim from code)

All paths below reference `/app/backend/calculations/`.

### A.1 Ephemeris layer
| Item | Mirror value | Source |
|---|---|---|
| Ephemeris engine | Swiss Ephemeris via `pyswisseph` | `astrology.py:29, 53–60` |
| Ephemeris path | `/app/backend/ephe/` (full SE files, not Moshier) | `astrology.py:53` |
| Calculation flags (planets) | `SWE_FLG_SWIEPH \| SWE_FLG_SIDEREAL` | `astrology.py:74` |
| Calculation flags (tropical-only helpers) | `SWE_FLG_SWIEPH` | `astrology.py:75` |
| Julian Day helper | `swe.julday(year, month, day, decimal_hour_UT)` (UT) | `astrology.py:101–111` |

### A.2 Sidereal mode / ayanamsa / SVP / epoch / precession

```python
# astrology.py:66–69
SVP_DEGREES = 31.2836         # Sharatan (β Arietis) anchored
J2000_EPOCH = 2451545.0       # Jan 1 2000, 12:00 TT
swe.set_sid_mode(swe.SIDM_USER, J2000_EPOCH, SVP_DEGREES)
```

| Aspect | Mirror behaviour |
|---|---|
| Sidereal mode | `SE_SIDM_USER` (user-defined fixed ayanamsa) |
| Ayanamsa at epoch t0 | **31.2836°** |
| Epoch t0 | **J2000 (JD 2451545.0)** |
| Yearly increment (precession of ayanamsa) | **0.0** *(implicit — SE applies its own precession of the equinoxes when computing tropical, then subtracts the fixed ayanamsa to produce sidereal)* |
| Effective ayanamsa at any other JD | Constant 31.2836° in sidereal-frame; tropical-frame precession is handled internally by SE |
| Nutation | Applied by SE by default (`SWE_FLG_SWIEPH` does include nutation) — not toggled off |

### A.3 Planet position pipeline

```python
# astrology.py:230–264, calculate_planet_position_sidereal()
result = swe.calc_ut(jd, planet_id, FLG_SWIEPH | FLG_SIDEREAL)
sidereal_longitude = result[0][0]            # already ayanamsa-subtracted by SE
sign_info = longitude_to_sign_degree(sidereal_longitude)
```

### A.4 Sign attribution — **NON-uniform, variable-width**
`calculations/sign_attribution.py`, `DEFAULT_MODE = MODE_TRUE_SIDEREAL_MIDPOINT`.

> ⚠️ This is a critical and often-overlooked fact: Mirror does NOT use fixed 30°-per-sign sidereal. It uses a 12-sign **constellation-midpoint** model (Ophiuchus merged into Scorpius, IAU 1930 Delporte projection, J2000), operating on the **tropical** longitude.

Mirror's boundary table (tropical degrees, full longitude 0–360):
```
Aries        25.61 → 56.53      width 30.92
Taurus       56.53 → 88.16      width 31.63
Gemini       88.16 → 116.29     width 28.13
Cancer       116.29 → 142.15    width 25.86
Leo          142.15 → 175.97    width 33.82  ← widest
Virgo        175.97 → 212.68    width 36.71  ← widest
Libra        212.68 → 241.68    width 29.00
Scorpio      241.68 → 268.52    width 26.84  (absorbed Ophiuchus)
Sagittarius  268.52 → 298.48    width 29.96
Capricorn    298.48 → 326.76    width 28.28
Aquarius     326.76 → 354.93    width 28.17
Pisces       354.93 → 25.61     width 30.68  (wraps 0°)
```

For each planet the sign-membership test runs against the **tropical** longitude; the "degrees within sign" reported is `tropical − sign_start`, which can be ≥ 30° for the wider signs (Leo, Virgo, Pisces).

### A.5 ASC / MC

```python
# astrology.py:267–296
houses, ascmc = swe.houses(jd, lat, lon, b'P')    # Placidus, tropical
asc_tropical = ascmc[0]
mc_tropical  = ascmc[1]
asc_sidereal = asc_tropical - 31.2836°            # (effectively)
mc_sidereal  = mc_tropical  - 31.2836°
```
Sign attribution for ASC/MC uses the same midpoint table — but called on the *sidereal* longitude with `tropical_longitude` not passed; `longitude_to_sign_degree` then reconstructs `tropical = sidereal + 31.2836°` and runs midpoint attribution.

### A.6 House cusps

| Setting | Equal mode (current default) | Placidus mode (optional) |
|---|---|---|
| Cusps source | `calculate_equal_houses(asc_sidereal)` — 12 × 30° starting at ASC | `swe.houses_ex(jd, lat, lon, b"P", FLG_SIDEREAL)` with `SIDM_USER` set |
| House 1 cusp | = ASC sidereal | = ASC sidereal (from SE) |
| House 10 cusp | = ASC + 270° (NOT the MC in general) | = MC sidereal by definition |
| Code path | `astrology.py:561` | `astrology.py:533–559` |

### A.7 Node mode
`PLANETS["North Node"] = swe.TRUE_NODE` (true node, not mean node). South Node computed as +180° from North Node.

### A.8 Compute integrity
Every chart payload carries `compute_integrity` validation (SymbolicComputeContract — `astrology.py:36–41`) so unintended mutations are caught.

---

## PHASE A summary table — Mirror's exact stack

```
zodiac           = True Sidereal — sign assignment via "Midpoint" variant B (12 signs, Ophiuchus merged into Scorpius)
ayanamsa         = User defined, fixed
  SVP            = 31.2836°
  epoch t0       = J2000 = JD 2451545.0
  yearly delta   = 0.0 (no precession of the sidereal frame)
nutation         = applied by SE default
precession       = applied by SE default (tropical → sidereal step)
nodes            = True Node (SE_TRUE_NODE), South Node = North + 180°
ASC / MC         = SE swe.houses(...) tropical Placidus → minus 31.2836° → sidereal
house cusps      = Equal 30° from sidereal ASC  (default; Placidus optional)
gates (HD)       = standard 64-gate wheel (separate module, unchanged by V2)
sign-degree      = degrees within variable-width tropical sign band (can exceed 30°)
```

---

## PHASE B — Checklist for the Ana session (what to capture from Genetic Matrix)

Capture **typed text or full screenshots** of each of the following pages. Do not rely on intuition; we need verbatim values.

### B.1 Global account / chart settings page
- [ ] Zodiac Type dropdown — exact label visible
- [ ] House System dropdown — exact label
- [ ] Ayanamsa dropdown — exact label
- [ ] If "Custom" or "User defined" is selected, screenshot the modal that opens (SVP, epoch, anchor star, yearly increment)
- [ ] Node setting (True vs Mean)
- [ ] Topocentric / Geocentric toggle
- [ ] Sidereal model (e.g., "True Sidereal-M (Midpoint)" — note the *exact* parenthetical label)

### B.2 True Sidereal sub-settings (if a separate page)
- [ ] Anchor star (Sharatan / β Arietis / other)
- [ ] Anchor degree (the "= 02° Aries" value)
- [ ] Whether boundaries are IAU-1930 (Delporte) or another constellation set
- [ ] Whether Ophiuchus is included (13 signs) or merged into Scorpius (12 signs)
- [ ] Reference epoch for the boundaries (J2000? other?)

### B.3 Zodiac 13 page (if visible separately)
- [ ] Each constellation's start degree (so we can reconstruct GM's boundary table)
- [ ] Whether the listing matches IAU midpoints or something else

### B.4 Per-chart "advanced calculation" page
- [ ] House system used **for this specific chart** (top-of-chart label)
- [ ] Any "ephemeris source" indicator
- [ ] Any "nutation" / "precession of the ayanamsa" toggle

### B.5 Verbatim numeric ground truth (typed, not OCR'd)
For Ana, please type out from the GM screen — *exactly* what is printed:
- [ ] ASC longitude (e.g., "Aries 12°14′") **and** the house number box
- [ ] MC longitude **and** house number box
- [ ] Sun longitude **and** house number
- [ ] Moon longitude **and** house number
- [ ] Mercury, Venus, Mars longitudes + house numbers
- [ ] Confirm whether degrees shown are within-sign or absolute (i.e., can they exceed 30°?)

### B.6 What we still cannot determine remotely
- Whether GM applies nutation
- Whether GM applies precession to the sidereal frame ("delta_T")
- Whether GM's "Midpoint" refers to IAU constellation arc-midpoints or to longitudinal midpoints between adjacent constellation start points (these differ by ~0.5°)
- Whether GM's house system is per-user or per-chart (Ana's PDF is Placidus, Pete & Mel are Equal — probably per-chart-overridable from a default)

---

## PHASE C — No code changes performed in chart calculations

Files **NOT** touched in this session:
- `calculations/astrology.py`
- `calculations/sign_attribution.py`
- `calculations/human_design.py` *(only canonical-flip text in admin_gm_aligned was reverted)*
- All cache writers / today / deep-dive / timeline pipelines

Files touched this session:
- `routers/admin_gm_aligned.py` — `CANONICAL_HOUSE_SYSTEM` flipped back to `"Equal"`, migration frozen, token rotated.
- `scripts/gm_forensic_audit.py` — created earlier in this audit (read-only).
- This document — created.

---

## SUCCESS-CRITERIA ANSWERS (partial — pending Ana session)

1. **What exactly does Mirror calculate?** — See Phase A. In short: SE-driven tropical → fixed-ayanamsa sidereal (SVP=31.2836°, J2000); sign attribution via the *True Sidereal-M Midpoint, 12-sign, Ophiuchus-merged* boundary table operating on tropical longitudes; Equal houses (default) from sidereal ASC; ASC/MC from `swe.houses` tropical Placidus then sidereal-shifted; True Nodes.

2. **What exactly does GM calculate?** — *Cannot be finalised without Phase-B settings dump.* From printed labels we know GM offers "True Sidereal-M (Midpoint)" with "User defined" ayanamsa and a per-chart house-system override. The PDF table contains "degrees-within-sign" values that exceed 30° (Moon 40°47′, MC 40°49′, Saturn 41°43′, etc.) — strong evidence that GM uses **variable-width sign bands** too, but possibly **Variant A (13-sign with Ophiuchus separated)** rather than Mirror's **Variant B (12-merged)**.

3. **Where do they differ?** — Three candidate sites, in priority order:
   - **(a) Sign-boundary set:** Mirror uses 12-merged Variant B. GM may use 13-sign Variant A, or different IAU midpoints (e.g., 1875 vs 1930 epoch, longitudinal vs arc midpoints).
   - **(b) House-system default per user:** Ana = Placidus, Pete & Mel = Equal. Per-chart toggle, not a single canonical.
   - **(c) Ayanamsa anchor:** likely matches (Sharatan = 02°Aries = 31.2836° SVP) — the Ana JPG explicitly shows `Custom(Sharatan(Beta Aries))=02° Aries`. *Probable match.*

4. **Is the discrepancy …?** Most likely **(zodiac implementation — sign boundary table)** + **(house system per user)**. Less likely ayanamsa, SVP, precession, chart storage, or UI rendering.

5. **Is any migration justified?** **NO.** Three live users disagree on house system in GM's own output (1 Placidus, 2 Equal). There is no universal target to migrate toward.

---

## FINAL RECOMMENDATION

> **C. Further forensic investigation required.**
>
> Specifically: complete Phase B (capture GM's exact zodiac-mode settings during the Ana session) **before** any chart-calculation change is even considered. After that, the most likely remaining work is *not* changing house systems but possibly extending `sign_attribution.py` to offer Variant A (13-sign / Ophiuchus separate) as an opt-in alternative — and only if it actually improves agreement with all three reference charts (not just one).
>
> The canonical default stays **Equal** until the user explicitly approves change. No migration will run.
