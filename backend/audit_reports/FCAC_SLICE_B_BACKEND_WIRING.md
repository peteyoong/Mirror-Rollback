# FCAC Slice B — Forum Chat Backend Wiring
**Delivery Report**

| Field | Value |
|---|---|
| Slice | B — Backend wiring of the Slice A resolver into Forum Chat |
| Status | **GREEN — pytest 13/13 + zero regressions (38/38 prior)** |
| Scope | Forum-Chat endpoint only.  No prompt redesign.  No UI changes.  No new collections.  No migrations. |
| New env flag | `FORUM_CHAT_AUTO_CONTEXT` — default unset (legacy path).  Set to `true` to enable auto-resolution. |
| Untouched flags | `INTENT_ROUTER_V2_CUTOVER`, `RELATIONSHIP_ORCHESTRATION_PROMPT`, `CROSS_LENS_PROMPT_SURFACE`, `RELATIONSHIP_FIELD_V2_PROMPT`, `RUN_VARIANT_A_MIGRATION` |

---

## 1. What landed

`POST /api/forums/{forum_id}/chat` now follows the new resolution order **when `FORUM_CHAT_AUTO_CONTEXT=true`**:

```
explicit_mode  ──┐
                 ├─→ rejected as the SOLE driver
target_member_id ┘
                 │
                 ▼
        Slice A resolver
   (services.relationship_field_v2.resolve_relationship_field)
                 │
                 ▼
     active_frame  ∈  {SELF, MEMBER, FORUM, PAIRWISE,
                       MULTI_PERSON, AMBIGUOUS}
                 │
                 ▼
     effective_mode  (legacy ForumChatMode) + effective_target_id
                 │
                 ▼
     existing context builder → orchestrator → FKR → LLM
```

### Resolution priority honoured (per your direction)

`MEMBER  >  PAIRWISE  >  MULTI_PERSON  >  FORUM  >  SELF`

Examples (from the live pytest suite):

| Message | Resolved frame | target_role |
|---|---|---|
| "Tell me about myself." | SELF | — |
| "What does Mel need from me?" | MEMBER | spouse |
| "What does Thaddeus need from me?" | MEMBER | child |
| "How are Mel and Thaddeus affecting each other?" | PAIRWISE | — |
| "What about my children?" | MULTI_PERSON (scope=my_children) | — |
| "What's the energy of this forum as a whole?" | FORUM | — |
| "Tell me about Test." (5 candidates) | AMBIGUOUS (short-circuits LLM) | — |
| "What does she need from me?" + last_target_id=MEL | MEMBER | spouse |

### Files touched
- `/app/backend/routers/forums_chat.py` — sole production edit
- `/app/backend/services/test_slice_b_forum_chat_wiring.py` — new test suite (13 tests)

### Request / response contract changes (additive)

**Request** — `mode` is now `Optional[ForumChatMode] = None`; new `last_target_id: Optional[str] = None`.

```jsonc
POST /api/forums/{forum_id}/chat
{
  "user_id":          "...",
  "message":          "What does Mel need from me?",
  "mode":             null,                  // optional when flag is on
  "target_member_id": null,                  // optional when flag is on
  "last_target_id":   "697ec826..."          // optional pronoun-memory hint
}
```

**Response** — three additive fields, all `null` / `false` / `[]` when the flag is off:

```jsonc
{
  "success":     true,
  "message_id":  "...",
  "response":    "...",
  "timestamp":   "...",
  "resolved_context": {                       // NEW
    "frame":             "MEMBER",
    "target_user_id":    "697ec826...",
    "target_name":       "Mel",
    "target_role":       "spouse",
    "target_user_id_b":  null,
    "target_name_b":     null,
    "scope_class":       null,
    "source":            "forum_relationship_edges",
    "confidence":        0.95
  },
  "requires_clarification":   false,         // NEW
  "clarification_candidates": []             // NEW
}
```

### AMBIGUOUS short-circuit
When the resolver returns `AMBIGUOUS`, the endpoint **returns 200 BEFORE invoking the LLM**, populates `requires_clarification=true`, and emits up to 6 candidates.  Verified in `test_B7_auto_ambiguous_short_circuits_llm` — the LLM stub records 0 calls for that path.

### Defensive guards
| Guard | Purpose |
|---|---|
| Resolver target must be a member of THIS forum | If resolver picks someone outside the current forum (e.g. via saved_people), the endpoint demotes to `SELF` and logs the demotion — never leaks cross-forum data. |
| Explicit mode not overridden by low-confidence resolver | The resolver only replaces an explicit `request.mode` when `confidence ≥ 0.70`. |
| Resolver exception is non-fatal | Any failure in the resolver falls back to the legacy mode-driven path with a warning log. |
| Legacy 400 preserved | When the flag is unset and `mode` is missing, the endpoint still returns 400 with a message that points at the flag. |

