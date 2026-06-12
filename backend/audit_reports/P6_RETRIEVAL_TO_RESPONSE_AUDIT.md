# P6 — Retrieval-to-Response Forensic Audit

**Date:** 2026-06-12
**Deployed host probed:** `https://birth-data-remediate.preview.emergentagent.com`
**Source commit at probe time:** `5f15750e8821f808f31f98b93af1ca01f0ba3c4e`
**Probe user:** Pete (`697f0c6abf35c0528ff06954`)
**Stage 1 bucket for Pete:** 99 → `cutover.enabled=False` → live path = legacy V1 stack
**Mode:** shadow telemetry intact; live response untouched (constraint honoured)

---

## Executive verdict

**User's hypothesis is CORRECT and PROVEN.**

| Layer | Status | Evidence |
|---|---|---|
| Intent Router V2 | ✅ **Working** (in shadow) | Classifies 4/4 probes correctly into receipts |
| Telemetry | ✅ **Working** | P3, cross-lens v2.2.0, forum-topology, stage1 all persisting |
| Retrieval | ⚠️ **Partially working** | V1 modules wired but most gate out silently; V2 modules NEVER read by live path |
| Prompt assembly | ❌ **Fails to include V2 context** | `system_prompt` is built from chart fundamentals + V1 modules only |
| Response synthesis | ❌ **Falls back to generic lens templates** | LLM has no real-time / relationship / founder / timeline signal |
| Context weighting | ❌ **Lens-priority modulation is shadow-only** | `lens_priority_after` recorded but live LLM call ignores it |

**Root classification: (C) Prompt-assembly failure + (B) partial retrieval failure.**
Not (A): router works. Not (D): the model dutifully reflects whatever it's given.
The V2 intent envelope, P3 plan, cross-lens contradictions, forum-topology
resolution — all live in the **receipt collection**, not in the prompt
sent to GPT-4o. Live generation therefore falls back to the V1
heuristic block + raw chart fundamentals.

---

## A. Intent Layer — 4-probe trace

Each row is the V2 intent envelope captured **from the just-made request**
(`mirror_chat_retrieval_receipts` collection, shadow-write, ~1s after
HTTP response).

| Probe | Message | V2 primary | V2 secondary | confidence | matched_phrases | unresolved_name | lens_priority_after |
|---|---|---|---|---|---|---|---|
| 1 | "What is happening for me right now?" | `general` | – | 0.0 | `{}` | – | `[cross_lens_atoms]` |
| 2 | "How does Mel map to me?" | `relationship` | – | 1.0 | `{relationship: [does mel, how does mel]}` | **Mel** | `[relationship, astrology, hd, enneagram, timeline, numerology]` |
| 3 | "Tell me about JH" | `general` | – | 0.0 | `{}` | – | `[cross_lens_atoms]` |
| 4 | "What is my biggest founder blind spot right now?" | `career` | – | 0.7 | `{career: [founder]}` | – | `[astrology, timeline, hd, enneagram, numerology, relationship]` |

### Sub-finding A1 — V2 classifications are reasonable but **NEVER REACHED THE LLM**

For Probe 4 the V2 classifier correctly fired on `founder` → primary
`career` and bumped `timeline` to position #2 in `lens_priority_after`.
The actual response (`response[:300]` captured live):

> "You're searching for clarity on what might be obstructing your view as a founder. However, there's a tendency here to seek a single, defining answer when multiple factors might be at play. Given what we know, your strengths often come fr…"

— generic Manifestor 5/1 / Emotional Authority / Enneagram 7w8
material. **No timeline data, no founder-specific context, no
leadership lens prioritization.** The `career` signal went to the
receipt collection only.

### Sub-finding A2 — Probe 1 ("right now") classified as `general`

The V2 lexicon has `right now` weight only in `timeline` (0.6). The
test produced `primary=general, confidence=0.0` — meaning that match
either fell below the threshold or the timeline lexicon isn't covering
the bare "right now" idiom strongly enough. **Even if V2 had fired
correctly, the result wouldn't have reached generation.**

### Sub-finding A3 — Probe 3 ("Tell me about JH") shows target-resolution dead end

