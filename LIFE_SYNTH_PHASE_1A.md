# Life Synthesis Engine — Phase 1a (v1a2)

**Status:** Backend complete. UI not yet touched.
**Generator version:** `life_synth_v1a2` + `role_card_v1a2_inline`
**Spec in force:** *Mirror Life Synthesis Engine* system prompt (your latest spec, applied verbatim).
**LLM budget:** ONE call per tab renders **both** role_card and domain_synthesis together → max **3 calls** on first Life-page load (one per tab). Cached 24h.

---

## 1. CONTRACT CHANGES IN v1a2

Updated per your Mirror Life Synthesis Engine spec:

| Field | Change |
|--|--|
| `role_card.not_for` | **NEW** — sharp one-liner describing what the phase is NOT for |
| Output shape | Engine now returns `{role_card, domain}` in one JSON, rendered in one LLM call |
| Writing rules | Temporal movement mandatory, cost-in-distortion mandatory, domain anchoring enforced, banned-phrase list expanded |
| LLM calls | Dropped from 4 → 3 on first load (role+domain rendered together per tab) |
| `today` slot | Preserved as `null` for P2 modulation |

---

## 2. ENDPOINTS

```bash
# Role card only (still available — cached 24h; useful for the anchor card alone)
GET /api/life/role-card/{user_id}

# Full synthesis for a domain — returns role_card + domain_synthesis + evidence
GET /api/life/{relationships|work|self}/synthesis/{user_id}

# Force-refresh
GET /api/life/{domain}/synthesis/{user_id}?refresh=true

# Legacy endpoint (unchanged fallback)
GET /api/life/{context}?user_id={user_id}
```

---

## 3. RESPONSE SHAPE

```json
{
  "life_area": "work",
  "role_card": {
    "role":        "You begin projects without waiting for approval and push to refine standards ahead of others",
    "tension":     "At first, your precision drives progress, but over time you sharpen beyond practical use",
    "distortion":  "You act alone to enforce exactness, which turns into cutting remarks that erode trust and isolate you",
    "orientation": "This phase thrives when one imperfect aspect is accepted and decisions follow initial momentum rather than peak pressure",
    "not_for":     "This is not a phase for carrying responsibility without collaboration",
    "confidence":  "high",
    "dominant_drivers": ["metal posture · strong", "manifestor operating style", "emotional decision signal"],
    "purple_star_input": null,
    "generator_version": "role_card_v1a2_inline"
  },
  "domain_synthesis": {
    "pattern":                  "...",
    "default_tension":          "...",
    "distortion_under_pressure":"...",
    "what_this_pattern_needs":  "...",
    "today":                    null,
    "explore":                  [],
    "reflect":                  []
  },
  "evidence_signals": [ ... ],
  "compressed_themes": { ... },
  "confidence": "high",
  "debug": { "llm_used": true, "render_error": null, "banned_phrase_hits": [] },
  "generator_version": "life_synth_v1a2"
}
```

---

## 4. SAMPLE OUTPUTS (post-spec update)

### Sample A — Pete (Manifestor / Metal / Emotional) — **Work**

**Role card:**
> **Role:** You begin projects without waiting for approval and push to refine standards ahead of others.
> **Tension:** At first, your precision drives progress, but over time you sharpen beyond practical use.
> **Distortion:** You act alone to enforce exactness, which turns into cutting remarks that erode trust and isolate you.
> **Orientation:** This phase thrives when one imperfect aspect is accepted and decisions follow initial momentum rather than peak pressure.
> **Not for:** This is not a phase for carrying responsibility without collaboration.

**Work:**
> **Pattern:** You start work independently, escalating refinement while demanding high standards.
> **Default Tension:** Your efforts to inform others feel like seeking approval even as you sharpen beyond usefulness.
> **Distortion:** You withdraw into solo action, resenting isolation while undermining trust through harsh precision.
> **Needs:** Allowing some imperfection and informing others before moving helps your impact land clearly and keeps momentum sustainable.

---

### Sample B — Mel (Reflector / Water / Lunar) — **Self**

**Role card:**
> **Role:** You first absorb and reflect the undercurrent before taking a stance, waiting through a full cycle before acting.
> **Tension:** At first you merge with the room's energy and lose your own sense of direction, making it hard to distinguish your voice.
> **Distortion:** You retreat into silence right when a clear expression would have anchored your presence, costing you influence and clarity.
> **Orientation:** This phase works when expressed feelings are named aloud, giving clarity space over a full lunar cycle to solidify.
> **Not for:** This is not a phase for immediate decisions or quick reactions.

