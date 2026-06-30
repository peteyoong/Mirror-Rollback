# GM Compatibility Specification v1.1
*Project Mirror — read-only reverse-engineering of Genetic Matrix*
*Status: DRAFT — Mirror was not modified during this investigation.*
*Generated: 2026-06-30 (supersedes v1.0).*

---

## Changes vs v1.0
- Adds **§8** SVP-probe protocol (Experiment 1)
- Adds **§9** Libra/Scorpio boundary survey (Experiment 2)
- Adds **§10** explicit decision recommendation on GM-compatibility labelling
- All §1–§7 content from v1.0 carries forward unchanged

---

## 8. Experiment 1 — SVP Probe Protocol

### 8.1 Goal
Determine whether GM's `True Sidereal-M (User defined)` zodiac-model dropdown actually obeys a per-chart SVP override, and quantify the shift it applies. Resolve the Pete Y / melisaa t / Jaan C mystery.

### 8.2 Hypothesis tree
| H | Hypothesis | Predicted observation under override (SVP_test = 30.0°) |
|---|---|---|
| **H₁** | GM honours per-chart SVP override exactly | Every body's sign label shifts by ((31.2836 – 30.0) / typical-sign-width) ≈ 1.28° later in zodiac — small but observable on near-boundary planets. |
| **H₂** | GM ignores user override and always uses a fixed canonical SVP | No change in any sign label or degree between default and override panels. |
| **H₃** | GM uses two SVPs internally — one for astrology display, one for HD gate.line — and the override only affects one | Sign labels change, but HD gate.line column is identical (or vice-versa). |
| **H₄** | GM stores the override but applies a *different* zodiac transform (e.g. ecliptic-of-date) | Shift is observable but does not equal (31.2836 – override). |

