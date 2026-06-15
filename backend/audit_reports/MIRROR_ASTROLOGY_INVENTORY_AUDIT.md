# MIRROR ASTROLOGY INVENTORY AUDIT + RECONNECTION

**Build marker:** `astrology-chat-v5-advanced-object-reconnect`
**Date:** 2026-06-15
**Scope:** Audit + recovery of advanced astrology objects in the chart payload
and downstream interpretation surfaces. No calculator, birth-data, timeline,
HD or generation logic was modified. No new collections. No schema migrations.

This document delivers the four artefacts the user explicitly requested:

1. [Inventory Report](#1-inventory-report)
2. [Historical Recovery Audit (Task 2.5)](#2-historical-recovery-audit-task-25)
3. [Regression Report](#3-regression-report)
4. [Reconnection Plan](#4-reconnection-plan--applied-fixes)
5. [Recommended Priority Order](#5-recommended-priority-order)

---

## 1. Inventory Report

A complete catalogue of advanced astrology objects across the canonical
chart payload and every interpretation surface. Status legend:

| Code | Meaning |
| ---- | ------- |
| ✅ ACTIVE | Computed AND surfaced |
| 🟡 RECONNECTED | Implemented but was silently dropping — **fixed in this audit** |
| 🟠 PARTIAL | Computed but only stored if amplifier layer ran |
| 🚫 EPHEMERIS-MISSING | Code wired correctly, awaiting `.se1` file install |
| ⚪ DESIGNED-NOT-IMPLEMENTED | Mentioned in router / aliases but no compute engine |
| ⛔ NEVER-DESIGNED | No evidence anywhere in code/history |

### 1.1 Lunar / Apogee Family

| Object | Status | Compute Source | Notes |
| ------ | ------ | -------------- | ----- |
| Black Moon Lilith (mean) | ✅ ACTIVE | `swe.MEAN_APOG` (on demand) | Aliases: `lilith`, `bml`, `black moon`, `mean lilith` |
| True Black Moon Lilith | ✅ ACTIVE | `swe.OSCU_APOG` (on demand) | Aliases: `true lilith`, `true black moon` |
| White Moon Selena | ⛔ NOT WIRED | — | No standard swisseph point. Returns clean refusal. |
| Dark Moon Lilith (Waldemath) | ⛔ NOT WIRED | — | Returns clean refusal. |

### 1.2 Asteroids (first-class swisseph constants)

| Object | Status | Compute Source | Notes |
| ------ | ------ | -------------- | ----- |
| Ceres   | ✅ ACTIVE | `swe.CERES` (on demand) | Was `AST_OFFSET+1` before — same result. |
| Pallas  | ✅ ACTIVE | `swe.PALLAS` | Was `AST_OFFSET+2` before. |
| Juno    | 🟡 **RECONNECTED** | `swe.JUNO` | Was **completely missing** from `_COMPUTE_ON_DEMAND` and only worked when the chart-builder amplifier layer happened to have populated `planets.Juno`. Charts built before that layer (e.g. Pete's) returned `no_path_to_compute`. |
| Vesta   | ✅ ACTIVE | `swe.VESTA` | Was `AST_OFFSET+4` before. |
| Pholus  | 🟡 **ADDED** | `swe.PHOLUS` | Bonus — centaur available in standard ephemeris. |

### 1.3 Named asteroids (require additional `.se1` files)

| Object | Status | Required File | Notes |
| ------ | ------ | ------------- | ----- |
| Eros    | 🚫 EPHEMERIS-MISSING | `se00433s.se1` | Dispatcher correct; refuses cleanly with `ephemeris_file_missing` reason. |
| Psyche  | 🚫 EPHEMERIS-MISSING | `se00016s.se1` | Same as above. |
| Astraea | 🚫 EPHEMERIS-MISSING | `se00005s.se1` | Same as above. |
| Hygiea  | 🚫 EPHEMERIS-MISSING | `se00010s.se1` | Same as above. |
| Eris    | 🚫 EPHEMERIS-MISSING | `s136199s.se1` | Same as above. |

### 1.4 Chart Angles

| Object | Status | Compute Source | Notes |
| ------ | ------ | -------------- | ----- |
| Ascendant / Descendant / MC / IC | ✅ ACTIVE | Stored in `angles.{asc,dc,mc,ic}` | Confirmed in Pete's chart. |
| Vertex | 🟡 **RECONNECTED** | `swe.houses_ex(... Placidus + sidereal)` | Previously only worked if the **amplifier** had populated `angles.vertex`. Legacy charts now compute on demand from stored JD + coordinates. |
| Anti-Vertex | 🟡 **RECONNECTED** | Vertex + 180° | Symmetric derivation; previously also only available via amplifier. |

### 1.5 Nodes & Karmic Points

| Object | Status | Source | Notes |
| ------ | ------ | ------ | ----- |
| North Node | ✅ ACTIVE | Stored in `planets.North Node` | True Node by default. |
| South Node | ✅ ACTIVE | Stored (or derived NN + 180°) | |
| Mean Node | ⚪ DESIGNED-NOT-USED | Available via `swe.MEAN_NODE` but no surface uses it. |

### 1.6 Healing / Wound Points

| Object | Status | Source | Notes |
| ------ | ------ | ------ | ----- |
| Chiron | ✅ ACTIVE | Stored in `planets.Chiron` | Confirmed in Pete's chart. |

### 1.7 Arabic Parts / Lots (sect-aware formula)

| Object | Status | Compute | Notes |
| ------ | ------ | ------- | ----- |
| Lot of Fortune | ✅ ACTIVE | `_compute_lot()` — sect-aware | Aliases: `part of fortune`, `pars fortuna`, `fortuna` |
| Lot of Spirit  | ✅ ACTIVE | `_compute_lot()` — sect-aware | |
| Lot of Eros / Necessity / Courage / Victory / Nemesis / Basis / Marriage / Children / Father / Mother / Siblings / Career / Profession / Wealth / Death / Illness / Exaltation | ⛔ NOT WIRED | — | Recognised by resolver, returns clean refusal. Designed-but-never-implemented. |

### 1.8 Hellenistic & Modern Asteroids referenced in aliases

| Object | Status | Notes |
| ------ | ------ | ----- |
| Eros (asteroid 433) | 🚫 EPHEMERIS-MISSING | See 1.3 |
| Psyche (asteroid 16) | 🚫 EPHEMERIS-MISSING | See 1.3 |

### 1.9 Chart Patterns (intent router knows them; no detection engine)

| Pattern | Status | Notes |
| ------- | ------ | ----- |
| Stellium | ✅ ACTIVE | Detected in `astrology_today_v4_behavior.py` (`has_stellium`), used in timeline modulation. |
| Yod | ⚪ DESIGNED-NOT-IMPLEMENTED | Mentioned only as a routing term in `intent_router_v2.py`. No detection logic. |
| Kite | ⚪ DESIGNED-NOT-IMPLEMENTED | Same as Yod. |
| Grand Trine | ⚪ DESIGNED-NOT-IMPLEMENTED | Same. |
| Grand Cross | ⚪ DESIGNED-NOT-IMPLEMENTED | Same. |
| T-Square | ⚪ DESIGNED-NOT-IMPLEMENTED | Same. |
| Mutual Reception | ⛔ NEVER-DESIGNED | No mentions anywhere. |
| Dispositor Chains | ⛔ NEVER-DESIGNED | "disposition" appears only as relationship vocabulary. |
| Critical Degrees | ⛔ NEVER-DESIGNED | No mentions in backend. |
| Fixed Stars (Regulus / Spica / Algol / Sirius) | ⚪ DESIGNED-NOT-IMPLEMENTED | Listed in `intent_router_v2.py` as recognisable user vocabulary; no engine. |
| Out-of-Bounds (declination beyond ±23°27′) | ⚪ DESIGNED-NOT-IMPLEMENTED | Listed in intent router (`oob`); no declination compute. |
| Stationing Planets | ⚪ DESIGNED-NOT-IMPLEMENTED | Mentioned in `keystone_lens_explanations.py` content blurb only; no detection of stationarity. |
| Decans | ✅ ACTIVE | `services/decan_engine.py` — Sun decan modulation feeds `cross_domain_engine` + `life_interpreter` prompts. |
| Karma (as object) | ⛔ NEVER-DESIGNED in astrology | Only appears in HD reflection content. |

---

## 2. Historical Recovery Audit (Task 2.5)

Per the user's directive *"Do not return 'not found' unless the repository
search includes active code, git history, archived files, prompt templates,
migrations, and disabled/unused services. If evidence is incomplete, label
it 'not yet found,' not 'never existed.'"*

Searches performed across the entire repository (3,932 commits, single
branch `main`, no archived branches):

* `git log --all -S "<term>"` on each object name
* `git log --all --diff-filter=A` for first-introduction commits
* `grep -rni` across `backend/`, `frontend/`, `audit_reports/`, `docs/`, prompt templates, migration files, disabled feature flags, and `tests/`.

### Status legend

* **A — Never designed**
* **B — Designed but never implemented**
* **C — Implemented then removed**
* **D — Implemented but orphaned (dead path)**
* **E — Implemented and active**

| Object | Status | First Found Location | Last Active Location | Notes |
| ------ | ------ | -------------------- | -------------------- | ----- |
| Vertex | **E** | `calculations/astrology.py` § "RELATIONSHIP-FIELD AMPLIFIERS" (~commit `749ba245`) | `services/natal_object_engine.py` (this fix) + `relationship_field.py:_get_vertex` | Previously only available when the amplifier ran during chart build. Reconnected via on-demand compute. |
| Anti-Vertex | **E** | `calculations/astrology.py` (same block as Vertex) | `services/natal_object_engine.py` (this fix) | Computed as Vertex + 180°. |
| Juno | **E** | `calculations/astrology.py` § "RELATIONSHIP-FIELD AMPLIFIERS" | `services/natal_object_engine.py` (this fix) + `relationship_field.compute_juno_amplifier` + `astrology_relationship_restory_v1.py` | Was completely absent from `_COMPUTE_ON_DEMAND`. Reconnected. |
| Chiron | **E** | `calculations/astrology.py` ≥ commit `2dc05eba` | Stored in `planets.Chiron` for all charts | Active end-to-end. |
| Lilith (mean) | **E** | `services/natal_object_engine.py` ≥ commit `a6b97f58` | Same | Computed on demand. |
| True Lilith | **E** | `services/natal_object_engine.py` | Same | Computed on demand. |
| Selena (White Moon) | **A** | Only as alias in resolver | — | Explicit `_NOT_WIRED` entry. No swisseph point exists. |
| Part of Fortune | **E** | `services/natal_object_engine.py` ≥ commit `57c4dd76` | Sect-aware formula | Active. |
| Part of Spirit | **E** | Same as Fortune | Same | Active. |
| Lot of Eros / Necessity / Courage / Victory / Nemesis / Basis / Marriage / Children / Father / Mother / Siblings / Career / Profession / Wealth / Death / Illness / Exaltation | **B** | Aliases + `_NOT_WIRED` in `services/natal_object_engine.py` | — | Each is recognised as a name but has no compute formula. **Designed (vocabulary)** but **never implemented (math)**. |
| Eros (asteroid 433) | **B** (compute path exists; ephemeris missing) | Resolver in `services/natal_object_engine.py` | `services/transit_object_engine.py:140` | Dispatcher would compute it if the `se00433s.se1` file were installed. |
| Psyche (asteroid 16) | **B** (same as Eros) | Resolver | — | `se00016s.se1` missing. |
| Karma | **A** (no astrology meaning) | Only as HD reflection content in `frontend/web_dist/_expo/...` | — | "Karma" appears only inside relationship/HD copy, never as an astrological point. |
| Decans | **E** | `services/decan_engine.py` ≥ commit `3b88d29d` | `cross_domain_engine.py:633`, `life_interpreter.py:1197`, `server.py:25952` | Sun-decan modulator. ACTIVE. |
| Dispositor Chains | **A** | — | — | Word "dispositor" never appears in astrology context. |
| Mutual Receptions | **A** | — | — | No reference in repository. |
| Critical Degrees | **A** | — | — | No reference. |
| Out-of-Bounds / OOB | **B** (recognised, no engine) | `intent_router_v2.py:119` | — | Listed only as a user-vocabulary term that routes to the astrology lens. No declination compute layer. |
| Stationing Planets | **B** (recognised, no detection) | `keystone_lens_explanations.py:87` (single content blurb) | — | Listed in the lens copy as a possible signal but no detection of station-direct/-retrograde from chart data. |
| Yod / Kite / Grand Trine / Grand Cross / T-Square | **B** (recognised, no detection) | `intent_router_v2.py:118-119` | — | Routing-only. No pattern-detection engine. |
| Stellium | **E** | `astrology_today_v4_behavior.py:250` | Same + `timeline_modulation.py:217` | Active in daily-engine sign-concentration computation. |
| Fixed Stars (Regulus / Spica / Algol / Sirius) | **B** | `intent_router_v2.py:119` (`fixed star` regex) | — | Routing-only. No fixed-star ephemeris loader. |

---

## 3. Regression Report

How the dropout happened and exactly which line of code caused it.

### 3.1 Smoking gun: legacy charts predate the amplifier layer

Commit `749ba245` added the "RELATIONSHIP-FIELD AMPLIFIERS" block to
`calculations/astrology.py` (lines 805–871). That block:

* Reads `swe.JUNO` and writes `planets["Juno"]` into the chart payload.
* Calls `swe.houses_ex(...)` and writes `angles["vertex"]` + `angles["anti_vertex"]`.

Charts created **before** that commit (or by a code path that doesn't
invoke the amplifier — e.g. cached chart documents, V-A migrated charts,
the `astrology_engine_version: 1.0` paths) **do not carry** Juno / Vertex
/ Anti-Vertex fields. There is no idempotent "backfill on read" step.

### 3.2 First-order dropout — `natal_object_engine.py`

The dispatcher in `compute_natal_object()` does this for any object it
recognises:

1. Try `_read_stored_natal_object(chart, canon)` — returns `None` for
   legacy charts that don't have Juno / Vertex stored.
2. If the canonical name is in `_FORMULA_OBJECTS` → compute (Lots).
3. If the canonical name is in `_COMPUTE_ON_DEMAND` → compute via swisseph.
4. Else → return `no_path_to_compute` ("not wired" message).

**The bug**: `Juno` was **NOT** in `_COMPUTE_ON_DEMAND`. `Vertex` and
`Anti-Vertex` were not in any compute path at all. So on legacy charts:

```
canon=Juno      → step 1 returns None → step 2 no match → step 3 no match → no_path_to_compute
canon=Vertex    → step 1 returns None → not in _FORMULA / _COMPUTE_ON_DEMAND → no_path_to_compute
canon=Anti-Vertex → same as Vertex.
```

The chat layer then surfaced the verbatim engine message:

> "Vertex is not wired into the astrology engine yet."

…even though the chart-builder fully understands how to compute it.

### 3.3 Second-order dropout — interpretation surfaces

The Relationship surfaces (`relationship_field.py`,
`astrology_relationship_restory_v1.py`, `pressure_topology_engine.py`)
read Juno / Vertex **directly** from the stored chart dict and have **no
fallback** to the natal-object engine. So even after fixing the chat
dispatcher, the Why-This-Person-Matters tray and the relationship-field
amplifier would have stayed empty for the same legacy charts.

### 3.4 Tertiary dropout — house-cusp shape mismatch

`house_inventory_engine._house_of` and the original Lot-of-Fortune /
Lilith compute helpers tried to look up cusps via:

```python
cusps = astro.get("houses") or astro.get("house_cusps")
```

But the canonical stored shape is `astro.houses` = **dict** (with a
`cusps` key inside), not a list. So `get_house_for_planet(sid, cusps)`
received a dict and silently failed inside the `except Exception: pass`
in some paths — meaning newly-computed Lilith / Lot / Vertex placements
came back with `house=None`. Fixed with a tolerant `_extract_cusps_list`
helper.

---

## 4. Reconnection Plan — Applied Fixes

### 4.1 `services/natal_object_engine.py`

| Change | Effect |
| ------ | ------ |
| Bumped `BUILD_MARKER` → `astrology-chat-v5-advanced-object-reconnect` | Audit trail in chat debug. |
| Replaced `AST_OFFSET + N` for major asteroids with direct `swe.{CERES,PALLAS,JUNO,VESTA}` constants | Adds **Juno** to compute-on-demand and is more reliable across pyswisseph versions. |
| Added **Pholus** (`swe.PHOLUS`) | Bonus centaur, no extra ephemeris needed. |
| Added `_compute_natal_vertex(chart, anti=False)` | Computes Vertex / Anti-Vertex on-demand via `swe.houses_ex` using stored `metadata.julian_day` + `metadata.coordinates`. |
| Added Vertex/Anti-Vertex dispatcher branch in `compute_natal_object` | Closes the previous `no_path_to_compute` fall-through. |
| Added `_extract_cusps_list(astro)` helper and routed all callers through it | Lot / Lilith / Vertex placements now correctly receive a `house` value. |
| Added `ensure_advanced_objects(chart)` | Side-effect-free chart hydration helper so legacy charts gain `planets.Juno` + `angles.vertex/anti_vertex` at read time. |

### 4.2 Surface wiring — lazy hydration calls

One-line `ensure_advanced_objects(chart)` calls added at the public
entry-points of:

* `services/astrology_relationship_restory_v1.py::maybe_compute_restory`
  — Why-This-Person-Matters evidence tray now uses Juno + Vertex.
* `services/relationship_field.py::build_relationship_field`
  — Juno-amplifier and Vertex-amplifier corroboration paths now fire on
  legacy charts.
* `services/pressure_topology_engine.py::build_pressure_topology`
  — Juno now contributes to body-weight pressure mapping.

### 4.3 `services/house_inventory_engine.py`

* Added **Anti-Vertex** to `_INVENTORY_TARGETS`.
* Rewrote `_house_of` to tolerate **all three** chart-cusp shapes
  (`astro.houses.cusps`, `astro.house_cusps`, list-of-formatted-cusps).

### 4.4 Chat path (unchanged, now functional)

`routers/mirror_chat.py` already routes `mode_label == "natal_object"`
through `compute_natal_object(...)` and `build_natal_object_proof_block(...)`.
With the engine reconnected, Vertex / Anti-Vertex / Juno queries now
flow end-to-end through the same proof block contract as Chiron.

### 4.5 What was **NOT** activated this pass (per user directive)

* **Timeline narrative generation** for advanced objects — *NOT YET*.
  The objects are now accessible to the Timeline engine via the
  natal_object_engine + ensure_advanced_objects helper. Narrative
  generation for transits-to-Vertex / Juno-return / etc. is parked
  pending an explicit interpretation framework.

### 4.6 What still requires user action

* **Ephemeris file install** for Eros, Psyche, Hygiea, Astraea, Eris.
  Astrodienst's public mirror no longer exposes these in a clean
  download path; you'll likely need to extract them from the Swiss
  Ephemeris source tarball. Until then the engine reports
  `ephemeris_file_missing` (clean refusal).

### 4.7 Test coverage (NEW)

`services/test_natal_object_reconnection.py` — 17 tests:

* Resolver coverage of all advanced-object aliases.
* Vertex / Anti-Vertex compute-on-demand on a legacy-shaped fixture.
* Juno compute-on-demand.
* Pholus compute-on-demand.
* Clean refusal for ephemeris-missing asteroids (Eros, Psyche, Hygiea, Astraea, Eris).
* `Selena` not-wired refusal preserved.
* `ensure_advanced_objects` hydration + idempotency + non-mutation.

All 17 pass. No regressions in the 63 pre-existing tests that ran cleanly
in the sweep (the 6 failures were pre-existing live-HTTP tests that
require an external preview URL — unrelated to this work).

---

## 5. Recommended Priority Order

Ranked by user-visible value vs. implementation effort.

### Tier 1 — Already shipped this audit (P0, done)

1. **Juno / Vertex / Anti-Vertex reconnect** in chat, story, relationship,
   topology, and house inventory. Highest user-visible impact: closes
   the "not wired" false-negative on Pete and every legacy chart.

### Tier 2 — Next quick wins (P1)

2. **Install missing asteroid ephemeris files** (Eros, Psyche, Hygiea,
   Astraea, Eris). Pure infrastructure change. Unlocks 5 named asteroids
   without any code change.
3. **Backfill `planets.Juno`, `angles.vertex`, `angles.anti_vertex`**
   into existing chart documents in a one-shot script (NOT a schema
   migration — fields already exist in the schema; just rerun the
   amplifier and persist). Eliminates the runtime hydration overhead
   forever.

### Tier 3 — Implement what's only routed but never built (P2)

4. **Out-of-Bounds detector**: planet declination computation +
   `is_out_of_bounds` flag. Small engine; intent router already knows
   the term.
5. **Stationing detector**: read planet speed (already present in chart
   `planets.<X>.speed`) and flag where `|speed| < threshold`. Trivial
   addition; activates the existing keystone-lens content blurb.
6. **Mean Node opt-in alias** (alternative to True Node for users who
   prefer it). Engine already has `swe.MEAN_NODE`.

### Tier 4 — New design + new engines (P3)

7. **Chart pattern detector** for Yod / Kite / Grand Trine / Grand Cross
   / T-Square. Walks the existing aspect list. Surfaces as a new
   `chart_patterns` envelope. The intent router and lens-term regex
   already match these terms.
8. **Mutual Reception + Dispositor Chains**. Requires domicile /
   exaltation tables; computationally simple but interpretively rich.
   Hellenistic depth.
9. **Critical Degrees overlay**. 0°, 13°, 26° of cardinal signs; 8°/9°
   of fixed; 4° of mutable. A flag on each placement.
10. **Fixed-star conjunctions** (Regulus, Spica, Algol, Sirius). Needs a
    static catalogue or `sefstars.txt`. Largest perceived-magic payoff
    of the bunch.

### Tier 5 — Symbolic / esoteric extensions (P4)

11. **Asteroid Karma (asteroid 3811)** — if the user truly wants a
    "Karma" body. Different ephemeris file (`s003811s.se1`).
12. **Hellenistic lots** (Eros, Necessity, Courage, …) — formulas
    exist in Valens; only need encoding into `_FORMULA_OBJECTS`.
13. **Vedic upagraha / Gulika / Mandi**. Distinct mathematical layer.

---

## Appendix A — Field-by-field verification on Pete's chart

After the fix:

```
Vertex          → 0°Virgo       (lon=142.13, house 9)   source: swisseph_houses_ex_on_demand
Anti-Vertex     → 3°Pisces      (lon=322.13, house 3)   source: swisseph_houses_ex_on_demand
Juno            → 47°Virgo      (lon=189.35, house 10)  source: swisseph_on_demand
Pholus          → 25°Capricorn  (lon=294.61, house 2)   source: swisseph_on_demand
Pallas          → 33°Leo        (lon=136.50, house 9)   source: swisseph_on_demand
Vesta           → 18°Aquarius   (lon=313.80, house 2)   source: swisseph_on_demand
Lot of Fortune  → 1°Ophiuchus   (lon=233.41, house 11)  source: formula
Lot of Spirit   → 17°Capricorn  (lon=286.44, house 2)   source: formula
Lilith (mean)   → 0°Taurus      (lon=19.93,  house 5)   source: swisseph_on_demand
True Lilith     → 4°Taurus      (lon=24.26,  house 5)   source: swisseph_on_demand
```

(Sign-width irregularities — e.g. "47°Virgo" — are correct under the
**True Sidereal-M Midpoint** zodiac variant: signs in this canon have
non-uniform widths. This is **not** an output bug; it's a property of
the user's chosen sign-attribution system.)

House inventory:

```
9th house  → Uranus, Pluto, Earth, Pallas, Vertex
10th house → South Node, Midheaven, Juno, Ceres
```

— Vertex + Juno are now present where they belong.

---

## Appendix B — Files Touched

```
backend/services/natal_object_engine.py                    (core fix + ensure_advanced_objects helper)
backend/services/astrology_relationship_restory_v1.py      (hydration at entry)
backend/services/relationship_field.py                      (hydration at entry)
backend/services/pressure_topology_engine.py                (hydration at entry)
backend/services/house_inventory_engine.py                  (Anti-Vertex target + cusps-shape tolerance)
backend/services/test_natal_object_reconnection.py          (NEW — 17 tests)
backend/audit_reports/MIRROR_ASTROLOGY_INVENTORY_AUDIT.md   (this report)
```

— end report —
