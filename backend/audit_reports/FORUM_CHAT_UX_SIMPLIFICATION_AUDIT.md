# Forum Chat UX Simplification + Auto Relationship Context Resolution

## Pre-Implementation Audit (Read-Only)

**Date:** 2026-06-14
**Status:** Audit complete. **No code changes performed.** Awaiting
implementation-plan approval before any slice begins.

---

## 1. Where Visible Mode Tabs Actually Exist (UI inventory)

The user-facing `[Me · Member · Forum]` tab strip lives in **exactly one
component** — not in Ask Mirror.

| Surface                                  | File                                          | Has visible mode tabs? |
| ---------------------------------------- | --------------------------------------------- | :---: |
| **Forum Chat window**                    | `components/ForumChatView.tsx` (L207-230)     | **YES** — the only place |
| Ask Mirror (default)                     | `components/MirrorChat.tsx`                   | No |
| Ask Mirror (per-person)                  | `app/people/[id]/chat.tsx`                    | No |
| Ask Mirror (per life-domain)             | `app/life/chat/[domain].tsx`                  | No |
| How This Person Maps To Me               | `app/forums/mappings.tsx`                     | No (not a chat) |
| Relationship Insight V2 card             | `components/RelationshipInsightV2Card.tsx`    | No (not a chat) |
| Astrology / Enneagram / BaZi lens chats  | `components/{AstrologyLensView,EnneagramLensView,BaziLensViewV2}.tsx` | No |

The visible tab strip in `ForumChatView.tsx`:

```
L207-230  <View style={modeSelector}>
            {(['self', 'member', 'forum'] as ForumChatMode[]).map((m) => (
              <Pressable onPress={() => handleModeChange(m)}>...</Pressable>
            ))}
          </View>
```

Backed by the `ForumChatMode` type at `services/api.ts:1188`:

```ts
export type ForumChatMode = 'self' | 'member' | 'forum';
```

Mounted from `app/forums/[id].tsx` at L2121, with `initialMode` set
contextually at L861/L868/L876.

**Scope of the UI simplification = a single component**, plus the
parent `[id].tsx` that currently feeds `initialMode`. Everything else
is unaffected.

## 2. Current API Payloads

### 2.1 Ask Mirror (`POST /api/mirror/chat`) — already mode-less

```
{ user_id, message, lens, session_id, include_journal, include_history,
  about_person_id?, forum_topology?, life_domain?,
  pattern_thread_context?, dominant_pattern_context? }
```

No `mode` field. Frame is currently inferred server-side by
`mirror_chat_shadow._derive_frame()` from `lens / life_domain /
about_person_id / forum_topology`, and **also** by Slice 2's
`resolve_relationship_field()` which attaches the canonical
`active_frame` to the receipt.

### 2.2 Forum Chat (`POST /api/forums/{forum_id}/chat`) — has explicit mode

```
{ message, mode: 'self'|'member'|'forum',
  target_member_id?, conversation_history? }
```

Backend `ForumChatRequest` schema (`routers/forums_chat.py:99-109`)
enforces the trio. The orchestrator's `build_relational_orchestrator_payload`
in `services/forum_mirror_orchestrator.py` uses this `mode` as part of
its Phase-1 resolution priority:

```
explicit_mode_member > alias > name_match
```

…meaning `mode='member' + target_member_id` short-circuits the natural-
language resolution. **This is exactly the override the user wants
removed.**

## 3. Backend Resolver Capability — Gap Analysis

### 3.1 What exists today (Slices 1-3 already shipped)

`services/relationship_field_v2.py` resolves:

```
active_frame ∈ { SELF, MEMBER, FORUM, RELATIONAL }
target_person, role, stance, directionality, closeness, weight,
forum_topology, confidence, source, conflicts, missing_data,
proposed_action  (for unresolved)
```

Used today only by Ask Mirror (Slice 2 receipt attach + Slice 3 prompt
gate). **Not yet called from Forum Chat.**

### 3.2 What's missing for this initiative

