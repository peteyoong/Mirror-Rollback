# PERSONAL MIRROR — AUDIT
Date: 2026-07-22
Scope: Session-1 audit of the 5 existing lenses + hidden Gene Keys
Author: main agent (read-only inspection, no code changes)
Test user: pete@pulsifi.me (user_id 697f0c6abf35c0528ff06954)

---

## 1. ROUTE MAP (frontend)

| Lens              | Route                                           | Component                                              |
|-------------------|-------------------------------------------------|--------------------------------------------------------|
| Lens library      | `/(tabs)/lenses`                                | `app/(tabs)/lenses.tsx` (270 LOC)                      |
| True Sidereal     | `/lenses/astrology`                             | `app/lenses/[lens].tsx` (1244 LOC, generic wrapper)    |
| Human Design      | `/lenses/human_design`                          | same wrapper, delegates to `HumanDesignLensView.tsx`   |
| Numerology        | `/lenses/numerology`                            | same wrapper                                            |
| BaZi              | `/lenses/bazi`                                  | same wrapper                                            |
| Enneagram         | `/enneagram`                                    | separate flow (assessment-first)                        |
| **Gene Keys**     | ❌ **no library entry** — hidden inside HD Deep Dive as "3 arcs" |

Header bug: `(tabs)/lenses.tsx:104` reads `"Four perspectives for understanding yourself"` but 5 lenses render (or 4 if Consciousness FF off — still says "Four" hardcoded).

## 2. KEY BACKEND ENDPOINTS

| Endpoint                                                     | File / line             | Notes                                                     |
|--------------------------------------------------------------|-------------------------|-----------------------------------------------------------|
| `GET /api/lenses`                                            | server.py               | Static lens catalogue                                     |
| `GET /api/human-design/summary/{user_id}`                    | server.py:16828         | Type / Authority / Profile / Definition                   |
| `GET /api/human-design/centers/{user_id}`                    | server.py:18457         | 9 centres w/ gates + narratives                           |
| `GET /api/human-design/deep-dive/{user_id}`                  | server.py:17720         | Full HD narrative payload                                 |
| `GET /api/human-design/mechanics/{user_id}`                  | server.py:16561         | Raw activations                                            |
| `GET /api/human-design/today-diagnosis/{user_id}`            | server.py:17075         | Timing overlay                                             |
| `GET /api/astrology/chart/{user_id}`                         | server.py:15003         | Full natal chart (planets/angles/houses/aspects)          |
| `GET /api/astrology/summary/{user_id}`                       | server.py:11181         | Sun / Moon / Asc summary                                   |
| `GET /api/astrology/today-v4/{user_id}`                      | server.py:11484         | Current transits                                            |
| `GET /api/astrology/constellations/{user_id}`                | server.py:15281         | Variant-A 13-sign widths                                    |
| Numerology / BaZi / Enneagram endpoints                      | (to inventory in Sess-2) |                                                            |

## 3. CONCRETE BUGS CONFIRMED FROM LIVE PAYLOAD (Pete)

### 3a. Lens library says "Four perspectives" while 5 render
`/app/frontend/app/(tabs)/lenses.tsx:104` — hardcoded string. ✅ Session-1 fix scope.

### 3b. HD centre naming — `"G Center Center"` duplication
Backend `GET /human-design/centers/697f0c6abf35c0528ff06954` returns:
```
center_name = "G Center"     display_name = "G / Identity"
center_name = "Ego"          display_name = "Heart / Ego"
```
Frontend `HumanDesignLensView.tsx:2207` renders `<Card title="${centerName} Center" ...>` — so when `centerName === "G Center"` we render **"G Center Center"**. ✅ Session-1 fix scope.

### 3c. Ego/Heart shown as "both defined and undefined"
Root cause identified across two files:

1. **Backend duplication risk**: `centers[]` list from `/human-design/centers/{id}` includes `Ego` (defined=True). Some downstream renderers ALSO consume a legacy `heart` key. If any renderer maps both `Ego` AND `heart` to the same UI slot, we get contradictory display.

2. **Mirror-card dictionary in FE**: `humanDesignMirrorCards.ts:540` uses key `'heart'` — both a `defined` and `undefined` copy — but SOME code paths look up BOTH and render both if the guard is broken.

Needs live reproduction in playwright to isolate the exact render path. ✅ Session-1 fix scope (after reproduction).

### 3d. Astrology degrees > 30° — **POLICY QUESTION, NOT A BUG**

Live pull from `/api/astrology/chart/697f0c6abf35c0528ff06954`:
```
Pluto:  sign=Leo    deg=37.0    lon=140.19
MC:     sign=Virgo  deg=28.24   lon=169.84
IC:     sign=Pisces deg=31.83   lon=349.84
```

