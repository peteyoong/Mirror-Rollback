# HD Deep Dive V2 — Calibration Spec

**Status**: Phase 1, Batch 1 (Ajna only) — SHIPPED. Awaiting user sign-off
before scaling to the other 8 centers.

## Voice & framing
- **Centers** = *the stable psychological weather system underneath the person*.
  Atmospheric, identity-level, foundational.
- **Gates** (future Phase 2) = *specific recurring behavioral patterns*.
  Sharper, situational, patterned.
- **Open centers must NOT be pathologized.** Read as permeability,
  amplification, sensitivity, wisdom-through-exposure. NEVER as lack,
  deficiency, inconsistency. Especially careful with: Emotional Solar
  Plexus, G Center, Ego/Will.

## Section order (non-negotiable)
1. **RECOGNITION**   — 1–2 sentences, dominant visual + emotional weight.
2. **HOW IT SHOWS UP** — 3 short behavioural bullets.
3. **THE DISTORTION** — 2–3 bullets. Never moralising.
4. **THE GIFT**       — 2–3 bullets. Integrated expression.
5. **SIDDHI**         — 3-line block: SHADOW → GIFT → SIDDHI, plus an
   optional one-line resonance quote. Sits AFTER the Gift (the layered
   arc: recognition → distortion → integration → transcendence).
6. **WHY THIS EXISTS** — SHORTEST section, dim visual treatment.
   Framework / proof-layer energy. Comes LAST.

## Writing rules
- SUPPRESS: `is about` / `represents` / `associated with` / `this energy` /
  `you may` / `often indicates` / framework-first phrasing / AI symmetry /
  over-poetic abstraction / coaching tone (`should`, `must`, `try to`).
- "tends to" is OK when describing lived behaviour (soft suppression).
- PRIORITIZE: behavioural specificity, lived mechanics, recognisable
  tension, emotional truth, compression, embodiment.
- The user should feel *"I recognise myself"*, NOT *"I am learning HD"*.

## Data shape (additive, lives under `center.v2`)
```python
{
  "recognition": str,                 # 1–2 sentences
  "how_it_shows_up": [str, str, str], # 3 bullets
  "the_distortion": [str, ...],       # 2–3 bullets
  "the_gift": [str, ...],             # 2–3 bullets
  "the_siddhi": {
    "shadow": str,
    "gift": str,
    "siddhi": str,
    "resonance_line": Optional[str],
  },
  "why_this_exists": str,             # shortest section
}
```

## Scope locked
- 1b: drop `try_this`, keep tight 3-bullet `how_it_shows_up`.
- 2a: Siddhi inline after Gift.
- 3b: soft suppression of "tends to"; hard ban on framework-first verbs.
- 4c: hand-written Siddhi at center level (Phase 1); gate-keyed
  Gene Keys data for gate cards (Phase 2).
- 5c: Ajna first → user verifies tone → then batch the other 8.

## Currently shipped
- Ajna defined + Ajna open V2 content live in
  `/app/backend/services/mirror_content_system.py` under
  `HD_CENTER_CONTENT["Ajna"]["defined"|"undefined"]["v2"]`.
- Plumbed through `services/human_design_centers.py::get_center_interpretation`.
- Rendered by `components/HumanDesignLensView.tsx::renderCenterContent`
  (V2 branch when `center.v2` exists, V1 fallback otherwise).
- BUILD_ID: `hd-deep-dive-v2-ajna-20260522`.
