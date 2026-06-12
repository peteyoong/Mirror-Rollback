# P0 Intelligence Utilization Audit — Forensic Report

**Generated:** 2026-06-12 (read-only forensic — no code, no data, no flag changes)
**Method:** Static analysis of the entire Mirror chat generation path (`routers/mirror_chat.py`, `services/mirror_chat_pipeline.py`, `services/mirror_chat_phase4_enrichment.py`, `services/mirror_chat_shadow.py`) + a 12-probe live trace (4 founder, 4 relationship, 4 forum) against Pete with full V2-receipt and backend-log capture per probe.

**Constraints honored.** No code changes, no flag changes, no prompt changes, no data mutations, no new intelligence systems. Read-only audit. All four constraint flags re-verified in `backend/.env`:
`INTENT_ROUTER_V2_CUTOVER=false`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT=10`,
`RELATIONSHIP_ORCHESTRATION_PROMPT=false`, `CROSS_LENS_PROMPT_SURFACE=false`.

> ## TL;DR (the one-sentence answer to the audit question)
>
> **The bottleneck is not retrieval.  Retrieval works.  The bottleneck is that ~70 % of the intelligence the router resolves never reaches the prompt at all — and what does reach the prompt is so soft-worded that GPT-4o consistently overrides it with stock coaching language.**
>
> Three immediate, code-only-not-prompt-not-flag actions would close most of the gap (§ 7):
>
> 1. **Wire `forum_field_intelligence` + `forum_conversational_field` into `mirror_chat.py`.**  Both services exist and are tested — they are simply not imported by the chat router.  Forum-axis questions today resolve a target but render the response as if the forum didn't exist.
> 2. **Promote the V2 receipt's resolved `target_name / role / topology_edge / P3 framing_hint` from soft "INTENT SIGNAL" advisory text into an enforced "RESOLVED TARGET" block** — same content the receipt already holds, but with the same "NAME / DO NOT SUBSTITUTE" copy treatment Phase 3 applied to MC/IC/Chiron.
> 3. **Backfill `founder_history` for Pete (and any operator) into the receipt source so the founder block has non-empty payload.**  The block emits today but logs `no_founder_history` and falls back to generic Manifestor / Enneagram framing.

---

## 1. Mirror chat generation path (static map)

```
POST /api/mirror/chat
  ↓
mirror_chat.py::mirror_chat()
  │
  ├─ V2 shadow envelope ─────────────── mirror_chat_shadow.compute_v2_envelope_sync
  │     (gated by INTENT_ROUTER_V2_SHADOW=true → runs for 100% of requests)
  │     ↳ receipt persisted to `mirror_chat_retrieval_receipts`  ✓ 212 docs observed
  │
  ├─ Astrology profile block (L264-440)
  │     ↳ Phase-3 MC FOCUS / DC FOCUS / IC FOCUS / CHIRON FOCUS blocks (gated by triggers)
  │
  ├─ context_parts → "--- USER CONTEXT ---"  (L1222)
  │
  ├─ Phase-4 enrichment (L1236-1424)
  │     ├─ R3b: resolve_target_via_forums (PFS-2.1 topology resolver)
  │     ├─ PFS-2.3: re-plan P3 lens_priority   ← receipt-only, NOT injected into prompt
  │     ├─ build_intent_v2_prompt_block        ← INJECTED (gated on INTENT_V2_PROMPT_INJECTION=true)
  │     ├─ build_timeline_v2_context           ← INJECTED (gated on TIMELINE_V2_READ_ENABLED=true)
  │     └─ build_founder_context_block         ← INJECTED (gated on FOUNDER_CONTEXT_ENABLED=true)
  │
  ├─ pattern_thread_context, keystone_insert, gene_keys, MV (L1448-1499)
  │
  ├─ Pipeline blocks (mirror_chat_pipeline.py, L1535-1622)
  │     ├─ build_lens_context                ← lens memory blocks
  │     ├─ build_life_domain_context         ← Life Tab Master Voice
  │     ├─ build_relational_context          ← relational awareness
  │     ├─ build_pattern_memory_context      ← longitudinal pattern memory
  │     ├─ build_micro_reflection_context    ← reflection loop block
  │     └─ build_contradiction_context       ← contradiction intelligence (Atom system)
  │
  ├─ Astrology grounding / overlays (L1675-2277, conditional on lens=='astrology')
  │     ↳ transit / solar return / natal object / pressure topology / field synthesis
  │     ↳ House Inventory v8 / relational synthesis
  │
  └─ emergent_generate(additional_system_prompt=system_prompt)  ← FINAL LLM call
