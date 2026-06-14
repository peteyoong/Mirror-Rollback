# RELATIONSHIP FIELD V2 — Orchestration Audit (Read-Only)

**Date:** 2026-06-14
**Scope:** End-to-end read-only audit of relationship-aware query
orchestration across five surfaces — **Ask Mirror, Forum Chat, Astrology
Chat, How This Person Maps To Me, Relationship Insight V2**.
**Mandate:** Map where relationship context is **preserved vs lost** for
seven signals — *active frame · target person · relationship role ·
closeness/weight · forum topology · prior mappings · lens-leading
logic*. No code, no DB writes, no migrations, no flag changes, no
deploys. All findings derived from live source (`/app/backend`,
`/app/frontend`) and a local read-only DB probe of Pete's network.

---

## 0. Surface Map (entry points → orchestration path)

| Surface                            | Frontend                                                | Endpoint                                  | Orchestrator                                       | Receipt persisted? |
| ---------------------------------- | ------------------------------------------------------- | ----------------------------------------- | -------------------------------------------------- | :---: |
| **Ask Mirror (generalist)**        | `components/MirrorChat.tsx`                             | `POST /api/mirror/chat` (lens=null)       | `compute_v2_envelope_sync` → `enrich_v2_receipt`   | YES (`mirror_chat_retrieval_receipts`) |
| **Ask Mirror (lens=astrology)**    | `components/astrology/*` → `MirrorChat.tsx` (lens set)  | `POST /api/mirror/chat` (lens=astrology)  | Same as above + `astrology_chat_router` (mode‐only) | YES |
| **Ask Mirror about person**        | `app/people/[id]/chat.tsx`                              | `POST /api/mirror/chat` + `about_person_id` | Same; `frame=member`                              | YES |
| **Life Tab chat**                  | `app/life/chat/[domain].tsx`                            | `POST /api/mirror/chat` + `life_domain`   | Same; `life_domain` routed                         | YES |
| **Forum Chat**                     | `components/ForumChatView.tsx`                          | `POST /api/forums/{fid}/chat`             | `forum_mirror_orchestrator` + FKR-v1               | NO (own log only) |
| **How This Person Maps To Me**     | `app/forums/mappings.tsx`                               | `POST /api/forum-mappings`                | `forum_hd_mapping.compute_*` + `build_relationship_bazi` | NO (returns rendered card) |
| **Relationship Insight V2**        | `components/RelationshipInsightV2Card.tsx`              | `GET /api/relationship-insight-v2/{uid}`  | Direct chart pair compute (no V2 router)           | NO |

Three independent orchestration trees exist:

1. **Mirror Chat tree** (V2 router + lexicon enrichment + intent prompt block)
2. **Forum Chat tree** (forum_mirror_orchestrator + FKR-v1 evidence)
3. **Mapping/Insight tree** (per-pair lens compute, no router)

These trees **do not share a target resolution layer**. Each rebuilds
the relationship context from its own primary key (user_id+message vs
forum_id+target_member_id vs user_id+other_name).

---

## 1. The Seven-Signal Truth Table

Legend: ✅ preserved · ⚠️ partially preserved · ❌ lost / not surfaced
into the live prompt path. Receipt-only signals (not consumed by the
LLM) count as ⚠️.

| Signal                       | Ask Mirror (generalist) | Ask Mirror (astrology lens) | Ask Mirror /people/[id] | Life Tab chat | Forum Chat | How They Map To Me | Relationship Insight V2 |
| ---------------------------- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Active frame (Me/Member/Forum) | ⚠️¹ | ⚠️¹ | ✅ (`frame=member`) | ✅ (`frame=self`/`forum`) | ✅ (`mode`) | ✅ (forum) | ⚠️ (assumed pair) |
| Target person                | ⚠️² | ⚠️² | ✅ (id passed) | ⚠️² | ✅ (target_member_id) | ✅ (forum_id+pair) | ✅ (other_name + lookup) |
| Relationship role            | ⚠️³ | ⚠️³ | ⚠️³ | ⚠️³ | ✅ (resolver) | ✅ (resolver) | ❌⁴ |
| Closeness / weight           | ❌⁵ | ❌⁵ | ❌⁵ | ❌⁵ | ✅⁶ | ✅⁶ | ❌ |
| Forum topology               | ❌⁷ | ❌⁷ | ❌⁷ | ❌⁷ | ✅ | ✅ | ❌ |
| Prior relational mappings    | ❌ | ❌ | ❌ | ❌ | ⚠️ (recent forum_chat_messages) | ❌ | ❌ |
| Lens-leading logic           | ⚠️⁸ | ⚠️⁸ | ⚠️⁸ | ⚠️⁸ | ❌⁹ | ❌⁹ | ❌¹⁰ |

