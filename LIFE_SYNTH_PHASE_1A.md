# Life Synthesis Engine — Phase 1a Deliverables

**Status:** Backend complete. UI is untouched (per your instruction: split 1a / 1b).
**Generator version:** `life_synth_v1a` + `role_card_v1a`
**LLM budget:** 1 render call per tab + 1 role card call = **max 4 calls per page (first load).** Cached 24h in-process.

---

## 1. JSON CONTRACTS

### Role Card (`GET /api/life/role-card/{user_id}`)

```json
{
  "role":        "You're in a phase where you're meant to refine and raise the standard — and the move is yours to make without waiting for permission.",
  "tension":     "Your efforts become so exacting that they surpass what others can follow.",
  "distortion":  "This precision may sever connections and undermine trust.",
  "orientation": "Allowing one imperfection to remain eases pressure; decisions settle after the intensity subsides.",
  "confidence":  "high | medium | low",
  "dominant_drivers": [
    "metal posture · strong",
    "manifestor operating style",
    "emotional decision signal"
  ],
  "purple_star_input": null,          // first-class hook, slot in later
  "debug": { ...seed provenance... },
  "generated_at": "2026-04-23T06:14:57Z",
  "generator_version": "role_card_v1a"
}
```

### Domain Synthesis (`GET /api/life/{work|relationships|self}/synthesis/{user_id}`)

```json
{
  "life_area": "work",
  "role_card": { ...above shape... },
  "domain_synthesis": {
    "pattern":                  "...",
    "default_tension":          "...",
    "distortion_under_pressure":"...",
    "what_this_pattern_needs":  "...",
    "today":                    null,   // RESERVED for P2 modulation
    "explore":                  ["...", "..."],
    "reflect":                  ["..."]
  },
  "evidence_signals": [
    { "lens": "operating_style",     "signal": "manifestor · emotional authority · 5/1", "weight": 0.85 },
    { "lens": "structural_posture",  "signal": "Metal day master — strong",              "weight": 0.80 },
    { "lens": "domain_field",        "signal": "House 10",                                "weight": 0.70 }
  ],
  "compressed_themes": { ... raw deterministic seeds ... },
  "confidence": "high",
  "debug": { "llm_used": true, "render_error": null, "banned_phrase_hits": [] },
  "generated_at": "...",
  "generator_version": "life_synth_v1a"
}
```

---

## 2. SAMPLE OUTPUTS (3 distinct chart types)

### Sample A — Manifestor / Metal / Emotional (Pete)

**Role card:**
> **Role:** You are in a phase of elevating standards through decisive action, advancing without waiting for external approval or validation.
> **Tension:** Your efforts become so exacting that they surpass what others can follow or effectively utilize.
> **Distortion:** This precision may sever connections and undermine trust within your environment.
> **Orientation:** Allowing one imperfection to remain eases pressure, with decisions settling clearly after initial intensity.

**Work:**
> **Pattern:** You start by taking action without waiting for others, then refine your work by raising standards with sharp discernment. You let one rough edge remain so momentum can continue.
> **Tension:** Informing others feels like asking for permission. Your insistence on exactness sharpens past usefulness, narrowing who can benefit.
> **Distortion:** You push forward alone but with growing resentment toward isolation. In your drive for precision, you cut deeply, unknowingly undermining trust.
> **Needs:** A way to set clear signals before acting, allowing impact to land without having to perfect every detail immediately.

### Sample B — Reflector / Water / Lunar (Mel)

**Role card:**
> **Role:** You are currently navigating a phase of sensing unseen currents, meant to observe a full cycle before making any firm commitment.
> **Tension:** You often absorb the atmosphere around you so deeply that your own perspective becomes uncertain and diluted.
> **Distortion:** In moments when clarity would serve you best, you may instead retreat into silence, missing the chance to speak with impact.
> **Orientation:** This period thrives when you openly acknowledge what you have already sensed, allowing understanding to unfold gradually over time.

**Relationships:**
> **Pattern:** You attune deeply to the emotional atmosphere before taking a stance, often sensing what others feel before it manifests. You express what you've sensed only after letting time settle the initial impression.
> **Tension:** You move toward decision before your body has settled, blurring the line between what is truly yours and what you've absorbed from others.
> **Distortion:** Under stress, you carry the mood of the room as your own burden and retreat into silence at the moment when a clear word would release tension and anchor your presence.
> **Needs:** Space to name what you've sensed aloud before committing. Waiting through that process allows your true stance to emerge free from absorbed influence.