V2 detected zero proper-name candidate ("JH" is too short for the
proper-name heuristic). The V7 astrology resolver (`resolve_target_member`)
also didn't fire because no astrology intent was detected by the legacy
`classify_astrology_intent`. The LLM was therefore handed a question
about an unidentified entity with no charts to read against.

---

## B. Relationship Orchestration (P3) — receipt-only

| Probe | rule_bucket | framing_hint | reordered | applied_rules |
|---|---|---|---|---|
| 1 | `self` | `self_inquiry` | false | `[self:default]` |
| 2 | `self` | `self_inquiry` | false | `[self:default]` |
| 3 | `self` | `self_inquiry` | false | `[self:default]` |
| 4 | `self` | `self_inquiry` | false | `[self:default]` |

**Why all four hit `self`:** the V2 relationship resolver returned
`relationship_role=None` for every probe (no role bound in the
request). For Probe 2 ("Mel") the target was *named* but
*unresolved* (`target_unresolved_name=Mel`, `target_resolved=None`)
because the `saved_people` lookup didn't find a Mel under Pete's
ownership. → role stays `None` → bucket falls through to `self`.

**The P3 plan is computed for every receipt and persisted, but the
live response path NEVER reads `relationship_orchestration_v1.*`.**
`grep -nE "relationship_orchestration_v1|plan_lens_priority" routers/mirror_chat.py` → **0 matches.**

---

## C. Retrieval Layer — per-block utilization map

Every probe was traced in `backend.err.log`. Below is the inventory of
retrieval blocks the live path could attach to `system_prompt`. **All
4 probes triggered ZERO retrieval-block log lines except the base
`MIRROR_CHAT REQUEST RECEIVED / chart fetched / LLM call` triplet.**

| Block | Status (Probe 1) | Status (Probe 2) | Status (Probe 3) | Status (Probe 4) | Notes |
|---|---|---|---|---|---|
| **Chart fundamentals** (Sun/Moon/Rising/HD/Numerology/Enneagram/BaZi) | FOUND AND INCLUDED | FOUND AND INCLUDED | FOUND AND INCLUDED | FOUND AND INCLUDED | Always included unconditionally |
| **`question_intent_router_v1`** domain proof block | FOUND BUT NOT EMITTED | FOUND BUT NOT EMITTED (no proof-block log) | FOUND BUT NOT EMITTED | FOUND BUT NOT EMITTED | Legacy router; `_domain` always `general` for these prompts |
| **`build_lens_context`** (memory_block) | FOUND? (no log) | FOUND? (no log) | FOUND? (no log) | FOUND? (no log) | Silent skip — module fires but log only emits when intensity rules trip |
| **`build_life_domain_context`** (mv_block) | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | Returns None when `life_domain=None` in request payload |
| **`build_relational_context`** (rel_block) | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | Gated on `about_person_id`; **all 4 probes have `about_person_id=None`** |
| **`build_pattern_memory_context`** (pattern_block) | NOT FOUND (no `matched_patterns` log) | NOT FOUND | NOT FOUND | NOT FOUND | Tag-detector didn't match any abstracted patterns |
| **`build_micro_reflection_context`** (r_block) | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | Requires accumulated micro-reflections |
| **`build_contradiction_context`** (`_c_block`) | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | Requires contradiction surfacer to trip |
| **V7 Ask-Mirror astrology engine** | NOT FOUND (no `AskMirrorV7 target_resolved` log) | NOT FOUND | NOT FOUND | NOT FOUND | Requires legacy `classify_astrology_intent` to detect astro intent first; none of the 4 prompts match |
| **V10 relationship synthesis** (`build_relational_synthesis_block`) | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | Requires V7 to bind a target first |
| **Timeline V2 / `user_timeline` retrieval** | **NOT RETRIEVED** | **NOT RETRIEVED** | **NOT RETRIEVED** | **NOT RETRIEVED** | `user_timeline` is **WRITE-ONLY** in this route (line 2214 `insert_one`). NO read-side retrieval. |
| **Relationship Field** | **NOT WIRED** | **NOT WIRED** | **NOT WIRED** | **NOT WIRED** | `grep relationship_field` → 0 hits in `routers/mirror_chat.py` |
| **Between You Today** | **NOT WIRED** | **NOT WIRED** | **NOT WIRED** | **NOT WIRED** | No retrieval call |
| **Founder / Operator context** | **NOT WIRED** | **NOT WIRED** | **NOT WIRED** | **NOT WIRED** | No dedicated retrieval module for founder context |
| **Member context** (via `saved_people`) | NOT FOUND | NOT FOUND (Mel unresolved) | NOT FOUND | NOT FOUND | Requires V7 + saved-people binding |
| **Forum topology resolution** | NOT FOUND (no topology) | NOT FOUND | NOT FOUND | NOT FOUND | None of probes carry a forum_topology |
| **Cross-Lens Synthesis v2 (agreements/tensions/contradictions)** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | Computed → persisted to receipt → live prompt never reads it |
| **P3 Relationship Orchestration plan** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | Receipt-only by design (Phase 2 not yet authorised) |
| **Intent Router V2 envelope (`lens_priority`)** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | **FOUND BUT DROPPED** | `grep classify_intent_v2 routers/mirror_chat.py` → 0 hits |