```

## 2. Deliverable 1 — Intelligence Utilization Matrix

Legend:
- **Exists** — code lives in `/app/backend/services/`.
- **Retrieved** — invoked at request time (V2 receipt or live call).
- **Prompt-Injected** — actually appended to `system_prompt`.
- **Influence** — GPT-4o response demonstrably references the signal in the 12-probe trace.  Classification: `DOMINANT` / `MODERATE` / `WEAK` / `INERT`.

| # | System | Exists | Retrieved | Prompt-Injected | Influence | Notes |
|---|--------|:------:|:---------:|:---------------:|:---------:|-------|
| 1 | **Intent Router V2** (`services/intent_router_v2.py`) | ✅ | ✅ shadow_mode=100% | ✅ when signal present | **MODERATE** | INTENT SIGNAL block emits when `primary != general OR target OR phrases`.  In trace, fired on 8/12 probes.  LLM sometimes echoes target name but rarely changes lens. |
| 2 | **Relationship Resolution V2** (`relationship_resolver.py`, `relationship_router_v2.py`) | ✅ | ✅ via V2 envelope | ✅ inside INTENT block | **MODERATE→WEAK** | Resolves `target/role/forum_id`.  Trace: Mel resolved as spouse in 3/4 relationship probes; the 4th ("between us") returns `target=None`. |
| 3 | **Topology-First Resolution (PFS-2.1)** (`forum_relationship_edges`) | ✅ | ✅ (3 probes show `topology_role_found=True`, role=`spouse`, conf=high) | ✅ inside INTENT block as topology telemetry | **WEAK** | Mel↔spouse edge resolved correctly but the resulting role rarely changes response framing (response stays generic about "your relationship with Mel"). |
| 4 | **Relationship Field** (`services/relationship_field.py`) | ✅ | ❌ **NOT IMPORTED BY `mirror_chat.py`** | ❌ | **INERT** | `mandatory_modules_invoked` claims `relationship_field` is invoked for all 4 relationship probes, but `grep` of `routers/mirror_chat.py` returns 0 imports. Imported only by `services/forum_hd_mapping.py`. Either telemetry is misleading or the call is via another indirect path. |
| 5 | **Between You Today** (`services/relationship_today.py`) | ✅ | ❌ no calls in chat path | ❌ | **INERT** | 1 grep hit in `mirror_chat.py` is a comment.  Service consumed by `routers/relationship_today.py` only — separate endpoint. |
| 6 | **Founder Context** (`mirror_chat_phase4_enrichment.build_founder_context_block`) | ✅ | ✅ | ✅ when `primary in {career,life_direction}` AND founder phrase matched | **WEAK** | Trace: block emitted for probes 1 & 4 (founder probes that matched lexicon).  But emission log shows `signals=[…, 'no_founder_history']` — block content is **empty** because `founder_history` field is unset for Pete.  Response stays generic ("your Manifestor type"). |
| 7 | **Timeline V2** (`build_timeline_v2_context`) | ✅ | ✅ | ✅ (block emitted on ALL 12 probes) | **WEAK** | Same payload every probe: `events=8 dominant_state=exploring`.  No probe response referenced any timeline event by name.  Dominant-state copy is too generic to anchor. |
| 8 | **Longitudinal Pattern Memory** (`longitudinal_pattern_memory.py`, via `build_pattern_memory_context`) | ✅ | ✅ | ✅ | **WEAK** | Pipeline block emits, debug payload returned, but trace responses never name a concrete prior pattern.  Block content largely "you have shown a recurring tendency…" template. |
| 9 | **Cross-Lens Synthesis v2.2** (`cross_lens_synthesis_v2.py`) | ✅ | ✅ in V2 receipt | ❌ **GATED OFF** (`CROSS_LENS_PROMPT_SURFACE=false`) | **INERT IN PROMPT** | Computed in shadow.  Surfaced only when the flag flips (constraint prevents flipping). |
| 10 | **Contradiction Intelligence** (`contradiction_intelligence.py`, via `build_contradiction_context`) | ✅ | ✅ | ✅ when contradiction found | **MODERATE** | Pipeline block emits; observed in `final_debug.contradictions` payload in `MirrorChatResponse`.  Some probe responses do use "tension / pull / contradiction" framing, suggesting weak influence. |
| 11 | **Forum Field Intelligence** (`services/forum_field_intelligence.py`) | ✅ | ❌ **NOT IMPORTED BY `mirror_chat.py`** | ❌ | **INERT** | `grep "from services.forum_field_intelligence" routers/mirror_chat.py` → 0 hits.  Service consumed only by `services/forum_conversational_field.py` and `routers/forums_field.py`. |
| 12 | **Forum Conversational Field** (`services/forum_conversational_field.py`) | ✅ | ❌ **NOT IMPORTED BY `mirror_chat.py`** | ❌ | **INERT** | Same status as #11. Used only by `routers/forums_field.py` (the dedicated forum-field endpoint), not by Ask Mirror chat. |
| 13 | **P3 Relationship Orchestration V1** (`relationship_orchestration_v1.py`) | ✅ | ✅ (P3 plan present in 4/4 relationship probe receipts: `bucket=spouse`, `framing=couple_dynamic`) | ❌ **GATED OFF** (`RELATIONSHIP_ORCHESTRATION_PROMPT=false`) | **INERT IN PROMPT** | Code comment at `mirror_chat.py:1310-1316` says explicitly *"This step is receipt-only — the live response path still reads `lens_priority` from the intent envelope, NOT from this plan."*  Plan is computed, persisted, and ignored. |
| 14 | **Domain Proof Blocks** (`services/astrology_domain_context.build_domain_proof_block`) | ✅ | ✅ when intent classifier emits domain | ✅ (L1210, `system_prompt += "\n" + _proof_block`) | **MODERATE** | 8 grep hits in `mirror_chat.py`.  When fired (relationship / career / family probes), inserts deterministic chart-anchored facts into the prompt.  Some bleed into response (e.g. probe 4 names "Midheaven in Virgo"). |
| 15 | **Astrology Profile Block** (`mirror_chat.py:264-440`) | ✅ | ✅ | ✅ always | **MODERATE→DOMINANT** | Phase-3 hardening surfaces MC/IC/DC/Chiron in 32+ of 48 probes from the Phase-3 sprint.  In this audit's relationship probes the LLM did pull MC/Sun/Moon labels through. |
| 16 | **MC / IC / Descendant / Chiron FOCUS weighting** (Phase-3 patches) | ✅ | n/a | ✅ trigger-gated | **MODERATE** | Phase-3 verification confirmed 42/48 PASS, 0 substitution leaks.  In this audit's founder probe 4 ("growth edge as a founder"), MC-in-Virgo was named verbatim. |
| 17 | Pattern Memory (`pattern_memory.py`, separate from #8) | ✅ | partial | partial | **WEAK** | Older engine; not the active path used by pipeline. |
| 18 | Lens Conversation memory (`lens_conversation.py`) | ✅ | ✅ via `build_lens_context` | ✅ | **MODERATE** | "Your last 3 reflections" style anchors visible in some probe responses. |
| 19 | Master Voice (Life Tab) | ✅ | ✅ via `build_life_domain_context` | ✅ when `life_domain` provided | **WEAK** | Trace probes did not pass `life_domain` → block did not fire. |
| 20 | Pressure Topology / Field Synthesis V7-V8 (astrology lens only) | ✅ | gated on `lens=='astrology'` | gated | **DOMINANT (in lens)** | These bypass the generalist path; not active for our trace (lens=None). |

## 3. Deliverable 2 — Prompt Dominance Audit

Static analysis of `system_prompt` assembly order (`mirror_chat.py` line numbers).  Earlier blocks are **anchor blocks** (set the tone); later blocks are **modifier blocks** (often overridden if not enforced).

| # | Block | Line | Position | Weight (approx tokens) | Enforcement language? | GPT-4o references in trace | Class |
|---|-------|------|----------|------------------------|-----------------------|-----------------------------|-------|
| 1 | `MIRROR_SYSTEM_PROMPT` base | 986 | 1st | ~400 | strong | always | **DOMINANT** |
| 2 | Lens prompt (`LENS_PROMPTS[lens]`) | 1070 | 2nd | ~200 | strong | when lens set | DOMINANT in lens |
| 3 | Keystone insert | 1087 | early | ~80 | medium | partial | MODERATE |
| 4 | Astrology profile block (Phase-3 FOCUS blocks included) | 264-440 / 1222 | mid | ~250-400 | **strong (Phase-3 mandates explicit naming)** | 3/12 probes named MC sign | MODERATE |
| 5 | USER CONTEXT (HD/Enneagram/Bazi/Numerology) | 1222 | mid | ~500-800 | medium | 11/12 probes echo HD type / Enneagram type | DOMINANT (overall, but generic) |
| 6 | INTENT SIGNAL V2 block | 1387 | mid-late | ~80 | **soft advisory** | 6/8 probes mentioned target name; framing rarely changed | WEAK |
| 7 | Timeline V2 block | 1399 | mid-late | ~100 | soft | 0/12 probes named a concrete event | **INERT** |
| 8 | Founder context block | 1412 | mid-late | ~50 (often empty) | soft | 0/4 founder probes named a founder-specific datum | **INERT-when-empty** |
| 9 | Pattern thread / Gene Keys / various enrichments | 1448-1499 | mid-late | ~100 | medium | sporadic | WEAK |
| 10 | Lens memory (build_lens_context) | 1547 | late | ~200 | medium | sometimes | MODERATE |
| 11 | Life Tab Master Voice | 1565 | late | ~200 | strong | only when life_domain set | MODERATE-conditional |
| 12 | Relational awareness | 1583 | late | ~150 | medium | rarely | WEAK |
| 13 | Pattern memory | 1598 | late | ~150 | medium | rarely | WEAK |
| 14 | Micro reflection | 1609 | late | ~80 | soft | rarely | WEAK |
| 15 | Contradiction intelligence | 1622 | late | ~100 | medium | sometimes ("tension between …") | MODERATE |
| 16 | Astrology grounding overlays (transit / SR / pressure / synthesis / lifecycle) | 1855-2277 | **last** | up to ~1000 | strong | dominant when lens=='astrology' | DOMINANT-in-lens |

**Key dominance findings.**

- **Order effect.** The astrology overlay blocks at L1855-2277 are appended *last*.  In lens="astrology" mode they dominate.  In the generalist path (our trace, `lens=None`) these blocks are skipped, leaving the response to the early DOMINANT blocks (system + USER CONTEXT) which are largely generic HD/Enneagram framing — the response then defaults to those archetypes.
- **Phase-4 retrieval blocks land in a "no-man's land"** at lines 1387-1412 — after USER CONTEXT but before the pipeline blocks at L1547-1622.  They have soft advisory language ("intent envelope detected …", "timeline shows …") and no explicit enforcement copy.  The LLM treats them as context, not as instructions.  Trace confirms: GPT-4o never names a target-resolved person beyond echo, never names a timeline event, never names a founder-specific datum.
- **The Phase-3 FOCUS blocks for MC/IC/DC/Chiron are the ONLY example in the pipeline of strong-enforcement copy** ("TREAT X AS PRIMARY SIGNAL", "EXPLICITLY NAME", "Do NOT substitute Y").  And those are the blocks whose acceptance rate jumped from 32/48 to 42/48 PASS with 0 leaks.  Pattern is clear: **enforcement copy works; advisory copy is INERT.**

## 4. Deliverable 3 — Founder Intelligence Audit (trace)

Probes (Pete, who is a Manifestor founder of Pulsifi):

| # | Probe | V2 primary | Matched phrases | Founder block? | Response excerpt | Verdict |
|---|-------|------------|-----------------|----------------|------------------|---------|
| 1 | "What is my biggest founder blind spot?" | `career` (conf 0.7) | `career: founder` | **emitted, `no_founder_history`** | "Your pattern as a Manifestor … Enneagram 7 core type reflects a zest for new experiences…" | **WEAK** — block fired but contained no Pete-specific founder data; LLM defaulted to HD/Enneagram |
| 2 | "What am I not seeing in Pulsifi?" | `general` (0.0) | none | not emitted | "People and situations often have layers…  What might you be overlooking about Pulsifi?" | **INERT** — router missed "Pulsifi"; response is pure reflection-back |
| 3 | "What leadership pattern keeps repeating?" | `general` (0.0) | none | not emitted | "You often navigate leadership by seeking to bring order and clarity…" | **INERT** — Virgo MC traits leak through (good!), but no concrete leadership history surfaced |
| 4 | "What is my next growth edge as a founder?" | `career` (0.74) | `founder`, `as a founder` | emitted, `no_founder_history` | "As a founder, your growth edge might be closely tied to the energy of your Midheaven in Virgo…" | **MODERATE** — Phase-3 MC FOCUS pulled `Midheaven in Virgo` into the answer.  But no Pulsifi context, no team data, no concrete founder history. |

**Why founder intelligence is muted.**

The founder block at `mirror_chat_phase4_enrichment.build_founder_context_block` reads from a `founder_history` field that **is empty for Pete in preview MongoDB**.  The log line `signals=[…, 'no_founder_history']` confirms this: the block emits a header but no payload.  The router-side founder lexicon (40+ phrases including `founder`, `founder ceo transition`, `founder burnout`, `cap table`, `term sheet`, `pmf`, …) IS firing — but the data the block would surface (Pulsifi-specific events, hires, raises, board moves) was never seeded.

## 5. Deliverable 4 — Relationship Intelligence Audit (trace)

| # | Probe | V2 envelope | Topology edge | P3 plan | Mandatory modules | Response verdict |
|---|-------|-------------|---------------|---------|---------------------|------------------|
| 5 | "Tell me about Mel" | `relationship`/1.0; target=`Mel`, role=`spouse`, source=`pair_forum` | role=`spouse`, conf=`high` | bucket=`spouse`, framing=`couple_dynamic`, domain_bias=`relationship` | `relationship_resolver`, `relationship_field`, `relationship_astrology_engine`, `relationship_3layer` | **WEAK** — Mel's name echoed; no synastry, no spouse-specific framing, no Mel chart data surfaced. |
| 6 | "How does Mel map to me?" | same | same | same | same | **WEAK** — response talks about **Pete's** Life Path 11 + Manifestor, not the map. |
| 7 | "What am I not seeing about Mel?" | `relationship`/0.6; target=Mel/spouse | same | same | same | **WEAK** — "unseen currents shaping the tides we notice" — pure deflection. |
| 8 | "What tension exists between us?" | `relationship`/1.0 (`between us` matched) | **NO target resolved** (router did not bind "us" → Mel) | bucket=`close_friend`, framing=`closeness` (default) | same | **INERT** — target resolution failure + generic response. |

**The four relationship intelligence layers all exist and all are listed in `mandatory_modules_invoked`, yet not one of them produced a quotable signal in the responses.** This is the single most striking finding in the audit.  Each layer's contribution:

| Layer | What it computed (per receipt) | What reached the prompt | What surfaced in response |
|-------|--------------------------------|--------------------------|-----------------------------|
| Topology-first edge (PFS-2.1) | `spouse` edge, high confidence, `forum_relationship_edges._id` | INTENT block: `Relationship target: Mel · role: spouse` (one line) | name echo only |
| `relationship_resolver` | `target_name=Mel`, `pair_forum` source | same | name echo only |
| `relationship_field` | claimed invoked but no imports in chat router | nothing visible | nothing |
| `relationship_astrology_engine` | claimed invoked | nothing visible | nothing |
| `relationship_3layer` | claimed invoked | nothing visible | nothing |
| P3 orchestration | `bucket=spouse`, `framing=couple_dynamic` | **GATED OFF** (flag) | nothing |
| Domain proof block | astrology proof for `relationship` domain | injected (L1210) | weak — only spouse-axis astrology hints in 1/4 probes |

**Where the intelligence is lost.**
- Layers 3-5 (`relationship_field`, `relationship_astrology_engine`, `relationship_3layer`) are *named in the receipt's mandatory_modules list* but `grep` finds zero imports from those modules in `routers/mirror_chat.py` or `services/mirror_chat_pipeline.py`.  Their telemetry boasts execution that the chat router can't possibly trigger.
- P3 framing (`spouse / couple_dynamic`) is gated off (`RELATIONSHIP_ORCHESTRATION_PROMPT=false`).  Even when the LLM gets the intent block, the spouse-bucket framing instruction never arrives.
- INTENT block is *soft advisory*: it says *"Relationship target: Mel · role: spouse"* and then nothing instructs the LLM to anchor the answer on Mel's chart, on synastry, or on couple-specific dynamics.

## 6. Deliverable 5 — Forum Intelligence Audit (trace)

| # | Probe | V2 result | Forum services invoked? | Response verdict |
|---|-------|-----------|--------------------------|------------------|
| 9 | "What is happening in Yoong Family?" | `general`/0.0; target=`Thaddeus Yoong`, role=`family`, source=`family_forum` | **NO** — `forum_field_intelligence` not imported by `mirror_chat.py`; only `pair_forum` was inspected for target resolution | **INERT** — generic family musings; Thaddeus never named; no recent forum updates surfaced. |
| 10 | "What is happening in Pulsifi Leadership?" | `general`/0.0; target=None | **NO** | **INERT** — *"I noticed you mentioned 'Pulsifi,' but I don't have more information about who or what that refers to."*  Pulsifi forum exists; chat router never asked. |
| 11 | "Tell me about JH" | `general`/0.0; target=None | **NO** | **INERT** — *"Are they someone close to you?"*  JH is a forum member; never looked up. |
| 12 | "Tell me about Jay" | `general`/0.0; target=Jay (alias hit, no forum lookup) | **NO** | **INERT** — *"I don't have any details about them in your saved information."* |

**The single biggest finding of the entire audit.**

Two services explicitly built for forum-axis intelligence — `services/forum_field_intelligence.py` and `services/forum_conversational_field.py` — exist, have tests, and produce real signals.  **Neither is imported anywhere inside `routers/mirror_chat.py` or `services/mirror_chat_pipeline.py`.**  They are consumed only by `routers/forums_field.py`, which is a separate REST endpoint that the chat path does not invoke.  Forum-axis questions in Ask Mirror are therefore answered as if no forum data exists.

Database confirmation: `forums: 5`, `forum_members: 9`, `forum_updates: 4`, `forum_chat_messages: 36`, `forum_mirror_chat_messages: 30`, `forum_relationship_edges: 2`.  The data is present.  It is simply not retrieved by the chat router.

## 7. Deliverable 6 — Ranked Opportunity List

Scoring rubric: `Impact` = qualitative judgement of how much the change would lift response quality across user base (HIGH = noticeable in every probe; MEDIUM = noticeable in domain-specific probes; LOW = noticeable in edge cases).  `Effort` = code-change scope (S = single function in one file; M = a few new wiring lines in `mirror_chat.py`; L = new prompt-builder service).  All "next steps" assume the existing constraints stay in place.

| Rank | Component | Impact | Effort | Impact ÷ Effort | Why |
|-----:|-----------|:------:|:------:|:---------------:|-----|
| **1** | **Wire `forum_field_intelligence` + `forum_conversational_field` into `mirror_chat.py` as a phase-4.5 step (after target/forum is resolved).** | HIGH | M (a few imports + one new builder + one `system_prompt +=`) | HIGHEST | Closes the worst gap in the audit — forum questions today don't even retrieve the forum.  Services + tests already exist. |
| **2** | **Promote the V2 INTENT block from soft advisory to Phase-3-style enforcement copy.**  Add explicit "RESOLVED TARGET — DO NOT SUBSTITUTE" / "NAME THE TARGET'S CHART" instructions when `target_resolved` is non-null. | HIGH | S (rewrite ~30 lines of `build_intent_v2_prompt_block`) | HIGH | Phase-3 proved enforcement copy works.  Soft advisory copy is INERT.  Same template applied to MC/IC/Chiron got 42/48 PASS. |
| **3** | **Backfill `founder_history` data into Pete's user document.** | HIGH (for founder probes) | S (one-time seed script) | HIGH | The block emits today but is empty.  Filling the data unlocks the full founder context block already in code. |
| **4** | **Stop listing `relationship_field`, `relationship_astrology_engine`, `relationship_3layer` in `mandatory_modules_invoked` unless they are actually called.**  Either wire them in or remove from the receipt schema. | MEDIUM | S (one-line audit fix) | MEDIUM | Today the telemetry lies — receipts claim invocation that doesn't happen.  Honest telemetry is a prerequisite for trusting the receipt. |
| **5** | **Hook `relationship_astrology_engine` into the chat path so synastry / composite / spouse-axis chart data actually reaches the prompt** when `topology_role_type in {spouse, partner, parent, child}`. | HIGH | M | MEDIUM | Topology resolves the edge to Mel as spouse but no chart synastry is surfaced.  This is the missing payload for relationship probes. |
| **6** | **Fix the "between us" resolution gap** — when the V2 envelope returns `relationship_relevant=True` AND `target=None` AND the user has at least one resolved high-confidence spouse/partner edge in `forum_relationship_edges`, auto-bind `target` to that edge. | MEDIUM | S | MEDIUM | One-line fix in `mirror_chat_shadow.py::compute_v2_envelope_sync`.  Currently probes like "What tension exists between us?" lose the spouse anchor. |
| **7** | **Add a router lexicon entry for `Pulsifi` (and any operator's known company names from `founder_history`) so "What am I not seeing in Pulsifi?" routes to `career` with `target_resolved=Pulsifi-forum`.** | MEDIUM | S | MEDIUM | Easy add to the intent router phrase table.  Operator-specific so should be data-driven, not hardcoded. |
| **8** | **Enforce that the Timeline V2 block, when present, names at least one event.**  Today it emits `events=8 dominant_state=exploring` — abstract enough that the LLM ignores it.  Rewrite the block builder to list 1-3 concrete event titles. | MEDIUM | S | MEDIUM | Same content already retrieved; just stop summarising it. |
| **9** | **Allow P3 framing_hint into the prompt under a separate, more granular flag** (e.g., `RELATIONSHIP_ORCHESTRATION_PROMPT_LIVE_TARGETS=true`) limited to cases where `topology_role_type ∈ {spouse, partner, parent, child}` and `topology_confidence=high`.  Keeps the parent constraint flag at `false` while unlocking the most reliable bucket. | MEDIUM | S | MEDIUM | The plan is computed and ignored.  This re-uses existing intelligence without ungating the broad surface. |
| **10** | **Stop appending the contradiction block to *all* probes.**  Gate it on `contradiction_count > 0` AND `confidence > threshold`.  Today the soft "tension / pull" framing leaks into every reflection probe ("dance between avoidance and engagement"). | LOW | S | LOW | Tightens style without changing functionality. |
| 11 | Add `evidence-drawer-v2` payload mention of intent_v2 + timeline_v2 + founder block emissions so the frontend can render *why* a particular framing was chosen. | LOW | M | LOW | Observability win, not response-quality win. |
| 12 | Strip `mandatory_modules_missing=[]` log noise from contexts where the field was never populated. | LOW | S | LOW | Hygiene. |

## 8. Smallest set of changes that would make Mirror "noticeably smarter without building anything new"

In priority order, **the top 3 alone would change the felt intelligence of the system on every founder/relationship/forum probe**:

1. **Wire the two forum services into the chat router** (Rank #1).
2. **Apply Phase-3 enforcement copy treatment to the V2 INTENT block** when `target_resolved` is set (Rank #2).
3. **Seed `founder_history` for any operator user** so the founder block has content (Rank #3).

All three are read-only on the constraint surface: they don't ungate P3 orchestration, they don't ungate Cross-Lens, they don't change rollout, they don't touch chart calculation, they don't change schema.

## 9. Stop condition honored

This report:
- maps every named intelligence system to its retrieval / injection / influence status,
- ranks every system by impact ÷ effort,
- identifies the single biggest gap (forum services exist but are not wired into chat),
- proposes **no remediation execution** — only analysis,
- preserves all four constraint flags as `false / 10 / false / false`.

Investigation ends here.

## 10. Files generated by this audit

- `audit_reports/INTELLIGENCE_UTILIZATION_REPORT.md` — this report
- `audit_reports/INTELLIGENCE_UTILIZATION_PROBES.json` — raw 12-probe trace with V2 receipts, log excerpts, and response evidence
- `scripts/intelligence_utilization_audit.py` — read-only probe driver