**Math check**: Under Variant-A True Sidereal:
- Leo constellation start = 140.19 − 37.00 = 103.19°; end (=Virgo start) = 141.60°. Leo width = **38.41°**. Pluto at 37° is **valid** within Leo's 38.41° window.
- Pisces width ≈ 37.6° (start 318.01, end ≈ 355.6). IC at 31.83° into Pisces is **valid**.

**Conflict with previous work**: The handoff summary explicitly states — *"Variant A Widths: Constellations have real astronomical widths (Virgo ~49.71°). NEVER clamp degree calculations to 30.0 under Variant A. 35° Virgo is valid."*

**User's Session-1 spec says**: *"Every sign-relative degree must be normalised to 0°00′–29°59′."*

These are mutually exclusive. This is a **design decision** — not a bug in the calculation. Three options:

| Option | Description | Impact |
|--------|-------------|--------|
| **A** | Keep Variant-A raw constellation-relative degree, add a label "of Leo's 38.4° span" everywhere. | Preserves methodology; educates user. |
| **B** | Ship a NEW `degree_normalized` field = `(rel_deg / constellation_width) × 30`, display that as primary, keep raw in drill-down. | Familiar-looking display, preserves math. |
| **C** | Switch back to tropical 30° signs. | Contradicts the entire Variant-A design that was ratified last session. |

**⚠️ BLOCKED**: Session-1 cannot ship the Phase 5A fix until you pick A / B / C. My recommendation is **B** (dual field, normalized-by-default).

### 3e. Astrology stored longitude anomalies
- `Moon: sign=Aries deg=11.06 lon=11.06` — deg == lon, which means the code stored Aries-relative degree AS the absolute longitude, or the ayanamsa was 0 for the Moon. Needs deeper inspection in Session-2.
- North Node deg=29.83 lon=347.84 → sign=Pisces (but 347.84 is definitely Pisces territory; deg=29.83 is right at the edge).
- Pluto row: `deg=37.0` — this ONE value fails any "0–30" validation → covered by the test in §6 below (regardless of Option A/B/C above).

