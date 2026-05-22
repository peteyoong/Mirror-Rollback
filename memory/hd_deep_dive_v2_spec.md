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

## Currently shipped (all 9 centers — full Phase 1 complete)
- Defined + Open V2 content live in
  `/app/backend/services/mirror_content_system.py` for:
  Head, Ajna, Throat, G Center, Ego, Solar Plexus, Sacral, Spleen, Root.
- Open-center protection verified: G Center, Ego/Heart, Solar Plexus,
  Sacral all framed as permeability/amplification/wave-based wisdom,
  never as deficiency.
- Plumbed through `services/human_design_centers.py::get_center_interpretation`.
- Rendered by `components/HumanDesignLensView.tsx::renderCenterContent`
  (V2 layout when `center.v2` exists, V1 fallback otherwise).
- BUILD_ID: `mirror-v2-scaleout-20260522`.

## Relationship Field V1.3 — Batch 2 channels also shipped
- 32-54, 28-38, 39-55, 18-58, 12-22, 1-8, 4-63, 11-56 added to
  `services/forum_hd_mapping.py::CHANNEL_INTERPRETATIONS`.
- All voice-calibrated against the over-intensification risk
  (especially 39-55, 28-38, 18-58 which can drift into suffering archetypes).