### Footnotes

1. `_derive_frame()` returns `"self"` whenever no `about_person_id`
   AND no `forum_topology` are supplied (the case for plain Ask Mirror).
   Frame is **never promoted post-resolution** even after lexicon
   enrichment binds a spouse target via edges.
   (`services/mirror_chat_shadow.py` L39-55)

2. Resolved only after `enrich_v2_receipt` runs — i.e. via
   `forum_relationship_edges` member-alias substring match, **not via
   `saved_people` for Pete's actual family** (Pete's `saved_people`
   contains synthetic test entries only; Mel/Thaddeus/Isaac live in
   `forum_relationship_edges`).

3. Role is populated only after the post-router fallback path
   (`resolve_target_via_forums`) re-plans P3 orchestration with
   `topology_role_type`. The role string IS injected into the
   "RESOLVED TARGET (HIGH CONFIDENCE)" mandate block in the prompt
   (`mirror_chat_phase4_enrichment.py` L780-839). However:
   - this fires **only when `resolution_source` ∈ {forum_member,
     pair_forum, family_forum, business_forum, alias_spouse_via_*}** —
     the *enriched* lexicon source (`member_alias_lexicon`) does NOT
     satisfy this gate, so the mandate block silently skips and falls
     through to the soft "`Relationship target: bound (role: X)`"
     line instead (`L840-843`).
   - `RELATIONSHIP_ORCHESTRATION_PROMPT=false` keeps `framing_hint`
     out of the prompt regardless.

4. `/api/relationship-insight-v2` does not consult
   `relationship_resolver.resolve_relationship` — the user supplies
   `context=spouse` as a *query param string* and it is passed
   verbatim to `generate_3layer_insight` without grounding in
   `forum_relationship_edges`. If the user types `context=foo` the
   card still renders.

5. The mirror-chat shadow router computes a soft `closeness` (0.7 for
   partner/spouse, 0.5 else) inside `_b1_load_saved_people`
   (`mirror_chat.py` L173-181) — but this is keyed off the
   `saved_people.relationship_type` field, which for real-family
   users (Pete) is **empty / wrong** because the actual roles live
   in `forum_relationship_edges`. The lexicon enrichment writes
   `role` but **does not back-fill `closeness` or `relationship_weight`**.

6. Computed by `services.relationship_resolver.resolve_relationship`
   with the `forum_relationship_edges → relationship_mappings →
   saved_people → forum_members → forum_inference` ladder. Emits
   `{closeness, emotional_weight}` ∈ {high, medium, low}.

7. `MirrorChat.tsx`, `people/[id]/chat.tsx`, `life/chat/[domain].tsx`
   never set `forum_topology` in the payload. Confirmed via grep
   across `/app/frontend/app` and `/app/frontend/components`.

8. `plan_lens_priority()` runs and writes
   `relationship_orchestration_v1.lens_priority_after` into the
   receipt. The live prompt path reads `lens_priority` from the
   intent envelope, **not** from the plan — gated behind
   `RELATIONSHIP_ORCHESTRATION_PROMPT=false`
   (`mirror_chat_phase4_enrichment.py` L861-866).

9. Forum Chat does not call the V2 router at all; it builds its own
   `forum_mirror_orchestrator` payload which selects lens emphasis
   structurally (astrology layered block for `life_domain=relationship`,
   V8 field synthesis for `intent=astrology+house+target`) but does
   not produce a numeric lens priority list.

10. V2 card collects all five lenses in parallel without re-ranking.
    The card layout enforces order (HD → Enneagram → Astrology → BaZi)
    inside the "Why this is so strong" surface, identical for every pair.

---

## 2. Where Context Is Preserved vs Lost — by Stage

### 2.1 Ask Mirror — staged orchestration trace