| Capability the user wants                | Status in resolver                      |
| ---------------------------------------- | --------------------------------------- |
| SELF frame                               | ✅ implemented (Slice 1)                 |
| MEMBER frame                             | ✅ implemented                           |
| FORUM frame                              | ✅ implemented                           |
| **PAIRWISE** ("Mel and Isaac")            | ❌ **not implemented** — needs new frame + dual-target resolution |
| **MULTI_PERSON** ("my children")          | ❌ **not implemented** — needs scope-class resolution (children, parents, colleagues, etc.) |
| **AMBIGUOUS / UNKNOWN**                   | ⚠️ partial — `proposed_unresolved` exists for one unknown name; **no multi-candidate clarification** state |
| Forum-intent detection ("our family")    | ❌ no current code path; would need a small classifier (regex/keyword + forum-membership cross-check) |
| Pronoun memory ("how is _he_ doing")     | ⚠️ field exists (`last_target_id`) but is never threaded — FE passes null |
| @mention resolution                      | ❌ no `@name` parser anywhere                  |

A **pairwise-dynamics endpoint already exists** in
`routers/forums_intelligence.py:541` (`POST /api/forums/{fid}/pairwise-dynamics`)
— so a pairwise *answer* surface is available; what is missing is a
**chat resolver** that recognises the pairwise *intent* and delegates
to it.

## 4. Forum-Mapping Ambiguity Reality Check (live DB)

A read-only count of first-name collisions in the local
`test_database.users` collection:

| First name (lowercased) | distinct users |
| ----------------------- | :------------: |
| test                    | 20             |
| pete                    | **12**         |
| hd                      | 4              |
| luna                    | 4              |
| verifier                | 4              |
| numerology              | 3              |
| yoong                   | 2              |
| mel                     | 2              |
| finaltest               | 2              |
| num                     | 2              |

Production scale will make this worse, not better. "Tell me about
Peter / Pete / Luna" without disambiguation will become an actual user
bug as soon as a forum contains multiple matches. **The resolver
must return a multi-candidate clarification state, not pick one
silently.**

## 5. Proposed Architecture Additions (DESIGN ONLY)

### 5.1 Extend `ActiveFrame`

```python
class ActiveFrame:
    SELF          = "SELF"
    MEMBER        = "MEMBER"
    FORUM         = "FORUM"
    PAIRWISE      = "PAIRWISE"      # NEW
    MULTI_PERSON  = "MULTI_PERSON"  # NEW
    AMBIGUOUS     = "AMBIGUOUS"     # NEW (distinct from missing-data)
    RELATIONAL    = "RELATIONAL"    # kept (existing)
```

### 5.2 Extend `RelationshipField` (additive only)

```python
target_user_id_b   : Optional[str]    # PAIRWISE secondary
target_name_b      : Optional[str]
scope_class        : Optional[str]    # "children"|"parents"|"forum"|"all"
ambiguity_candidates : List[{
    user_id, name, role?, forum_id?, forum_name?,
    confidence, source
}]
```

No backend schema change. No new collections.

### 5.3 New resolver order (replaces current race)

```
priority:
  1. explicit @mention                                   → MEMBER
  2. explicit about_person_id / target_member_id (hint)  → MEMBER (validated against edges)
  3. forum_relationship_edges direct name hit            → MEMBER  (canonical)
  4. exact member name within active forum               → MEMBER  (forum-scoped)
  5. saved_people / relationship_mappings                → MEMBER
  6. pairwise pattern ("X and Y", "X & Y")               → PAIRWISE
  7. multi-person scope ("my children", "all my forum
     members")                                            → MULTI_PERSON
  8. forum-intent ("our family", "in this group")        → FORUM
  9. self-intent ("I", "me", "my chart")                 → SELF
 10. proper-name fallback with >1 candidate              → AMBIGUOUS
 11. proper-name fallback with 1 unknown                 → proposed_unresolved (existing)
```

The current `forum_mirror_orchestrator` "explicit_mode_member > alias
> name_match" priority is **demoted**. UI mode hints become tiebreakers
at confidence-equal positions only.

### 5.4 Resolved Context payload returned to FE

```jsonc
{
  "frame":             "MEMBER",
  "label":             "Mel · Spouse",          // pre-rendered display
  "target_id":         "697ec826ad4b18f75bf42616",
  "target_name":       "Mel",
  "stance":            "covenant_partner",
  "confidence":        0.95,
  "source":            "forum_relationship_edges",
  "needs_clarification": false,
  "candidates":        []
}
```

When `needs_clarification: true`:

```jsonc
{
  "frame":   "AMBIGUOUS",
  "label":   "Needs clarification",
  "candidates": [
    {"user_id":"...","name":"Pete","role":"self","forum":"—",
     "confidence":0.62,"source":"self_match"},
    {"user_id":"...","name":"Peter Vogt","role":"forum_member",
     "forum":"EO Forum","confidence":0.58,"source":"forum_members"},
    {"user_id":"...","name":"Peter Cohen","role":"close_friend",
     "forum":"Founders","confidence":0.52,"source":"saved_people"}
  ],
  "needs_clarification": true,
  "clarification_prompt": "I found more than one Peter. Which one do you mean?"
}
```

## 6. Frontend Surface Map

### 6.1 Files to modify (proposal — none touched yet)

```
M  components/ForumChatView.tsx
   └─ remove L207-230 mode selector
   └─ remove L106-110 member-picker auto-open on mode change
   └─ keep internal `mode` state if API still requires it (transitional)
   └─ add <ResolvedContextChip /> at top of message area
   └─ add <AmbiguityClarificationPanel /> conditional on needs_clarification

A  components/relationship/ResolvedContextChip.tsx              (new)
A  components/relationship/AmbiguityClarificationPanel.tsx       (new)

M  app/forums/[id].tsx
   └─ remove `forumChatInitialMode` state (L345, L861-876)
   └─ keep entry-point hints (target id, forum id) as passthroughs

M  services/api.ts
   └─ `ForumChatMode` becomes optional in payload (transitional)
   └─ new ResolvedContext / AmbiguityCandidate types

(NO change to)
   - components/MirrorChat.tsx   (Ask Mirror — already mode-less)
   - components/RelationshipInsightV2Card.tsx
   - components/astrology/* / EnneagramLensView / BaziLensViewV2
```

### 6.2 Files to NOT touch

The user's "do not break working surfaces" list is structurally
isolated from the chat surface:

- `app/forums/mappings.tsx` (How They Map To Me) — separate route
- `components/RelationshipInsightV2Card.tsx` — separate component
- `services/relationship_field_v2.py` — additive only (new frames)
- `services/relationship_field_v2_prompt.py` — flag-gated, untouched
- All BaZi / Ophiuchus / Variant-A engine code
- `services/relationship_bazi_engine.py`
- Existing forum-mappings diagnostics

## 7. Before / After UX Flow

### 7.1 Before (today)

```
User opens Forum X
   │
   ▼
ForumChatView mounts with initialMode='self'
   │
   ▼
   [ Me ][ Member ][ Forum ]   ← visible tab strip
       ▲
       └── user clicks one (or doesn't notice and asks anyway)
   │
   ▼
User types "What does Thaddeus need from me?"
   │
   ▼
mode = 'self'  (still)
   │
   ▼
Backend reads mode='self' as the strongest signal
   │
   ▼
Answer framed as user-self-reflection
   │
   ▼
User confused: "Why didn't it answer about Thaddeus?"
```

### 7.2 After (proposed)

```
User opens Forum X
   │
   ▼
ForumChatView mounts (no tabs)
   │
   ▼
User types "What does Thaddeus need from me?"
   │
   ▼
Backend resolver: PAIRWISE? no → MEMBER (Thaddeus) — confidence 0.95
   │
   ▼
Response renders   ┌──────────────────────────┐
                   │ Resolved: Thaddeus · Child│   ← chip above answer
                   └──────────────────────────┘
                   <answer body framed as parenting>
   │
   ▼
If user asks the very next question without naming anyone:
   "How is he doing?"
   │
   ▼
Resolver uses last_target_id (Thaddeus) → MEMBER, same frame
   │
   ▼
Same chip; answer continues parenting frame.
```

Ambiguous case ("Tell me about Peter"):

```
   ┌─────────────────────────────────────────────────┐
   │ Resolved: Needs clarification                   │
   │                                                 │
   │ I found 3 Peters. Which one do you mean?        │
   │   ○ Pete (you)                                  │
   │   ○ Peter Vogt — Forum member · EO Forum        │
   │   ○ Peter Cohen — Close friend · Founders forum │
   └─────────────────────────────────────────────────┘
```

User taps → resolver locks `last_target_id` → answer follows.

## 8. Proposed Implementation Slices

All slices are read-only-against-DB. No migrations. No flag flips
unless explicitly approved.

### Slice A — Resolver frames + ambiguity (backend, additive)

- Add `PAIRWISE`, `MULTI_PERSON`, `AMBIGUOUS` to `ActiveFrame` enum.
- Add `target_user_id_b`, `target_name_b`, `scope_class`,
  `ambiguity_candidates` to `RelationshipField`.