### 3f. Backend caching + generic centre boilerplate
`HumanDesignLensView.tsx:2175-2183` has the exact "Your X centre is defined—this is consistent energy that is always present" boilerplate you flagged. It's a client-side fallback used when `center.what_this_is` is null. Currently `center.what_this_is` IS populated in Pete's payload for Head/Ajna, but if it were null, the boilerplate would leak. ✅ Session-1: add a Phase-11 test that flags identical fallback strings across centres (out of scope for this session's fix, in scope for the Phase-11 test skeleton).

### 3g. Astrology "holds things so tightly they can't breathe" claim
Not reproduced yet — needs Playwright trace on the deep-dive route. Marked for Session-2 investigation.

### 3h. Gene Keys visibility
Currently rendered INSIDE `HumanDesignLensView.tsx` (search: "3 arcs" / "Life's Work" / "Radiance"). No standalone lens card, no library entry. Session-2+ scope (full new lens).

### 3i. Numerology "almost entirely a Life Path 11 reading" (deep-dive)
Not reproduced yet — needs Playwright trace. Session-2 scope.

### 3j. BaZi reductive language: "calculating underneath / stubborn beyond reason / clever enough to trick themselves"
grep confirms in `bazi_*.py` narrative files. Session-2 rewrite scope.

## 4. INFORMATION AVAILABLE BUT NOT DISPLAYED (per lens)

Documented in the payload live pull, to be fixed in Session-2 lens rebuilds.

| Lens | Available but hidden |
|------|----------------------|
| HD | Personality/Design planetary activations per planet (full 13-row table), gate lines, colour/tone/base for variables (may not be reliable — see next row), incarnation cross full, split-definition sub-classification (small/wide/triple), hanging gates per centre |
| HD Variables/PHS | The strings "wrong acoustics" / "wrong lighting" / "distance creates confusion" ARE present in the frontend template but their calculation provenance is UNVERIFIED — flagged for Session-2 audit against the source engine |
| Astrology | Aspect patterns (grand trine, T-square, yod), house rulers, dispositor tree, mutual receptions, chart-ruler chain, angular strength scores, element/modality balance percentages |
| Numerology | Maturity Number, Pinnacle series, Challenge series, Personal Year/Month/Day, Karmic Lessons, Karmic Debts |
| Enneagram | Assessment score breakdown (why "High confidence"), instinctual subtype status (assessed vs inferred), tritype status (assessed vs inferred) |
| BaZi | Full 4-pillar table with hidden stems, seasonal command reasoning, useful/favourable elements with method disclosure, luck-pillar phase table, current annual interaction |
| Gene Keys | Activation / Venus / Pearl sequences all 12 gene keys with shadow/gift/siddhi, line-level detail |

## 5. PROMPT / TEMPLATE / FALLBACK / CACHE LOCATIONS

| Concern | Location |
|---------|----------|
| Generic centre fallback | `HumanDesignLensView.tsx:2175-2183` (client-side) |
| HD Ego/Heart card copy | `utils/humanDesignMirrorCards.ts:540-568` |
| Numerology narratives | `backend/services/numerology_narrative*.py` |
| BaZi narratives | `backend/services/bazi_narrative*.py` |
| Astrology narratives | `backend/services/astrology_dynamics*.py` |
| Lens catalogue | `backend/data/lenses.py` or server.py (to verify) |
| Cache | `backend/routers/*.py` — most endpoints check MongoDB stored chart before recompute; `force_refresh=true` param present on several |

## 6. TESTS SESSION-1 WILL ADD

Only the bugs Session-1 actually FIXES get tests. Broader test infra is Phase-11 scope for later sessions.

1. **`test_lens_library_count.py`** — parses `(tabs)/lenses.tsx` and asserts the header noun matches the actual count of enabled lens cards.
2. **`test_hd_center_naming.py`** — hits `/human-design/centers/{id}` for Pete and asserts:
   - No centre `display_name` ends in " Center Center" after FE render
   - No two entries in `centers[]` share the same `display_name` while having opposite `defined` values (guard against the Ego/Heart duplicate-display bug).
3. **`test_astrology_deg_bounds.py`** (**PENDING POLICY CALL — option A/B/C**)
   - Under Option B: assert every planet's `degree_normalized` ∈ [0, 30).
   - Under Option A: assert every planet's `degree` ≤ `constellation_width_by_sign[sign]` and add a label field.
   - The test is written but skipped/xfailed until the decision lands.
4. **`test_astrology_angle_consistency.py`** — asserts MC lon and IC lon differ by exactly 180°, and same for Asc/Desc, within 0.001° tolerance. This is universal — safe to ship regardless of A/B/C.

## 7. RECOMMENDED PATH FOR SESSION-1 FIXES (blocked / go)

| Fix | Blocked on user decision? | Action |
|-----|---------------------------|--------|
| Lens library "Four perspectives" → "Five perspectives" (or dynamic count) | ❌ No | ✅ Ship |
| `"G Center Center"` display bug | ❌ No | ✅ Ship |
| Ego/Heart both defined & undefined (once reproduced) | ❌ No | ✅ Ship |
| Astrology angle consistency test | ❌ No | ✅ Ship |
| Astrology degree normalization | ✅ YES — needs A/B/C decision | ⚠️ Test scaffold only until decision |
| Generic centre fallback dedup test | ❌ No | ✅ Ship (test-only, no fix) |

## 8. WHAT SESSION-1 DELIBERATELY DOES NOT DO

Per the confirmed scope, Session-1 does NOT:

- Rewrite ANY lens narrative or prompt copy
- Add the standalone Gene Keys lens
- Ship a cross-lens synthesis layer
- Modify calculation engines (only display-layer + test-layer changes)
- Expose new backend structural data (Session-2 scope)
- Rewrite the numerology / BaZi / Enneagram deep-dive content
- Address the "holds things so tightly they can't breathe" claim (needs live reproduction)

## 9. SESSION-1 EXIT CRITERIA

Session-1 is complete when:

- ✅ This audit is written
- ✅ Lens count string is fixed
- ✅ "G Center Center" is fixed
- ✅ Ego/Heart contradiction is reproduced and fixed
- ✅ Astrology angle-consistency test is passing
- ⚠️ Astrology degree normalization: **awaiting user's A/B/C decision** — deferred to Session-2 unless decision arrives in-session
- ✅ Test scaffold committed for all four tests
- ✅ Roadmap document written (`personal_mirror_roadmap_2026_07.md`)

## 10. OPEN QUESTIONS FOR USER

1. **Astrology display degrees**: Pick A (raw + label), B (normalized-by-default + raw drill-down), or C (revert to tropical 30°). My recommendation: **B**.
2. **Ego/Heart canonical label**: Backend already emits `display_name = "Heart / Ego"`. FE should use that verbatim everywhere. OK to standardize on **"Heart / Ego"** across the whole product?
3. **Lens library subtitle**: Should the string be dynamic ("Five perspectives") or should it just say "Perspectives" with no count? My recommendation: **dynamic count** so it never drifts again.