### Sample C — Manifesting Generator / Fire / Emotional (Jane)

**Role card:**
> **Role:** You're meant to warm the atmosphere and set the rhythm by completing one focus before beginning another.
> **Tension:** Your energy shapes the environment, yet you often cling to it as if unable to release.
> **Distortion:** You overperform vitality to mask a lack of genuine presence.
> **Orientation:** Allow your energy to rest without seeing it as weakness, letting decisions come after the intensity subsides.

**Self:**
> **Pattern:** You ignite energy by responding quickly, often leaping ahead before all pieces settle. Your presence activates the environment, but the rhythm pushes you to keep moving before the whole story finishes — a scattered intensity that warms but doesn't always complete.
> **Tension:** You rush through moments that others linger in, depleting your reserves to maintain a charged atmosphere. This leaves unfinished threads hanging, burdening you with hidden responsibilities you didn't accept but feel compelled to carry.
> **Distortion:** You juggle too many energies at once, performing outward vitality to mask internal dullness. The frantic motion stops engagement from settling, and you risk becoming a blur.
> **Needs:** Hold space for rest without judgment and finish existing currents before sparking new ones.

---

## 3. DETERMINISTIC MAPPING LOGIC

File locations:
- `/app/backend/services/life_synthesis_engine.py`
- `/app/backend/services/role_card_engine.py`

### HD operating style extraction

From `chart.human_design`:
- `type`          → initiation / friction / distortion / restorative phrases (see `_HD_OPERATING_STYLES`)
- `authority`     → emotional wave flag + authority note in Role orientation
- `profile`       → carried through to evidence only (not used for synthesis prose yet)
- Centers (defined / undefined) → carried to lens_snapshots for later P2 use
- **Weight:** 0.85 when type is present, else 0.0

### BaZi structural-pattern extraction

From `chart.bazi.day_master` + `chart.bazi.elements`:
- `element` (Wood/Fire/Earth/Metal/Water) → posture / strain / distortion / restorative (see `_BAZI_ELEMENT_PATTERN`)
- `strength` (strong / weak / mixed) → surfaced in drivers only
- `dominant_elements`, `weak_elements` → carried to lens_snapshots
- **Weight:** 0.80 when element is present

### Astrology house/domain contribution

From `chart.astrology`:
- Domain → primary houses mapping:
  - `relationships` → [7, 5, 8]
  - `work`          → [10, 6, 2]
  - `self`          → [1, 4, 12]
- Extracts: primary cusp sign, planets falling in domain houses, primary posture (sign → phrase)
- **Weight:** 0.70 when planets or cusp found

### Pattern-memory contribution

From `db.pattern_memory`:
- `memory_state` in {recurring_pattern, new_pattern, ...}
- `match_count` ≥ 3 → "the pattern is cycling, not resolving"
- **Weight:** 0.60 when state is known

### Lifeline contribution (stub for P3)

From `db.lifeline_events`:
- Pulls last 12 events, extracts top 5 recurring themes
- **Weight:** 0.40 when themes exist

### Confidence logic

| Strong lenses (weight ≥ 0.6) | Confidence |
|--|--|
| 3+ | high |
| 2 | medium |
| 0–1 | low |

### Hierarchical compression (the synthesis itself)

`_compress_themes()` in order:

1. **core_pattern_seed:** HD initiation + BaZi posture + astro primary posture joined by `;`
2. **default_tension_seed:** HD friction + BaZi strain + memory phase hint, joined by `—`
3. **distortion_seed:** HD distortion + BaZi distortion, joined by `;`
4. **orientation_seed:** BaZi restorative + HD restorative, joined by `and`

These seeds are the DETERMINISTIC compression. The LLM then polishes them into Mirror-language prose in ONE call (no re-prompting, no chain-of-thought).

### Banned-phrase filter (post-LLM)