### 8.3 Required artefacts (you to capture)
For **one user account** (recommend creating a fresh sandbox profile so you don't pollute Ana/Pete):

1. Birth data — copy Ana's exactly: 1983-05-03, 08:20 local, San Miguel, Argentina, lat=-34.5424, lon=-58.7141. Reusing Ana lets us reuse all of v1.0's validated baseline values.
2. Generate GM chart with **default** zodiac model (note exact dropdown text), screenshot left panel.
3. In the same account, change the zodiac model to `True Sidereal-M (User defined)` and explicitly set SVP = **30.0000°** (or whatever GM exposes as the SVP input field). Regenerate. Screenshot left panel.
4. Regenerate once more with SVP = **31.2836°** (Mirror's canonical). Screenshot.
5. Regenerate once more with SVP = **25.0000°** (well outside any standard ayanamsa, to amplify the shift). Screenshot.

For each screenshot, send the full Astro HD Natal table (left panel) including the column header text.

### 8.4 Predicted Mirror-equivalent values per SVP (computed now, no live GM call needed)

| SVP° | Mirror Sun (sidereal lng) | Mirror Sun sign·degree | Mirror ASC (sidereal lng) | Mirror ASC sign·degree |
|---:|---:|---|---:|---|
| **25.0000** | 17.71 | Aries 17°43' | 26.71 | Taurus 6°59' |
| **30.0000** | 12.71 | Aries 12°43' | 21.71 | Taurus 1°59' |
| **31.2836** | 11.43 | Aries 11°26' | 20.43 | Taurus 0°26' |
| **32.0000** | 10.71 | Aries 10°43' | 19.71 | Aries 19°43' |

(Computed analytically from Ana's frozen tropical positions Sun=42.71° and ASC=51.71° at her birth UTC. Each row = tropical − SVP, then sign-attributed under Mirror's Athen Variant-A table.)

### 8.5 Decision rule
Compare the four GM left-panel screenshots against the table above.

- **All four GM panels show different Sun/ASC labels matching the predictions** → H₁ confirmed. Mirror was right about per-chart SVP override; we should expose an SVP field on Mirror user records for parity.
- **All four GM panels are identical** → H₂ confirmed. GM does NOT obey override; the dropdown is cosmetic. Pete/melisaa/Jaan diverge for some other reason (likely a global GM SVP setting that drifted recently, or per-account historical SVP snapshots).
- **Sign labels change but HD gate.line column is identical** → H₃. Mirror is safe to ignore.
- **Shifts are observable but ≠ (31.28 – override)** → H₄. We'll reverse-out GM's actual transform from the residual.

### 8.6 Why this is the right experiment
Pete Y's GM left-panel Sun is at "Aries 16°27'" while Ana's matches Mirror exactly under default SVP. The simplest explanation that fits both observations is **per-user SVP** stored on the GM account. The probe above tests that directly with a single subject under controlled SVP variation, so we don't need to convince GM to expose Pete's SVP — Ana's same-account SVP-sweep is sufficient evidence.

### 8.7 Status: BLOCKED on you to capture GM screenshots
Until then I can't draw a numerical SVP conclusion. Predictions are pre-registered above so the analysis after the data arrives is mechanical.

---

## 9. Experiment 2 — Libra / Scorpio Boundary Survey

### 9.1 Goal
Pinpoint the GM Libra→Scorpio cusp longitude. Mirror's Athen table places it at sidereal 210.1972°; GM's behaviour on Ana's DC implies it sits ~19° earlier, but we have only **one** confirmed data point.

### 9.2 In-hand data (sidereal lng, Mirror Variant-A, GM observed label)
| Subject | Body | Mirror sidereal lng | Mirror label (Variant-A) | GM label | Source | Confidence |
|---|---|---:|---|---|---|:---:|
| Ana | DC | **200.4301°** | Libra 9°07' | **Scorpio 9°06'** | user verbal spec + PDF | 🟢 high |
| Ana | Jupiter | 217.92° | Scorpio 7°43' | (PDF AI read "Libra 7°42' R" — sign UNRELIABLE) | PDF extraction | 🟡 needs user confirm |
| Ana | Uranus | 217.08° | Scorpio 6°53' | (PDF AI read mixed — sign UNRELIABLE) | PDF extraction | 🟡 needs user confirm |
| Pete Y | Earth | unknown (Pete divergence unresolved) | Libra 15°39' (GM) | n/a | — | 🔴 cannot use |

### 9.3 Inference from Ana's DC alone
- 200.4301° is **inside Mirror's Libra band** [191.32°, 210.20°), Position 9.11° into the band.
- 200.4301° must be **inside GM's Scorpio band**, position 9.10° into the band.
- Therefore GM's Scorpio band STARTS at ≤ 200.4301° − 0° = 200.4301° and the previous (Libra/something) band ENDS at the same boundary.

Combined with Mirror's table where Virgo→Libra cusp = 191.32°, and assuming **GM does not have a Libra band wider than Mirror's**, the GM Libra→Scorpio cusp must satisfy:

```
  191.32°  ≤  GM_Libra→Scorpio_cusp  ≤  200.4301°
```

i.e. **GM's Libra is ≤9.11° wide** (vs Mirror's 18.88°), and GM's Scorpio starts somewhere between Mirror's Virgo→Libra cusp and Ana's DC longitude.

### 9.4 Test the "GM's Libra is absent" sub-hypothesis
If GM's table eliminates Libra entirely (a known choice in some 12+1 = 13-sign schemes where Libra is treated as a sub-band of Virgo or Scorpio):

| Hypothesis | Predicted GM_Libra→Scorpio_cusp | Predicted GM label for Ana DC |
|---|---:|---|
| **A. Libra absent — Virgo→Scorpio direct** | 191.32° | Scorpio 9.11° ✓ matches GM |
| **B. Libra exists, but narrow** (~5° wide) | 196.32° | Scorpio 4.11° ✗ doesn't match GM "9°06'" |
| **C. Libra exists at Mirror width (18.88°)** | 210.20° | Libra 9.11° ✗ contradicts GM |

**Hypothesis A is consistent with the single data point.** Hypothesis B is consistent only if Libra has a very specific width (~0°). Hypothesis C is contradicted.

### 9.5 What 3–5 additional GM charts would resolve this
The cleanest sample bodies are ones whose Mirror sidereal longitude falls in {191°, 193°, 196°, 198°, 200°, 205°, 209°}. If GM labels all of them "Scorpio", **Hypothesis A is confirmed**: GM has no Libra band, all of Mirror's Libra maps to GM Scorpio.

Bodies you can use:
- Any chart whose **Earth** (Sun + 180°) longitude sits in this range — happens whenever Sun is at sidereal 11°–29° (Aries-Taurus boundary), e.g. April–early May births.
- Any chart whose **DC** sits in this range — happens for ASCs in early Taurus (like Ana).
- Any chart whose **Jupiter / Uranus / etc** transits this band.

If you can give me Ana's complete planet list with GM's literal sign labels (just the sign column, no degrees needed), I can identify Jupiter / Uranus / South Node / etc and lock the boundary to within 1°. (The AI extracted these from the PDF but mislabelled the panels — I need your eyes on which sign GM literally prints for each Ana planet.)

### 9.6 Provisional v1.1 conclusion
**Highest-likelihood inferred GM zodiac table** (subject to revision once §8 + §9 data arrives):

| Sign | GM start (inferred) | GM end (inferred) | Width | Δ vs Mirror |
|---|---:|---:|---:|---|
| Aries | 0.0000 | 19.7286 | 19.7286 | identical |
| Taurus | 19.7286 | 56.5875 | 36.8589 | identical |
| Gemini | 56.5875 | 86.0412 | 29.4537 | identical |
| Cancer | 86.0412 | 103.1900 | 17.1488 | identical |
| Leo | 103.1900 | 141.6065 | 38.4165 | identical |
| Virgo | 141.6065 | 191.3200 | 49.7135 | identical |
| **(Libra)** | — | — | **0 (absent)** | **DELETED in GM** |
| **Scorpio** | **191.3200** | **223.4245** | **32.1045** | **EXTENDS BACKWARD into Mirror's Libra** |
| Ophiuchus | 223.4245 | 235.7818 | 12.3573 | identical |
| Sagittarius | 235.7818 | 269.2677 | 33.4859 | identical |
| Capricorn | 269.2677 | 294.8435 | 25.5758 | identical |
| Aquarius | 294.8435 | 318.0103 | 23.1668 | identical |
| Pisces | 318.0103 | 360.0000 | 41.9897 | identical |

**Confidence: 🟡 medium (single anchor data point: Ana's DC). Will rise to 🟢 high once 2+ additional same-band data points are confirmed.**

### 9.7 Why this shape makes astronomical sense
The IAU 1930 constellation boundaries place the **physical Libra constellation entirely within the ecliptic span ~218°–242°** (Lahiri sidereal). Mirror's Athen midpoint table reduces this to ~191°–210° in Sharatan frame, while GM's apparent table may simply **fold Libra into Scorpio** (treating Libra as Scorpio's claws — historically that *was* the constellation's identity in pre-Roman astronomy). If true, GM is using a 12-sign Athen variant that omits Libra by design.

---

## 10. Recommendation — GM-compatibility label layer

### 10.1 The decision
**Do not collapse Mirror's Libra into Scorpio.** Mirror's Athen table is astronomically faithful and matches modern Variant-A standards. Forcing parity with GM by dropping Libra would degrade Mirror's correctness for the >90% of placements that already agree with GM.

### 10.2 What to add instead (additive only)
Surface a **`gm_compat_sign`** field alongside `sign` in chart payloads — a thin alias that re-labels Libra placements as "Scorpio" (with `gm_compat_label_offset = sign_start - 191.32°` for display). Mirror's engine, UI, and all relationship logic continue to use the canonical `sign` field. GM-parity views (such as the dual-house audit endpoint) can opt-in to `gm_compat_sign`.

### 10.3 Pseudocode (NOT implemented — pending §8 outcome)
```python
GM_COMPAT_SIGN_REMAP = {
    "Libra": ("Scorpio", -18.88),   # sign + degree offset
    # all other signs identical
}
def gm_compat_relabel(sign: str, degree: float) -> tuple[str, float]:
    if sign in GM_COMPAT_SIGN_REMAP:
        new_sign, deg_shift = GM_COMPAT_SIGN_REMAP[sign]
        return new_sign, degree - deg_shift  # add Libra width back
    return sign, degree
```
With this, Ana's DC `Libra 9.11°` would expose:
```
{ "sign": "Libra", "degree": 9.11,
  "gm_compat_sign": "Scorpio", "gm_compat_degree": 28.0 }
```
…wait, that doesn't equal GM's "Scorpio 9°06'". Let me retract — the offset is **wrong**: GM's Scorpio band STARTS at 191.32° (Mirror Libra start). So the correct relabel for Mirror Libra X.Y° is "Scorpio X.Y°" (Mirror Libra and GM Scorpio share the same `sign_start = 191.32°` under Hypothesis A). The offset is therefore **zero**:

```python
GM_COMPAT_SIGN_REMAP = {"Libra": "Scorpio"}   # degree unchanged
```

Ana DC becomes `sign="Libra", degree=9.11, gm_compat_sign="Scorpio", gm_compat_degree=9.11`. ✓ matches GM exactly.

### 10.4 When to implement
**Defer until §8 + §9 close.** If H₂ (GM ignores SVP override) turns out to be the explanation for Pete/melisaa/Jaan divergence, the GM-compat label may also need to fold in an SVP shim — too early to write the code now. The cost of waiting is zero (Mirror's canonical output is correct).

---

## 11. Compatibility matrix delta vs v1.0

| Layer | v1.0 confidence | v1.1 confidence | Reason |
|---|:---:|:---:|---|
| Variant-A boundary table — **Libra band** | 🔴 30% | 🟡 55% | Inferred Hypothesis A (Libra absent in GM); needs 2+ more data points. |
| GM-compat label layer (recommended approach) | not defined | 🟢 — additive, zero-risk | Above. |
| Per-user SVP override hypothesis | ⚪ 0% | ⚪ 0% (until §8) | Blocked. |
| All other layers | unchanged | unchanged | — |

---

## 12. Pending actions

| # | Action | Owner | Blocks |
|---|---|---|---|
| 1 | Capture 4 GM screenshots per §8.3 (default SVP, 30°, 31.2836°, 25°) | user | SVP conclusion |
| 2 | Send Ana's complete planet-list with GM literal sign-only column per §9.5 | user | Libra boundary lock |
| 3 | Apply predictions in §8.4 to the captured data and finalise §8 conclusion | Mirror agent | — |
| 4 | Decide on §10 GM-compat label rollout (now: defer until §8/§9 close) | Mirror agent + user | — |

---

*End of GM Compatibility Specification v1.1.*