### Prompt leakage policy
Internal taxonomy strings (`PAIRWISE`, `MULTI_PERSON`, `AMBIGUOUS`, `scope_class`, `forum_intent`, `covenant_partner`, `steward_guardian`) are **never** sent to the LLM.  PAIRWISE / MULTI_PERSON framing hints use human language only ("the relationship BETWEEN them", "a group within the forum") — verified in the system-prompt assembly code.

---

## 2. Acceptance matrix (13 tests, all green)

| # | Scenario | Flag | Status |
|---|---|---|---|
| L1 | mode missing → 400 | OFF | ✅ |
| L2 | explicit member + target → unchanged path | OFF | ✅ |
| L3 | explicit self → unchanged path | OFF | ✅ |
| L4 | explicit forum → unchanged path | OFF | ✅ |
| B1 | auto SELF | ON | ✅ |
| B2 | auto MEMBER spouse | ON | ✅ |
| B3 | auto MEMBER child | ON | ✅ |
| B4 | auto PAIRWISE | ON | ✅ |
| B5 | auto MULTI_PERSON (children) | ON | ✅ |
| B6 | auto FORUM | ON | ✅ |
| B7 | auto AMBIGUOUS — LLM short-circuit verified | ON | ✅ |
| B8 | pronoun follow-up via last_target_id | ON | ✅ |
| B9 | explicit mode preserved on low-confidence resolver | ON | ✅ |

```
$ python -m pytest services/test_slice_b_forum_chat_wiring.py -v
=== 13 passed in 2.07s ===
```

---

## 3. Regression sweep

```
$ python -m pytest services/test_slice_a_auto_context.py \
                   services/test_relationship_field_v2.py \
                   services/test_slice_2_ask_mirror_wiring.py \
                   services/test_slice_3_prompt_gate.py -q
=== 38 passed in 37.13s ===
```

Zero regressions in Slice A (auto-context resolver), Slice 1 (canonical resolver), Slice 2 (Ask Mirror wiring), or Slice 3 (prompt gate).

---

## 4. Guardrails honoured

| Constraint | Honoured | Evidence |
|---|---|---|
| Calculators / birth data / timeline / HD / astrology / numerology / bazi engine | UNTOUCHED | no edits outside `routers/forums_chat.py` |
| No new collections / no migrations | UNTOUCHED | no schema changes |
| No prompt redesign | UNTOUCHED | the FORUM_CHAT_SYSTEM_PROMPT constant is byte-identical |
| No UI changes | UNTOUCHED | frontend is for Slice C |
| Untouched protected flags | UNTOUCHED | only `FORUM_CHAT_AUTO_CONTEXT` introduced |
| Mode > resolver when explicitly UI-supplied | ✅ | `test_B9` |
| Member target must belong to forum | ✅ | demotion to SELF + log on mismatch |
| AMBIGUOUS never invokes LLM | ✅ | `test_B7` (stub call count = 0) |
| No prompt leakage of internal taxonomy | ✅ | only human-language framing hints |
| Legacy 400 preserved when flag is off | ✅ | `test_L1` |

---

## 5. Operational notes

### Enabling auto-context
Set `FORUM_CHAT_AUTO_CONTEXT=true` in `/app/backend/.env`.  Reversible in seconds — unset to restore legacy behaviour.  No DB migration required.

### Backwards compatibility
- Existing clients that always send `mode` + `target_member_id` continue to work whether the flag is on or off.  The resolver only **overrides** the mode if its confidence ≥ 0.70.
- Clients that send NO `mode` will 400 when the flag is off (preserves the legacy contract).
- The new response fields (`resolved_context`, `requires_clarification`, `clarification_candidates`) are additive — old clients ignore them.

### Telemetry
Every auto-context request logs:
```
[ForumChat][SliceB] auto-context resolved: frame=MEMBER target='Mel' role='spouse'
  source=forum_relationship_edges conf=0.95 → legacy_mode=member effective_target=...
```

AMBIGUOUS short-circuits log a separate line:
```
[ForumChat][SliceB] AMBIGUOUS — candidates=5 path=['proper_name_match', 'ambiguity:...']
```

---

## 6. What is NOT in this slice

- Frontend tab hide + Context chip (Slice C)
- Ambiguity clarification UI (Slice D — folded into Slice C in your scoping)
- Pronoun memory surface wiring on the chat thread (Slice E)
- Astrology Chat consumption of auto-context (Slice F)
- Astrology Relationship Re-Story V1 (separate workstream, delivered next)

---

## 7. Next step

Proceed to **Slice C** (frontend Context Chip + ambiguity panel) — `FORUM_CHAT_AUTO_CONTEXT` flag is the same gate.

— end of report —
