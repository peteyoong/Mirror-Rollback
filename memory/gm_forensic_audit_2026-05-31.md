# GM-ALIGNMENT FORENSIC AUDIT — Cross-User Report
**Date:** 2026-05-31  **Mode:** READ-ONLY (no code changes, no migration)
**Mirror engine state:** GM-Aligned-V2 build (Placidus default) installed but **NOT live recomputed**.

---

## PHASE 1 — VERIFIED GM SETTINGS PER USER

| Source artifact | User | Zodiac dropdown | House label (printed) | Ayanamsa label | Node mode | Other config visible |
|---|---|---|---|---|---|---|
| `Pete_Natal_Chart_new.jpg` | Pete | `True Sidereal-M (Midpoint)` | **`House: Equal`** | `True Sidereal-M (User defined)` | not labeled | "Astro HD Natal + Transits" view |
| `Mel_Natal_Chart_new.jpg`  | Mel  | `True Sidereal-M (Midpoint)` | **`House: Equal`** | `True Sidereal-M (User defined)` | not labeled | Same view |
| `Ana_GM_Astro_HD_chart.pdf` (PDF text layer, verbatim) | Ana | `True Sidereal-M (Midpoint)` | **`House: Placidus`** | `True Sidereal-M (User defined)` | not labeled | Same view |
| `Ana_Natal_chart.jpg` (Z13 view) | Ana | `Zodiac 13 Birth Chart` | **`Equal (Asc = 1st)`** | `Custom( Sharatan( Beta Aries ) ) = 02° Aries` | `True Nodes` | `Topocentric`, `Modern` |

> **Observed-vs-assumed:** Mirror engine currently assumes a **single canonical** house system project-wide. GM however is **per-user configurable** — Pete & Mel are on Equal; Ana's PDF is on Placidus. The previous fork generalised Ana's Placidus to "the GM standard" — that generalisation is **not supported by the other two artifacts**.

---

## STRUCTURAL TEST — house of MC

Mathematical invariant: **under Placidus, MC IS the 10th-house cusp by construction**, so MC must be in house 10. Under Equal, MC can fall anywhere in houses 9–11.

| User | GM table (left "Astro HD Natal") MC house | Compatible with |
|---|---|---|
| Pete | **9** | Equal only |
| Mel  | **9** *(read from left table; right table = 10)* | Equal only (left); Placidus (right) |
| Ana  | **10** *(PDF, Placidus mode set)* | Placidus |

Pete's "MC in house 9" is **mathematically impossible** under Placidus — confirms Pete's GM view is Equal.

---

## PHASE 2 / 3 / 4 — MIRROR vs GM PER USER

Mirror was queried with **both** Equal and Placidus to give a fair comparison.

### PETE (1968-04-01 01:25 UTC+07:30, Petaling Jaya MY)

| Body | Mirror Sign (Equal & Placidus identical) | Mirror Equal-House | Mirror Placidus-House |
|---|---|---|---|
| Sun     | Pisces      | 3 | 3 |
| Moon    | Aries       | 4 | 4 |
| Mercury | Aquarius    | 3 | 3 |
| Venus   | Aquarius    | 3 | 3 |
| Mars    | Aries       | 4 | 4 |
| Jupiter | Leo         | 8 | 8 |
| Saturn  | Pisces      | 3 | 3 |
| Uranus  | Virgo       | 9 | 9 |
| Neptune | Libra       | 11 | 11 |
| Pluto   | Leo         | 9 | 9 |
| Chiron  | Pisces      | 3 | 3 |
| ASC     | **Sagittarius** | 1 | 1 |
| MC      | **Virgo**    | (in 10th sign sequentially) | 10 |

> Mirror ASC = Sagittarius. The OCR of the GM screenshot returned conflicting signs (one pass said "Aries", another said "Leo"). **OCR on these tiny chart glyphs is unreliable** — recommend the user paste the verbatim sign names from the GM left-table rather than rely on extraction.

### MEL (1981-07-13 07:25 UTC+07:30, Melaka MY)

| Body | Mirror Sign | Equal-H | Placidus-H |
|---|---|---|---|
| Sun     | Gemini   | 12 | 12 |
| Moon    | Scorpio  | 5  | 4  |
| Mercury | Gemini   | 11 | 11 |
| Venus   | Cancer   | 1  | 1  |
| Mars    | Taurus   | 11 | 11 |
| Jupiter | Virgo    | 3  | 3  |
| Saturn  | Virgo    | 3  | 3  |
| Uranus  | Libra    | 4  | 4  |
| Neptune | Scorpio  | 5  | 5  |
| Pluto   | Virgo    | 3  | 3  |
| Chiron  | Aries    | 10 | 10 |
| ASC     | **Cancer**  | 1 | 1 |
| MC      | **Aries**   | (10th sign sequentially) | 10 |

> Equal vs Placidus differ only for **Moon (5 vs 4)** in Mel's chart — boundary case.

### ANA (1983-05-03 08:20 UTC-03:00, San Miguel AR)

