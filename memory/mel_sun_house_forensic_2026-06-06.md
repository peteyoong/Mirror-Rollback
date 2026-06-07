# Forensic — Mel's Sun House Assignment
**Date:** 2026-06-06 · **Mode:** Read-only · **Subject:** Melissa Tan
- Birth: 13 Jul 1981 07:25 local (+07:30) — Melaka, Malaysia (2.1896° N, 102.2501° E)
- UTC: 1981-07-12 23:55:00  · JD 2444798.4965

> ⚠️ **Important up-front correction.** Mirror's chart for Mel currently stores the **Sun in House 12** — not House 11. The user's question premise ("Why is Sun classified as House 11?") does not match what Mirror's engine actually returns. The forensic below shows where Mirror does place the Sun and why; if a UI surface is rendering "House 11" anywhere, that is a downstream display bug to chase separately.

---

## 1. Exact sidereal longitude of Sun
```
Sun sidereal longitude      = 79.48916°
Sun tropical longitude      = 110.51085°   (sidereal + SVP 31.2836°)
Sun sign (Mirror, midpoint) = Gemini 22°21′05″
Sun stored speed            = 0.0°/day (not tracked in natal)
```

## 2. Exact sidereal longitude of ASC
```
ASC sidereal longitude  = 89.10342°
ASC tropical longitude  = 120.38702°
ASC sign (Mirror)       = Cancer 4°05′49″
```
*Note:* In a fixed-30° sidereal frame `ASC = 89.10°` would be 29°06′ Gemini; Mirror's *display* label is Cancer 4° because sign attribution uses the variable-width True Sidereal-M Midpoint table while house cusps use sidereal longitudes. **Both labels describe the same point — 89.10° sidereal.**

## 3. All 12 house cusps Mirror currently uses
House system = **Equal** (sidereal). 30° steps starting at sidereal ASC.

| House | Sidereal cusp (°) | Mirror display label |
|------:|------------------:|----------------------|
|  1 (ASC) |  89.10342 | 4° Cancer |
|  2 | 119.10342 | 8° Leo |
|  3 | 149.10342 | 4° Virgo |
|  4 (IC) | 179.10342 | 34° Virgo¹ |
|  5 | 209.10342 | 27° Libra |
|  6 | 239.10342 | 1° Sagittarius |
|  7 (DC) | 269.10342 | 1° Capricorn |
|  8 | 299.10342 | 3° Aquarius |
|  9 | 329.10342 | 5° Pisces |
| 10 (MC²) | 359.10342 | 4° Aries |
| **11** | **29.10342** | **3° Taurus** |
| **12** | **59.10342** | **2° Gemini** |
|  ⤴ wraps back to H1 at 89.10342 |  |  |

¹ "34° Virgo" reads >30° because Mirror's midpoint Virgo band is wider than 30°; the cusp's sidereal value (179.10°) is correct.
² Mirror's house system here is **Equal**, so the printed "MC" angle is independent of the 10th-house cusp (cf. Placidus where MC = 10th cusp).

## 4. Formula Mirror uses to assign houses

```python
# from calculations/astrology.py  (Equal-house path, unchanged)
def equal_house_cusps(asc_sidereal):
    return [(asc_sidereal + 30.0 * i) % 360.0 for i in range(12)]

def assign_house(body_sidereal, cusps):
    """Return 1..12. Body falls in house n iff its longitude lies in
    the half-open arc [cusps[n-1], cusps[n]) measured along the
    direction of zodiac motion. Houses wrap modulo 360°."""
    for n in range(12):
        a = cusps[n]
        b = cusps[(n + 1) % 12]
        # normalize the body's longitude relative to cusp a
        d = (body_sidereal - a) % 360.0
        if 0.0 <= d < 30.0:        # equal houses: width is always 30°
            return n + 1
    return 12                       # defensive fallback
```

- Both inputs (the body's longitude and the cusps) live in the **sidereal** frame (SVP 31.2836°, J2000).
- No tropical fallback. No midpoint sign math is involved in the house decision — sign attribution is a *separate* downstream label.

## 5. Why Sun is classified as House **12** (not 11)

```
Sun sidereal   =  79.48916°
H11 cusp       =  29.10342°   →   width 30°   →   ends at 59.10342°
H12 cusp       =  59.10342°   →   width 30°   →   ends at 89.10342° (= H1)

(Sun − H12 cusp) mod 360°  =  20.38574°   →   0 ≤ d < 30°  →  ASSIGN H12
(Sun − H11 cusp) mod 360°  =  50.38574°   →   d ≥ 30°       →  not H11
```

Sun is **20.39° INSIDE House 12** and 9.61° away from re-crossing the Ascendant (H1). It is unambiguously House 12.

## 6. Distance from Sun to the 11/12 cusp

The 11/12 cusp is **59.10342° sidereal** ( = 2°06′12″ Gemini in Mirror's midpoint label, or 29°06′ Taurus in fixed-30° sidereal terms).

```
Sun − 11/12_cusp  =  79.48916° − 59.10342°  =  20.38574°
                  =  20° 23′ 09″  past the 11→12 boundary, in the 12th house direction
```

## 7. Would GM's printed longitude (Gemini 22°54′) put Sun into House 12?

GM's printed natal Sun for Mel is **Gemini 22°54′** (33′ later than Mirror's Gemini 22°21′).

Translating GM's value through Mirror's house grid:

```
GM Sun  =  Gemini 22°54′
Mirror midpoint Gemini starts at tropical 88.16°
GM Sun tropical      =  88.16 + 22.90  =  111.06°
GM Sun sidereal      =  111.06 − 31.28 =   79.77°
```

Apply Mirror's house assignment:
```
GM_Sun_sid − H12_cusp = 79.77 − 59.10 = 20.67°  →  0 ≤ d < 30°  →  HOUSE 12
GM_Sun_sid − H11_cusp = 79.77 − 29.10 = 50.67°  →  d ≥ 30°       →  NOT H11
```

**Answer: YES.** GM's stated longitude (Gemini 22°54′) is only 33′ further along the ecliptic than Mirror's current Sun and lands in the same equal-house bucket — **House 12**.

Both 22°21′ Gemini and 22°54′ Gemini are roughly 20° INTO the 12th house with ~9°-10° remaining before the Ascendant. There is no realistic perturbation of Mel's Sun longitude (within ±10°) that would move it into House 11 under the current Equal-house system anchored to sidereal ASC 89.10°.

---

## Summary

| Item | Value |
|---|---|
| Mirror Sun (sidereal) | 79.489° |
| Mirror ASC (sidereal) | 89.103° |
| House system | Equal — 30° steps from sidereal ASC |
| Mirror assigns Sun to | **House 12** |
| Distance Sun → 11/12 cusp | **20°23′** *into* House 12 |
| GM's "Gemini 22°54′" under Mirror's houses | Also House 12 |
| User's premise ("Sun classified as 11") | **Not matched by stored chart data** — needs UI source check |

No chart math, ayanamsa, house system, code, or DB record has been modified by this audit.

*Cross-reference:* The previous GM-Forensic-V2 audit (2026-05-31) established that GM is per-user configurable (Equal for Pete & Mel, Placidus for Ana) and that GM's "True Sidereal-M (Midpoint)" sign attribution diverges from Mirror's Variant B Midpoint by a few arcminutes. The 33′ Sun discrepancy here is consistent with that earlier finding — same root cause, no new bug.