`BANNED_PHRASES` list covers:
- Vague abstractions (`dynamic blend`, `multiple perspectives`, `invites growth`, etc.)
- Prescriptive language (`you should`, `you must`, `will happen`)
- Flattery without cost (`unique gift`, `deep wisdom`)
- **Framework name leakage** (`human design`, `astrology`, `bazi`, `day master`, `manifestor`, `emotional authority`, etc.) — this is the critical one

If any banned phrase appears in LLM output, it's scrubbed in place and logged in `debug.banned_phrase_hits`. In the 12 sample generations across 4 charts, **zero banned-phrase hits** were triggered.

---

## 4. KNOWN LIMITATIONS (being honest about where it's still weak)

1. **Self vs Work bleed.** The `self` and `work` outputs for high-action types (e.g., Manifestor / Metal) can read similarly because the core pattern is the same person operating in adjacent domains. Mitigation: the astrology houses differ (1 vs 10) so orientation differs, but the LLM sometimes collapses them to nearly-identical prose. **P2 should tighten the prompt with stronger domain-focus hints.**

2. **`explore` and `reflect` questions are LLM-generated from the same seed set.** They can feel thematically similar within a user across tabs. **P2 fix:** generate these separately with a domain-specific question template.

3. **No today-modulation yet.** `domain_synthesis.today` is always `null`. Contract reserves the slot. P2 will fill it via a light transit overlay that *modulates the existing pattern* (not a separate daily generator — per your brief).

4. **Pattern-memory / lifeline are stubs.** The code fetches `db.pattern_memory` + `db.lifeline_events` but most users have empty collections, so most runs have weight 0 on these. **P3 is the full integration.**

5. **Purple Star not wired.** The `purple_star_input` kwarg flows through end-to-end untouched. When you supply the data shape, it'll merge into the Role seeds without a rewrite.

6. **Word budgets are not enforced server-side.** The prompt asks for e.g. `pattern: 45-70 words` but the LLM occasionally produces 80-90. I did not add a truncator because trimming mid-sentence would violate the "elegant, not bloated" rule. The LLM is disciplined in ~80% of generations — the edge cases may feel slightly long.

7. **Caching is in-process.** If the backend restarts (as it does on deploy), the 24h cache clears. For production this should move to Mongo (small addition, deferred).

8. **Houses are Equal-house only.** The astro extraction assumes cusps are available at each integer house. This matches the current compute. If Placidus is introduced, domain_field weights may need recalculation.

9. **No re-prompt on banned-phrase hit.** Currently the filter scrubs the phrase and moves on. A harder path would re-prompt the LLM when a hit occurs. Deferred — zero hits so far.

10. **No A/B against old endpoint.** The legacy `/api/life/{context}` still works and is fully unchanged (per your "keep as fallback" decision). No routing changes or flags yet.

---

## 5. OVERFIT GUARDS

- No user name, birthdate, email, or location appears anywhere in prompts.
- Prompts reference only compressed seeds (HD type, BaZi element strength, etc.) — the same compression applies to every user.
- LLM has `session_id` keyed by `{user_id, domain}` so different users get separate chat threads (prevents bleed between users).
- Tested across Manifestor/Metal, Reflector/Water, MG/Earth, MG/Fire — each produced visibly distinct role and pattern language.

---

## 6. REVIEW ASKS

Before I start **Phase 1b (UI refactor)**, please tell me:

**A. Does the output quality land?** Specifically:
- Is the Role card sharp enough?
- Do the Pattern / Tension / Distortion / Needs sections feel like a living pattern (not a trait summary)?
- Does the language pass your "strong ChatGPT session" bar, or does it still feel too polished?

**B. Anything to tighten before UI work?**
- Different word budget?
- Different banned phrases to add?
- Different domain → house mapping for astrology?
- Different weight on any lens?

**C. Concerns I flagged as limitations (1, 2, 3, 4, 6) — which do you want fixed in P1b before UI lands vs pushed to P2?**

---

## 7. ENDPOINTS & CURL

```bash
# Role card (cached 24h)
curl "http://host/api/life/role-card/{user_id}"

# Domain synthesis for any of: relationships | work | self
curl "http://host/api/life/work/synthesis/{user_id}"

# Force-refresh (skip cache)
curl "http://host/api/life/work/synthesis/{user_id}?refresh=true"

# Legacy endpoint (unchanged, fallback)
curl "http://host/api/life/work?user_id={user_id}"
```