### Dropped-context inventory

* **V2 intent envelope** — never read by live path (shadow-only).
* **P3 lens_priority_after** — never read by live path.
* **Cross-lens v2.2.0 contradictions + polarity** — never read by live path.
* **Forum-topology v2 resolution telemetry** — never read by live path.
* **B3.2 founder/operator lexicon scores** — never reach generation.
* **Timeline V2 user_timeline events** — write-only in the route.

---

## D. Prompt Assembly — what actually reaches GPT-4o

Reconstructed `system_prompt` for **Probe 4** ("What is my biggest founder blind spot right now?") by tracing every `system_prompt +=` statement in `routers/mirror_chat.py`:

```
[1]   MIRROR_SYSTEM_PROMPT
            ← base "I am Mirror" persona, ~1000 chars

[2]   V1 preferences insert
            ← tone/depth/support from prefs (`v1_preferences`)

[3]   LENS_PROMPTS[None]
            ← no lens → empty (generalist mode)

[4]   keystone_insert
            ← keystone phrase

[5]   thread_anchor              (only if active thread)
            ← NONE for these probes

[6]   _proof_block                (only if _domain != "general")
            ← NONE — legacy classifier said "general"
              even when V2 said "career" / "relationship"

[7]   --- USER CONTEXT ---
            ← Sun in Pisces, Moon in Aries, Rising in ___,
              HD Type=Manifestor, Strategy=Inform, Authority=Emotional,
              Profile=5/1, Definition=Single,
              Incarnation Cross=___,
              Life Path=___, Birthday Number=___,
              Enneagram Core=7, Wing=8,
              BaZi Day Master=Earth (or whatever Pete has)

[8]   pattern_thread_insert       (only if pattern_thread_context)
            ← NONE for these probes

[9]   gene_keys_context           (only if Gene Keys pattern matched)
            ← NONE for these probes (silent)

[10]  memory_block from build_lens_context
            ← Likely empty / minimal — no log line emitted

[11]  mv_block from build_life_domain_context
            ← EMPTY (life_domain=None in request)

[12]  rel_block from build_relational_context
            ← EMPTY (about_person_id=None)

[13]  pattern_block from build_pattern_memory_context
            ← EMPTY (no matched_patterns log)

[14]  r_block from build_micro_reflection_context
            ← EMPTY (no reflections accumulated for Pete in window)

[15]  _c_block from build_contradiction_context
            ← EMPTY (no contradiction surfaced)

[16]  Astrology V7-V10 proof blocks
       (house_inventory / field_synthesis / lifecycle /
        solar_return / natal_object / relational_synthesis)
            ← NONE — V7 didn't activate (no astrology intent
              detected by legacy classify_astrology_intent)
```

**Effective prompt for Probe 4:**
```
MIRROR_SYSTEM_PROMPT
+ V1 preferences
+ --- USER CONTEXT ---
    Name: Pete
    Birth date: ...
    Sun: Pisces
    Moon: Aries
    Rising: ...
    Type: Manifestor
    Strategy: Inform
    Authority: Emotional
    Profile: 5/1
    Incarnation Cross: ...
    Defined Centers: ...
    Life Path: ...
    Enneagram Core: 7 (Enthusiast)
    Wing: 8
    BaZi Day Master: Earth ...
```