| Body | Mirror Sign | Equal-H | Placidus-H |
|---|---|---|---|
| Sun     | Aries        | 12 | 12 |
| Moon    | Sagittarius  | 9  | 8  |
| Mercury | Aries        | 1  | 1  |
| Venus   | Taurus       | 2  | 2  |
| Mars    | Aries        | 12 | 12 |
| Jupiter | Scorpio      | 7  | 7  |
| Saturn  | Virgo        | 6  | 6  |
| Uranus  | Scorpio      | 7  | 7  |
| Neptune | Sagittarius  | 8  | 8  |
| Pluto   | Virgo        | 6  | 5  |
| Chiron  | Taurus       | 1  | 1  |
| ASC     | **Aries**       | 1 | 1 |
| MC      | **Aquarius** (sidereal-M 28.94°) | (sequentially 10) | 10 |

Houses where Equal ≠ Placidus for Ana (only **2 of 12** planets shift): Moon (9→8) and Pluto (6→5).

> Hardcoded "GM expected Placidus houses" in `routers/admin_gm_aligned.py` matched Mirror-Placidus for **12/12 planets** earlier — but those values were transcribed from Ana's PDF right-table ("Natal Quantum" view). They are a confirmation that Mirror-Placidus matches Ana-Placidus *for that user*, not a general claim about GM.

---

## PHASE 5 — MC INVESTIGATION (Ana specifically)

| MC variant | Exact value | Sign |
|---|---|---|
| Mirror Tropical-Placidus MC | 329.987° | Aquarius 29°59′ *(boundary — 1′ from Capricorn)* |
| Mirror Sidereal-M Placidus MC (SVP 31.2836°) | 298.94° | Aquarius 28°56′ |
| Mirror Sidereal-Lahiri Placidus MC | 306.37° | Aquarius 6°22′ |
| GM PDF Ana MC | text reads "25.1 10 40° 49' MC" | Sign GLYPH not in text layer — needs visual confirm |

**Classification of MC discrepancy:** likely **(D) extraction issue + (A) house-system label mixing** — the previous fork claimed GM said "Capricorn" for MC, but the PDF text layer does not contain a sign name. The "40° 49'" reading from the GM left-table is **>30°**, meaning GM's "True Sidereal-M (Midpoint)" is using **variable-width constellation boundaries** (13-sign or constellation-midpoint sidereal), which is a **different zodiac system** from Mirror's fixed 30°-per-sign sidereal.

This is the most important phase-5 finding: **GM and Mirror are not using the same zodiac**, despite both being labeled "True Sidereal-M".

---

## PHASE 6 — DECISION MATRIX

| Metric | Mirror = Equal | Mirror = Placidus |
|---|---|---|
| Pete ASC sign matches GM | OCR-unreliable (likely **no** either way) | Same |
| Pete MC house matches GM (=9) | **✗** (Mirror MC sign different) | **✗** (Mirror puts it in 10) |
| Mel ASC/MC matches GM (Cancer/Aries) | **✓** | **✓** |
| Mel house agreement | 11/12 planets | 10/12 planets |
| Ana ASC matches (Aries) | **✓** | **✓** |
| Ana MC sign matches GM | OCR-unreliable | OCR-unreliable |
| Ana planet-house agreement vs PDF | unclear (need ground-truth) | matches encoded expectations |
| HD type/profile/authority/channels/cross | **✓** | **✓** *(unchanged by house system)* |
| Overall **defensible** GM agreement | Higher (matches Pete & Mel's printed label) | Only matches Ana's Placidus PDF |

### Answers to the six closing questions

1. **Does GM appear to use Placidus?** No — GM uses whatever the user has set. Only Ana's PDF shows Placidus.
2. **Does GM appear to use Equal?** Yes — Pete & Mel screenshots explicitly say "House: Equal". And only Equal explains Pete's MC-in-house-9.
3. **Is there evidence of a hybrid implementation?** Yes — GM is **configurable per user**, not a single mode. Two of three artifacts are Equal; one is Placidus.
4. **Should Mirror remain Equal?** Recommended — it matches the majority of the supplied GM artifacts and avoids touching 171 user charts on weak evidence.
5. **Should Mirror switch to Placidus?** No — there is no universal GM-mandates-Placidus evidence.
6. **Should we migrate 171 users?** **No.** Migration would change house assignments for users whose GM views are Equal, breaking Pete & Mel's reference (and likely many others).

---

## RECOMMENDATION

> **C. HYBRID / FURTHER INVESTIGATION REQUIRED**
>
> Specifically:
> - **Immediate:** revert Mirror's *default* canonical house system to **Equal** (status before Phase 2 changes). Do NOT publish Phase 2's Placidus default to live; do NOT run the migration.
> - Keep the Placidus code-path available behind a flag — it works correctly when requested (`get_full_natal_chart(..., house_system="Placidus")`) and we can offer it as a per-user preference later.
> - **Resolve zodiac-system mismatch first.** GM's "True Sidereal-M (Midpoint)" appears to use **variable-width constellation-derived sign boundaries** (degrees > 30° appear in the PDF table). Mirror's "True Sidereal-M" uses fixed 30° signs offset by SVP. These can produce different sign assignments at boundary planets even though the underlying longitudes match. Until this is reconciled, sign-by-sign matching with GM will always have boundary noise.
> - Before any future migration, the user should provide **typed, verbatim** values from each GM screenshot (ASC sign, MC sign, Sun sign + house for at least the three users) so we can avoid OCR error.

---

*No code or DB has been modified by this audit. Mirror remains in the same state as before this request.*