```
HTTP POST /api/mirror/chat
  │
  ├─ MirrorChatRequest validated
  │     payload from MirrorChat.tsx: NO about_person_id, NO forum_topology,
  │     NO life_domain. (people/[id]/chat sets about_person_id only;
  │     life/chat/[domain] sets life_domain only.)
  │
  ├─ B1 shadow hook
  │   ├─ _b1_load_saved_people()     [reads db.saved_people]
  │   │     closeness defaulted 0.7 (partner/spouse) or 0.5
  │   ├─ _derive_frame()              → "self" (NO topology, NO person_id)
  │   ├─ compute_v2_envelope_sync()
  │   │     ├─ resolve_relationship_context()
  │   │     │     1. explicit target_id?     (none)
  │   │     │     2. name match saved_people (synthetic-only for Pete)
  │   │     │     3. pronoun + last_target   (not threaded across turns)
  │   │     │     4. forum default           (frame=self → skipped)
  │   │     │     5. proper-name fallback    → target_unresolved_name
  │   │     │                                  + proposed_action (receipt-only)
  │   │     ├─ classify_intent_v2()    primary_domain, lens_priority
  │   │     ├─ plan_lens_priority()    bucket + framing_hint + lens reorder
  │   │     │   ── PLAN COMPUTED BUT NOT INJECTED (FLAG OFF) ──
  │   │     └─ cross_lens_synthesis_v2 (receipt-only)
  │   │
  │   └─ enrich_v2_receipt()          [reads forum_relationship_edges /
  │         forum_members / forums / users]
  │         ├─ forum-name lexicon match     (e.g. "Pete & Mel")
  │         ├─ member-alias lexicon match   (binds target+forum_id)
  │         ├─ spouse auto-bind             (when relationship-intent
  │         │                                detected, single spouse edge)
  │         └─ founder/company phrase activation
  │
  ├─ R3b forum-fallback resolution  (only if NOT already resolved)
  │   ├─ resolve_target_via_forums()  (PFS-2.1 topology-first)
  │   │     resolution_source ∈ {pair_forum, family_forum,
  │   │                          business_forum, alias_spouse_via_*}
  │   └─ re-plan P3 orchestration with topology role
  │
  ├─ build_intent_v2_prompt_block()
  │     emits "RESOLVED TARGET (HIGH CONFIDENCE)" mandate IFF
  │     resolution_source ∈ R3b-gated set.
  │     Lexicon-enrichment sources (member_alias_lexicon, spouse_auto_bind)
  │     fall through to soft line at L840-843 — NO mandate block.
  │
  └─ LLM call (the response the user sees)
```

#### What survives into the LLM prompt for "Tell me about Mel" (Pete, plain Ask Mirror)