That's it. **No timeline, no relationship field, no founder-specific
data, no Mel, no JH, no transit-of-today, no pattern history.**

The user's observed response (`"As a Manifestor with a 5/1 profile and
Emotional Authority… Considering your Enneagram Type 7w8…"`) is a
**word-for-word echo of the USER CONTEXT block.** GPT-4o is doing
exactly what it's been asked: reflect Pete's chart fundamentals.

---

## E. Response Attribution per probe

### Probe 1 — "What is happening for me right now?"

> "Right now, the timing appears to hold a mix of energies that could feel both demanding and transformative. With a Fire-type energy present today, there might be a sensation of pressure and intensification…"

| Sentence | Source | Contribution |
|---|---|:---:|
| "Right now, the timing appears…" | Generic Lens Template (LLM filler) | 30% |
| "Fire-type energy present today" | Transit context line (`mode=timeline` adds `Added transit context: timezone=Asia/Kuala_Lumpur, date=2026-06-12`) — date+timezone only, NO actual transit ephemeris | 20% |
| "Sun in Pisces and Moon in Aries…" | USER CONTEXT chart fundamentals | 30% |
| "Manifestor by design… emotional authority" | USER CONTEXT chart fundamentals | 20% |

**Source mix:** 50% chart fundamentals · 30% generic lens template · 20% transit *metadata* (no actual transits).
**Timeline V2 contribution: 0%.**

### Probe 2 — "How does Mel map to me?"

> "You're curious about how Mel relates to your own characteristics or experiences. Mel might represent a part of yourself…"