- Add a small `_extract_pairwise()` + `_extract_scope_class()`
  to message parsing.
- Add a name-collision detector that returns top-N candidates.
- Unit tests: extend `test_relationship_field_v2.py` with PAIRWISE,
  MULTI_PERSON, AMBIGUOUS scenarios.
- No surface change yet.

### Slice B — Backend chat-resolver wiring (Forum Chat)

- `routers/forums_chat.py`: call `resolve_relationship_field()` at
  request entry (mirroring Slice 2's Ask Mirror integration).
- `mode` field in `ForumChatRequest` becomes optional and is treated
  as a *tiebreaker only* (UI sends it; resolver demotes it).
- Attach `relationship_field_v2` to the forum-chat receipt path (or
  the response payload — design choice).
- Add response-level `resolved_context` block for FE rendering.
- No prompt-block change yet (Slice 3 prompt block is Ask-Mirror-only).

### Slice C — Frontend FlagOff dual-mode (transitional)

- Behind a new dedicated flag `FORUM_CHAT_AUTO_CONTEXT` (default
  `false`), `ForumChatView.tsx` hides the tab strip and shows the
  `ResolvedContextChip` based on response payload.
- When flag is `false`, current behaviour is bit-identical.
- Acceptance: zero visible-UI change with flag off; new chip visible
  with flag on.

### Slice D — Ambiguity clarification UI

- `AmbiguityClarificationPanel` component renders candidate list when
  `resolved_context.needs_clarification === true`.
- Tap selects a candidate, posts a follow-up message with
  `target_member_id` hint.
- Resolver locks `last_target_id` for the next N turns.

### Slice E — Pronoun memory thread

- FE sends `last_target_id` on every Mirror Chat / Forum Chat request.
- Resolver step 5 ("pronoun memory") becomes active.

### Slice F — Removal of legacy tab UI

- Once Slices A-E are deployed and the flag has been enabled in
  production for 1+ session of internal use, the tab-strip code is
  deleted from `ForumChatView.tsx`. `ForumChatMode` becomes
  `'auto' | 'self' | 'member' | 'forum'` with `'auto'` default.
- `forumChatInitialMode` plumbing in `app/forums/[id].tsx` removed.

## 9. Test Matrix

Acceptance per the user's directive, mapped to the slice that adds it:

| # | Question                                                | Expected resolve             | Slice |
| - | ------------------------------------------------------- | ---------------------------- | :---: |
| 1 | "Do I have Ophiuchus in my chart?"                      | SELF · Variant-A context     | A (pre-exists today) |
| 2 | "Tell me about Mel"                                     | MEMBER · Mel · spouse · covenant_partner | A (pre-exists) |
| 3 | "What does Thaddeus need from me?"                      | MEMBER · Thaddeus · child · steward_guardian · USER_AS_GIVER | A (pre-exists) |
| 4 | "What is happening in our family right now?"            | FORUM · Yoong family         | A — needs new forum-intent classifier |
| 5 | "How are Mel and Isaac affecting each other?"           | PAIRWISE · Mel · Isaac       | A — new |
| 6 | "Which of my children needs my attention most?"         | MULTI_PERSON · scope=children | A — new |
| 7 | "Tell me about Peter" (multiple matches)                | AMBIGUOUS · 3 candidates     | A — new |
| 8 | follow-up "How is he?"  (after #2)                      | MEMBER · Mel  (pronoun memory) | E — new |
| 9 | Tab strip hidden when flag on; visible when flag off    | UI parity                    | C |
| 10 | Ambiguity panel renders with 3 buttons                  | UI render + click            | D |

Existing surfaces that **must not regress** (independent test cases):

| Surface                          | Existing test asset                                       |
| -------------------------------- | --------------------------------------------------------- |
| How This Person Maps To Me       | Manual smoke — Pete↔Mel modal still mounts, no `currentUserName` crash |
| BaZi Wisdom Mode + Evidence V2   | Bundle marker check + visual smoke                        |
| Astrology Placements tab         | `tests/test_variant_a_canonical.py`                        |
| Ophiuchus inventory engine       | `tests/test_ophiuchus_first_class.py`                      |
| Relationship Field V2 receipts   | `services/test_relationship_field_v2.py`                   |
| Ask Mirror Slice 2/2.5/3 paths   | `services/test_slice_{2,2_5,3}*.py`                        |

## 10. Risk Inventory

| Risk                                                                              | Mitigation in plan                                                                |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Forum Chat answers regress because mode no longer routes                          | Slice B + C are flag-gated; default OFF; full A/B test before flip                |
| Pairwise pattern false-positives (e.g. "Mel and I", "Pete and the team")          | Pairwise extractor requires *two* resolvable target ids; bare "X and I" → MEMBER (X) |
| MULTI_PERSON misfires on "my colleagues" when no colleague edges exist            | Returns AMBIGUOUS (zero matches) instead of guessing                              |
| Ambiguity prompt fatigues the user                                                | Confidence threshold for clarification > 0.40; single high-conf match auto-binds |
| Hiding the tabs breaks muscle memory of power users                                | Keep tab strip available behind flag for two release cycles                       |
| Backend resolver added load per request                                            | One indexed `find_one` per request (already measured at ~5 ms in Slice 2)         |
| Forum-intent regex matches "in our family" but viewer's only forum is "Yoong"     | Cross-check against viewer's actual forum memberships; ambiguity if 0 or >1 match |
| `RELATIONSHIP_FIELD_V2_PROMPT` accidentally flipped during this work               | Strict no-flag-flip rule; this audit verifies it stays `false`                    |

## 11. Hard Constraints (verified untouched by the audit itself)

| Constraint                                | Verified |
| ----------------------------------------- | :------: |
| No DB writes                              | ✅ — audit is grep+probe only |
| No migrations                             | ✅       |
| No feature-flag changes                   | ✅ — `RELATIONSHIP_FIELD_V2_PROMPT=false` still |
| No backend / frontend code changes        | ✅ — zero files modified during this audit |
| Calculator / BaZi math / Ophiuchus / Variant-A untouched | ✅ — none referenced by the proposal |
| Existing surfaces preserved                | ✅ — see §6.2 untouched list |

## 12. Open Questions for the User (Disposition Required Before Slice A)

1. **Frame names** — keep `MEMBER` / `FORUM` / `SELF` / `PAIRWISE` /
   `MULTI_PERSON` / `AMBIGUOUS` / `RELATIONAL`? Or rename
   `RELATIONAL` → `PAIRWISE` and drop the redundant one?
2. **Forum-intent triggers** — which phrases auto-resolve to FORUM?
   Proposed seed: `our (family|team|forum|group|community)`, `in this
   (group|forum|family)`, `everyone (here|in our)`. Anything else?
3. **MULTI_PERSON scopes** — initial set: `children`, `parents`,
   `siblings`, `forum_members`, `all_family`. Add `friends`,
   `colleagues`, `mentors`? Each needs an edge-graph predicate.
4. **Ambiguity threshold** — clarify when candidates have confidence
   within 0.10 of each other? Or always when ≥2 sources match?
5. **last_target_id storage** — server-side in receipt vs client-side
   in chat state? (Server-side is more reliable across devices.)
6. **Forum Chat prompt** — should Slice 3's `RESOLVED RELATIONSHIP
   FIELD` prompt block be reused here, gated by a new flag
   `FORUM_CHAT_AUTO_CONTEXT_PROMPT`? Or share the existing
   `RELATIONSHIP_FIELD_V2_PROMPT`?
7. **Tab-strip removal timeline** — keep behind flag for one release,
   two, or remove immediately when the resolver lands?

## 13. Recommended Slice Order

Smallest blast radius first; visible UX last:

```
Slice A  (backend, additive resolver capability)         ←  start here
Slice B  (forum-chat backend wiring, mode optional)
Slice C  (frontend flag-gated tab hide + chip)            ←  user-visible
Slice D  (ambiguity panel UI)
Slice E  (pronoun memory thread)
Slice F  (legacy tab-strip removal after validation)
```

## 14. Hold Point

Audit complete. No code changes. Awaiting:

1. Disposition on §12 open questions.
2. Approval of slice ordering in §13.
3. Confirmation that the proposed `ResolvedContextChip` copy in §5.4
   matches your intended UX language.
4. Disposition on whether to share `RELATIONSHIP_FIELD_V2_PROMPT` for
   Forum Chat or introduce a separate flag.

Atlas access remains blocked pending IP whitelist — no production
reads attempted during this audit. All resolver and DB findings ran
against `localhost:27017 / test_database`.