| Field                              | Surfaces in prompt? | Source                              |
| ---------------------------------- | :---: | --- |
| Active frame                       | ❌    | derived="self", never injected      |
| Target ID (Mel's user_id)          | ❌    | resolved but not printed            |
| Target name "Mel"                  | ⚠️    | only via the soft "bound" line      |
| Role "spouse"                      | ⚠️    | soft line only — NOT mandate block  |
| Closeness / weight                 | ❌    | not computed for non-saved_people   |
| Forum topology (Pete & Mel forum)  | ❌    | not supplied by FE; lex returns id  |
| Recent Pete↔Mel mappings           | ❌    | mirror_chat doesn't read forum-mappings |
| Lens reorder (spouse → astrology)  | ❌    | RELATIONSHIP_ORCHESTRATION_PROMPT=false |
| Framing hint `couple_dynamic`      | ❌    | same flag                           |

### 2.2 Forum Chat — staged trace

```
HTTP POST /api/forums/{forum_id}/chat
  │
  ├─ ForumChatRequest      (mode, target_member_id)
  ├─ membership check       (asker ∈ forum)
  ├─ _build_forum_chat_context  (all member lens cards)
  │
  ├─ build_relational_orchestrator_payload()
  │     ├─ classify_question_intent()   life_domain (relationship / career / …)
  │     ├─ Phase 1 — Resolve target
  │     │     priority: explicit_mode_member > alias > forum_member_name
  │     │     + spouse auto-promotion (when life_domain=relationship)
  │     ├─ Phase 2 — classify_query_intent()   intent + house_number
  │     ├─ Phase 3 — resolve_relationship()
  │     │     ladder: forum_relationship_edges → relationship_mappings →
  │     │            saved_people → forum_members → forum_inference
  │     │     → role, closeness, emotional_weight, relationship_source
  │     └─ Phase 4 — build_layered_relationship_block (astrology DC/7th/Venus)
  │
  ├─ build_fkr_evidence_block()  (Forum Knowledge Retrieval v1)
  │     reads charts / users / forum_relationship_edges / forum_members /
  │           forums / pattern_memory / user_timeline
  │     → deterministic "DETERMINISTIC EVIDENCE" block in prompt
  │
  └─ LLM call
```

**Verdict:** Forum Chat is the strongest surface — `forum_id` is bound
at the URL level, target/role/closeness/weight all resolve through
`resolve_relationship`, and FKR-v1 supplies factual evidence.
**Gap:** No call to the V2 router, so the receipt persistence /
cross-lens dashboards never see Forum Chat traffic. Two parallel
graphs of telemetry exist (Mirror receipts vs Forum logs).

### 2.3 How This Person Maps To Me

```
POST /api/forum-mappings { user_id, forum_id }
  │
  └─ For each member in forum:
        ├─ compute_astrology_signals()       attraction / tension / growth
        ├─ compute_bazi_signals()            support / tension / growth
        ├─ compute_enneagram_signals()       help / friction
        ├─ compute_numerology_signals()      themes
        ├─ build_layered_convergence()       cross-lens convergence
        ├─ resolve_relationship()            role / closeness / weight
        ├─ build_relationship_bazi()         BaZi V3 narrative card
        └─ Ophiuchus injection (when applicable)
```

**Verdict:** Single-page report style. Fully populates every signal
**per pair** but never feeds back into chat. The relationship-aware
output is read-once, not retrieved by Mirror Chat.

### 2.4 Relationship Insight V2

```
GET /api/relationship-insight-v2/{user_id}?other_name=...&context=...
  │
  ├─ _v2_find_user(user_id)
  ├─ other-user resolution ladder:
  │     1. explicit other_user_id query param
  │     2. saved_people row name match
  │     3. forum_relationship_edges (a_name / b_name) match
  │     4. users.find_one by case-insensitive name match
  ├─ R1 signal compute (forum_hd_mapping.compute_*)
  ├─ build_relationship_bazi() for diagnostics passthrough  (today's change)
  └─ generate_3layer_insight()      story / patterns / signals
```

**Verdict:** Pair-explicit. Best when `other_user_id` is passed
directly; falls back to fuzzy name match otherwise. **Doesn't read
`forum_relationship_edges.role_type` for role grounding** — uses the
free-text `context` query param verbatim, which is why "context=spouse"
works but "context=foo" still renders without erroring.

---

## 3. Live-Data Example Flows (read-only)

All flows traced for **viewer = Pete (`697f0c6abf35c0528ff06954`)**.
Pete's network from the local `test_database` probe:

```
saved_people (synthetic only):
  Test, Pete Forum 2 ×2, x, Peter Test 2B, Test Child, Test Spouse,
  Test Boss, Test Ex      ← no Mel / Thaddeus / Isaac entries

forum_relationship_edges (canonical graph):
  Pete → Mel        role=spouse  conf=high  forum=Yoong family
  Pete → Mel        role=spouse  conf=high  forum=Pete & Mel
  Pete → Thaddeus   role=child   conf=high  forum=Yoong family
  Pete → Isaac      role=child   conf=high  forum=Yoong family
  Thaddeus → Pete   role=parent  conf=high  forum=Yoong family
  Isaac → Pete      role=parent  conf=high  forum=Yoong family

Forums Pete belongs to:
  Pete & Mel     (private, 2 members)
  Yoong family   (private, 4 members)
  FM TEST 1      (1 member)
  FM Test 2      (1 member)
```

The key live-data fact: **Pete's spouse/child relationships live in
`forum_relationship_edges`, not in `saved_people`.** Every surface that
reads `saved_people` first will miss them.

---

### Flow A — Spouse: Mel

**Query:** "Tell me about Mel."

| Stage | Ask Mirror (plain) | Ask Mirror /people/[id]=Mel | Forum Chat (Pete & Mel forum) | How They Map To Me | Relationship Insight V2 |
| --- | --- | --- | --- | --- | --- |
| Frontend payload         | `lens=null` only | `+ about_person_id=697ec826…` | `+ target_member_id=697ec826…` `mode=member` | `forum_id=69dd05ea…` | `other_name=Mel&context=spouse` |
| Frame derived            | **self**         | **member**                   | **member**                                 | (n/a)               | (n/a)                          |
| Target resolution path   | `saved_people` miss → `proper_name_fallback` → lexicon `member_alias_lexicon:Mel` | `explicit_target_id` (saved_people miss inside, role stays null) | `explicit_mode_member` + `resolve_relationship` via edges | forum members + edges | name → `forum_relationship_edges` `b_name=Mel` |
| Role detected            | post-lex: `forum_peer` (lexicon default) — **NOT spouse** unless R3b runs & resolution_source matches gate | `null` (saved_people had no row for personId=697ec826) | **spouse** (edges, conf=high) | **spouse** (edges) | string `"spouse"` from URL — not validated |
| Closeness / weight       | ❌                | ❌                            | high / high                                 | high / high          | ❌                              |
| Forum topology           | ❌                | ❌                            | bound by URL                                | bound by URL         | ❌                              |
| Prompt enforcement       | Soft "Relationship target: bound" line | "RESOLVED TARGET (HIGH)" mandate IFF R3b fires | Full orchestrator block + FKR evidence + V8 anchor | (no LLM call)        | (no LLM call)                  |
| Lens lead                | `lens_priority` from intent envelope (unchanged) | Same — `astrology+`,`hd+` etc. NOT applied (flag off) | Layered Relationship Block leads (astrology DC/7th/Venus) | All 5 lenses parallel | All 5 lenses parallel         |
| Expected user-visible drift | Generic "spouse"-ish reflection only when lexicon fires; otherwise reads as solo Pete query | Mandates "treat Mel as user's resolved person" but **role is unknown** — generic relationship advice | Mel-specific, evidence-anchored answer | Static report   | Static card                    |

**Where context is lost on Flow A — plain Ask Mirror:**

1. `saved_people` has no Mel → name-match step fails.
2. Lexicon enrichment binds target via `member_alias_lexicon`, **but
   sets `role = "forum_peer"` not `spouse`** unless the spouse auto-bind
   path fires (which requires `_is_relationship_intent()` to fire on
   the message — "Tell me about Mel" does NOT match the
   `we / us / between us / our marriage / …` regex).
3. R3b `resolve_target_via_forums` only runs when V2 reports
   `target_unresolved_name` AND `not _already_resolved`. The lexicon
   step ran FIRST and set `target` → R3b skips
   (`mirror_chat.py` L1273-1280, condition `not _already_resolved`).
   Net effect: the *strongest* role-grounding path (R3b
   topology-first) is **bypassed** by the *weaker* lexicon path that
   ran a millisecond earlier.
4. Result: role stays `"forum_peer"`, the mandate block at L780-839
   doesn't fire (gate excludes `member_alias_lexicon`), prompt
   receives only the soft "bound" line.

---

### Flow B — Child: Thaddeus

**Query:** "What's coming up for Thaddeus this week?"

| Stage                   | Ask Mirror (plain)                           | Ask Mirror /people/[id]=Thaddeus | Forum Chat (Yoong family) member=Thaddeus | How They Map To Me | Relationship Insight V2 |
| ----------------------- | -------------------------------------------- | -------------------------------- | ----------------------------------------- | ------------------ | ----------------------- |
| `saved_people` match    | "Test Child" exists, "Thaddeus" does not    | not in saved_people              | (n/a — forum binds target)               | (n/a)              | (n/a)                   |
| Proper-name fallback    | `target_unresolved_name="Thaddeus"`         | already resolved                 | bypassed                                  | n/a                | n/a                     |
| Lexicon enrichment      | `forum_members.names_lc=["thaddeus","thaddeus yoong"]` → binds target + Yoong family + role=`forum_peer` | edges return parent (Thaddeus → Pete) not child — **role inverted unless edge direction respected** | edges: Pete → Thaddeus role=`child` | role=`child` | uses URL `context` verbatim |
| R3b path                | skipped (already resolved)                   | runs if unresolved                | n/a                                       | n/a                | n/a                     |
| **What surfaces**       | Mel-style soft line: "bound (role: forum_peer)"; no parenting framing | Generic /people/ mandate, role=null | Full "parenting / lineage" framing IFF `life_domain=relationship` triggers (the regex hits "Thaddeus" only as a name, NOT a relationship token — so the Layered Relationship Block does **not** lead) | Card-style       | Card-style              |

**Gap unique to Flow B:**
The life-domain classifier in `services/question_intent_router.py`
(`/app/backend/services/question_intent_router.py` L10-14) defines
`relationship` via the regex `marriage|spouse|husband|wife|partner|…`.
**"What's coming up for Thaddeus this week?"** has none of those
tokens — so even though Thaddeus is the user's **child** in
`forum_relationship_edges`, the orchestrator does NOT lead with the
`parenting` framing block. The role is correctly resolved as `child`
in the metadata but the **framing_hint `parenting`** never reaches
the prompt (`RELATIONSHIP_ORCHESTRATION_PROMPT=false`).

---

### Flow C — Child: Isaac (identical structure to Flow B)

| Stage             | Ask Mirror (plain)                                  | Forum Chat (Yoong family) member=Isaac |
| ----------------- | --------------------------------------------------- | -------------------------------------- |
| Edge resolution   | Pete → Isaac role=`child` (Yoong family)            | same                                   |
| Lexicon match     | `forum_members.names_lc=["isaac","isaac yoong"]`   | n/a                                    |
| Frame             | `self` (NOT `member`/`forum`)                       | `member`                               |
| Role surfaces?    | as `forum_peer` (lex default), not `child`          | `child` (resolver)                     |
| Framing hint      | `parenting` — flag-gated off                        | Layered Relationship Block only if msg matches relationship regex |
| Net user output   | Generic Isaac reflection; no parent voice           | Strong parent voice IFF question phrases ∈ relationship lexicon |

**Cross-flow observation:** For both children (Flow B & C), the same
*structural* gap exists — the **edge graph holds the truth, the
classifier doesn't pick it up from a child's name alone**, and the
plan is flag-gated.

---

### Flow D — Forum Member (not family)

**Setup:** Pete is in `FM TEST 1` and `FM Test 2` forums (single-
member forums in local DB — but imagine a multi-member professional
forum, e.g. "Pulsifi leadership").
**Query:** "How does Bee land for me in this forum?"

| Stage                | Ask Mirror (plain) | Forum Chat (selected forum) |
| -------------------- | ------------------ | --------------------------- |
| Frame                | `self`             | `forum` or `member`         |
| Target resolution    | depends on `Bee` being in `forum_members.names_lc` for any of Pete's forums; otherwise `proper_name_fallback` → `target_unresolved_name="Bee"` → `proposed_action: add_to_circle` (receipt-only) | `explicit_mode_member` if selected, else `_resolve_target_via_forum_members` |
| Forum topology       | ❌ not passed       | ✅ forum_id bound            |
| Closeness / weight   | ❌                  | from `forum_relationship_edges` if present, else `forum_inference` (e.g. private 2-member forum → partner) |
| Role                 | `forum_peer` (lex) or null | `forum_member` / actual edge role |
| FKR evidence         | n/a                | Yes — pulls Bee's chart, comparisons, recent forum_chat_messages |

**Gap:** In Ask Mirror, if Bee is not in any of Pete's saved_people
AND not in any of Pete's forum_members, the resolver emits a
`proposed_action: add_to_circle` payload — **but no UI is wired to
surface this CTA** (receipt-only per `relationship_router_v2.py`
docstring L11-18). The user sees a generic response that doesn't
acknowledge the unresolved target.

---

### Flow E — Unknown Person ("Patricia")

**Query:** "What does Mirror think about Patricia?" (Patricia is **not**
in Pete's saved_people, edges, or forum_members.)

| Stage                | Ask Mirror (plain)                                  |
| -------------------- | --------------------------------------------------- |
| `saved_people` match | ❌                                                   |
| Lexicon enrichment   | no member alias hit, no forum-name hit              |
| Spouse auto-bind     | skipped (no relationship-intent regex hit)          |
| Missing-target fallback | `target_unresolved_name="Patricia"`, `proposed_action.type="add_to_circle"`, `confidence≈0.55` |
| Prompt block         | Emits at L844-851: "Acknowledge this rather than guessing who they are. Ask the user who 'Patricia' is." |
| Frame                | `self` (never promoted)                             |
| Lens lead            | Intent envelope only                                |

**Verdict:** Flow E is the **best-handled "unknown person" path** —
the prompt explicitly instructs the LLM to *acknowledge non-resolution*
rather than hallucinate. But the `proposed_action` is **dead-lettered**:
no frontend reads `v2_receipt.proposed_action` to render an
"Add Patricia to your circle" CTA.

---

## 4. Concrete Loss-of-Context Inventory (the bug surface)

Each row is a directly-observable behavioural gap, ordered by
relationship-field severity. **No fixes yet — read-only inventory.**

| # | Loss point                                                                 | Where         | Effect                                                                                    | Severity |
| - | -------------------------------------------------------------------------- | ------------- | ----------------------------------------------------------------------------------------- | :---: |
| 1 | Frame stays `self` even after lexicon binds a target with a `spouse`/`child` edge | Ask Mirror | LLM treats the question as solo self-inquiry; no "between you and Mel" framing            | 🔴 critical |
| 2 | R3b path skipped because lexicon already set `target` → loses topology-first role grounding | Ask Mirror | role stays at lexicon default (`forum_peer`) instead of `spouse`/`child`                  | 🔴 critical |
| 3 | RESOLVED-TARGET mandate block gated to a specific `resolution_source` set that excludes lexicon | Ask Mirror | Strong "treat X as the user's resolved spouse" mandate **silently doesn't fire**          | 🔴 critical |
| 4 | `RELATIONSHIP_ORCHESTRATION_PROMPT=false` keeps `framing_hint` + `lens_priority_after` out of the prompt | Ask Mirror | Lens-leading logic exists but is invisible to the LLM                                     | 🟠 high     |
| 5 | `MirrorChat.tsx` (the default Ask Mirror surface) never passes `forum_topology` | Ask Mirror | No way to disambiguate which forum context the user is reflecting from                     | 🟠 high     |
| 6 | `closeness / relationship_weight` never propagate from `forum_relationship_edges` into the V2 receipt | Ask Mirror | "high-weight" relationships (spouse, child) treated identically to acquaintances           | 🟠 high     |
| 7 | Forum Chat doesn't emit V2 receipts                                        | Forum Chat    | Two parallel telemetry trees; dashboards can't see forum traffic patterns                  | 🟡 medium   |
| 8 | `proposed_action.type=add_to_circle` is dead-lettered (no UI consumer)     | All Mirror surfaces | Users with new people in messages never see "Add to Circle" CTA                            | 🟡 medium   |
| 9 | Life-domain classifier regex hard-codes role nouns — child name alone doesn't trigger `relationship` domain | Forum + Mirror | "What's coming up for Thaddeus?" doesn't get the parenting frame                          | 🟡 medium   |
| 10 | Relationship Insight V2 doesn't ground `context` against `forum_relationship_edges` | Insight V2 | `context=spouse` is trusted blindly; no contradiction check vs the edge graph              | 🟢 low      |
| 11 | Prior Pete↔Mel mappings (`forum-mappings` output) never surface in Mirror Chat | Ask Mirror   | Mirror has no memory of yesterday's relationship synthesis                                 | 🟢 low      |

---

## 5. Architecture Diagnosis

There are three orthogonal causes:

### A. **Two target-resolution layers, race condition between them.**
- Layer 1: `relationship_router_v2.resolve_relationship_context()` —
  reads `saved_people` only.
- Layer 2 (post-router): `enrich_v2_receipt()` — reads
  `forum_relationship_edges` + `forum_members` + `forums`.
- Layer 3 (post-enrichment): `resolve_target_via_forums()` — would
  re-bind with topology role, but only runs if Layer 2 didn't.

For Pete's real network (where roles live in edges, not in
`saved_people`), Layer 2 always wins → role downgraded to
`forum_peer` → Layer 3 never fires → role mandate block silently
falls through.

**Architecturally:** there is no single canonical "resolve who and
what role for this question" function. Three different paths produce
three different role strings, with no reconciliation.

### B. **Computed plan ≠ injected plan.**
`relationship_orchestration_v1.plan_lens_priority()` produces a
beautifully-structured plan (bucket, framing_hint, domain_bias,
lens_priority_after, applied_rules) and writes it to the receipt
— but the only consumer of `lens_priority_after` is the dashboard.
The live LLM prompt reads `lens_priority` from the **pre-plan**
intent envelope. The flag `RELATIONSHIP_ORCHESTRATION_PROMPT` is
the gate; while it is `false`, the plan is observability-only.

### C. **Surface fragmentation.**
- Ask Mirror = thinking layer (V2 router + receipt + dashboards).
- Forum Chat = retrieval layer (FKR + orchestrator + V8 anchor).
- Mappings + Insight V2 = report layer (one-shot lens cards).

None of these three trees read each other's outputs. A user who has
just seen Mel's full Relationship Insight V2 card and then types
"Tell me about Mel" in Ask Mirror gets an answer with **none of the
mapping evidence retrieved** — because the retrieval graph for
Mirror Chat doesn't include `forum_mappings` results.

---

## 6. What the User Asked Mirror To Become

Recap of the directive:

> When I ask "Tell me about Mel" the system automatically understands:
> – Mel is my spouse
> – spouse context should be activated
> – relationship field should be available
> – astrology, HD, BaZi and Enneagram should answer through the
>   relationship frame rather than as an isolated person profile

Mapping the directive onto today's machinery:

| Requirement                                  | Already exists? | Where                                                       | What's missing                                                                                                  |
| -------------------------------------------- | :---: | --- | --- |
| Detect "Mel is the user's spouse"           | ✅    | `forum_relationship_edges` + `relationship_resolver`         | Mirror Chat's resolver doesn't read edges first                                                                  |
| Activate "spouse context"                    | ⚠️    | `relationship_orchestration_v1` (bucket=spouse, framing=couple_dynamic, lens_priority_after) | Gated behind `RELATIONSHIP_ORCHESTRATION_PROMPT=false`; injected only at mandate-block level which has a narrow `resolution_source` gate |
| Make relationship field available            | ⚠️    | `/forum-mappings` + Relationship Insight V2 produce them    | Mirror Chat doesn't retrieve from those outputs                                                                  |
| Answer through the relationship frame        | ⚠️    | Forum Chat's `build_layered_relationship_block` does this   | Not invoked from Ask Mirror; only fires when forum chat is opened                                                |

So the building blocks exist; the assembly is incomplete. The
fastest theoretical wiring (no code in this audit) is the three steps
of Section 7.

---

## 7. Proposed Architecture (no implementation — review only)

> **Update (2026-06-14):** Superseded by
> `RELATIONSHIP_FIELD_V2_DESIGN_REFINEMENT.md`, which adds
> `relationship_stance` as a first-class field, locks the schema, and
> provides worked example envelopes for Mel · Thaddeus · Isaac ·
> forum_member · unknown person. Read that document for the current
> design; this section is preserved for change-history continuity.


A **single canonical resolver call** that Mirror Chat, Forum Chat,
and any future surface all consult before assembling a prompt.

```
                         ┌────────────────────────────┐
                         │   resolve_field(user_id,    │
                         │     message,                │
                         │     hints:{about_person_id, │
                         │            forum_topology,  │
                         │            life_domain})    │
                         └─────────────┬──────────────┘
                                       │
       ┌───────────────────────────────┼────────────────────────────────┐
       │                               │                                │
       ▼                               ▼                                ▼
  [edges first]              [saved_people fallback]         [lexicon enrichment]
  forum_relationship_edges   relationship_mappings           forum_members alias
  (canonical role + conf)    (explicit user mapping)         (proper-name match)
       │                               │                                │
       └─────────── merge with priority: edges > maps > lex ─────────────┘
                                       │
                                       ▼
                          ┌────────────────────────────┐
                          │  RelationshipField {        │
                          │    active_frame,            │
                          │    target_user_id,          │
                          │    target_name,             │
                          │    role,                    │
                          │    closeness,               │
                          │    emotional_weight,        │
                          │    forum_id,                │
                          │    framing_hint,            │
                          │    lens_priority,           │
                          │    domain_bias,             │
                          │    confidence,              │
                          │    resolution_path[]        │
                          │  }                          │
                          └─────────────┬──────────────┘
                                        │
              ┌─────────────────────────┼─────────────────────────┐
              │                         │                         │
              ▼                         ▼                         ▼
      Ask Mirror prompt        Forum Chat prompt         Insight V2 grounding
   (RESOLVED FIELD block,    (replaces ad-hoc          (validates URL `context`
    no flag gate, lens-      orchestrator paths,        against the field
    priority injected from   feeds layered block        — mismatches surface
    field.lens_priority)     deterministically)         as conflict telemetry)
```

Three deliverables required to make this real (out of scope here):

1. **A single `resolve_relationship_field()` service** that fuses today's
   three resolution layers, with `forum_relationship_edges` as the
   canonical first source, then `relationship_mappings`, then the
   lexicon scan. Returns the unified envelope above.
2. **Frontend payload normalisation.** `MirrorChat.tsx` becomes
   `forum_topology`-aware (when the user opened the chat from a forum
   tab) and `about_person_id`-aware (when opened from a People entry
   point). The default surface should also pass `last_target_id` so
   pronoun memory threads across turns.
3. **Prompt block consolidation.** Remove the `resolution_source` gate
   on the RESOLVED TARGET mandate block — let it fire on any
   high-confidence resolution (edges, mappings, or lexicon with
   confidence ≥ 0.7). Remove the `RELATIONSHIP_ORCHESTRATION_PROMPT`
   flag gate on `framing_hint` and `lens_priority_after`, OR fold
   them into the same MANDATE block.

---

## 8. Read-Only Evidence Trail

All findings sourced from:

```
# Backend orchestration
/app/backend/routers/mirror_chat.py             (Ask Mirror endpoint)
/app/backend/routers/forums_chat.py             (Forum Chat endpoint)
/app/backend/services/mirror_chat_shadow.py     (V2 envelope compute)
/app/backend/services/relationship_router_v2.py (target resolution)
/app/backend/services/relationship_orchestration_v1.py (lens plan)
/app/backend/services/v2_receipt_lexicon_enrichment.py (post-router enrichment)
/app/backend/services/mirror_chat_phase4_enrichment.py (prompt block builder)
/app/backend/services/forum_mirror_orchestrator.py (forum chat orchestrator)
/app/backend/services/relationship_resolver.py  (role/closeness/weight ladder)
/app/backend/services/question_intent_router.py (life-domain classifier)
/app/backend/services/astrology_chat_router.py  (data-mode classifier — NO relational logic)
/app/backend/server.py                          (V2 insight endpoint + MirrorChatRequest schema)

# Frontend entry points
/app/frontend/components/MirrorChat.tsx         (Ask Mirror — sends NO context fields)
/app/frontend/app/people/[id]/chat.tsx          (passes about_person_id)
/app/frontend/app/life/chat/[domain].tsx        (passes life_domain)
/app/frontend/components/ForumChatView.tsx      (passes target_member_id; no topology)
/app/frontend/app/forums/mappings.tsx           (calls /api/forum-mappings)
/app/frontend/components/RelationshipInsightV2Card.tsx (calls /api/relationship-insight-v2)

# Live DB probe (test_database, local — Pete network)
saved_people:                synthetic test entries only
forum_relationship_edges:    canonical roles (Mel=spouse, Thaddeus/Isaac=child)
forums:                      Pete & Mel (private/2), Yoong family (private/4)
```

---

## 9. Hold Point

This audit produces zero side effects:
- No file in `/app` modified
- No env flag changed
- No DB writes
- No Atlas access attempted
- `INTENT_ROUTER_V2_CUTOVER`, `INTENT_ROUTER_V2_ROLLOUT_PERCENT`,
  `RELATIONSHIP_ORCHESTRATION_PROMPT`, `CROSS_LENS_PROMPT_SURFACE`
  remain untouched.

**Awaiting user approval** on Section 7's proposed architecture before
any implementation. No coding will start without explicit go.