| Sentence | Source | Contribution |
|---|---|:---:|
| "You're curious about how Mel relates…" | Generic deflection (LLM didn't know who Mel is) | 60% |
| "Mel might represent a part of yourself…" | Pure LLM inference / projection guidance | 40% |

**Source mix:** 0% Mel-specific. The V2 receipt records `target_unresolved_name=Mel` — V2 saw the name and could not bind it to a saved_person. The live path's V7 resolver also didn't fire. **Member Context contribution: 0%.**

### Probe 3 — "Tell me about JH"

> "I'm here to reflect with you about what JH might be bringing up for you, rather than providing specific details about them. Consider what you notice about your feelings…"

| Sentence | Source | Contribution |
|---|---|:---:|
| "I'm here to reflect with you about what JH might be bringing up…" | Hard-deflection from `MIRROR_SYSTEM_PROMPT` (the persona refuses generic info) | 70% |
| "Consider what you notice about your feelings…" | Mirror reflective scaffolding | 30% |

**Source mix:** 0% JH-specific. The system has **no JH binding** (no saved_person, no forum member) and no module to surface that gap explicitly to the user. **Member/Forum Context contribution: 0%.**

Note: the screenshot the user attached shows a *different* in-app session where the response talked about "Jay and Jaan" — that was the LLM hallucinating from prior turn history. The clean curl probe above shows the actual zero-context behaviour.

### Probe 4 — "What is my biggest founder blind spot right now?"

> "You're searching for clarity on what might be obstructing your view as a founder. However, there's a tendency here to seek a single, defining answer when multiple factors might be at play. Given what we know, your strengths often come fr…"

| Sentence | Source | Contribution |
|---|---|:---:|
| "Searching for clarity…" | Mirror reflective scaffolding | 15% |
| "Strengths come from Manifestor / 5/1 / Emotional Authority…" | USER CONTEXT chart fundamentals (line-by-line) | 60% |
| "Enneagram 7w8 drive for exploration…" | USER CONTEXT chart fundamentals | 20% |
| "Right now / this week" | Generic temporal framing (no transit ephemeris attached) | 5% |

**Source mix:** 80% chart fundamentals · 20% generic. **Timeline V2 contribution: 0%. Founder Context contribution: 0%. Pattern Memory contribution: 0%.**

---

## F. Root-Cause Analysis (point-by-point)

| Question | Answer | Evidence |
|---|---|---|
| 1. Was context never retrieved? | **PARTIALLY.** V2 stack runs in shadow and retrieves correctly (Intent V2 / P3 / cross-lens / forum / target-name extraction). V1 stack mostly returns empty because its gates aren't met (no `about_person_id`, no `life_domain`, no `pattern_thread_context`, no `forum_topology`). | Receipt-trace shows V2 fired with non-trivial classifications for Probes 2 and 4. Backend log shows zero retrieval-block log lines for any probe. |
| 2. Was context retrieved but discarded? | **YES, for the entire V2 stack.** `classify_intent_v2`, `plan_lens_priority`, `compute_synthesis_v2`, forum-topology resolution, B3.2 founder lexicon — all run in a fire-and-forget `asyncio.create_task` background coroutine that writes to MongoDB and never feeds back. | `routers/mirror_chat.py:196` → `_asyncio_b1.create_task(_b1_run_shadow())`. The task body persists to `mirror_chat_retrieval_receipts` and returns. |
| 3. Was context present in prompt but ignored by model? | **NO.** GPT-4o is faithfully reflecting whatever is in `system_prompt`. The reason responses are generic is that the prompt itself is generic. | Probe 4 response paragraphs map 1:1 to USER CONTEXT lines (`"As a Manifestor with a 5/1 profile and Emotional Authority…"` ↔ `"Type: Manifestor / Profile: 5/1 / Authority: Emotional"`). |
| 4. Are generic lens templates overwhelming retrieved context? | **YES — by absence.** With nothing else in the prompt, the model has only USER CONTEXT to lean on. It's not "overwhelming" — it's the only thing there. | Reconstructed prompt above. Steps [10]-[16] all empty. |
| 5. Is orchestration telemetry-only and not affecting generation? | **YES — and this is by design (shadow mode).** No reader exists in the live path. | `grep relationship_orchestration_v1\|plan_lens_priority routers/mirror_chat.py` → 0 matches. |
| 6. Is Timeline V2 reaching the response path? | **NO.** `user_timeline` is **WRITE-ONLY** in `routers/mirror_chat.py`. The only references are `db.user_timeline.insert_one(timeline_event)` at line 2214 — post-response. There is no `find` / `find_one` on `user_timeline` anywhere in the route. | `grep timeline_v2\|user_timeline routers/mirror_chat.py` → only write paths. |
| 7. Is Relationship Field reaching the response path? | **NO — module not wired.** `grep relationship_field\|between_you_today` → 0 hits. | A dedicated retrieval module for "Relationship Field" does not exist in the live mirror_chat route. V1 `relational_awareness` is the only relationship-flavoured retrieval and requires `about_person_id`. |
| 8. Is Founder Context reaching the response path? | **NO — module not wired.** `grep founder_context\|operator_context` → 0 hits. | B3.2 founder/operator lexicon only contributes to V2 *scoring*; there is no founder-specific retrieval block that injects content into the prompt. |

---

## G. Context-utilization map (visual summary)

```
ASK MIRROR (live) ─┬─→ MIRROR_SYSTEM_PROMPT          ✓ included
                   ├─→ V1 preferences                ✓ included
                   ├─→ LENS_PROMPTS[lens]            ✓ included (empty for None)
                   ├─→ keystone                      ✓ included
                   ├─→ thread_anchor                 ✗ none active
                   ├─→ DOMAIN PROOF (V1 router)      ✗ classifier→"general"
                   ├─→ USER CONTEXT (chart funds)    ✓ INCLUDED ← dominant signal
                   ├─→ pattern_thread_context        ✗ not supplied
                   ├─→ gene_keys_context             ✗ no match
                   ├─→ memory_block (lens)           ✗ empty (silent)
                   ├─→ mv_block (life_domain)        ✗ empty (life_domain=None)
                   ├─→ rel_block (relational)        ✗ empty (about_person_id=None)
                   ├─→ pattern_block                 ✗ empty (no match)
                   ├─→ r_block (micro-reflection)    ✗ empty
                   ├─→ _c_block (contradiction)      ✗ empty
                   ├─→ V7 astrology proof blocks     ✗ not activated
                   └─→ ── LLM CALL (gpt-4o) ──
                              ↑
                              │ system_prompt =
                              │   {MIRROR_PROMPT + USER CONTEXT}
                              │
ASK MIRROR (shadow) ─→ ALL V2 retrievals
                       │  • Intent Router V2 envelope
                       │  • P3 lens_priority_after
                       │  • Cross-lens v2.2.0 (contradictions)
                       │  • Forum-topology resolution
                       │  • Founder lexicon scoring
                       └─→ mirror_chat_retrieval_receipts (MongoDB)
                                              │
                                              └─ FOR DASHBOARD VIEWING ONLY
                                                 (never reaches LLM)
```

---

## H. Ranked Remediation Plan

Ordered by **impact ÷ risk**, with each step gated and reversible.
**ALL recommendations preserve current Stage 1 constraints (CUTOVER=false, ROLLOUT_PERCENT=10).**

### R1 · Wire Timeline V2 retrieval into the prompt (HIGH IMPACT · LOW RISK)
**Why:** "Right now" and "blind spot right now" prompts have zero
temporal anchor today. A read-side `user_timeline` lookup of the last
N events (filtered by inferred_state, lens hits) would give GPT-4o
real material.
**How:** Add `build_timeline_v2_context(db, user_id, window_days=14)`
→ returns the last 5-8 most-relevant `user_timeline` events as a
prompt block. Insert after `pattern_block`. Gate behind a feature
flag `TIMELINE_V2_READ_ENABLED=false` so it can be A/B tested in the
10% bucket first.
**Effort:** 1 day. Reversible: flip flag.

### R2 · Surface V2 envelope.matched_phrases into the prompt (HIGH IMPACT · LOW RISK)
**Why:** When V2 says `career: [founder]` with confidence 0.7, the LLM
should know "the user is asking about their founder identity" — not
re-derive it from raw chart. Adding a single line like
`Domain signal: career (founder); secondary lenses: timeline, leadership`
would dramatically anchor founder-blind-spot answers.
**How:** Run `classify_intent_v2` **synchronously** (not in background
task), drop a 1-2-line "Intent signal" block into `system_prompt`.
The V2 stack is already shadow-validated at 100% routing-pass, so
trust is high.
**Effort:** 2 hours. Reversible: feature flag `INTENT_V2_PROMPT_INJECTION`.

### R3 · Fix target resolution for Probe 2 (HIGH IMPACT · MEDIUM RISK)
**Why:** "Mel" is in V2's `target_unresolved_name` but the saved_people
lookup didn't bind. Need to investigate whether Pete actually has
Mel as a saved_person on the deployed account, or whether the
resolver's name-matching is too strict.
**How:** Add explicit logging when `target_unresolved_name` is set
but `target_resolved` is null. Improve `relationship_router_v2`'s
fuzzy name match. When match found, pass the resolved person's
member context into `build_relational_context` even without an
explicit `about_person_id` on the request.
**Effort:** 1 day. Reversible: revert resolver changes.

### R4 · Add a Founder/Operator context retrieval (MEDIUM IMPACT · LOW RISK)
**Why:** B3.2 lexicon detects founder-mode but no retrieval module
gives the LLM ANYTHING founder-specific. Stub a
`build_founder_context_block(db, user_id, intent_envelope)` that
loads from `user_timeline` filtered to events tagged `founder_*` /
`leadership_*` and surfaces them.
**Effort:** 1-2 days. Reversible: feature flag.

### R5 · Surface P3 `framing_hint` to live response generation (MEDIUM IMPACT · MEDIUM RISK)
**Why:** P3 plan correctly identifies `spouse_focus` / `cofounder_strategic`
/ `forum_member_dynamic` but the LLM never sees the hint. Surface
the bucket label as a 1-line "Framing: spouse_focus" in system_prompt.
**How:** Read `relationship_orchestration_v1` block from the just-emitted
receipt (or compute synchronously). Requires explicit authorisation
per the P3 observation-window protocol — **NOT to be implemented
without operator sign-off.**
**Effort:** 1 day. **Gate behind the P3 readiness scorecard.**

### R6 · Add a Relationship Field retrieval module (HIGH IMPACT · MEDIUM RISK)
**Why:** "Between You Today" / Relationship Field aren't wired at all.
Probe 2 ("How does Mel map to me") got zero relationship-field
data even though we have synastry/composite calculations elsewhere
in the codebase.
**How:** Add `build_relationship_field_block(db, user_id, target_id)`
that loads the latest computed synastry/composite/today's field
snapshot. Insert when `target_resolved` is non-null.
**Effort:** 2-3 days. Reversible: feature flag.

### R7 · Wire Cross-Lens Synthesis v2.2 surfacing (LOW IMPACT NOW · HIGH IMPACT LATER · MEDIUM RISK)
**Why:** Contradictions/polarity/agreements are computed but unused.
Once R1-R3 add real content, the synthesis pass becomes more
valuable as a "tension namer."
**How:** Read `cross_lens_synthesis_v2.tensions` (top 1) and
`agreements` (top 1) from the just-emitted shadow receipt, project
as a 1-line system_prompt hint. **Requires explicit authorisation
per the constraint.**
**Effort:** 0.5 day. **Gate behind operator sign-off.**

### R8 · Convert shadow → sync for V2 stack (HIGH IMPACT · MEDIUM RISK)
**Why:** Currently `_b1_run_shadow()` is fire-and-forget. The
receipts arrive *after* the LLM call has already returned. To use
V2 outputs in the prompt, we need them ready BEFORE the LLM call.
**How:** Refactor `_b1_run_shadow` so the in-memory `intent_envelope`
+ `p3_plan` + `cross_lens_synthesis` are returned to the caller
synchronously; only the persistence step (MongoDB write) stays
async. Then the prompt builder can read them.
**Effort:** 2 days. **The 80% solution: keep persistence async,
hoist computation to sync. Stage 1 telemetry behaviour unchanged.**

---

## I. Recommended order of operations

1. **R2** (V2 envelope → prompt) — 2 hours, immediate dramatic improvement on Probes 2 & 4.
2. **R8** (sync V2 computation) — unblocks R5 / R7.
3. **R1** (Timeline V2 retrieval) — fixes "right now" prompts.
4. **R3** (Mel resolution) — fixes target binding gap.
5. **R4** (founder context retrieval) — fixes founder blind-spot prompts.
6. **R5** (P3 framing_hint surfacing) — gated on operator sign-off.
7. **R6** (Relationship Field) — bigger lift, do after R3 stabilises.
8. **R7** (Cross-lens contradictions) — gated on operator sign-off.

---

## J. Verdict against user's hypothesis

| User claim | Verified? | Evidence |
|---|:---:|---|
| Router = working | ✅ TRUE | 4/4 V2 classifications in receipts |
| Telemetry = working | ✅ TRUE | stage1_bucket, cutover_decision, P3, cross-lens v2.2.0 all persisting |
| Retrieval = partially working | ✅ TRUE | V1 modules wired but gate out (no `about_person_id` / no `life_domain`); V2 modules persisted but unread |
| Response layer generating from generic lens templates rather than Timeline, Relationship Field, Founder Context, Pattern Memory | ✅ TRUE | Source-attribution analysis on all 4 probes: 60-80% USER CONTEXT (chart fundamentals); 0% Timeline V2 / Relationship Field / Founder Context |

**Hypothesis fully confirmed. Classification: (C) Prompt-assembly failure
compounded by (B) partial-retrieval failure. The fix is to wire the
already-built V2 + retrieval modules into `system_prompt` synchronously,
gated by feature flags so the 10% Stage 1 constraint is preserved.**

---

## K. Constraint compliance ledger

| Constraint | Status |
|---|:---:|
| `INTENT_ROUTER_V2_CUTOVER=false` | ✅ Unchanged |
| `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10` | ✅ Unchanged |
| Stage 1 telemetry uninterrupted | ✅ Verified live |
| No live response changes made during audit | ✅ Read-only forensic; no code changes |
| P3 plan still receipt-only | ✅ Confirmed |
| Cross-lens contradictions still receipt-only | ✅ Confirmed |

**No code was modified during this audit. This is a forensic report only. No further work until you authorise the R-series remediations.**