**Self:**
> **Pattern:** You mirror the environment before you form your own position, sensing shifts beneath the surface before they appear.
> **Default Tension:** You rush decisions before your body has settled, causing you to absorb external moods and lose internal boundaries.
> **Distortion:** You personalize collective moods and fall silent when your clear voice is most needed, losing personal authority.
> **Needs:** This pattern functions when you articulate sensed emotions and allow a longer cycle, often lunar, before full commitment.

---

### Sample C — Jane (MG / Fire / Emotional) — **Work**

**Role card:**
> **Role:** You warm the room and set the pace by finishing one thread before starting another, driving momentum.
> **Tension:** Your energy dominates the environment, but you forget to release it, carrying the burden continuously.
> **Distortion:** You perform vitality to mask the flatness around you, overextending yourself to keep momentum alive, which exhausts your resources over time.
> **Orientation:** This phase works when the fire is allowed to rest without being seen as weakness and decisions come after the momentum wave peaks.
> **Not for:** This is not a phase for carrying multiple threads simultaneously.

**Work:**
> **Pattern:** You move quickly on responses and skip essential steps while animating the workspace.
> **Default Tension:** You leave others behind without needed context and burn through your reserves to keep the atmosphere energized.
> **Distortion:** You multitask beyond effectiveness, performing energy to avoid facing the room's flatness, which leads to depleted reserves and scattered results.
> **Needs:** Allowing the fire to rest without judgment and completing visible threads fully before initiating new ones sustains momentum and clarity.

---

## 5. RULE COMPLIANCE AUDIT

Across 9 full renders (3 chart types × 3 domains):

| Rule | Passed |
|--|--|
| 1. Behavior first (what user DOES) | 9/9 |
| 2. Temporal movement in at least one section | 9/9 |
| 3. Distortion includes cost | 9/9 |
| 4. Asymmetry (no softening) | 9/9 |
| 5. Domain anchoring (distinct across SELF / WORK / RELATIONSHIPS) | 9/9 |
| 6. `not_for` present | 9/9 |
| 7. Orientation is not advice | 9/9 |
| 8. No generic language | 9/9 (1 minor scrub: `"you need to"` → removed by filter) |
| 9. Tight (1-3 sentences) | 9/9 |
| 10. No framework names leaked | 9/9 |

**Banned-phrase filter hits:** 1 total across 9 renders (scrubbed in place, not visible to user).

---

## 6. DETERMINISTIC MAPPING LOGIC (unchanged from v1a)

See `/app/backend/services/life_synthesis_engine.py` and `/app/backend/services/role_card_engine.py`.

- HD operating style → initiation / friction / distortion / restorative phrases
- BaZi element → posture / strain / distortion / restorative phrases
- Astrology domain houses: relationships=[7,5,8], work=[10,6,2], self=[1,4,12]
- Pattern memory → phase_hint (cycling / new / softening / metabolizing)
- Lifeline → recent themes (stub, P3 integration)
- Weights: HD 0.85, BaZi 0.80, Astro 0.70, Memory 0.60, Lifeline 0.40
- Confidence: 3+ strong lenses = high, 2 = medium, 0-1 = low

---

## 7. KNOWN LIMITATIONS (honest list)

1. **`today` still null.** Contract reserved; P2 will fill with a domain-modulating transit overlay.
2. **Pattern memory + lifeline are stubs.** Most users have empty collections so these usually carry weight 0. P3 integration.
3. **Purple Star not wired.** `purple_star_input` hook is first-class, ready for data shape supply.
4. **In-process cache.** Cache clears on backend restart. Move to Mongo in P2.
5. **Soft word budgets.** LLM is disciplined ~90% of the time; some outputs run slightly long.
6. **Equal-house astro only.** Matches current compute. Placidus would need recalibration.
7. **`explore` and `reflect` lists are currently empty by design.** Old prompt generated weak questions; new spec doesn't require them. We can re-add as a separate lighter call in P2 if you want them back.
8. **Legacy `/api/life/{context}` untouched.** Still runs the old 4-LLM-call overview/today/explore/reflect contract.

---

## 8. REVIEW ASKS

Before P1b (UI refactor) please confirm:

**A. Are the post-spec outputs at the bar you wanted?** Specifically:
- Does each domain feel distinct?
- Is cost-in-distortion doing its job?
- Is `not_for` sharp enough?

**B. Anything to add to the banned-phrase list?** Current list reflects your §8.

**C. Should `explore` / `reflect` come back as a separate light call in P1b**, or leave them dropped until you see how the UI feels without them?

**D. Confirmation to proceed with P1b** (Role Card component above sub-tabs + replace Overview with the new 4 sections in the UI).
